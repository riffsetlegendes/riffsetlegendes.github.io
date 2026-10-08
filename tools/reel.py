"""Reel Instagram 1080x1920 (15 s, 30 i/s) à partir d'un carrousel : photo en bichromie, textes animés, disque final.
Usage : python3 tools/reel.py instagram/AAAA-MM-JJ-xxx.json [photo_locale.jpg]  ->  out/instagram/<stem>/reel.mp4"""
import io, json, math, subprocess, sys, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "tools" / "fonts"
W, H, FPS, DUR = 1080, 1920, 30, 15.0
NAVY, BLUE, YELLOW, PAPER, VINYL = (21, 27, 94), (37, 54, 208), (245, 191, 29), (241, 241, 235), (11, 12, 24)


def head(size, wght=900):
    f = ImageFont.truetype(str(F / "BigShouldersDisplay.ttf"), size)
    try:
        f.set_variation_by_axes([wght])
    except Exception:
        pass
    return f


def mono(size):
    return ImageFont.truetype(str(F / "DMMono-Medium.ttf"), size)


def serif(size):
    return ImageFont.truetype(str(F / "Newsreader-Italic.ttf"), size)


def wrap(d, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def riso(img):
    g = ImageOps.autocontrast(ImageOps.grayscale(img), cutoff=1)
    g = g.point(lambda v: min(255, int(v * 1.08)))
    r = g.point(lambda v: max(v, BLUE[0])); gg = g.point(lambda v: max(v, BLUE[1])); b = g.point(lambda v: max(v, BLUE[2]))
    return Image.merge("RGB", (r, gg, b))


def get_photo(spec, local=None):
    try:
        if local:
            return Image.open(local).convert("RGB")
        if spec.get("photo"):
            url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(spec["photo"]) + "?width=1400"
            req = urllib.request.Request(url, headers={"User-Agent": "RiffsEtLegendes/1.0 (riffsetlegendes.github.io)"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return Image.open(io.BytesIO(r.read())).convert("RGB")
    except Exception as ex:
        print("photo indisponible :", ex, file=sys.stderr)
    return None


def cover_fit(img, w, h, zoom, focus_y=0.3, focus_x=0.5):
    s = max(w / img.width, h / img.height) * zoom
    im = img.resize((math.ceil(img.width * s), math.ceil(img.height * s)), Image.BILINEAR)
    x = int((im.width - w) * focus_x)
    y = int((im.height - h) * focus_y)
    return im.crop((x, y, x + w, y + h))


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def main():
    spec_path = Path(sys.argv[1])
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    photo = get_photo(spec, sys.argv[2] if len(sys.argv) > 2 else None)
    photo = riso(photo) if photo else None
    out = ROOT / "out" / "instagram" / spec_path.stem
    out.mkdir(parents=True, exist_ok=True)
    slides = spec.get("slides", [])[:4]
    year = spec.get("disc") or spec.get("big", "")
    fk, ft, fh, fb = mono(34), head(118), mono(36), head(128)
    ys = 300
    while ys > 120 and ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(str(year), font=head(ys)) > W - 140:
        ys -= 10
    fy = head(ys)
    sys.path.insert(0, str(ROOT / "tools"))
    import music
    wav = music.make(out / "reel.wav", DUR, seed=sum(map(ord, spec_path.stem)))
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-i", str(wav), "-shortest",
                             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
                             "-c:a", "aac", "-movflags", "+faststart", str(out / "reel.mp4")], stdin=subprocess.PIPE)
    PH = 1240  # hauteur de la zone photo
    seg = 2.3
    t_slides, t_end = 2.6, 2.6 + seg * len(slides)
    vinyl = Image.open(ROOT / "tools" / "symbole.png").convert("RGBA").resize((640, 640), Image.LANCZOS)
    for i in range(int(DUR * FPS)):
        t = i / FPS
        im = Image.new("RGB", (W, H), NAVY)
        d = ImageDraw.Draw(im)
        if t < t_end:
            if photo:
                segi = 0 if t < t_slides else 1 + int((t - t_slides) // seg)
                t0 = 0 if segi == 0 else t_slides + (segi - 1) * seg
                p = ease((t - t0) / (t_slides if segi == 0 else seg)) * 0.85 + 0.15 * ((t - t0) / (t_slides if segi == 0 else seg))
                moves = [(1.25, 1.05, 0.5, 0.5, 0.25, 0.3),   # dézoom d'ouverture
                         (1.05, 1.22, 0.35, 0.6, 0.3, 0.3),  # zoom avant + glissé
                         (1.22, 1.10, 0.65, 0.45, 0.2, 0.35),
                         (1.10, 1.28, 0.5, 0.5, 0.35, 0.2),
                         (1.28, 1.06, 0.4, 0.6, 0.25, 0.3)]
                z0, z1, x0, x1, y0, y1 = moves[segi % len(moves)]
                z = z0 + (z1 - z0) * p
                im.paste(cover_fit(photo, W, PH, z, y0 + (y1 - y0) * p, x0 + (x1 - x0) * p), (0, 0))
            else:
                for r in range(200, 1700, 16):
                    d.ellipse((W // 2 - r, PH // 2 - r, W // 2 + r, PH // 2 + r), outline=(32, 40, 125), width=2)
            if t < t_slides:  # intro
                a = ease(t / 0.8)
                d.text((70, 90), spec.get("label", "").upper(), font=fk, fill=YELLOW)
                d.text((64, PH - 40 + int(80 * (1 - a))), str(year), font=fy, fill=YELLOW, anchor="ls")
                lines = wrap(d, spec["title"].upper(), ft, W - 140)[:4]
                b = ease((t - 0.5) / 0.8)
                for k, ln in enumerate(lines):
                    d.text((70, PH + 90 + k * 108 + int(60 * (1 - b))), ln, font=ft, fill=PAPER if b > 0.05 else NAVY)
            else:
                k = min(int((t - t_slides) // seg), len(slides) - 1)
                s = slides[k]
                lt = (t - t_slides) - k * seg
                a = ease(lt / 0.6)
                d.text((70, 90), f"{k + 1:02d} / {len(slides):02d}", font=fk, fill=YELLOW)
                d.text((70, PH + 70), s.get("head", "").upper(), font=fh, fill=YELLOW)
                lines = wrap(d, s["big"].upper(), fb, W - 140)[:4]
                for j, ln in enumerate(lines):
                    off = int(70 * (1 - ease((lt - 0.08 * j) / 0.6)))
                    d.text((70, PH + 140 + j * 118 + off), ln, font=fb, fill=PAPER)
                d.rectangle((0, PH, int(W * min(1, lt / seg)), PH + 8), fill=YELLOW)
        else:  # fin : disque qui tourne
            lt = t - t_end
            a = ease(lt / 0.7)
            v = vinyl.rotate(-lt * 120, resample=Image.BICUBIC)
            sc = 0.85 + 0.15 * a
            v = v.resize((int(640 * sc), int(640 * sc)), Image.BICUBIC)
            im.paste(v, ((W - v.width) // 2, 640 - v.height // 2), v)
            d.text((W // 2, 1250), "L'HISTOIRE COMPLÈTE", font=head(120), fill=PAPER, anchor="mm")
            d.text((W // 2, 1370), "sur le site, lien en bio", font=serif(56), fill=YELLOW, anchor="mm")
            d.text((W // 2, 1500), "riffsetlegendes.github.io", font=mono(40), fill=PAPER, anchor="mm")
        proc.stdin.write(im.tobytes())
    proc.stdin.close()
    proc.wait()
    print(out / "reel.mp4")


if __name__ == "__main__":
    main()
