"""Reel Instagram 1080x1920 à partir d'un carrousel : plusieurs photos en bichromie, mouvements de caméra,
textes lisibles, logo final, musique libre de droits (Kevin MacLeod, CC BY 4.0).
Usage : python3 tools/reel.py instagram/AAAA-MM-JJ-xxx.json  ->  out/instagram/<stem>/reel.mp4 + reel_credit.txt"""
import io, json, math, random, re, subprocess, sys, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "tools" / "fonts"
W, H, FPS = 1080, 1920, 30
NAVY, BLUE, YELLOW, PAPER = (21, 27, 94), (37, 54, 208), (245, 191, 29), (241, 241, 235)
UA = {"User-Agent": "RiffsEtLegendes/1.0 (riffsetlegendes.github.io)"}
T_INTRO, T_SLIDE, T_END = 3.6, 4.2, 3.6


def head(size, wght=900):
    f = ImageFont.truetype(str(F / "BigShouldersDisplay.ttf"), size)
    try:
        f.set_variation_by_axes([wght])
    except Exception:
        pass
    return f


def mono(size):
    return ImageFont.truetype(str(F / "DMMono-Medium.ttf"), size)


def serif(size, italic=True):
    return ImageFont.truetype(str(F / ("Newsreader-Italic.ttf" if italic else "Newsreader.ttf")), size)


def wrap(d, text, font, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    return lines + ([cur] if cur else [])


def riso(img):
    g = ImageOps.autocontrast(ImageOps.grayscale(img), cutoff=1).point(lambda v: min(255, int(v * 1.08)))
    return Image.merge("RGB", tuple(g.point(lambda v, c=c: max(v, c)) for c in BLUE))


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def photos(spec, local):
    if local:
        return [riso(Image.open(p).convert("RGB")) for p in local]
    names = spec.get("photos") or ([spec["photo"]] if spec.get("photo") else [])
    out = []
    for n in names:
        try:
            data = fetch("https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(n) + "?width=1400")
            out.append(riso(Image.open(io.BytesIO(data)).convert("RGB")))
        except Exception as ex:
            print("photo indisponible :", n, ex, file=sys.stderr)
    return out


def pick_music(spec, seed):
    lib = json.loads((ROOT / "music" / "library.json").read_text(encoding="utf-8"))
    cat = {x["title"]: x for x in json.loads((ROOT / "music" / "incompetech.json").read_text(encoding="utf-8"))}
    mood = spec.get("music_mood")
    if not mood:
        ys = [int(v) for v in re.findall(r"(19\d\d)", spec.get("disc", "") + " " + spec.get("big", ""))]
        y = (ys[0] + 22 if len(ys) > 1 else ys[0]) if ys else 1970  # pour une vie, l'âge d'or vers 22 ans
        txt = json.dumps(spec, ensure_ascii=False).lower()
        mood = "punk" if "punk" in txt else "blues" if "blues" in txt else "fifties" if y < 1963 else "seventies"
    title = random.Random(seed).choice(lib[mood])
    return title, cat[title]["filename"]


def cover_fit(img, w, h, zoom, fy=0.3, fx=0.5):
    s = max(w / img.width, h / img.height) * zoom
    im = img.resize((math.ceil(img.width * s), math.ceil(img.height * s)), Image.BILINEAR)
    x, y = int((im.width - w) * fx), int((im.height - h) * fy)
    return im.crop((x, y, x + w, y + h))


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


MOVES = [(1.28, 1.04, 0.5, 0.5, 0.25, 0.3), (1.04, 1.22, 0.35, 0.62, 0.3, 0.25), (1.22, 1.08, 0.66, 0.42, 0.2, 0.35),
         (1.06, 1.26, 0.5, 0.5, 0.35, 0.18), (1.25, 1.05, 0.4, 0.6, 0.22, 0.3)]


def main():
    spec_path = Path(sys.argv[1])
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    pics = photos(spec, sys.argv[2:])
    out = ROOT / "out" / "instagram" / spec_path.stem
    out.mkdir(parents=True, exist_ok=True)
    slides = spec.get("slides", [])[:4]
    dur = T_INTRO + T_SLIDE * len(slides) + T_END
    seed = sum(map(ord, spec_path.stem))
    # musique
    title, filename = pick_music(spec, seed)
    mp3 = out / "music.mp3"
    try:
        mp3.write_bytes(fetch("https://incompetech.com/music/royalty-free/mp3-royaltyfree/" + urllib.parse.quote(filename)))
        audio = ["-ss", "4", "-i", str(mp3)]
        afilter = ["-af", f"afade=t=in:d=0.6,afade=t=out:st={dur - 2.2:.2f}:d=2.2,volume=0.9"]
        (out / "reel_credit.txt").write_text(f"Musique : « {title} », Kevin MacLeod (incompetech.com), licence CC BY 4.0\n", encoding="utf-8")
    except Exception as ex:
        print("musique indisponible :", ex, file=sys.stderr)
        audio, afilter = ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"], []
        (out / "reel_credit.txt").write_text("", encoding="utf-8")
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", *audio, "-t", f"{dur:.2f}", *afilter, "-map", "0:v", "-map", "1:a",
                             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
                             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out / "reel.mp4")], stdin=subprocess.PIPE)
    year = spec.get("disc") or spec.get("big", "")
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    ys = 300
    while ys > 120 and probe.textlength(str(year), font=head(ys)) > W - 140:
        ys -= 10
    fk, fy, ft, fh, fb, fx = mono(34), head(ys), head(112), mono(36), head(112), serif(44, italic=False)
    logo = Image.open(ROOT / "tools" / "symbole.png").convert("RGBA").resize((600, 600), Image.LANCZOS)
    PH = 1120
    t_end = T_INTRO + T_SLIDE * len(slides)
    for i in range(int(dur * FPS)):
        t = i / FPS
        im = Image.new("RGB", (W, H), NAVY)
        d = ImageDraw.Draw(im)
        if t < t_end:
            segi = 0 if t < T_INTRO else 1 + int((t - T_INTRO) // T_SLIDE)
            t0 = 0 if segi == 0 else T_INTRO + (segi - 1) * T_SLIDE
            ln = T_INTRO if segi == 0 else T_SLIDE
            lt = t - t0
            if pics:
                p = ease(lt / ln) * 0.8 + 0.2 * (lt / ln)
                z0, z1, x0, x1, y0, y1 = MOVES[segi % len(MOVES)]
                im.paste(cover_fit(pics[segi % len(pics)], W, PH, z0 + (z1 - z0) * p, y0 + (y1 - y0) * p, x0 + (x1 - x0) * p), (0, 0))
                if lt < 0.25 and segi > 0:  # fondu rapide entre deux photos
                    im = Image.blend(Image.new("RGB", (W, H), NAVY), im, lt / 0.25)
                    d = ImageDraw.Draw(im)
            else:
                for r in range(200, 1700, 16):
                    d.ellipse((W // 2 - r, PH // 2 - r, W // 2 + r, PH // 2 + r), outline=(32, 40, 125), width=2)
            if segi == 0:
                a = ease(lt / 0.8)
                d.text((70, 90), spec.get("label", "").upper(), font=fk, fill=YELLOW)
                d.text((64, PH - 40 + int(80 * (1 - a))), str(year), font=fy, fill=YELLOW, anchor="ls")
                b = ease((lt - 0.5) / 0.8)
                for k, l in enumerate(wrap(d, spec["title"].upper(), ft, W - 140)[:5]):
                    if b > 0.02:
                        d.text((70, PH + 90 + k * 104 + int(60 * (1 - b))), l, font=ft, fill=PAPER)
            else:
                s = slides[segi - 1]
                d.rectangle((0, PH, int(W * min(1, lt / ln)), PH + 8), fill=YELLOW)
                d.text((70, 90), f"{segi:02d} / {len(slides):02d}", font=fk, fill=YELLOW)
                d.text((70, PH + 70), s.get("head", "").upper(), font=fh, fill=YELLOW)
                y = PH + 130
                for j, l in enumerate(wrap(d, s["big"].upper(), fb, W - 140)[:3]):
                    off = int(60 * (1 - ease((lt - 0.08 * j) / 0.6)))
                    d.text((70, y + off), l, font=fb, fill=PAPER)
                    y += 108
                c = ease((lt - 0.7) / 0.6)
                if c > 0.02 and s.get("text"):
                    y += 24
                    for l in wrap(d, s["text"], fx, W - 140)[:5]:
                        d.text((70, y + int(30 * (1 - c))), l, font=fx, fill=(int(21 + 214 * c), int(27 + 210 * c), int(94 + 141 * c)))
                        y += 58
        else:  # fin : le logo tourne
            lt = t - t_end
            a = ease(lt / 0.7)
            v = logo.rotate(-lt * 110, resample=Image.BICUBIC)
            sc = 0.82 + 0.18 * a
            v = v.resize((int(600 * sc), int(600 * sc)), Image.BICUBIC)
            im.paste(v, ((W - v.width) // 2, 640 - v.height // 2), v)
            d.text((W // 2, 1200), "L'HISTOIRE COMPLÈTE", font=head(120), fill=PAPER, anchor="mm")
            d.text((W // 2, 1320), "sur le site, lien en bio", font=serif(56), fill=YELLOW, anchor="mm")
            d.text((W // 2, 1450), "riffsetlegendes.github.io", font=mono(40), fill=PAPER, anchor="mm")
        proc.stdin.write(im.tobytes())
    proc.stdin.close()
    proc.wait()
    print(out / "reel.mp4", f"{dur:.1f}s", title)


if __name__ == "__main__":
    main()
