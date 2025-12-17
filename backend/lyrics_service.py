import requests
import os
import urllib.parse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Load from environment variable
XAI_API_KEY = os.getenv("XAI_API_KEY", "")

# CORS proxies for sites that block direct requests
CORS_PROXIES = [
    {
        "name": "AllOrigins",
        "url": "https://api.allorigins.win/get?url={url}",
        "response_key": "contents"
    },
    {
        "name": "corsproxy.io",
        "url": "https://corsproxy.io/?{url}",
        "response_key": None  # Direct response
    },
]

def fetch_with_cors_proxy(url: str) -> str:
    """
    Fetch webpage content using CORS proxies for sites that block direct requests.
    Tries multiple proxies until one succeeds.
    """
    encoded_url = urllib.parse.quote(url, safe='')
    last_error = None

    for proxy in CORS_PROXIES:
        try:
            proxy_url = proxy["url"].format(url=encoded_url)
            print(f"  🌐 Trying {proxy['name']} proxy: {url}")

            response = requests.get(proxy_url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            response.raise_for_status()

            if proxy["response_key"]:
                # JSON response with content in a specific key
                data = response.json()
                if proxy["response_key"] in data:
                    content = data[proxy["response_key"]]
                    print(f"  ✅ {proxy['name']} returned {len(content)} characters")
                    return content
                else:
                    raise Exception(f"Response missing '{proxy['response_key']}' field")
            else:
                # Direct HTML response
                content = response.text
                print(f"  ✅ {proxy['name']} returned {len(content)} characters")
                return content

        except Exception as e:
            print(f"  ⚠️ {proxy['name']} failed: {e}")
            last_error = e
            continue

    raise Exception(f"All CORS proxies failed. Last error: {last_error}")


async def fetch_with_playwright(url: str) -> str:
    """
    Fetch webpage content using Playwright for JavaScript-rendered sites
    """
    async with async_playwright() as p:
        # Docker/container-friendly Chromium launch args
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--single-process'
            ]
        )
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

            # Site-specific wait strategies
            if 'smule.com' in url.lower():
                # Smule loads lyrics dynamically, wait longer and look for specific elements
                print("  ⏳ Waiting for Smule to load lyrics...")
                try:
                    await page.wait_for_selector('[class*="lyric"], [class*="Lyric"], [class*="arrangement"]', timeout=10000)
                except:
                    await page.wait_for_timeout(5000)  # Fallback wait
            else:
                # Wait for content to render
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
    Fetch the webpage and extract lyrics using multiple strategies + xAI Grok
    """
    try:
        # Sites that require JavaScript rendering - MUST use Playwright first
        # (CORS proxies only get static HTML, missing dynamically loaded content)
        js_rendered_sites = ['smule.com']
        needs_js_rendering = any(site in url.lower() for site in js_rendered_sites)

        # Sites that block headless browsers but serve static HTML - use CORS proxy first
        static_sites_that_block = ['shazam.com']
        use_cors_proxy_first = any(site in url.lower() for site in static_sites_that_block)

        webpage_content = None

        if needs_js_rendering:
            # Sites like Smule load lyrics via JavaScript - MUST use Playwright
            print(f"🎭 Site requires JavaScript rendering, using Playwright: {url}")
            try:
                webpage_content = await fetch_with_playwright(url)
            except Exception as e:
                print(f"  ⚠️ Playwright failed: {e}, trying CORS proxy as fallback")
                try:
                    webpage_content = fetch_with_cors_proxy(url)
                except Exception as cors_error:
                    print(f"  ⚠️ CORS proxy also failed: {cors_error}")
                    raise e  # Re-raise original Playwright error
        elif use_cors_proxy_first:
            # Try CORS proxy first for sites that block scrapers but have static HTML
            print(f"🌐 Site may block scrapers, trying CORS proxy first: {url}")
            try:
                webpage_content = fetch_with_cors_proxy(url)
            except Exception as e:
                print(f"  ⚠️ CORS proxy failed: {e}, falling back to Playwright")

        if not webpage_content:
            # Default: Try Playwright first, then CORS proxy
            print(f"🎭 Fetching URL with Playwright: {url}")
            try:
                webpage_content = await fetch_with_playwright(url)
            except Exception as playwright_error:
                print(f"  ⚠️ Playwright failed: {playwright_error}")
                print(f"  🌐 Trying CORS proxy as fallback...")
                webpage_content = fetch_with_cors_proxy(url)

        if not webpage_content:
            raise Exception("Failed to fetch webpage content")

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
                "model": "grok-4-1-fast-non-reasoning",
                "messages": [
                    {
                        "role": "system",
                        "content": """You are a song lyrics extraction assistant for church worship presentations.

Extract the song title and CLEAN lyrics from the provided webpage text.

LANGUAGE REQUIREMENTS:
- PREFER lyrics in English or English transliteration (romanized Latin script)
- If the page has lyrics in non-Latin scripts (Tamil, Telugu, Hindi, Devanagari, Malayalam, etc.):
  1. FIRST check if English transliteration is also available on the page - use that
  2. If no transliteration exists, YOU MUST TRANSLITERATE the lyrics yourself into romanized form
  3. NEVER return 'NO_ENGLISH_LYRICS_FOUND' if you can transliterate the text
- Examples of acceptable output:
  * Full English lyrics
  * Tamil song: "Unga naamam uyaranum" (NOT "உங்க நாமம் உயரணும்")
  * Hindi song: "Kya de sakta hu shukriya tera" (NOT "क्या दे सकता हूं शुक्रिया तेरा")
- ONLY return 'NO_ENGLISH_LYRICS_FOUND' if you cannot find OR transliterate any lyrics

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
