"""Shared palette and relief helpers."""
INK = '#151b5e'      # encre outremer foncée
BAND = '#1b2390'     # outremer
RISO = '#2536d0'     # bleu riso
YEL = '#f5bf1d'      # jaune label
PAPER = '#f1f1eb'
VINYL = '#0b0c18'
NIGHT = '#0d1033'

_uid = [0]
def uid(p='e'):
    _uid[0] += 1
    return f"{p}{_uid[0]}"

def relief(d, face=YEL, side=BAND, outline=INK, depth=14, dx=1.0, dy=1.0, ow=5, fw=0, shine=None, stripes=None, keyline=None, kw=9):
    """Return SVG for a path with a solid 3D extrusion, outer outline, and optional shine/stripes.
    shine: colour of a thin inner highlight (offset up-left) clipped to the face.
    stripes: (colour, [(y0,y1),...]) horizontal bands clipped to the face."""
    pid = uid('p')
    out = [f'<defs><path id="{pid}" d="{d}"/></defs>']
    steps = [(i * dx, i * dy) for i in range(int(depth), -1, -1)]
    if keyline:
        out.append(f'<g fill="{keyline}" stroke="{keyline}" stroke-width="{(ow+kw)*2}" stroke-linejoin="round">')
        for x, y in steps:
            out.append(f'<use href="#{pid}" transform="translate({x:.2f} {y:.2f})"/>')
        out.append('</g>')
    # outer outline: stroke of every extrusion copy
    if outline:
        out.append(f'<g fill="{outline}" stroke="{outline}" stroke-width="{ow*2}" stroke-linejoin="round">')
        for x, y in steps:
            out.append(f'<use href="#{pid}" transform="translate({x:.2f} {y:.2f})"/>')
        out.append('</g>')
    # extrusion body
    out.append(f'<g fill="{side}">')
    for x, y in steps[:-1]:
        out.append(f'<use href="#{pid}" transform="translate({x:.2f} {y:.2f})"/>')
    out.append('</g>')
    # face
    out.append(f'<path d="{d}" fill="{face}"/>' if not fw else f'<path d="{d}" fill="{face}" stroke="{outline}" stroke-width="{fw}" stroke-linejoin="round"/>')
    cid = uid('c')
    if shine or stripes:
        out.append(f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">')
        if stripes:
            col, bands = stripes
            for y0, y1 in bands:
                out.append(f'<rect x="-5000" y="{y0}" width="20000" height="{y1-y0}" fill="{col}"/>')
        if shine:
            out.append(f'<rect x="-5000" y="-5000" width="20000" height="20000" fill="{shine}"/>')
            out.append(f'<path d="{d}" fill="{face}" transform="translate(5 5)"/>')
        out.append('</g>')
    return '\n'.join(out)

def vinyl(cx, cy, r, label_r=None, label=YEL, rings=7, body=VINYL, groove=PAPER):
    label_r = label_r or r * 0.4
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{body}"/>',
           f'<g fill="none" stroke="{groove}" stroke-opacity=".2" stroke-width="{max(1.2, r/110):.2f}">']
    span = r * 0.93 - label_r * 1.12
    for i in range(rings):
        rr = r * 0.93 - span * i / max(1, rings - 1)
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{rr:.1f}"/>')
    out.append('</g>')
    # light sheen arcs
    out.append(f'<path d="M{cx - r*0.62:.1f} {cy - r*0.62:.1f} A{r*0.88:.1f} {r*0.88:.1f} 0 0 1 {cx + r*0.18:.1f} {cy - r*0.86:.1f}" fill="none" stroke="{groove}" stroke-opacity=".35" stroke-width="{r/40:.1f}" stroke-linecap="round"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{label_r}" fill="{label}"/>')
    return '\n'.join(out)

def svg(w, h, body, bg=None):
    bgr = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ''
    return f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{bgr}{body}</svg>'
