# -*- coding: utf-8 -*-
"""Связь с запущенным Tabletop Simulator.

TTS слушает localhost:39999 (External Editor API — тот же канал, которым
пользуются плагины Atom и VS Code) и принимает JSON-сообщения. Нам нужно одно:
«выполни этот Lua-код в загруженной сцене» (messageID 3). Ответы игра шлёт на
порт 39998, но мы их не читаем — код сам печатает результат в чат игры.

Так sync.py подменяет изменённые объекты прямо на столе, без перезагрузки
сцены. Картинки при этом игра качает по публичным ссылкам, поэтому подмена
идёт только после того, как push прошёл и ссылки отвечают.
"""
import json, socket

HOST, PORT = "127.0.0.1", 39999


def execute(lua):
    """Отправляет Lua на выполнение. False — TTS не запущен."""
    msg = json.dumps({"messageID": 3, "guid": "-1", "script": lua}, ensure_ascii=False)
    try:
        with socket.create_connection((HOST, PORT), timeout=5) as s:
            s.sendall(msg.encode("utf-8"))
            s.shutdown(socket.SHUT_WR)
    except OSError:
        return False
    return True


# Lua-скрипт подмены. Ищет объекты проекта по метке в GMNotes (teyrin:<ключ>@…),
# картинкам меняет ссылку и перезагружает их на месте, колоды удаляет и
# создаёт заново из JSON на прежнем месте. Если в сцене меток нет — это не
# наша сцена, ничего не трогает.
_LUA = r"""
local MARK = "teyrin:"
local IMAGES = %(images)s
local DECKS = %(decks)s

local function marked(key)
    local out, pre = {}, MARK .. key .. "@"
    for _, o in ipairs(getAllObjects()) do
        local n = o.getGMNotes() or ""
        if n:sub(1, #pre) == pre then out[#out + 1] = o end
    end
    return out
end

local any = false
for _, o in ipairs(getAllObjects()) do
    if (o.getGMNotes() or ""):sub(1, #MARK) == MARK then any = true break end
end
if not any then
    printToAll("Тэйрин: в загруженной сцене нет объектов проекта — ничего не менял", {1, 0.7, 0.4})
    return
end

local n = 0
for _, im in ipairs(IMAGES) do
    for _, o in ipairs(marked(im.key)) do
        o.setGMNotes(im.note)
        o.setCustomObject({image = im.url})
        o.reload()
        n = n + 1
    end
end
for _, d in ipairs(DECKS) do
    local olds = marked(d.key)
    local params = {json = d.json}
    if olds[1] then
        params.position = olds[1].getPosition()
        params.rotation = olds[1].getRotation()
        params.scale = olds[1].getScale()
        for _, o in ipairs(olds) do o.destruct() end
    end
    spawnObjectJSON(params)
    n = n + 1
end
printToAll("Тэйрин: обновлено объектов — " .. n, {0.6, 0.9, 0.6})
"""


def _lua_str(s):
    """Строка как длинный литерал Lua: без экранирования, годится для JSON."""
    lvl = "="
    while "]" + lvl + "]" in s:
        lvl += "="
    return "[" + lvl + "[" + s + "]" + lvl + "]"


def replace(images, decks):
    """images: [(key, url, note)], decks: [(key, json_str)]. Возвращает True,
    если TTS принял команду."""
    im = "{" + ", ".join('{key=%s, url=%s, note=%s}' % (_lua_str(k), _lua_str(u), _lua_str(n))
                         for k, u, n in images) + "}"
    dk = "{" + ", ".join('{key=%s, json=%s}' % (_lua_str(k), _lua_str(j))
                         for k, j in decks) + "}"
    return execute(_LUA % {"images": im, "decks": dk})
