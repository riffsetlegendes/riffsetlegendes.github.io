"""Mises en page du logo : bloc deux lignes et version en ligne."""
from glyphs import text_path
from fx import *
F='fraunces-black-soft.ttf'
SH='#fde7a0'
def bloc(theme, AF, asz):
    W,H=1300,800; X=110
    dark=theme!='papier'
    bg={'papier':PAPER,'outremer':BAND,'nuit':NIGHT}[theme]
    side=RISO if dark else BAND; outl=VINYL if dark else INK; kl=PAPER if dark else None
    d1,w1=text_path(F,'Riffs',250,X,330,tracking=-4)
    d2,w2=text_path(F,'Légendes',250,X,612,tracking=-6)
    cx=X+w1+(w2-w1)/2+18; cy=250; r=212
    body=[]
    if dark: body.append(f'<circle cx="{cx}" cy="{cy}" r="{r+9}" fill="{PAPER}"/>')
    body.append(vinyl(cx,cy,r,label_r=92))
    amp,_=text_path(AF,'&',asz,cx+2,cy+asz*0.30,anchor='middle')
    body.append(f'<path d="{amp}" fill="{INK}"/>')
    for d in (d1,d2): body.append(relief(d,side=side,outline=outl,depth=16,shine=SH,keyline=kl))
    tag,_=text_path('dmmono.ttf','LE ROCK DE 1950 À 1999 · UN JOUR À LA FOIS',21,X+6,752,tracking=4.2)
    body.append(f'<path d="{tag}" fill="{PAPER if dark else INK}"/>')
    return svg(W,H,'\n'.join(body),bg)
def ligne(theme, AF, asz, aface):
    dark=theme!='papier'
    bg={'papier':PAPER,'outremer':BAND,'nuit':NIGHT}[theme]
    side=RISO if dark else BAND; outl=VINYL if dark else INK; kl=PAPER if dark else None
    s=170; base=250; r=118; vx=40+r; vy=base-58
    x=vx+r+40
    d1,w1=text_path(F,'Riffs',s,x,base,tracking=-3)
    amp,wa=text_path(AF,'&',asz,0,0)
    ax=x+w1+34
    amp,_=text_path(AF,'&',asz,ax,base+4)
    x2=ax+wa+30
    d2,w2=text_path(F,'Légendes',s,x2,base,tracking=-4)
    W=int(x2+w2+60); H=360
    body=[]
    if dark: body.append(f'<circle cx="{vx}" cy="{vy}" r="{r+7}" fill="{PAPER}"/>')
    body.append(vinyl(vx,vy,r,label_r=48,rings=6))
    body.append(f'<circle cx="{vx}" cy="{vy}" r="7" fill="{bg}"/>')
    for d in (d1,d2): body.append(relief(d,side=side,outline=outl,depth=11,ow=4,shine=SH,keyline=kl))
    face=aface if aface else YEL
    body.append(relief(amp,face=face,side=side,outline=outl,depth=11,ow=4,shine=SH if face==YEL else None,keyline=kl))
    tag,_=text_path('dmmono.ttf','LE ROCK DE 1950 À 1999 · UN JOUR À LA FOIS',19,x+4,base+70,tracking=4)
    body.append(f'<path d="{tag}" fill="{PAPER if dark else INK}"/>')
    return svg(W,H,'\n'.join(body),bg)
