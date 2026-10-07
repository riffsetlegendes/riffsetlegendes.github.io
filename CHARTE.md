# Charte éditoriale Riffs & Légendes (à respecter strictement)

Site : média rock français, rock et musiques populaires 1950–1999 + rubrique « La relève » (groupes actuels).
Articles : fichiers Markdown dans /home/claude/riffs-legendes/content/.

## Règles non négociables
1. **Zéro plagiat.** Texte 100 % original, écrit avec tes propres mots et ta propre construction. Ne recopie ni ne paraphrase de près aucune source (Wikipédia, presse, biographies, communiqués). Utilise les sources uniquement pour vérifier des faits, puis rédige librement. Pas de citations longues : au plus une courte citation (une phrase) par article, entre guillemets français, attribuée, et seulement si elle est bien documentée.
2. **Aucune comparaison entre groupes récents et anciens**, dans un sens comme dans l'autre. Interdits : « héritiers de », « nouveaux Led Zeppelin », « rappelle X », « dans la lignée de », « sonne comme », « à la manière de », « digne de », « clone », mentions que la presse les compare à tel groupe, etc. Un groupe de la relève est présenté pour lui-même : son histoire, ses membres, ses disques, sa scène, son écriture, ses choix de production. De même, un article sur une légende ne dit pas « tel groupe actuel lui doit tout ». Les influences revendiquées par un artiste historique (ex. Keith Richards sur Chuck Berry) restent acceptables quand c'est de l'histoire documentée entre artistes de l'époque, mais restent sobres.
3. **Exactitude.** Vérifie chaque date, chiffre, lieu, nom via WebSearch/WebFetch. En cas de doute, retire le fait plutôt que d'inventer. Aucune invention de citation.
4. **Plus riche.** Viser 850 à 1 200 mots de texte pour portraits, anecdotes, ce-jour-là et actu ; 600 à 900 mots pour les playlists (une intro + un paragraphe original par morceau expliquant contexte, enregistrement, ce qu'il faut écouter). Structure avec 3 à 5 intertitres `##`. Contexte, coulisses, enregistrement, réception, détails concrets, ce qu'il faut écouter et pourquoi. Ajouter si pertinent un bloc `:::fiche` (Notes de pochette) et/ou `:::aussi Titre` (repères chronologiques, `année | texte`).
5. Ton : français soigné, vivant, précis, sans superlatifs creux ni clichés (« légende incontournable », « mythique » à répétition). Phrases variées. Pas de tirets cadratins en rafale.

## Format technique (ne pas casser)
- En-tête `clé: valeur` jusqu'à une ligne `---`. Conserver **inchangés** : slug, date, category, image, image_alt, image_caption, event_year (sauf erreur factuelle). Tu peux réécrire title et excerpt (excerpt : 1 à 2 phrases, sans comparaison). Mettre à jour/ajouter `sources:` au format `[Nom](url), [Nom](url)` avec les pages réellement consultées.
- Blocs (une ligne par élément, colonnes séparées par ` | `, bloc fermé par `:::` seul) :
  - `:::fiche` lignes `Clé | Valeur`
  - `:::aussi Titre` lignes `Année | Texte`
  - `:::ecoute` et `:::tracklist` lignes `Titre | Artiste | Année | spotifyTrackID`. **Garder les ID Spotify existants tels quels.** N'ajoute un morceau que si tu peux vérifier son ID de piste Spotify exact (sinon ne l'ajoute pas).
- Ne touche à aucun autre fichier que ceux qui te sont assignés.

## Rendu
Réécris les fichiers en place. À la fin, réponds avec : pour chaque fichier, le nombre de mots et une ligne sur les faits vérifiés délicats ou retirés.
