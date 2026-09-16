# -*- coding: utf-8 -*-
"""Единая геометрия гекс-решётки: ею пользуются и генератор карт, и генератор
сохранения, поэтому картинка локации и позиции фигурок не могут разъехаться.

Гексы «плоской крышей» (вершины слева и справа, ровные верх и низ) — как на
схеме в «Сценарии первого прототипа». Колонки идут вертикально, нечётные
смещены вниз на половину гекса (offset odd-q).

HEX_W / HEX_H — габаритный прямоугольник одного гекса; именно эти два числа
TTS показывает в Options → Grid как Size X и Size Y.
"""
import math

HEX_W = 2.0                        # ширина гекса, от вершины до вершины
HEX_H = HEX_W * math.sqrt(3) / 2   # высота гекса, от грани до грани
COL   = HEX_W * 0.75               # шаг между колонками
ROW   = HEX_H                      # шаг между рядами внутри колонки


def board_size(cols, rows):
    """Габариты поля из cols x rows гексов."""
    return COL * (cols - 1) + HEX_W, ROW * rows + HEX_H / 2


def center(cols, rows, bx, bz, c, r):
    """Центр гекса (c, r) в координатах стола; поле центрировано в (bx, bz)."""
    w, h = board_size(cols, rows)
    x = bx - w / 2 + HEX_W / 2 + c * COL
    z = bz + h / 2 - (HEX_H / 2 + r * ROW + (c % 2) * HEX_H / 2)
    return x, z


# Общая решётка стола: гекс с индексами (i, j) имеет центр (i*COL, -(j*ROW)),
# нечётные колонки сдвинуты вниз на половину гекса. Поле локации кладётся на
# эту решётку: его гекс (0, 0) совпадает с гексом (gc, gr).
def world(gc, gr, c, r):
    """Центр гекса (c, r) поля, посаженного на решётку в узел (gc, gr)."""
    i, j = gc + c, gr + r
    return i * COL, -(j * ROW + (i % 2) * HEX_H / 2)


def board_center(gc, gr, cols, rows):
    """Куда поставить саму доску, чтобы её гексы легли на узлы решётки."""
    bx = COL * (2 * gc + cols - 1) / 2
    bz = -(2 * gr + rows - 1) * ROW / 2 - HEX_H / 4
    return bx, bz


def center_px(radius, c, r):
    """Центр гекса (c, r) в пикселях картинки; radius — половина ширины гекса."""
    return (radius + c * radius * 1.5,
            radius * math.sqrt(3) / 2 * (1 + 2 * r + (c % 2)))


def image_size(radius, cols, rows):
    return (int(round(radius * 1.5 * (cols - 1) + radius * 2)),
            int(round(radius * math.sqrt(3) * rows + radius * math.sqrt(3) / 2)))


def corners(cx, cy, radius):
    return [(cx + radius * math.cos(math.radians(a)),
             cy + radius * math.sin(math.radians(a))) for a in range(0, 360, 60)]


def neighbours(c, r):
    """Шесть соседей гекса (c, r) в порядке рёбер, возвращаемых corners()."""
    odd = c % 2
    return {"N":  (c, r - 1),          "S":  (c, r + 1),
            "NE": (c + 1, r - 1 + odd), "SE": (c + 1, r + odd),
            "NW": (c - 1, r - 1 + odd), "SW": (c - 1, r + odd)}


# Расстояния считаются в кубических координатах: в offset-координатах
# (колонка, ряд) соседи нечётных и чётных колонок нумеруются по-разному, и
# «на два гекса вокруг» там не выражается простым условием.
def cube(c, r):
    """Кубические координаты гекса (c, r); раскладка odd-q, плоская крыша."""
    q = c
    s = r - (c - (c & 1)) // 2
    return q, s, -q - s


def distance(a, b):
    """Расстояние в гексах между (c, r) и (c, r)."""
    (aq, as_, ay), (bq, bs, by) = cube(*a), cube(*b)
    return (abs(aq - bq) + abs(as_ - bs) + abs(ay - by)) // 2


def disc(c, r, radius, cols=None, rows=None):
    """Гексы не дальше radius от (c, r): центр плюс radius колец вокруг.
    Радиус 2 даёт 19 гексов — форма раскалённой зоны из сценария."""
    out = set()
    for cc in range(c - 2 * radius, c + 2 * radius + 1):
        for rr in range(r - 2 * radius, r + 2 * radius + 1):
            if cols is not None and not (0 <= cc < cols):
                continue
            if rows is not None and not (0 <= rr < rows):
                continue
            if distance((c, r), (cc, rr)) <= radius:
                out.add((cc, rr))
    return out
