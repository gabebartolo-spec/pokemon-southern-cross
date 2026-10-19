"""Map previews: size, autotile quarters, event markers, sight lines, CLI."""
from pathlib import Path

import pytest
from PIL import Image

from tools.maps import autotile, preview
from tools.rmxp import marshal

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


def test_markers_draw_warp_blue_trainer_red():
    # Map900: Door (8,7) warp, Ben (5,14) facing right with sight 3.
    img = preview.render_map(900, overlays=True)
    plain = preview.render_map(900, overlays=False)
    px = lambda im, cx, cy: im.getpixel((cx * 64 + 25, cy * 64 + 25))  # noqa: E731
    assert px(img, 8, 7) != px(plain, 8, 7)
    b, r = px(img, 8, 7), px(img, 5, 14)
    assert b[2] > b[0] + 40, "warp reads blue"
    assert r[0] > r[2] + 40, "trainer reads red"
    # sight line cell in front of Ben is tinted red against the plain map
    s, p = px(img, 6, 14), px(plain, 6, 14)
    assert s[0] - p[0] > 15 or s[0] > s[2] + 20
