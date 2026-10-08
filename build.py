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
OUT = ROOT / "docs"  # remplacé plus bas par la racine pour un dépôt <compte>.github.io

SITE_NAME = "Riffs & Légendes"
SITE_TAGLINE = "Le rock de 1950 à 1999, un jour à la fois"
import os
# Adresse du site. Dépôt « <compte>.github.io » : site servi à la racine.
def _origin():
    """Déduit le compte et le dépôt GitHub depuis le remote « origin »."""
    import subprocess
    try:
        u = subprocess.run(["git", "remote", "get-url", "origin"], cwd=Path(__file__).parent,
                           capture_output=True, text=True, check=True).stdout.strip()
        parts = u.rstrip("/").removesuffix(".git").split("/")
        return parts[-2], parts[-1]
    except Exception:
        return "riffsetlegendes", "riffsetlegendes.github.io"


_o, _r = _origin()
OWNER = os.environ.get("RL_OWNER", _o)
REPO = os.environ.get("RL_REPO", _r)
if REPO.endswith(".github.io"):
    SITE_URL = f"https://{REPO}"
    BASE = ""
    OUT = ROOT  # GitHub Pages sert la branche main à la racine
else:
    SITE_URL = f"https://{OWNER}.github.io/{REPO}"
    BASE = f"/{REPO}"

CATEGORIES = {
    "ce-jour-la": ("Ce jour-là", "Chaque matin, un anniversaire du rock : une naissance, une disparition, un disque ou un concert qui a compté."),
    "legendes": ("Légendes", "Les portraits de celles et ceux qui ont fait le rock, de 1950 à la fin du siècle."),
    "anecdotes": ("Anecdotes", "Les petites histoires derrière les grands morceaux."),
    "releve": ("La relève", "Les groupes d'aujourd'hui qui jouent un rock à guitares, chaud et organique : sorties, tournées et coups de cœur."),
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


def fr_typo(s):
    s = (s or "").replace("« ", "«\u00a0").replace(" »", "\u00a0»")
    return re.sub(r" ([;?!:])(?=\s|$)", "\u00a0\\1", s)


def esc(s):
    return html.escape(fr_typo(s if isinstance(s, str) else str(s or "")), quote=True)


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
        if ":" not in line:
            continue
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
    for i, row in enumerate(items, 1):
        title, artist, year = row[:3]
        sid = row[3] if len(row) > 3 else ""
        inner = (f'<span class="tl-n">{i}</span>'
                 f'<span class="tl-t">{esc(title)}<span class="tl-a">{esc(artist)}, {esc(year)}</span></span>'
                 f'<span class="tl-play" aria-hidden="true"></span>')
        if sid:
            out.append(f'<li><button type="button" class="tl-row" data-uri="spotify:track:{esc(sid)}" '
                       f'data-title="{esc(title)}" data-artist="{esc(artist)}" '
                       f'aria-label="Écouter {esc(title)}, {esc(artist)}">{inner}</button></li>')
        else:
            out.append(f'<li><a class="tl-row" href="{esc(yt(title, artist))}" target="_blank" rel="noopener">{inner}</a></li>')
    out.append("</ol>")
    return "\n".join(out)


PLAY_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4.5v15l13-7.5z" fill="currentColor"/></svg>'


def listen_head(items):
    if not any(len(r) > 3 for r in items):
        return ""
    return (f'<div class="listen-cta"><button type="button" class="btn" data-play-all>{PLAY_ICON}Écouter</button>'
            f'<p>Lecture via Spotify : extraits de 30 secondes, titres complets si vous êtes connecté à votre compte.</p></div>')


def render_body(meta):
    body = meta["body_md"]
    # typographie française : espaces insécables devant : ; ? ! et dans les guillemets
    body = body.replace("« ", "«\u00a0").replace(" »", "\u00a0»")
    body = re.sub(r" ([;?!])", "\u202f\\1", body)
    body = re.sub(r"(\w) :(\s)", "\\1\u00a0:\\2", body)

    def fiche(m):
        items = rows(m.group(1))
        dl = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in items)
        return f'\n<aside class="notes"><h2>Notes de pochette</h2><dl>{dl}</dl></aside>\n'

    def aussi(m):
        title, items = m.group(1).strip(), rows(m.group(2))
        lis = "".join(f'<li><span class="yr">{esc(y)}</span><span>{esc(t)}</span></li>' for y, t in items)
        return f'\n<section class="also"><h2>{esc(title)}</h2><ul>{lis}</ul></section>\n'

    def ecoute(m):
        r = rows(m.group(1))
        return f'\n<section class="listen" data-queue><h2>À écouter</h2>{listen_head(r)}{render_tracklist(r)}</section>\n'

    def thisis(m):
        out = []
        for r in rows(m.group(1)):
            if len(r) < 2 or not r[1].strip():
                continue
            name, pid = r[0].strip(), r[1].strip()
            out.append(f'''<figure class="thisis"><figcaption><span class="ti-k">Playlist Spotify</span><strong>This Is {esc(name)}</strong><span class="ti-n">L'essentiel de {esc(name)} réuni par Spotify, à écouter ici ou dans l'application.</span><a href="https://open.spotify.com/playlist/{esc(pid)}" rel="noopener" target="_blank">Ouvrir dans Spotify</a></figcaption><iframe title="This Is {esc(name)} sur Spotify" src="https://open.spotify.com/embed/playlist/{esc(pid)}?utm_source=generator" height="452" loading="lazy" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe></figure>''')
        return "\n" + "".join(out) + "\n" if out else ""

    def tracklist(m):
        r = rows(m.group(1))
        return f'\n<section class="listen listen--full" data-queue>{listen_head(r)}{render_tracklist(r)}</section>\n'

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
    body = re.sub(r":::thisis\n(.*?)\n:::", stash(thisis), body, flags=re.S)
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

import hashlib as _h
ASSET_V = _h.md5((ROOT / "assets" / "style.css").read_bytes() + (ROOT / "assets" / "site.js").read_bytes()).hexdigest()[:8]

FONTS = ("https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900"
         "&family=Big+Shoulders+Display:wght@600..900&family=DM+Mono:wght@500"
         "&family=Newsreader:ital,opsz,wght@0,6..72,400..600;1,6..72,400&display=swap")


def layout(title, body, description="", canonical="", og_image="", body_class="", head_extra=""):
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
<link rel="preload" href="{BASE}/assets/fonts/bigshoulders.woff" as="font" type="font/woff" crossorigin>
<link rel="preload" href="{BASE}/assets/fonts/newsreader.woff" as="font" type="font/woff" crossorigin>
<link rel="manifest" href="{BASE}/manifest.webmanifest">
<link rel="apple-touch-icon" href="{BASE}/assets/icon-512.png">
<meta name="twitter:card" content="summary_large_image">
{head_extra}
<link rel="stylesheet" href="{BASE}/assets/style.css?v={ASSET_V}">
</head>
<body class="{body_class}">
<a class="skip" href="#contenu">Aller au contenu</a>
<header class="site-head">
  <div class="wrap head-row">
    <a class="wordmark" href="{url()}" aria-label="{esc(SITE_NAME)}, accueil"><img class="mark" src="{BASE}/assets/symbole.svg" alt="" width="42" height="42"><span class="wm-text"><span class="wm-1">Riffs <span class="amp">&amp;</span></span><span class="wm-2">Légendes</span></span></a>
    <nav class="nav" aria-label="Rubriques">{nav}<a href="{url('concerts')}">Concerts</a><a href="{url('bibliotheque')}">Bibliothèque</a><a class="nav-search" href="{url('recherche')}">Rechercher</a><a class="nav-ig" href="https://www.instagram.com/riffsetlegendes/" target="_blank" rel="noopener" aria-label="Instagram @riffsetlegendes"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.4" cy="6.6" r="1.3" fill="currentColor"/></svg></a></nav>
  </div>
</header>
<main id="contenu">
{body}
</main>
<div class="dock" id="dock" hidden>
  <div class="dock-in">
    <div class="dock-now"><span class="dock-disc" aria-hidden="true"></span>
      <p class="dock-text" aria-live="polite"><span class="dock-title"></span><span class="dock-artist"></span></p></div>
    <div class="dock-ctrl">
      <button type="button" class="dock-btn" data-act="prev" aria-label="Morceau précédent"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 5h2v14H6zM20 5v14L9 12z" fill="currentColor"/></svg></button>
      <button type="button" class="dock-btn" data-act="next" aria-label="Morceau suivant"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16 5h2v14h-2zM4 5v14l11-7z" fill="currentColor"/></svg></button>
      <button type="button" class="dock-btn" data-act="close" aria-label="Fermer le lecteur"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.4 5 12 10.6 17.6 5 19 6.4 13.4 12l5.6 5.6-1.4 1.4L12 13.4 6.4 19 5 17.6 10.6 12 5 6.4z" fill="currentColor"/></svg></button>
    </div>
    <div class="dock-embed"><div id="spotify-embed"></div></div>
  </div>
</div>
<footer class="site-foot">
  <div class="wrap">
    <p class="foot-mark">Riffs <span class="amp">&amp;</span> Légendes</p>
    <div class="foot-row">
      <p>{esc(SITE_TAGLINE)}. Un article chaque matin, des portraits, des histoires et des disques à écouter.</p>
      <nav aria-label="Pied de page"><a href="{url('archives')}">Archives</a><a href="{url('a-propos')}">À propos</a><a href="{url('credits')}">Crédits photos</a><a href="{url('mentions-legales')}">Mentions légales</a><a href="https://www.instagram.com/riffsetlegendes/" rel="me noopener" target="_blank">Instagram</a><a href="{BASE}/feed.xml">Flux RSS</a></nav>
    </div>
    <p class="foot-small">Textes originaux, sources citées sous chaque article. Photos d'archives : Wikimedia Commons, licences libres. Extraits musicaux : Spotify.</p>
  </div>
</footer>
<script src="{BASE}/assets/site.js?v={ASSET_V}" defer></script>
<script data-goatcounter="https://riffetlegendes.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
"""


def commons_file(a):
    src = a.get("image", "")
    return src.split(":", 1)[1].strip() if src.startswith("commons:") else ""


def commons_page(name):
    return "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(name)


def img_src(a, w=1000):
    src = a.get("image", "")
    if not src:
        return ""
    f = commons_file(a)
    if f:
        return f"https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(f)}?width={w}"
    if src.startswith("http"):
        if "wordpress.com" in src:
            return "https://i0.wp.com/" + src.split("://", 1)[1] + f"?w={w}"
        return src
    return f"{BASE}/{src.lstrip('/')}"


def credit(a):
    f = commons_file(a)
    cap = esc(a.get("image_caption", ""))
    if f:
        return (f'<figcaption class="credit">{cap} Photo : <a href="{esc(commons_page(f))}" target="_blank" rel="noopener">'
                f'Wikimedia Commons</a>, licence libre (auteur et licence sur la page de la photo).</figcaption>')
    return f'<figcaption class="credit">{cap}</figcaption>' if cap else ""


def art(a, extra="", eager=False):
    """Visuel bichrome de l'article, ou pochette typographique s'il n'a pas d'image."""
    label = esc(a.get("event_year") or str(a["date_obj"].year))
    cat = esc(a["cat_name"])
    if not a.get("image"):
        cat_no = f'R&amp;L {a["date_obj"].strftime("%m%d")}'
        who = esc(a.get("cover_artist", ""))
        sub = esc(a.get("cover_sub", ""))
        foot = (f'<span class="tc-who">{who}</span>' if who else "") + (f'<span class="tc-sub">{sub}</span>' if sub else "")
        return (f'<div class="riso type-cover {extra}" role="img" aria-label="{esc(a["title"])}">'
                f'<span class="tc-top"><span class="tc-cat">{cat}</span><span class="tc-no">{cat_no}</span></span>'
                f'<span class="tc-main"><span class="tc-year">{label}</span>{foot}</span></div>')
    loading = "eager" if eager else "lazy"
    return (f'<div class="riso {extra}" data-cat="{cat}" data-label="{label}"><img src="{esc(img_src(a))}" '
            f'alt="{esc(a.get("image_alt", ""))}" loading="{loading}" decoding="async"></div>')


def sleeve(a, size="", eager=False):
    return f'<div class="sleeve {size}">{art(a, eager=eager)}</div>'


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

def page_home(arts, concerts=()):
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
    releve = "".join(card(a) for a in by["releve"][:4])
    concerts_block = ""
    if concerts:
        concerts_block = f"""<section class="block wrap concerts-home">
  <div class="block-head"><h2>Concerts</h2><a class="more" href="{url('concerts')}">Tout le calendrier</a></div>
  <div class="tickets tickets--home">{''.join(ticket(c, compact=True) for c in concerts[:4])}</div>
</section>"""
    anecdotes = "".join(f"""<article class="anec">
  <a href="{a['url']}" class="anec-img">{art(a, "riso--yellow")}</a>
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
    <div data-queue>{render_tracklist(tracks, 'tracklist tracklist--compact')}</div>
    <a class="more" href="{a['url']}">Toute la playlist</a>
  </div>
</article>"""

    news = "".join(f"""<li><a href="{a['url']}"><span class="news-thumb">{art(a)}</span><time datetime="{a['date_obj']:%Y-%m-%d}">{fr_date(a['date_obj'])}</time>
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
{concerts_block}
<section class="block wrap releve">
  <div class="block-head"><h2>La relève</h2><a class="more" href="{url('rubriques/releve')}">Toute la relève</a></div>
  <p class="block-intro">Des groupes d'aujourd'hui qui jouent un rock à guitares, chaud et organique : leurs disques, leurs tournées, leur histoire.</p>
  <div class="bin">{releve}</div>
</section>
<section class="block wrap">
  <div class="block-head"><h2>Playlists</h2><a class="more" href="{url('rubriques/playlists')}">Toutes les playlists</a></div>
  <div class="pl-grid">{playlists}</div>
</section>
<section class="block wrap news">
  <div class="block-head"><h2>L'actu des classiques</h2><a class="more" href="{url('rubriques/actu')}">Toute l'actu</a></div>
  <ul class="news-list">{news}</ul>
</section>"""
    return layout(SITE_NAME, body, SITE_TAGLINE, SITE_URL + "/", img_src(today, 1200), "home")


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
    reading = max(1, round(len(re.sub(r":::.*?:::", "", a["body_md"], flags=re.S).split()) / 220))
    body = f"""<div class="read-progress" aria-hidden="true"><span></span></div>
<article class="post wrap">
  <div class="post-cover"><figure class="post-cover-in"><div class="post-cover-art">{sleeve(a, eager=True)}{sticker}</div>{credit(a)}</figure></div>
  <header class="post-title">
    <p class="post-kicker"><a href="{url('rubriques/' + a['category'])}">{esc(a['cat_name'])}</a>, <time datetime="{d:%Y-%m-%d}">{fr_date(d)}</time>, {reading} min de lecture</p>
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
      <aside class="ig-follow"><img src="{BASE}/assets/symbole.svg" alt="" width="64" height="64"><p><strong>Une histoire de rock chaque jour sur Instagram</strong>Un carrousel le matin, un Reel le soir.</p><a class="btn" href="https://www.instagram.com/riffsetlegendes/" target="_blank" rel="noopener">Suivre @riffsetlegendes</a></aside>
    </div>
</article>
<section class="block wrap">
  <div class="block-head"><h2>À lire aussi</h2></div>
  <div class="bin bin--3">{rel}</div>
</section>
<script>
document.querySelectorAll('[data-copy]').forEach(function(b){{b.addEventListener('click',function(){{var t=b.getAttribute('data-copy');var done=function(){{b.textContent='Lien copié';setTimeout(function(){{b.textContent='Copier le lien'}},2000)}};if(navigator.clipboard){{navigator.clipboard.writeText(t).then(done,function(){{prompt('Copiez ce lien :',t)}})}}else{{prompt('Copiez ce lien :',t)}}}})}});
</script>"""
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"], "description": a["excerpt"],
          "datePublished": f"{d:%Y-%m-%d}", "inLanguage": "fr", "mainEntityOfPage": SITE_URL + a["url"].replace(BASE, ""),
          "author": {"@type": "Organization", "name": SITE_NAME}, "publisher": {"@type": "Organization", "name": SITE_NAME,
          "logo": {"@type": "ImageObject", "url": SITE_URL + "/assets/icon-512.png"}}}
    if a.get("image"):
        ld["image"] = img_src(a, 1200)
    extra = (f'<meta property="og:type" content="article"><meta property="article:published_time" content="{d:%Y-%m-%d}">'
             f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    return layout(a["title"], body, a["excerpt"], SITE_URL + a["url"].replace(BASE, ""), img_src(a, 1200), "article", extra)


def page_category(key, arts):
    name, desc = CATEGORIES[key]
    items = [a for a in arts if a["category"] == key]
    grid = "".join(card(a) for a in items) or '<p class="empty">Les premiers articles arrivent bientôt.</p>'
    stack = "".join(f'<div class="sleeve">{art(a)}</div>' for a in items[:3])
    body = f"""<section class="cat-head cat-head--stack wrap"><div class="cat-text"><h1>{esc(name)}</h1><p>{esc(desc)}</p></div>
<div class="cat-stack" aria-hidden="true">{stack}</div></section>
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
    res.innerHTML=hits.map(function(a){{return '<article class="card"><a class="card-link" href="'+a.url+'"><div class="sleeve">'+(a.image?'<div class="riso"><img src="'+a.image+'" alt="" loading="lazy"></div>':'<div class="riso type-cover"><span class="tc-cat">'+esc(a.cat)+'</span><span class="tc-year">'+esc(a.year)+'</span></div>')+'</div><h3>'+esc(a.title)+'</h3></a><p class="card-meta">'+esc(a.cat)+'</p><p class="card-ex">'+esc(a.excerpt)+'</p></article>'}}).join('');
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
<p>Les faits sont vérifiés dans plusieurs sources, citées sous chaque article. Les photos sont des documents d'époque issus de Wikimedia Commons, sous licence libre. Les morceaux s'écoutent directement sur le site grâce au lecteur Spotify.</p>
</div></section>"""
    return layout("À propos", body, "Le projet Riffs & Légendes.", f"{SITE_URL}/a-propos/")


# ---------------------------------------------------------------- concerts

TYPE_LABEL = {"legende": "Légende", "releve": "La relève"}
DAYS_SHORT = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
MONTHS_SHORT = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def load_concerts():
    f = ROOT / "concerts.json"
    if not f.exists():
        return []
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=2))).date()
    out = []
    for c in json.loads(f.read_text(encoding="utf-8")):
        c["d"] = dt.date.fromisoformat(c["date"])
        if c["d"] >= today:
            import unicodedata
            raw = unicodedata.normalize("NFKD", f'{c["date"]}-{c["artist"]}-{c["city"]}').encode("ascii", "ignore").decode()
            c["id"] = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
            out.append(c)
    out.sort(key=lambda c: (c["d"], c["artist"]))
    return out


def ics(c):
    start = c["d"].strftime("%Y%m%d")
    if c.get("time"):
        hh, mm = c["time"].split(":")
        dtstart = f"DTSTART;TZID=Europe/Paris:{start}T{hh}{mm}00"
        dtend = f"DTEND;TZID=Europe/Paris:{start}T{(int(hh) + 3) % 24:02d}{mm}00"
    else:
        nxt = (c["d"] + dt.timedelta(days=1)).strftime("%Y%m%d")
        dtstart, dtend = f"DTSTART;VALUE=DATE:{start}", f"DTEND;VALUE=DATE:{nxt}"
    return "\r\n".join([
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Riffs & Legendes//Concerts//FR", "BEGIN:VEVENT",
        f"UID:{c['id']}@riffsetlegendes", f"DTSTAMP:{start}T000000Z", dtstart, dtend,
        f"SUMMARY:{c['artist']} en concert", f"LOCATION:{c['venue']}, {c['city']}",
        f"DESCRIPTION:Infos et billets : {c['source']}", "END:VEVENT", "END:VCALENDAR", ""])


def ticket(c, compact=False):
    d = c["d"]
    time = ""
    if c.get("time"):
        hh, mm = c["time"].split(":")
        time = f", {int(hh)} h" + ("" if mm == "00" else f" {mm}")
    tag = TYPE_LABEL.get(c.get("type"), "")
    art = f'<a class="tk-more" href="{url("articles/" + c["article"])}">Lire l\'article</a>' if c.get("article") else ""
    actions = "" if compact else (
        f'<div class="tk-actions"><a href="{esc(c["source"])}" target="_blank" rel="noopener">Infos et billets</a>'
        f'<a href="{BASE}/concerts/ics/{c["id"]}.ics" download>Ajouter à mon agenda</a>{art}</div>')
    return f"""<article class="ticket" data-city="{esc(c['city'])}" data-type="{esc(c.get('type',''))}" id="{c['id']}">
  <div class="tk-date"><span class="tk-dow">{DAYS_SHORT[d.weekday()]}</span><span class="tk-day">{d.day}</span><span class="tk-mon">{MONTHS_SHORT[d.month-1]} {d.year}</span></div>
  <div class="tk-body"><span class="tk-tag tk-tag--{esc(c.get('type',''))}">{tag}</span><h3>{f'<a href="{url("concerts")}#{c["id"]}">{esc(c["artist"])}</a>' if compact else esc(c['artist'])}</h3>
  <p class="tk-place">{esc(c['venue'])}, {esc(c['city'])}{time}</p>{actions}</div>
</article>"""


def month_grid(year, month, concerts):
    import calendar
    cal = calendar.Calendar(firstweekday=0)
    by_day = {}
    for c in concerts:
        if c["d"].year == year and c["d"].month == month:
            by_day.setdefault(c["d"].day, []).append(c)
    head = "".join(f"<span class='cg-h'>{x[:3]}</span>" for x in ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"])
    cells = ""
    for wk in cal.monthdayscalendar(year, month):
        for day in wk:
            if day == 0:
                cells += "<span class='cg-c cg-empty'></span>"
            elif day in by_day:
                names = "".join(f"<a href='#{c['id']}' data-city=\"{esc(c['city'])}\" data-type=\"{esc(c.get('type',''))}\">{esc(c['artist'])}</a>" for c in by_day[day])
                cells += f"<span class='cg-c cg-on'><b>{day}</b>{names}</span>"
            else:
                cells += f"<span class='cg-c'><b>{day}</b></span>"
    return f"<div class='cg' aria-hidden='true'>{head}{cells}</div>"


def page_concerts(concerts):
    cities = sorted({c["city"] for c in concerts})
    opts = "".join(f'<option value="{esc(x)}">{esc(x)}</option>' for x in cities)
    months = {}
    for c in concerts:
        months.setdefault((c["d"].year, c["d"].month), []).append(c)
    blocks = ""
    for (y, m), items in months.items():
        blocks += f"""<section class="cmonth" data-month="{y}-{m:02d}">
  <div class="cmonth-head"><h2>{MONTHS[m-1].capitalize()} <span>{y}</span></h2></div>
  <div class="cmonth-grid">{month_grid(y, m, concerts)}<div class="tickets">{''.join(ticket(c) for c in items)}</div></div>
</section>"""
    if not blocks:
        blocks = '<p class="empty">Aucun concert à venir pour l\'instant. Les prochaines dates arrivent bientôt.</p>'
    body = f"""<section class="cat-head wrap"><h1>Concerts</h1>
<p>Les dates à venir en France des légendes du rock et de la relève. Ajoutez un concert à votre agenda en un clic.</p>
<form class="cfilters" onsubmit="return false">
  <div class="chips" role="group" aria-label="Type de concert">
    <button type="button" class="chip is-on" data-filter-type="">Tous</button>
    <button type="button" class="chip" data-filter-type="legende">Légendes</button>
    <button type="button" class="chip" data-filter-type="releve">La relève</button>
  </div>
  <label class="csel"><span>Ville</span><select id="city"><option value="">Toute la France</option>{opts}</select></label>
</form></section>
<div class="wrap cal">{blocks}<p id="cempty" class="empty" hidden>Aucun concert ne correspond à ces filtres.</p>
<p class="cnote">Dates et salles vérifiées auprès des billetteries et des médias spécialisés, sous réserve de modification par les organisateurs. Vérifiez toujours sur le lien « Infos et billets ».</p></div>
<script>
(function(){{
  var type='', city='';
  function apply(){{
    var any=false;
    document.querySelectorAll('.ticket').forEach(function(t){{
      var ok=(!type||t.dataset.type===type)&&(!city||t.dataset.city===city); t.hidden=!ok; if(ok) any=true;
    }});
    document.querySelectorAll('.cg-on a').forEach(function(a){{
      a.classList.toggle('is-off', !((!type||a.dataset.type===type)&&(!city||a.dataset.city===city)));
    }});
    document.querySelectorAll('.cmonth').forEach(function(m){{
      m.hidden=!m.querySelector('.ticket:not([hidden])');
    }});
    document.getElementById('cempty').hidden=any;
  }}
  document.querySelectorAll('[data-filter-type]').forEach(function(b){{b.addEventListener('click',function(){{
    type=b.dataset.filterType; document.querySelectorAll('[data-filter-type]').forEach(function(x){{x.classList.toggle('is-on',x===b)}}); apply();}})}});
  document.getElementById('city').addEventListener('change',function(e){{city=e.target.value;apply();}});
}})();
</script>"""
    return layout("Concerts", body, "Les prochains concerts rock en France : légendes et relève, avec calendrier.", f"{SITE_URL}/concerts/")


def lib_key(name):
    import unicodedata
    a = re.sub(r"^(the|les|le|la|l')\s*", "", name.strip().casefold())
    return "".join(c for c in unicodedata.normalize("NFD", a) if unicodedata.category(c) != "Mn")


def page_library(arts):
    """Bibliothèque : tous les artistes du site et de la playlist encyclopédique, de A à Z."""
    names = {}
    enc = ROOT / "spotify" / "encyclopedie.txt"
    lines = enc.read_text(encoding="utf-8").splitlines() if enc.exists() else []
    for l in lines:
        c = [x.strip() for x in l.split("|")]
        if len(c) >= 3 and not l.startswith("#"):
            names.setdefault(lib_key(c[1]), c[1])
    extra = ROOT / "spotify" / "artistes.txt"
    if extra.exists():
        for l in extra.read_text(encoding="utf-8").splitlines():
            if l.strip() and not l.startswith("#"):
                names.setdefault(lib_key(l), l.strip())
    for a in arts:
        for block in re.findall(r":::(?:ecoute|tracklist)\n(.*?)\n:::", a["body_md"], re.S):
            for row in block.splitlines():
                c = [x.strip() for x in row.split("|")]
                if len(c) >= 2 and c[1]:
                    names.setdefault(lib_key(c[1]), c[1])
    ids = {}
    af = ROOT / "spotify" / "artists.json"
    if af.exists():
        ids = json.loads(af.read_text(encoding="utf-8"))
    groups = {}
    for k in sorted(names):
        letter = k[:1].upper() if k[:1].isalpha() else "#"
        groups.setdefault(letter, []).append(names[k])
    def link(n):
        href = f"https://open.spotify.com/artist/{ids[n]}" if ids.get(n) else "https://open.spotify.com/search/" + urllib.parse.quote(n) + "/artists"
        return f'<li><a href="{esc(href)}" target="_blank" rel="noopener">{esc(n)}</a></li>'
    index = "".join(f'<a href="#lettre-{l}">{l}</a>' for l in groups)
    body_groups = "".join(f'<section class="lib-letter" id="lettre-{l}"><h2>{l}</h2><ul>{"".join(link(n) for n in ns)}</ul></section>' for l, ns in groups.items())
    pl = ""
    st = ROOT / "spotify" / "state.json"
    if st.exists():
        pid = json.loads(st.read_text()).get("playlist")
        if pid:
            pl = f'<p><a class="btn" href="https://open.spotify.com/playlist/{pid}" target="_blank" rel="noopener">Écouter la playlist encyclopédique</a></p>'
    body = f"""<section class="wrap cat-head"><h1>Bibliothèque</h1>
<p class="block-intro">{len(names)} artistes, de A à Z. Chaque nom ouvre sa page Spotify.</p>{pl}
<input class="lib-filter" type="search" placeholder="Trouver un artiste" aria-label="Trouver un artiste" autocomplete="off">
<nav class="lib-index" aria-label="Lettres">{index}</nav></section>
<div class="wrap lib">{body_groups}</div>
<script>
var q=document.querySelector('.lib-filter');q.addEventListener('input',function(){{var v=q.value.trim().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
document.querySelectorAll('.lib-letter').forEach(function(s){{var any=false;s.querySelectorAll('li').forEach(function(li){{var t=li.textContent.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');var ok=!v||t.indexOf(v)>-1;li.hidden=!ok;any=any||ok}});s.hidden=!any}})}});
</script>"""
    return layout("Bibliothèque des artistes", body, f"{len(names)} artistes du rock de 1950 à aujourd'hui, de A à Z, avec leur page Spotify.", SITE_URL + "/bibliotheque/")


def page_credits(arts):
    rows_ = "".join(
        f'<li><a href="{a["url"]}">{esc(a["title"])}</a><span>{esc(a.get("image_caption", ""))} '
        f'<a href="{esc(commons_page(commons_file(a)))}" target="_blank" rel="noopener">Voir la photo, son auteur et sa licence sur Wikimedia Commons</a></span></li>'
        for a in arts if commons_file(a))
    body = f"""<section class="cat-head wrap"><h1>Crédits photos</h1><p>Les photos d'archives du site proviennent de Wikimedia Commons et sont publiées sous licence libre : domaine public, CC0 ou Creative Commons. Chaque lien mène à la page de la photo, avec son auteur et sa licence exacte.</p></section>
<section class="block wrap"><ul class="credits-list">{rows_}</ul></section>"""
    return layout("Crédits photos", body, "Crédits des photos utilisées sur le site.", f"{SITE_URL}/credits/")


def page_archives(arts):
    groups = {}
    for a in arts:
        groups.setdefault((a["date_obj"].year, a["date_obj"].month), []).append(a)
    out = ""
    for (y, m), items in groups.items():
        lis = "".join(f'<li><a href="{a["url"]}"><span class="ar-cat">{esc(a["cat_name"])}</span><span class="ar-t">{esc(a["title"])}</span></a></li>' for a in items)
        out += f'<section class="archive-month"><h2>{MONTHS[m-1].capitalize()} {y}</h2><ul class="archive-list">{lis}</ul></section>'
    body = f"""<section class="cat-head wrap"><h1>Archives</h1><p>Tous les articles publiés depuis le lancement du site, du plus récent au plus ancien.</p></section>
<section class="block wrap">{out}</section>"""
    return layout("Archives", body, "Tous les articles de Riffs & Légendes.", f"{SITE_URL}/archives/")


def page_legal():
    body = f"""<section class="cat-head wrap"><h1>Mentions légales</h1></section>
<section class="block wrap"><div class="prose prose--page">
<h2>Éditeur</h2>
<p>Riffs &amp; Légendes est un site personnel et non commercial consacré à l'histoire du rock.</p>
<h2>Hébergement</h2>
<p>GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, États-Unis.</p>
<h2>Contenus</h2>
<p>Les textes sont originaux. Les faits sont vérifiés dans plusieurs sources, citées sous les articles. Aucune parole de chanson n'est reproduite.</p>
<p>Les photos proviennent de Wikimedia Commons, sous licence libre : voir la page <a href="{url('credits')}">Crédits photos</a>. Les extraits musicaux sont diffusés par le lecteur officiel de Spotify.</p>
<h2>Données personnelles</h2>
<p>Le site ne dépose aucun cookie et ne collecte aucune donnée. Le lecteur Spotify ne se charge que lorsque vous lancez un morceau ; Spotify applique alors sa propre politique de confidentialité.</p>
</div></section>"""
    return layout("Mentions légales", body, "Mentions légales du site.", f"{SITE_URL}/mentions-legales/")


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
    generated = ["index.html", "404.html", "feed.xml", "search.json", "sitemap.xml", "robots.txt", "manifest.webmanifest", "bibliotheque",
                 "articles", "rubriques", "recherche", "concerts", "a-propos", "credits", "archives", "mentions-legales"]
    if OUT == ROOT:
        for g in generated:
            t = OUT / g
            if t.is_dir():
                shutil.rmtree(t)
            elif t.exists():
                t.unlink()
    else:
        if OUT.exists():
            shutil.rmtree(OUT)
        OUT.mkdir()
        shutil.copytree(ASSETS, OUT / "assets")
    concerts = load_concerts()
    write("index.html", page_home(arts, concerts))
    write("concerts/index.html", page_concerts(concerts))
    for c in concerts:
        write(f"concerts/ics/{c['id']}.ics", ics(c))
    for a in arts:
        write(f"articles/{a['slug']}/index.html", page_article(a, arts))
    for k in CATEGORIES:
        write(f"rubriques/{k}/index.html", page_category(k, arts))
    write("recherche/index.html", page_search())
    write("a-propos/index.html", page_about())
    write("credits/index.html", page_credits(arts))
    write("archives/index.html", page_archives(arts))
    write("mentions-legales/index.html", page_legal())
    write("feed.xml", feed(arts))
    index = [{"title": a["title"], "url": a["url"], "image": img_src(a, 600), "cat": a["cat_name"], "year": a.get("event_year", ""),
              "excerpt": a["excerpt"], "text": re.sub(r"[#*:|]", " ", a["body_md"])} for a in arts]
    write("search.json", json.dumps(index, ensure_ascii=False))
    urls = [SITE_URL + "/"] + [SITE_URL + a["url"].replace(BASE, "") for a in arts] + \
           [f"{SITE_URL}/rubriques/{k}/" for k in CATEGORIES] + [f"{SITE_URL}/concerts/", f"{SITE_URL}/bibliotheque/"]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>\n")
    write("bibliotheque/index.html", page_library(arts))
    write("manifest.webmanifest", json.dumps({"name": SITE_NAME, "short_name": "Riffs & Légendes", "lang": "fr",
        "start_url": BASE + "/", "display": "standalone", "background_color": "#f1f1eb", "theme_color": "#151b5e",
        "icons": [{"src": BASE + "/assets/icon-512.png", "sizes": "512x512", "type": "image/png"}]}, ensure_ascii=False))
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    write(".nojekyll", "")
    write("404.html", layout("Page introuvable", f'<section class="cat-head wrap"><h1>Face introuvable</h1><p>Cette page n\'existe pas ou a changé d\'adresse.</p><p><a class="btn" href="{url()}">Revenir à l\'accueil</a></p></section>'))
    print(f"{len(arts)} articles générés dans {OUT}")


if __name__ == "__main__":
    main()
