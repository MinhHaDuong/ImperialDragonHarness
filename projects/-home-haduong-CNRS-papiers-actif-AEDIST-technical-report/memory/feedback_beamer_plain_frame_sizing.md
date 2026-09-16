---
name: feedback_beamer_plain_frame_sizing
description: "Beamer [plain] full-page figure frames need both width=\\paperwidth AND height=\\paperheight with keepaspectratio"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: aec7aadb-4f9c-4638-a4ea-33dfe527711a
---

For Beamer `[plain]` frames containing a single full-page figure, always use `width=\paperwidth,height=\paperheight,keepaspectratio`. Using only `width=\paperwidth` causes `Overfull \hbox` warnings when the figure's natural aspect ratio is wider than the text area.

**Why:** Multiple hbox overflow warnings required reactive fixes during ticket 0318. Should be applied as the default from the start.

**How to apply:** Every `\begin{frame}[plain]` with `\centering\includegraphics` gets both width and height constraints. Exception: figures inside `\column` environments use `width=\textwidth` only.
