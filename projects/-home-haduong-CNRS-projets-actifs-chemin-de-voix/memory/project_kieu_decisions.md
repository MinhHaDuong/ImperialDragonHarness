---
name: Décisions créatives Chemin de voix
description: Choix structurels et éditoriaux fixés pour la contribution — replanifiés 2026-04-27
type: project
originSessionId: 36d1acf3-4f7c-4c25-9343-05779577ace1
---
Contribution au Tracing Kieu : titre de la contribution = "Chemin de voix, traversée du Kiều". "Tracing Kieu" = titre de la publication externe, immutable. Échéance juin 2026.

**Why:** Replanification complète 2026-04-27 — nouveau titre, nouvelles figures, méthode IA.

**How to apply:** Ne pas rouvrir les décisions structurelles sauf si Minh le demande. Vérifier les tickets pour l'état courant.

## Texte final = 9 voix (sur 13 générées)

13 voix générées par pipeline IA (12 héros au mur + Héloïse). Les 9 voix finales sont choisies en phase d'assemblage.

## Figures et passages

| # | Voix | Vers | Statut |
|---|------|------|--------|
| - | Ada Lovelace | 1–8 | v0 brouillon (remplacé par IA) |
| - | Thích Nhất Hạnh | 80–105 | v0 brouillon (remplacé par IA) |
| - | Héloïse d'Argenteuil | 350–380 | v0 brouillon (remplacé par IA) |
| - | Richard Feynman | 460–490 | v0 brouillon (remplacé par IA) |
| - | Hồ Chí Minh | TBD (ticket 0003) | passage à rechoisir — cadre intellectuel |
| - | Marie Curie | 1400–1450 | v0 brouillon (remplacé par IA) |
| - | Aliénor d'Aquitaine | 2355–2380 | v0 brouillon (remplacé par IA) |
| - | Zheng He | 2455–2500 | v0 brouillon (remplacé par IA) |
| - | Alan Manne | 3095–3150 | v0 brouillon (remplacé par IA) |
| - | Rahan | TBD (ticket 0009) | nouveau — BD Lécureux/Chéret |
| - | Adrian Carton de Wiart | TBD (ticket 0009) | nouveau — *Happy Odyssey* |
| - | Indiana Jones | TBD (ticket 0009) | nouveau — scripts films |
| - | 12e héros | TBD | voir Heroes/ |

## Décisions spécifiques

- **Ada** : traduit Nguyễn Du (v.1–8), pas Kiều — seule entrée méta.
- **HCM reframé** : intellectuel prolifique à impact social (journaliste, poète, *Carnets de prison*) — pas homme d'État. Passage à rechoisir centré sur écriture/transmission.
- **Fictifs (Rahan, Indy) traités identiquement aux réels** — pas de distinction éditoriale.
- **Brouillons v0** : archivés, aucun data leak vers le pipeline IA.

## Master document

HTML comme document de travail maître. Les voix-*.md + intro.md + coda.md sont archivés comme v0.

## Méthode

Voix générées par LoRA fine-tuning sur écrits originaux de chaque figure + voix-auteur (banhhanoi.art + papiers curatés). Sweep température × poids-auteur. Best-of-N : présélection 3 LLM → HITL Emma + auteur.
