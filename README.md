# Riffs & Légendes

Le rock de 1950 à 1999, un jour à la fois. Site statique publié sur GitHub Pages :
https://yanncollin23.github.io/riffs-legendes/

## Ajouter un article

1. Créer un fichier Markdown dans `content/` (modèle : n'importe quel fichier existant).
   L'en-tête contient `title`, `slug`, `date`, `category` (ce-jour-la, legendes, anecdotes,
   playlists, actu), `event_year`, `image`, `image_alt`, `excerpt` et éventuellement `sources`,
   puis une ligne `---` et le texte.
2. Blocs spéciaux : `:::fiche`, `:::aussi Titre`, `:::ecoute`, `:::tracklist`
   (une ligne par élément, colonnes séparées par `|`).
3. Lancer `python3 build.py` (nécessite le paquet `markdown`), puis commit et push.
   Le site est servi depuis le dossier `docs/`.
