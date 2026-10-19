"""Map previews: size, autotile quarters, event markers, sight lines, CLI."""
from pathlib import Path

import pytest
from PIL import Image

from tools.maps import autotile, build, preview
from tools.rmxp import marshal, rpg

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "game" / "Data"


def map_size(mid):
    m = marshal.loads((DATA / ("Map%03d.rxdata" % mid)).read_bytes())
    return m.ivars["@width"], m.ivars["@height"]


@pytest.mark.parametrize("mid", [900, 2])
def test_preview_size_is_map_tiles_times_64(mid):
    w, h = map_size(mid)
    assert preview.render_map(mid).size == (w * 64, h * 64)


def test_preview_file_keeps_map_area_above_legend(tmp_path):
    w, h = map_size(900)
    assert preview.main(["--out", str(tmp_path), "900"]) == 0
    img = Image.open(tmp_path / "900.png")
    assert img.width == w * 64 and img.height >= h * 64
    assert img.crop((0, 0, w * 64, h * 64)).tobytes() == preview.render_map(900).convert(img.mode).tobytes()


def test_no_args_previews_every_content_map(tmp_path):
    assert preview.main(["--out", str(tmp_path)]) == 0
    assert (tmp_path / "900.png").is_file()


def test_unknown_map_is_an_error(tmp_path, capsys):
    assert preview.main(["--out", str(tmp_path), "999"]) == 1
    assert "999" in capsys.readouterr().out


def test_autotile_cell_is_composed_from_its_quarters(tmp_path):
    # One colour per 16px quarter number 1..48; shape 0 must read quarters 27, 28, 33, 34.
    sheet = Image.new("RGBA", (96, 128))
    for q in range(1, 49):
        c, r = (q - 1) % 6, (q - 1) // 6
        sheet.paste((q * 5, 255 - q * 5, q, 255), (c * 16, r * 16, c * 16 + 16, r * 16 + 16))
    for shape in (0, 46):
        cell = preview.autotile_cell(sheet, shape)
        assert cell.size == (32, 32)
        for i, q in enumerate(autotile.QUARTERS[shape]):
            got = cell.getpixel(((i % 2) * 16 + 8, (i // 2) * 16 + 8))
            assert got == (q * 5, 255 - q * 5, q, 255)


def test_animated_autotile_sheet_uses_first_frame():
    sheet = Image.new("RGBA", (192, 128), (0, 0, 255, 255))
    sheet.paste((255, 0, 0, 255), (0, 0, 96, 128))
    assert preview.autotile_cell(sheet, 0).getpixel((5, 5)) == (255, 0, 0, 255)


def test_single_tile_autotile_fills_every_shape():
    sheet = Image.new("RGBA", (160, 32), (9, 9, 9, 255))
    assert preview.autotile_cell(sheet, 30).getpixel((20, 20)) == (9, 9, 9, 255)


def test_sight_line_stops_at_first_blocked_tile():
    free = lambda x, y: (x, y) != (6, 3)  # noqa: E731
    assert preview.sight_cells(3, 3, 6, 4, free) == [(4, 3), (5, 3)]
    assert preview.sight_cells(3, 3, 8, 2, free) == [(3, 2), (3, 1)]
    edge = lambda x, y: x >= 0 and y >= 0  # noqa: E731
    assert preview.sight_cells(0, 0, 4, 3, edge) == []  # map edge
    assert preview.sight_cells(3, 3, 2, 2, lambda x, y: True) == [(3, 4), (3, 5)]


def test_map900_markers_are_classified():
    kinds = {e["name"]: e["kind"] for e in preview.map_events(preview.load_map(900)[0])}
    assert kinds["Door"] == "warp" and kinds["Trainer(3)"] == "trainer"
    assert kinds["Potion"] == "item" and kinds["Local"] == "npc"
    ben = next(e for e in preview.map_events(preview.load_map(900)[0]) if e["name"] == "Trainer(3)")
    assert (ben["sight"], ben["direction"]) == (3, 6)


GRAPHICS = ROOT / "game" / "Graphics"


def _tile_ids(mid):
    m, ts = preview.load_map(mid)
    return m, ts, rpg.Table.from_userdef(m.ivars["@data"])


def _blend(under, over_rgb, alpha):
    return tuple(round(u * (255 - alpha) / 255 + o * alpha / 255) for u, o in zip(under[:3], over_rgb)) + (255,)


def _near(a, b, tol=1):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def _source_crop(ts, tid):
    src = Image.open(GRAPHICS / "Tilesets" / (ts.ivars["@tileset_name"].text + ".png")).convert("RGBA")
    col, row = (tid - 384) % 8, (tid - 384) // 8
    return src.crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32))


def test_markers_draw_exact_colours_at_known_cells():
    # Marker dots are opaque; sampled off the white direction line. Cells from content/maps/900.
    img = preview.render_map(900)
    at = lambda cx, cy: img.getpixel((cx * 64 + 25, cy * 64 + 25))  # noqa: E731
    events = {e["name"]: e for e in preview.map_events(preview.load_map(900)[0])}
    assert at(events["Door"]["x"], events["Door"]["y"]) == (40, 110, 255, 255)
    assert at(5, 14) == (235, 40, 40, 255) and at(10, 14) == (235, 40, 40, 255)
    assert at(events["Potion"]["x"], events["Potion"]["y"]) == (255, 190, 30, 255)
    assert at(events["Local"]["x"], events["Local"]["y"]) == (170, 70, 220, 255)
    assert at(events["Sign"]["x"], events["Sign"]["y"]) == (200, 200, 200, 255)


def test_sight_tint_is_exactly_on_the_seen_cells():
    # Ben (5,14) faces right, sight 3; Crissy (10,14) faces up, sight 2.
    img, plain = preview.render_map(900), preview.render_map(900, overlays=False)
    corner = lambda im, cx, cy: im.getpixel((cx * 64 + 4, cy * 64 + 58))  # noqa: E731
    for cx, cy in [(6, 14), (7, 14), (8, 14), (10, 13), (10, 12)]:
        assert _near(corner(img, cx, cy), _blend(corner(plain, cx, cy), (235, 40, 40), 95)), (cx, cy)
    for cx, cy in [(9, 14), (10, 11), (4, 14), (10, 15)]:  # one past each line, and behind
        assert corner(img, cx, cy) == corner(plain, cx, cy), (cx, cy)


def test_sight_cells_on_built_tables_stop_at_the_blocked_tile():
    m, ts, tiles = _tile_ids(900)
    tables = preview._tables(ts)
    w, h = m.ivars["@width"], m.ivars["@height"]

    def free(x, y):
        return 0 <= x < w and 0 <= y < h and build.walkable(tables, tiles, x, y)

    assert not build.walkable(tables, tiles, 10, 11)  # blocked cell above Crissy
    assert preview.sight_cells(10, 14, 8, 5, free) == [(10, 13), (10, 12)]  # stops before (10,11)
    assert preview.sight_cells(5, 14, 6, 3, free) == [(6, 14), (7, 14), (8, 14)]
    assert preview.sight_cells(0, 5, 4, 3, free) == []  # map edge


def _fake_map(w, h, layers, tileset_name, autotile_names):
    data = rpg.Table(w, h, 3)
    for z, row in enumerate(layers):
        for x, tid in enumerate(row):
            data.set(x, 0, z, tid)
    m = marshal.RubyObject("RPG::Map", {"@width": w, "@height": h, "@data": data.to_userdef()})
    ts = marshal.RubyObject("RPG::Tileset", {
        "@tileset_name": marshal.RString.utf8(tileset_name),
        "@autotile_names": [marshal.RString.utf8(n) for n in autotile_names]})
    return m, ts


def test_layers_draw_in_order_ground_then_mid_then_top(tmp_path):
    # Tile 0 opaque red; tile 1 green on its left half only; tile 2 blue on its top 8 rows only.
    (tmp_path / "Tilesets").mkdir()
    sheet = Image.new("RGBA", (256, 32), (0, 0, 0, 0))
    sheet.paste((255, 0, 0, 255), (0, 0, 32, 32))
    sheet.paste((0, 255, 0, 255), (32, 0, 48, 32))
    sheet.paste((0, 0, 255, 255), (64, 0, 96, 8))
    sheet.save(tmp_path / "Tilesets" / "T.png")
    m, ts = _fake_map(1, 1, [[384], [385], [386]], "T", [""] * 7)
    img = preview._tile_image(m, ts, tmp_path)
    assert img.size == (64, 64)
    assert img.getpixel((50, 40)) == (255, 0, 0, 255)  # only the ground is there
    assert img.getpixel((10, 40)) == (0, 255, 0, 255)  # mid over ground
    assert img.getpixel((10, 4)) == (0, 0, 255, 255)   # top over mid
    assert img.getpixel((50, 4)) == (0, 0, 255, 255)   # top over ground


def test_map900_roof_cell_is_layer_1_over_layer_0():
    # Map900 (7,3): ground tile 401, mid tile 1960 (has see-through pixels).
    m, ts, tiles = _tile_ids(900)
    below, above = tiles.get(7, 3, 0), tiles.get(7, 3, 1)
    assert below and above and not tiles.get(7, 3, 2)
    right = _source_crop(ts, below).copy()
    right.alpha_composite(_source_crop(ts, above))
    wrong = _source_crop(ts, above).copy()
    wrong.alpha_composite(_source_crop(ts, below))
    assert right.tobytes() != wrong.tobytes() and right.tobytes() != _source_crop(ts, below).tobytes()
    got = preview.render_map(900, overlays=False).crop((7 * 64, 3 * 64, 8 * 64, 4 * 64))
    assert got.tobytes() == right.resize((64, 64), Image.NEAREST).tobytes()


@pytest.mark.parametrize("cell", [(6, 14), (7, 14), (8, 14), (3, 3)])
def test_tileset_cell_matches_source_png_crop(cell):
    x, y = cell
    m, ts, tiles = _tile_ids(900)
    tid = tiles.get(x, y, 0)
    assert tid >= 384 and not tiles.get(x, y, 1) and not tiles.get(x, y, 2)
    want = _source_crop(ts, tid).resize((64, 64), Image.NEAREST)
    got = preview.render_map(900, overlays=False).crop((x * 64, y * 64, x * 64 + 64, y * 64 + 64))
    assert got.tobytes() == want.tobytes()
    # an off-by-one index (next tile along, or one row down) would be a different picture
    for off in (1, 8, -1, -8):
        other = _source_crop(ts, tid + off).resize((64, 64), Image.NEAREST)
        assert other.tobytes() != want.tobytes()


def test_map900_flowers_autotile_cell_matches_its_sheet():
    # Map900 (7,12) is autotile id 274: slot 4 by kind_of, the one-tile sheet Flowers1.
    m, ts, tiles = _tile_ids(900)
    tid = tiles.get(7, 12, 0)
    assert autotile.kind_of(tid) == 4 and not tiles.get(7, 12, 1) and not tiles.get(7, 12, 2)
    name = ts.ivars["@autotile_names"][autotile.kind_of(tid)].text
    assert name == "Flowers1"
    sheet = Image.open(GRAPHICS / "Autotiles" / (name + ".png")).convert("RGBA")
    want = sheet.crop((0, 0, 32, 32)).resize((64, 64), Image.NEAREST)
    got = preview.render_map(900, overlays=False).crop((7 * 64, 12 * 64, 8 * 64, 13 * 64))
    assert got.tobytes() == want.tobytes()


def test_autotile_slot_and_shape_come_from_the_tile_id(tmp_path):
    # Sheets A (slot 0) and B (slot 1) differ; id 48+3 is slot 0 shape 3, id 96+3 slot 1 shape 3.
    (tmp_path / "Tilesets").mkdir()
    (tmp_path / "Autotiles").mkdir()
    for name, shade in (("A", 0), ("B", 100)):
        sheet = Image.new("RGBA", (96, 128))
        for q in range(1, 49):
            c, r = (q - 1) % 6, (q - 1) // 6
            sheet.paste((q * 2 + shade, 10, shade, 255), (c * 16, r * 16, c * 16 + 16, r * 16 + 16))
        sheet.save(tmp_path / "Autotiles" / (name + ".png"))
    Image.new("RGBA", (256, 32)).save(tmp_path / "Tilesets" / "T.png")
    m, ts = _fake_map(2, 1, [[48 + 3, 96 + 3], [0, 0], [0, 0]], "T", ["A", "B", "", "", "", "", ""])
    img = preview._tile_image(m, ts, tmp_path)
    for cell, shade in ((0, 0), (1, 100)):
        for i, q in enumerate(autotile.QUARTERS[3]):
            px = img.getpixel((cell * 64 + (i % 2) * 32 + 16, (i // 2) * 32 + 16))
            assert px == (q * 2 + shade, 10, shade, 255), (cell, i)
