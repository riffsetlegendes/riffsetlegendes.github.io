"""Génère le système de logo Riffs & Légendes (rétro en relief).
Lancer depuis ce dossier : python3 build_logo.py  -> fichiers SVG dans ./out
Polices : Fraunces (mots), Young Serif (esperluette), DM Mono (signature), sous licence OFL."""
import os, re
from glyphs import text_path, arch_warp, layout
from fx import *
import lockups as v2
F='fraunces-black-soft.ttf'; AMP='youngserif.ttf'; SH='#fde7a0'
OUT='out'; os.makedirs(OUT,exist_ok=True)
def save(name, s): open(f'{OUT}/{name}','w').write(s)

def tight(body, x0,y0,x1,y1, bg=None):
    w,h=x1-x0,y1-y0
    bgr=f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="{bg}"/>' if bg else ''
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {w} {h}" width="{w}" height="{h}">{bgr}{body}</svg>'

# 1. wordmark seul, une ligne, fond transparent (en-tête du site)
def wordmark(dark, face=YEL, shine=SH):
    s=170; base=200; x=40
    side=RISO if dark else BAND; outl=VINYL if dark else INK; kl=PAPER if dark else None
    d1,w1=text_path(F,'Riffs',s,x,base,tracking=-3)
    _,wa=text_path(AMP,'&',175,0,0)
    ax=x+w1+34; amp,_=text_path(AMP,'&',175,ax,base+4)
    x2=ax+wa+30; d2,w2=text_path(F,'Légendes',s,x2,base,tracking=-4)
    body=''.join(relief(d,face=face,side=side,outline=outl,depth=11,ow=4,shine=shine,keyline=kl) for d in (d1,amp,d2))
    pad=12 if dark else 6
    return tight(body, x-pad-8, 40, x2+w2+30, 290)
save('wordmark.svg', wordmark(False)); save('wordmark-sombre.svg', wordmark(True))
save('wordmark-sur-jaune.svg', wordmark(False, face=PAPER, shine=None))  # bandeau jaune du pied de page

# 2. symbole : vinyle + étiquette + esperluette
def symbole(body_col=VINYL, label=YEL, amp_col=INK, bg=None, size=320):
    c=size/2; r=size*0.47
    b=vinyl(c,c,r,label_r=r*0.43,label=label,rings=5,body=body_col)
    a,_=text_path(AMP,'&',r*0.62,c+r*0.01,c+r*0.20,anchor='middle')
    b+=f'<path d="{a}" fill="{amp_col}"/>'
    return svg(size,size,b,bg)
save('symbole.svg', symbole())
save('symbole-jaune.svg', symbole(body_col=INK, label=YEL))
save('favicon.svg', symbole())
save('icon-512.svg', svg(512,512, re.sub(r'^<svg[^>]*>|</svg>$','',symbole(size=512)).replace('<circle','<circle',1), BAND))

# 3. bloc et ligne (versions validées, & Young Serif)
for t in ['papier','outremer']: save(f'logo-bloc-{t}.svg', v2.bloc(t,AMP,170))
for t in ['papier','nuit']: save(f'logo-ligne-{t}.svg', v2.ligne(t,AMP,175,None))

# 4. écusson
def ecusson(theme):
    W,H=1200,1100; cx,cy=600,560
    dark=theme!='papier'
    bg={'papier':PAPER,'outremer':BAND}[theme]
    side=RISO if dark else BAND; outl=VINYL if dark else INK; kl=PAPER if dark else None
    R=265; body=[]
    if dark: body.append(f'<circle cx="{cx}" cy="{cy}" r="{R+10}" fill="{PAPER}"/>')
    body.append(vinyl(cx,cy,R,label_r=108,rings=8))
    a,_=text_path(AMP,'&',190,cx+2,cy+58,anchor='middle'); body.append(f'<path d="{a}" fill="{INK}"/>')
    s1=270; _,w1=layout(F,'RIFFS',s1,tracking=-2)
    d1,_=text_path(F,'RIFFS',s1,cx,400,tracking=-2,anchor='middle',warp=arch_warp(cx,w1/2,80))
    s2=190; _,w2=layout(F,'LÉGENDES',s2,tracking=-2)
    d2,_=text_path(F,'LÉGENDES',s2,cx,905,tracking=-2,anchor='middle',warp=arch_warp(cx,w2/2,70,smile=True))
    for d in (d1,d2): body.append(relief(d,side=side,outline=outl,depth=15,shine=SH,keyline=kl))
    return svg(W,H,'\n'.join(body),bg)
for t in ['papier','outremer']: save(f'logo-ecusson-{t}.svg', ecusson(t))

# 5. avatar Instagram R&L
def avatar(theme='outremer'):
    W=H=1080; cx=cy=540
    bg={'outremer':BAND,'papier':PAPER}[theme]
    body=[vinyl(cx,cy,470,label_r=158,rings=10)]
    s=360; _,wR=text_path(F,'R',s,0,0); _,wL=text_path(F,'L',s,0,0)
    gap=370; x0=cx-(wR+gap+wL)/2
    dR,_=text_path(F,'R',s,x0,cy+128); dL,_=text_path(F,'L',s,x0+wR+gap,cy+128)
    a,_=text_path(AMP,'&',215,cx+2,cy+66,anchor='middle'); body.append(f'<path d="{a}" fill="{INK}"/>')
    for d in (dR,dL): body.append(relief(d,side=BAND,outline=INK,depth=20,ow=6,shine=SH))
    return svg(W,H,'\n'.join(body),bg)
save('avatar-instagram.svg', avatar('outremer')); save('avatar-papier.svg', avatar('papier'))
print(sorted(os.listdir(OUT)))

# 6. disque seul (en-tête du site, tourne au survol) : étiquette jaune, trou central
def disque(size=320):
    c=size/2; r=size*0.47
    return svg(size,size,vinyl(c,c,r,label_r=r*0.43,rings=5)+f'<circle cx="{c}" cy="{c}" r="{r*0.06:.1f}" fill="{INK}"/>')
save('disque.svg', disque())
