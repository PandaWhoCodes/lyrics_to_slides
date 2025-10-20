from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

from search_service import search_lyrics
from lyrics_service import extract_lyrics
from pptx_service import create_presentation

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

@app.post("/api/generate")
async def generate_presentation(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Generate PowerPoint presentation from lyrics"""
    filename = None
    try:
        all_lyrics = []
        song_names = []

        # Extract lyrics from each URL (includes title from Grok)
        for url in request.urls:
            grok_response = await extract_lyrics(url)

            if not grok_response:
                raise HTTPException(status_code=400, detail=f"Could not extract lyrics from URL: {url}")

            # Parse title and lyrics from Grok's response
            song_name, lyrics = parse_grok_response(grok_response)

            all_lyrics.append(lyrics)
            song_names.append(song_name)

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
