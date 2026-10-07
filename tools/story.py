"""Story Instagram 1080x1920 à partir de la couverture d'un carrousel (01.png)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "tools" / "fonts"
NAVY, YELLOW, PAPER, BLUE = (21, 27, 94), (245, 191, 29), (241, 241, 235), (37, 54, 208)


def head(size, wght=900):
    f = ImageFont.truetype(str(F / "BigShouldersDisplay.ttf"), size)
    try:
        f.set_variation_by_axes([wght])
    except Exception:
        pass
    return f


def mono(size):
    return ImageFont.truetype(str(F / "DMMono-Medium.ttf"), size)


def make(folder, kind):
    folder = Path(folder)
    cover = Image.open(folder / "01.png").convert("RGB")
    W, H = 1080, 1920
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    # sillons discrets en fond
    for r in range(260, 1500, 14):
        d.ellipse((W - 120 - r, 1500 - r, W - 120 + r, 1500 + r), outline=(30, 37, 112), width=2)
    # en-tête
    label = "CE JOUR-LÀ" if kind == "jour" else "LE FOCUS DU SOIR"
    d.text((80, 150), "NOUVEAU POST", font=mono(34), fill=YELLOW)
    d.text((80, 196), label, font=head(120), fill=PAPER)
    # couverture du carrousel avec ombre
    cw = 880
    ch = round(cover.height * cw / cover.width)
    c = cover.resize((cw, ch), Image.LANCZOS)
    x, y = (W - cw) // 2, 400
    sh = Image.new("RGBA", (cw + 120, ch + 120), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((60, 80, cw + 60, ch + 60), fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(28))
    im.paste(sh, (x - 60, y - 60), sh)
    im.paste(c, (x, y))
    # pied
    by = y + ch + 90
    d.rounded_rectangle((80, by, W - 80, by + 150), radius=75, fill=YELLOW)
    t = "À VOIR SUR LE COMPTE"
    f = head(78)
    tw = d.textlength(t, font=f)
    d.text(((W - tw) / 2, by + 30), t, font=f, fill=NAVY)
    s = "L'histoire complète : riffsetlegendes.github.io"
    fm = mono(30)
    d.text(((W - d.textlength(s, font=fm)) / 2, by + 200), s, font=fm, fill=PAPER)
    out = folder / "story"
    out.mkdir(exist_ok=True)
    im.save(out / "story.png")
    return out


if __name__ == "__main__":
    print(make(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "jour"))
