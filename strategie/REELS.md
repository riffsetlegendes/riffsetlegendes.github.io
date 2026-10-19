# Stratégie Reels Riffs & Légendes (mise à jour du 19/10/2026)

À lire avant de choisir les sujets et d'écrire les 3 Reels du jour. Les preuves chiffrées sont dans strategie/SWIPE.md.

## 1. Ce qui fait les vues dans la niche

Deux concepts portent la quasi-totalité des Reels qui dépassent 3 fois la médiane de leur compte :

- **L'origine improbable** : pourquoi un groupe, un album, un logo ou un son s'appelle ou sonne ainsi. Exemple de moule : « Pourquoi le premier album de Pearl Jam s'appelle Ten ? »
- **Le détail caché derrière une fin** : un dernier concert que personne ne savait être le dernier, un drame, une disparition, avec UN détail que le public ignore. Toujours calé sur la date du jour.

Ce qui ne marche pas : la biographie « de X à Y en N albums », l'hommage générique sans détail, la liste de sorties du jour, le simple « joyeux anniversaire ».

## 2. Le format : le récit narré, sur les trois créneaux

Décision de Yann du 19/10 (carte blanche) : le format « recit » de tools/reel_formats.py REMPLACE journal, countdown et docu pour tous les Reels. C'est la forme de tous les Reels viraux de la niche : une voix off qui raconte, des photos plein écran qui bougent, de gros sous-titres mot à mot, une accroche parlée dès la première seconde.

| Créneau | Fichier | Concept imposé |
|---|---|---|
| 8 h | instagram/AAAA-MM-JJ-jour.json | Détail caché derrière une fin, ou anniversaire + fait étrange (date du jour) |
| 13 h | instagram/AAAA-MM-JJ-anecdote.json | Origine improbable (« Pourquoi… ? ») ou « deux dates » (chute puis triomphe) |
| 18 h | instagram/AAAA-MM-JJ-focus.json | Coulisses d'un disque, détail caché, ou relève sous l'angle d'une origine ou d'une actu |

Champs du JSON : "format": "recit", "title" (bandeau jaune fixe en haut, 30 caractères maximum, une promesse), "narration" [{"text", "photo"}], "photos" (4 à 6, toutes différentes), "song", "caption", "hashtags", "reel": true, "label", "big". Facultatifs : "voice" (défaut fr-FR-HenriNeural), "rate" (défaut +8 %). Le champ "slides" n'est plus utilisé.

Musique à la publication Metricool : le vrai morceau de l'artiste PASSE SOUS LA VOIX, audioConfiguration {audioId, audioVolume: 15, videoVolume: 100}. Jamais audioVolume 100 / videoVolume 0 sur un récit, sinon la voix disparaît.

Contrôle du rendu (workflow dry_run) : la vidéo doit durer 30 à 45 s, la voix doit s'entendre (ffmpeg volumedetect, mean_volume autour de -16 dB), les sous-titres ne débordent pas.

## 3. Règles d'écriture de la narration

- 80 à 110 mots, 7 à 9 phrases courtes (une phrase = une photo ou un plan). Écrit pour l'oreille : phrases simples, verbes au présent, aucun sigle obscur, nombres que l'on peut dire à voix haute.
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
