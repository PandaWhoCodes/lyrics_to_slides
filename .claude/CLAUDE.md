# Claude Context - Lyrics to Slides Project

## Project Overview
A full-stack application that generates PowerPoint presentations from song lyrics fetched from the web.

## Architecture

### Backend (Python/FastAPI)
- **main.py**: API endpoints for search, extract lyrics, generate presentation
- **search_service.py**: Google Custom Search integration
- **lyrics_service.py**: Playwright-based web scraping + Grok AI for lyrics extraction
- **pptx_service.py**: Orchestrates presentation generation
- **church_template_v3.py**: Template-based PPTX generation (current working version)

### Frontend (React)
- Located in frontend directory
- Running on port 5173
- Communicates with backend API on port 8000

## Recent Issues Solved ✅

### 1. Template Slide Deletion (Fixed)
**Problem**: Slide 3 (template) was remaining in final presentation
**Solution**: Added code to delete slide 3 after all lyrics slides are created

### 2. Text Overflow (Fixed)
**Problem**: All lyrics (16+ lines) were being put on each slide instead of 4 lines
**Solution**: Fixed text replacement logic to properly use only the specified lines_per_slide

### 3. Bullet Points in Lyrics (Fixed)
**Problem**: Lyrics were appearing as bullet points
**Solution**: Added code to explicitly remove bullet formatting and add `buNone` element to paragraphs

### 4. UNKNOWN ARTIST Removal (Fixed)
**Problem**: When artist is unknown, "Song Title by UNKNOWN ARTIST" was displayed on every slide
**Solution**:
- Updated Grok prompt to not include " by UNKNOWN ARTIST" suffix
- Added fallback logic in `parse_grok_response()` to strip " by UNKNOWN ARTIST" (case-insensitive)

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

## Testing

Run tests with:
```bash
source venv/bin/activate
python3 backend/church_template_v3.py
```

Output: `church_style_output.pptx`

## System Status

All major features are working:
✅ Template modification approach preserves all formatting
✅ Lyrics extraction with Grok AI
✅ Presentation generation with proper slide duplication
✅ Date updates on title slide
✅ No bullet points in lyrics
✅ Proper line-per-slide logic
