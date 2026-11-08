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

**Horaires (23/10) :** GitHub lance les crons avec ~35 min de retard, d’où des crons à 6 h 25, 11 h 25 et 16 h 25 UTC (heure d’hiver, passés le 25/10). À partir du passage à l’heure d’hiver (25/10), les décaler d’une heure (6 h 40, 11 h 40, 16 h 40 UTC) dans .github/workflows/instagram.yml, lignes schedule ET tests elif.

**Publication (règle de Yann du 04/11) : Metricool EN PRIORITÉ, puis l'API Instagram une fois la limite atteinte.** Le forfait gratuit publie 20 posts par mois (compteur remis à zéro le 1er, seuls les posts publiés comptent). Le fichier strategie/metricool-quota.json tient le compte. Tant que utilises < 20 et epuise = false : programmer chaque Reel dans Metricool (createScheduledPost, blogId 7397416, type REEL, media = URL raw ig-media du reel.mp4, audioConfiguration {audioId: l'audio_id du JSON, audioVolume 100, videoVolume 0}), écrire aussitôt instagram/publies/AAAA-MM-JJ-<clé>-reel.txt ({"via":"metricool","post":id,"uuid":...}) pour que le cron GitHub ne publie pas en double, incrémenter utilises, commit + push. À la vérification (+30 min) : si le post Metricool est en ERROR (« account limit » ou autre), supprimer le marqueur, mettre epuise = true, et lancer le workflow kind=<clé> dry_run=false (API Instagram). Quand epuise = true (ou au changement de mois, remettre à zéro), ne rien programmer dans Metricool : le cron GitHub publie seul par l'API.

Ancienne règle : **Publication (21/10) : quota Metricool atteint.** Les Reels partent par le workflow GitHub programmé (cron 8 h, 13 h, 18 h, tools/ig_publish.py, API Instagram) avec le vrai morceau : mettre "audio_id" dans le JSON (liste des sons via dispatch kind=audio:<Titre Artiste>), sinon recherche automatique d'après "song". Le marqueur instagram/publies/ est écrit par le workflow. Ne plus programmer dans Metricool tant que le quota n'est pas revenu.

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

Classer avec ces mesures, pas avec les vues brutes (méthode ig-audit, montrer le calcul) :

| Mesure | Calcul | Ce qu'elle juge |
|---|---|---|
| Multiple | vues ÷ médiane du compte (30 derniers Reels) | vrai succès ou journée normale |
| Portée hors abonnés | % de la portée venant de non-abonnés | le Reel a-t-il voyagé |
| Temps regardé moyen | Metricool | le milieu a-t-il tenu |
| Partages par portée | partages ÷ portée | le signal le plus fort : quelqu'un met son nom dessus |
| Abonnements par portée | abonnements gagnés ÷ portée | le profil convertit-il |

Puis comparer les 3 meilleurs et les 3 moins bons dans cet ordre, et s'arrêter au premier écart net : temps regardé (si c'est là que ça diffère, c'est l'accroche et rien d'autre), formule d'accroche (§8), concept (§1), durée, thème, créneau horaire (en dernier). Noter la conclusion en une phrase dans SWIPE.md, même si elle contredit la stratégie.

## 8. Accroches et contrôle qualité (pack instagram-agent, adapté)

**L'accroche (phrase 1 de la narration).** 12 mots maximum, lisible en 2 secondes, le fait étrange ou la question avec un élément concret (nom, nombre, objet) dans les 6 premiers mots. Jamais de date seule en ouverture, de salutation, de « Aujourd'hui », « Le saviez-vous », « Retour sur », « Dans cette vidéo ». Écrire 3 accroches avec des formules différentes, garder la plus concrète. Formules qui marchent pour l'histoire du rock :

| Formule | Exemple de moule |
|---|---|
| Pourquoi (origine) | « Pourquoi Kiss s'appelle Kiss ? » |
| Le prix | « Une limousine refusée lui a coûté la vie. » |
| Contre-pied | « Ce tube devait finir en face B. » |
| Personne ne savait | « Personne ne savait que c'était leur dernier concert. » |
| Le chiffre | « Trois accords. Quarante millions de disques. » |
| Le seul / le premier | « Le seul album que Bowie a renié. » |
| Deux dates | « Viré en 1975, numéro un en 1980. » |
| L'objet | « Cette cassette a sauvé le dernier concert des Beatles. » |
| En pleine action | « Le batteur s'endort au milieu du concert. » |
| Le témoin oublié | « Un ingénieur de 19 ans a sauvé cet album. » |

Noter la formule retenue dans le JSON (champ "hook_formule") pour que le bilan du lundi puisse les comparer.

**Rythme.** Une phrase = une photo : au-delà de 16 mots (≈ 8 s), la photo reste fixe trop longtemps et c'est là qu'on décroche ; couper en deux. Une relance au milieu (« Mais… », « Problème : », un chiffre, un retournement). La dernière phrase de la narration est la question, et seulement elle (= "cta").

**Légende.** Seuls les ~125 premiers caractères s'affichent avant « … plus » : la 1re phrase tient dedans, reformule l'accroche sans la recopier et finit sur une curiosité, pas au milieu d'une idée.

**Contrôle obligatoire avant commit :**

```
python3 tools/ig_qa.py instagram/AAAA-MM-JJ-*.json --content content --fix
python3 tools/ig_qa.py content/AAAA-MM-JJ-*.md
```

Zéro ÉCHEC avant commit. Les ALERTES se corrigent sauf raison précise (à dire dans le message à Yann). Le script nettoie seul les caractères invisibles, tirets cadratins et apostrophes courbes (--fix), et signale sans les réécrire les tics d'écriture IA, les chiffres absents de l'article du jour et les comparaisons relève/anciens (vérifier le contexte : « les héritiers de Janis » n'en est pas une).

## 9. Story du jour (Yann la poste lui-même)

Partager le Reel en story sans rien ajouter est la story la plus ignorée de la plateforme. Chaque jour, le message à Yann propose pour le Reel le plus fort un sticker prêt à coller : un **quiz** (la question de l'accroche avec 3 réponses dont la vraie, ex. « Pourquoi AC/DC ? Une machine à coudre / Un ampli / Un juron ») ou un **sondage** (la question finale en deux choix). Texte au centre de l'écran, une idée, tutoiement. Réponse donnée dans la story suivante ou en commentaire du Reel.

Le premier lundi du mois : refaire l'étude de la niche avec Treg (anyapi.instagram.user.reels sur les comptes de la section 5 et 3 ou 4 nouveaux trouvés via anyapi.instagram.hashtag_top_posts sur #histoiredurock et #rockhistory), budget maximum 0,05 $, et mettre à jour les concepts de SWIPE.md.

## 10. Test « suspense » (semaine du 09/11/2026, idée tirée de la pub RTL2 repérée par Yann)
- Sur 1 Reel par jour (l'anecdote de 13 h) : 6 à 7 phrases au présent, racontées comme une scène (un lieu, un geste) ; l'avant-dernière phrase s'arrête juste avant la chute.
- Dernière phrase et "cta" : renvoi explicite, ex. « La fin de l'histoire est sur le site, lien en bio. » (pas de question ce jour-là).
- Durée visée : 30 à 40 s.
- Au bilan du 16/11 : comparer la rétention et les visites du site (articles des Reels « suspense » contre les autres).
