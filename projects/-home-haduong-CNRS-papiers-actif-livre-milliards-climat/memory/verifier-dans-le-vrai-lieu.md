---
name: verifier-dans-le-vrai-lieu
description: "Ne jamais annoncer « vérifié / propre » depuis un contrôle qui n'a pas réellement tourné, ni depuis une copie isolée — vérifier dans le checkout réel et la sortie réelle."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d4e038ad-fda0-44ef-b26c-40436685369b
---

Sur ce projet livre, trois fois dans une même session j'ai présenté comme acquis
ce qui ne l'était pas, et l'auteur l'a relevé sèchement (« tu m'enfumes ») :
1. « notes purgées du PDF (0 occurrence) » alors que `pdftotext` était **absent** :
   le `grep` tournait sur une entrée vide et renvoyait 0 — un faux négatif pris
   pour une preuve.
2. « build sans warning » en ne scannant que stderr, alors que les *Overfull
   hbox* et le warning de glyphe vivaient ailleurs (le `.log` LaTeX, capturé par
   tectonic).
3. Tout le travail fait dans un **worktree isolé** pendant que le fichier que
   l'auteur ouvre sur le disque (`dossier-proposition.md`) restait celui de la
   veille — « régénéré » et « vérifié » dans une sandbox déconnectée.

**Why:** un contrôle qui n'a pas vraiment tourné (outil absent, mauvais flux,
mauvais répertoire) renvoie souvent un « 0 » ou un succès vide indiscernable d'un
vrai pass. L'affirmer érode la confiance plus vite que n'importe quel bug.

**How to apply:**
- Avant de dire « 0 / propre / vérifié », confirmer que la commande a *fait* le
  travail : outil présent (`command -v`), bon flux (les warnings LaTeX sont dans
  le `.log`, pas sur stderr — compiler et grep le log), sortie réelle inspectée
  (extraire le texte du PDF/docx, pas le markdown intermédiaire).
- Vérifier et régénérer dans le **checkout réel de l'auteur**, pas dans une copie.
  Ce projet travaille **direct sur `main`, sans worktree** (cf. [[CONVENTIONS]] /
  AGENTS.md) : la sandbox cachait le travail au lieu de le livrer.
- Dire honnêtement ce qui n'a pas pu être vérifié (ex. liens 403 anti-robot :
  « non confirmé depuis ici, à voir au navigateur ») plutôt que d'affirmer.
