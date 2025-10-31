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


def create_church_presentation_v3(lyrics_list, song_names, lines_per_slide=4):
    """
    Create a church-styled presentation by modifying template directly.
    This preserves all original formatting.
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

    # Process each song
    for song_idx, (lyrics, song_name) in enumerate(zip(lyrics_list, song_names)):
        print(f"  Processing '{song_name}'...")

        # Clean and process lyrics
        lyrics = lyrics.replace('---SLIDE---', '\n\n')
        lyrics_lines = []

        for line in lyrics.split('\n'):
            line = line.strip()
            if line and not line.startswith('---'):
                lyrics_lines.append(line)

        # Create slides for this song
        total_lines = len(lyrics_lines)

        for i in range(0, total_lines, lines_per_slide):
            slide_lines = lyrics_lines[i:i + lines_per_slide]
            slide_text = '\n'.join(slide_lines)

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
                                    run.text = song_name
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
                        current_slide_num = i // lines_per_slide + 1
                        total_slides = (total_lines + lines_per_slide - 1) // lines_per_slide
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
    # Test
    test_lyrics = [
        """Amazing grace, how sweet the sound
That saved a wretch like me
I once was lost but now am found
Was blind, but now I see"""
    ]
    test_songs = ["Amazing Grace"]

    create_church_presentation_v3(test_lyrics, test_songs, lines_per_slide=4)
