-- Тэйрин, первый прототип. Global-скрипт сцены.
--
-- Шаблон: gen_save.py подставляет значения вместо меток в двойных фигурных
-- скобках и кладёт результат в поле LuaScript сохранения. Править этот файл.
--
-- ЗАЧЕМ ЭТОТ СКРИПТ
--
-- В документации TTS не написано, что означает Size X для гексагональной
-- сетки: ширину гекса по вершинам, по граням или шаг между центрами. Разница
-- между трактовками — 15%, и на глаз она выглядит как «карта не совпадает с
-- разметкой». Настоящий размер Custom Tile тоже нельзя вычислить заранее: он
-- зависит от пропорций картинки.
--
-- Поэтому вся раскладка считается здесь, в игре, от одного числа — HEX,
-- реальной ширины гекса сетки в единицах стола. Меняешь HEX меню калибровки,
-- и доски, и фигурки пересчитываются вместе: карта остаётся привязанной к
-- гексам при любом размере.
--
-- Решётка: гекс (i, j) имеет центр (i*COL, -(j*ROW)), нечётные колонки
-- сдвинуты вниз на половину. Поле локации садится гексом (0,0) в узел
-- (gc, gr). Отсюда и центр доски, и позиция каждой фигурки.

local NOMINAL = 2.000000       -- размер гекса, заложенный в файл сохранения
local ISLAND  = "1003a5"

local AREAS = {
    isl = {guid = "1003a5", cols = 13, rows = 8, gc = -10, gr = -4},
    cmp = {guid = "1004dc", cols = 5, rows = 4, gc = 4, gr = 4},
}

local LINK = {guid = "100613", area = "cmp", c = 2, r = -2, w = 0.7500}

local PIECES = {
    {guid = "10074a", area = "isl", c = 3, r = 1, w = 0.5750},
    {guid = "100881", area = "isl", c = 4, r = 3, w = 0.6250},
    {guid = "1009b8", area = "isl", c = 4, r = 4, w = 0.6250},
    {guid = "100aef", area = "isl", c = 3, r = 6, w = 0.6250},
    {guid = "100c26", area = "isl", c = 6, r = 3, w = 0.6750},
    {guid = "100d5d", area = "isl", c = 9, r = 3, w = 0.5000},
    {guid = "100e94", area = "cmp", c = 2, r = 0, w = 0.5750},
    {guid = "100fcb", area = "cmp", c = 2, r = 2, w = 0.5750},
}

-- Кандидаты на настоящий размер гекса: единица, 2/sqrt(3), sqrt(3)/2, 4/3,
-- 3/4 от заложенного. Это и есть перебор трактовок Size X.
local SIZES = {
    {1.000000, "как в файле"},
    {1.154701, "Size X = ширина по граням"},
    {0.866025, "Size X = ширина по вершинам, сетка мельче"},
    {1.333333, "Size X = шаг между центрами"},
    {0.750000, "обратный случай"},
}

local size_i = 1                -- индекс в SIZES
local off_x, off_z = 0, 0       -- сдвиг всей раскладки, в долях гекса
local applied = nil             -- при какой калибровке раскладка уже применена

-- ------------------------------------------------------------------ геометрия
local function hexOf()
    return NOMINAL * SIZES[size_i][1]
end

local function fitWidth(o, width)
    if o == nil then return end
    local size = o.getBounds().size
    if size.x > 0.01 then
        local s = o.getScale()
        local k = width / size.x
        o.setScale({x = s.x * k, y = s.y * k, z = s.z * k})
    end
end

local function moveTo(o, x, z)
    if o == nil then return end
    local p = o.getPosition()
    o.setPosition({x = x, y = p.y, z = z})
end

local function layout()
    local hex = hexOf()
    local hexH = hex * 0.8660254
    local col  = hex * 0.75
    local dx, dz = off_x * hex, off_z * hexH

    for _, a in pairs(AREAS) do
        local o = getObjectFromGUID(a.guid)
        fitWidth(o, col * (a.cols - 1) + hex)
        moveTo(o,
               col * (2 * a.gc + a.cols - 1) / 2 + dx,
               -(2 * a.gr + a.rows - 1) * hexH / 2 - hexH / 4 + dz)
    end

    -- Плитка перехода считается так же, как фигурки: она привязана к гексу
    -- поля старта (за его краем, отсюда отрицательный ряд).
    local place = {}
    for _, p in ipairs(PIECES) do place[#place + 1] = p end
    place[#place + 1] = LINK

    for _, p in ipairs(place) do
        local a = AREAS[p.area]
        local i, j = a.gc + p.c, a.gr + p.r
        local o = getObjectFromGUID(p.guid)
        fitWidth(o, p.w * hex)
        moveTo(o, i * col + dx, -(j * hexH + (i % 2) * hexH / 2) + dz)
    end
end

local function report()
    local hex = hexOf()
    print(string.format("Гекс %.4f (%s, x%.4f от %.4f), сдвиг %.2f / %.2f гекса.",
                        hex, SIZES[size_i][2], SIZES[size_i][1], NOMINAL, off_x, off_z))
    local o = getObjectFromGUID(ISLAND)
    if o ~= nil then
        local b = o.getBounds().size
        print(string.format("Остров: %.3f x %.3f единиц стола.", b.x, b.z))
    end
end

-- Отпечаток текущей калибровки: по нему видно, менялись ли параметры с
-- прошлой загрузки.
local function stamp()
    return string.format("%d/%.4f/%.4f", size_i, off_x, off_z)
end

local function apply()
    layout()
    applied = stamp()
    report()
end

-- Настройки сетки подобраны в игре под расставленную вручную сцену, поэтому
-- Offset Y — просто замеренное число, а не доля гекса: раскладка больше не
-- считается от решётки с началом в (0, 0).
--
-- Options -> Grid: Type = гексы, Size X = Size Y = 2, Offset X = 0,
-- Offset Y = 1.3, Snapping = Center, Show Lines, Thin.
local GRID = {
    type       = 2,      -- гексы, первый из двух вариантов
    sizeX      = 2.0,
    sizeY      = 2.0,    -- равные размеры = неискажённый гекс
    offsetX    = 0.0,
    offsetY    = 1.3,
    snapping   = 3,      -- 1 выкл, 2 по линиям, 3 по центрам, 4 и то и то
    lines      = true,
    thickLines = false,
}

local function setupGrid()
    Grid.type        = GRID.type
    Grid.sizeX       = GRID.sizeX
    Grid.sizeY       = GRID.sizeY
    Grid.offsetX     = GRID.offsetX
    Grid.offsetY     = GRID.offsetY
    Grid.snapping    = GRID.snapping
    Grid.show_lines  = GRID.lines
    Grid.thick_lines = GRID.thickLines
end

-- Картинки грузятся асинхронно; пока Custom Tile не догрузился, его габариты
-- ничего не значат. Раньше скрипт ждал фиксированные 2 секунды и запоминал,
-- что уже сработал, — карта острова весит 2.5 МБ и не укладывалась.
local function loaded()
    local ok, res = pcall(function()
        for _, a in pairs(AREAS) do
            local o = getObjectFromGUID(a.guid)
            if o == nil or o.loading_custom == true then return false end
        end
        for _, p in ipairs(PIECES) do
            local o = getObjectFromGUID(p.guid)
            if o == nil or o.loading_custom == true then return false end
        end
        local l = getObjectFromGUID(LINK.guid)
        if l == nil or l.loading_custom == true then return false end
        return true
    end)
    if not ok then return true end
    return res
end

-- ---------------------------------------------------------------------- меню
local function addMenu()
    local o = getObjectFromGUID(ISLAND)
    if o == nil then return end
    o.addContextMenuItem("Размер гекса: следующий", function()
        size_i = size_i % #SIZES + 1
        apply()
    end, true)
    o.addContextMenuItem("Сдвиг: пол-колонки вбок", function()
        off_x = (off_x + 0.375) % 0.75
        apply()
    end, true)
    o.addContextMenuItem("Сдвиг: пол-ряда вниз", function()
        off_z = (off_z + 0.5) % 1.0
        apply()
    end, true)
    o.addContextMenuItem("Повернуть гексы сетки", function()
        Grid.type = (Grid.type == 2) and 3 or 2
        print("Grid.type = " .. Grid.type .. " (2 = horizontal, 3 = vertical)")
    end, true)
    o.addContextMenuItem("Сброс калибровки", function()
        size_i, off_x, off_z = 1, 0, 0
        setupGrid()
        apply()
    end, true)
    o.addContextMenuItem("Числа в чат", report, true)
end

-- Раскладка применяется только когда параметры калибровки изменились (и на
-- первой загрузке, где их ещё нет). Иначе скрипт при каждом открытии сцены
-- возвращал бы все фигурки на исходные гексы и стирал ход игры.
-- ------------------------------------------------------- второй ведущий
-- Отдельного второго места ведущего в TTS нет: чёрное место одно, и цвет у
-- него не меняется. Поэтому белый назначен вторым ведущим через Promote —
-- это почти все права хоста, кроме правки скриптов, импорта своего контента
-- и изменения кастомных объектов.
--
-- Чего Promote НЕ даёт: доступа к тому, что видно только чёрному — GM-заметок
-- объектов и скрытых зон, привязанных к чёрному цвету. Общие материалы
-- ведущих лучше держать не в GM-заметках, а в скрытой зоне, заведённой в том
-- числе на белый.

local SECOND_GM = "White"

local function promoteSecondGM(why)
    local p = Player[SECOND_GM]
    if p == nil or not p.seated then return end
    if p.host then return end          -- у хоста права и так шире
    if p.promoted then return end

    local ok = pcall(function() p.promoted = true end)
    if not ok or not p.promoted then   -- на старых сборках поле только у функции
        pcall(function() p.promote(true) end)
    end
    if p.promoted then
        print(SECOND_GM .. ": выдан Promote, второй ведущий (" .. why .. ").")
    end
end

function onPlayerChangeColor(colour)
    if colour == SECOND_GM then
        -- Место занимают не мгновенно: даём игре усадить игрока.
        Wait.time(function() promoteSecondGM("сел за стол") end, 0.5)
    end
end

function onSave()
    return JSON.encode({size_i = size_i, off_x = off_x, off_z = off_z, applied = applied})
end

function onLoad(saved)
    if saved ~= nil and saved ~= "" then
        local ok, d = pcall(function() return JSON.decode(saved) end)
        if ok and type(d) == "table" then
            if type(d.size_i) == "number" and SIZES[d.size_i] ~= nil then size_i = d.size_i end
            if type(d.off_x) == "number" then off_x = d.off_x end
            if type(d.off_z) == "number" then off_z = d.off_z end
            if type(d.applied) == "string" then applied = d.applied end
        end
    end
    pcall(setupGrid)
    pcall(addMenu)
    Wait.time(function() promoteSecondGM("загрузка сцены") end, 1)
    if applied ~= stamp() then
        Wait.condition(apply, loaded, 30, apply)
    end
end
