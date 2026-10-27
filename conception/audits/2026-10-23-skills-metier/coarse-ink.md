# Coarse-ink : examen de réutilisation

Signalé par l’auteur pendant le train. Source PyPI1.9.6, commit publié2e813b28b76ee0679aa48bb174f6de8700f692db, MIT. Examen statique des sources publiques par le worker bibliographie, sans installation, exécution ni credentials. Qualité et coûts annoncés non mesurés.

Harvard AppendixC teste un lecteur complet avec recherches/récupérations, sans démontrer le bénéfice des panels ou des synthèses multiagents. Coarse décompose la lecture en vue globale, complétude, sections, contrôles et filtrage. Notre parcours conserve le lecteur unique et ajoute explicitement vérification bornée, traçabilité et décisions de l’auteur.

Constats dans les sources épinglées :
- src/coarse/pipeline.py518–524 : références exclues des agents de section, annexes de moins de500caractères sautées,25sections sélectionnées au plus. agents/base.py17–23 tronque à500000caractères. Une passe globale reçoit du texte extrait ; cela ne constitue pas notre preuve d’inspection texte/image de chaque page.
- quote_verify.py91 : rapprochement des citations au manuscrit, réparation approximative ou suppression de commentaires ; pas les quatre jugements sur les sources externes décisives.
- headless_clients.py768–795 : clients natifs Claude/Codex/Gemini réels ; Claude utilise outils désactivés et sortie texte. Retour stdout, espace temporaire ; pas nos traces natives observées.
- headless_review.py430 : fichiers de sortie déterministes écrits avec write_text ; aucune garantie équivalente d’essais immuables établie dans ce parcours.
- config.py42 et llm.py505 : pas de champ endpoint exposé dans la configuration publique ni baseURL dans review_paper. Compatibilité Albert non prouvée ; ne pas annoncer un backend déjà disponible.
- pyproject.toml : Python>=3.12,12dépendances directes dont LiteLLM/Instructor/Pydantic/PyMuPDF, Docling optionnel. Adoption du pipeline augmenterait la pile pour des garanties différentes.

Décision MOE : conserver le moteur simple du train. Coarse est un candidat d’essai ultérieur comme revue advisory supplémentaire, pas une dépendance ni un remplacement ici. Réutilisation sélective éventuelle du rapprochement de citations seulement après besoin établi. Aucun benchmark ajouté au protocole de production, aucune supériorité scientifique déduite de cette inspection.

Sources : https://pypi.org/project/coarse-ink/ ; https://github.com/Davidvandijcke/coarse/tree/2e813b28b76ee0679aa48bb174f6de8700f692db .
