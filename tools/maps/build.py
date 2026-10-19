"""Build content/maps/*.tmj (Tiled JSON) into game/Data/MapNNN.rxdata.

    python tools/maps/build.py

Writes one MapNNN.rxdata per content/maps/<NNN>_<slug>.tmj, then updates MapInfos.rxdata and
Tilesets.rxdata for our maps and tilesets only; base Essentials entries are never changed.
Same input, same bytes. Conventions are in docs/MAPS.md.
"""
import json
import re
import struct
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.maps import autotile  # noqa: E402
from tools.rmxp import rpg  # noqa: E402
from tools.rmxp.marshal import RHash, RString, RubyObject, UserDef, dumps, loads  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "game" / "Data"
CONTENT_DIR = ROOT / "content"

# Essentials v21.1 base content: these entries are never rewritten.
BASE_MAP_IDS = frozenset((
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25, 26, 27,
    28, 29, 30, 31, 34, 35, 36, 37, 38, 39, 40, 41, 44, 45, 46, 47, 49, 50, 51, 52, 53, 54, 55, 56,
    57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75))
BASE_TILESET_COUNT = 25  # Tilesets.rxdata entries 1..25

TILE_LAYERS = ("ground", "mid", "top")  # RMXP layers z = 0, 1, 2
EVENT_LAYER = "events"
TILE = 32
AUTOTILE_SLOTS = 7
FIRST_TILESET_LOCAL = 8  # local ids: 0 blank, 1..7 autotile key, 8+ tileset tiles
TERRAIN_NEUTRAL, TERRAIN_BRIDGE = 13, 15  # Essentials tags that skip tile passability
FLIP_BITS = 0xF0000000
DIRECTIONS = {"retain": 0, "down": 2, "left": 4, "right": 6, "up": 8}
TONE_BLACK, TONE_CLEAR = (-255.0, -255.0, -255.0, 0.0), (0.0, 0.0, 0.0, 0.0)
FADE_FRAMES, WARP_WAIT_FRAMES = 6, 8
TRIGGER_PLAYER_TOUCH = 1

# Ivar orders as stored by the base files (the most common order where files differ).
MAP_IVARS = ["@bgm", "@events", "@tileset_id", "@bgs", "@autoplay_bgm", "@data", "@autoplay_bgs",
             "@height", "@encounter_step", "@width", "@encounter_list"]
EVENT_IVARS = ["@pages", "@name", "@y", "@x", "@id"]
PAGE_IVARS = ["@move_type", "@list", "@condition", "@direction_fix", "@move_route", "@trigger",
              "@step_anime", "@move_frequency", "@graphic", "@always_on_top", "@walk_anime",
              "@move_speed", "@through"]
MAPINFO_IVARS = ["@scroll_x", "@name", "@expanded", "@order", "@scroll_y", "@parent_id"]
TILESET_IVARS = ["@terrain_tags", "@panorama_hue", "@fog_sy", "@name", "@fog_opacity", "@priorities",
                 "@panorama_name", "@fog_sx", "@fog_hue", "@passages", "@autotile_names", "@fog_zoom",
                 "@fog_name", "@battleback_name", "@tileset_name", "@id", "@fog_blend_type"]
# Tileset fields beyond the tile tables, with the base files' defaults.
TILESET_EXTRAS = {"panorama_name": "", "panorama_hue": 0, "fog_name": "", "fog_hue": 0,
                  "fog_opacity": 64, "fog_blend_type": 0, "fog_zoom": 100, "fog_sx": 0, "fog_sy": 0,
                  "battleback_name": ""}

MAP_FILE = re.compile(r"^(\d{1,3})_([a-z0-9_]+)\.tmj$")


class MapBuildError(Exception):
    pass


def s(text):
    return RString.utf8(text)


def obj(cls, ivars):
    return RubyObject(cls, dict(ivars))


# ---------------------------------------------------------------- tilesets

class Tileset:
    """A content/tilesets/*.json file: per-tile passage, priority and terrain tag."""

    def __init__(self, path):
        self.path = Path(path)
        try:
            d = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise MapBuildError("%s: cannot read tileset: %s" % (self.path, e))
        try:
            self.id = int(d["tileset_id"])
            self.name = d["name"]
            self.image = d["tileset_name"]
            self.autotiles = d["autotiles"]
            t = d["tiles"]
            self.passage, self.priority, self.terrain = t["passage"], t["priority"], t["terrain_tag"]
        except (KeyError, TypeError, ValueError) as e:
            raise MapBuildError("%s: missing or bad field %s" % (self.path, e))
        self.replaces_base = bool(d.get("replaces_base", False))
        self.extras = {k: d.get(k, v) for k, v in TILESET_EXTRAS.items()}
        if len(self.autotiles) != AUTOTILE_SLOTS:
            raise MapBuildError("%s: needs exactly 7 autotiles (blank name for an empty slot)" % self.path)
        n = len(self.passage)
        if len(self.priority) != n or len(self.terrain) != n:
            raise MapBuildError("%s: passage, priority and terrain_tag lists differ in length" % self.path)
        self.count = n

    def tables(self):
        """Full RMXP tables indexed by tile id: 0..47 blank, 48..383 autotiles, 384+ tiles."""
        out = []
        for key, blank, tiles in (("passage", 0, self.passage), ("priority", 0, self.priority),
                                  ("terrain_tag", 0, self.terrain)):
            data = [blank] * autotile.AUTOTILE_FIRST
            if key == "priority":
                data[0] = 5  # RMXP stores priority 5 for the empty tile
            for a in self.autotiles:
                data += [int(a[key])] * 48
            out.append(data + [int(v) for v in tiles])
        return out

    def rmxp_id(self, local, where):
        if local == 0:
            return 0
        if local < FIRST_TILESET_LOCAL:
            if not self.autotiles[local - 1]["name"]:
                raise MapBuildError("%s: autotile slot %d is empty in %s" % (where, local, self.path.name))
            return autotile.AUTOTILE_FIRST * local  # shape added later
        if local - FIRST_TILESET_LOCAL >= self.count:
            raise MapBuildError("%s: tile %d is outside tileset %s" % (where, local, self.path.name))
        return autotile.TILESET_FIRST + local - FIRST_TILESET_LOCAL

    def to_ruby(self):
        passages, priorities, terrain = self.tables()
        n = len(passages)
        v = {"@terrain_tags": rpg.Table(n, data=terrain).to_userdef(),
             "@priorities": rpg.Table(n, data=priorities).to_userdef(),
             "@passages": rpg.Table(n, data=passages).to_userdef(),
             "@name": s(self.name), "@tileset_name": s(self.image), "@id": self.id,
             "@autotile_names": [s(a["name"]) for a in self.autotiles]}
        for k, val in self.extras.items():
            v["@" + k] = s(val) if isinstance(val, str) else int(val)
        return obj("RPG::Tileset", [(k, v[k]) for k in TILESET_IVARS])


def tileset_from_json(path):
    """RPG::Tileset built from a content/tilesets/*.json file."""
    return Tileset(path).to_ruby()


def walkable(tables, tiles, x, y):
    """Essentials' playerPassable? for a cell, walking, ignoring events and bridges."""
    passages, priorities, terrain = tables
    for z in (2, 1, 0):
        tid = tiles.get(x, y, z)
        if tid == 0 or terrain[tid] in (TERRAIN_NEUTRAL, TERRAIN_BRIDGE):
            continue
        if passages[tid] & 0x0F == 0x0F:
            return False
        if priorities[tid] == 0:
            return True
    return True


# ---------------------------------------------------------------- tmj reading

def _props(items, where):
    out = {}
    for p in items or []:
        try:
            out[p["name"]] = p["value"]
        except (KeyError, TypeError):
            raise MapBuildError("%s: malformed property %r" % (where, p))
    return out


def _read_tmj(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise MapBuildError("%s: cannot read map: %s" % (path, e))


def map_id_of(path):
    m = MAP_FILE.match(Path(path).name)
    if not m or int(m.group(1)) == 0:
        raise MapBuildError("%s: map files are named <map_id>_<slug>.tmj (id 1..999, slug a-z 0-9 _)"
                            % Path(path).name)
    return int(m.group(1))


class _Context:
    """Map sizes for warp checks: content maps beside the tmj, then base maps in data_dir."""

    def __init__(self, content_maps_dir, data_dir):
        self.content = {}
        for p in sorted(Path(content_maps_dir).glob("*.tmj")):
            try:
                mid = map_id_of(p)
            except MapBuildError:
                continue
            d = _read_tmj(p)
            self.content[mid] = (d.get("width"), d.get("height"))
        self.data_dir = Path(data_dir)
        self.base = {}

    def size(self, mid):
        if mid in self.content:
            return self.content[mid]
        if mid not in self.base:
            f = self.data_dir / ("Map%03d.rxdata" % mid)
            if mid not in BASE_MAP_IDS or not f.is_file():
                self.base[mid] = None
            else:
                m = loads(f.read_bytes())
                self.base[mid] = (m.ivars["@width"], m.ivars["@height"])
        return self.base[mid]


def _tileset_for(doc, path):
    sets = doc.get("tilesets") or []
    if len(sets) != 1 or "source" not in sets[0]:
        raise MapBuildError("%s: needs exactly one tileset, by source path to content/tilesets" % path.name)
    return Tileset((path.parent / sets[0]["source"]).resolve()), int(sets[0].get("firstgid", 1))


def _tile_layers(doc, path, w, h, ts, firstgid):
    layers = {}
    for layer in doc.get("layers", []):
        name, kind = layer.get("name"), layer.get("type")
        if kind == "tilelayer" and name in TILE_LAYERS:
            if name in layers:
                raise MapBuildError("%s: two layers named %s" % (path.name, name))
            layers[name] = layer
        elif kind == "objectgroup" and name == EVENT_LAYER:
            continue
        else:
            raise MapBuildError("%s: unexpected layer %r (%s); use ground, mid, top and events"
                                % (path.name, name, kind))
    tiles = rpg.Table(w, h, 3)
    for z, name in enumerate(TILE_LAYERS):
        layer = layers.get(name)
        if layer is None:
            raise MapBuildError("%s: missing tile layer %s" % (path.name, name))
        data = layer.get("data")
        if not isinstance(data, list) or len(data) != w * h or layer.get("encoding", "csv") != "csv":
            raise MapBuildError("%s: layer %s must hold %d tile numbers as a plain list" % (path.name, name, w * h))
        kinds = [[None] * w for _ in range(h)]
        for i, gid in enumerate(data):
            x, y = i % w, i // w
            where = "%s layer %s (%d,%d)" % (path.name, name, x, y)
            if not isinstance(gid, int) or gid < 0 or gid & FLIP_BITS:
                raise MapBuildError("%s: flipped or invalid tile %r" % (where, gid))
            if gid == 0:
                continue
            if gid < firstgid:
                raise MapBuildError("%s: tile %d is below the tileset's firstgid" % (where, gid))
            tid = ts.rmxp_id(gid - firstgid, where)
            tiles.set(x, y, z, tid)
            kinds[y][x] = autotile.kind_of(tid)
        for y in range(h):
            for x in range(w):
                if kinds[y][x] is not None:
                    tiles.set(x, y, z, tiles.get(x, y, z) + autotile.resolve(kinds, x, y))
    return tiles


# ---------------------------------------------------------------- events

def _audio(name, volume, pitch):
    return obj("RPG::AudioFile", [("@volume", int(volume)), ("@name", s(name)), ("@pitch", int(pitch))])


def _cmd(code, params, indent=0):
    return obj("RPG::EventCommand", [("@parameters", params), ("@indent", indent), ("@code", code)])


def _tone(rgbg):
    return UserDef("Tone", struct.pack("<4d", *rgbg))


def _page(commands, trigger):
    condition = obj("RPG::Event::Page::Condition", [
        ("@switch2_valid", False), ("@self_switch_ch", s("A")), ("@switch1_id", 1),
        ("@switch1_valid", False), ("@variable_value", 0), ("@self_switch_valid", False),
        ("@variable_id", 1), ("@variable_valid", False), ("@switch2_id", 1)])
    route = obj("RPG::MoveRoute", [("@list", [obj("RPG::MoveCommand", [("@parameters", []), ("@code", 0)])]),
                                   ("@skippable", False), ("@repeat", True)])
    graphic = obj("RPG::Event::Page::Graphic", [
        ("@opacity", 255), ("@character_name", s("")), ("@pattern", 0), ("@tile_id", 0),
        ("@direction", 2), ("@blend_type", 0), ("@character_hue", 0)])
    v = {"@move_type": 0, "@list": commands + [_cmd(0, [])], "@condition": condition,
         "@direction_fix": False, "@move_route": route, "@trigger": trigger, "@step_anime": False,
         "@move_frequency": 3, "@graphic": graphic, "@always_on_top": False, "@walk_anime": True,
         "@move_speed": 3, "@through": False}
    return obj("RPG::Event::Page", [(k, v[k]) for k in PAGE_IVARS])


def _int_prop(props, key, where):
    v = props.get(key)
    if not isinstance(v, int) or isinstance(v, bool):
        raise MapBuildError("%s: needs integer property %s" % (where, key))
    return v


def _warp_commands(props, where, ctx):
    target = _int_prop(props, "target_map", where)
    tx, ty = _int_prop(props, "target_x", where), _int_prop(props, "target_y", where)
    size = ctx.size(target)
    if size is None:
        raise MapBuildError("%s: warp target map %d does not exist" % (where, target))
    if not (0 <= tx < size[0] and 0 <= ty < size[1]):
        raise MapBuildError("%s: warp target (%d,%d) is outside map %d (%dx%d)"
                            % (where, tx, ty, target, size[0], size[1]))
    direction = props.get("direction", "retain")
    if direction not in DIRECTIONS:
        raise MapBuildError("%s: direction must be one of %s" % (where, ", ".join(DIRECTIONS)))
    cmds = []
    if props.get("sound"):
        cmds.append(_cmd(250, [_audio(props["sound"], 80, 100)]))
    cmds += [_cmd(223, [_tone(TONE_BLACK), FADE_FRAMES]), _cmd(106, [WARP_WAIT_FRAMES]),
             _cmd(201, [0, target, tx, ty, DIRECTIONS[direction], 1]),
             _cmd(223, [_tone(TONE_CLEAR), FADE_FRAMES])]
    return cmds


def _events(doc, path, w, h, tiles, ts, ctx):
    objects = []
    for layer in doc.get("layers", []):
        if layer.get("type") == "objectgroup" and layer.get("name") == EVENT_LAYER:
            objects = sorted(layer.get("objects", []), key=lambda o: o.get("id", 0))
    events = RHash()
    tables = ts.tables()
    for o in objects:
        name = o.get("name") or ""
        where = "%s object %r (id %s)" % (path.name, name, o.get("id"))
        kind = o.get("type") or o.get("class") or ""
        if "gid" in o:
            raise MapBuildError("%s: tile objects are not supported; use a rectangle" % where)
        x, y = int(o.get("x", 0)) // TILE, int(o.get("y", 0)) // TILE
        if not (0 <= x < w and 0 <= y < h):
            raise MapBuildError("%s: at (%d,%d), outside the map" % (where, x, y))
        props = _props(o.get("properties"), where)
        if kind == "spawn":
            if not walkable(tables, tiles, x, y):
                raise MapBuildError("%s: spawn at (%d,%d) is on an impassable tile" % (where, x, y))
            continue
        if kind == "warp":
            page = _page(_warp_commands(props, where, ctx), TRIGGER_PLAYER_TOUCH)
        else:
            raise MapBuildError("%s: unknown object type %r (warp or spawn)" % (where, kind))
        eid = len(events) + 1
        events[eid] = obj("RPG::Event", [("@pages", [page]), ("@name", s(name)), ("@y", y), ("@x", x),
                                         ("@id", eid)])
    return events


# ---------------------------------------------------------------- maps

def map_from_tmj(path, data_dir=None):
    """RubyObject('RPG::Map') for a content/maps/*.tmj file; raises MapBuildError."""
    path = Path(path)
    doc = _read_tmj(path)
    w, h = doc.get("width"), doc.get("height")
    if not (isinstance(w, int) and isinstance(h, int) and w > 0 and h > 0) or doc.get("infinite"):
        raise MapBuildError("%s: needs a fixed positive width and height" % path.name)
    if doc.get("tilewidth", TILE) != TILE or doc.get("tileheight", TILE) != TILE:
        raise MapBuildError("%s: tiles must be 32x32" % path.name)
    ts, firstgid = _tileset_for(doc, path)
    tiles = _tile_layers(doc, path, w, h, ts, firstgid)
    ctx = _Context(path.parent, data_dir or DATA_DIR)
    events = _events(doc, path, w, h, tiles, ts, ctx)
    p = _props(doc.get("properties"), path.name)
    v = {"@bgm": _audio(p.get("bgm", ""), p.get("bgm_volume", 80), p.get("bgm_pitch", 100)),
         "@events": events, "@tileset_id": ts.id,
         "@bgs": _audio(p.get("bgs", ""), p.get("bgs_volume", 80), p.get("bgs_pitch", 100)),
         "@autoplay_bgm": bool(p.get("autoplay_bgm", False)), "@data": tiles.to_userdef(),
         "@autoplay_bgs": bool(p.get("autoplay_bgs", False)), "@height": h,
         "@encounter_step": int(p.get("encounter_step", 30)), "@width": w, "@encounter_list": []}
    return obj("RPG::Map", [(k, v[k]) for k in MAP_IVARS])


def _write_if_changed(path, data):
    if not path.is_file() or path.read_bytes() != data:
        path.write_bytes(data)
        return True
    return False


def _build_tilesets(content_dir, data_dir):
    base_path = data_dir / "Tilesets.rxdata"
    tilesets = loads(base_path.read_bytes())
    out = list(tilesets[:BASE_TILESET_COUNT + 1])
    ours = {}
    for p in sorted((content_dir / "tilesets").glob("*.json")):
        ts = Tileset(p)
        built = ts.to_ruby()
        if 1 <= ts.id <= BASE_TILESET_COUNT:
            if ts.replaces_base:
                out[ts.id] = built
            elif dumps(built) != dumps(tilesets[ts.id]):
                raise MapBuildError("%s: differs from base tileset %d; set replaces_base to change it"
                                    % (p.name, ts.id))
        elif ts.id in ours:
            raise MapBuildError("%s: tileset id %d is used twice" % (p.name, ts.id))
        else:
            ours[ts.id] = built
    for i, tid in enumerate(sorted(ours)):
        if tid != BASE_TILESET_COUNT + 1 + i:
            raise MapBuildError("new tileset ids must run on from %d without gaps (got %s)"
                                % (BASE_TILESET_COUNT + 1, sorted(ours)))
        out.append(ours[tid])
    _write_if_changed(base_path, dumps(out))


def build_all(content_dir=CONTENT_DIR, data_dir=DATA_DIR):
    """Build every content map into data_dir; returns the built map ids."""
    content_dir, data_dir = Path(content_dir), Path(data_dir)
    _build_tilesets(content_dir, data_dir)
    maps = {}
    for p in sorted((content_dir / "maps").glob("*.tmj")):
        mid = map_id_of(p)
        if mid in maps:
            raise MapBuildError("%s: map id %d is also used by %s" % (p.name, mid, maps[mid].name))
        maps[mid] = p
    built = {}
    for mid, p in sorted(maps.items()):
        props = _props(_read_tmj(p).get("properties"), p.name)
        if mid in BASE_MAP_IDS and props.get("replaces_base") is not True:
            raise MapBuildError("%s: map id %d belongs to a base map; set replaces_base to replace it"
                                % (p.name, mid))
        m = map_from_tmj(p, data_dir)
        _write_if_changed(data_dir / ("Map%03d.rxdata" % mid), dumps(m))
        name = props.get("name") or p.stem.split("_", 1)[1].replace("_", " ")
        built[mid] = (name, int(props.get("parent_id", 0)))
    infos_path = data_dir / "MapInfos.rxdata"
    infos = loads(infos_path.read_bytes())
    out = RHash()
    for k, v in infos.items():
        if k in BASE_MAP_IDS:
            out[k] = v
    order = max(v.ivars["@order"] for v in out.values())
    for mid in sorted(built):
        if mid in BASE_MAP_IDS:
            continue
        name, parent = built[mid]
        order += 1
        out[mid] = obj("RPG::MapInfo", [("@scroll_x", 0), ("@name", s(name)), ("@expanded", False),
                                        ("@order", order), ("@scroll_y", 0), ("@parent_id", parent)])
    _write_if_changed(infos_path, dumps(out))
    return sorted(built)


def main():
    try:
        ids = build_all()
    except MapBuildError as e:
        print("map build failed: %s" % e)
        return 1
    print("built %d map(s): %s" % (len(ids), ", ".join("Map%03d" % i for i in ids) or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
