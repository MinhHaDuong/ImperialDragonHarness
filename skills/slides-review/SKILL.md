---
name: slides-review
description: "Diagnostic review of an existing slide deck (ODP, PPTX, PDF): critique and concrete improvements."
---

# Slides Review

Systematic analysis and improvement of existing slide decks through multi-level diagnostic review.

## Core Principle

**Good slides = Clear message + Consistent visuals + Technical excellence**

Review identifies gaps at three levels: narrative (message & flow), visual (design & consistency), and technical (readability & execution).

## When to Use This Skill

Use slides-review when:
- User has existing slides and wants feedback
- Quality assessment needed before important presentation
- Slides feel "off" but user can't identify why
- Iterative improvement of existing deck
- Learning from past presentations

**NOT for**:
- Creating slides from scratch → use text-to-slides
- Only needing message clarification → use message-framing
- Technical generation help → use text-to-slides

## Process Overview

1. **Load & Inventory** - Extract slides, understand structure
2. **Multi-level Diagnostic** - Analyze narrative, visual, technical
3. **Prioritize Issues** - Critical → Important → Polish
4. **Recommend Fixes** - Actionable improvements with references
5. **Iterate** - Apply fixes, re-review if needed

---

## Step 1: Load & Inventory

### 1.1 Extract Slide Content

**For PDF files:**
```bash
# Extract as images for visual inspection
pdftoppm presentation.pdf slide -png -scale-to-x 1200

# Count slides
pdfinfo presentation.pdf | grep Pages
```

**For ODP/PPTX files:**
```bash
# Convert to PDF first if needed
libreoffice --headless --convert-to pdf presentation.odp

# Then extract
```

### 1.2 Create Inventory

Document for each slide:
- **Slide number**
- **Title text** (if present)
- **Visual type** (photo, diagram, text-heavy, blank)
- **Apparent function** (intro, data, conclusion, transition)

**Example inventory:**
```
Slide 1: "Our Q4 Results" - Photo background - Opening
Slide 2: "Revenue Growth" - Bar chart - Data
Slide 3: "Key Challenges" - Bullet points - Problem
Slide 4: "Strategic Response" - Diagram - Solution
Slide 5: "Next Steps" - Text list - Action
```

### 1.3 Initial Observations

Quick scan for obvious patterns:
- Total slide count vs presentation duration (target: 1 slide / 2-3 min)
- Visual consistency (same layout repeated or each different?)
- Text density (titles only or paragraphs?)
- Central message apparent from titles alone?

---

## Step 2: Multi-Level Diagnostic

### 2.1 Narrative Level

**Goal**: Assess message clarity and logical flow

#### Check 1: Central Message Identifiable?

**Test**: Read all slide titles in sequence. Can you state the presentation's main point in one sentence?

**Good example:**
- Titles: "Why change?", "Current problems", "Our solution", "How it works", "Next steps"
- Message clear: "We should adopt solution X"

**Bad example:**
- Titles: "Background", "Analysis", "Data", "Trends", "Summary"  
- Message unclear: What's the takeaway?

**If message unclear** → Reference **message-framing** skill to help user clarify

---

#### Check 2: Narrative Progression

**Test**: Does each slide logically follow the previous?

**Flow patterns to verify:**
- Problem → Solution
- Past → Present → Future  
- Question → Answer
- General → Specific

**Red flags:**
- ❌ Random order (could shuffle and not notice)
- ❌ Missing links (slide 3 doesn't connect to slide 2)
- ❌ Circular logic (returns to same point)

---

#### Check 3: Title Quality

**Criteria for good titles:**
- ✓ One clear idea per title
- ✓ Maximum 2 lines
- ✓ States a claim, not just a topic
- ✓ Meaningful without the image

**Examples:**

| Bad | Good |
|-----|------|
| "Results" | "Revenue up 23% year-over-year" |
| "Background" | "Three factors drove this crisis" |
| "Data Analysis of Customer Satisfaction Survey Results Q3 2024" | "Customers want faster support" |

---

#### Check 4: Slide Count & Density

**Rules of thumb:**
- 1 slide per 2-3 minutes of presentation time
- More slides with less content > fewer slides packed dense

**Example:**
- 30-minute presentation with 40 slides = GOOD (brief slides)
- 30-minute presentation with 8 slides = WARNING (probably too dense)

**Exceptions**: Intentional "build" sequences acceptable

---

### 2.2 Visual Level

**Goal**: Assess design consistency and visual effectiveness

Reference **text-to-slides Step 3 (Visual Design)** for design system principles.

#### Check 5: Layout Consistency

**Test**: Are the same design elements repeated on every slide?

**What should be consistent:**
- Title position (same x,y coordinates)
- Font family, size, weight, color
- Image framing (full-screen, centered, sidebar)
- Margins and spacing

**Red flags:**
- ❌ Each slide different layout
- ❌ Title jumps around (left, center, right)
- ❌ Mixed fonts (Arial + Times + Comic Sans)
- ❌ Inconsistent image sizing

**Example diagnosis:**
> "Slides 1-3 have title top-left, slides 4-6 have title centered, slide 7 has no title. Inconsistent."

---

#### Check 6: Visual-Message Alignment

**Test**: Does each image support the slide's idea?

**Good alignment:**
- Slide about growth → image of upward trend
- Slide about team → photo of actual team
- Slide about problem → visual representation of issue

**Bad alignment:**
- Generic stock photos (smiling businesspeople)
- Decorative images unrelated to content
- Charts that don't support the claim

**Worst case**: Image contradicts message (slide says "success", image shows failure)

---

#### Check 7: One Idea Per Slide

**Test**: Can you summarize each slide in one sentence?

**If not** → Slide is trying to do too much

**Common violations:**
- Multiple bullet point lists on one slide
- "And also..." transitions within a slide
- Combining unrelated data visualizations

**Fix**: Split into multiple slides, each with single focus

---

#### Check 8: Bullet Point Overload

**Rule**: Bullet points are a design failure, not a design

**Acceptable**: 2-3 bullet points maximum, each very brief
**Unacceptable**: 6+ bullets, full sentences, sub-bullets

**Better alternatives:**
- One key statement as title, image as support
- Sequential reveals (1 slide per point)
- Visual diagram showing relationships

---

### 2.3 Technical Level

**Goal**: Assess readability and technical execution

Reference **text-to-slides Step 5 (Verification)** for technical standards.

#### Check 9: Text Readability

**Test**: Can you read the text from 6-7 meters away?

**Standards:**
- Title text: minimum 32-36pt
- Body text (if any): minimum 20-24pt
- Maximum 2 lines for titles

**Common problems:**
- Font too small (trying to fit too much text)
- Titles overflow to 3+ lines
- Text cramped with insufficient spacing

---

#### Check 10: Contrast & Overlay

**Test**: Is text readable on all slide backgrounds?

**Critical check**: Light backgrounds (photos with sky, white/light surfaces)

**Good practice:**
- Semi-transparent overlay (40-50% black) behind white text
- Dark overlay behind light text
- Consistent overlay across all slides

**Bad practice:**
- White text directly on variable backgrounds
- Hoping the background will be "dark enough"
- No overlay strategy

Reference **text-to-slides Step 4.4** for overlay implementation.

---

#### Check 11: Image Quality

**Standards:**
- No pixelation when projected
- Minimum 1920×1080 for 16:9 full-screen
- Proper aspect ratio (no stretching)

**Red flags:**
- ❌ Blurry images
- ❌ Stretched/squashed photos
- ❌ Low-resolution screenshots

---

#### Check 12: Typography Consistency

**What to check:**
- Same font family throughout (max 2 fonts: title + body)
- Consistent sizing (title always same size)
- Consistent color (#F5F5F5 white, not mix of white/#FFFFFF/#EEEEEE)
- Consistent weight (always bold, not mix bold/regular)

**Technical debt indicators:**
- Slides from different templates merged
- Copied content with formatting preserved
- Manual formatting instead of styles

---

## Step 3: Prioritize Issues

### 3.1 Critical Issues (Must Fix)

**Definition**: Blocks understanding or creates confusion

**Examples:**
- No identifiable central message
- Illogical slide progression  
- Text illegible (too small, poor contrast)
- Factual errors or contradictions

**Criterion**: If this isn't fixed, presentation will fail

---

### 3.2 Important Issues (Should Fix)

**Definition**: Degrades quality and professionalism

**Examples:**
- Visual inconsistency (layout jumps around)
- Bullet point overload
- Poor visual-message alignment
- Font sizes borderline readable

**Criterion**: Audience will notice, reduces impact

---

### 3.3 Polish Suggestions (Nice to Have)

**Definition**: Improvements that enhance polish

**Examples:**
- Title wording could be sharper
- Image choices could be more evocative
- Spacing/margins could be more generous
- Color palette could be more sophisticated

**Criterion**: Professionals would appreciate, most audiences won't notice

---

## Step 4: Recommend Fixes

### Output Format

For each identified issue, provide:

1. **Issue description** - What's wrong, where (slide numbers)
2. **Impact** - Why this matters for audience
3. **Fix** - Specific actionable recommendation
4. **Reference** - Link to relevant skill/section for execution

### Example Recommendations

**Issue 1 (Critical)**: No clear central message  
**Impact**: Audience won't remember takeaway  
**Fix**: Use **message-framing** skill to identify core message, then restructure slide titles to build toward that message  
**Execution**: Start with message-framing, then refer to text-to-slides Step 2 for narrative architecture

---

**Issue 2 (Critical)**: Text illegible on slides 3, 7, 12 (white text on light backgrounds)  
**Impact**: Audience can't read content  
**Fix**: Add semi-transparent black overlay (45% opacity) behind title text on all slides  
**Execution**: Refer to text-to-slides Step 4.4 for overlay implementation with odfpy or image preprocessing

---

**Issue 3 (Important)**: Inconsistent layout (slides 1-4 title top-left, slides 5-9 centered)  
**Impact**: Presentation feels unprofessional, distracting  
**Fix**: Standardize title position (recommend bottom-left, 8% from left edge, 72% from top)  
**Execution**: Refer to text-to-slides Step 3.3 for design system implementation

---

**Issue 4 (Important)**: Slides 8-11 have 6-8 bullet points each  
**Impact**: Cognitive overload, audience tunes out  
**Fix**: Extract one key idea per slide, split slide 8 into slides 8a-8c  
**Execution**: Refer to text-to-slides Step 2.1 for "one idea per slide" principle

---

**Issue 5 (Polish)**: Slide 6 title "Data" is too generic  
**Impact**: Minor - doesn't help audience understand  
**Fix**: Rephrase to claim, e.g., "Revenue grew 23% in Q4"  
**Execution**: Simple text edit

---

### Prioritized Summary Template

```markdown
## Critical Issues (Must Fix Before Presenting)

1. [Issue description]
   - Slides affected: [numbers]
   - Impact: [why critical]
   - Fix: [specific action]
   - Reference: [skill/section]

2. [...]

## Important Issues (Should Fix)

1. [Issue description]
   - Slides affected: [numbers]
   - Impact: [why important]
   - Fix: [specific action]
   - Reference: [skill/section]

2. [...]

## Polish Suggestions (Nice to Have)

1. [Issue description]
   - Slides affected: [numbers]
   - Enhancement: [what improves]
   - Fix: [specific action]

2. [...]
```

---

## Step 5: Iterate

### 5.1 Apply Fixes Systematically

**Process:**
1. Start with critical issues (order matters)
2. Fix message/narrative before visual refinement
3. Apply visual consistency before technical polish
4. Test readability after each major change

**Why this order:**
- No point polishing slides that will be restructured
- Visual consistency easier after narrative settled
- Technical execution last (implements design decisions)

---

### 5.2 Re-Review After Major Changes

**When to re-review:**
- After restructuring narrative (message/flow changes)
- After applying visual design system
- Before final presentation

**Partial re-review sufficient:**
- Only re-check sections that were modified
- Full narrative check even if only some slides changed

---

### 5.3 User Testing

**Best practice**: Present to test audience

**What to ask:**
- "What was the main message?" (should match your framed message)
- "Which slides were confusing?" (remaining issues)
- "What do you remember?" (memorability test)

**Incorporate feedback** → Re-review → Iterate

---

## Common Diagnostic Patterns

### Pattern 1: "Data Dump" Deck

**Symptoms:**
- Many slides with dense tables/charts
- No clear narrative
- Titles are generic ("Q1 Data", "Analysis")

**Root cause**: Confusing presentation with report

**Fix:**
- Extract 3-5 key insights from data
- Create narrative around insights
- Use data as supporting evidence, not primary content
- Consider: presentation for insights, appendix/handout for data

---

### Pattern 2: "Frankenstein" Deck

**Symptoms:**
- Visual inconsistency (different templates merged)
- Typography chaos (multiple fonts/sizes/colors)
- Looks like content from different sources

**Root cause**: Assembled from multiple existing decks

**Fix:**
- Define unified design system (text-to-slides Step 3.3)
- Rebuild all slides with consistent template
- May be faster to recreate than fix

---

### Pattern 3: "Essay on Slides"

**Symptoms:**
- Paragraphs of text on slides
- Presenter reads slides verbatim
- Bullet point lists everywhere

**Root cause**: Misunderstanding presentation vs document

**Fix:**
- Extract one claim per slide as title
- Remove body text (goes in speaker notes)
- Add visual support for each claim
- Refer to text-to-slides core principle

---

### Pattern 4: "Clip Art Special"

**Symptoms:**
- Generic stock photos (handshakes, lightbulbs)
- Decorative icons unrelated to content
- "Professional" template with gradients/shadows

**Root cause**: Trying to "jazz up" slides visually

**Fix:**
- Use authentic images that support message
- Remove decorative elements
- Embrace simplicity (text-to-slides Step 3.1: authentic over generic)

---

### Pattern 5: "Mystery Message"

**Symptoms:**
- Slides individually coherent but no clear arc
- Each slide seems fine in isolation
- After presentation, audience asks "so what?"

**Root cause**: No central message defined upfront

**Fix:**
- Use **message-framing** skill to identify core message
- Restructure slides to build toward message
- Each slide should serve the central message

---

## Red Flags Checklist

Quick diagnostic for common serious issues:

- [ ] **No central message identifiable** → Use message-framing
- [ ] **More than 20 slides for 15-min presentation** → Probably too dense
- [ ] **Fewer than 5 slides for 15-min presentation** → Probably too sparse
- [ ] **Paragraphs on slides** → Violates presentation principle
- [ ] **6+ bullet points on any slide** → Information overload
- [ ] **Text illegible from distance** → Technical failure
- [ ] **Each slide different layout** → Design inconsistency
- [ ] **Generic stock photos** → Weak visual strategy
- [ ] **Could shuffle slides randomly** → No narrative structure
- [ ] **Titles are topics not claims** → Weak messaging

**If 3+ red flags**: Major restructuring needed, not just polish.

---

## Special Cases

### Case 1: Inherited Deck (Not Your Content)

**Challenge**: You didn't create it, limited context

**Approach:**
1. Ask user: What's the intended message? (if unclear → message-framing)
2. Assess current deck against that message
3. Recommend changes that serve stated message
4. Don't impose your aesthetic preferences

---

### Case 2: Template-Constrained Deck

**Challenge**: Corporate template enforces certain design

**Approach:**
1. Work within template constraints
2. Focus on narrative and content quality
3. Improve what's controllable (titles, image choice, flow)
4. Document template limitations in review

---

### Case 3: Technical/Academic Presentation

**Challenge**: Complex content, specialized audience

**Approach:**
1. Don't oversimplify (audience has expertise)
2. Still enforce "one idea per slide"
3. Technical accuracy > visual polish
4. Data visualizations need extra care (clarity critical)

---

### Case 4: Already Good Deck (Polish Only)

**Challenge**: No major issues, just optimization

**Approach:**
1. Acknowledge quality ("This is already strong")
2. Focus on polish suggestions
3. Consider A/B testing (try two versions)
4. May suggest leaving as-is if changes marginal

---

## Integration with Other Skills

### When to Reference message-framing

**Trigger conditions:**
- No clear central message identifiable
- User uncertain about presentation focus
- Narrative restructuring needed

**Process:**
1. Identify issue: "Your deck lacks clear message"
2. Recommend: "Use message-framing skill to clarify"
3. After message framed → return to slides-review for restructuring

---

### When to Reference text-to-slides

**Trigger conditions:**
- Technical fixes needed (overlay, typography)
- Design system implementation needed
- Narrative architecture rebuild needed
- User wants to recreate from scratch

**What to reference:**
- Step 2: Narrative architecture
- Step 3: Visual design system
- Step 4: Technical generation
- Step 5: Verification checklists

**Process:**
1. Diagnose issue
2. Recommend specific text-to-slides section
3. User applies fix
4. Re-review modified section

---

## Limitations

**What this skill does NOT do:**
- Generate new slides (use text-to-slides)
- Frame message from scratch (use message-framing)
- Detailed content editing (focus is structure/design/readability)
- Fact-checking claims (assumes content accuracy)

**When to recommend starting over:**
- "Frankenstein" deck with 3+ merged templates
- Fundamental narrative problems (easier to rebuild than fix)
- When user says "I hate these slides"

---

## Output Quality Standards

### Good Review Delivers

✓ Clear diagnosis of what's wrong  
✓ Prioritized issues (critical → important → polish)  
✓ Specific actionable fixes  
✓ References to relevant skills/sections  
✓ Realistic about effort required  

### Good Review Avoids

✗ Vague feedback ("slides could be better")  
✗ Aesthetic preferences ("I don't like blue")  
✗ Overwhelming user (50 issues dumped at once)  
✗ Fixes without priority (treat all equal)  
✗ Criticism without constructive guidance  

---

## Examples

### Example 1: Corporate Quarterly Review

**Context**: 25 slides, 20-minute board presentation

**Critical Issues Found:**
1. No clear message (data presented without synthesis)
2. Slides 8-12 text illegible (8pt font in tables)

**Important Issues:**
1. Bullet point overload (slides 15-18 have 7-9 bullets each)
2. Inconsistent chart formatting

**Recommendation Priority:**
1. Extract key message: "Q3 exceeded targets, Q4 cautious" (message-framing)
2. Restructure around that message (text-to-slides Step 2)
3. Increase font size to minimum 20pt, simplify tables
4. Split bullet-heavy slides

---

### Example 2: Conference Talk

**Context**: 40 slides, 30-minute academic presentation

**Critical Issues Found:**
1. None (technically solid)

**Important Issues:**
1. Slide 12 title "Methods" too generic
2. Transition between sections abrupt (slide 19→20)

**Polish Suggestions:**
1. Slide 12 → "Three-stage analysis pipeline"
2. Add transition slide between sections
3. Consider: slightly larger title font (32pt → 36pt) for back-of-room readability

**Verdict**: Already strong, minor improvements only

---

### Example 3: Startup Pitch

**Context**: 15 slides, 10-minute investor pitch

**Critical Issues Found:**
1. Message unclear (product features vs investment opportunity)
2. No "ask" slide (what do you want from investors?)

**Important Issues:**
1. Slides 3-6 too technical for non-technical audience
2. No market size slide

**Recommendation:**
1. Frame message: "We solve X, market is Y, we need $Z" (message-framing)
2. Simplify technical slides (one benefit per slide, not features)
3. Add market sizing slide
4. Explicit ask slide at end

---

## Troubleshooting

**Problem**: User defensive about feedback  
**Solution**: Frame as "here's what I notice" not "this is wrong", acknowledge strengths first

**Problem**: Too many issues, user overwhelmed  
**Solution**: Show only critical issues first, offer to discuss important/polish after fixes applied

**Problem**: User wants different aesthetic than recommended  
**Solution**: Distinguish objective issues (readability) from subjective (color choice), defer to user on subjective

**Problem**: Unclear if issue is serious or nitpick  
**Solution**: Use prioritization framework consistently, explain why categorized as critical/important/polish

**Problem**: User wants review but won't share slides  
**Solution**: Verbal description can work but limits diagnostic depth, recommend sharing at least screenshots
