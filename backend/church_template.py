"""
Church Template V3 - Working approach that preserves all formatting
Instead of copying slides, we modify the template directly
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from datetime import datetime
import os
import shutil
from copy import deepcopy


def insert_blank_separator(prs, separator_template):
    """
    Insert a blank black separator slide using template formatting.
    Copies the separator template and removes all text shapes.
    """
    template_layout = separator_template.slide_layout
    new_slide = prs.slides.add_slide(template_layout)

    # Remove all shapes to make it blank
    for shape in list(new_slide.shapes):
        sp = shape.element
        sp.getparent().remove(sp)

    return new_slide


def deduplicate_slides(slide_texts):
    """
    Smart deduplication of slide content.
    - Removes consecutive duplicate slides (keeps first occurrence)
    - Returns list of unique slide texts in order

    Example:
    Input:  ["Verse 1", "Chorus", "Chorus", "Verse 2", "Chorus"]
    Output: ["Verse 1", "Chorus", "Verse 2", "Chorus"]

    The pastor doesn't need to flip through identical slides back-to-back.
    """
    if not slide_texts:
        return []

    deduplicated = [slide_texts[0]]

    for slide_text in slide_texts[1:]:
        # Normalize for comparison (strip whitespace, lowercase)
        current_normalized = slide_text.strip().lower()
        prev_normalized = deduplicated[-1].strip().lower()

        # Only add if different from previous slide
        if current_normalized != prev_normalized:
            deduplicated.append(slide_text)
        else:
            print(f"    ⏭️ Skipping duplicate slide (same as previous)")

    return deduplicated


def create_church_presentation_v3(lyrics_list, song_names, lines_per_slide=4):
    """
    Create a church-styled presentation by modifying template directly.
    This preserves all original formatting.

    Smart features:
    - Deduplicates consecutive identical slides (chorus repeated back-to-back)
    - Keeps the flow natural for worship leaders
    """
    template_path = os.path.join(os.path.dirname(__file__), '..', 'reference_template.pptx')

    # Create a working copy of the template
    temp_working_path = os.path.join(os.path.dirname(__file__), '..', 'temp_working.pptx')
    shutil.copy(template_path, temp_working_path)

    print("Loading template...")
    prs = Presentation(temp_working_path)

    print(f"Original template has {len(prs.slides)} slides")
    print()

    # Keep only the first 3 slides (title, welcome, lyrics template)
    print("Keeping first 3 slides as base...")
    slides_to_keep = 3
    while len(prs.slides) > slides_to_keep:
        rId = prs.slides._sldIdLst[-1].rId
        prs.part.drop_rel(rId)
        del prs.slides._sldIdLst[-1]

    print(f"Now have {len(prs.slides)} slides")
    print()

    # Update date on first slide
    print("Updating date on title slide...")
    date_str = datetime.now().strftime("%d %b'%y")

    for shape in prs.slides[0].shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text
            # Look for date pattern with apostrophe or month names
            if "'" in text or any(month in text for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                # Replace the entire text frame to avoid duplication
                shape.text_frame.text = date_str
                print(f"  Updated date to: {date_str}")
                break

    print()
    print("Creating lyrics slides...")

    # Get the lyrics template slide (slide 3)
    lyrics_template_slide = prs.slides[2]

    # Store separator template (Slide 2 - Welcome slide)
    separator_template_slide = prs.slides[1]

    # Process each song
    for song_idx, (lyrics, song_name) in enumerate(zip(lyrics_list, song_names)):
        # Insert separator slide BEFORE songs 2, 3, 4, etc. (not before first song)
        if song_idx > 0:
            insert_blank_separator(prs, separator_template_slide)
            print(f"  Inserted separator slide before song {song_idx + 1}")

        # Clean song name: remove " by Artist" for display
        display_title = song_name.split(' by ')[0].strip()

        print(f"  Processing '{display_title}'...")

        # Parse lyrics - respect AI's ---SLIDE--- groupings
        # Split by ---SLIDE--- marker to get pre-grouped sections
        sections = lyrics.split('---SLIDE---')

        # Build slide texts from sections
        all_slide_texts = []
        for section in sections:
            # Clean section: remove ---TITLE---, ---LYRICS--- markers and empty lines
            section_lines = []
            for line in section.split('\n'):
                line = line.strip()
                if line and not line.startswith('---'):
                    section_lines.append(line)

            if not section_lines:
                continue

            # If section has more lines than lines_per_slide, split it
            if len(section_lines) > lines_per_slide:
                for i in range(0, len(section_lines), lines_per_slide):
                    chunk = section_lines[i:i + lines_per_slide]
                    if chunk:
                        all_slide_texts.append('\n'.join(chunk))
            else:
                all_slide_texts.append('\n'.join(section_lines))

        # Smart deduplication - remove consecutive identical slides
        unique_slide_texts = deduplicate_slides(all_slide_texts)

        print(f"    📊 {len(all_slide_texts)} raw slides → {len(unique_slide_texts)} unique slides")

        total_slides = len(unique_slide_texts)

        for slide_idx, slide_text in enumerate(unique_slide_texts):

            # Duplicate the lyrics template slide using its own layout
            # Use the same layout as the template to preserve structure
            template_layout = lyrics_template_slide.slide_layout
            new_slide = prs.slides.add_slide(template_layout)

            # Remove all existing shapes from the new slide
            for shape in list(new_slide.shapes):
                sp = shape.element
                sp.getparent().remove(sp)

            # Deep copy all shapes from template
            for shape in lyrics_template_slide.shapes:
                el = shape.element
                newel = deepcopy(el)
                new_slide.shapes._spTree.insert_element_before(newel, 'p:extLst')

            # Now replace text in the new slide
            for shape in new_slide.shapes:
                if shape.has_text_frame:
                    # Get position to determine what type of text this is
                    # Title text (small text at top)
                    if shape.top < Inches(1):
                        for paragraph in shape.text_frame.paragraphs:
                            for run in paragraph.runs:
                                if run.text.strip():
                                    run.text = display_title
                                    break
                    # Main lyrics text (large text in middle)
                    elif Inches(1) < shape.top < Inches(4.5):
                        # Clear existing text and set new lyrics
                        shape.text_frame.text = slide_text

                        # Remove bullet formatting from all paragraphs
                        for paragraph in shape.text_frame.paragraphs:
                            # Remove bullets by clearing the paragraph properties
                            if hasattr(paragraph, '_element') and paragraph._element is not None:
                                pPr = paragraph._element.get_or_add_pPr()
                                # Remove bullet character element if it exists
                                buChar = pPr.find('.//a:buChar', {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'})
                                if buChar is not None:
                                    pPr.remove(buChar)
                                # Set buNone to explicitly have no bullets
                                from pptx.oxml.ns import qn
                                buNone = pPr.find(qn('a:buNone'))
                                if buNone is None:
                                    from pptx.oxml import parse_xml
                                    buNone = parse_xml('<a:buNone xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>')
                                    pPr.insert(0, buNone)
                    # Slide number (small text at bottom right)
                    elif shape.top > Inches(4.5) and shape.left > Inches(7):
                        current_slide_num = slide_idx + 1
                        for paragraph in shape.text_frame.paragraphs:
                            for run in paragraph.runs:
                                run.text = f"{current_slide_num}/{total_slides}"
                                break

    # Delete slide 3 (the template slide) after we're done using it
    print()
    print("Removing template slide (slide 3)...")
    # Get the slide ID for slide 3 (index 2)
    slide_id = prs.slides._sldIdLst[2]
    prs.part.drop_rel(slide_id.rId)
    del prs.slides._sldIdLst[2]

    # Save presentation
    output_path = os.path.join(os.path.dirname(__file__), '..', 'church_style_output.pptx')
    prs.save(output_path)

    # Clean up temp file
    try:
        os.remove(temp_working_path)
    except:
        pass

    print()
    print(f"✅ Presentation saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    # Test with repeated chorus to demonstrate deduplication
    test_lyrics = [
        """---TITLE---
Amazing Grace
---LYRICS---
Amazing grace, how sweet the sound
That saved a wretch like me
I once was lost but now am found
Was blind, but now I see
---SLIDE---
'Twas grace that taught my heart to fear
And grace my fears relieved
How precious did that grace appear
The hour I first believed
---SLIDE---
Amazing grace, how sweet the sound
That saved a wretch like me
I once was lost but now am found
Was blind, but now I see
---SLIDE---
Amazing grace, how sweet the sound
That saved a wretch like me
I once was lost but now am found
Was blind, but now I see
---SLIDE---
Through many dangers, toils and snares
I have already come
'Tis grace hath brought me safe thus far
And grace will lead me home"""
    ]
    test_songs = ["Amazing Grace"]

    print("Testing smart deduplication...")
    print("Input has 5 slides, with slides 1, 3, 4 being identical (chorus repeated)")
    print("Expected output: 4 unique slides (consecutive duplicates removed)")
    print()

    create_church_presentation_v3(test_lyrics, test_songs, lines_per_slide=4)
