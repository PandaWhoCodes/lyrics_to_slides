import requests
import os
from typing import List, Dict

# Load from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

async def search_lyrics(song_name: str) -> List[Dict[str, str]]:
    """
    Search for song lyrics using Google Custom Search API
    """
    # Add 'lyrics' to the search query
    query = f"{song_name} lyrics"

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": query,
        "num": 5  # Return top 5 results
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
                    "snippet": item.get("snippet", "")
                })

        return results

    except requests.exceptions.RequestException as e:
        raise Exception(f"Error searching for lyrics: {str(e)}")
