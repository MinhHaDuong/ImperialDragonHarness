# Astra : avis de conception KISS

Révision examinée : `1206b23e`. Avis de conception, pas validation finale.
Identité réelle `gpt-6-astra`, effort `high`, confirmée dans le `turn_context` du sous-agent. Famille OpenAI, contexte distinct mais même famille que le MOE. Route native `spawn_agent`, `fork_turns=none`.

Constats transmis par le lecteur :

1. Le lecteur de registre R&R reconstruit un schéma fixe et perdrait les preuves/statuts ajoutés par le moteur. Accord préalable sur les champs additifs et test de round-trip ; conserver la critique verbatim et séparer factualité et décision de l’auteur.
2. Les outils réellement utilisés demandent une trace d’exécution observable : `searched: true`, URL listées et revue non vide ne suffisent pas. Une première route outillée fonctionnelle, sans framework de backends ; preuve de recherche/fetch et limites déclarées.
3. Le skill actuel et sa référence continueraient de multiplier les lecteurs et de favoriser la répétition. Le nouveau chemin doit partir d’une revue complète et d’une vérification bornée ; l’ancien helper peut rester pendant l’essai sans en conserver les défauts comme défauts du nouveau chemin.
4. Distinguer validation du nouveau chemin et migration des derniers appelants de l’ancien. Le MOE conserve toutefois l’objectif de retrait demandé par l’auteur, sous réserve d’un essai satisfaisant.
5. Épingler la provenance du prompt et distinguer les adaptations IDH : annexes, traces durables, vérification des critiques majeures, décisions et suivi des révisions. La génération et les instruments expérimentaux de jugement de l’article sont des objets distincts.

Architecture minimale recommandée : un script, un dossier d’exécution, un lecteur complet ; préparation des entrées et pages ; revue outillée et brute conservée ; vérification source-aware bornée ; restitution et registre R&R commun ; nouvelle tentative liée à la précédente sans écrasement. L’archivage et la résolution des remarques ont des états séparés. Aucun résultat scientifique de la future revue n’a été évalué dans cette passe.

Sources fournies au lecteur : PDFs et extractions complets du papier et du supplément King–Worthington, version du 22 octobre 2026, stockés dans Zotero (œuvre `5IWA45WQ`) ; supplément Appendix C pour le prompt, D pour le jugement, E pour les domaines. Il les a consultés en lecture seule.
