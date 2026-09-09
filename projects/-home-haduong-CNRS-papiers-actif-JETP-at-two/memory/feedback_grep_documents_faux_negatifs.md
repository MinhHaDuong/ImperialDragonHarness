---
name: feedback-grep-documents-faux-negatifs
description: Grepper un document n'est pas grepper du code — cinq faux négatifs en une session, et les cinq modes de défaillance propres aux documents
metadata:
  type: feedback
---

Un `grep` qui ne trouve rien dans un **document** dit rarement « absent ». Il
dit le plus souvent « je n'ai pas su regarder ». Cinq occurrences dans la
session du 2026-09-09, toutes sur le dépôt du livre :

1. **Morphologie française.** `grep -i "turqu"` a renvoyé « aucune occurrence »
   alors que les deux plans portaient le cas turc — l'un écrivait « le cas
   **turc** », l'autre « **Türkiye** ». J'ai rapporté une absence à l'auteur
   avant qu'il ne me détrompe.
2. **Apostrophe typographique.** `grep "Vietnam's"` contre un PDF qui rend `’`.
3. **Retour à la ligne.** Une expression cherchée sur une ligne quand la source
   la coupait en deux.
4. **Encodage de transfert.** `grep "extraits adaptés"` sur un fichier `.eml` :
   zéro, le corps étant en quoted-printable où `é` s'écrit `=C3=A9`.
5. **Couches du PDF.** « zéro URL » affirmé plusieurs fois d'après
   `pdftotext`, qui ne montre que le texte d'ancre. Les dossiers envoyés
   portaient sept annotations de lien chacun. Voir
   [[reference-verifier-liens-pdf]].

**Pourquoi.** Le code est du texte plat et normalisé ; un document a une
morphologie, une typographie, une mise en page, un encodage et des couches. Le
motif littéral est le bon outil pour l'un et le mauvais pour l'autre.

**Comment appliquer.** Avant de rapporter une absence dans un document :
faire tourner la sonde sur un cas **connu positif**. C'est ce qui a démasqué
le cinquième cas — la sonde `/URI` répondait zéro sur la version INTERNE, qui
contient certainement des URL. Sans ce contrôle, j'aurais confirmé une
deuxième fois une affirmation fausse en croyant l'avoir vérifiée.

Pièges à couvrir d'office : variantes morphologiques du terme (turc/turque/
Turquie/Türkiye), les deux apostrophes et les deux jeux de guillemets, la
recherche sur texte déplié plutôt que ligne à ligne, le décodage avant la
recherche pour tout fichier généré, et la bonne couche pour un PDF.

Et une forme dégénérée à ne jamais écrire : `grep … | head -3 || echo absent`
— `head` sort en 0, donc la branche « absent » ne s'exécute jamais et l'absence
n'est jamais confirmée, seulement déduite d'une sortie vide.

Cas général déjà tenu par le harnais (`rules/coding-bash.md`, § sonde dont
l'acquittement ne se distingue pas du « je n'ai pas su regarder ») ; ceci en
est la déclinaison documentaire.
