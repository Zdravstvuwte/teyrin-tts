# -*- coding: utf-8 -*-
"""Листы карт для Tabletop Simulator, собираются из cards.xlsx.
Вёрстка повторяет скрипты nanDECK (face.txt / back.txt): 6.3 x 8.8 см,
белая карта, чёрная графика, две половины через 180° у карт действий."""
import io, os, openpyxl

import paths
from PIL import Image, ImageDraw, ImageFont

SYM   = os.path.join(paths.CARDS, "Карты действий", "symbols")   # иконки классов
PPCM  = 70                      # render resolution
CW, CH = 6.3, 8.8               # card size in cm
W, H  = int(CW * PPCM), int(CH * PPCM)
HALF  = 4.15                    # each rotated half occupies 0..4.15 cm

ARIAL   = r"C:\Windows\Fonts\arial.ttf"
ARIALBD = r"C:\Windows\Fonts\arialbd.ttf"

def cm(v):  return int(round(v * PPCM))
def font(path, pt): return ImageFont.truetype(path, max(6, int(round(pt * PPCM / 28.35))))

SYMBOLS = {}
for key, fn in [("1","spear_full"),("A","spear_empty"),("2","shield_full"),("B","shield_empty"),
                ("3","focus_full"),("C","focus_empty"),("4","pain_full"),("D","pain_empty"),
                ("5","legend_full"),("E","legend_empty")]:
    SYMBOLS[key] = Image.open(os.path.join(SYM, fn + ".png")).convert("RGBA")

def rounded(d, x, y, w, h, r, width=0.04, fill=None):
    d.rounded_rectangle([cm(x), cm(y), cm(x + w), cm(y + h)], radius=cm(r),
                        outline=(0, 0, 0, 255), width=max(1, cm(width)), fill=fill)

def ellipse(d, x, y, w, h, width=0.1, fill=None):
    d.ellipse([cm(x), cm(y), cm(x + w), cm(y + h)], outline=(0, 0, 0, 255),
              width=max(1, cm(width)), fill=fill)

def wrap(draw, text, fnt, maxw):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur); cur = word
    if cur: lines.append(cur)
    return lines

def fit_text(img, text, x, y, w, h, fpath, pt, ):
    """Centered, word-wrapped, shrink-to-fit (nanDECK flag F)."""
    if not text: return
    d = ImageDraw.Draw(img)
    bx, by, bw, bh = cm(x), cm(y), cm(w), cm(h)
    size = pt
    while True:
        fnt = font(fpath, size)
        lines = wrap(d, text, fnt, bw)
        lh = int(fnt.size * 1.18)
        if size <= 4:
            break
        if len(lines) * lh <= bh and all(d.textlength(l, font=fnt) <= bw for l in lines):
            break
        size -= 0.5
    ty = by + (bh - len(lines) * lh) // 2
    for line in lines:
        d.text((bx + (bw - d.textlength(line, font=fnt)) / 2, ty), line,
               font=fnt, fill=(0, 0, 0, 255))
        ty += lh

def centered(img, text, x, y, w, h, fpath, pt):
    if text == "" or text is None: return
    d = ImageDraw.Draw(img)
    fnt = font(fpath, pt)
    bx, by, bw, bh = cm(x), cm(y), cm(w), cm(h)
    tw = d.textlength(text, font=fnt)
    asc, desc = fnt.getmetrics()
    d.text((bx + (bw - tw) / 2, by + (bh - (asc + desc)) / 2), text, font=fnt, fill=(0, 0, 0, 255))

def icons(img, classes, x, y, iw, ih, count=5):
    """Row of class symbols, spread across the given width."""
    if not classes: return
    for i, ch in enumerate(classes[:count]):
        s = SYMBOLS.get(ch)
        if s is None: continue
        s = s.resize((cm(iw), cm(ih)), Image.LANCZOS)
        img.alpha_composite(s, (cm(x + i * iw), cm(y)))

# ---------------------------------------------------------------- action cards
def action_half(name, ap, stam, cls, effect):
    img = Image.new("RGBA", (W, cm(HALF)), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    rounded(d, 2.35, 0.40, 3.65, 0.85, 0.10, 0.04)            # name plate
    fit_text(img, name, 2.40, 0.48, 3.55, 0.72, ARIALBD, 11)
    ellipse(d, 0.40, 0.40, 0.85, 0.85, 0.10, (255, 255, 255, 255))   # action points
    centered(img, ap, 0.40, 0.40, 0.85, 0.85, ARIALBD, 20)
    rounded(d, 1.35, 0.42, 0.80, 0.80, 0.16, 0.10, (255, 255, 255, 255))  # stamina
    centered(img, stam, 1.35, 0.42, 0.80, 0.80, ARIALBD, 18)
    rounded(d, 0.30, 1.35, 5.70, 0.50, 0.06, 0.035)           # class strip
    icons(img, cls, 1.35, 1.38, 0.72, 0.44)
    rounded(d, 0.30, 1.85, 5.70, 2.25, 0.06, 0.035)           # effect box
    fit_text(img, effect, 0.45, 1.95, 5.40, 2.05, ARIAL, 11)
    return img

def action_back_half(cls):
    """Large class cluster: spear TL, shield TR, legend C, focus BL, pain BR."""
    img = Image.new("RGBA", (W, cm(HALF)), (255, 255, 255, 0))
    if not cls: return img
    slots = [(0, 1.55, 0.90), (1, 3.30, 0.90), (4, 2.425, 1.75), (2, 1.55, 2.60), (3, 3.30, 2.60)]
    for idx, x, y in slots:
        if idx >= len(cls): continue
        s = SYMBOLS.get(cls[idx])
        if s is None: continue
        img.alpha_composite(s.resize((cm(1.45), cm(1.45)), Image.LANCZOS), (cm(x), cm(y)))
    return img

def blank_card():
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(img)
    rounded(d, 0.12, 0.12, 6.06, 8.56, 0.28, 0.06)
    return img

def action_face(c):
    img = blank_card()
    img.alpha_composite(action_half(c["t_name"], c["t_ap"], c["t_stam"], c["t_class"], c["t_effect"]), (0, 0))
    if c["b_name"] or c["b_effect"]:
        bot = action_half(c["b_name"], c["b_ap"], c["b_stam"], c["b_class"], c["b_effect"]).rotate(180)
        img.alpha_composite(bot, (0, H - cm(HALF)))
    d = ImageDraw.Draw(img)
    rounded(d, 0.30, 4.15, 5.70, 0.50, 0.06, 0.035)           # shared affiliation
    fit_text(img, c["affil"], 0.40, 4.22, 5.50, 0.36, ARIAL, 11)
    return img

def action_back(c):
    img = blank_card()
    d = ImageDraw.Draw(img)
    d.line([cm(0.30), cm(4.40), cm(6.00), cm(4.40)], fill=(0, 0, 0, 255), width=max(1, cm(0.05)))
    img.alpha_composite(action_back_half(c["t_class"]), (0, 0))
    if c["b_class"]:
        img.alpha_composite(action_back_half(c["b_class"]).rotate(180), (0, H - cm(HALF)))
    return img

# ------------------------------------------------------------------ gear cards
def gear_face(c):
    img = blank_card()
    d = ImageDraw.Draw(img)
    lw = max(1, cm(0.045))
    d.line([cm(0.12), cm(0.95), cm(6.18), cm(0.95)], fill=(0, 0, 0, 255), width=lw)
    d.line([cm(0.12), cm(7.70), cm(6.18), cm(7.70)], fill=(0, 0, 0, 255), width=lw)
    fit_text(img, c["name"],   0.35, 0.28, 5.60, 0.55, ARIALBD, 15)
    fit_text(img, c["effect"], 0.40, 1.15, 5.50, 6.30, ARIAL, 12)
    fit_text(img, c["tipe"],   0.35, 7.85, 5.60, 0.55, ARIAL, 12)
    return img

def gear_back():
    img = blank_card()
    d = ImageDraw.Draw(img)
    lw = max(1, cm(0.05))
    ellipse(d, 2.65, 0.95, 1.00, 1.00, 0.05)
    for a, b, x, y in [(3.15, 1.95, 3.15, 4.55), (3.15, 2.15, 1.95, 3.65), (3.15, 2.15, 4.35, 3.65),
                       (3.15, 4.55, 2.30, 6.05), (3.15, 4.55, 4.00, 6.05)]:
        d.line([cm(a), cm(b), cm(x), cm(y)], fill=(0, 0, 0, 255), width=lw)
    fit_text(img, "Снаряжение", 0.40, 6.55, 5.50, 1.00, ARIALBD, 22)
    return img

# ----------------------------------------------------------------------- sheets
def read(path, key):
    import scene
    return scene.read_cards(path, key)

def sheet(images, cols, rows, key):
    """Собирает лист и кладёт его через paths.store — с хешем в имени."""
    s = Image.new("RGBA", (W * cols, H * rows), (255, 255, 255, 255))
    for i, im in enumerate(images):
        s.paste(im, ((i % cols) * W, (i // cols) * H))
    buf = io.BytesIO()
    s.convert("RGB").save(buf, "PNG", optimize=True)
    name = paths.store(key, buf.getvalue())
    print("%-42s %dx%d, карт: %d" % (name, s.size[0], s.size[1], len(images)))
    return name

if __name__ == "__main__":
    import scene
    os.makedirs(paths.ASSETS, exist_ok=True)
    # Колоды берутся из scene.DECKS: там всё, что нашлось в папке Карты.
    for d in scene.DECKS:
        cards = read(d["xlsx"], d["name_col"])
        cols, rows = d["sheet"]
        if d["kind"] == "action":
            faces = [action_face(c) for c in cards]
            backs = [action_back(c) for c in cards]
            sheet(faces, cols, rows, d["key"] + "_face")
            sheet(backs, cols, rows, d["key"] + "_back")
        else:                                   # снаряжение: рубашка одна на всех
            sheet([gear_face(c) for c in cards], cols, rows, d["key"] + "_face")
            sheet([gear_back()], 1, 1, d["key"] + "_back")
        print("  %s: %d карт" % (d["nick"], len(cards)))
