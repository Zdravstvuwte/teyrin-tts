# -*- coding: utf-8 -*-
"""Где что лежит. Единственное место с путями и адресами.

Исходники карт (cards.xlsx) остаются в Obsidian — там их правит человек.
Всё остальное живёт в этом репозитории: скрипты, картинки, копия сцены.
Картинки публикуются на GitHub, и сцена ссылается на них по адресам
raw.githubusercontent.com — такие ссылки видят все игроки.
"""
import glob, hashlib, json, os

REPO     = os.path.dirname(os.path.abspath(__file__))
ASSETS   = os.path.join(REPO, "assets")
MANIFEST = os.path.join(ASSETS, "assets.json")   # ключ -> актуальное имя файла
LUA      = os.path.join(REPO, "global.lua")      # Global-скрипт сцены

CARDS    = r"C:\1_Obsidian\Obsidian_cloud\Тэйрин\Карты"   # папки с cards.xlsx

# Папка сохранений TTS. Из меню Save & Load игра читает только её.
TTS      = r"C:\Users\dk466\OneDrive\Документы\My Games\Tabletop Simulator"
SAVES    = os.path.join(TTS, "Saves")
SLOT     = "TS_Save_1"                                 # цифра = номер в меню
LIVE     = os.path.join(SAVES, SLOT + ".json")         # этот файл грузит TTS
COPY     = os.path.join(REPO, "save", SLOT + ".json")  # копия в репозитории

# Публикация. Репозиторий должен быть публичным, иначе TTS картинки не скачает.
GITHUB    = "Zdravstvuwte/teyrin-tts"
BRANCH    = "main"
ASSET_URL = "https://raw.githubusercontent.com/%s/%s/assets/" % (GITHUB, BRANCH)


# Каждая картинка лежит под именем <ключ>.<хеш содержимого>.png. Правка
# меняет хеш, а значит имя и ссылку. Так ни кэш TTS, ни кэш GitHub никогда
# не покажут старую картинку под новым содержимым.
def _manifest():
    if not os.path.exists(MANIFEST):
        return {}
    return json.load(open(MANIFEST, encoding="utf-8"))


def store(key, data):
    """Кладёт PNG под именем <key>.<hash>.png, старые версии удаляет."""
    name = "%s.%s.png" % (key, hashlib.sha1(data).hexdigest()[:8])
    for old in glob.glob(os.path.join(ASSETS, key + ".*.png")):
        if os.path.basename(old) != name:
            os.remove(old)
    with open(os.path.join(ASSETS, name), "wb") as f:
        f.write(data)
    table = _manifest()
    table[key] = name
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(table, f, ensure_ascii=False, indent=2)
    return name


def asset(key):
    """Актуальное имя файла по ключу ('map_island', 'beast_face' ...)."""
    table = _manifest()
    if key not in table:
        raise SystemExit("в %s нет %r — сначала собери картинки (sync.py)" % (MANIFEST, key))
    return table[key]


def asset_hash(key):
    """Хеш содержимого из имени файла."""
    return asset(key).rsplit(".", 2)[1]


def url(key):
    """Публичная ссылка на актуальную картинку."""
    return ASSET_URL + asset(key)
