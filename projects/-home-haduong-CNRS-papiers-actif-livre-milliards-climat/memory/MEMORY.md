# Mémoire — livre « 100 milliards »

- [Vérifier dans le vrai lieu](verifier-dans-le-vrai-lieu.md) — ne pas annoncer « propre/vérifié » depuis un contrôle qui n'a pas tourné ni depuis une sandbox ; travailler direct sur main.
- [Workflow EDM](edm-workflow.md) — Zotero = système de référence ; `docs/` et `.bib` sont du staging (git-ignorés), synchronisés vers Zotero puis purgés à l'archivage après publication.
- [git commit -- pathspec contourne l'index](git-commit-pathspec-bypasses-index.md) — un commit par pathspec lit l'arbre de travail, donc ignore silencieusement un `git rm --cached` stagé ; commiter l'index (plain `git commit`).
