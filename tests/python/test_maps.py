"""Map pipeline: autotile shapes, tmj -> RPG::Map, export round trip, MapInfos/Tilesets updates."""
import json
import shutil
from pathlib import Path

import pytest

from tools.maps import autotile, build, export_tmj
from tools.rmxp import marshal, rpg

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "game" / "Data"

# Base maps whose every autotile cell follows the neighbour rule (RMXP editor output, untouched).
CLEAN_MAPS = [2, 5, 7, 21, 23, 28, 31, 35, 52]
# Base maps with hand-placed autotile shapes (coastlines, sea-deep borders, stale shapes the
# editor never re-shaped). Value: number of autotile cells the rule cannot reproduce. Measured
# 2026-10-19; any change means the rule changed. See docs/MAPS.md "Autotiles".
HAND_SHAPED = {39: 24, 40: 22, 41: 414, 44: 332, 45: 209, 68: 20, 69: 444, 70: 17, 71: 12,
               72: 68, 73: 68}


def load(path):
    return marshal.loads(Path(path).read_bytes())


def tiles_of(m):
    return rpg.Table.from_userdef(m.ivars["@data"])


# ---------------------------------------------------------------- autotile

def test_autotile_isolated_cell_is_shape_46():
    # The brief named this "shape 0"; RMXP's own layout and every base map say 46 (see docs).
    assert autotile.resolve([[None, None, None], [None, 1, None], [None, None, None]], 1, 1) == 46


def test_autotile_full_surround_is_shape_0():
    assert autotile.resolve([[1, 1, 1], [1, 1, 1], [1, 1, 1]], 1, 1) == 0


def test_autotile_map_edge_counts_as_same():
    assert autotile.resolve([[1]], 0, 0) == 0


def test_autotile_every_neighbourhood_has_a_shape():
    shapes = set()
    for mask in range(256):
        grid = [[1 if mask >> (3 * y + x - (1 if 3 * y + x > 4 else 0)) & 1 else None
                 for x in range(3)] for y in range(3)]
        grid[1][1] = 1
        shapes.add(autotile.resolve(grid, 1, 1))
    assert shapes == set(range(47))


def test_autotile_other_kind_does_not_connect():
    assert autotile.resolve([[2, 2, 2], [2, 1, 2], [2, 2, 2]], 1, 1) == 46


def _mismatches(m):
    t = tiles_of(m)
    bad = total = 0
    for z in range(3):
        grid = [[autotile.kind_of(t.get(x, y, z)) for x in range(t.xsize)] for y in range(t.ysize)]
        for y in range(t.ysize):
            for x in range(t.xsize):
                if grid[y][x] is None:
                    continue
                total += 1
                bad += autotile.resolve(grid, x, y) != t.get(x, y, z) % 48
    return bad, total


def test_autotile_matches_base_maps():
    clean_cells = 0
    for mid in CLEAN_MAPS:
        bad, total = _mismatches(load(DATA / ("Map%03d.rxdata" % mid)))
        assert bad == 0, mid
        clean_cells += total
    assert clean_cells > 300
    for mid, expected in HAND_SHAPED.items():
        assert _mismatches(load(DATA / ("Map%03d.rxdata" % mid)))[0] == expected, mid
    others = set(build.BASE_MAP_IDS) - set(CLEAN_MAPS) - set(HAND_SHAPED)
    for mid in others:  # maps with no autotile cells at all
        assert _mismatches(load(DATA / ("Map%03d.rxdata" % mid))) == (0, 0), mid


# ---------------------------------------------------------------- tmj fixtures

def _tileset_json(tmp):
    src = ROOT / "content" / "tilesets" / "outside.json"
    dst = tmp / "content" / "tilesets" / "outside.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)
    return dst


def _tmj(tmp, name, w=5, h=4, objects=(), props=(), fill=10, ground=None):
    """A small map on the Outside tileset (firstgid 1). gid 10 = local 9 = RMXP 385, walkable."""
    _tileset_json(tmp)
    data = ground if ground is not None else [fill] * (w * h)
    layers = [{"type": "tilelayer", "name": n, "width": w, "height": h, "x": 0, "y": 0,
               "data": d, "opacity": 1, "visible": True, "id": i + 1}
              for i, (n, d) in enumerate([("ground", data), ("mid", [0] * (w * h)), ("top", [0] * (w * h))])]
    layers.append({"type": "objectgroup", "name": "events", "id": 4, "objects": list(objects)})
    doc = {"type": "map", "orientation": "orthogonal", "renderorder": "right-down", "infinite": False,
           "width": w, "height": h, "tilewidth": 32, "tileheight": 32,
           "tilesets": [{"firstgid": 1, "source": "../tilesets/outside.json"}],
           "properties": list(props), "layers": layers}
    p = tmp / "content" / "maps" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


def _obj(oid, name, typ, x, y, **props):
    plist = [{"name": k, "type": "int" if isinstance(v, int) else "string", "value": v}
             for k, v in props.items()]
    return {"id": oid, "name": name, "type": typ, "x": x * 32, "y": y * 32, "width": 32, "height": 32,
            "properties": plist}


def test_built_map_dimensions_match_tmj(tmp_path):
    p = _tmj(tmp_path, "901_small.tmj", w=7, h=5)
    m = build.map_from_tmj(p)
    t = tiles_of(m)
    assert m.cls == "RPG::Map" and (m.ivars["@width"], m.ivars["@height"]) == (7, 5)
    assert (t.xsize, t.ysize, t.zsize) == (7, 5, 3)
    assert t.get(0, 0, 0) == 385 and t.get(0, 0, 1) == 0


def test_built_map_uses_base_ivar_order(tmp_path):
    p = _tmj(tmp_path, "901_small.tmj", objects=[_obj(1, "Gate", "warp", 1, 1, target_map=2,
                                                         target_x=8, target_y=8)])
    m = build.map_from_tmj(p)
    base = load(DATA / "Map002.rxdata")
    assert list(m.ivars) == list(base.ivars) == build.MAP_IVARS
    ev = m.ivars["@events"][1]
    assert list(ev.ivars) == ["@pages", "@name", "@y", "@x", "@id"]
    assert list(ev.ivars["@pages"][0].ivars) == build.PAGE_IVARS
    assert marshal.loads(marshal.dumps(m)).cls == "RPG::Map"


def test_warp_builds_transfer_event(tmp_path):
    p = _tmj(tmp_path, "901_small.tmj", objects=[_obj(3, "Gate", "warp", 2, 1, target_map=2,
                                                         target_x=8, target_y=8, direction="up")])
    ev = build.map_from_tmj(p).ivars["@events"][1]
    assert (ev.ivars["@x"], ev.ivars["@y"], ev.ivars["@name"].text) == (2, 1, "Gate")
    page = ev.ivars["@pages"][0]
    assert page.ivars["@trigger"] == 1
    codes = [(c.ivars["@code"], c.ivars["@parameters"]) for c in page.ivars["@list"]]
    assert (201, [0, 2, 8, 8, 8, 1]) in codes and codes[-1] == (0, [])


def test_warp_target_must_exist(tmp_path):
    p = _tmj(tmp_path, "901_small.tmj", objects=[_obj(1, "To nowhere", "warp", 1, 1, target_map=999,
                                                         target_x=1, target_y=1)])
    with pytest.raises(build.MapBuildError) as e:
        build.map_from_tmj(p)
    assert "901_small.tmj" in str(e.value) and "To nowhere" in str(e.value)
    p = _tmj(tmp_path, "901_small.tmj", objects=[_obj(1, "Off the edge", "warp", 1, 1, target_map=2,
                                                         target_x=32, target_y=0)])
    with pytest.raises(build.MapBuildError) as e:
        build.map_from_tmj(p)
    assert "901_small.tmj" in str(e.value) and "Off the edge" in str(e.value)


def test_warp_to_another_content_map(tmp_path):
    _tmj(tmp_path, "902_other.tmj", w=3, h=3)
    ok = _tmj(tmp_path, "901_small.tmj", objects=[_obj(1, "Next", "warp", 0, 0, target_map=902,
                                                          target_x=2, target_y=2)])
    build.map_from_tmj(ok)
    bad = _tmj(tmp_path, "901_small.tmj", objects=[_obj(1, "Next", "warp", 0, 0, target_map=902,
                                                           target_x=3, target_y=2)])
    with pytest.raises(build.MapBuildError):
        build.map_from_tmj(bad)


def test_impassable_spawn_rejected(tmp_path):
    ground = [10] * 20
    ground[1 * 5 + 2] = 9  # gid 9 = local 8 = RMXP 384, passage 15 (blocked)
    p = _tmj(tmp_path, "901_small.tmj", ground=ground, objects=[_obj(1, "Start", "spawn", 2, 1)])
    with pytest.raises(build.MapBuildError) as e:
        build.map_from_tmj(p)
    assert "Start" in str(e.value) and "901_small.tmj" in str(e.value)
    p = _tmj(tmp_path, "901_small.tmj", ground=ground, objects=[_obj(1, "Start", "spawn", 3, 1)])
    assert build.map_from_tmj(p).ivars["@events"] == {}


def test_unknown_object_type_rejected(tmp_path):
    p = _tmj(tmp_path, "901_small.tmj", objects=[_obj(1, "Thing", "teleporter", 1, 1)])
    with pytest.raises(build.MapBuildError):
        build.map_from_tmj(p)


def test_flipped_tiles_rejected(tmp_path):
    p = _tmj(tmp_path, "901_small.tmj", fill=10 | 0x80000000)
    with pytest.raises(build.MapBuildError):
        build.map_from_tmj(p)


def test_autotile_key_expands_to_shapes(tmp_path):
    ground = [10] * 20
    for x, y in [(1, 1), (2, 1), (3, 1), (1, 2), (2, 2), (3, 2)]:
        ground[y * 5 + x] = 2  # gid 2 = local 1 = autotile slot 0 (Sea)
    t = tiles_of(build.map_from_tmj(_tmj(tmp_path, "901_small.tmj", ground=ground)))
    assert all(48 <= t.get(x, y, 0) < 96 for x, y in [(1, 1), (2, 2)])
    assert t.get(2, 1, 0) == 48 + autotile.resolve(
        [[None] * 5, [None, 0, 0, 0, None], [None, 0, 0, 0, None], [None] * 5], 2, 1)


# ---------------------------------------------------------------- export round trip

@pytest.mark.parametrize("mid", CLEAN_MAPS)
def test_build_of_export_equals_base_tiles(tmp_path, mid):
    base = load(DATA / ("Map%03d.rxdata" % mid))
    tmj = export_tmj.export_map(mid, tmp_path / "content", data_dir=DATA)
    built = build.map_from_tmj(tmj, data_dir=DATA)
    assert tiles_of(built) == tiles_of(base)
    for k in ("@width", "@height", "@tileset_id", "@encounter_step", "@autoplay_bgm", "@autoplay_bgs"):
        assert built.ivars[k] == base.ivars[k], k


def test_export_refuses_hand_shaped_map(tmp_path):
    with pytest.raises(export_tmj.ExportError):
        export_tmj.export_map(41, tmp_path / "content", data_dir=DATA)


def test_tileset_json_reproduces_every_base_tileset(tmp_path):
    tilesets = load(DATA / "Tilesets.rxdata")
    for ts in tilesets[1:]:
        path = export_tmj.export_tileset(ts, tmp_path)
        rebuilt = build.tileset_from_json(path)
        assert marshal.dumps(rebuilt) == marshal.dumps(ts), ts.ivars["@id"]


# ---------------------------------------------------------------- build_all

def _data_copy(tmp):
    d = tmp / "Data"
    d.mkdir()
    for p in DATA.glob("Map*.rxdata"):
        shutil.copy(p, d / p.name)
    shutil.copy(DATA / "Tilesets.rxdata", d / "Tilesets.rxdata")
    return d


def test_build_all_is_deterministic_and_keeps_base_entries(tmp_path):
    data = _data_copy(tmp_path)
    _tmj(tmp_path, "901_small.tmj", props=[{"name": "name", "type": "string", "value": "Test Field"}])
    base_infos = load(DATA / "MapInfos.rxdata")
    build.build_all(tmp_path / "content", data)
    first = {p.name: p.read_bytes() for p in data.iterdir()}
    build.build_all(tmp_path / "content", data)
    assert first == {p.name: p.read_bytes() for p in data.iterdir()}
    infos = load(data / "MapInfos.rxdata")
    for k, v in base_infos.items():
        if k in build.BASE_MAP_IDS:
            assert marshal.dumps(infos[k]) == marshal.dumps(v), k
    assert infos[901].ivars["@name"].raw == b"Test Field"
    assert list(infos[901].ivars) == list(base_infos[2].ivars)
    assert (DATA / "Tilesets.rxdata").read_bytes() == (data / "Tilesets.rxdata").read_bytes()
    for p in DATA.glob("Map0*.rxdata"):
        assert (data / p.name).read_bytes() == p.read_bytes(), p.name


def test_build_all_drops_removed_maps_from_mapinfos(tmp_path):
    data = _data_copy(tmp_path)
    p = _tmj(tmp_path, "901_small.tmj")
    build.build_all(tmp_path / "content", data)
    p.unlink()
    build.build_all(tmp_path / "content", data)
    assert 901 not in load(data / "MapInfos.rxdata")


def test_base_id_collision_rejected(tmp_path):
    data = _data_copy(tmp_path)
    p = _tmj(tmp_path, "002_clash.tmj")
    with pytest.raises(build.MapBuildError):
        build.build_all(tmp_path / "content", data)
    p.unlink()
    _tmj(tmp_path, "002_clash.tmj", props=[{"name": "replaces_base", "type": "bool", "value": True}])
    build.build_all(tmp_path / "content", data)
    assert tiles_of(load(data / "Map002.rxdata")).xsize == 5
    assert marshal.dumps(load(data / "MapInfos.rxdata")[2]) == marshal.dumps(load(DATA / "MapInfos.rxdata")[2])


def test_new_tileset_written_to_tilesets(tmp_path):
    data = _data_copy(tmp_path)
    ts_path = _tileset_json(tmp_path)
    doc = json.loads(ts_path.read_text(encoding="utf-8"))
    doc["tileset_id"], doc["name"] = 26, "Southern grass"
    (ts_path.parent / "southern.json").write_text(json.dumps(doc), encoding="utf-8")
    build.build_all(tmp_path / "content", data)
    tilesets = load(data / "Tilesets.rxdata")
    assert len(tilesets) == 27 and tilesets[26].ivars["@name"].text == "Southern grass"
    assert list(tilesets[26].ivars) == list(tilesets[1].ivars)
    assert marshal.dumps(tilesets[1]) == marshal.dumps(load(DATA / "Tilesets.rxdata")[1])


def test_committed_data_matches_content(tmp_path):
    """Rule 4: game/Data is build output; rebuilding content/ must reproduce the committed files."""
    data = tmp_path / "Data"
    data.mkdir()
    for p in DATA.glob("Map*.rxdata"):
        shutil.copy(p, data / p.name)
    shutil.copy(DATA / "Tilesets.rxdata", data / "Tilesets.rxdata")
    build.build_all(ROOT / "content", data)
    for p in data.iterdir():
        assert p.read_bytes() == (DATA / p.name).read_bytes(), p.name


# ---------------------------------------------------------------- events: cross references (Task 10)

def _raises(p, *names):
    with pytest.raises(build.MapBuildError) as e:
        build.map_from_tmj(p)
    for n in names:
        assert n in str(e.value), (n, str(e.value))
    return str(e.value)


def test_warp_arrival_must_be_walkable_on_content_map(tmp_path):
    ground = [10] * 9
    ground[2 * 3 + 2] = 9  # gid 9 = RMXP 384, passage 15
    _tmj(tmp_path, "902_other.tmj", w=3, h=3, ground=ground)
    ok = _tmj(tmp_path, "901_small.tmj", objects=[_obj(1, "Next", "warp", 0, 0, target_map=902,
                                                          target_x=1, target_y=1)])
    assert len(build.map_from_tmj(ok).ivars["@events"]) == 1
    bad = _tmj(tmp_path, "901_small.tmj", objects=[_obj(1, "Into the wall", "warp", 0, 0, target_map=902,
                                                           target_x=2, target_y=2)])
    assert "not walkable" in _raises(bad, "901_small.tmj", "Into the wall")


def test_warp_arrival_must_be_walkable_on_base_map(tmp_path):
    ok = _tmj(tmp_path, "901_small.tmj", objects=[_obj(1, "Home", "warp", 0, 0, target_map=2,
                                                          target_x=8, target_y=7)])
    build.map_from_tmj(ok)  # onto the Lappet Town door, as base Map003's exit does
    bad = _tmj(tmp_path, "901_small.tmj", objects=[_obj(1, "Tower wall", "warp", 0, 0, target_map=59,
                                                           target_x=2, target_y=8)])
    _raises(bad, "901_small.tmj", "Tower wall", "not walkable")


# Base warps whose arrival cell is a wall: Battle Frontier cutscene starts (the player is moved
# off by a script). Every other base warp lands on a cell the walkable rule accepts.
SCRIPTED_ARRIVALS = {(59, 2, 8), (63, 4, 9), (64, 2, 9)}


def test_base_warps_land_on_walkable_cells():
    ctx = build._Context(ROOT / "content" / "maps", DATA)
    checked = 0
    for mid in sorted(build.BASE_MAP_IDS):
        for ev in load(DATA / ("Map%03d.rxdata" % mid)).ivars["@events"].values():
            for page in ev.ivars["@pages"]:
                for c in page.ivars["@list"]:
                    p = c.ivars["@parameters"]
                    if c.ivars["@code"] != 201 or p[0] != 0 or ctx.size(p[1]) is None:
                        continue
                    checked += 1
                    assert ctx.walkable(p[1], p[2], p[3]) == (tuple(p[1:4]) not in SCRIPTED_ARRIVALS), (mid, p)
    assert checked == 168


@pytest.mark.parametrize("source", ["../maps/outside.json", "../../tilesets/outside.json", "../tilesets/missing.json",
                                    "../tilesets/outside.tsx"])
def test_tileset_source_must_be_in_content_tilesets(tmp_path, source):
    p = _tmj(tmp_path, "901_small.tmj")
    shutil.copy(tmp_path / "content" / "tilesets" / "outside.json", tmp_path / "content" / "maps" / "outside.json")
    (tmp_path / "tilesets").mkdir()
    shutil.copy(tmp_path / "content" / "tilesets" / "outside.json", tmp_path / "tilesets" / "outside.json")
    doc = json.loads(p.read_text(encoding="utf-8"))
    doc["tilesets"][0]["source"] = source
    p.write_text(json.dumps(doc), encoding="utf-8")
    _raises(p, "901_small.tmj", "content/tilesets")


@pytest.mark.parametrize("width", ["5", None, 0, True, 2.5])
def test_malformed_size_in_any_content_map_rejected(tmp_path, width):
    other = _tmj(tmp_path, "902_other.tmj", w=3, h=3)
    doc = json.loads(other.read_text(encoding="utf-8"))
    doc["width"] = width
    other.write_text(json.dumps(doc), encoding="utf-8")
    p = _tmj(tmp_path, "901_small.tmj")
    _raises(p, "902_other.tmj", "width and height")
    p.write_text(json.dumps(doc), encoding="utf-8")
    _raises(p, "901_small.tmj", "width and height")


@pytest.mark.parametrize("obj, fault", [
    (_obj(1, "Ball", "item", 1, 1, item="MADEUPITEM"), "items.txt"),
    (_obj(1, "Kid", "trainer", 1, 1, trainer="YOUNGSTER,Nobody", sight=2, intro="Oi!"), "trainers.txt"),
    (_obj(1, "Kid", "trainer", 1, 1, trainer="NOTATYPE,Ben", sight=2, intro="Oi!"), "trainers.txt"),
    (_obj(1, "Bloke", "npc", 1, 1, graphic="NPC 99", text="G'day."), "Graphics/Characters"),
])
def test_event_cross_references_checked(tmp_path, obj, fault):
    _raises(_tmj(tmp_path, "901_small.tmj", objects=[obj]), "901_small.tmj", fault)


def test_one_event_of_each_type_builds(tmp_path):
    objs = [_obj(1, "Gate", "warp", 0, 0, target_map=2, target_x=8, target_y=7),
            _obj(2, "Sign", "sign", 1, 0, text="Route 1"),
            _obj(3, "Bloke", "npc", 2, 0, graphic="NPC 01", text="G'day."),
            _obj(4, "Ball", "item", 3, 0, item="POTION"),
            _obj(5, "Kid", "trainer", 4, 0, trainer="YOUNGSTER,Ben", sight=2, intro="Oi!"),
            _obj(6, "Check", "script", 0, 1, script="pbHealAll")]
    evs = build.map_from_tmj(_tmj(tmp_path, "901_small.tmj", objects=objs)).ivars["@events"]
    assert [evs[i].ivars["@name"].text for i in sorted(evs)] == ["Gate", "Sign", "Bloke", "Ball", "Trainer(2)",
                                                                 "Check"]
    assert sorted(evs) == [1, 2, 3, 4, 5, 6] and all(evs[i].ivars["@id"] == i for i in evs)


def test_trainer_version_checked_against_pbs(tmp_path):
    ok = _obj(1, "Jeff", "trainer", 1, 1, trainer="CAMPER,Jeff,1", sight=2, intro="Rematch!")
    build.map_from_tmj(_tmj(tmp_path, "901_small.tmj", objects=[ok]))
    bad = _obj(1, "Jeff", "trainer", 1, 1, trainer="CAMPER,Jeff,7", sight=2, intro="Rematch!")
    _raises(_tmj(tmp_path, "901_small.tmj", objects=[bad]), "901_small.tmj", "trainers.txt")
