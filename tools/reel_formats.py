"""Trois formats de Reels 1080x1920 (champ "format" du JSON) :
  journal   : « Ce jour-là » façon une de quotidien vintage, texte tapé à la machine
  countdown : anecdote « Le saviez-vous ? », compte à rebours 3-2-1 avec gros chiffres
  docu      : mini-documentaire, frise chronologique et grain de pellicule
Usage : python3 tools/reel_formats.py instagram/AAAA-MM-JJ-xxx.json [photos locales...]
Sortie : out/instagram/<stem>/reel.mp4 (+ reel_credit.txt). La vraie musique est ajoutée à la publication
(Metricool, catalogue Instagram) ; la vidéo garde une musique libre en secours."""
import json, random, subprocess, sys, urllib.parse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reel import (ROOT, W, H, FPS, NAVY, BLUE, YELLOW, PAPER, head, mono, serif, wrap, riso, fetch,
                  photos, pick_music, cover_fit, ease)

INK = (24, 22, 20)
NEWS = (236, 228, 208)


def sepia(img):
    g = ImageOps.autocontrast(ImageOps.grayscale(img), cutoff=1)
    return ImageOps.colorize(g, (30, 26, 22), (238, 228, 205))


def grain(im, amount=18, seed=0):
    rnd = random.Random(seed)
    n = Image.effect_noise((W // 2, H // 2), amount).resize((W, H)).convert("RGB")
    return Image.blend(im, n, 0.06 + rnd.random() * 0.02)


def text_block(d, x, y, text, font, width, fill, lh, maxl=6, reveal=1.0, anchor_center=False):
    lines = wrap(d, text, font, width)[:maxl]
    total = sum(len(l) for l in lines)
    shown = int(total * reveal)
    for l in lines:
        part = l[:max(0, shown)]
        shown -= len(l)
        if part:
            if anchor_center:
                d.text((W // 2, y), part, font=font, fill=fill, anchor="ma")
            else:
                d.text((x, y), part, font=font, fill=fill)
        y += lh
    return y


def fit_size(d, text, maker, start, width, maxl, minsize=60):
    s = start
    while s > minsize and len(wrap(d, text, maker(s), width)) > maxl:
        s -= 6
    return s


# ---------- format 1 : la une ----------
def frame_journal(t, spec, pics, segs):
    im = Image.new("RGB", (W, H), NEWS)
    d = ImageDraw.Draw(im)
    seg, lt, ln = segs(t)
    # bandeau du journal
    d.text((W // 2, 90), "LE RIFF QUOTIDIEN", font=head(110), fill=INK, anchor="ma")
    d.line((60, 220, W - 60, 220), fill=INK, width=6)
    d.line((60, 232, W - 60, 232), fill=INK, width=2)
    d.text((60, 250), spec.get("dateline", spec.get("big", "")).upper(), font=mono(34), fill=INK)
    d.text((W - 60, 250), "ÉDITION SPÉCIALE", font=mono(34), fill=INK, anchor="ra")
    d.line((60, 300, W - 60, 300), fill=INK, width=2)
    slides = spec["slides"]
    if seg == 0:  # une : gros titre + photo
        a = ease(lt / 0.6)
        size = fit_size(d, spec["title"].upper(), head, 150, W - 120, 4)
        y = text_block(d, 60, 340 + int(40 * (1 - a)), spec["title"].upper(), head(size), W - 120, INK, int(size * 0.95), 4)
        if pics:
            z = 1.05 + 0.08 * (lt / ln)
            ph = cover_fit(sepia(pics[0]), W - 120, H - y - 200, z)
            im.paste(ph, (60, y + 30))
            d.rectangle((60, y + 30, W - 60, y + 30 + ph.height), outline=INK, width=4)
    elif seg <= len(slides):
        s = slides[seg - 1]
        if pics:
            p = pics[seg % len(pics)]
            z = 1.04 + 0.1 * (lt / ln)
            ph = cover_fit(sepia(p), W - 120, 900, z, 0.3, 0.5)
            im.paste(ph, (60, 340))
            d.rectangle((60, 340, W - 60, 1240), outline=INK, width=4)
        if s.get("head"):
            d.text((60, 1280), s["head"].upper(), font=mono(38), fill=(150, 30, 30))
        size = fit_size(d, s["big"], lambda z: serif(z, italic=False), 74, W - 120, 5, 44)
        text_block(d, 60, 1350, s["big"], serif(size, italic=False), W - 120, INK, int(size * 1.25), 5,
                   reveal=min(1, lt / (ln * 0.55)))
    else:
        d.text((W // 2, 700), spec.get("big", ""), font=head(260), fill=INK, anchor="mm")
        d.text((W // 2, 930), "L'HISTOIRE COMPLÈTE", font=head(110), fill=INK, anchor="mm")
        d.text((W // 2, 1050), "lien en bio", font=serif(60), fill=(150, 30, 30), anchor="mm")
        d.text((W // 2, 1150), "riffsetlegendes.github.io", font=mono(40), fill=INK, anchor="mm")
    return grain(im, 30, int(t * 8))


# ---------- format 2 : compte à rebours ----------
def frame_countdown(t, spec, pics, segs):
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    seg, lt, ln = segs(t)
    slides = spec["slides"][:3]
    if seg == 0:  # accroche plein écran
        if pics:
            bg = cover_fit(riso(pics[0]), W, H, 1.15 - 0.08 * (lt / ln)).filter(ImageFilter.GaussianBlur(3))
            im = Image.blend(im, bg, 0.45)
            d = ImageDraw.Draw(im)
        d.text((70, 200), "LE SAVIEZ-VOUS ?", font=mono(44), fill=YELLOW)
        hook = spec.get("hook", spec["title"]).upper()
        size = fit_size(d, hook, head, 150, W - 140, 6)
        a = ease(lt / 0.5)
        text_block(d, 70, 420 + int(60 * (1 - a)), hook, head(size), W - 140, PAPER, int(size * 0.95), 6)
    elif seg <= len(slides):
        s = slides[seg - 1]
        n = len(slides) - seg + 1
        if pics:
            ph = cover_fit(riso(pics[seg % len(pics)]), W, 1000, 1.2 - 0.12 * ease(lt / ln))
            im.paste(ph, (0, 0))
        # gros numéro qui claque
        k = ease(lt / 0.25)
        sz = int(560 - 160 * k)
        d.text((W - 40, 1060), str(n), font=head(sz), fill=YELLOW, anchor="rs")
        d.rectangle((0, 1000, W, 1010), fill=YELLOW)
        size = fit_size(d, s["big"].upper(), head, 120, W - 140, 3)
        y = text_block(d, 70, 1090, s["big"].upper(), head(size), W - 140, PAPER, int(size * 0.95), 3)
        c = ease((lt - 0.6) / 0.5)
        if c > 0.02 and s.get("text"):
            text_block(d, 70, y + 30, s["text"], serif(48, italic=False), W - 140,
                       tuple(int(NAVY[i] + (PAPER[i] - NAVY[i]) * c) for i in range(3)), 62, 4)
    else:
        d.text((W // 2, 760), "L'HISTOIRE COMPLÈTE", font=head(120), fill=PAPER, anchor="mm")
        d.text((W // 2, 880), "lien en bio", font=serif(60), fill=YELLOW, anchor="mm")
        d.text((W // 2, 990), "riffsetlegendes.github.io", font=mono(40), fill=PAPER, anchor="mm")
    return im


# ---------- format 3 : mini-documentaire ----------
def frame_docu(t, spec, pics, segs):
    im = Image.new("RGB", (W, H), (8, 8, 10))
    d = ImageDraw.Draw(im)
    seg, lt, ln = segs(t)
    slides = spec["slides"]
    BAR = 300
    if seg == 0:
        if pics:
            ph = cover_fit(ImageOps.grayscale(pics[0]).convert("RGB"), W, H - 2 * BAR, 1.25 - 0.12 * (lt / ln))
            im.paste(ph, (0, BAR))
            im = Image.blend(Image.new("RGB", (W, H), (8, 8, 10)), im, min(1, lt / 1.0) * 0.75)
            d = ImageDraw.Draw(im)
        a = ease((lt - 0.4) / 0.9)
        d.text((W // 2, 360), "EN 30 SECONDES", font=mono(40), fill=YELLOW, anchor="ma")
        size = fit_size(d, spec["title"].upper(), head, 130, W - 160, 4)
        lines = wrap(d, spec["title"].upper(), head(size), W - 160)[:4]
        y = H // 2 - len(lines) * size * 0.95 / 2
        for l in lines:
            d.text((W // 2, y), l, font=head(size), fill=(int(240 * a),) * 3, anchor="ma")
            y += size * 0.95
    elif seg <= len(slides):
        s = slides[seg - 1]
        if pics:
            p = pics[seg % len(pics)]
            ph = cover_fit(ImageOps.grayscale(p).convert("RGB"), W, H - 2 * BAR, 1.06 + 0.14 * (lt / ln),
                           0.25 + 0.1 * (seg % 2), 0.4 + 0.2 * (seg % 2))
            im.paste(ph, (0, BAR))
            if lt < 0.5:
                im = Image.blend(Image.new("RGB", (W, H), (8, 8, 10)), im, lt / 0.5)
            d = ImageDraw.Draw(im)
        # frise
        n = len(slides)
        x0, x1, yy = 90, W - 90, BAR - 90
        d.line((x0, yy, x1, yy), fill=(90, 90, 90), width=4)
        prog = (seg - 1 + min(1, lt / ln)) / n
        d.line((x0, yy, x0 + (x1 - x0) * prog, yy), fill=YELLOW, width=6)
        for k in range(n):
            cx = x0 + (x1 - x0) * (k + 0.5) / n
            on = k < seg
            d.ellipse((cx - 12, yy - 12, cx + 12, yy + 12), fill=YELLOW if on else (90, 90, 90))
        d.text((W // 2, BAR - 200), s.get("head", "").upper(), font=head(90), fill=YELLOW, anchor="ma")
        # sous-titre cinéma
        a = ease((lt - 0.3) / 0.6)
        if a > 0.02:
            col = (int(240 * a),) * 3
            text_block(d, 0, H - BAR + 50, s["big"], serif(56, italic=False), W - 160, col, 70, 3, anchor_center=True)
    else:
        d.text((W // 2, 800), "L'HISTOIRE COMPLÈTE", font=head(120), fill=(240, 240, 240), anchor="mm")
        d.text((W // 2, 920), "lien en bio", font=serif(60), fill=YELLOW, anchor="mm")
        d.text((W // 2, 1030), "riffsetlegendes.github.io", font=mono(40), fill=(240, 240, 240), anchor="mm")
    return grain(im, 40, int(t * 12))


STYLES = {"journal": (frame_journal, 3.2, 4.0, 3.0),
          "countdown": (frame_countdown, 3.0, 4.2, 2.8),
          "docu": (frame_docu, 3.6, 4.6, 3.2)}


def main():
    spec_path = Path(sys.argv[1])
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    fmt = spec.get("format", "countdown")
    draw, t_in, t_sl, t_out = STYLES[fmt]
    pics = photos(spec, sys.argv[2:])
    slides = spec["slides"][:3] if fmt == "countdown" else spec["slides"][:5]
    dur = t_in + t_sl * len(slides) + t_out
    out = ROOT / "out" / "instagram" / spec_path.stem
    out.mkdir(parents=True, exist_ok=True)

    def segs(t):
        if t < t_in:
            return 0, t, t_in
        k = int((t - t_in) // t_sl)
        if k < len(slides):
            return k + 1, t - t_in - k * t_sl, t_sl
        return len(slides) + 1, t - t_in - len(slides) * t_sl, t_out

    title, filename = pick_music(spec, sum(map(ord, spec_path.stem)))
    mp3 = out / "music.mp3"
    try:
        mp3.write_bytes(fetch("https://incompetech.com/music/royalty-free/mp3-royaltyfree/" + urllib.parse.quote(filename)))
        audio = ["-ss", "4", "-i", str(mp3)]
        afilter = ["-af", f"afade=t=in:d=0.6,afade=t=out:st={dur - 2:.2f}:d=2,volume=0.9"]
        (out / "reel_credit.txt").write_text(f"Musique : « {title} », Kevin MacLeod (incompetech.com), licence CC BY 4.0\n", encoding="utf-8")
    except Exception as ex:
        print("musique indisponible :", ex, file=sys.stderr)
        audio, afilter = ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"], []
        (out / "reel_credit.txt").write_text("", encoding="utf-8")
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", *audio, "-t", f"{dur:.2f}", *afilter, "-map", "0:v", "-map", "1:a",
                             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
                             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out / "reel.mp4")], stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)):
        proc.stdin.write(draw(i / FPS, spec, pics, segs).convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()
    print(out / "reel.mp4", f"{dur:.1f}s", fmt)


if __name__ == "__main__":
    main()
