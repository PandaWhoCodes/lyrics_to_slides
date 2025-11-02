# Lyrics to Slides - System Documentation

## Project Overview
A full-stack application that generates PowerPoint presentations from song lyrics fetched from the web. Designed for church worship services with focus on speed, accuracy, and clean formatting.

## Architecture

### Tech Stack
- **Backend**: Python 3.x, FastAPI, asyncio
- **Frontend**: React (Vite), Axios
- **AI Services**: xAI Grok API (lyrics extraction & validation)
- **Search**: Google Custom Search API
- **Web Scraping**: Playwright (headless Chromium)
- **Presentation**: python-pptx

### Directory Structure
```
lyrics_to_slides/
├── backend/
│   ├── main.py                    # FastAPI server & endpoints
│   ├── search_service.py          # Google Custom Search integration
│   ├── lyrics_service.py          # Web scraping + AI extraction
│   ├── validation_service.py      # AI result validation
│   ├── pptx_service.py            # Presentation orchestration
│   └── church_template.py         # Template-based PPTX generation
├── src/
│   ├── App.jsx                    # React frontend
│   └── App.css                    # Styling
├── reference_template.pptx        # PowerPoint template (preserves formatting)
├── .env                           # API keys (not in git)
└── .claude/CLAUDE.md              # This file
```

## System Workflow

### Phase 1: Search (Parallel Batch Processing)
**Endpoint**: `POST /api/search-batch`

1. **User Input**: Enter list of song names (e.g., "Amazing Grace", "How Great Thou Art")
2. **Batch Search**: Frontend sends ALL songs in single API call
3. **Backend Parallel Processing**: Uses `asyncio.gather()` to search all songs simultaneously
4. **Search Strategy**:
   - **Priority**: Curated lyrics sites (Genius, AZLyrics, Lyrics.com, Musixmatch, etc.)
   - **Fallback**: Broader Google search if < 5 results
   - **Filtering**: Removes YouTube, video sites, and video-related keywords
5. **AI Validation**: xAI Grok validates each result for relevance and confidence
6. **Result Caching**: All results cached in frontend for instant navigation

**Performance**: ~47% faster for 5 songs vs sequential (parallel backend processing)

### Phase 2: URL Selection
1. **User Reviews Results**: For each song, user sees validated search results
2. **Instant Navigation**: Results pre-cached, no waiting between songs
3. **Manual Input Fallback**: If no good results, user can paste lyrics manually
4. **Selection**: User picks best URL for each song

### Phase 3: Lyrics Extraction (Parallel)
**Endpoint**: `POST /api/extract-lyrics`

1. **Batch Extraction**: All URLs processed in parallel (batches of 5)
2. **Playwright Scraping**:
   - Headless Chromium with realistic user agent
   - Adaptive timeout (1.5-2s) for lyrics selector
   - Handles JavaScript-rendered sites
3. **AI Extraction with Grok**:
   - Model: `grok-4-fast-non-reasoning`
   - Extracts song title + lyrics
   - **Intelligent Grouping**: Groups lyrics by song structure (verse, chorus, bridge)
   - **Metadata Cleaning**: Removes [tags], (ad-libs), timestamps, etc.
   - **Title Cleaning**: Removes (Live), (Official), (Lyric Video), etc.
4. **Format**: Returns structured data with `---TITLE---`, `---LYRICS---`, `---SLIDE---` markers

### Phase 4: Review & Reselection
**Endpoint**: `POST /api/review-extraction`

1. **Preview**: User reviews extracted lyrics for each song
2. **AI Validation**: xAI checks extraction quality (structure, completeness, cleanliness)
3. **Reselection Option**: If extraction poor, user can pick different URL
4. **Manual Edit**: User can paste corrected lyrics if needed

### Phase 5: Presentation Generation
**Endpoint**: `POST /api/generate`

1. **Template Approach**: Modifies `reference_template.pptx` directly (preserves ALL formatting)
2. **Template Structure**:
   - Slide 1: Title slide with date (auto-updated to current date)
   - Slide 2: Welcome slide
   - Slide 3: Lyrics template (copied for each lyrics slide, then deleted)
3. **Slide Duplication**:
   - Deep copies Slide 3 at XML level (preserves theme colors, fonts, backgrounds)
   - Replaces text while maintaining formatting
   - Removes bullet points from lyrics
   - Adds slide numbers (e.g., "1/4", "2/4")
4. **Output**: `church_style_output.pptx` with black background, white text, proper fonts

## Key Technical Decisions

### Why Template Modification Instead of Creation?
**Problem**: Creating new Presentation() and copying slides loses theme colors and formatting.

**Solution**: Work within the template file itself:
```python
# Copy template to temp file
shutil.copy('reference_template.pptx', 'temp_working.pptx')
prs = Presentation('temp_working.pptx')

# Keep first 3 slides, delete rest
# Duplicate slide 3 for each lyrics slide using deepcopy(element)
# Delete slide 3 template after done
# Save and cleanup
```

**Result**: Preserves MSO_THEME_COLOR references, master slides, all formatting.

### Why Batch Search Endpoint?
**Problem**: Frontend parallel requests were processed sequentially on backend.

**Solution**: Single endpoint that receives all song names and uses `asyncio.gather()`:
```python
@app.post("/api/search-batch")
async def search_songs_batch(request: BatchSearchRequest):
    search_tasks = [search_lyrics(song) for song in request.song_names]
    all_results = await asyncio.gather(*search_tasks)
    return batch_response
```

**Result**: True parallelism, 47% faster for 5 songs.

### Why AI for Metadata Cleaning?
**Problem**: Regex can't distinguish between metadata `(yeah)` and lyrical content `(How great is our God)`.

**Solution**: xAI Grok with detailed prompt removes [tags], (ad-libs), timestamps while keeping meaningful parentheticals.

### Why Curated Sites List?
**Problem**: Google returns YouTube videos, music stores, random blogs.

**Solution**: Priority search on 8 trusted lyrics sites, then filtered fallback:
```python
CURATED_LYRICS_SITES = [
    "genius.com", "azlyrics.com", "lyrics.com",
    "musixmatch.com", "lyricsmode.com", "songlyrics.com",
    "metrolyrics.com", "lyricsfreak.com"
]
```

## Template Structure (reference_template.pptx)

- **Slide 1**: Title slide (Sunday Service + date)
- **Slide 2**: Welcome slide ("We are glad you are here!")
- **Slide 3**: Lyrics template slide with:
  - Black background
  - Song title at top
  - Lyrics text in center (white, large font)
  - Slide number at bottom right

**Total slides in template**: 21

## Working Approach (v3) - DETAILED STEP BY STEP

### Overview
Instead of creating a new presentation and copying slides (which loses theme colors and formatting), we **modify the template file directly**. This preserves all original formatting because we're working within the same presentation's theme context.

### Step-by-Step Process

#### Step 1: Make a Working Copy of the Template
```python
import shutil
from pptx import Presentation

template_path = 'reference_template.pptx'
temp_working_path = 'temp_working.pptx'

# Create a copy to work with (never modify the original)
shutil.copy(template_path, temp_working_path)
prs = Presentation(temp_working_path)
```

**Why this works**: The copied file retains all theme definitions, master slides, and formatting.

#### Step 2: Keep Only the First 3 Slides
```python
# Keep first 3 slides: Title (1), Welcome (2), Lyrics Template (3)
slides_to_keep = 3

while len(prs.slides) > slides_to_keep:
    # Get the relationship ID of the last slide
    rId = prs.slides._sldIdLst[-1].rId

    # Drop the relationship from the presentation part
    prs.part.drop_rel(rId)

    # Remove from the slide ID list
    del prs.slides._sldIdLst[-1]
```

**Result**: Presentation now has exactly 3 slides with all original formatting intact.

#### Step 3: Update Date on First Slide
```python
from datetime import datetime

date_str = datetime.now().strftime("%d %b'%y")  # e.g., "21 Oct'25"

# Find and update date text in first slide
for shape in prs.slides[0].shapes:
    if shape.has_text_frame:
        text = shape.text_frame.text
        # Look for date patterns (contains ' or month names)
        if "'" in text or any(month in text for month in ['Jan', 'Feb', 'Mar', ...]):
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    if "'" in run.text:
                        run.text = date_str  # Replace while keeping formatting
```

**Critical**: Update `run.text`, NOT `text_frame.text` (which clears formatting).

#### Step 4: Duplicate Slide 3 for Each Lyrics Slide
```python
from copy import deepcopy

# Get the lyrics template slide (slide 3, index 2)
lyrics_template_slide = prs.slides[2]

# For each lyrics slide needed:
# 4a. Create new slide with SAME layout as template
template_layout = lyrics_template_slide.slide_layout
new_slide = prs.slides.add_slide(template_layout)

# 4b. Remove default shapes that come with the layout
for shape in list(new_slide.shapes):
    sp = shape.element
    sp.getparent().remove(sp)

# 4c. Deep copy all shapes from template at XML element level
for shape in lyrics_template_slide.shapes:
    el = shape.element
    newel = deepcopy(el)
    new_slide.shapes._spTree.insert_element_before(newel, 'p:extLst')
```

**Why this works**:
- Using the same layout preserves master slide references
- Removing default shapes prevents duplicates
- `deepcopy(el)` copies the XML element with all formatting intact
- `insert_element_before` adds it to the slide's shape tree

#### Step 5: Replace Text in Duplicated Slide (Updated with fixes)
```python
# Identify shapes by position and replace text
for shape in new_slide.shapes:
    if shape.has_text_frame:
        # Song title (top of slide)
        if shape.top < Inches(1):
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    if run.text.strip():
                        run.text = song_name
                        break

        # Main lyrics (middle of slide)
        elif Inches(1) < shape.top < Inches(4.5):
            # Set text directly (fixes line overflow)
            shape.text_frame.text = slide_text

            # Remove bullet formatting (fixes bullet points)
            for paragraph in shape.text_frame.paragraphs:
                if hasattr(paragraph, '_element'):
                    pPr = paragraph._element.get_or_add_pPr()
                    # Remove bullet characters
                    buChar = pPr.find('.//a:buChar', {'a': '...'})
                    if buChar is not None:
                        pPr.remove(buChar)
                    # Add buNone element
                    from pptx.oxml import parse_xml
                    buNone = parse_xml('<a:buNone xmlns:a="..."/>')
                    pPr.insert(0, buNone)

        # Slide number (bottom right)
        elif shape.top > Inches(4.5) and shape.left > Inches(7):
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    run.text = f"{current_slide}/{total_slides}"
                    break
```

**Critical Points**:
- Identify shapes by **position** (top, left) not by content
- Update `run.text` to preserve all font formatting
- Break after first run if you want to replace entire text block

#### Step 6: Delete Template Slide (Added)
```python
# After all lyrics slides are created, remove slide 3 (template)
slide_id = prs.slides._sldIdLst[2]
prs.part.drop_rel(slide_id.rId)
del prs.slides._sldIdLst[2]
```

#### Step 7: Save the Final Presentation
```python
output_path = 'church_style_output.pptx'
prs.save(output_path)

# Clean up temporary file
import os
os.remove(temp_working_path)
```

### Key Principles for Success

1. **Never create a new Presentation()** - Always start with template file
2. **Use deepcopy on XML elements** - Not manual shape recreation
3. **Replace run.text, not text_frame.text** - Preserves formatting
4. **Use same layout as template** - Maintains master slide references
5. **Remove default shapes before copying** - Prevents duplicates
6. **Identify shapes by position** - More reliable than text content

### What Gets Preserved

✅ Theme colors (MSO_THEME_COLOR)
✅ Font sizes and styles
✅ Text alignment and positioning
✅ Background colors and fills
✅ Images and logos
✅ Placeholder formatting
✅ Master slide references

### Common Pitfalls to Avoid

❌ `prs = Presentation()` - Creates new presentation, loses theme
❌ `text_frame.text = "..."` - Clears all formatting runs
❌ `add_slide(blank_layout)` - Wrong layout, loses structure
❌ Manual shape copying - Loses XML relationships
❌ Not removing default shapes - Creates duplicates

### Template Structure Requirements

Your template should have:
- **Slide 1**: Title slide (e.g., "Sunday Service" + date)
- **Slide 2**: Welcome/announcement slide
- **Slide 3**: Lyrics template slide with:
  - Song title placeholder (top)
  - Lyrics content placeholder (middle)
  - Slide number (bottom right)

All subsequent lyrics slides will be duplicates of Slide 3.

## Key Files

- `backend/church_template.py` - **Current working implementation** ✅ (renamed from v3)
- `backend/pptx_service.py` - **Updated to use church_template.py** ✅
- `reference_template.pptx` - Original PowerPoint template
- `test_modify_template.py` - Reference test file demonstrating working approach
- `.claude/CLAUDE.md` - This file - project context for Claude

**Note**: Old template files (church_template_v2.py, church_template_simple.py) have been deleted.

## Environment

- Python virtual environment: `venv/`
- Backend port: 8000 (uvicorn with --reload)
- Frontend port: 5173 (npm run dev)
- Platform: macOS (Darwin 24.6.0)

## Dependencies

- python-pptx: PowerPoint manipulation
- FastAPI: Web framework
- Playwright: Web scraping
- Grok AI: Lyrics extraction and grouping

## Environment Setup

### Required Environment Variables
Create `.env` file in project root:
```bash
XAI_API_KEY=your_xai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

### Installation
```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# Frontend
cd ../
npm install
```

### Running the Application
```bash
# Terminal 1 - Backend (from project root)
cd backend
source venv/bin/activate
python3 -m uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend (from project root)
npm run dev
```

Access: http://localhost:5173

## Common Issues & Solutions

### Issue: Date showing "2525" instead of '25
**Cause**: Replacing individual text runs caused duplication/concatenation.
**Fix**: Replace entire text frame instead: `shape.text_frame.text = date_str`

### Issue: Song titles have "(Live)", "(Official)", etc.
**Cause**: Extracted raw metadata from source.
**Fix**: Added title cleaning instruction to Grok prompt.

### Issue: YouTube videos in search results
**Cause**: Google returns all content types.
**Fix**: Curated site priority + video site/keyword filtering.

### Issue: Metadata in lyrics ([Intro:], (yeah), etc.)
**Cause**: Source pages include performance annotations.
**Fix**: Detailed Grok prompt with explicit removal instructions.

### Issue: System too slow (sequential processing)
**Cause**: Frontend parallel requests processed sequentially on backend.
**Fix**: Batch endpoint with `asyncio.gather()` for true parallelism.

### Issue: Template formatting lost
**Cause**: Creating new Presentation() instead of modifying template.
**Fix**: Work within template file using deepcopy at XML level.

## Testing

### Test Batch Search Performance
```bash
python3 test_batch_search.py
```
Expected: ~47% faster for 5 songs (parallel vs sequential).

### Test Church Template
```bash
cd backend
python3 church_template.py
```
Expected: `church_style_output.pptx` created with proper formatting.

## Performance Metrics

- **Search (5 songs)**: ~7-8 seconds (parallel batch)
- **Search (5 songs sequential)**: ~13-15 seconds (old way)
- **Extraction per song**: ~2-4 seconds
- **Presentation generation**: ~1-2 seconds
- **Total workflow (5 songs)**: ~30-45 seconds

## System Status

All major features are working:
✅ Parallel batch search (47% faster)
✅ AI-powered lyrics extraction & cleaning
✅ Template formatting preservation
✅ Date auto-update (01 Nov'25 format)
✅ Title cleaning (removes Live, Official, etc.)
✅ No bullet points in lyrics
✅ Manual lyrics input fallback
✅ AI validation & reselection
