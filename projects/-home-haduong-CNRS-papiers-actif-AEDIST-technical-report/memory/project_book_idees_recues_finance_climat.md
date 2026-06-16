---
name: project_book_idees_recues_finance_climat
description: "Side book project — \"Idées reçues sur la générosité climatique des pays riches\" (Le Cavalier Bleu), separate from AEDIST"
metadata: 
  node_type: memory
  type: project
  originSessionId: ca2b78dc-59b4-4ce7-9ac0-b7b65483a84b
---

A grand-public book the user is reviving, in its **own git repo** (not AEDIST) at
`~/CNRS/papiers/actif/Comment dépenser plus de 100 milliards de dollars - Projet Livre/`.

- **Concept:** a *démontage* of 16 idées reçues on North–South climate finance, for Le Cavalier Bleu's flagship "Idées reçues" collection. Title settled 2026-06-15: *Idées reçues sur la générosité climatique des pays riches* — sous-titre *Cent, trois cents milliards : à qui profite le compte ?*. Offensive but good-faith, no plaidoyer. Reframe of a stalled 2024 project ("Comment dépenser 100 milliards") whose COP30-anticipation premise had burned (NCQG was set at Bakou/COP29, Nov 2024: 300 Md\$/yr by 2035).
- **Build:** markdown parts → pandoc + tectonic. `dossier/build-dossier.sh` assembles `dossier/dossier-proposition.pdf` — the pitch (bordereau + lettre à A.-L. Marsaleix + projet + sommaire commenté + 2 sample chapters: ch.3 Bakou, ch.12 JETP/Vietnam). The book itself is a Quarto project (`_quarto.yml`). Generated PDFs are gitignored; markdown parts are tracked.
- **State at 2026-06-15:** dossier finalised (13 p.), claims hardened + URLs verified, démontages retitled grand-public, préface dropped (decided with author), interview plan in `notes/entretiens.md`. **Next step:** author sends the dossier to Romain Blachier (the recommender) to request a warm intro to Anne-Laure Marsaleix at Le Cavalier Bleu.

Living state lives in the book repo's own `README.md`, `notes/synopsis.md`, `TODO.md`. Working style: [[feedback_editorial_book_work]].
