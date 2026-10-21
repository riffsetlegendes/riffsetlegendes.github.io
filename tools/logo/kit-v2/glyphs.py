"""Outline text into SVG path data, with optional arc warp."""
import math
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.basePen import decomposeQuadraticSegment

_cache = {}
FONTS = 'fonts/'

def font(name):
    if name not in _cache:
        f = TTFont(FONTS + name)
        _cache[name] = (f, f.getGlyphSet(), f.getBestCmap(), f['head'].unitsPerEm)
    return _cache[name]

def _fmt(v):
    return f"{v:.2f}".rstrip('0').rstrip('.')

def _emit(rec, tf):
    out = []
    for op, pts in rec.value:
        if op == 'moveTo':
            x, y = tf(*pts[0]); out.append(f"M{_fmt(x)} {_fmt(y)}")
        elif op == 'lineTo':
            x, y = tf(*pts[0]); out.append(f"L{_fmt(x)} {_fmt(y)}")
        elif op == 'curveTo':
            (a, b), (c, d), (e, f) = [tf(*p) for p in pts]
            out.append(f"C{_fmt(a)} {_fmt(b)} {_fmt(c)} {_fmt(d)} {_fmt(e)} {_fmt(f)}")
        elif op == 'qCurveTo':
            # expand implied on-curve points
            if pts[-1] is None:
                raise ValueError('closed quad contour without on-curve')
            for (c, e) in decomposeQuadraticSegment(pts) if len(pts) > 2 else [pts]:
                (a, b), (x, y) = tf(*c), tf(*e)
                out.append(f"Q{_fmt(a)} {_fmt(b)} {_fmt(x)} {_fmt(y)}")
        elif op == 'closePath' or op == 'endPath':
            out.append('Z')
    return ''.join(out)

def layout(fontname, text, size, tracking=0, kern=None):
    """Return list of (glyphname, x_offset_units) and total advance in px."""
    f, gs, cmap, upm = font(fontname)
    kern = kern or {}
    s = size / upm
    x = 0.0
    items = []
    for i, ch in enumerate(text):
        g = cmap.get(ord(ch))
        if g is None:
            raise KeyError(ch)
        items.append((g, x))
        adv = gs[g].width * s + tracking
        if i + 1 < len(text):
            adv += kern.get(ch + text[i + 1], 0) * size / 1000
        x += adv
    width = x - tracking
    return items, width

def text_path(fontname, text, size, x=0, y=0, tracking=0, kern=None, anchor='start', warp=None):
    """warp: callable (px, py) -> (X, Y) applied after placement (py measured up from baseline as negative)."""
    f, gs, cmap, upm = font(fontname)
    s = size / upm
    items, width = layout(fontname, text, size, tracking, kern)
    if anchor == 'middle':
        x0 = x - width / 2
    elif anchor == 'end':
        x0 = x - width
    else:
        x0 = x
    parts = []
    for g, gx in items:
        rec = DecomposingRecordingPen(gs); gs[g].draw(rec)
        def tf(px, py, gx=gx):
            X = x0 + gx + px * s
            Y = y - py * s
            if warp:
                return warp(X, Y)
            return X, Y
        parts.append(_emit(rec, tf))
    return ''.join(parts), width

def arc_warp(cx, cy, r, x_center, baseline_y, outward=True):
    """Bend horizontal text around a circle. Text laid out along baseline_y centred on x_center.
    outward=True: text sits on top arc reading left->right, letters pointing away from centre.
    outward=False: text on bottom arc, readable, letters pointing toward centre."""
    def w(X, Y):
        dx = X - x_center
        h = baseline_y - Y  # height above baseline
        if outward:
            ang = -math.pi / 2 + dx / r
            rr = r + h
        else:
            ang = math.pi / 2 - dx / r
            rr = r - h
        return cx + rr * math.cos(ang), cy + rr * math.sin(ang)
    return w

def arch_warp(x_center, half, amount, smile=False):
    """Vertical arch envelope: letters stay upright, baseline bends.
    amount>0 lifts the middle (rainbow) unless smile=True (middle drops)."""
    def w(X, Y):
        u = (X - x_center) / half
        k = amount * max(0.0, 1 - u * u)
        return X, (Y + k) if smile else (Y - k)
    return w
