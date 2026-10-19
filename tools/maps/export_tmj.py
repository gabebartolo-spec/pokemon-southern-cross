"""Export a base map to content/maps/<id>_<slug>.tmj and its tileset to content/tilesets/<slug>.json.

    python tools/maps/export_tmj.py <map_id> [--content DIR]

The reverse of build.py, for starting a map from an Essentials one. Tiles only: base events
are not exported. A map whose autotile shapes the builder cannot reproduce (hand-placed
shapes) is refused, so build(export(map)) always equals the base tile data.
"""
import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.maps import autotile, build  # noqa: E402
from tools.rmxp import rpg  # noqa: E402
from tools.rmxp.marshal import loads  # noqa: E402

TILESET_ROW = 8


class ExportError(Exception):
    pass


def slug(text, fallback):
    out = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return out or fallback


def to_json_text(doc, row):
    """JSON with long integer lists written `row` numbers to a line (stable, diff-friendly)."""
    def fmt(v, ind):
        pad, inner = " " * ind, " " * (ind + 2)
        if isinstance(v, dict):
            if not v:
                return "{}"
            flat = json.dumps(v, ensure_ascii=False, separators=(", ", ": "))
            if all(not isinstance(x, (dict, list)) for x in v.values()) and len(flat) + ind < 100:
                return flat
            items = ["%s%s: %s" % (inner, json.dumps(k), fmt(x, ind + 2)) for k, x in v.items()]
            return "{\n" + ",\n".join(items) + "\n" + pad + "}"
        if isinstance(v, list):
            if not v:
                return "[]"
            if all(isinstance(x, int) and not isinstance(x, bool) for x in v) and len(v) > row:
                lines = [", ".join(str(x) for x in v[i:i + row]) for i in range(0, len(v), row)]
                return "[\n" + ",\n".join(inner + ln for ln in lines) + "\n" + pad + "]"
            if all(not isinstance(x, (dict, list)) for x in v):
                return "[" + ", ".join(json.dumps(x, ensure_ascii=False) for x in v) + "]"
            return "[\n" + ",\n".join(inner + fmt(x, ind + 2) for x in v) + "\n" + pad + "]"
        return json.dumps(v, ensure_ascii=False)
    return fmt(doc, 0) + "\n"


def _table(ts, key):
    return rpg.Table.from_userdef(ts.ivars[key]).data


def export_tileset(ts, out_dir):
    """Write RPG::Tileset `ts` as <out_dir>/<slug>.json; returns the path."""
    passages, priorities, terrain = (_table(ts, k) for k in ("@passages", "@priorities", "@terrain_tags"))
    first = autotile.TILESET_FIRST
    names = [n.text for n in ts.ivars["@autotile_names"]]
    autotiles = [{"name": names[k], "passage": passages[48 * (k + 1)],
                  "priority": priorities[48 * (k + 1)], "terrain_tag": terrain[48 * (k + 1)]}
                 for k in range(build.AUTOTILE_SLOTS)]
    doc = {"name": ts.ivars["@name"].text, "tileset_id": ts.ivars["@id"],
           "tileset_name": ts.ivars["@tileset_name"].text, "autotiles": autotiles}
    for k, default in build.TILESET_EXTRAS.items():
        v = ts.ivars["@" + k]
        doc[k] = v.text if isinstance(default, str) else v
    doc["tiles"] = {"passage": passages[first:], "priority": priorities[first:], "terrain_tag": terrain[first:]}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / ("%s.json" % slug(doc["name"], "tileset_%d" % doc["tileset_id"]))
    path.write_text(to_json_text(doc, TILESET_ROW), encoding="utf-8", newline="\n")
    rebuilt = build.Tileset(path).tables()
    if rebuilt != [passages, priorities, terrain]:
        raise ExportError("tileset %d does not round trip" % doc["tileset_id"])
    return path


def _gid(tid, firstgid):
    if tid == 0:
        return 0
    k = autotile.kind_of(tid)
    if k is not None:
        return firstgid + k + 1
    return firstgid + tid - autotile.TILESET_FIRST + build.FIRST_TILESET_LOCAL


def export_map(map_id, content_dir, data_dir=build.DATA_DIR):
    """Write base map `map_id` as a tmj under content_dir/maps; returns the tmj path."""
    data_dir, content_dir = Path(data_dir), Path(content_dir)
    m = loads((data_dir / ("Map%03d.rxdata" % map_id)).read_bytes())
    infos = loads((data_dir / "MapInfos.rxdata").read_bytes())
    tilesets = loads((data_dir / "Tilesets.rxdata").read_bytes())
    ts_path = export_tileset(tilesets[m.ivars["@tileset_id"]], content_dir / "tilesets")
    tiles = rpg.Table.from_userdef(m.ivars["@data"])
    w, h = tiles.xsize, tiles.ysize
    name = infos[map_id].ivars["@name"].text if map_id in infos else "Map %d" % map_id
    layers = [{"id": z + 1, "name": layer, "type": "tilelayer", "width": w, "height": h, "x": 0, "y": 0,
               "opacity": 1, "visible": True,
               "data": [_gid(tiles.get(x, y, z), 1) for y in range(h) for x in range(w)]}
              for z, layer in enumerate(build.TILE_LAYERS)]
    layers.append({"id": 4, "name": build.EVENT_LAYER, "type": "objectgroup", "x": 0, "y": 0,
                   "opacity": 1, "visible": True, "draworder": "topdown", "objects": []})
    bgm, bgs = m.ivars["@bgm"].ivars, m.ivars["@bgs"].ivars
    props = [("name", "string", name), ("bgm", "string", bgm["@name"].text),
             ("bgm_volume", "int", bgm["@volume"]), ("bgm_pitch", "int", bgm["@pitch"]),
             ("autoplay_bgm", "bool", m.ivars["@autoplay_bgm"]), ("bgs", "string", bgs["@name"].text),
             ("bgs_volume", "int", bgs["@volume"]), ("bgs_pitch", "int", bgs["@pitch"]),
             ("autoplay_bgs", "bool", m.ivars["@autoplay_bgs"]),
             ("encounter_step", "int", m.ivars["@encounter_step"])]
    doc = {"type": "map", "version": "1.10", "orientation": "orthogonal", "renderorder": "right-down",
           "infinite": False, "width": w, "height": h, "tilewidth": build.TILE, "tileheight": build.TILE,
           "nextlayerid": 5, "nextobjectid": 1,
           "properties": [{"name": n, "type": t, "value": v} for n, t, v in props],
           "tilesets": [{"firstgid": 1, "source": "../tilesets/%s" % ts_path.name}],
           "layers": layers}
    out = content_dir / "maps" / ("%03d_%s.tmj" % (map_id, slug(name, "map")))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_json_text(doc, w), encoding="utf-8", newline="\n")
    rebuilt = rpg.Table.from_userdef(build.map_from_tmj(out, data_dir).ivars["@data"])
    if rebuilt != tiles:
        bad = sum(a != b for a, b in zip(rebuilt.data, tiles.data))
        out.unlink()
        raise ExportError("Map%03d has %d hand-placed autotile cells the builder cannot reproduce"
                          % (map_id, bad))
    return out


def main(argv):
    if not argv or not argv[0].isdigit():
        print(__doc__)
        return 2
    content = Path(argv[argv.index("--content") + 1]) if "--content" in argv else build.CONTENT_DIR
    try:
        print(export_map(int(argv[0]), content))
    except (ExportError, build.MapBuildError) as e:
        print("export failed: %s" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
