import os
import requests
from typing import List, Dict, Optional
import json

# Load from environment variable
XAI_API_KEY = os.getenv("XAI_API_KEY", "")

async def validate_search_results(
    song_query: str,
    search_results: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    """
    Use AI to validate and rank search results based on user intent
    Returns the results with confidence scores and rankings
    """
    if not search_results:
        return []

    # Prepare the results for validation
    results_for_validation = []
    for i, result in enumerate(search_results[:10]):  # Validate top 10
        results_for_validation.append({
            "index": i,
            "title": result["title"],
            "url": result["link"],
            "snippet": result["snippet"]
        })

    validation_prompt = f"""
You are a search result validator for worship song lyrics.

User is searching for: "{song_query}"

Validate each search result and assign:
1. A confidence score (0-100) that this is the correct song
2. Whether it's actually a lyrics page (not video, not album info, etc.)
3. If an artist was specified, whether it matches

Return JSON array with this structure:
[
  {{
    "index": 0,
    "confidence": 95,
    "is_lyrics_page": true,
    "artist_match": true,
    "reason": "Exact match with specified artist"
  }}
]

Search results to validate:
{json.dumps(results_for_validation, indent=2)}

IMPORTANT:
- Worship songs often have multiple versions by different artists
- If user specified an artist (e.g., "by Kari Jobe" or "- Hillsong"), prefer that version
- Generic versions (no specific artist) are acceptable if the specified artist version isn't found
- Mark videos, album pages, and chord sheets with is_lyrics_page: false
"""

    try:
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-4-fast-non-reasoning",
                "messages": [
                    {"role": "system", "content": "You are a search result validator. Return only valid JSON."},
                    {"role": "user", "content": validation_prompt}
                ],
                "temperature": 0.1
            },
            timeout=30
        )

        response.raise_for_status()
        result = response.json()
        validation_text = result["choices"][0]["message"]["content"].strip()

        # Parse the JSON response
        try:
            # Extract JSON from the response (in case there's extra text)
            import re
            json_match = re.search(r'\[.*\]', validation_text, re.DOTALL)
            if json_match:
                validations = json.loads(json_match.group())
            else:
                validations = json.loads(validation_text)
        except json.JSONDecodeError:
            print(f"Failed to parse validation response: {validation_text}")
            # Return original results if validation fails
            return search_results

        # Create a map of validations by index
        validation_map = {v["index"]: v for v in validations}

        # Enhance results with validation data
        enhanced_results = []
        for i, result in enumerate(search_results[:10]):
            if i in validation_map:
                validation = validation_map[i]
                # Only include results that are actual lyrics pages
                if validation.get("is_lyrics_page", False):
                    result["confidence"] = validation.get("confidence", 50)
                    result["validation_reason"] = validation.get("reason", "")
                    enhanced_results.append(result)
            else:
                # Include unvalidated results at the end with low confidence
                result["confidence"] = 25
                result["validation_reason"] = "Not validated"
                enhanced_results.append(result)

        # Add remaining results that weren't validated
        for result in search_results[10:]:
            result["confidence"] = 20
            result["validation_reason"] = "Not validated"
            enhanced_results.append(result)

        # Sort by confidence score (highest first)
        enhanced_results.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        print(f"Validated {len(validations)} results, returning {len(enhanced_results)} lyrics pages")
        return enhanced_results

    except Exception as e:
        print(f"Error validating search results: {str(e)}")
        # Return original results if validation fails
        return search_results

async def validate_single_result(
    song_query: str,
    url: str,
    title: str,
    snippet: str
) -> Dict[str, any]:
    """
    Validate a single search result to check if it matches the user's intent
    """
    validation_prompt = f"""
User is searching for: "{song_query}"

Is this the correct result?
Title: {title}
URL: {url}
Snippet: {snippet[:200]}

Return JSON:
{{
  "is_match": true/false,
  "confidence": 0-100,
  "is_lyrics_page": true/false,
  "reason": "brief explanation"
}}
"""

    try:
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-4-fast-non-reasoning",
                "messages": [
                    {"role": "system", "content": "Return only valid JSON."},
                    {"role": "user", "content": validation_prompt}
                ],
                "temperature": 0.1
            },
            timeout=15
        )

        response.raise_for_status()
        result = response.json()
        validation_text = result["choices"][0]["message"]["content"].strip()

        # Parse JSON response
        import re
        json_match = re.search(r'\{.*\}', validation_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return json.loads(validation_text)

    except Exception as e:
        print(f"Error validating single result: {str(e)}")
        return {
            "is_match": True,  # Assume it's valid if validation fails
            "confidence": 50,
            "is_lyrics_page": True,
            "reason": "Validation failed, assuming valid"
        }