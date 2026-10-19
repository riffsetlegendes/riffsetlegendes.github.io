"""Trois formats de Reels 1080x1920 (champ "format" du JSON) :
  journal   : « Ce jour-là » façon une de quotidien vintage, texte tapé à la machine
  countdown : anecdote « Le saviez-vous ? », compte à rebours 3-2-1 avec gros chiffres
  docu      : mini-documentaire, frise chronologique et grain de pellicule
  recit     : récit narré (format des Reels viraux de la niche) : voix off française (edge-tts), photos plein écran
              en mouvement, sous-titres mot à mot, titre fixe en haut. Champs : "narration" [{text, photo}], "title",
              "photos", option "voice" (défaut fr-FR-HenriNeural) et "rate" (défaut +8 %).
Usage : python3 tools/reel_formats.py instagram/AAAA-MM-JJ-xxx.json [photos locales...]
Sortie : out/instagram/<stem>/reel.mp4 (+ reel_credit.txt). La vraie musique est ajoutée à la publication
(Metricool, catalogue Instagram) ; la vidéo garde une musique libre en secours."""
import io, json, os, random, subprocess, sys, urllib.parse
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


def cta_card(d, spec, y, fill):
    """Question finale facultative (champ "cta", 60 caractères max) qui invite à commenter."""
    q = spec.get("cta")
    if q:
        text_block(d, 0, y, q, serif(64, italic=False), W - 160, fill, 80, 3, anchor_center=True)


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
    if d.textlength(spec.get("dateline", spec.get("big", "")).upper(), font=mono(34)) < W - 120 - d.textlength("ÉDITION SPÉCIALE", font=mono(34)) - 40:
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
        cta_card(d, spec, 360, INK)
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
        cta_card(d, spec, 420, YELLOW)
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
            im = Image.blend(Image.new("RGB", (W, H), (8, 8, 10)), im, 0.45 + 0.3 * min(1, lt / 1.0))
            d = ImageDraw.Draw(im)
        a = 0.85 + 0.15 * ease(lt / 0.4)  # titre lisible dès la 1re image (accroche à 0 s)
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
        cta_card(d, spec, 460, YELLOW)
        d.text((W // 2, 800), "L'HISTOIRE COMPLÈTE", font=head(120), fill=(240, 240, 240), anchor="mm")
        d.text((W // 2, 920), "lien en bio", font=serif(60), fill=YELLOW, anchor="mm")
        d.text((W // 2, 1030), "riffsetlegendes.github.io", font=mono(40), fill=(240, 240, 240), anchor="mm")
    return grain(im, 40, int(t * 12))


# ---------- format 4 : récit narré (format viral : voix off, photos plein écran, sous-titres mot à mot) ----------
RECIT_VOICE = "fr-FR-HenriNeural"


def _tts_sentence(text, voice, rate):
    """Synthèse d'une phrase avec edge-tts : (octets mp3, [(mot, début_s, fin_s)])."""
    import asyncio
    import edge_tts

    async def run():
        try:
            com = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
        except TypeError:
            com = edge_tts.Communicate(text, voice, rate=rate)
        audio, words = b"", []
        async for ch in com.stream():
            if ch["type"] == "audio":
                audio += ch["data"]
            elif ch["type"] == "WordBoundary":
                st = ch["offset"] / 1e7
                words.append((ch["text"], st, st + ch["duration"] / 1e7))
        return audio, words
    return asyncio.run(run())


def _probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def build_narration(spec, out):
    """Voix off phrase par phrase. Renvoie (chemin audio, phrases [{start, end, photo, words[(mot, t0, t1)]}], durée)."""
    voice, rate, gap = spec.get("voice", RECIT_VOICE), spec.get("rate", "+8%"), 0.18
    parts, sents, t = [], [], 0.25
    allow_silent = os.environ.get("RECIT_ALLOW_SILENT") == "1"
    for i, item in enumerate(spec["narration"]):
        text = item["text"].strip()
        try:
            audio, words = _tts_sentence(text, voice, rate)
            seg = out / f"voice_{i}.mp3"
            seg.write_bytes(audio)
            dur = _probe(seg)
        except Exception as ex:
            if not allow_silent:
                raise RuntimeError(f"voix off indisponible : {ex}")
            print("voix off indisponible, aperçu muet :", ex, file=sys.stderr)
            toks = text.split()
            dur, words, seg = 0.34 * len(toks) + 0.3, [], None
            for k, w in enumerate(toks):
                words.append((w, 0.34 * k, 0.34 * (k + 1)))
        if not words:
            toks = text.split()
            words = [(w, dur * k / len(toks), dur * (k + 1) / len(toks)) for k, w in enumerate(toks)]
        sents.append({"start": t, "end": t + dur, "photo": item.get("photo", i),
                      "words": [(w, t + a, t + b) for w, a, b in words]})
        parts.append((seg, dur))
        t += dur + gap
    total = t + 0.9
    voice_path = out / "voice.m4a"
    if all(p for p, _ in parts):
        inputs, filt = [], []
        for k, (p, d) in enumerate(parts):
            inputs += ["-i", str(p)]
            filt.append(f"[{k}:a]aresample=44100,adelay={int((sents[k]['start']) * 1000)}|{int((sents[k]['start']) * 1000)}[a{k}]")
        mix = "".join(f"[a{k}]" for k in range(len(parts)))
        filt.append(f"{mix}amix=inputs={len(parts)}:normalize=0,apad,atrim=0:{total:.2f},loudnorm=I=-14:TP=-1.5[v]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt),
                        "-map", "[v]", "-c:a", "aac", "-b:a", "192k", str(voice_path)], check=True)
    else:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                        "-t", f"{total:.2f}", "-c:a", "aac", str(voice_path)], check=True)
    return voice_path, sents, total


def _speech_regions(path, total):
    """Plages où la voix parle (hors silences), via silencedetect."""
    err = subprocess.run(["ffmpeg", "-i", str(path), "-af", "silencedetect=n=-38dB:d=0.18", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    regs, cur = [], 0.0
    for line in err.splitlines():
        if "silence_start" in line:
            st = float(line.split("silence_start:")[1].split()[0])
            if st - cur > 0.05:
                regs.append((cur, st))
        elif "silence_end" in line:
            cur = float(line.split("silence_end:")[1].split("|")[0])
    if total - cur > 0.05:
        regs.append((cur, total))
    return regs or [(0, total)]


def narration_from_file(spec, out):
    """Voix off fournie (fichier audio enregistré ou généré avec intention de jeu, ex. Gemini TTS).
    Les mots sont répartis sur les plages parlées au prorata de leur longueur (les pauses suspendent les sous-titres)."""
    src = ROOT / spec["voice_file"]
    tempo = float(spec.get("voice_tempo", 1.0))
    voice = out / "voice_src.wav"
    af = f"atempo={tempo}," if abs(tempo - 1) > 0.001 else ""
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-af",
                    af + "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                    "-ar", "44100", "-ac", "1", str(voice)], check=True)
    dur = _probe(voice)
    lead = 0.15
    regs = [(a + lead, b + lead) for a, b in _speech_regions(voice, dur)]
    items = spec["narration"]
    toks = [(w, i) for i, it in enumerate(items) for w in it["text"].split()]
    weights = [len(w) + 2 for w, _ in toks]
    speech = sum(b - a for a, b in regs)
    unit = speech / sum(weights)
    words, r, pos = [], 0, regs[0][0]
    for (w, i), wt in zip(toks, weights):
        need = wt * unit
        start = pos
        while need > 1e-6:
            a, b = regs[r]
            room = b - pos
            if need <= room or r == len(regs) - 1:
                pos += need; need = 0
            else:
                need -= room; r += 1; pos = regs[r][0]
                if start >= b - 0.02:
                    start = pos
        words.append((w, i, start, pos))
    sents = []
    for i, it in enumerate(items):
        ws = [(w, a, b) for w, k, a, b in words if k == i]
        sents.append({"start": ws[0][1] if ws else 0, "end": ws[-1][2] if ws else 0, "photo": it.get("photo", i), "words": ws})
    total = dur + lead + 0.9
    voice_path = out / "voice.m4a"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(voice), "-af",
                    f"adelay={int(lead*1000)},loudnorm=I=-14:TP=-1.5,apad,atrim=0:{total + RECIT_OUTRO:.2f}",
                    "-c:a", "aac", "-b:a", "192k", str(voice_path)], check=True)
    return voice_path, sents, total


def add_bed(spec, voice_path, out, total):
    """Aperçu seulement ("preview_bed": true) : musique libre sous la voix pour juger le mixage.
    À la publication, le vrai morceau est posé par Instagram (audioVolume ~25, videoVolume 100)."""
    title, filename = pick_music(spec, 7)
    mp3 = out / "bed.mp3"
    mp3.write_bytes(fetch("https://incompetech.com/music/royalty-free/mp3-royaltyfree/" + urllib.parse.quote(filename)))
    mixed = out / "voice_bed.m4a"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(voice_path), "-ss", "3", "-i", str(mp3), "-filter_complex",
                    f"[1:a]volume=0.16,afade=t=out:st={total + RECIT_OUTRO - 1.5:.2f}:d=1.5[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]",
                    "-map", "[a]", "-c:a", "aac", "-b:a", "192k", str(mixed)], check=True)
    return mixed


def _chunks(words, maxw=3, maxc=20):
    """Regroupe les mots en sous-titres courts (3 mots max), façon Reels."""
    merged = []
    for w in words:  # « ? », « ! », « : » isolés restent collés au mot précédent
        if merged and not any(ch.isalnum() for ch in w[0]):
            pw, a, b = merged[-1]
            merged[-1] = (pw + w[0], a, max(b, w[2]))
        else:
            merged.append(w)
    words = merged
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= maxw or len(" ".join(x[0] for x in cur + [w])) > maxc or cur[-1][0][-1:] in ".,:;?!"):
            out.append(cur); cur = []
        cur.append(w)
    return out + ([cur] if cur else [])


def recit_photos(spec):
    names = spec.get("photos") or []
    out = []
    for n in names:
        try:
            url = n if n.startswith(("http", "file:")) else "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(n) + "?width=1600"
            out.append(Image.open(io.BytesIO(fetch(url))).convert("RGB"))
        except Exception as ex:
            print("photo indisponible :", n, ex, file=sys.stderr)
    return out


def grade(img):
    """Couleurs légèrement désaturées et contrastées, look documentaire."""
    from PIL import ImageEnhance
    img = ImageEnhance.Color(img).enhance(0.75)
    return ImageEnhance.Contrast(img).enhance(1.12)


RECIT_OUTRO = 2.6
_LOGO = {}


def outro_recit(t, pics, sents, total):
    """Fin : dernière photo floutée, logo Riffs & Légendes qui arrive, adresse du site."""
    u = (t - total) / RECIT_OUTRO
    p = pics[sents[-1]["photo"] % len(pics)]
    bg = cover_fit(p, W, H, 1.18).filter(ImageFilter.GaussianBlur(18))
    im = Image.blend(bg, Image.new("RGB", (W, H), (8, 10, 30)), 0.62)
    if "img" not in _LOGO:
        _LOGO["img"] = Image.open(ROOT / "brand" / "wordmark-video.png").convert("RGBA")
    a = ease(min(1, u / 0.35))
    lw = int((W - 120) * (0.9 + 0.1 * a))
    logo = _LOGO["img"].resize((lw, int(_LOGO["img"].height * lw / _LOGO["img"].width)), Image.LANCZOS)
    if a < 1:
        logo.putalpha(logo.getchannel("A").point(lambda v: int(v * a)))
    im.paste(logo, ((W - lw) // 2, 760 - logo.height // 2), logo)
    d = ImageDraw.Draw(im)
    b = ease(min(1, max(0, (u - 0.25) / 0.3)))
    if b > 0:
        col = tuple(int(c * b) for c in (240, 240, 240))
        d.text((W // 2, 1000), "L'histoire complète", font=serif(64), fill=tuple(int(c * b) for c in YELLOW), anchor="mm")
        d.text((W // 2, 1090), "riffsetlegendes.github.io", font=mono(46), fill=col, anchor="mm")
        d.text((W // 2, 1160), "lien en bio", font=mono(34), fill=col, anchor="mm")
    return im


def frame_recit(t, spec, pics, sents, chunks, total):
    if t >= total:
        return outro_recit(t, pics, sents, total)
    im = Image.new("RGB", (W, H), (10, 10, 12))
    # phrase courante
    k = 0
    for i, s in enumerate(sents):
        if t >= s["start"] - 0.05:
            k = i
    s = sents[k]
    if pics:
        p = pics[s["photo"] % len(pics)]
        span = max(0.1, (sents[k + 1]["start"] if k + 1 < len(sents) else total) - s["start"])
        u = min(1, max(0, (t - s["start"]) / span))
        zin = k % 2 == 0
        z = 1.04 + 0.12 * (u if zin else 1 - u)
        ph = cover_fit(p, W, H, z, 0.35 + 0.1 * (k % 3) / 2, 0.5)
        im.paste(ph, (0, 0))
        if k > 0 and t - s["start"] < 0.25:  # fondu court entre deux photos
            q = pics[sents[k - 1]["photo"] % len(pics)]
            prev = cover_fit(q, W, H, 1.16 if (k - 1) % 2 == 0 else 1.04)
            im = Image.blend(prev, im, max(0, (t - s["start"]) / 0.25))
    # dégradés haut et bas pour la lisibilité
    shade = Image.new("L", (1, H))
    for y in range(H):
        a = 0
        if y > H * 0.48:
            a = int(205 * min(1, (y - H * 0.48) / (H * 0.32)))
        if y < 420:
            a = max(a, int(150 * (1 - y / 420)))
        shade.putpixel((0, y), a)
    im = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), im, shade.resize((W, H)))
    d = ImageDraw.Draw(im)
    # titre fixe en haut (contexte pour qui arrive en cours de vidéo)
    if spec.get("title"):
        f = head(64)
        lines = wrap(d, spec["title"].upper(), f, W - 160)[:2]
        y = 150
        for l in lines:
            tw = d.textlength(l, font=f)
            d.rectangle((W / 2 - tw / 2 - 22, y - 6, W / 2 + tw / 2 + 22, y + 70), fill=YELLOW)
            d.text((W // 2, y), l, font=f, fill=(15, 15, 15), anchor="ma")
            y += 82
    # sous-titre mot à mot
    cur = None
    for c in chunks:
        if c[0][1] - 0.05 <= t <= c[-1][2] + 0.25:
            cur = c
    if cur:
        pop = ease((t - cur[0][1]) / 0.12)
        size = int(118 * (0.86 + 0.14 * pop))
        f = head(size)
        words = [w for w, _, _ in cur]
        full = " ".join(words).upper()
        lines = wrap(d, full, f, W - 140)
        y = 1240 - (len(lines) - 1) * size // 2
        idx = 0
        for line in lines:
            toks = line.split(" ")
            lw = d.textlength(line, font=f)
            x = W / 2 - lw / 2
            for tok in toks:
                if idx >= len(cur):
                    break
                w, a, b = cur[idx]
                lit = max([j for j, (_, a2, _) in enumerate(cur) if a2 - 0.02 <= t] or [0])  # un seul mot allumé
                col = YELLOW if idx == lit else (255, 255, 255)
                d.text((x, y), tok, font=f, fill=col, stroke_width=9, stroke_fill=(0, 0, 0))
                x += d.textlength(tok + " ", font=f)
                idx += 1
            y += int(size * 0.98)
    # signature
    d.text((W // 2, H - 150), "@riffsetlegendes", font=mono(34), fill=(235, 235, 235), anchor="mm")
    return im


def main_recit(spec_path, spec):
    out = ROOT / "out" / "instagram" / spec_path.stem
    out.mkdir(parents=True, exist_ok=True)
    voice, sents, total = narration_from_file(spec, out) if spec.get("voice_file") else build_narration(spec, out)
    if spec.get("preview_bed"):
        voice = add_bed(spec, voice, out, total)
    chunks = [c for s in sents for c in _chunks(s["words"])]  # jamais de sous-titre à cheval sur deux phrases
    pics = [grade(p) for p in recit_photos(spec)] or [Image.new("RGB", (W, H), (30, 30, 34))]
    credit = spec.get("photo_credit")
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-i", str(voice), "-t", f"{total + RECIT_OUTRO:.2f}", "-map", "0:v", "-map", "1:a",
                             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "21", "-maxrate", "9M",
                             "-bufsize", "18M", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out / "reel.mp4")],
                            stdin=subprocess.PIPE)
    for i in range(int((total + RECIT_OUTRO) * FPS)):
        im = frame_recit(i / FPS, spec, pics, sents, chunks, total)
        if credit:
            ImageDraw.Draw(im).text((W // 2, 14), credit, font=mono(20), fill=(170, 170, 170), anchor="mt")
        proc.stdin.write(im.tobytes())
    proc.stdin.close()
    proc.wait()
    (out / "reel_credit.txt").write_text("", encoding="utf-8")
    (out / "narration.json").write_text(json.dumps(
        [{"start": round(s["start"], 2), "end": round(s["end"], 2), "text": " ".join(w for w, _, _ in s["words"])} for s in sents],
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(out / "reel.mp4", f"{total:.1f}s", "recit")


STYLES = {"journal": (frame_journal, 3.2, 4.0, 3.0),
          "countdown": (frame_countdown, 3.0, 4.2, 2.8),
          "docu": (frame_docu, 3.6, 4.6, 3.2)}


def main():
    spec_path = Path(sys.argv[1])
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    fmt = spec.get("format", "countdown")
    if fmt == "recit":
        return main_recit(spec_path, spec)
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
    credit = spec.get("photo_credit")

    def draw_c(t):
        im = draw(t, spec, pics, segs).convert("RGB")
        if credit:
            ImageDraw.Draw(im).text((W // 2, 14), credit, font=mono(20), fill=(170, 170, 170), anchor="mt")
        return im
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", *audio, "-t", f"{dur:.2f}", *afilter, "-map", "0:v", "-map", "1:a",
                             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "27" if fmt == "docu" else "22", "-maxrate", "8M", "-bufsize", "16M",
                             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out / "reel.mp4")], stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)):
        proc.stdin.write(draw_c(i / FPS).tobytes())
    proc.stdin.close()
    proc.wait()
    print(out / "reel.mp4", f"{dur:.1f}s", fmt)


if __name__ == "__main__":
    main()
