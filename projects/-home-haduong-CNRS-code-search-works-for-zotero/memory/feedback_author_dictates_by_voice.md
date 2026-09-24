---
name: feedback-author-dictates-by-voice
description: The author often works by voice — his client transcribes; read his messages as speech-to-text output and answer in a listenable form
metadata:
  type: feedback
---

The author sometimes conducts a whole session by voice: the Claude Code client
captures and transcribes his speech, and only the resulting text reaches the
model. He stated this on 2026-09-11 ("cette session est faite en audio").

**Why:** a transcribed message is not a typed one. Homophones, absent or wrong
punctuation, and mangled proper nouns, paths and identifiers are transcription
noise, not the author being imprecise — and treating an artifact as intent
sends the work in the wrong direction. Symmetrically, an answer he may be
hearing or reading on a phone is degraded by long paths, wide code blocks and
dense enumerations.

**How to apply:** read odd wording charitably and reconstruct the intended term
from context; when a doubtful word would change what gets built, ask instead of
guessing — one short question beats a wrong branch. Keep replies compact, put
any indispensable path or command alone on its own line, and prefer prose to
tables when the session is spoken. Do not conclude from a garbled identifier
that a file or ticket is missing: check the plausible spelling first
([[feedback-search-the-fork-before-claiming-absence]]). Unrelated to
[[reference-author-voice-corpus]], which is about his written prose style.
