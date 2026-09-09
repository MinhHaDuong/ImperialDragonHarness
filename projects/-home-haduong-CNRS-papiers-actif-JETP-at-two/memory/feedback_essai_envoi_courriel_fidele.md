---
name: feedback-essai-envoi-courriel-fidele
description: Tester un courriel avant un envoi irréversible — destinataire d'enveloppe distinct de l'en-tête To:, pour voir exactement ce que le vrai destinataire verra
metadata:
  type: feedback
---

Avant un envoi irréversible et sortant (dossier à un éditeur, soumission),
s'envoyer le message d'essai en **dissociant le destinataire d'enveloppe de
l'en-tête `To:`** :

```bash
msmtp moi@exemple.org < message.eml   # en-têtes du .eml intacts
```

En donnant le destinataire en argument, `msmtp` ne prend pas les destinataires
dans les en-têtes (contrairement à `-t`). On conserve ainsi les mêmes données
rédigées : `To:`, `Subject`, corps MIME et pièce jointe. Les serveurs ajoutent
des en-têtes de transport et peuvent normaliser le message ; les exemplaires
reçus ne sont donc pas nécessairement identiques octet pour octet. Vérifier
les champs et le contenu de la pièce jointe, plutôt que les octets du courriel
reçu entier. Cet essai montre le rendu dans la boîte de l'auteur ; il ne
garantit ni le rendu ni la délivrabilité chez un autre destinataire.

**Pourquoi.** Modifier le sujet ou le destinataire pour marquer l'essai revient
à tester autre chose que ce qu'on enverra. L'essai complète les vérifications
locales par une réception réelle : rendu des accents et des guillemets
français, pièce jointe qui s'ouvre vraiment et `Reply-To` effectif.

**Vérifier aussi l'expéditeur avant d'envoyer.** Le 2026-09-09, msmtp était
configuré sur `minh@haduong.com` alors que la signature des courriels annonçait
l'adresse CNRS : les réponses des éditeurs seraient parties ailleurs que là où
la lettre les appelait. Corrigé par un `Reply-To:`, pas par un changement de
configuration. Lire `from` dans `~/.msmtprc` — sans jamais afficher les
identifiants qui l'accompagnent.

Procédure retenue pour cette campagne, à confirmer comme règle : corps affichés
pour validation, puis essai fidèle à l'auteur, puis envoi sur son « go ».
