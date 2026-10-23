# Stratégie Reels Riffs & Légendes (mise à jour du 19/10/2026)

À lire avant de choisir les sujets et d'écrire les 3 Reels du jour. Les preuves chiffrées sont dans strategie/SWIPE.md.

## 1. Ce qui fait les vues dans la niche

Deux concepts portent la quasi-totalité des Reels qui dépassent 3 fois la médiane de leur compte :

- **L'origine improbable** : pourquoi un groupe, un album, un logo ou un son s'appelle ou sonne ainsi. Exemple de moule : « Pourquoi le premier album de Pearl Jam s'appelle Ten ? »
- **Le détail caché derrière une fin** : un dernier concert que personne ne savait être le dernier, un drame, une disparition, avec UN détail que le public ignore. Toujours calé sur la date du jour.

Ce qui ne marche pas : la biographie « de X à Y en N albums », l'hommage générique sans détail, la liste de sorties du jour, le simple « joyeux anniversaire ».

## 2. Le format : le récit narré, sur les trois créneaux

Décision de Yann du 19/10 (carte blanche) : le format « recit » de tools/reel_formats.py REMPLACE journal, countdown et docu pour tous les Reels. C'est la forme de tous les Reels viraux de la niche : des photos plein écran qui bougent, de gros sous-titres mot à mot, une accroche lisible dès la première seconde.

**Mise à jour de Yann du 19/10 au soir : PAS DE VOIX OFF.** On garde le texte (sous-titres), la voix est supprimée jusqu'à nouvel ordre. Le générateur rend la piste audio muette par défaut (la synthèse ne sert qu'à caler le rythme des sous-titres, ralenti à -12 %) ; ne mets jamais "voice_on": true sans accord de Yann.

| Créneau | Fichier | Concept imposé |
|---|---|---|
| 8 h | instagram/AAAA-MM-JJ-jour.json | Détail caché derrière une fin, ou anniversaire + fait étrange (date du jour) |
| 13 h | instagram/AAAA-MM-JJ-anecdote.json | Origine improbable (« Pourquoi… ? ») ou « deux dates » (chute puis triomphe) |
| 18 h | instagram/AAAA-MM-JJ-focus.json | Coulisses d'un disque, détail caché, ou relève sous l'angle d'une origine ou d'une actu |

Champs du JSON : "format": "recit", "title" (bandeau jaune fixe en haut, 30 caractères maximum, une promesse), "narration" [{"text", "photo"}], "photos" (4 à 6, toutes différentes), "song", "caption", "hashtags", "reel": true, "label", "big". Facultatifs : "voice" (défaut fr-FR-HenriNeural), "rate" (défaut +8 %). Le champ "slides" n'est plus utilisé.

**Photos (consigne de Yann du 19/10) : qualité et variété avant tout, droits non bloquants (compte de passionné, non commercial).** Une photo différente par phrase, d'époque (celle de l'histoire racontée), en haute définition (1000 px minimum), trouvée par recherche d'images (presse, séances photo, archives, fans) via des URL directes. Pas de photos floues, pas de scans de magazine pleins de texte, pas de doublons, pas de photos de concerts récents pour une histoire ancienne. Commons seulement si la photo est bonne.

**Anti-répétition (remarque de Yann du 20/10 : « tu parles très souvent des mêmes artistes »).** Avant de choisir un sujet de Reel, liste les artistes des Reels des 30 derniers jours (champ "song.artist" et "title" des fichiers instagram/AAAA-MM-JJ-*.json, plus les artistes cités dans la narration). Un artiste déjà au centre d'un Reel dans les 30 jours est interdit, et un artiste seulement cité (ex. Elvis dans une histoire de Tom Petty) n'est pas le sujet principal non plus pendant 14 jours. Viser chaque semaine au moins 5 artistes jamais traités en Reel, en variant les décennies (50s à 2020s), les genres (rock, punk, metal, soul, pop, chanson, blues, grunge, relève) et les pays (y compris français). Le fichier semaine doit respecter cette règle ; s'il la viole, remplace le sujet.

**Horaires (23/10) :** GitHub lance les crons avec ~35 min de retard, d’où des crons à 5 h 40, 10 h 40 et 15 h 40 UTC (heure d’été). À partir du passage à l’heure d’hiver (25/10), les décaler d’une heure (6 h 40, 11 h 40, 16 h 40 UTC) dans .github/workflows/instagram.yml, lignes schedule ET tests elif.

**Publication (21/10) : quota Metricool atteint.** Les Reels partent par le workflow GitHub programmé (cron 8 h, 13 h, 18 h, tools/ig_publish.py, API Instagram) avec le vrai morceau : mettre "audio_id" dans le JSON (liste des sons via dispatch kind=audio:<Titre Artiste>), sinon recherche automatique d'après "song". Le marqueur instagram/publies/ est écrit par le workflow. Ne plus programmer dans Metricool tant que le quota n'est pas revenu.

Musique à la publication Metricool : le vrai morceau de l'artiste seul, audioConfiguration {audioId, audioVolume: 100, videoVolume: 0}.

**Musique (correction de Yann du 20/10 au soir : TOUJOURS un vrai morceau de l'artiste, jamais de musique libre de droits).** Les vrais morceaux existent dans les candidats Metricool sous forme de « original_sound ». Méthode :
1. Chercher « Titre Artiste », puis « Artiste - Titre », puis un autre tube du même artiste si besoin, jusqu'à avoir plusieurs candidats.
2. Écarter tout titre contenant cover, live, remix, sped up, slowed, acoustic, karaoke, instrumental, piano, ukulele, guitar, voceux, edit, mashup, ou un nom de tiers ; écarter les durées inférieures à 30 s.
3. Essayer les candidats retenus un par un (createScheduledPost en draft, puis lire igUsername et durationMs) : préférer, dans l'ordre, le compte officiel de l'artiste ou du label, puis un titre propre « Artiste - Titre » de durée longue (60 s et plus, signe d'un extrait de la version album), puis la durée la plus proche du morceau studio.
4. Supprimer les brouillons d'essai inutiles (ou les laisser en brouillon, jamais publiés) et garder un seul post final.
5. La musique libre n'est autorisée que si l'artiste n'a VRAIMENT aucun morceau disponible, ce qui doit rester exceptionnel ; le signaler alors à Yann.

Contrôle du rendu (workflow dry_run) : la vidéo dure 40 à 60 s (temps de lecture confortable, consigne de Yann du 22/10 : rallonger plutôt que de rendre le texte illisible), les sous-titres ne débordent pas, restent affichés jusqu’au suivant, sur bandeau sombre.

## 3. Règles d'écriture de la narration

- 80 à 110 mots, 7 à 9 phrases courtes (une phrase = une photo ou un plan). Écrit pour être lu vite : phrases simples, verbes au présent, aucun sigle obscur, nombres que l'on peut dire à voix haute.
- Phrase 1 = l'accroche : le fait étrange ou la question « Pourquoi… ? », avec un élément précis (nom, nombre, objet). Le sujet est compris en 2 secondes.
- Une seule promesse : chaque phrase répond à l'accroche, aucune digression biographique.
- Phrases 2 à 4 : la preuve (date, lieu, chiffre). Vers le milieu, une relance (« Mais… », « Problème : », un chiffre, un retournement).
- Dernière phrase = la question au spectateur (« Toi, tu l'aurais gardée, cette pochette ? »), qui donne envie de commenter. Pas de carte finale « lien en bio » : la vidéo boucle, le lien est dans la légende.
- Chiffres et faits uniquement repris de l'article vérifié du jour.

## 4. Légende et hashtags

- Légende : 3 à 5 phrases courtes qui racontent l'histoire (elle sert de sous-titre à ceux qui coupent le son). Première phrase = l'accroche reformulée, pas recopiée de la carte. Avant-dernière phrase = la question finale de la narration. Dernière phrase : « L'histoire complète est sur riffsetlegendes.github.io, lien en bio. »
- 5 hashtags exactement : riffsetlegendes + l'artiste + le morceau ou l'album + 2 hashtags de niche francophones ou génériques (histoiredurock, anecdotemusicale, classicrock, rock70s, etc.).
- Mentions : comptes officiels vérifiés uniquement.

## 5. Reprendre des idées des comptes anglophones (autorisé par Yann)

Les sujets et les angles qui marchent en anglais peuvent être repris pour le public français, à condition de :

- revérifier chaque fait dans deux sources fiables, indépendantes du compte anglophone ;
- écrire avec nos propres mots, notre propre ordre de cartes et notre propre accroche : jamais de traduction d'une légende ou d'une carte, jamais la même première phrase ;
- ne jamais reprendre leurs vidéos, leurs montages ni leurs images ;
- laisser au moins 10 jours d'écart si le même compte vient de publier le même sujet, et préférer un angle différent (autre détail, autre date).

Comptes à surveiller (sources d'idées, pas de texte) : @musicandentertainmenthistory, @rockgrails, @sonic.index, @musicmomentshistory, @top.music.songs ; en français : @ggb.art.

## 6. Réservoir d'idées (à vérifier le jour J, à piocher selon la date)

Origine improbable (13 h) :
- Pourquoi Led Zeppelin s'appelle ainsi (le « ballon de plomb »)
- Pourquoi Pink Floyd (deux bluesmen de Caroline)
- Pourquoi AC/DC (l'inscription sur une machine à coudre)
- Pourquoi « A Hard Day's Night » (une phrase de Ringo)
- Pourquoi « Smells Like Teen Spirit » (un déodorant et un graffiti)
- Pourquoi « Smoke on the Water » (l'incendie du casino de Montreux, à caler le 4 décembre)
- Pourquoi les Beatles écrivent leur nom avec un « a »
- Pourquoi Ten (Pearl Jam) : déjà prévu le 22/10

Détail caché derrière une fin (8 h ou 18 h, à la date anniversaire) :
- 29 octobre 1971, Duane Allman
- 23 et 24 novembre 1991, Freddie Mercury : l'annonce publique la veille de sa mort
- 29 novembre 2001, George Harrison
- 8 décembre 1980, John Lennon : l'autographe signé quelques heures avant
- 3 février 1959, « The Day the Music Died » : la place cédée dans l'avion
- 29 août 1966, Candlestick Park : le dernier vrai concert des Beatles, enregistré en cachette sur cassette

## 7. Bilan du lundi

Chaque lundi, avant la production : relever dans Metricool (brandId 7397416, connecteur reels : IGRE02, IGRE03, IGRE23, IGRE11, IGRE27, IGRE28, IGRE21, IGRE12) les Reels des 7 derniers jours, calculer la médiane des vues, noter dans strategie/SWIPE.md (section « Mon compte ») les 3 meilleurs et les 3 moins bons avec leur concept, et ajuster le réservoir. Un Reel à 3 fois la médiane ou plus devient une recette : refaire le même concept sur un autre artiste dans les 14 jours.

Le premier lundi du mois : refaire l'étude de la niche avec Treg (anyapi.instagram.user.reels sur les comptes de la section 5 et 3 ou 4 nouveaux trouvés via anyapi.instagram.hashtag_top_posts sur #histoiredurock et #rockhistory), budget maximum 0,05 $, et mettre à jour les concepts de SWIPE.md.
