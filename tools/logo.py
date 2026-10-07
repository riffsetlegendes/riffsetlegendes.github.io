"""Génère le logo Riffs & Légendes en SVG vectorisé (textes convertis en tracés)."""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "tools" / "fonts"
OUT = ROOT / "brand"
NAVY, BLUE, YELLOW, PAPER, VINYL = "#151b5e", "#2536d0", "#f5bf1d", "#f1f1eb", "#0b0c18"

def inst(name, **axes):
    f = TTFont(F / name)
    return instantiateVariableFont(f, axes) if "fvar" in f else f

HEAD = inst("BigShouldersDisplay.ttf", wght=900)
SERIF_I = inst("Newsreader-Italic.ttf", wght=500, opsz=72) if "fvar" in TTFont(F / "Newsreader-Italic.ttf") else TTFont(F / "Newsreader-Italic.ttf")
MONO = TTFont(F / "DMMono-Medium.ttf")

def text(font, s, x, y, size, track=0.0):
    """Renvoie (chemin SVG, largeur) pour s, ligne de base en y."""
    gs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
    upm = font["head"].unitsPerEm
    k = size / upm
    pen = SVGPathPen(gs)
    cx = 0.0
    for ch in s:
        g = cmap.get(ord(ch))
        if g is None:
            continue
        tp = TransformPen(pen, (k, 0, 0, -k, x + cx, y))
        gs[g].draw(tp)
        cx += hmtx[g][0] * k + track * size
    return pen.getCommands(), cx - track * size

def width(font, s, size, track=0.0):
    return text(font, s, 0, 0, size, track)[1]

def symbol(cx, cy, r, disc=VINYL, label=YELLOW, amp=NAVY, groove=PAPER):
    """Le symbole : un 45-tours vu de face, l'esperluette imprimée sur l'étiquette."""
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{disc}"/>']
    for f in (0.92, 0.84, 0.76, 0.68):
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r*f:.2f}" fill="none" stroke="{groove}" stroke-opacity=".22" stroke-width="{r*0.012:.2f}"/>')
    lr = r * 0.52
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{lr:.2f}" fill="{label}"/>')
    size = lr * 1.55
    w = width(SERIF_I, "&", size)
    d, _ = text(SERIF_I, "&", cx - w / 2 - size * 0.02, cy + size * 0.33, size)
    out.append(f'<path d="{d}" fill="{amp}"/>')
    return "\n".join(out)

def svg(w, h, body, bg=None):
    b = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{b}{body}</svg>\n'

def wordmark(x, y, cap, ink, accent):
    """RIFFS & / LÉGENDES : deux lignes justifiées à la même largeur, & en italique."""
    s2 = cap
    w2 = width(HEAD, "LÉGENDES", s2, 0.01)
    # ligne 1 dimensionnée pour que « RIFFS & » ait exactement la largeur de « LÉGENDES »
    unit_r = width(HEAD, "RIFFS", 1, 0.02)
    unit_a = width(SERIF_I, "&", 1.12)
    gap = 0.12
    s1 = w2 / (unit_r + gap + unit_a)
    b1 = s1 * 0.74
    d1, wr = text(HEAD, "RIFFS", x, y + b1, s1, 0.02)
    sa = s1 * 1.12
    wa = width(SERIF_I, "&", sa)
    da, _ = text(SERIF_I, "&", x + w2 - wa, y + b1 + s1 * 0.02, sa)
    b2 = b1 + s2 * 1.1
    d2, _ = text(HEAD, "LÉGENDES", x, y + b2, s2, 0.01)
    body = f'<path d="{d1}" fill="{ink}"/><path d="{da}" fill="{accent}"/><path d="{d2}" fill="{ink}"/>'
    return body, w2, b2

def tagline(x, y, size, ink, s="ROCK · 1950–1999 · ET LA RELÈVE"):
    d, w = text(MONO, s, x, y, size, 0.08)
    return f'<path d="{d}" fill="{ink}"/>', w

def lockup(ink, accent, disc, label, ampc, groove, bg=None, name="horizontal"):
    r = 120
    wm, ww, wh = wordmark(0, 0, 150, ink, accent)
    pad = 40
    W = pad + 2 * r + 56 + ww + pad
    H = pad + 2 * r + pad
    oy = pad + r - wh / 2
    body = symbol(pad + r, pad + r, r, disc, label, ampc, groove)
    body += f'<g transform="translate({pad + 2*r + 56},{oy:.1f})">{wm}</g>'
    return svg(round(W), round(H), body, bg)

def stacked(ink, accent, disc, label, ampc, groove, bg=None):
    r = 150
    wm, ww, wh = wordmark(0, 0, 150, ink, accent)
    tg, tw = tagline(0, 0, 26, ink)
    W = max(ww, tw, 2 * r) + 120
    cx = W / 2
    body = symbol(cx, 60 + r, r, disc, label, ampc, groove)
    y = 60 + 2 * r + 50
    body += f'<g transform="translate({cx - ww/2:.1f},{y})">{wm}</g>'
    body += f'<g transform="translate({cx - tw/2:.1f},{y + wh + 60:.1f})" opacity=".8">{tg}</g>'
    return svg(round(W), round(y + wh + 110), body, bg)

def main():
    OUT.mkdir(exist_ok=True)
    pos = dict(ink=NAVY, accent=BLUE, disc=VINYL, label=YELLOW, ampc=NAVY, groove=PAPER)
    neg = dict(ink=PAPER, accent=YELLOW, disc=VINYL, label=YELLOW, ampc=NAVY, groove=PAPER)
    mono = dict(ink=NAVY, accent=NAVY, disc=NAVY, label=PAPER, ampc=NAVY, groove=PAPER)
    (OUT / "logo-horizontal.svg").write_text(lockup(**pos))
    (OUT / "logo-horizontal-negatif.svg").write_text(lockup(**neg, bg=NAVY))
    (OUT / "logo-horizontal-mono.svg").write_text(lockup(**mono))
    (OUT / "logo-vertical.svg").write_text(stacked(**pos))
    (OUT / "logo-vertical-negatif.svg").write_text(stacked(**neg, bg=NAVY))
    (OUT / "symbole.svg").write_text(svg(320, 320, symbol(160, 160, 150)))
    (OUT / "symbole-jaune.svg").write_text(svg(320, 320, symbol(160, 160, 150, disc=NAVY), bg=YELLOW))
    # icône du site : symbole seul
    (ROOT / "assets" / "favicon.svg").write_text(svg(64, 64, symbol(32, 32, 31)).replace(' width="64" height="64"', ""))
    print("ok")

if __name__ == "__main__":
    main()

def extras():
    (ROOT / "assets" / "symbole.svg").write_text(svg(320, 320, symbol(160, 160, 150)))
    (OUT / "avatar-instagram.svg").write_text(svg(1080, 1080, symbol(540, 540, 430), bg=NAVY))

extras()
