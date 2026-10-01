# odfpy example: ODP with semi-transparent overlay

Worked example, not a shipped tool. Needs `odfpy` (`pip install odfpy`).

```python
#!/usr/bin/env python3
"""
Working example of ODP generation with semi-transparent overlay using odfpy.

This script demonstrates the correct approach for creating LibreOffice Impress
presentations with proper contrast management through semi-transparent overlays.

Requirements:
  - python3
  - odfpy: pip install odfpy
  - LibreOffice (for PDF export): soffice in PATH

Usage:
  python3 odfpy_example.py
"""

from odf.opendocument import OpenDocumentPresentation
from odf.style import (
    Style, MasterPage, PageLayout, PageLayoutProperties,
    GraphicProperties, TextProperties, ParagraphProperties
)
from odf.draw import Page, Frame, Image, TextBox
from odf.text import P
from odf import teletype
import subprocess
import pathlib
import shutil

# Configuration
SLIDES = [
    ("Example Slide 1", "/path/to/image1.jpg"),
    ("Example Slide 2", "/path/to/image2.jpg"),
]

OUT_ODP = "example_output.odp"
OUT_PDF = "example_output.pdf"

# 16:9 widescreen dimensions (LibreOffice standard)
PAGE_W = "28.575cm"
PAGE_H = "16.065cm"

def build_odp(output_path: str):
    """Build ODP presentation with proper overlay support."""
    
    doc = OpenDocumentPresentation()
    
    # Page layout (16:9)
    pl = PageLayout(name="WidescreenLayout")
    pl.addElement(PageLayoutProperties(
        pagewidth=PAGE_W,
        pageheight=PAGE_H,
        printorientation="landscape"
    ))
    doc.automaticstyles.addElement(pl)
    
    # Master page
    mp = MasterPage(name="Default", pagelayoutname=pl)
    doc.masterstyles.addElement(mp)
    
    # Title text style
    title_style = Style(name="TitleText", family="paragraph")
    title_style.addElement(TextProperties(
        fontfamily="Liberation Sans",
        fontsize="32pt",
        fontweight="bold",
        color="#F5F5F5"  # Off-white for better rendering
    ))
    title_style.addElement(ParagraphProperties(textalign="left"))
    doc.styles.addElement(title_style)
    
    # Title box style (black semi-transparent overlay)
    # This is the critical element for readability
    title_box_style = Style(name="TitleBox", family="graphic")
    title_box_style.addElement(GraphicProperties(
        fill="solid",
        fillcolor="#000000",
        opacity="45%",  # 40-50% is optimal range
        stroke="none"
    ))
    doc.automaticstyles.addElement(title_box_style)
    
    # Generate slides
    for i, (title, img_path) in enumerate(SLIDES, start=1):
        page = Page(masterpagename=mp, name=f"Slide{i}", stylename=pl)
        doc.presentation.addElement(page)
        
        # Full-bleed background image
        img_frame = Frame(
            anchortype="page",
            x="0cm",
            y="0cm",
            width=PAGE_W,
            height=PAGE_H
        )
        href = doc.addPicture(img_path)
        img_frame.addElement(Image(href=href))
        page.addElement(img_frame)
        
        # Title frame with overlay (bottom-left positioning)
        title_frame = Frame(
            anchortype="page",
            x="1.7cm",      # 6% from left
            y="12.9cm",     # Near bottom (page height - title height - margin)
            width="25.0cm", # 85% of page width
            height="2.6cm", # Enough for 2 lines at 32pt
            stylename=title_box_style  # Apply semi-transparent overlay
        )
        
        # Text box with title
        tb = TextBox()
        p = P(stylename=title_style)
        teletype.addTextToElement(p, title)
        tb.addElement(p)
        title_frame.addElement(tb)
        page.addElement(title_frame)
    
    doc.save(output_path)

def export_pdf(input_odp: str, output_pdf: str):
    """Export ODP to PDF using LibreOffice headless."""
    
    outdir = pathlib.Path(output_pdf).parent
    cmd = [
        "soffice",
        "--headless",
        "--nologo",
        "--nolockcheck",
        "--convert-to", "pdf",
        "--outdir", str(outdir),
        input_odp
    ]
    subprocess.check_output(cmd)
    
    # Handle naming
    produced = outdir / pathlib.Path(input_odp).with_suffix(".pdf").name
    if produced != pathlib.Path(output_pdf):
        shutil.move(produced, output_pdf)

def main():
    """Main execution."""
    
    print("Building ODP with semi-transparent overlays...")
    build_odp(OUT_ODP)
    print(f"✓ Created: {OUT_ODP}")
    
    print("Exporting to PDF...")
    export_pdf(OUT_ODP, OUT_PDF)
    print(f"✓ Created: {OUT_PDF}")

if __name__ == "__main__":
    main()

# Key differences from python-pptx approach:
#
# 1. OVERLAY SUPPORT: odfpy natively supports semi-transparent overlays
#    through GraphicProperties(fill="solid", fillcolor="#000000", opacity="45%")
#
# 2. COORDINATE SYSTEM: Uses centimeters directly, not Inches() conversion
#
# 3. STYLE DEFINITION: Styles defined once, applied via stylename parameter
#
# 4. ANCHOR TYPE: Uses anchortype="page" for absolute positioning
#
# 5. ODF COMPLIANCE: Uses correct ODF attribute names (fill, fillcolor, opacity)
#    not invalid attributes like horizontalalignment
#
# Common pitfalls to avoid:
# - Using non-existent ODF attributes (check spec: docs.oasis-open.org)
# - Forgetting master page (required for Page elements)
# - Wrong opacity syntax (use "45%" not 0.45)
# - Incorrect coordinate units (cm not inches)
```
