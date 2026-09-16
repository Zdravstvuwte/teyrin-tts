# -*- coding: utf-8 -*-
"""Стоячие фигурки, жетон и плитка перехода.

Подписей на картинках нет: миниатюра должна помещаться в гекс, а имя видно
в тултипе при наведении. Всё рисуется в 4x и уменьшается — края чистые.
"""
import io, math, os, random

import paths
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
S = 4
random.seed(7)


def canvas(w, h, bg=(0, 0, 0, 0)):
    img = Image.new("RGBA", (w * S, h * S), bg)
    return img, ImageDraw.Draw(img, "RGBA")


def done(img, w, h, key):
    img = img.resize((w, h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    stored = paths.store(key, buf.getvalue())
    print("%-36s %dx%d" % (stored, img.size[0], img.size[1]))
    return img


def s(*vals):
    return [v * S for v in vals]


# ==================================================================== фигурки
def standee(w, h, draw_fn):
    img, d = canvas(w, h)
    draw_fn(d, img, w, h)
    return img


def d_player(d, img, w, h):
    C, O = (54, 122, 168), (22, 58, 88)
    d.line(s(w * 0.74, h * 0.10, w * 0.30, h * 0.92), fill=(126, 92, 52, 255), width=int(w * 0.04 * S))
    d.polygon([(w * 0.76 * S, h * 0.03 * S), (w * 0.67 * S, h * 0.17 * S), (w * 0.81 * S, h * 0.16 * S)],
              fill=(206, 210, 214, 255), outline=(90, 96, 100, 255), width=int(3 * S))
    d.ellipse(s(w * 0.37, h * 0.15, w * 0.63, h * 0.34), fill=C + (255,), outline=O + (255,), width=int(5 * S))
    d.polygon([(w * 0.32 * S, h * 0.62 * S), (w * 0.39 * S, h * 0.34 * S), (w * 0.61 * S, h * 0.34 * S),
               (w * 0.68 * S, h * 0.62 * S)], fill=C + (255,), outline=O + (255,), width=int(5 * S))
    d.line(s(w * 0.41, h * 0.40, w * 0.28, h * 0.62), fill=C + (255,), width=int(w * 0.08 * S))
    d.line(s(w * 0.59, h * 0.40, w * 0.68, h * 0.57), fill=C + (255,), width=int(w * 0.08 * S))
    d.line(s(w * 0.44, h * 0.62, w * 0.39, h * 0.95), fill=O + (255,), width=int(w * 0.10 * S))
    d.line(s(w * 0.56, h * 0.62, w * 0.61, h * 0.95), fill=O + (255,), width=int(w * 0.10 * S))


def d_npc(d, img, w, h):
    C, O = (74, 112, 88), (36, 62, 48)
    d.line(s(w * 0.28, h * 0.12, w * 0.31, h * 0.95), fill=(110, 82, 46, 255), width=int(w * 0.035 * S))
    d.ellipse(s(w * 0.60, h * 0.36, w * 0.88, h * 0.64), fill=(122, 92, 56, 255),
              outline=(70, 52, 30, 255), width=int(5 * S))
    d.ellipse(s(w * 0.39, h * 0.15, w * 0.63, h * 0.34), fill=C + (255,), outline=O + (255,), width=int(5 * S))
    d.polygon([(w * 0.34 * S, h * 0.64 * S), (w * 0.40 * S, h * 0.34 * S), (w * 0.62 * S, h * 0.34 * S),
               (w * 0.68 * S, h * 0.64 * S)], fill=C + (255,), outline=O + (255,), width=int(5 * S))
    d.line(s(w * 0.42, h * 0.40, w * 0.29, h * 0.53), fill=C + (255,), width=int(w * 0.075 * S))
    d.line(s(w * 0.45, h * 0.64, w * 0.41, h * 0.95), fill=O + (255,), width=int(w * 0.095 * S))
    d.line(s(w * 0.58, h * 0.64, w * 0.62, h * 0.95), fill=O + (255,), width=int(w * 0.095 * S))


def d_crab(d, img, w, h):
    C, O = (198, 74, 44), (118, 36, 20)
    for sgn in (-1, 1):
        for i in range(3):
            y = h * (0.54 + i * 0.13)
            d.line([(w * (0.5 + sgn * 0.14)) * S, y * S, (w * (0.5 + sgn * 0.45)) * S, (y + h * 0.16) * S],
                   fill=O + (255,), width=int(w * 0.05 * S))
    for sgn in (-1, 1):
        cx = w * (0.5 + sgn * 0.33)
        d.line([(w * (0.5 + sgn * 0.16)) * S, h * 0.48 * S, cx * S, h * 0.32 * S],
               fill=O + (255,), width=int(w * 0.06 * S))
        d.polygon([(cx * S, h * 0.38 * S), ((cx + sgn * w * 0.16) * S, h * 0.19 * S),
                   ((cx + sgn * w * 0.04) * S, h * 0.10 * S), ((cx - sgn * w * 0.05) * S, h * 0.27 * S)],
                  fill=C + (255,), outline=O + (255,), width=int(4 * S))
    d.ellipse(s(w * 0.24, h * 0.34, w * 0.76, h * 0.74), fill=C + (255,), outline=O + (255,), width=int(6 * S))
    for sgn in (-1, 1):
        ex = w * (0.5 + sgn * 0.12)
        d.line([ex * S, h * 0.36 * S, ex * S, h * 0.22 * S], fill=O + (255,), width=int(w * 0.03 * S))
        d.ellipse(s(ex - w * 0.05, h * 0.16, ex + w * 0.05, h * 0.25), fill=(250, 246, 236, 255),
                  outline=O + (255,), width=int(4 * S))
        d.ellipse(s(ex - w * 0.02, h * 0.185, ex + w * 0.02, h * 0.225), fill=(20, 18, 16, 255))


def d_beast(d, img, w, h):
    """Хищник в припадающей стойке: низкий корпус, тяжёлый загривок,
    вытянутый череп с раскрытой пастью, когти и длинный хвост."""
    C, O = (80, 38, 100), (34, 14, 46)
    HI, TOOTH, EYE = (146, 88, 178), (238, 234, 242), (130, 255, 224)

    FAR = (52, 24, 66)

    def P(*pts, fill=C, outline=O, width=5):
        d.polygon([(w * x * S, h * y * S) for x, y in pts],
                  fill=fill + (255,), outline=(outline + (255,)) if outline else None,
                  width=int(width * S))

    def leg(hip, knee, paw, colour, edge, thick, claws=True):
        pts = [(w * x * S, h * y * S) for x, y in (hip, knee, paw)]
        if edge:                                   # тёмная подложка даёт контур
            d.line(pts, fill=edge + (255,), width=int(w * thick * 1.28 * S), joint="curve")
        d.line(pts, fill=colour + (255,), width=int(w * thick * S), joint="curve")
        if claws:
            for i in range(3):
                x0 = paw[0] - 0.030 + i * 0.026
                P((x0, paw[1] - 0.01), (x0 - 0.030, paw[1] + 0.055), (x0 + 0.012, paw[1] + 0.038),
                  fill=TOOTH, outline=O, width=2)

    # хвост: сужается от крупа к кончику, поэтому нарисован полигоном
    P((0.76, 0.44), (0.86, 0.36), (0.95, 0.22), (0.99, 0.09), (0.95, 0.09),
      (0.90, 0.23), (0.83, 0.36), (0.76, 0.54), fill=C)

    # дальняя пара лап — за корпусом, приглушённого цвета
    leg((0.38, 0.58), (0.31, 0.76), (0.39, 0.92), FAR, None, 0.055, claws=False)
    leg((0.74, 0.56), (0.67, 0.76), (0.75, 0.92), FAR, None, 0.055, claws=False)

    # корпус: высокие лопатки, провисшая спина, подобранный живот
    P((0.21, 0.50), (0.27, 0.35), (0.42, 0.39), (0.57, 0.42), (0.68, 0.33), (0.80, 0.43),
      (0.81, 0.58), (0.68, 0.66), (0.44, 0.69), (0.28, 0.65), (0.21, 0.58))

    # гребень: длинные шипы над лопатками, к хвосту сходит на нет
    for x, base, k in [(0.26, 0.37, 0.24), (0.35, 0.39, 0.27), (0.45, 0.40, 0.22),
                       (0.55, 0.42, 0.15), (0.65, 0.36, 0.10)]:
        P((x, base + 0.02), (x + 0.040, base - k), (x + 0.082, base + 0.02),
          fill=HI, outline=O, width=3)

    # ближняя пара лап
    leg((0.33, 0.60), (0.25, 0.78), (0.33, 0.92), C, O, 0.075)
    leg((0.70, 0.58), (0.61, 0.78), (0.70, 0.92), C, O, 0.075)

    # шея от лопаток вперёд-вниз к черепу
    P((0.28, 0.40), (0.19, 0.47), (0.14, 0.60), (0.22, 0.64), (0.29, 0.60))

    # череп с раскрытой пастью
    P((0.23, 0.44), (0.11, 0.42), (0.01, 0.50), (0.02, 0.58), (0.21, 0.60))   # верхняя челюсть
    P((0.21, 0.63), (0.09, 0.74), (0.03, 0.71), (0.12, 0.62), (0.22, 0.60))   # нижняя челюсть
    for i in range(5):                                                        # клыки
        x = 0.035 + i * 0.035
        P((x, 0.575), (x + 0.016, 0.578), (x + 0.008, 0.632), fill=TOOTH, outline=TOOTH, width=1)
    for i in range(4):
        x = 0.055 + i * 0.035
        y = 0.700 - i * 0.024
        P((x, y), (x + 0.016, y - 0.004), (x + 0.008, y - 0.052), fill=TOOTH, outline=TOOTH, width=1)

    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))                          # свечение глаз
    gd = ImageDraw.Draw(glow)
    for ex, ey in [(0.10, 0.495), (0.165, 0.480)]:
        gd.ellipse(s(w * ex - w * 0.055, h * ey - h * 0.06, w * ex + w * 0.055, h * ey + h * 0.06),
                   fill=EYE + (140,))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(int(w * 0.028 * S))))
    for ex, ey in [(0.075, 0.482), (0.140, 0.468)]:
        d.polygon([(w * ex * S, h * ey * S), (w * (ex + 0.055) * S, h * (ey + 0.014) * S),
                   (w * (ex + 0.014) * S, h * (ey + 0.046) * S)], fill=EYE + (255,))


def d_palm(d, img, w, h):
    TR, LF = (122, 88, 52), (46, 132, 62)
    d.line([(w * 0.52) * S, h * 0.96 * S, (w * 0.45) * S, h * 0.56 * S, (w * 0.40) * S, h * 0.28 * S],
           fill=TR + (255,), width=int(w * 0.095 * S), joint="curve")
    for i in range(7):
        a = math.radians(-176 + i * 27)
        tipx, tipy = w * 0.40 + math.cos(a) * w * 0.45, h * 0.28 + math.sin(a) * h * 0.24
        midx, midy = (w * 0.40 + tipx) / 2, (h * 0.28 + tipy) / 2 - h * 0.10
        d.polygon([(w * 0.40 * S, h * 0.28 * S), (midx * S, midy * S), (tipx * S, tipy * S),
                   (midx * S, (midy + h * 0.08) * S)], fill=LF + (255,),
                  outline=(24, 84, 40, 255), width=int(4 * S))
    for dx, dy in [(-0.055, 0.05), (0.035, 0.045), (-0.01, 0.105)]:
        cx, cy = w * (0.40 + dx), h * (0.32 + dy)
        d.ellipse(s(cx - w * 0.055, cy - w * 0.055, cx + w * 0.055, cy + w * 0.055),
                  fill=(96, 66, 38, 255), outline=(56, 38, 20, 255), width=int(4 * S))


# ====================================================================== жетон
def firestone(w=512, h=512):
    img, d = canvas(w, h)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse(s(40, 40, w - 40, h - 40), fill=(255, 110, 30, 150))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(22 * S)))
    d.ellipse(s(34, 34, w - 34, h - 34), fill=(58, 44, 40, 255), outline=(198, 90, 30, 255), width=int(10 * S))
    cx, cy, r = w / 2, h / 2, w * 0.27
    pts = [(cx + math.cos(math.radians(-90 + i * 60)) * r * (1.0 if i % 2 == 0 else 0.78),
            cy + math.sin(math.radians(-90 + i * 60)) * r * (1.0 if i % 2 == 0 else 0.78)) for i in range(6)]
    d.polygon([(x * S, y * S) for x, y in pts], fill=(255, 146, 40, 255),
              outline=(255, 226, 150, 255), width=int(7 * S))
    d.polygon([((cx + (x - cx) * 0.45) * S, (cy + (y - cy) * 0.45) * S) for x, y in pts],
              fill=(255, 232, 168, 255))
    for i in range(10):
        a = math.radians(i * 36 + 12)
        d.line([(cx + math.cos(a) * r * 1.25) * S, (cy + math.sin(a) * r * 1.25) * S,
                (cx + math.cos(a) * r * 1.62) * S, (cy + math.sin(a) * r * 1.62) * S],
               fill=(255, 150, 50, 200), width=int(6 * S))
    return done(img, w, h, "tok_firestone")


# =================================================================== переход
def transition(w=300, h=600):
    """Стрелка вертикальная: поле старта лежит ниже острова, и переход ведёт
    снизу вверх. Рисуем сразу в нужную сторону, чтобы не крутить плитку —
    у повёрнутого Custom Tile габарит по X перестаёт быть шириной картинки,
    и подгонка размера начинает мерить не то."""
    img, d = canvas(w, h)
    d.rounded_rectangle(s(8, 8, w - 8, h - 8), radius=int(46 * S),
                        fill=(30, 28, 26, 235), outline=(214, 190, 130, 255), width=int(7 * S))
    d.polygon([(w * 0.38 * S, h * 0.80 * S), (w * 0.62 * S, h * 0.80 * S),
               (w * 0.62 * S, h * 0.38 * S), (w * 0.82 * S, h * 0.38 * S),
               (w * 0.50 * S, h * 0.16 * S), (w * 0.18 * S, h * 0.38 * S),
               (w * 0.38 * S, h * 0.38 * S)], fill=(214, 190, 130, 255))
    return done(img, w, h, "transition")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    firestone()
    transition()
    # зверь — низкий и длинный, поэтому холст у него шире остальных
    for fn, fname, size in [(d_player, "fig_player", (560, 700)),
                            (d_npc, "fig_npc", (560, 700)),
                            (d_crab, "fig_crab", (560, 700)),
                            (d_beast, "fig_beast", (760, 540)),
                            (d_palm, "fig_palm", (560, 700))]:
        done(standee(size[0], size[1], fn), size[0], size[1], fname)
