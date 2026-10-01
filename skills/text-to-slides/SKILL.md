---
name: text-to-slides
description: "Turn a written text into an image-based slide deck (ODP, PPTX, PDF) for a talk."
---

# Text to Slides

Transform written documents into effective visual presentations through strategic framing, narrative architecture, and technical generation.

## Core Principle

**A presentation is NOT text read aloud.** It's a visual support accompanying speech. One central message, supported by images and short titles.

## When NOT to Use This Skill

- Highly technical presentations requiring complex data visualizations
- Presentations with extensive animations or multimedia
- Slides that are intentionally heterogeneous (each slide very different)
- Purely graphical presentations without narrative structure

## Process Overview

Follow these steps in order:

1. **Strategic framing** - Define context, audience, message
2. **Narrative architecture** - Build slide plan (titles only)
3. **Visual design** - Map images, define graphic rules
4. **Technical generation** - Produce ODP/PPTX/PDF files
5. **Verification** - Extract and visually check output
6. **Iteration** - Refine typography, contrast, positioning

## Step 1: Strategic Framing

**If the central message is not yet clear**, use the **message-framing** skill to:
- Analyze presentation context (format, function, audience, constraints)
- Extract candidate messages from source content
- Select optimal message through strategic filtering

**If message is already framed**, proceed directly to Step 2.

**One presentation = one central message only.** All slides must serve this message.

**Example (AMAP case):**
- Context: 15min AG opening, motivate members
- Message: "What we already do in AMAP aligns with climate recommendations"
- Rationale: Motivating, recognizes existing practice, suitable for opening

## Step 2: Narrative Architecture

### 2.1 Build Slide Plan (Titles Only)

**Quantitative constraint**: ~1 slide per 2-3 minutes of speech

**Classic narrative structure**:
1. **Anchor** - Why this topic here/now?
2. **Problem** - What tension/difficulty?
3. **Context** - Are all actors equal?
4. **Solution** - What does established knowledge say?
5. **Recognition** - What are we already doing?
6. **Perspective** - Where does this lead?

**Example (AMAP, 6 slides for 15min):**
1. Why discuss climate in an AMAP?
2. The real problem: instability (not average temperature)
3. All agricultural systems don't react the same
4. What science recommends
5. What we already do in AMAP corresponds
6. AMAP as transition already in action

### 2.2 Validate Narrative Thread

**Robustness test:**
- Read titles aloud without the rest
- If logic isn't clear → rework
- If a slide doesn't serve central message → delete

**Rules:**
- Each title = **one idea**, not a paragraph
- Maximum 2 lines per title
- No "catch-all" slides

## Step 3: Visual Design

### 3.1 Define Visual Register

**Binary decision:**

| Approach | When to Use | Risks |
|----------|-------------|-------|
| **Authentic photos** | Local anchoring, field credibility | Variable quality |
| **Generic images** | Universal message, pro aesthetic | Coldness, stock photo feel |
| **Charts/data** | Quantitative argument | Cognitive overload |
| **Icons/diagrams** | Abstract concepts | Infantilization, corporate clipart |

**Decision framework:**
- Local/specific topic → Authentic photos
- Abstract/universal topic → Icons/diagrams
- Data-heavy argument → Charts (but keep simple)

### 3.2 Map Visuals ↔ Slides (1:1)

**Principle**: One slide = **one image**, not a collage

Method:
1. Inventory available visuals
2. Precise mapping: which visual illustrates which idea?
3. Arbitrate ambiguities

**Example (AMAP, slides 4-5 arbitration):**
- Slide 4: "What science recommends"
  - Candidates: bio sign, diverse vegetables
  - Choice: bio sign (frame/principles)
- Slide 5: "What we already do"
  - Choice: vegetable shelves (concrete collective recognition)
- Logic: slide 4 = abstract frame, slide 5 = concrete practice

### 3.3 Define Graphic Rules (Design System)

**Parameters to fix:**

| Element | Decisions | Example AMAP |
|---------|-----------|--------------|
| **Format** | 4:3 or 16:9 | 16:9 |
| **Layout** | Repeated structure | Full-screen image + title bottom-left |
| **Typography** | Font, size, weight, color | Source Sans 3, 32-36pt, bold, #F5F5F5 |
| **Positioning** | Fixed coordinates | x=1.7cm, y=12.9cm |
| **Contrast** | Background, overlay, shadow | Black overlay 45% opacity |
| **Ornaments** | Logos, frames, icons | **None** (sobriety) |

**Golden rule**: **Consistency > originality**

Better 6 identical slides than a patchwork.

### 3.4 The Semi-Transparent Overlay Problem

**Problem**: White text on image → variable readability depending on background

**Solutions (by robustness order):**

1. **Semi-transparent overlay** (optimal)
   - Black background 40-50% opacity under text
   - Guarantees readability on all backgrounds
   - **Always implement this**

2. **Drop shadow** (fallback)
   - Text with light black shadow
   - Less robust on complex backgrounds

3. **White text alone** (insufficient)
   - Only works on dark backgrounds
   - Fails on sunrise, light signs
   - **Never use without overlay**

## Step 4: Technical Generation

### 4.1 Choose Generation Tool

**Recommended: python-pptx → conversion**

Reasons:
- Intuitive API, rich documentation
- PPTX widely compatible
- Easy LibreOffice conversion to ODP

Alternative (ODP native):
- Use `odfpy` if strict ODP requirement
- More complex API, sparse documentation
- See `references/odfpy_example.md` for working script (python-pptx alternative: `references/pptx_example.md`)

### 4.2 Handle Image Assets

**Technical checklist:**

1. **Minimum resolution**: 1920×1080 for 16:9 full-screen
   - If lower → upscale with ImageMagick:
   ```bash
   convert input.jpg -resize 1920x1080^ -gravity center -extent 1920x1080 output.jpg
   ```

2. **Supported formats**:
   - Universal: JPG, PNG
   - Modern: WebP → convert to JPG
   - Problematic: AVIF (variable support) → convert

3. **Size**: Target <500KB per image after processing

### 4.3 Implement Design System

**Code architecture (python-pptx):**

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_VERTICAL_ANCHOR
from pptx.dml.color import RGBColor

# Define constants BEFORE loop
SLIDE_WIDTH = Inches(10)
SLIDE_HEIGHT = Inches(5.625)  # 16:9
TITLE_X = SLIDE_WIDTH * 0.08
TITLE_Y = SLIDE_HEIGHT * 0.72
TITLE_WIDTH = SLIDE_WIDTH * 0.85
TITLE_HEIGHT = SLIDE_HEIGHT * 0.23
FONT_SIZE = Pt(36)
FONT_COLOR = RGBColor(245, 245, 245)  # #F5F5F5

# Create presentation
prs = Presentation()
prs.slide_width = SLIDE_WIDTH
prs.slide_height = SLIDE_HEIGHT
blank_layout = prs.slide_layouts[6]

# Loop on slides
for slide_data in SLIDES:
    slide = prs.slides.add_slide(blank_layout)
    
    # Full-screen image
    slide.shapes.add_picture(
        slide_data["image"], 0, 0,
        width=SLIDE_WIDTH, height=SLIDE_HEIGHT
    )
    
    # Title with overlay
    # Note: python-pptx doesn't support semi-transparent shapes directly
    # Workaround: pre-process images with overlay or use odfpy
    
    textbox = slide.shapes.add_textbox(TITLE_X, TITLE_Y, TITLE_WIDTH, TITLE_HEIGHT)
    text_frame = textbox.text_frame
    text_frame.word_wrap = True
    text_frame.vertical_anchor = MSO_VERTICAL_ANCHOR.BOTTOM
    
    p = text_frame.paragraphs[0]
    p.text = slide_data["title"]
    p.alignment = PP_ALIGN.LEFT
    p.line_spacing = 1.0
    
    for run in p.runs:
        run.font.name = 'Source Sans 3'
        run.font.size = FONT_SIZE
        run.font.bold = True
        run.font.color.rgb = FONT_COLOR

prs.save("output.pptx")
```

**Critical limitation python-pptx**: No native semi-transparent shape support. Options:
1. Pre-process images with overlay using PIL/Pillow
2. Use odfpy for native ODP with overlay (see `references/odfpy_example.md`)
3. Accept limitation and use only white text (not recommended)

### 4.4 Semi-Transparent Overlay Implementation (odfpy)

For proper overlay support, use odfpy. See `references/odfpy_example.md` for complete working script with:

```python
# Title box style (black, 45% opacity)
title_box_style = Style(name="TitleBox", family="graphic")
title_box_style.addElement(GraphicProperties(
    fill="solid",
    fillcolor="#000000",
    opacity="45%",
    stroke="none"
))
doc.automaticstyles.addElement(title_box_style)

# Apply to frame
title_frame = Frame(
    anchortype="page",
    x="1.7cm", y="12.9cm",
    width="25.0cm", height="2.6cm",
    stylename=title_box_style
)
```

## Step 5: Verification

### 5.1 Validation Workflow

**Pipeline:**
```
Generation → Export PDF → Extract PNG → Visual verification
```

**Commands:**
```bash
# Generation
python3 generate_slides.py  # → output.pptx or output.odp

# PDF export
libreoffice --headless --convert-to pdf output.odp

# Preview extraction
pdftoppm output.pdf preview -png -scale-to-x 1000
```

### 5.2 Quick Verification

**Essential checks only:**
- [ ] All images loaded?
- [ ] Text readable at 6-7m distance?
- [ ] Overlay/contrast sufficient on all backgrounds?
- [ ] Typography consistent across all slides?

**For comprehensive diagnostic**, use **slides-review** skill which provides:
- 12 detailed checks (narrative, visual, technical)
- Prioritized issue list (critical → important → polish)
- Specific fix recommendations

### 5.3 Never Announce Success Without Looking

**Critical rule**: Never announce success without having **looked** at final rendering.

**Correct process:**
1. Generate → Export PDF → Extract PNG
2. **Visually inspect** extracted images
3. If issues → iterate (Step 6)
4. Only then announce completion

## Step 6: Iteration

### Quick Fixes for Common Issues

**Typography problems:**

| Symptom | Quick fix |
|---------|-----------|
| Text overflows bottom | Reduce font 4-6pt |
| Text illegible | Increase font 4-6pt OR simplify title |
| Text on 3+ lines | Reformulate (max 2 lines) |

**Contrast problems:**
- Increase overlay opacity: 45% → 55%
- Test on lightest background first

**For comprehensive diagnostic and prioritized improvements**, use **slides-review** skill:
- Multi-level analysis (narrative, visual, technical)
- Identifies root causes vs symptoms
- Provides specific fix roadmap

## Deliverables

### File Formats

Provide multiple formats:

| Format | Usage | Priority |
|--------|-------|----------|
| **.odp** | LibreOffice editable | ✓ Primary |
| **.pptx** | Microsoft editable | Optional |
| **.pdf** | Universal projection, archiving | ✓ Primary |
| **generation script** | Reproducibility, documentation | ✓ Primary |

### Script Documentation

Always include generation script with:
- Clear dependencies (versions)
- Execution instructions
- Parameter documentation
- Design choices rationale

## Common Errors to Avoid

Quick reference of critical mistakes:

1. ❌ Copy-paste text on slides → ✓ One message, visual support
2. ❌ Bullet points everywhere → ✓ One image + one title max
3. ❌ No overlay on variable backgrounds → ✓ 40-50% opacity always
4. ❌ Inconsistent layout → ✓ Same structure all slides
5. ❌ No verification → ✓ Always extract and inspect PDF
6. ❌ Titles 3+ lines → ✓ Max 2 lines, one idea

**For detailed diagnostics and fixes**, see **slides-review** skill.

## Tool Comparison

| Criterion | python-pptx + conversion | odfpy native | LaTeX Beamer |
|-----------|-------------------------|--------------|--------------|
| **API ease** | ★★★★☆ | ★★☆☆☆ | ★★☆☆☆ |
| **Native format** | PPTX | ODP | PDF |
| **Semi-transparent overlay** | ✗ (workaround needed) | ★★★★★ | ★★★☆☆ |
| **Learning curve** | Low | Medium | High |
| **Documentation** | Excellent | Sparse | Excellent |
| **Reproducibility** | ★★★★★ | ★★★★★ | ★★★★★ |

**General recommendation:**
- **Beginner**: python-pptx (intuitive API, rich doc)
- **Strict LibreOffice**: odfpy (but read ODF spec first)
- **Academic**: LaTeX Beamer (typo quality, publications)
