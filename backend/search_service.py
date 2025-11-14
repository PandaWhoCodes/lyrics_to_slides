import requests
import os
import re
from typing import List, Dict, Tuple

# Load from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

# Import validation service
from validation_service import validate_search_results

def contains_non_latin(text: str) -> bool:
    """
    Check if text contains non-Latin characters (Tamil, Telugu, Hindi, etc.)
    """
    non_latin_pattern = re.compile(r'[\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F\u0C00-\u0C7F\u0C80-\u0CFF\u0D00-\u0D7F\u4E00-\u9FFF]')
    return bool(non_latin_pattern.search(text))

def detect_language_keywords(text: str) -> bool:
    """
    Check if text contains language indicator keywords
    """
    language_keywords = ['tamil', 'telugu', 'hindi', 'malayalam', 'kannada', 'bengali', 'punjabi']
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in language_keywords)

def build_search_query(song_name: str) -> Tuple[str, bool]:
    """
    Build search query with language awareness
    Returns: (query_string, is_non_english)
    """
    is_non_english = contains_non_latin(song_name) or detect_language_keywords(song_name)

    if is_non_english:
        # Add keywords for English transliteration
        query = f"{song_name} lyrics english transliteration romanized"
        print(f"  🌍 Detected non-English song - searching for English transliteration")
    else:
        query = f"{song_name} lyrics"

    return query, is_non_english

# Enhanced curated list of reliable lyrics sites (including Christian/worship specific sites)
CURATED_LYRICS_SITES = [
    # Original general lyrics sites
    "genius.com",
    "azlyrics.com",
    "lyrics.com",
    "musixmatch.com",
    "lyricsmode.com",
    "songlyrics.com",
    "metrolyrics.com",
    "lyricsfreak.com",
    # Christian/worship specific sites (for multilingual songs with English transliteration)
    "songs.wcflondon.com",
    "tamilchristiansongs.org",
    "onewaytheonlyway.com",
    "waytochurch.com",
    "praisecharts.com",
    "worshiptogether.com",
    "christianlyricz.com",
    "worldtamilchristians.com"
]

async def search_curated_sites(song_name: str) -> List[Dict[str, str]]:
    """
    Search only on curated lyrics sites using site: operator with language awareness
    """
    # Build language-aware query
    query, is_non_english = build_search_query(song_name)

    # Build site restriction query
    site_restrictions = " OR ".join([f"site:{site}" for site in CURATED_LYRICS_SITES])
    full_query = f"{query} ({site_restrictions})"

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": full_query,
        "num": 10
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        results = []
        if "items" in data:
            for item in data["items"]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "curated"
                })

        return results

    except requests.exceptions.RequestException as e:
        print(f"Error in curated search: {str(e)}")
        return []

async def search_lyrics(song_name: str) -> List[Dict[str, str]]:
    """
    Search for song lyrics with curated sites priority and fallback to 20 unfiltered results
    """
    all_results = []

    # Step 1: Try curated sites first
    print(f"🎯 Searching curated lyrics sites for: {song_name}")
    curated_results = await search_curated_sites(song_name)

    if curated_results:
        print(f"✅ Found {len(curated_results)} results from curated sites")
        all_results.extend(curated_results)
    else:
        print(f"❌ No results from curated sites")

    # Step 2: If NO results from curated sites, do fallback with 20 results
    if not all_results:
        print(f"🌐 FALLBACK: Searching broadly for up to 20 results...")

        # Build language-aware query
        query, _ = build_search_query(song_name)

        url = "https://www.googleapis.com/customsearch/v1"

        # First batch (results 1-10)
        params = {
            "key": GOOGLE_API_KEY,
            "cx": SEARCH_ENGINE_ID,
            "q": query,
            "num": 10
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "items" in data:
                for item in data["items"]:
                    link = item.get("link", "").lower()
                    title = item.get("title", "").lower()

                    # Filter out YouTube and video sites
                    video_sites = ['youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com',
                                   'facebook.com/watch', 'tiktok.com', 'instagram.com']
                    is_video = any(site in link for site in video_sites)

                    # Also filter if title suggests it's a video
                    video_keywords = ['official video', 'music video', 'lyric video',
                                     'official audio', 'visualizer', 'karaoke', 'instrumental']
                    has_video_keyword = any(keyword in title for keyword in video_keywords)

                    # Skip video results
                    if not (is_video or has_video_keyword):
                        all_results.append({
                            "title": item.get("title", ""),
                            "link": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "source": "fallback"
                        })

            # Second batch (results 11-20) if we have room
            if len(all_results) < 20:
                params["start"] = 11
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                if "items" in data:
                    for item in data["items"]:
                        if len(all_results) >= 20:
                            break

                        link = item.get("link", "").lower()
                        title = item.get("title", "").lower()

                        # Same filtering
                        video_sites = ['youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com',
                                       'facebook.com/watch', 'tiktok.com', 'instagram.com']
                        is_video = any(site in link for site in video_sites)
                        video_keywords = ['official video', 'music video', 'lyric video',
                                         'official audio', 'visualizer', 'karaoke', 'instrumental']
                        has_video_keyword = any(keyword in title for keyword in video_keywords)

                        if not (is_video or has_video_keyword):
                            all_results.append({
                                "title": item.get("title", ""),
                                "link": item.get("link", ""),
                                "snippet": item.get("snippet", ""),
                                "source": "fallback"
                            })

            print(f"✅ Found {len(all_results)} results via fallback (excluding videos)")

        except requests.exceptions.RequestException as e:
            print(f"❌ Error in fallback search: {str(e)}")

    print(f"📊 Total results: {len(all_results)}")

    # Step 3: Validate and rank results using AI
    if all_results:
        print(f"🤖 Validating results with AI...")
        validated_results = await validate_search_results(song_name, all_results)
        return validated_results

    return all_results
