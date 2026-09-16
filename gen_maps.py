# -*- coding: utf-8 -*-
"""Карты локаций: каждая поверхность выложена целыми гексами, границы зон
идут строго по рёбрам гексов. Никаких подписей на доске — названия зон живут
в тултипах объектов и в заметке «Правила».
"""
import io, math, os, random
from PIL import Image, ImageDraw

import hexgrid as hg
import paths

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
R   = 120                     # радиус гекса в пикселях итоговой картинки
S   = 2                       # сглаживание: рисуем в 2x и уменьшаем
random.seed(11)

# --------------------------------------------------------------- поверхности
TERRAIN = {
    "water": dict(fill=(30, 92, 138),  edge=(18, 62, 96),   speck=[(255, 255, 255), (14, 68, 110)]),
    "sand":  dict(fill=(214, 188, 130), edge=(162, 134, 80), speck=[(255, 250, 232), (150, 120, 70)]),
    "rock":  dict(fill=(128, 126, 120), edge=(88, 86, 82),   speck=[(78, 78, 78), (196, 196, 196)]),
    "hot":   dict(fill=(110, 48, 38),  edge=(58, 22, 18),   speck=[(178, 78, 36), (52, 22, 18)]),
    "dirt":  dict(fill=(120, 102, 72), edge=(82, 68, 46),   speck=[(88, 74, 50), (166, 146, 106)]),
    "path":  dict(fill=(158, 138, 100), edge=(112, 96, 66),  speck=[(180, 162, 124), (120, 102, 70)]),
}
ZONE_EDGE = (26, 22, 18)      # цвет жирной границы между зонами
EDGES = ["SE", "S", "SW", "NW", "N", "NE"]


def hex_map(cols, rows, terrain_of, props=None, name="map"):
    w, h = hg.image_size(R, cols, rows)
    img = Image.new("RGBA", (w * S, h * S), (44, 36, 29, 255))
    d = ImageDraw.Draw(img, "RGBA")
    r = R * S

    grid = {(c, ro): terrain_of(c, ro) for c in range(cols) for ro in range(rows)}

    for (c, ro), kind in grid.items():
        cx, cy = hg.center_px(r, c, ro)
        t = TERRAIN[kind]
        pts = hg.corners(cx, cy, r)
        d.polygon(pts, fill=t["fill"] + (255,))

        for _ in range(150):                                   # фактура внутри гекса
            a, rad = random.uniform(0, 2 * math.pi), r * 0.86 * math.sqrt(random.random())
            px, py = cx + math.cos(a) * rad, cy + math.sin(a) * rad
            s = random.uniform(0.8, 2.6) * S
            d.ellipse([px - s, py - s, px + s, py + s],
                      fill=random.choice(t["speck"]) + (random.randint(12, 32),))

        if kind == "hot":                                      # трещины и жар
            for _ in range(11):
                a, rad = random.uniform(0, 2 * math.pi), r * 0.7 * math.sqrt(random.random())
                px, py = cx + math.cos(a) * rad, cy + math.sin(a) * rad
                ang, L = random.uniform(0, math.pi), random.uniform(0.06, 0.18) * r
                d.line([px - math.cos(ang) * L, py - math.sin(ang) * L,
                        px + math.cos(ang) * L, py + math.sin(ang) * L],
                       fill=(255, 148, 48, 220), width=int(random.uniform(1.4, 3.0) * S))

        # Контур каждого гекса намеренно НЕ рисуется: сетку на столе рисует
        # сам TTS, а вторая разметка поверх неё только мешает. Зоны читаются
        # цветом, их края — жирной линией ниже.

    for (c, ro), kind in grid.items():                          # жирные границы зон
        cx, cy = hg.center_px(r, c, ro)
        pts = hg.corners(cx, cy, r)
        nb = hg.neighbours(c, ro)
        for i, side in enumerate(EDGES):
            if grid.get(nb[side]) != kind:
                a, b = pts[i], pts[(i + 1) % 6]
                d.line([a, b], fill=ZONE_EDGE + (255,), width=int(5 * S))

    for fn in (props or []):                                    # декор внутри гексов
        fn(d, r)

    img = img.resize((w, h), Image.LANCZOS).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    stored = paths.store(name, buf.getvalue())
    print("%-36s %dx%d, %d гексов" % (stored, img.size[0], img.size[1], cols * rows))
    return img


# ------------------------------------------------------------------- остров
ISL_COLS, ISL_ROWS = 13, 8
WATER_END = [2, 2, 3, 3, 2, 2, 3, 2]        # колонки 0..WATER_END-1 — вода
SAND_END  = [5, 6, 6, 5, 5, 6, 6, 5]        # далее до SAND_END-1 — пляж

# Раскалённая зона по схеме сценария: гексагональный «цветок» — центральный
# гекс с огненным камнем и два кольца вокруг, 1 + 6 + 12 = 19 гексов.
# По колонкам это 3-4-5-4-3.
FIRESTONE = (9, 3)
HOT_RADIUS = 2
HOT = hg.disc(FIRESTONE[0], FIRESTONE[1], HOT_RADIUS, ISL_COLS, ISL_ROWS)


def island_terrain(c, r):
    if (c, r) in HOT:      return "hot"
    if c < WATER_END[r]:   return "water"
    if c < SAND_END[r]:    return "sand"
    return "rock"


# ------------------------------------------------------------- стартовый лагерь
CMP_COLS, CMP_ROWS = 5, 4
CMP_PATH = {(0, 3), (1, 2), (2, 2), (3, 1), (4, 1)}
TENTS = [(0, 1), (4, 0)]
FIRE = (2, 3)


def camp_terrain(c, r):
    return "path" if (c, r) in CMP_PATH else "dirt"


def draw_tent(d, r, c, ro):
    cx, cy = hg.center_px(r, c, ro)
    k = r * 0.52
    d.polygon([(cx, cy - k), (cx - k * 0.9, cy + k * 0.6), (cx + k * 0.9, cy + k * 0.6)],
              fill=(176, 152, 116, 255), outline=(74, 58, 40, 255), width=int(0.05 * r))
    d.polygon([(cx, cy - k), (cx - k * 0.28, cy + k * 0.6), (cx + k * 0.28, cy + k * 0.6)],
              fill=(74, 58, 40, 255))


def draw_fire(d, r, c, ro):
    cx, cy = hg.center_px(r, c, ro)
    k = r * 0.42
    d.ellipse([cx - k, cy - k * 0.5, cx + k, cy + k * 0.5], fill=(58, 50, 40, 255))
    for a in range(8):
        ang = a / 8 * 2 * math.pi
        d.line([cx + math.cos(ang) * k * 0.4, cy + math.sin(ang) * k * 0.22,
                cx + math.cos(ang) * k * 0.95, cy + math.sin(ang) * k * 0.5],
               fill=(96, 72, 46, 255), width=int(0.055 * r))
    d.polygon([(cx, cy - k * 1.15), (cx - k * 0.42, cy + k * 0.2), (cx + k * 0.42, cy + k * 0.2)],
              fill=(240, 148, 40, 255))
    d.polygon([(cx, cy - k * 0.6), (cx - k * 0.2, cy + k * 0.2), (cx + k * 0.2, cy + k * 0.2)],
              fill=(255, 222, 120, 255))


# -------------------------------------------------------------------- запуск
if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    hex_map(ISL_COLS, ISL_ROWS, island_terrain, name="map_island")
    hex_map(CMP_COLS, CMP_ROWS, camp_terrain,
            props=[lambda d, r: [draw_tent(d, r, *t) for t in TENTS],
                   lambda d, r: draw_fire(d, r, *FIRE)],
            name="map_camp")
