---
name: applied-econ-writing
description: "Structure and draft applied economics papers (environmental, development) following Shapiro, Head, Bellemare and J-PAL."
---

# Applied Economics Paper Writing

Guide for structuring and writing applied economics papers, based on proven methodologies from Shapiro, Head, Bellemare, and J-PAL.

## Scope

**Primary domain**: Environmental economics, development economics, resource economics.

**Applicable with caution**: Other applied micro fields (labor, health, IO empirique, public economics).

**Not applicable**: Pure theory, macroeconomics, quantitative finance, econometric methodology papers.

## Workflow Decision Tree

```
User request
    │
    ├─► "Help me start/structure a paper"
    │       └─► Use Four Steps (Shapiro) + Introduction Formula (Head)
    │
    ├─► "Review/improve my introduction"
    │       └─► Check against Introduction Formula (Head)
    │
    ├─► "Structure my empirical section"
    │       └─► Use Paper Structure (Bellemare)
    │
    ├─► "Write a grant proposal"
    │       └─► Use J-PAL methodology (see references/jpal-proposals.md)
    │
    └─► "Where should I submit?"
            └─► Use Journal Selection guidance
```

## Core Method: Four Steps (Shapiro)

### Step 1: Aspirational Introduction
Write an introduction for the paper you aspire to write. Make up results if needed. Ask: "If I write this paper, will I be happy with it?" If imaginary results don't excite you, real ones won't either.

### Step 2: Research
Work first on whatever is least clear or most likely to prevent success. Return frequently to the introduction—it is your compass.

### Step 3: Robot
Write the body for a robot:
- **Linear**: Undefined concepts break it
- **Clear**: Nonsense breaks it
- **Plain**: Fancy talk doesn't impress it
- **Formal**: Correct math is fine

### Step 4: Contractual Introduction
Rewrite the introduction as a contract. Reader agrees to be excited if paper delivers what introduction promises.

## Introduction Formula (Head)

Five components, in order:

### 1. Hook (1-2 paragraphs)
Attract interest. Y is worth studying because:
- Y matters (people hurt/helped when Y changes)
- Y is puzzling (defies easy explanation)
- Y is controversial (disagreement exists)
- Y is big or common

**Avoid**: Bait-and-switch; "all my friends are doing it" (no motivation beyond literature exists).

### 2. Question (1-2 paragraphs)
State what the paper does. End with: "This paper addresses the question..."

### 3. Antecedents (1-2 paragraphs)
Critical prior work only. Establish gaps non-insultingly.

### 4. Value-Added (1-3 paragraphs)
~3 contributions relative to antecedents. Most important for convincing referees. Contributions make sense only in light of prior work.

### 5. Road-map (1 paragraph)
Outline organization. Customize to project, mention landmarks. Keep short.

**Key practice**: Write intro first, edit every time you work on the paper.

## Paper Structure (Bellemare)

Standard structure for applied papers:

1. **Title** – Short, clear. "The Impacts of D on y: Evidence from [Context]"
2. **Abstract** – Intelligible to non-specialist PhD economist
3. **Introduction** – Follow Head's formula
4. **Theoretical Framework** – Theory of change; can adapt existing
5. **Data and Descriptive Statistics** – Answer all reader questions about data
6. **Empirical Framework** – Estimation strategy + identification strategy
7. **Results and Discussion** – Core → robustness → heterogeneity → mechanisms → limitations
8. **Conclusion** – Summary → limitations → policy implications → future research
9. **References**
10. **Appendix**

## Research Question Criteria (Shapiro)

A good question:
- **Has an answer** – "Effect of X on Y?" has one; "Nature of behavior in industry?" doesn't
- **Answer not obvious** – Can't determine from logic/common sense/existing evidence
- **Answer is actionable** – Someone (policymaker, firm, NGO) would do things differently

## Empirical Framework Checklist

### Estimation Strategy
- Show equations to estimate
- Proper subscripts (i, j, k from smallest to largest unit)
- Latin letters = variables; Greek = coefficients
- Don't reuse notation across specifications
- Specify estimation method
- Discuss inference (robust SEs, clustering level, weights)

### Identification Strategy
- Explain intuitively why results approach causality
- Discuss: reverse causality, unobserved heterogeneity, measurement error
- Check SUTVA violations
- Be honest about limitations—don't lie about what results can/cannot do

## Results Presentation

### Order
Most parsimonious → least parsimonious (bivariate → full controls).

### Robustness Checks
- Multiple outcome measures
- Multiple treatment measures
- Placebo tests (fake treatment → should find nothing)
- Falsification tests (fake outcome → should find nothing)
- Alternative estimators

### Treatment Heterogeneity
Split by subgroups. Can salvage null findings (average masks heterogeneity).

### Mechanisms
Test causal pathways. Measure attitudes + knowledge + behavior to identify which drives effects.

## Tables Checklist

- Self-explanatory titles: "OLS Results for Effect of X on Y"
- Same decimal places throughout (2-3)
- Show all controls (or list them in notes)
- Report N, R², significance symbols in notes
- Use plain English variable names, not code names
- Same estimation sample across specifications

## Conclusion Structure

1. **Summary** – Tell them what you told them
2. **Limitations** – Be honest
3. **Policy implications** – Winners/losers, feasibility, back-of-envelope cost-benefit
4. **Future research** – What remains to be done

## Journal Selection

### Strategy
- Cite 5+ recent articles from target journal (last 5 years)
- If you improve internal AND external validity → try general journal first
- Network effects matter: present at seminars before submission

### Signals to Editor
- Recent citations from journal = good fit signal
- Recent citations help editor find reviewers who've seen your work

## References

For detailed guidance:
- **Grant proposals**: See `references/jpal-proposals.md`
- **Full methodologies**: See `references/source-documents.md`

## Anti-Patterns

❌ **Topic as question**: "My paper is about X" → Not a question  
❌ **Generic truism**: "Climate change is important" → Everyone agrees, not distinctive  
❌ **Multiple messages**: Pick one main contribution  
❌ **Burying the message**: Get to the point  
❌ **Lying about identification**: Don't claim causality you don't have
