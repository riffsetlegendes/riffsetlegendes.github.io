#!/usr/bin/env python3
"""Génère le site statique Riffs & Légendes dans le dossier docs/.

Usage : python3 build.py
Chaque article est un fichier Markdown dans content/ avec un en-tête
« clé: valeur » terminé par une ligne « --- ».
"""
import datetime as dt
import html
import json
import re
import shutil
import urllib.parse
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
ASSETS = ROOT / "assets"
OUT = ROOT / "docs"

SITE_NAME = "Riffs & Légendes"
SITE_TAGLINE = "Le rock de 1950 à 1999, un jour à la fois"
SITE_URL = "https://yanncollin23.github.io/riffs-legendes"
BASE = "/riffs-legendes"

CATEGORIES = {
    "ce-jour-la": ("Ce jour-là", "Chaque matin, un anniversaire du rock : une naissance, une disparition, un disque ou un concert qui a compté."),
    "legendes": ("Légendes", "Les portraits de celles et ceux qui ont fait le rock, de 1950 à la fin du siècle."),
    "anecdotes": ("Anecdotes", "Les petites histoires derrière les grands morceaux."),
    "playlists": ("Playlists", "Des sélections à écouter, par époque, par humeur, par route."),
    "actu": ("Actu", "Rééditions, archives, coffrets et tournées des grands noms du rock."),
}

MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
          "août", "septembre", "octobre", "novembre", "décembre"]
DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def fr_date(d, weekday=False):
    s = f"{d.day} {MONTHS[d.month - 1]} {d.year}"
    if d.day == 1:
        s = f"1er {MONTHS[d.month - 1]} {d.year}"
    return (DAYS[d.weekday()] + " " + s) if weekday else s


def esc(s):
    return html.escape(s or "", quote=True)


def yt(title, artist):
    q = urllib.parse.quote_plus(f"{artist} {title}")
    return f"https://www.youtube.com/results?search_query={q}"


def url(path=""):
    return f"{BASE}/{path}".rstrip("/") + "/" if path else f"{BASE}/"


# ---------------------------------------------------------------- contenu

def parse_article(path):
    raw = path.read_text(encoding="utf-8")
    head, body = raw.split("\n---\n", 1)
    meta = {}
    for line in head.strip().splitlines():
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip()
    meta["date_obj"] = dt.datetime.strptime(meta["date"], "%Y-%m-%d %H:%M")
    meta["blocks"] = {}
    meta["body_md"] = body
    return meta


def rows(block):
    return [[c.strip() for c in l.split("|")] for l in block.strip().splitlines() if l.strip()]


def render_tracklist(items, cls="tracklist"):
    out = [f'<ol class="{cls}">']
    for i, (title, artist, year) in enumerate(items, 1):
        out.append(
            f'<li><a href="{esc(yt(title, artist))}" target="_blank" rel="noopener">'
            f'<span class="tl-n">{i}</span>'
            f'<span class="tl-t">{esc(title)}<span class="tl-a">{esc(artist)}, {esc(year)}</span></span>'
            f'<span class="tl-play" aria-hidden="true"></span></a></li>')
    out.append("</ol>")
    return "\n".join(out)


def render_body(meta):
    body = meta["body_md"]

    def fiche(m):
        items = rows(m.group(1))
        dl = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in items)
        return f'\n<aside class="notes"><h2>Notes de pochette</h2><dl>{dl}</dl></aside>\n'

    def aussi(m):
        title, items = m.group(1).strip(), rows(m.group(2))
        lis = "".join(f'<li><span class="yr">{esc(y)}</span><span>{esc(t)}</span></li>' for y, t in items)
        return f'\n<section class="also"><h2>{esc(title)}</h2><ul>{lis}</ul></section>\n'

    def ecoute(m):
        return f'\n<section class="listen"><h2>À écouter</h2>{render_tracklist(rows(m.group(1)))}</section>\n'

    def tracklist(m):
        return f'\n<section class="listen listen--full">{render_tracklist(rows(m.group(1)))}</section>\n'

    placeholders = {}

    def stash(fn):
        def inner(m):
            key = f"BLOCK{len(placeholders)}X"
            placeholders[key] = fn(m)
            return f"\n\n{key}\n\n"
        return inner

    body = re.sub(r":::fiche\n(.*?)\n:::", stash(fiche), body, flags=re.S)
    body = re.sub(r":::aussi ([^\n]*)\n(.*?)\n:::", stash(aussi), body, flags=re.S)
    body = re.sub(r":::ecoute\n(.*?)\n:::", stash(ecoute), body, flags=re.S)
    body = re.sub(r":::tracklist\n(.*?)\n:::", stash(tracklist), body, flags=re.S)
    out = markdown.markdown(body, extensions=["smarty"], extension_configs={
        "smarty": {"smart_quotes": False, "smart_dashes": False}})
    for k, v in placeholders.items():
        out = out.replace(f"<p>{k}</p>", v)
    return out


def load_articles():
    arts = [parse_article(p) for p in sorted(CONTENT.glob("*.md"))]
    arts.sort(key=lambda a: a["date_obj"], reverse=True)
    for a in arts:
        a["url"] = url(f"articles/{a['slug']}")
        a["cat_name"] = CATEGORIES[a["category"]][0]
    return arts


# ---------------------------------------------------------------- gabarits

FONTS = ("https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900"
         "&family=Newsreader:ital,opsz,wght@0,6..72,400..600;1,6..72,400&display=swap")


def layout(title, body, description="", canonical="", og_image="", body_class=""):
    full_title = f"{title} | {SITE_NAME}" if title != SITE_NAME else f"{SITE_NAME} : {SITE_TAGLINE.lower()}"
    nav = "".join(f'<a href="{url("rubriques/" + k)}">{v[0]}</a>' for k, v in CATEGORIES.items())
    og = f'<meta property="og:image" content="{esc(og_image)}">' if og_image else ""
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description or SITE_TAGLINE)}">
<link rel="canonical" href="{esc(canonical or SITE_URL + '/')}">
<meta property="og:site_name" content="{esc(SITE_NAME)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description or SITE_TAGLINE)}">
<meta property="og:locale" content="fr_FR">
{og}
<meta name="theme-color" content="#1b2390">
<link rel="icon" href="{BASE}/assets/favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="{esc(SITE_NAME)}" href="{BASE}/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{BASE}/assets/style.css">
</head>
<body class="{body_class}">
<a class="skip" href="#contenu">Aller au contenu</a>
<header class="site-head">
  <div class="wrap head-row">
    <a class="wordmark" href="{url()}" aria-label="{esc(SITE_NAME)}, accueil">Riffs <span class="amp">&amp;</span> Légendes</a>
    <nav class="nav" aria-label="Rubriques">{nav}<a class="nav-search" href="{url('recherche')}">Rechercher</a></nav>
  </div>
</header>
<main id="contenu">
{body}
</main>
<footer class="site-foot">
  <div class="wrap">
    <p class="foot-mark">Riffs <span class="amp">&amp;</span> Légendes</p>
    <div class="foot-row">
      <p>{esc(SITE_TAGLINE)}. Un article chaque matin, des portraits, des histoires et des disques à écouter.</p>
      <nav aria-label="Pied de page"><a href="{url('a-propos')}">À propos</a><a href="{BASE}/feed.xml">Flux RSS</a><a href="{url('recherche')}">Rechercher</a></nav>
    </div>
    <p class="foot-small">Illustrations générées par IA. Textes originaux, sources citées sous chaque article.</p>
  </div>
</footer>
</body>
</html>
"""


def sleeve(a, size="", eager=False):
    loading = "eager" if eager else "lazy"
    return (f'<div class="sleeve {size}"><div class="riso">'
            f'<img src="{esc(a["image"])}?w=1000" alt="{esc(a["image_alt"])}" loading="{loading}" decoding="async">'
            f'</div></div>')


def anniversary(a):
    y = a.get("event_year", "")
    if a["category"] == "ce-jour-la" and re.fullmatch(r"\d{4}", y):
        n = a["date_obj"].year - int(y)
        return n
    return None


def card(a, extra=""):
    return f"""<article class="card {extra}">
  <a class="card-link" href="{a['url']}">{sleeve(a)}
    <h3>{esc(a['title'])}</h3></a>
  <p class="card-meta">{esc(a.get('event_year', ''))}</p>
  <p class="card-ex">{esc(a['excerpt'])}</p>
</article>"""


# ---------------------------------------------------------------- pages

def page_home(arts):
    by = {k: [a for a in arts if a["category"] == k] for k in CATEGORIES}
    today = by["ce-jour-la"][0] if by["ce-jour-la"] else arts[0]
    d = today["date_obj"]
    n = anniversary(today)
    sticker = f'<span class="sticker"><b>{n}</b> ans</span>' if n else ""
    label_year = today.get("event_year", "")

    hero = f"""<section class="hero wrap">
  <div class="hero-text">
    <p class="hero-date"><a href="{url('rubriques/ce-jour-la')}">Ce jour-là</a>, {fr_date(d, weekday=True)}</p>
    <h1><a href="{today['url']}">{esc(today['title'])}</a></h1>
    <p class="hero-lede">{esc(today['excerpt'])}</p>
    <a class="btn" href="{today['url']}">Lire l'histoire</a>
  </div>
  <a class="record" href="{today['url']}" aria-label="{esc(today['title'])}">
    <span class="disc" aria-hidden="true"><span class="disc-label"><span class="dl-day">{d.day} {MONTHS[d.month-1][:3]}.</span><span class="dl-year">{esc(label_year)}</span></span></span>
    {sleeve(today, eager=True)}
    {sticker}
  </a>
</section>"""

    legends = "".join(card(a) for a in by["legendes"][:4])
    anecdotes = "".join(f"""<article class="anec">
  <a href="{a['url']}" class="anec-img"><div class="riso riso--yellow"><img src="{esc(a['image'])}?w=1000" alt="{esc(a['image_alt'])}" loading="lazy"></div></a>
  <p class="anec-year">{esc(a.get('event_year',''))}</p>
  <h3><a href="{a['url']}">{esc(a['title'])}</a></h3>
  <p>{esc(a['excerpt'])}</p>
</article>""" for a in by["anecdotes"][:2])

    playlists = ""
    for a in by["playlists"][:2]:
        m = re.search(r":::tracklist\n(.*?)\n:::", a["body_md"], re.S)
        tracks = rows(m.group(1))[:5] if m else []
        playlists += f"""<article class="pl">
  <a class="pl-cover" href="{a['url']}">{sleeve(a)}</a>
  <div class="pl-body">
    <h3><a href="{a['url']}">{esc(a['title'])}</a></h3>
    <p class="pl-years">{esc(a.get('event_year',''))}</p>
    {render_tracklist(tracks, 'tracklist tracklist--compact')}
    <a class="more" href="{a['url']}">Toute la playlist</a>
  </div>
</article>"""

    news = "".join(f"""<li><a href="{a['url']}"><time datetime="{a['date_obj']:%Y-%m-%d}">{fr_date(a['date_obj'])}</time>
<span class="news-t">{esc(a['title'])}</span><span class="news-ex">{esc(a['excerpt'])}</span></a></li>""" for a in by["actu"][:4])

    body = f"""{hero}
<section class="block wrap">
  <div class="block-head"><h2>Légendes</h2><a class="more" href="{url('rubriques/legendes')}">Tous les portraits</a></div>
  <div class="bin">{legends}</div>
</section>
<section class="band">
  <div class="wrap">
    <div class="block-head"><h2>Anecdotes</h2><a class="more" href="{url('rubriques/anecdotes')}">Toutes les histoires</a></div>
    <div class="anec-grid">{anecdotes}</div>
  </div>
</section>
<section class="block wrap">
  <div class="block-head"><h2>Playlists</h2><a class="more" href="{url('rubriques/playlists')}">Toutes les playlists</a></div>
  <div class="pl-grid">{playlists}</div>
</section>
<section class="block wrap news">
  <div class="block-head"><h2>L'actu des classiques</h2><a class="more" href="{url('rubriques/actu')}">Toute l'actu</a></div>
  <ul class="news-list">{news}</ul>
</section>"""
    return layout(SITE_NAME, body, SITE_TAGLINE, SITE_URL + "/", today["image"] + "?w=1200", "home")


def page_article(a, arts):
    d = a["date_obj"]
    n = anniversary(a)
    sticker = f'<span class="sticker"><b>{n}</b> ans</span>' if n else ""
    related = [r for r in arts if r["category"] == a["category"] and r["slug"] != a["slug"]][:3]
    if len(related) < 3:
        related += [r for r in arts if r["slug"] != a["slug"] and r not in related][:3 - len(related)]
    rel = "".join(card(r) for r in related)
    sources = f'<p class="sources">Sources : {markdown.markdown(a["sources"])[3:-4]}.</p>' if a.get("sources") else ""
    share = urllib.parse.quote(SITE_URL + a["url"].replace(BASE, ""), safe="")
    body = f"""<article class="post wrap">
  <div class="post-cover"><div class="post-cover-in">{sleeve(a, eager=True)}{sticker}</div></div>
  <header class="post-title">
    <p class="post-kicker"><a href="{url('rubriques/' + a['category'])}">{esc(a['cat_name'])}</a>, <time datetime="{d:%Y-%m-%d}">{fr_date(d)}</time></p>
    <h1>{esc(a['title'])}</h1>
    <p class="post-lede">{esc(a['excerpt'])}</p>
  </header>
    <div class="prose">
{render_body(a)}
      {sources}
      <div class="share">
        <button type="button" class="btn btn--ghost" data-copy="{esc(SITE_URL + a['url'].replace(BASE, ''))}">Copier le lien</button>
        <a class="btn btn--ghost" href="https://www.facebook.com/sharer/sharer.php?u={share}" target="_blank" rel="noopener">Partager sur Facebook</a>
      </div>
    </div>
</article>
<section class="block wrap">
  <div class="block-head"><h2>À lire aussi</h2></div>
  <div class="bin bin--3">{rel}</div>
</section>
<script>
document.querySelectorAll('[data-copy]').forEach(function(b){{b.addEventListener('click',function(){{var t=b.getAttribute('data-copy');var done=function(){{b.textContent='Lien copié';setTimeout(function(){{b.textContent='Copier le lien'}},2000)}};if(navigator.clipboard){{navigator.clipboard.writeText(t).then(done,function(){{prompt('Copiez ce lien :',t)}})}}else{{prompt('Copiez ce lien :',t)}}}})}});
</script>"""
    return layout(a["title"], body, a["excerpt"], SITE_URL + a["url"].replace(BASE, ""), a["image"] + "?w=1200", "article")


def page_category(key, arts):
    name, desc = CATEGORIES[key]
    items = [a for a in arts if a["category"] == key]
    grid = "".join(card(a) for a in items) or '<p class="empty">Les premiers articles arrivent bientôt.</p>'
    body = f"""<section class="cat-head wrap"><h1>{esc(name)}</h1><p>{esc(desc)}</p></section>
<section class="block wrap"><div class="bin bin--3">{grid}</div></section>"""
    return layout(name, body, desc, f"{SITE_URL}/rubriques/{key}/")


def page_search():
    body = f"""<section class="cat-head wrap"><h1>Rechercher</h1><p>Un artiste, un album, une année : tout le site est passé en revue.</p>
<form class="search" role="search" onsubmit="return false">
  <label for="q" class="sr">Rechercher sur le site</label>
  <input id="q" type="search" placeholder="Hendrix, 1971, Montreux…" autocomplete="off">
</form></section>
<section class="block wrap"><p id="count" class="search-count" aria-live="polite"></p><div id="results" class="bin bin--3"></div></section>
<script>
(function(){{
  var idx=[],q=document.getElementById('q'),res=document.getElementById('results'),count=document.getElementById('count');
  function norm(s){{return (s||'').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'')}}
  function esc(s){{return s.replace(/[&<>"]/g,function(c){{return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]}})}}
  function show(){{
    var t=norm(q.value.trim());
    var hits=t?idx.filter(function(a){{return a.hay.indexOf(t)>-1}}):idx;
    count.textContent=t?(hits.length?hits.length+' résultat'+(hits.length>1?'s':''):'Aucun résultat. Essayez un nom d\\'artiste ou une année.'):'Tous les articles';
    res.innerHTML=hits.map(function(a){{return '<article class="card"><a class="card-link" href="'+a.url+'"><div class="sleeve"><div class="riso"><img src="'+a.image+'?w=600" alt="" loading="lazy"></div></div><h3>'+esc(a.title)+'</h3></a><p class="card-meta">'+esc(a.cat)+'</p><p class="card-ex">'+esc(a.excerpt)+'</p></article>'}}).join('');
  }}
  fetch('{BASE}/search.json').then(function(r){{return r.json()}}).then(function(d){{idx=d.map(function(a){{a.hay=norm(a.title+' '+a.excerpt+' '+a.text+' '+a.cat);return a}});var p=new URLSearchParams(location.search).get('q');if(p)q.value=p;show()}});
  q.addEventListener('input',show);
}})();
</script>"""
    return layout("Rechercher", body, "Rechercher un artiste, un album ou une année.", f"{SITE_URL}/recherche/")


def page_about():
    body = f"""<section class="cat-head wrap"><h1>À propos</h1></section>
<section class="block wrap"><div class="prose">
<p>Riffs &amp; Légendes raconte le rock de 1950 à 1999, un jour à la fois. Chaque matin, un anniversaire : la naissance d'un artiste, une disparition, la sortie d'un disque ou un concert qui a compté.</p>
<p>Autour de ce rendez-vous quotidien, le site publie des portraits de légendes, les histoires qui se cachent derrière les grands morceaux, des playlists à écouter et l'actualité des rééditions.</p>
<p>Les faits sont vérifiés dans plusieurs sources, citées sous chaque article. Les illustrations sont générées par intelligence artificielle : elles évoquent une époque ou une ambiance, jamais une personne réelle.</p>
</div></section>"""
    return layout("À propos", body, "Le projet Riffs & Légendes.", f"{SITE_URL}/a-propos/")


def feed(arts):
    items = "".join(f"""<item><title>{esc(a['title'])}</title><link>{SITE_URL}{a['url'].replace(BASE, '')}</link>
<guid>{SITE_URL}{a['url'].replace(BASE, '')}</guid><pubDate>{a['date_obj']:%a, %d %b %Y %H:%M:00} +0200</pubDate>
<category>{esc(a['cat_name'])}</category><description>{esc(a['excerpt'])}</description></item>""" for a in arts[:30])
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>{esc(SITE_NAME)}</title><link>{SITE_URL}/</link>
<description>{esc(SITE_TAGLINE)}</description><language>fr</language>{items}</channel></rss>
"""


def write(path, text):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main():
    arts = load_articles()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ASSETS, OUT / "assets")
    write("index.html", page_home(arts))
    for a in arts:
        write(f"articles/{a['slug']}/index.html", page_article(a, arts))
    for k in CATEGORIES:
        write(f"rubriques/{k}/index.html", page_category(k, arts))
    write("recherche/index.html", page_search())
    write("a-propos/index.html", page_about())
    write("feed.xml", feed(arts))
    index = [{"title": a["title"], "url": a["url"], "image": a["image"], "cat": a["cat_name"],
              "excerpt": a["excerpt"], "text": re.sub(r"[#*:|]", " ", a["body_md"])} for a in arts]
    write("search.json", json.dumps(index, ensure_ascii=False))
    urls = [SITE_URL + "/"] + [SITE_URL + a["url"].replace(BASE, "") for a in arts] + \
           [f"{SITE_URL}/rubriques/{k}/" for k in CATEGORIES]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    write(".nojekyll", "")
    write("404.html", layout("Page introuvable", f'<section class="cat-head wrap"><h1>Face introuvable</h1><p>Cette page n\'existe pas ou a changé d\'adresse.</p><p><a class="btn" href="{url()}">Revenir à l\'accueil</a></p></section>'))
    print(f"{len(arts)} articles générés dans {OUT}")


if __name__ == "__main__":
    main()
