# Design: Song Separator Slides & Title Cleanup

**Date**: 2025-02-11
**Status**: Approved
**File**: `backend/church_template.py`

## Overview
Two improvements to enhance the church worship presentation:
1. Add blank black separator slides between songs
2. Remove artist names from song titles on lyrics slides

## Feature 1: Black Separator Slides

### Requirements
- Insert a blank black slide between each song (not before the first song)
- Use template formatting from Slide 2 (Welcome slide)
- Maintain all theme colors, backgrounds, and master slide references

### Implementation Approach
- Copy Slide 2 from template as separator base
- Remove all text shapes to create blank black slide
- Insert separator only between songs (song_idx > 0)

### Example Flow (3 songs)
```
Slide 1: Title (Sunday Service + date)
Slide 2: Welcome
Slides 3-6: Song 1 lyrics (4 slides)
Slide 7: [BLACK SEPARATOR] ← inserted
Slides 8-11: Song 2 lyrics (4 slides)
Slide 12: [BLACK SEPARATOR] ← inserted
Slides 13-16: Song 3 lyrics (4 slides)
```

### Code Changes
1. Store reference to Slide 2 as separator template
2. Create `insert_blank_separator()` helper function
3. In song processing loop, insert separator when `song_idx > 0`

## Feature 2: Remove Artist Names from Titles

### Requirements
- Display only song name on lyrics slides, not "Song by Artist"
- Clean at presentation generation time
- Preserve all text formatting (font, size, color)

### Implementation Approach
- Split song_name on " by " delimiter
- Take first part as display title
- Apply to all lyrics slides for that song

### Example Transformations
- "Amazing Grace by John Newton" → "Amazing Grace"
- "How Great Thou Art by Carl Boberg" → "How Great Thou Art"
- "Oceans" → "Oceans" (unchanged if no artist)

### Code Changes
1. Before song processing loop, add: `display_title = song_name.split(' by ')[0].strip()`
2. Use `display_title` instead of `song_name` when setting title text

## Technical Details

### Helper Function
```python
def insert_blank_separator(prs, separator_template):
    """Insert a blank black separator slide using template formatting"""
    template_layout = separator_template.slide_layout
    new_slide = prs.slides.add_slide(template_layout)

    # Remove all shapes to make it blank
    for shape in list(new_slide.shapes):
        sp = shape.element
        sp.getparent().remove(sp)

    return new_slide
```

### Modified Song Loop
```python
# Store separator template
separator_template_slide = prs.slides[1]  # Slide 2

# Process each song
for song_idx, (lyrics, song_name) in enumerate(zip(lyrics_list, song_names)):

    # Insert separator BEFORE songs 2, 3, 4, etc.
    if song_idx > 0:
        insert_blank_separator(prs, separator_template_slide)
        print(f"  Inserted separator slide before song {song_idx + 1}")

    # Clean title: remove artist name
    display_title = song_name.split(' by ')[0].strip()

    print(f"  Processing '{display_title}'...")

    # ... rest of song processing ...
    # Use display_title when setting title text (around line 107)
```

## Testing Strategy

### Unit Test
- Create presentation with 3 test songs
- Verify separator count: 2 separators (between songs 1-2 and 2-3)
- Verify separator slides are completely blank
- Verify titles display without artist names

### Integration Test
- Run full workflow through frontend
- Generate presentation for 5 songs
- Manually inspect PowerPoint:
  - Separator slides maintain black background
  - No text/shapes visible on separators
  - Song titles clean (no "by Artist")
  - All formatting preserved

### Success Criteria
- ✅ Separator slides inserted only between songs
- ✅ Separators are blank with template formatting
- ✅ Song titles show only song name (no artist)
- ✅ All existing formatting preserved
- ✅ No regressions in date update, bullet removal, etc.

## Impact Analysis

### Files Modified
- `backend/church_template.py` - Only file requiring changes

### Backward Compatibility
- Fully backward compatible
- No API changes
- No frontend changes
- No database/data format changes

### Performance Impact
- Negligible (2 extra slides per song, O(n) operations)
- Separator insertion: ~10ms per slide
- Title string split: <1ms

## Deployment Notes
- No configuration changes needed
- No database migrations
- Test with actual church template before Sunday service
- Keep backup of previous version if rollback needed
