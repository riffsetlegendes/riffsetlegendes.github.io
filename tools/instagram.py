#!/usr/bin/env python3
"""Génère les carrousels Instagram de Riffs & Légendes (images 1080 x 1350).

Usage : python3 tools/instagram.py instagram/2026-10-07-jour.json [autres.json ...]
Les images sont écrites dans out/instagram/<nom du fichier>/ (dossier ignoré par git).

Format du fichier JSON :
{
  "type": "jour" | "focus",
  "label": "Ce jour-là" | "Légende" | "Anecdote",
  "big": "7 octobre",            # jour : la date en très grand ; focus : l'année ou la période
  "title": "La route s'arrête pour Johnny Kidd",
  "sticker": "60 ans",           # facultatif
  "disc": "1966",                # jour : texte de l'étiquette du disque
  "slides": [{"head": "Londres, 1960", "big": "Phrase forte", "text": "Développement"}],
  "tracks": [["Titre", "Artiste", "1960"]],
  "caption": "Légende du post",
  "hashtags": ["rock", "vinyle"]
}
"""
import asyncio
import base64
import html
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "tools" / "fonts"
OUT = ROOT / "out" / "instagram"
SITE = "riffs & légendes"

def font_uri(name):
    return "data:font/ttf;base64," + base64.b64encode((FONTS / name).read_bytes()).decode()


CSS = f"""
@font-face {{ font-family: "Archivo"; src: url("{font_uri('Archivo.ttf')}") format("truetype"); font-weight: 100 900; font-stretch: 62% 125%; }}
@font-face {{ font-family: "Newsreader"; src: url("{font_uri('Newsreader.ttf')}") format("truetype"); font-weight: 200 800; }}
@font-face {{ font-family: "Newsreader"; src: url("{font_uri('Newsreader-Italic.ttf')}") format("truetype"); font-weight: 200 800; font-style: italic; }}
:root {{ --paper:#f1f1eb; --ink:#151b5e; --soft:#4b5189; --riso:#2536d0; --yellow:#f5bf1d; --vinyl:#0b0c18; }}
* {{ box-sizing: border-box; margin: 0; }}
body {{ background: #888; }}
.slide {{ width: 1080px; height: 1350px; position: relative; overflow: hidden; padding: 88px; display: flex; flex-direction: column;
  font-family: "Newsreader", serif; color: var(--ink); background: var(--paper); }}
.slide::after {{ content: ""; position: absolute; inset: 0; pointer-events: none; opacity: .22; mix-blend-mode: multiply;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 .6 0'/%3E%3C/filter%3E%3Crect width='220' height='220' filter='url(%23n)'/%3E%3C/svg%3E"); }}
.d {{ font-family: "Archivo", sans-serif; }}
.foot {{ position: absolute; left: 88px; right: 88px; bottom: 70px; display: flex; justify-content: space-between; align-items: baseline;
  font-family: "Archivo"; font-weight: 800; font-size: 30px; font-stretch: 125%; letter-spacing: -.01em; z-index: 3; }}
.pg {{ position: absolute; top: 40px; right: 88px; font-family: "Archivo"; font-stretch: 100%; font-weight: 700; font-size: 26px; opacity: .7; z-index: 4; }}
.amp {{ font-family: "Newsreader"; font-style: italic; font-weight: 400; }}

/* couverture « ce jour-là » */
.cover-jour {{ background: var(--riso); color: var(--paper); }}
.cover-jour .label {{ font-family: "Archivo"; font-weight: 700; font-size: 38px; color: var(--yellow); position: relative; z-index: 2; }}
.cover-jour .date {{ font-family: "Archivo"; font-weight: 900; font-stretch: 125%; font-size: 190px; line-height: .82; letter-spacing: -.045em;
  color: var(--yellow); margin-top: 28px; position: relative; z-index: 2; }}
.cover-jour .title {{ font-family: "Archivo"; font-weight: 850; font-stretch: 112%; font-size: 82px; line-height: .95; letter-spacing: -.025em;
  margin-top: auto; margin-bottom: 120px; position: relative; z-index: 2; max-width: 900px; text-wrap: balance; }}
.disc {{ position: absolute; width: 760px; height: 760px; right: -260px; top: 300px; border-radius: 50%; z-index: 1;
  background: conic-gradient(from 20deg, transparent 0 9%, rgba(255,255,255,.14) 13%, transparent 19% 58%, rgba(255,255,255,.1) 63%, transparent 69%),
    repeating-radial-gradient(circle at 50% 50%, var(--vinyl) 0 3px, #1d2034 4px 5px), var(--vinyl);
  box-shadow: 0 30px 60px -30px rgba(0,0,0,.8); }}
.disc .lab {{ position: absolute; inset: 33%; border-radius: 50%; background: var(--yellow); color: var(--ink); display: grid; place-content: center;
  text-align: center; font-family: "Archivo"; font-weight: 900; font-stretch: 125%; font-size: 64px; letter-spacing: -.03em; }}
.disc .lab::after {{ content: ""; position: absolute; left: 50%; top: 50%; width: 22px; height: 22px; border-radius: 50%; background: var(--riso); translate: -50% -50%; }}
.disc .lab {{ place-content: start center; padding-top: 20%; font-size: 58px; }}
.sticker {{ position: absolute; z-index: 3; width: 210px; height: 210px; border-radius: 50%; background: var(--yellow); color: var(--ink); rotate: -10deg;
  display: grid; place-content: center; text-align: center; line-height: .9; font-family: "Archivo"; font-weight: 700; font-size: 34px;
  box-shadow: 0 12px 24px -12px rgba(0,0,0,.5); }}
.sticker b {{ display: block; font-weight: 900; font-stretch: 125%; font-size: 92px; letter-spacing: -.04em; }}
.cover-jour .sticker {{ right: 90px; top: 90px; }}

/* couverture focus */
.cover-focus {{ padding: 0; }}
.cover-focus .top {{ background: var(--ink); color: var(--yellow); height: 560px; padding: 88px; display: flex; flex-direction: column; justify-content: space-between; position: relative; z-index: 2; }}
.cover-focus .label {{ font-family: "Archivo"; font-weight: 700; font-size: 38px; color: var(--paper); }}
.cover-focus .years {{ font-family: "Archivo"; font-weight: 900; font-stretch: 125%; font-size: 200px; line-height: .8; letter-spacing: -.05em; }}
.cover-focus .years.long {{ font-size: 150px; }}
.cover-focus .name {{ padding: 70px 88px 0; font-family: "Archivo"; font-weight: 900; font-stretch: 118%; font-size: 112px; line-height: .9;
  letter-spacing: -.035em; color: var(--riso); position: relative; z-index: 2; text-wrap: balance; }}
.cover-focus .sticker {{ right: 70px; top: 470px; }}

/* pages d'histoire */
.story .head {{ font-family: "Archivo"; font-weight: 800; font-stretch: 112%; font-size: 40px; color: var(--riso); border-top: 8px solid var(--ink); padding-top: 26px; position: relative; z-index: 2; }}
.story .big {{ font-family: "Archivo"; font-weight: 850; font-stretch: 112%; font-size: 104px; line-height: .96; letter-spacing: -.03em; margin-top: 70px; position: relative; z-index: 2; text-wrap: balance; }}
.story .text {{ font-size: 50px; line-height: 1.36; color: var(--soft); margin-top: 56px; position: relative; z-index: 2; max-width: 880px; }}
.story.alt {{ background: var(--ink); color: var(--paper); }}
.story.alt .head {{ color: var(--yellow); border-color: var(--yellow); }}
.story.alt .text {{ color: #c9cce6; }}

.story .mark {{ position: absolute; width: 560px; height: 560px; right: -210px; bottom: -210px; border-radius: 50%; z-index: 1;
  background: radial-gradient(circle, var(--paper) 0 3%, var(--riso) 3.5% 34%, transparent 34.5%), repeating-radial-gradient(circle, var(--vinyl) 0 3px, #1d2034 4px 5px); }}
.story.alt .mark {{ background: radial-gradient(circle, var(--ink) 0 3%, var(--yellow) 3.5% 34%, transparent 34.5%), repeating-radial-gradient(circle, var(--vinyl) 0 3px, #262a45 4px 5px); }}

/* dernière page */
.end {{ background: var(--yellow); color: var(--ink); }}
.end .head {{ font-family: "Archivo"; font-weight: 800; font-size: 40px; border-top: 8px solid var(--ink); padding-top: 26px; }}
.end ol {{ list-style: none; padding: 0; margin-top: 40px; }}
.end li {{ display: grid; grid-template-columns: 70px 1fr; align-items: baseline; padding: 22px 0; border-bottom: 2px solid rgba(21,27,94,.25); }}
.end li .n {{ font-family: "Archivo"; font-weight: 800; font-size: 40px; }}
.end li .t {{ font-family: "Archivo"; font-weight: 800; font-size: 48px; line-height: 1.05; }}
.end li .a {{ display: block; font-family: "Newsreader"; font-style: italic; font-size: 36px; margin-top: 6px; opacity: .8; }}
.end .cta {{ margin-top: auto; margin-bottom: 110px; font-family: "Archivo"; font-weight: 900; font-stretch: 125%; font-size: 110px; line-height: .86; letter-spacing: -.04em; }}
.end .cta small {{ display: block; font-size: 44px; font-weight: 700; font-stretch: 100%; letter-spacing: 0; margin-top: 26px; font-family: "Newsreader"; font-style: italic; }}

/* avatar */
.avatar {{ width: 1080px; height: 1080px; background: var(--ink); display: grid; place-items: center; position: relative; overflow: hidden; }}
.avatar .rec {{ width: 860px; height: 860px; border-radius: 50%; display: grid; place-items: center;
  background: repeating-radial-gradient(circle at 50% 50%, var(--vinyl) 0 3px, #262a45 4px 5px); }}
.avatar .rec div {{ width: 470px; height: 470px; border-radius: 50%; background: var(--yellow); display: grid; place-content: center; text-align: center;
  font-family: "Archivo"; font-weight: 900; font-stretch: 125%; color: var(--ink); font-size: 170px; letter-spacing: -.05em; line-height: .9; }}
.avatar .rec div .amp {{ font-size: 150px; color: var(--riso); }}
/* typographie v2, alignée sur le site */
@font-face {{ font-family: "Big Shoulders Display"; src: url("{font_uri('BigShouldersDisplay.ttf')}") format("truetype"); font-weight: 100 900; }}
@font-face {{ font-family: "DM Mono"; src: url("{font_uri('DMMono-Medium.ttf')}") format("truetype"); font-weight: 500; }}
.cover-jour .date, .cover-jour .title, .cover-focus .years, .cover-focus .name, .story .big, .end .cta, .end li .t, .avatar .rec div {{
  font-family: "Big Shoulders Display"; font-stretch: normal; font-weight: 900; text-transform: uppercase; letter-spacing: 0; }}
.cover-jour .date {{ font-size: 230px; }} .cover-jour .title {{ font-size: 104px; line-height: .9; }}
.cover-focus .years {{ font-size: 250px; }} .cover-focus .name {{ font-size: 118px; line-height: .9; padding-bottom: 150px; }}
.story .big {{ font-size: 124px; line-height: .92; }} .end .cta {{ font-size: 140px; }} .end li .t {{ font-weight: 800; font-size: 56px; line-height: 1; }}
.end .cta small, .amp, .end li .a {{ text-transform: none; }}
.end li .a {{ font-family: "Newsreader"; font-weight: 400; letter-spacing: 0; }}
.pg, .end li .n {{ font-family: "DM Mono"; font-weight: 500; }}
.avatar .rec div {{ font-size: 200px; line-height: .85; }}
.cover-photo {{ background: var(--paper); display: flex; flex-direction: column; }}
.cover-photo .ph {{ position: relative; height: 780px; flex: none; overflow: hidden; background: #fff; isolation: isolate; }}
.cover-photo .ph img {{ width: 100%; height: 100%; object-fit: cover; object-position: var(--pos, 50% 25%); filter: grayscale(1) contrast(1.25) brightness(1.08); }}
.cover-photo .ph::after {{ content: ""; position: absolute; inset: 0; background: var(--riso); mix-blend-mode: lighten; }}
.cover-photo .ph .yr {{ position: absolute; z-index: 3; left: 72px; bottom: 40px; font-family: "Big Shoulders Display"; font-weight: 900; font-size: 190px; line-height: .8; color: var(--yellow); }}
.cover-photo .ph .lb {{ position: absolute; z-index: 3; left: 72px; top: 64px; font-family: "Archivo"; font-weight: 700; font-size: 34px; color: var(--yellow); }}
.cover-photo .tt {{ padding: 44px 0 0; font-family: "Big Shoulders Display"; font-weight: 900; text-transform: uppercase; font-size: 92px; line-height: .9; color: var(--ink); text-wrap: balance; max-height: 340px; overflow: hidden; }}
.cover-photo .sticker {{ top: 40px; right: 60px; left: auto; }}
.cover-photo.dark {{ background: var(--ink); color: var(--paper); }} .cover-photo.dark .tt {{ color: var(--paper); }}
"""



def fetch_photo(name):
    """Photo Wikimedia Commons en base64 (None si indisponible : on garde la couverture typographique)."""
    import base64, urllib.parse, urllib.request
    url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(name) + "?width=1200"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RiffsEtLegendes/1.0 (riffsetlegendes.github.io)"})
        with urllib.request.urlopen(req, timeout=40) as r:
            data, ctype = r.read(), r.headers.get_content_type()
        return f"data:{ctype};base64," + base64.b64encode(data).decode()
    except Exception as ex:
        print(f"Photo indisponible ({ex}), couverture typographique.", file=sys.stderr)
        return None


def e(s):
    return html.escape(s or "")


def footer(i, n, dark=False):
    return f'<div class="foot"><span>Riffs <span class="amp">&amp;</span> Légendes</span></div><span class="pg">{i}/{n}</span>'


def build(spec):
    slides = spec.get("slides", [])
    total = len(slides) + 2
    out = []
    sticker = ""
    if spec.get("sticker"):
        num, _, rest = spec["sticker"].partition(" ")
        sticker = f'<div class="sticker"><b>{e(num)}</b>{e(rest)}</div>'
    photo = fetch_photo(spec["photo"]) if spec.get("photo") else None
    if photo:
        dark = " dark" if spec["type"] == "focus" else ""
        pos = e(spec.get("photo_pos", "50% 25%"))
        out.append(f"""<section class="slide cover-photo{dark}"><div class="ph" style="--pos:{pos}"><img src="{photo}" alt="">
<p class="lb">{e(spec['label'])}</p><p class="yr">{e(spec.get('disc') or spec['big'])}</p></div>{sticker}
<h1 class="tt">{e(spec['title'])}</h1>{footer(1, total)}</section>""")
    elif spec["type"] == "jour":
        out.append(f"""<section class="slide cover-jour"><p class="label">{e(spec['label'])}</p>
<p class="date">{e(spec['big'])}</p><div class="disc"><div class="lab"><span>{e(spec.get('disc',''))}</span></div></div>{sticker}
<h1 class="title">{e(spec['title'])}</h1>{footer(1, total)}</section>""")
    else:
        long = " long" if len(spec["big"]) > 5 else ""
        out.append(f"""<section class="slide cover-focus"><div class="top"><p class="label">{e(spec['label'])}</p><p class="years{long}">{e(spec['big'])}</p></div>
{sticker}<h1 class="name">{e(spec['title'])}</h1>{footer(1, total)}</section>""")
    for i, s in enumerate(slides, 2):
        alt = " alt" if i % 2 == 1 else ""
        out.append(f"""<section class="slide story{alt}"><p class="head">{e(s.get('head',''))}</p><p class="big">{e(s['big'])}</p>
<p class="text">{e(s.get('text',''))}</p><div class="mark"></div>{footer(i, total)}</section>""")
    tracks = "".join(f'<li><span class="n">{n}</span><span class="t">{e(t)}<span class="a">{e(a)}, {e(y)}</span></span></li>'
                     for n, (t, a, y) in enumerate(spec.get("tracks", [])[:4], 1))
    out.append(f"""<section class="slide end"><p class="head">À écouter</p><ol>{tracks}</ol>
<p class="cta">Toute l'histoire sur le site<small>Lien en bio, avec les morceaux à écouter.</small></p>{footer(total, total)}</section>""")
    return out


async def render(pages, folder, avatar=False):
    folder.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        doc = f"<!doctype html><html lang='fr'><meta charset='utf-8'><style>{CSS}</style><body>{''.join(pages)}</body></html>"
        await pg.set_content(doc)
        await pg.evaluate("document.fonts.ready")
        await pg.wait_for_timeout(400)
        sel = ".avatar" if avatar else ".slide"
        els = await pg.query_selector_all(sel)
        files = []
        for i, el in enumerate(els, 1):
            f = folder / (f"avatar.png" if avatar else f"{i:02d}.png")
            await el.screenshot(path=str(f))
            files.append(f)
        await b.close()
    return files


def main():
    args = sys.argv[1:]
    if args == ["--avatar"]:
        files = asyncio.run(render(['<div class="avatar"><div class="rec"><div>R<span class="amp">&amp;</span>L</div></div></div>'], OUT / "profil", avatar=True))
        print("\n".join(str(f) for f in files))
        return
    for path in args:
        spec = json.loads(Path(path).read_text(encoding="utf-8"))
        folder = OUT / Path(path).stem
        files = asyncio.run(render(build(spec), folder))
        caption = spec.get("caption", "").strip() + "\n\n" + " ".join("#" + h for h in spec.get("hashtags", []))
        (folder / "legende.txt").write_text(caption.strip() + "\n", encoding="utf-8")
        print("\n".join(str(f) for f in files))
        print(folder / "legende.txt")


if __name__ == "__main__":
    main()
