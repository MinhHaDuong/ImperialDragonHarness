# Stylème — garde-fous méthodologiques

2026-09-15 : une revue externe de la PR #169 a montré que la séparation des
registres ne peut pas être inférée de moyennes par bucket ni d'un split par
segments : les segments d'un même document fuient leur lexique entre train et
test. Le protocole obligatoire est désormais : split déterministe par fichier,
classification de chaque segment entièrement tenu à part, et empreintes SHA-256
du manifest, du corpus effectivement lu et du script dans le rapport.

Le score contrastif ne soustrait jamais deux deltas de Burrows normalisés par
des profils différents. Il emploie l'intersection des traits et un écart-type
poolé. Les profils contrastés exigent une cible `positive` et un contraste
`negative`; leurs sources publiables ne contiennent que des empreintes de
contenu, jamais des chemins locaux.

Résultat corrigé à 500 tokens : 27/162 = 16,7 %, soit le hasard pour six
buckets. Un profil global reste donc défendable à ce stade.
