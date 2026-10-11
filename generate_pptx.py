import os
import re
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt

def parse_markdown(md_path: Path):
    """Parse markdown file into list of slide dicts with title and body lines."""
    with md_path.open("r", encoding="utf-8") as f:
        content = f.read()
    # Split slides by '---' delimiter
    raw_slides = [s.strip() for s in content.split('---') if s.strip()]
    slides = []
    for raw in raw_slides:
        lines = raw.splitlines()
        # First non‑empty line that starts with ## is the title
        title = "Slide"
        body = []
        for i, line in enumerate(lines):
            if line.startswith('##'):
                title = line.lstrip('#').strip()
                # The rest of the lines after title become body
                body = [l for l in lines[i+1:] if l.strip()]
                break
        slides.append({"title": title, "body": body})
    return slides

def add_bullets(slide, lines):
    for line in lines:
        # Remove leading markdown bullet markers
        clean = re.sub(r'^[\-\*]\s+', '', line)
        # Skip Mermaid code blocks or empty lines
        if clean.startswith('```') or not clean:
            continue
        p = slide.shapes.title.text_frame.add_paragraph() if slide.shapes.title else None
        # Use the slide's placeholder for body text
        try:
            body_shape = slide.shapes.placeholders[1]
            tf = body_shape.text_frame
        except Exception:
            tf = slide.shapes.title.text_frame
        p = tf.add_paragraph()
        p.text = clean
        p.level = 0
        p.font.size = Pt(18)

def create_pptx(md_path: Path, pptx_path: Path):
    prs = Presentation()
    slides = parse_markdown(md_path)
    for slide_info in slides:
        slide_layout = prs.slide_layouts[1]  # Title & Content layout
        slide = prs.slides.add_slide(slide_layout)
        # Set title
        title_placeholder = slide.shapes.title
        title_placeholder.text = slide_info["title"]
        # Add bullet points
        add_bullets(slide, slide_info["body"])
    prs.save(pptx_path)

if __name__ == "__main__":
    project_root = Path(__file__).parent
    md_file = project_root / "Project_Overview.md"
    pptx_file = project_root / "Project_Overview.pptx"
    create_pptx(md_file, pptx_file)
    print(f"PPTX generated at {pptx_file}")
