# -*- coding: utf-8 -*-
"""Одна команда после любой правки.

    python sync.py              обновить сцену, опубликовать, подменить в игре
    python sync.py --dry-run    только показать, что изменилось бы
    python sync.py --no-push    всё, кроме публикации (и без подмены в игре:
                                игра не увидит неопубликованные картинки)

Что происходит по порядку:

  1. Картинки пересобираются из исходников: листы карт из cards.xlsx, поля
     локаций, фигурки. Имя файла содержит хеш содержимого, поэтому правка
     даёт новое имя и новую ссылку — кэш никогда не покажет старое.
  2. В живом сохранении TTS каждый объект проекта сверяется с исходником.
     Совпадает — не трогается вовсе. Отличается — у картинки меняется ссылка,
     у колоды пересобираются карты. Положение, поворот, масштаб, ручная
     расстановка — всё остаётся. Объекта нет в сцене — создаётся на месте
     по умолчанию из scene.py. Изменился global.lua — обновляется скрипт.
  3. Копия сцены и картинки коммитятся и уходят на GitHub. С этого момента
     картинки видят все игроки.
  4. Если TTS запущен с этой сценой, изменённые объекты подменяются прямо на
     столе (tts_live.py). Если нет — увидите при следующей загрузке сцены.
  5. Chest (Objects → Saved Objects → Тэйрин) переписывается: колоды,
     отдельные карты, фигурки — всё можно вытащить на стол мышкой.

Объекты опознаются по метке в GMNotes: `teyrin:<ключ>@<хеш>`. Не по GUID и не
по номеру колоды — TTS их перенумеровывает при сохранении. Метку видно
ведущему при наведении, она безвредна; стирать не надо.
"""
import hashlib, json, os, re, shutil, subprocess, sys, time, urllib.request

import paths, scene, tts_live
from paths import LIVE, COPY, ASSET_URL, SAVES, asset, asset_hash, url
from scene import MARK

DRY = "--dry-run" in sys.argv
PUSH = "--no-push" not in sys.argv


# ------------------------------------------------------------ объекты в файле
def mark_of(o):
    """(ключ, хеш) из метки GMNotes или (None, None)."""
    m = re.match(re.escape(MARK) + r"([\w]+)@([0-9a-f]+)$", (o.get("GMNotes") or "").strip())
    return (m.group(1), m.group(2)) if m else (None, None)


def stamp(o, key, h):
    o["GMNotes"] = "%s%s@%s" % (MARK, key, h)


def walk(objs):
    for o in objs:
        yield o
        for c in o.get("ContainedObjects", []):
            yield c


def base_object(guid, name, nick, desc, x, z, **kw):
    o = {"GUID": guid, "Name": name,
         "Transform": {"posX": x, "posY": 1.6, "posZ": z, "rotX": 0.0, "rotY": 0.0,
                       "rotZ": 0.0, "scaleX": 1.0, "scaleY": 1.0, "scaleZ": 1.0},
         "Nickname": nick, "Description": desc, "GMNotes": "",
         "AltLookAngle": {"x": 0.0, "y": 0.0, "z": 0.0},
         "ColorDiffuse": {"r": 1.0, "g": 1.0, "b": 1.0},
         "LayoutGroupSortIndex": 0, "Value": 0, "Locked": False, "Grid": True,
         "Snap": True, "IgnoreFoW": False, "MeasureMovement": False,
         "DragSelectable": True, "Autoraise": True, "Sticky": True, "Tooltip": True,
         "GridProjection": False, "HideWhenFaceDown": False, "Hands": False,
         "LuaScript": "", "LuaScriptState": "", "XmlUI": ""}
    o.update(kw)
    return o


class Guids:
    def __init__(self, objs):
        self.taken = {o["GUID"] for o in walk(objs)}
        self.n = 0x400000

    def new(self):
        while True:
            self.n += 0x137
            g = format(self.n & 0xFFFFFF, "06x")
            if g not in self.taken:
                self.taken.add(g)
                return g


# ------------------------------------------------------------------- картинки
def sync_images(objs, guids, log):
    """Доски, фигурки, жетоны. Возвращает [(key, url, note)] для подмены в игре."""
    hot = []
    for entry in scene.IMAGES:
        key, cur, want = entry["key"], asset_hash(entry["key"]), url(entry["key"])
        note = "%s%s@%s" % (MARK, key, cur)
        found = [o for o in objs if mark_of(o)[0] == key]
        if not found:                                          # первичное опознание
            found = [o for o in objs if o.get("Nickname") == entry["nick"]
                     and "CustomImage" in o and not mark_of(o)[0]]
        if not found:
            o = base_object(guids.new(), entry["kind"], entry["nick"], "",
                            entry["pos"][0], entry["pos"][1],
                            CustomImage={"ImageURL": want, "ImageSecondaryURL": "",
                                         "ImageScalar": 1.0, "WidthScale": 0.0})
            if entry["kind"] == "Custom_Tile":
                o["CustomImage"]["CustomTile"] = {"Type": 0, "Thickness": 0.1,
                                                  "Stackable": False, "Stretch": True}
                o["Locked"] = True
            elif entry["kind"] == "Custom_Token":
                o["CustomImage"]["CustomToken"] = {"Thickness": 0.2, "MergeDistancePixels": 15.0,
                                                   "StandUp": False, "Stackable": False}
            stamp(o, key, cur)
            objs.append(o)
            log("создан", entry["nick"], asset(key))
            hot.append((key, want, note))
            continue
        changed = False
        for o in found:
            if o["CustomImage"]["ImageURL"] != want:
                o["CustomImage"]["ImageURL"] = want
                changed = True
            stamp(o, key, cur)
        if changed:
            log("обновлён", entry["nick"] + (" ×%d" % len(found) if len(found) > 1 else ""), asset(key))
            hot.append((key, want, note))
        else:
            log("без изменений", entry["nick"], "")
    return hot


# --------------------------------------------------------------------- колоды
def deck_hash(entry, cards):
    """Содержимое колоды: лист лица + лист рубашки + тексты всех карт."""
    face, back = asset_hash(entry["key"] + "_face"), asset_hash(entry["key"] + "_back")
    blob = json.dumps([entry["describe"](c) for c in cards], ensure_ascii=False)
    return hashlib.sha1((face + back + blob).encode("utf-8")).hexdigest()[:8]


def is_deck(o):
    return o["Name"] in ("Deck", "DeckCustom") and "CustomDeck" in o


def sheet_of(o):
    cd = list(o["CustomDeck"].values())[0]
    return (cd["NumWidth"], cd["NumHeight"])


def rebuild_deck(o, entry, cards, guids):
    """Пересобирает карты внутри колоды. Сам объект колоды остаётся: его
    положение, поворот, GUID и номер колоды в файле не меняются."""
    deck_id = list(o["CustomDeck"].keys())[0]
    nw, nh = entry["sheet"]
    if len(cards) > nw * nh:
        raise SystemExit("%s: карт %d, а на листе %dx%d клеток"
                         % (entry["nick"], len(cards), nw, nh))
    cd = {deck_id: {"FaceURL": url(entry["key"] + "_face"),
                    "BackURL": url(entry["key"] + "_back"),
                    "NumWidth": nw, "NumHeight": nh, "BackIsHidden": True,
                    "UniqueBack": entry["unique_back"], "Type": 0}}
    t = o["Transform"]
    contained, ids = [], []
    for i, c in enumerate(cards):
        cid = int(deck_id) * 100 + i
        ids.append(cid)
        nick, desc = entry["describe"](c)
        card = base_object(guids.new(), "Card", nick, desc, t["posX"], t["posZ"],
                           CardID=cid, SidewaysCard=False, HideWhenFaceDown=True,
                           CustomDeck=json.loads(json.dumps(cd)))
        card["Transform"] = dict(t, posY=t["posY"] + i * 0.2)
        contained.append(card)
    o["CustomDeck"] = cd
    o["DeckIDs"] = ids
    o["ContainedObjects"] = contained
    o["Description"] = "Колода: %d карт." % len(cards)
    if not o.get("Nickname"):
        o["Nickname"] = entry["nick"]


def sync_decks(objs, guids, log):
    """Возвращает [(key, json_колоды)] для подмены в игре."""
    hot = []
    for entry in scene.DECKS:
        key = entry["key"]
        cards = scene.read_cards(entry["xlsx"], entry["name_col"])
        cur = deck_hash(entry, cards)
        found = [o for o in objs if is_deck(o) and mark_of(o)[0] == key]
        if not found:                                          # первичное опознание
            found = [o for o in objs if is_deck(o) and not mark_of(o)[0]
                     and sheet_of(o) == tuple(entry["sheet"])]
        if not found:
            deck_id = str(max([int(k) for o in objs if is_deck(o)
                               for k in o["CustomDeck"].keys()] + [0]) + 1)
            o = base_object(guids.new(), "DeckCustom", entry["nick"], "",
                            entry["pos"][0], entry["pos"][1],
                            SidewaysCard=False, HideWhenFaceDown=True,
                            CustomDeck={deck_id: {}}, DeckIDs=[], ContainedObjects=[])
            o["Transform"]["rotZ"] = 180.0                     # рубашкой вверх
            rebuild_deck(o, entry, cards, guids)
            stamp(o, key, cur)
            objs.append(o)
            log("создана", entry["nick"], "%d карт" % len(cards))
            hot.append((key, json.dumps(o, ensure_ascii=False)))
            continue
        if len(found) > 1:
            log("ВНИМАНИЕ", entry["nick"], "нашлось %d колод с этой меткой, беру первую" % len(found))
        o = found[0]
        _, h = mark_of(o)
        face_ok = list(o["CustomDeck"].values())[0].get("FaceURL") == url(key + "_face")
        if h != cur or not face_ok:
            rebuild_deck(o, entry, cards, guids)
            stamp(o, key, cur)
            log("пересобрана", entry["nick"], "%d карт" % len(cards))
            hot.append((key, json.dumps(o, ensure_ascii=False)))
        else:
            stamp(o, key, cur)
            log("без изменений", entry["nick"], "")
    return hot


# ------------------------------------------------------------------------ Lua
def sync_lua(save, log):
    if not os.path.exists(paths.LUA):
        return False
    lua = open(paths.LUA, encoding="utf-8").read()
    if lua == save["LuaScript"]:
        log("без изменений", "global.lua", "")
        return False
    save["LuaScript"] = lua
    log("обновлён", "global.lua", "скрипт применится при загрузке сцены")
    return True


# ---------------------------------------------------------------------- Chest
# Objects -> Saved Objects в TTS — это папка Saves\Saved Objects: один JSON на
# объект плюс PNG-миниатюра. sync.py пишет туда каждую колоду, каждую карту и
# каждую фигурку со ссылками, которые сейчас в сцене.
CHEST = os.path.join(SAVES, "Saved Objects", "Тэйрин")


def chest_name(s):
    return re.sub(r'[\\/:*?"<>|]+', "—", s).strip(" .") or "объект"


def chest_write(folder, name, obj, thumb):
    os.makedirs(folder, exist_ok=True)
    o = json.loads(json.dumps(obj))
    o["Transform"].update(posX=0.0, posY=2.0, posZ=0.0)
    doc = {"SaveName": "", "GameMode": "", "Gravity": 0.5, "PlayArea": 0.5, "Date": "",
           "Table": "", "Sky": "", "Note": "", "Rules": "", "XmlUI": "", "LuaScript": "",
           "LuaScriptState": "", "ObjectStates": [o], "TabStates": {}, "VersionNumber": ""}
    base = os.path.join(folder, chest_name(name))
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    thumb.save(base + ".png", "PNG", optimize=True)


def thumb_from(path, crop=None, size=256):
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    if crop:
        im = im.crop(crop)
    im.thumbnail((size, size), Image.LANCZOS)
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg.paste(im, ((size - im.width) // 2, (size - im.height) // 2), im)
    return bg


def write_chest(objs):
    from PIL import Image
    # Папка TTS лежит в OneDrive, и он часто держит каталоги открытыми: файлы
    # удаляются, а сам каталог — нет. Это не мешает: он тут же заполняется заново.
    shutil.rmtree(CHEST, ignore_errors=True)
    n = 0
    for entry in scene.DECKS:
        deck = next((o for o in objs if is_deck(o) and mark_of(o)[0] == entry["key"]), None)
        if deck is None:
            continue
        face = os.path.join(paths.ASSETS, asset(entry["key"] + "_face"))
        with Image.open(face) as im:
            cw, ch = im.width // entry["sheet"][0], im.height // entry["sheet"][1]
        chest_write(os.path.join(CHEST, "Колоды"), entry["nick"], deck,
                    thumb_from(face, (0, 0, cw, ch)))
        n += 1
        # В Chest карты идут по номеру в таблице (он зашит в CardID), а не по тасовке.
        for card in sorted(deck.get("ContainedObjects", []), key=lambda c: c["CardID"]):
            i = card["CardID"] % 100
            c, r = i % entry["sheet"][0], i // entry["sheet"][0]
            single = json.loads(json.dumps(card))
            single["Transform"]["rotZ"] = 0.0                  # лицом вверх
            chest_write(os.path.join(CHEST, entry["nick"]), "%02d %s" % (i + 1, card["Nickname"]),
                        single, thumb_from(face, (c * cw, r * ch, (c + 1) * cw, (r + 1) * ch)))
            n += 1
    seen = set()
    for entry in scene.IMAGES:
        o = next((o for o in objs if mark_of(o)[0] == entry["key"]), None)
        if o is None or entry["key"] in seen:
            continue
        seen.add(entry["key"])
        chest_write(os.path.join(CHEST, "Фигурки"), entry["nick"], o,
                    thumb_from(os.path.join(paths.ASSETS, asset(entry["key"]))))
        n += 1
    return n


# ------------------------------------------------------------------ публикация
def git(*args):
    r = subprocess.run(["git", *args], cwd=paths.REPO, capture_output=True, text=True,
                       encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit("git %s:\n%s%s" % (" ".join(args), r.stdout, r.stderr))
    return r.stdout.strip()


def publish(message):
    """Коммит и push. Возвращает подпись коммита или None, если было нечего."""
    git("add", "-A")
    status = git("status", "--porcelain")
    if not status:
        return None
    if message is None:                 # объекты не менялись: что тогда в коммите?
        message = "расстановка сцены" if "save/" in status else "правки в репозитории"
    git("commit", "-q", "-m", "sync: " + message[:200])
    git("push", "-q")
    return message


def wait_public(urls, tries=15, pause=2):
    """Ждёт, пока GitHub начнёт отдавать новые файлы (обычно секунды)."""
    for u in urls:
        for _ in range(tries):
            try:
                req = urllib.request.Request(u, method="HEAD")
                if urllib.request.urlopen(req, timeout=10).status == 200:
                    break
            except Exception:
                pass
            time.sleep(pause)
        else:
            raise SystemExit("не отвечает после push: " + u)


# ------------------------------------------------------------------------ main
def build():
    for script in ("gen_cards.py", "gen_maps.py", "gen_art.py"):
        r = subprocess.run([sys.executable, os.path.join(paths.REPO, script)],
                           cwd=paths.REPO, capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            print(r.stdout, r.stderr)
            raise SystemExit(script + " завершился с ошибкой")


def main():
    build()
    print("картинки собраны: %d" % len(json.load(open(paths.MANIFEST, encoding="utf-8"))))

    save = json.load(open(LIVE, encoding="utf-8"))
    objs = save["ObjectStates"]
    guids = Guids(objs)

    rows = []
    def log(what, who, detail):
        rows.append((what, who, detail))

    hot_images = sync_images(objs, guids, log)
    hot_decks = sync_decks(objs, guids, log)
    lua_changed = sync_lua(save, log)
    changed = [r for r in rows if r[0] != "без изменений"]

    width = max(len(r[1]) for r in rows)
    for what, who, detail in changed:
        print("  %-12s %-*s  %s" % (what, width, who, detail))
    print("  без изменений: %d" % (len(rows) - len(changed)))

    foreign = sorted({u for u in re.findall(r'"(?:ImageURL|FaceURL|BackURL)"\s*:\s*"([^"]+)"',
                                            json.dumps(save)) if not u.startswith(ASSET_URL)})
    if foreign:
        print("  ссылки не на GitHub (%d) — объекты вне проекта или старые:" % len(foreign))
        for u in foreign:
            print("     " + u[:100])

    if DRY:
        print("\n--dry-run: ничего не записано")
        return

    if changed:
        with open(LIVE, "w", encoding="utf-8") as f:
            json.dump(save, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(COPY), exist_ok=True)
    shutil.copyfile(LIVE, COPY)
    print("Chest: %d объектов" % write_chest(objs))

    if not PUSH:
        print("\n--no-push: не опубликовано. Игра не увидит новые картинки, пока не сделан push.")
        return

    summary = publish("; ".join("%s %s" % (w, who) for w, who, _ in changed) or None)
    if summary:
        wait_public([u for _, u, _ in hot_images]
                    + [url(k + "_face") for k, _ in hot_decks]
                    + [url(k + "_back") for k, _ in hot_decks])
        print("опубликовано: " + summary)
    else:
        print("публиковать нечего")

    if hot_images or hot_decks:
        if tts_live.replace(hot_images, hot_decks):
            print("TTS: объекты подменены на столе (%d)" % (len(hot_images) + len(hot_decks)))
        else:
            print("TTS не запущен — изменения появятся при загрузке сцены")
    if lua_changed:
        print("скрипт изменился — перезагрузите сцену (Load), чтобы он применился")


if __name__ == "__main__":
    main()
