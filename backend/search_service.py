import requests
import os
from typing import List, Dict

# Load from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

# Import validation service
from validation_service import validate_search_results

# Curated list of reliable lyrics sites
CURATED_LYRICS_SITES = [
    "genius.com",
    "azlyrics.com",
    "lyrics.com",
    "musixmatch.com",
    "lyricsmode.com",
    "songlyrics.com",
    "metrolyrics.com",
    "lyricsfreak.com"
]

async def search_curated_sites(song_name: str) -> List[Dict[str, str]]:
    """
    Search only on curated lyrics sites using site: operator
    """
    # Build site restriction query
    site_restrictions = " OR ".join([f"site:{site}" for site in CURATED_LYRICS_SITES])
    query = f"{song_name} lyrics ({site_restrictions})"

    url = "https://www.googleapis.com/customsearch/v1"
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
    Search for song lyrics with curated sites priority and filtered fallback
    """
    all_results = []

    # Step 1: Try curated sites first
    print(f"Searching curated lyrics sites for: {song_name}")
    curated_results = await search_curated_sites(song_name)

    if curated_results:
        print(f"Found {len(curated_results)} results from curated sites")
        all_results.extend(curated_results)

    # Step 2: If we need more results, do a broader search
    if len(all_results) < 5:
        print(f"Searching broadly for more results...")

        # Broader search without site restrictions
        query = f"{song_name} lyrics"
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": SEARCH_ENGINE_ID,
            "q": query,
            "num": 15
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "items" in data:
                for item in data["items"]:
                    link = item.get("link", "").lower()
                    title = item.get("title", "").lower()

                    # Skip if we already have this result
                    if any(r["link"].lower() == link for r in all_results):
                        continue

                    # Filter out YouTube and video sites
                    video_sites = ['youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com',
                                   'facebook.com/watch', 'tiktok.com', 'instagram.com']
                    is_video = any(site in link for site in video_sites)

                    # Also filter if title suggests it's a video
                    video_keywords = ['official video', 'music video', 'lyric video',
                                     'official audio', 'visualizer', 'karaoke', 'instrumental']
                    has_video_keyword = any(keyword in title for keyword in video_keywords)

                    # Skip video results
                    if is_video or has_video_keyword:
                        continue

                    all_results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source": "fallback"
                    })

        except requests.exceptions.RequestException as e:
            print(f"Error in fallback search: {str(e)}")

    # Sort results: curated sites first, then others
    all_results.sort(key=lambda x: (x.get("source", "fallback") != "curated", x["link"]))

    print(f"Total results after filtering: {len(all_results)}")

    # Step 3: Validate and rank results using AI
    if all_results:
        print(f"Validating results with AI...")
        validated_results = await validate_search_results(song_name, all_results)
        return validated_results

    return all_results
