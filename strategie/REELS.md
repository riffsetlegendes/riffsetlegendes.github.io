# Stratégie Reels Riffs & Légendes (mise à jour du 19/10/2026)

À lire avant de choisir les sujets et d'écrire les 3 Reels du jour. Les preuves chiffrées sont dans strategie/SWIPE.md.

## 1. Ce qui fait les vues dans la niche

Deux concepts portent la quasi-totalité des Reels qui dépassent 3 fois la médiane de leur compte :

- **L'origine improbable** : pourquoi un groupe, un album, un logo ou un son s'appelle ou sonne ainsi. Exemple de moule : « Pourquoi le premier album de Pearl Jam s'appelle Ten ? »
- **Le détail caché derrière une fin** : un dernier concert que personne ne savait être le dernier, un drame, une disparition, avec UN détail que le public ignore. Toujours calé sur la date du jour.

Ce qui ne marche pas : la biographie « de X à Y en N albums », l'hommage générique sans détail, la liste de sorties du jour, le simple « joyeux anniversaire ».

## 2. Les trois créneaux

| Créneau | Format (reel_formats.py) | Concept imposé | Règle d'accroche |
|---|---|---|---|
| 8 h | journal | Détail caché derrière une fin, ou anniversaire + fait étrange | title = une affirmation qui contient le fait étrange, jamais une date seule ni un simple nom d'album |
| 13 h | countdown | Origine improbable (en priorité) ou « deux dates » (chute puis triomphe) | hook = une question « Pourquoi… ? » ou une affirmation surprenante, 12 mots maximum |
| 18 h | docu | Détail caché derrière une fin, coulisses d'un disque ou relève sous l'angle d'une origine ou d'une actu | title = une promesse précise, jamais « portrait de X » |

Le choix du sujet du jour se fait d'abord sur le concept, ensuite sur l'artiste. Un sujet sans fait étrange vérifiable ne passe pas en Reel (il peut rester un article du site).

## 3. Règles d'écriture des cartes

- Première carte : le fait étrange ou la question, avec un élément précis (nom, nombre, objet). Le spectateur doit comprendre le sujet en 1 seconde.
- Une seule promesse : chaque carte répond à l'accroche, aucune digression biographique.
- Les cartes 2 et 3 apportent la preuve (date, lieu, chiffre). L'avant-dernière relance (« Mais ce n'est pas le plus fou », un chiffre, un retournement).
- Chiffres et faits uniquement repris de l'article vérifié du jour.
- Champ "cta" (nouveau, affiché sur la carte finale) : UNE question précise liée à l'histoire, 60 caractères maximum, qui donne envie de répondre en commentaire. Exemples : « Tu l'aurais gardée, cette pochette ? », « Tu connaissais l'origine de ce nom ? ». Jamais « Like si… », « Tague un ami ».

## 4. Légende et hashtags

- Légende : 3 à 5 phrases courtes qui racontent l'histoire (elle sert de sous-titre à ceux qui coupent le son). Première phrase = l'accroche reformulée, pas recopiée de la carte. Avant-dernière phrase = la question du "cta". Dernière phrase : « L'histoire complète est sur riffsetlegendes.github.io, lien en bio. »
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
