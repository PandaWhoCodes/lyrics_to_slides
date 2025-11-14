import requests
import os
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Load from environment variable
XAI_API_KEY = os.getenv("XAI_API_KEY", "")

async def fetch_with_playwright(url: str) -> str:
    """
    Fetch webpage content using Playwright for JavaScript-rendered sites
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True
        )
        page = await context.new_page()

        try:
            # Try different wait strategies
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            except:
                # If that fails, try with load event
                await page.goto(url, wait_until='load', timeout=60000)

            # Wait for content to render (reduced from 5000ms)
            # Try to wait for common lyrics selectors, with fallback to shorter timeout
            try:
                await page.wait_for_selector('[class*="lyrics"], [class*="Lyrics"], [data-lyrics-container]', timeout=2000)
            except:
                # If no lyrics selector found, just wait a bit for JS to render
                await page.wait_for_timeout(1500)

            # Get the full page content
            content = await page.content()

            await browser.close()
            return content
        except Exception as e:
            await browser.close()
            raise Exception(f"Playwright error: {str(e)}")

def extract_lyrics_from_html(html_content: str, url: str) -> str:
    """
    Extract lyrics from HTML using BeautifulSoup with site-specific selectors
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Try common lyrics selectors
    lyrics_selectors = [
        {'class': 'lyrics'},
        {'class': 'Lyrics__Container'},
        {'class': 'song-lyrics'},
        {'class': 'lyric-body'},
        {'data-lyrics-container': 'true'},
        {'id': 'lyrics-root'},
        {'class': 'song_body-lyrics'},
        {'class': 'lyrics-text'},
    ]

    for selector in lyrics_selectors:
        elements = soup.find_all(attrs=selector)
        if elements:
            lyrics_text = '\n'.join([elem.get_text(separator='\n', strip=True) for elem in elements])
            if lyrics_text and len(lyrics_text) > 50:
                return lyrics_text

    # If no specific selector works, try to extract all text and clean it
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "header", "footer"]):
        script.decompose()

    text = soup.get_text(separator='\n', strip=True)
    return text

async def extract_lyrics(url: str) -> str:
    """
    Fetch the webpage and extract lyrics using Playwright + xAI Grok
    """
    try:
        # Use Playwright for JavaScript-heavy sites
        print(f"Fetching URL with Playwright: {url}")
        webpage_content = await fetch_with_playwright(url)

        # First try to extract with BeautifulSoup
        lyrics_html = extract_lyrics_from_html(webpage_content, url)

        # Truncate if too long (to avoid token limits)
        if len(lyrics_html) > 50000:
            lyrics_html = lyrics_html[:50000]

        # Use xAI Grok to extract song title and intelligently group lyrics
        print("Extracting title and grouping lyrics with Grok...")
        grok_response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-4-fast-non-reasoning",
                "messages": [
                    {
                        "role": "system",
                        "content": """You are a song lyrics extraction assistant for church worship presentations.

Extract the song title and CLEAN lyrics from the provided webpage text.

LANGUAGE REQUIREMENTS - CRITICAL:
- ONLY extract lyrics in English or English transliteration (romanized)
- If the page has lyrics in non-Latin scripts (Tamil, Telugu, Hindi, Devanagari, Malayalam, etc.), check if English transliteration is also available
- Prefer English transliteration over native script ALWAYS
- If ONLY native script is available, return 'NO_ENGLISH_LYRICS_FOUND' instead of extracting
- Examples of acceptable formats:
  * Full English lyrics
  * Tamil/Telugu song with English transliteration (e.g., "Unga naamam uyaranum" not "உங்க நாமம் உயரணும்")
  * English translation OR transliteration (prefer transliteration)

CRITICAL FORMATTING - MUST FOLLOW EXACTLY:
---TITLE---
Song Title by Artist Name
---LYRICS---
Line 1 of verse 1
Line 2 of verse 1
---SLIDE---
Line 1 of chorus
Line 2 of chorus
---SLIDE---
Line 1 of verse 2
Line 2 of verse 2

METADATA TO REMOVE (NEVER include these):
- Section markers: [Intro:], [Verse 1:], [Verse 2:], [Chorus:], [Bridge:], [Outro:], [Pre-Chorus:], etc.
- Artist annotations: [Chandler Moore:], [Brandon Lake:], (feat. Artist Name), etc.
- Performance instructions: (Repeat), (x2), (x3), (2X), etc.
- Ad-libs and sounds: (yeah), (oh), (uh), (woo), (clap), etc.
- Time stamps: [0:45], (2:30), etc.
- Any text in square brackets [ ] or angle brackets < >
- YouTube metadata like "views", "likes", "subscribe"

WHAT TO KEEP:
- Actual song lyrics that are meant to be sung (in ENGLISH or English transliteration ONLY)
- Meaningful parenthetical content that's part of the lyrics, like: (How great is our God), (I will praise)

RULES:
1. First line MUST be exactly "---TITLE---"
2. Second line is the song title with artist (e.g., "What A Beautiful Name by Hillsong Worship")
   - If artist is unknown, just use the song title WITHOUT adding "by UNKNOWN ARTIST"
   - CLEAN the title: Remove (Live), (Official), (Lyric Video), (Audio), etc. from title
   - Example: "Endless Praise (Live) by Maverick City Music" → "Endless Praise by Maverick City Music"
3. Third line MUST be exactly "---LYRICS---"
4. Group lyrics by natural song structure with "---SLIDE---" between sections
5. Keep verses, choruses, and bridges intact as logical units
6. DO NOT include section labels - the structure should be clear from repetition
7. Clean all metadata but preserve the actual lyrics' meaning
8. If no English/transliteration found, return 'NO_ENGLISH_LYRICS_FOUND'
9. If no clear lyrics found, return 'NO_LYRICS_FOUND'

EXAMPLE of what to remove:
[Verse 1: Brandon Lake]
I'll praise in the valley (yeah)
Praise on the mountain (oh)

Should become:
I'll praise in the valley
Praise on the mountain"""
                    },
                    {
                        "role": "user",
                        "content": f"Extract the song title and intelligently grouped lyrics from this webpage:\n\n{lyrics_html}"
                    }
                ],
                "temperature": 0.1
            },
            timeout=60
        )

        grok_response.raise_for_status()
        result = grok_response.json()

        response_text = result["choices"][0]["message"]["content"].strip()

        if response_text == "NO_ENGLISH_LYRICS_FOUND":
            raise Exception("This page contains only non-English script. Please select a page with English transliteration.")

        if response_text == "NO_LYRICS_FOUND" or len(response_text) < 50:
            raise Exception("Could not extract meaningful lyrics from this page. The site may not have lyrics or may require authentication.")

        print(f"Successfully extracted {len(response_text)} characters")
        return response_text

    except Exception as e:
        raise Exception(f"Error extracting lyrics: {str(e)}")
