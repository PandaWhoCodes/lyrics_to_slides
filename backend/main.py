from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

from backend.search_service import search_lyrics
from backend.lyrics_service import extract_lyrics
from backend.pptx_service import create_presentation

load_dotenv()

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    song_name: str

class SearchResult(BaseModel):
    title: str
    link: str
    snippet: str

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

@app.get("/")
async def root():
    return {"message": "Lyrics to Slides API"}

@app.post("/api/search", response_model=List[SearchResult])
async def search_song(request: SearchRequest):
    """Search for song lyrics using Google Custom Search"""
    try:
        results = await search_lyrics(request.song_name)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/extract-lyrics", response_model=List[LyricsExtractionResult])
async def extract_lyrics_batch(request: ExtractLyricsRequest):
    """Extract lyrics from multiple URLs and return status for each"""
    results = []

    for url in request.urls:
        try:
            grok_response = await extract_lyrics(url)

            # Check if lyrics were found
            if not grok_response or grok_response == "NO_LYRICS_FOUND":
                results.append(LyricsExtractionResult(
                    url=url,
                    success=False,
                    error="No lyrics found on this page"
                ))
                continue

            # Parse title and lyrics from response
            song_name, lyrics = parse_grok_response(grok_response)

            # Check if we got valid lyrics
            if lyrics and len(lyrics) > 50:
                results.append(LyricsExtractionResult(
                    url=url,
                    success=True,
                    title=song_name,
                    lyrics=lyrics
                ))
            else:
                results.append(LyricsExtractionResult(
                    url=url,
                    success=False,
                    error="Extracted content too short or invalid"
                ))

        except Exception as e:
            results.append(LyricsExtractionResult(
                url=url,
                success=False,
                error=str(e)
            ))

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
            # Extract lyrics from each URL (includes title from Grok)
            for url in request.urls:
                grok_response = await extract_lyrics(url)

                if not grok_response or grok_response == "NO_LYRICS_FOUND":
                    # Skip songs with no lyrics instead of failing
                    continue

                # Parse title and lyrics from Grok's response
                song_name, lyrics = parse_grok_response(grok_response)

                all_lyrics.append(lyrics)
                song_names.append(song_name)

        if not all_lyrics:
            raise HTTPException(status_code=400, detail="No valid lyrics found for any songs")

        # Generate PPTX with all songs
        filename = create_presentation(all_lyrics, song_names, request.lines_per_slide)

        # Add background task to delete file after sending
        background_tasks.add_task(cleanup_file, filename)

        # Create response
        return FileResponse(
            path=filename,
            filename="lyrics_presentation.pptx",
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
