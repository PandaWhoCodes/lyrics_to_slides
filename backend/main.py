from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables BEFORE importing other modules
load_dotenv()

from search_service import search_lyrics, search_all_sites
from lyrics_service import extract_lyrics
from pptx_service import create_presentation

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend) - check if dist directory exists
dist_path = os.path.join(os.path.dirname(__file__), "..", "dist")
if os.path.exists(dist_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")

class SearchRequest(BaseModel):
    song_name: str

class BatchSearchRequest(BaseModel):
    song_names: List[str]

class SearchResult(BaseModel):
    title: str
    link: str
    snippet: str

class BatchSearchResponse(BaseModel):
    song_name: str
    results: List[SearchResult]

class GenerateRequest(BaseModel):
    urls: List[str]
    lines_per_slide: int
    # Optional: pre-extracted lyrics from validation step
    validated_songs: Optional[List[dict]] = None

class ExtractLyricsRequest(BaseModel):
    urls: List[str]

class LyricsExtractionResult(BaseModel):
    url: str
    success: bool
    title: Optional[str] = None
    lyrics: Optional[str] = None
    error: Optional[str] = None

class ManualLyricsRequest(BaseModel):
    title: str
    lyrics: str
    clean_formatting: bool = True  # Whether to clean the lyrics of metadata

class ManualLyricsResponse(BaseModel):
    success: bool
    title: str
    lyrics: str
    slide_groups: Optional[List[str]] = None  # Lyrics grouped for slides

@app.get("/health")
async def health_check():
    """Health check endpoint for Fly.io"""
    return {"status": "healthy", "service": "lyrics-to-slides"}

@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {"message": "Lyrics to Slides API"}

@app.get("/")
async def serve_frontend():
    """Serve the React frontend"""
    index_path = os.path.join(os.path.dirname(__file__), "..", "dist", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not built. Run 'npm run build' first."}

@app.post("/api/search", response_model=List[SearchResult])
async def search_song(request: SearchRequest):
    """Search for song lyrics using Google Custom Search"""
    try:
        results = await search_lyrics(request.song_name)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search-batch", response_model=List[BatchSearchResponse])
async def search_songs_batch(request: BatchSearchRequest):
    """Search for multiple songs in parallel using Google Custom Search"""
    try:
        # Search all songs in parallel
        search_tasks = [search_lyrics(song_name) for song_name in request.song_names]
        all_results = await asyncio.gather(*search_tasks)

        # Format the response
        batch_response = []
        for song_name, results in zip(request.song_names, all_results):
            batch_response.append(BatchSearchResponse(
                song_name=song_name,
                results=results
            ))

        return batch_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search-all", response_model=List[SearchResult])
async def search_all(request: SearchRequest):
    """Search all sites without curated restrictions - for broader results"""
    try:
        results = await search_all_sites(request.song_name)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def extract_single_url(url: str) -> LyricsExtractionResult:
    """Extract lyrics from a single URL"""
    try:
        grok_response = await extract_lyrics(url)

        # Check if lyrics were found
        if not grok_response or grok_response == "NO_LYRICS_FOUND":
            return LyricsExtractionResult(
                url=url,
                success=False,
                error="No lyrics found on this page"
            )

        # Parse title and lyrics from response
        song_name, lyrics = parse_grok_response(grok_response)

        # Check if we got valid lyrics
        if lyrics and len(lyrics) > 50:
            return LyricsExtractionResult(
                url=url,
                success=True,
                title=song_name,
                lyrics=lyrics
            )
        else:
            return LyricsExtractionResult(
                url=url,
                success=False,
                error="Extracted content too short or invalid"
            )

    except Exception as e:
        return LyricsExtractionResult(
            url=url,
            success=False,
            error=str(e)
        )

@app.post("/api/extract-lyrics", response_model=List[LyricsExtractionResult])
async def extract_lyrics_batch(request: ExtractLyricsRequest):
    """Extract lyrics from multiple URLs in parallel and return status for each"""
    # Process URLs in parallel, batching them to avoid overwhelming the system
    # Process up to 5 URLs at a time
    batch_size = 5
    results = []

    for i in range(0, len(request.urls), batch_size):
        batch_urls = request.urls[i:i + batch_size]

        # Extract lyrics for this batch in parallel
        batch_tasks = [extract_single_url(url) for url in batch_urls]
        batch_results = await asyncio.gather(*batch_tasks)

        results.extend(batch_results)

    return results

@app.post("/api/generate")
async def generate_presentation(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Generate PowerPoint presentation from lyrics"""
    filename = None
    try:
        all_lyrics = []
        song_names = []

        # If we have pre-validated songs, use them
        if request.validated_songs:
            for song in request.validated_songs:
                all_lyrics.append(song['lyrics'])
                song_names.append(song['title'])
        else:
            # Extract lyrics from all URLs in parallel
            extraction_tasks = [extract_single_url(url) for url in request.urls]
            extraction_results = await asyncio.gather(*extraction_tasks)

            # Process successful extractions
            for result in extraction_results:
                if result.success and result.lyrics and result.title:
                    all_lyrics.append(result.lyrics)
                    song_names.append(result.title)

        if not all_lyrics:
            raise HTTPException(status_code=400, detail="No valid lyrics found for any songs")

        # Generate PPTX with all songs
        filename = create_presentation(all_lyrics, song_names, request.lines_per_slide)

        # Add background task to delete file after sending
        background_tasks.add_task(cleanup_file, filename)

        # Create response with explicit headers
        return FileResponse(
            path=filename,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": "attachment; filename=lyrics_presentation.pptx"
            }
        )
    except Exception as e:
        # Clean up file if there was an error
        if filename and os.path.exists(filename):
            os.remove(filename)
        raise HTTPException(status_code=500, detail=str(e))

def parse_grok_response(grok_response: str) -> tuple[str, str]:
    """
    Parse Grok's response to extract title and lyrics
    Format:
    ---TITLE---
    Song Title by Artist
    ---LYRICS---
    lyrics content...
    """
    try:
        # Split by markers
        if "---TITLE---" in grok_response and "---LYRICS---" in grok_response:
            parts = grok_response.split("---TITLE---")
            if len(parts) > 1:
                title_and_rest = parts[1].split("---LYRICS---")
                if len(title_and_rest) > 1:
                    title = title_and_rest[0].strip()
                    lyrics = title_and_rest[1].strip()

                    # Remove " by UNKNOWN ARTIST" if present (case-insensitive)
                    if title.upper().endswith(" BY UNKNOWN ARTIST"):
                        title = title[:title.upper().rfind(" BY UNKNOWN ARTIST")].strip()

                    return title, lyrics

        # Fallback: treat entire response as lyrics, use generic title
        return "Unknown Song", grok_response
    except Exception as e:
        print(f"Error parsing Grok response: {e}")
        return "Unknown Song", grok_response

def cleanup_file(filepath: str):
    """Background task to delete file after sending"""
    import time
    time.sleep(2)  # Wait 2 seconds after response
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Cleaned up: {filepath}")
    except Exception as e:
        print(f"Error cleaning up {filepath}: {e}")

async def clean_manual_lyrics(lyrics: str) -> str:
    """
    Clean manually input lyrics using AI to remove metadata if present
    """
    import requests
    XAI_API_KEY = os.getenv("XAI_API_KEY", "")

    clean_prompt = """Clean these lyrics for church presentation:

REMOVE:
- Section markers like [Verse 1], [Chorus], [Bridge]
- Artist annotations like (feat. Artist)
- Performance notes like (repeat), (x2), (yeah), (oh)
- Any metadata in brackets or unnecessary parentheses

KEEP:
- Actual lyrics
- Meaningful parenthetical lyrics like "(How great is our God)"
- Natural line breaks and verse structure

Group the lyrics with "---SLIDE---" between sections.
Return ONLY the cleaned lyrics, nothing else.

Lyrics to clean:
""" + lyrics

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
                    {"role": "system", "content": "You are a lyrics cleaner. Return only cleaned lyrics with ---SLIDE--- markers."},
                    {"role": "user", "content": clean_prompt}
                ],
                "temperature": 0.1
            },
            timeout=30
        )

        response.raise_for_status()
        result = response.json()
        cleaned = result["choices"][0]["message"]["content"].strip()
        return cleaned

    except Exception as e:
        print(f"Error cleaning lyrics: {e}")
        # Return original if cleaning fails, but try basic cleanup
        import re
        # Remove common metadata patterns
        cleaned = re.sub(r'\[.*?\]', '', lyrics)  # Remove [brackets]
        cleaned = re.sub(r'\(repeat.*?\)', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\(x\d+\)', '', cleaned)
        cleaned = re.sub(r'\((yeah|oh|uh|woo)\)', '', cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

@app.post("/api/manual-lyrics", response_model=ManualLyricsResponse)
async def process_manual_lyrics(request: ManualLyricsRequest):
    """Process manually input lyrics and prepare them for presentation"""
    try:
        # Clean the lyrics if requested
        if request.clean_formatting:
            print(f"Cleaning manual lyrics for: {request.title}")
            cleaned_lyrics = await clean_manual_lyrics(request.lyrics)
        else:
            cleaned_lyrics = request.lyrics

        # Split into slide groups if markers are present
        slide_groups = None
        if "---SLIDE---" in cleaned_lyrics:
            slide_groups = [group.strip() for group in cleaned_lyrics.split("---SLIDE---") if group.strip()]

        return ManualLyricsResponse(
            success=True,
            title=request.title,
            lyrics=cleaned_lyrics,
            slide_groups=slide_groups
        )

    except Exception as e:
        return ManualLyricsResponse(
            success=False,
            title=request.title,
            lyrics=request.lyrics,
            slide_groups=None
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
