# python-pptx example: image slides with titles

Worked example from one talk, not a shipped tool. Needs `python-pptx`. No native semi-transparent overlay; convert to ODP through LibreOffice if needed. Prefer the odfpy approach (`references/odfpy_example.md`) for overlays.

```python
#!/usr/bin/env python3
"""
Création présentation PPTX puis conversion ODP
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_VERTICAL_ANCHOR
from pptx.dml.color import RGBColor
import os

def create_presentation():
    """Créer présentation PPTX"""
    
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(5.625)  # 16:9
    
    # Supprimer layouts par défaut
    blank_layout = prs.slide_layouts[6]  # Blank layout
    
    slides_content = [
        {
            "image": "images_processed/slide1.jpg",
            "title": "Pourquoi parler de climat\ndans une AMAP ?"
        },
        {
            "image": "images_processed/slide2.jpg",
            "title": "Pour l'agriculture, le vrai problème\nn'est pas la chaleur, mais l'instabilité"
        },
        {
            "image": "images_processed/slide3.jpg",
            "title": "Tous les systèmes agricoles\nne réagissent pas de la même façon"
        },
        {
            "image": "images_processed/slide4.jpg",
            "title": "Ce que la science recommande pour\nune alimentation compatible avec le climat"
        },
        {
            "image": "images_processed/slide5.jpg",
            "title": "Ce que nous faisons déjà en AMAP\ncorrespond à ces recommandations"
        },
        {
            "image": "images_processed/slide6.jpg",
            "title": "L'AMAP : une transition alimentaire\ndéjà en action"
        }
    ]
    
    for slide_data in slides_content:
        slide = prs.slides.add_slide(blank_layout)
        
        # Image plein écran
        slide.shapes.add_picture(
            slide_data["image"],
            0, 0,
            width=prs.slide_width,
            height=prs.slide_height
        )
        
        # Titre bas gauche
        left = prs.slide_width * 0.08
        top = prs.slide_height * 0.72
        width = prs.slide_width * 0.85
        height = prs.slide_height * 0.23
        
        textbox = slide.shapes.add_textbox(left, top, width, height)
        text_frame = textbox.text_frame
        text_frame.word_wrap = True
        text_frame.vertical_anchor = MSO_VERTICAL_ANCHOR.BOTTOM
        
        # Paragraphe
        p = text_frame.paragraphs[0]
        p.text = slide_data["title"]
        p.alignment = PP_ALIGN.LEFT
        p.line_spacing = 1.0
        
        # Format texte
        for run in p.runs:
            run.font.name = 'Source Sans 3'
            run.font.size = Pt(36)
            run.font.bold = True
            run.font.color.rgb = RGBColor(245, 245, 245)  # #F5F5F5
    
    return prs

if __name__ == "__main__":
    print("Création PPTX...")
    prs = create_presentation()
    
    pptx_path = "AMAP_climat.pptx"
    prs.save(pptx_path)
    print(f"✓ PPTX créé: {pptx_path} ({os.path.getsize(pptx_path)/1024:.1f} Ko)")
```
