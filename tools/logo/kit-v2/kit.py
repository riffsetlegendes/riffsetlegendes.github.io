"""Kit du logo Riffs & Légendes — symbole « L'étiquette » (piste A, octobre 2026).
Symbole : vinyle plein, une rainure, étiquette jaune, esperluette Young Serif.
Typographie : nom en relief Fraunces + esperluette Young Serif (inchangé).
Usage : python3 kit.py <dossier_sortie>"""
import os, sys, re
from glyphs import text_path, font
from fx import relief, INK, BAND, RISO, YEL, PAPER, VINYL, NIGHT
from fontTools.pens.boundsPen import BoundsPen

OUT = sys.argv[1] if len(sys.argv) > 1 else 'kit'
os.makedirs(OUT, exist_ok=True)
F = 'fraunces-black-soft.ttf'; AMP = 'youngserif.ttf'; SH = '#fde7a0'
C = 128

def r2(d):
    d = re.sub(r'-?\d+\.\d+', lambda m: f"{float(m.group()):.2f}".rstrip('0').rstrip('.'), d)
    return re.sub(r'\s+', ' ', re.sub(r'([MLHVCSQTAZ])', r' \1 ', d)).strip()

def circ(cx, cy, r, ccw=False):
    s = 0 if ccw else 1
    return f"M{cx-r:g} {cy:g}A{r:g} {r:g} 0 1 {s} {cx+r:g} {cy:g}A{r:g} {r:g} 0 1 {s} {cx-r:g} {cy:g}Z"

def amp(cx, cy, h):
    f, gs, cmap, upm = font(AMP)
    bp = BoundsPen(gs); gs[cmap[ord('&')]].draw(bp); x0, y0, x1, y1 = bp.bounds
    size = h * upm / (y1 - y0); s = size / upm
    d, _ = text_path(AMP, '&', size, cx - (x0 + x1) / 2 * s, cy + (y0 + y1) / 2 * s)
    return d

def doc(body, w, h, title, vb=None):
    vb = vb or f"0 0 {w} {h}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{w}" height="{h}" role="img" '
            f'aria-labelledby="t"><title id="t">{title}</title>{body}</svg>')

def save(name, s):
    open(os.path.join(OUT, name), 'w').write(s)

# ---------------------------------------------------------------- symbole
# Construction (grille 256) : disque r=120 ; rainure = anneau vide entre r=91 et r=96 ;
# étiquette r=60 ; esperluette haute de 76, centrée optiquement 1 unité au-dessus du centre.
# Petite taille (≤ 32 px) : pas de rainure, étiquette r=74, esperluette haute de 96.
def symbol_parts(small=False):
    if small:
        return dict(disc=circ(C, C, 120), label=circ(C, C, 76), amp=amp(C + 1, C - 1, 100))
    return dict(disc=circ(C, C, 120) + circ(C, C, 96, True) + circ(C, C, 91),
                label=circ(C, C, 60), amp=amp(C + 1, C - 1, 76))

def symbol_color(small=False, dark=False):
    p = symbol_parts(small)
    halo = f'<path fill="{PAPER}" d="{circ(C, C, 125)}"/>' if dark else ''
    groove_fill = f'<path fill="{PAPER}" d="{circ(C, C, 96)}"/>' if dark and not small else ''
    return (halo + groove_fill + f'<path fill="{VINYL}" fill-rule="evenodd" d="{r2(p["disc"])}"/>'
            f'<path fill="{YEL}" d="{r2(p["label"])}"/><path fill="{INK}" d="{r2(p["amp"])}"/>')

def symbol_mono(col, small=False):
    p = symbol_parts(small)
    return f'<path fill="{col}" fill-rule="evenodd" d="{r2(p["disc"] + p["amp"])}"/>'

T = 'Riffs &amp; Légendes'
save('symbole-couleur.svg', doc(symbol_color(), 256, 256, T))
save('symbole-couleur-fond-sombre.svg', doc(symbol_color(dark=True), 256, 256, T))
save('symbole-petit-couleur.svg', doc(symbol_color(small=True), 256, 256, T))
save('symbole-noir.svg', doc(symbol_mono('#000000'), 256, 256, T))
save('symbole-blanc.svg', doc(symbol_mono('#ffffff'), 256, 256, T))
save('symbole-outremer.svg', doc(symbol_mono(INK), 256, 256, T))
save('symbole-petit-noir.svg', doc(symbol_mono('#000000', small=True), 256, 256, T))

# ---------------------------------------------------------------- nom (typographie inchangée)
def word_paths():
    s = 170; base = 200; x = 40
    d1, w1 = text_path(F, 'Riffs', s, x, base, tracking=-3)
    _, wa = text_path(AMP, '&', 175, 0, 0)
    ax = x + w1 + 34; a, _ = text_path(AMP, '&', 175, ax, base + 4)
    x2 = ax + wa + 30; d2, w2 = text_path(F, 'Légendes', s, x2, base, tracking=-4)
    return (d1, a, d2), x2 + w2

def word_relief(dark=False, face=YEL, shine=SH):
    side = RISO if dark else BAND; outl = VINYL if dark else INK; kl = PAPER if dark else None
    ds, right = word_paths()
    return ''.join(relief(d, face=face, side=side, outline=outl, depth=11, ow=4, shine=shine, keyline=kl) for d in ds), right

def word_flat(col):
    ds, right = word_paths()
    return f'<path fill="{col}" d="{r2("".join(ds))}"/>', right

# boîte du nom : x 40 → right, ligne de base 200, hauteur de capitale ≈ 119, jambage de g ≈ 246
CAP = 119
WB = dict(x0=26, y0=40, y1=290)

def lockup_h(sym, word):
    body_w, right = word
    # symbole r=120 centré (128,128) ; centre optique du nom aligné sur le centre du symbole
    tx = 300 - 40; ty = 128 - (200 - CAP / 2)
    w = int(tx + right + 24)
    return doc(f'<g id="symbole">{sym}</g><g id="nom" transform="translate({tx:.0f} {ty:.1f})">{body_w}</g>',
               w, 300, T, vb=f"0 -22 {w} 300")

def lockup_v(sym, word):
    body_w, right = word
    ww = right - 26
    w = int(ww + 60); cx = w / 2
    sc = 1.35
    sym_g = f'<g id="symbole" transform="translate({cx - 128 * sc:.1f} 0) scale({sc})">{sym}</g>'
    ty = 256 * sc + 40 - 40
    word_g = f'<g id="nom" transform="translate({cx - (26 + right) / 2:.1f} {ty:.1f})">{body_w}</g>'
    h = int(ty + 290)
    return doc(sym_g + word_g, w, h, T)

save('logo-horizontal-couleur.svg', lockup_h(symbol_color(), word_relief()))
save('logo-horizontal-fond-sombre.svg', lockup_h(symbol_color(dark=True), word_relief(dark=True)))
save('logo-horizontal-noir.svg', lockup_h(symbol_mono('#000000'), word_flat('#000000')))
save('logo-horizontal-blanc.svg', lockup_h(symbol_mono('#ffffff'), word_flat('#ffffff')))
save('logo-empile-couleur.svg', lockup_v(symbol_color(), word_relief()))
save('logo-empile-fond-sombre.svg', lockup_v(symbol_color(dark=True), word_relief(dark=True)))
save('logo-empile-noir.svg', lockup_v(symbol_mono('#000000'), word_flat('#000000')))

def word_only(body, right, name):
    save(name, doc(body, int(right + 30 - 26), 250, T, vb=f"26 40 {int(right + 30 - 26)} 250"))
b, r = word_relief(); word_only(b, r, 'nom-couleur.svg')
b, r = word_relief(dark=True); word_only(b, r, 'nom-fond-sombre.svg')
b, r = word_relief(face=PAPER, shine=None); word_only(b, r, 'nom-sur-jaune.svg')
b, r = word_flat('#000000'); word_only(b, r, 'nom-noir.svg')
b, r = word_flat('#ffffff'); word_only(b, r, 'nom-blanc.svg')

# ---------------------------------------------------------------- avatar Instagram (1080, recadrage rond)
av = f'<rect width="1080" height="1080" fill="{BAND}"/><g transform="translate(540 540) scale(3.6) translate(-128 -128)">{symbol_color(dark=True)}</g>'
save('avatar-instagram.svg', doc(av, 1080, 1080, T))
print(sorted(os.listdir(OUT)))
