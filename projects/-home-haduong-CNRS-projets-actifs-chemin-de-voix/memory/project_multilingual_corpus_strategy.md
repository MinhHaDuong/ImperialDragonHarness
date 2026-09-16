---
name: multilingual corpus strategy
description: language-fit is a tie-breaker (not a score dimension); single-directory layout; HCM Prison Diary is ZH; HCM FR corpus now available via bibliomarxiste (CDSM Art. 4)
type: project
originSessionId: dabd1750-4d3a-468f-8222-0138a55d1233
---

Merged in PR #27 (2026-05-09). Key decisions:

**Language-fit is a soft tie-breaker, not a score dimension.**
The 0–10 scale (authenticity + genre + decon) is unchanged. `select_dataset.py --lang <target>`
breaks ties: target-language chunks rank first at equal score. At 5× budget,
non-target-language chunks face threshold+1. At 2× budget, ordering preference only.

**Translations score authenticity−1.**
A translation of a figure's authentic text scores authenticity=3 (not 4) — content
preserved, style mediated by translator.

**Single-directory layout.**
Every voice has one `voix-{slug}/` directory. No `voix-auteur-fr/` / `voix-auteur-en/`
split. `# language: <iso>` header in each chunk. Ticket 0072 migrates the author's corpus.

**HCM Prison Diary is Classical Chinese, not Vietnamese.**
Hồ Chí Minh was imprisoned by KMT (Kuomintang) forces in Guangxi, 1942–43. His Chinese
jailers forbade him from writing in Vietnamese, so the 133 poems (獄中日記) are in
Classical Chinese heptasyllabic regulated verse — same register as Zheng He's corpus.
VN and EN editions are translations (authenticity=3). ZH original = authenticity=4.
FR writings (Le Procès, Lénine et les peuples coloniaux, etc.) fetched from
bibliomarxiste.net in PR #47 (ticket 0120). Legal basis: 1924+1925 pieces are PD
(pre-1929 US); all covered by CDSM Directive 2019/790 Art. 4 TDM exception for
local LoRA training. ~36K words authentic FR voice, scoring auth-4.

**How to apply:** When building HCM dataset for FR LoRA: ZH Prison Diary gets full
authenticity score; EN/VN translations score 3. FR writings are now available
(~36K words, auth-4) — these are the primary FR training signal for voix-hcm.
Use `--lang fr` flag to prefer FR+EN over ZH at tie-break time.
