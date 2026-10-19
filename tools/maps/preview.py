"""Preview PNGs of built maps, drawn from the data the game will load.

    python tools/maps/preview.py [--out DIR] [map_id ...]

No ids = every content map in content/maps. An id may also be a base Essentials map (2 = Lappet
Town). Writes <out>/<map_id>.png (default out/previews, gitignored): the map at 2x (width*64 by
height*64, nearest-neighbour from native 32px tiles), then a legend strip below it.

Rendered from game/Data/MapNNN.rxdata + Tilesets.rxdata and the tileset / autotile PNGs, not from
the tmj, so it shows what the game draws: the 3 layers in order, tileset tiles (id - 384, 8 per
row), autotiles composed from 16px quarters by the shape table in autotile.py. Overlays: warps
blue, trainers red with their sight line (n tiles in the facing direction, stopping at the first
tile the player cannot walk on), item balls amber, people violet, signs grey.
Needs Pillow (dev-only, see docs/LICENSING_REGISTER.md).
"""
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from tools.maps import autotile, build  # noqa: E402
from tools.rmxp import rpg  # noqa: E402
from tools.rmxp.marshal import loads  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "game" / "Data"
GRAPHICS_DIR = ROOT / "game" / "Graphics"
DEFAULT_OUT = ROOT / "out" / "previews"

TILE, SCALE = 32, 2
CELL = TILE * SCALE  # 64 px per map tile in the preview
ITEM_BALL_GRAPHIC = "Object ball"
TRANSFER_CODE, TEXT_CODE = 201, 101
TRIGGER_ACTION = 0
DIRECTION_STEP = {2: (0, 1), 4: (-1, 0), 6: (1, 0), 8: (0, -1)}
TRAINER_NAME = re.compile(r"^Trainer\((\d+)\)$")

# kind -> (RGB, legend label)
KINDS = {"warp": ((40, 110, 255), "Warp"), "trainer": ((235, 40, 40), "Trainer"),
         "item": ((255, 190, 30), "Item ball"), "npc": ((170, 70, 220), "Person"),
         "sign": ((200, 200, 200), "Sign")}
SIGHT_RGB = (235, 40, 40)


# ---------------------------------------------------------------- loading

def load_map(map_id, data_dir=DATA_DIR):
    """(RPG::Map, RPG::Tileset) from game/Data; raises FileNotFoundError for an unknown map."""
    data_dir = Path(data_dir)
    path = data_dir / ("Map%03d.rxdata" % map_id)
    if not path.is_file():
        raise FileNotFoundError("Map%03d.rxdata not found in %s" % (map_id, data_dir))
    m = loads(path.read_bytes())
    tilesets = loads((data_dir / "Tilesets.rxdata").read_bytes())
    return m, tilesets[m.ivars["@tileset_id"]]


def _tables(ts):
    return tuple(rpg.Table.from_userdef(ts.ivars[k]).data
                 for k in ("@passages", "@priorities", "@terrain_tags"))


# ---------------------------------------------------------------- tiles

def autotile_cell(sheet, shape):
    """The 32x32 cell of RMXP autotile shape 0..47 from an autotile PNG.

    A 96x128 sheet is 6x8 quarters of 16px; wider sheets are animation frames (the first is
    used); a sheet one tile high is a single tile repeated for every shape (Flowers1).
    """
    if sheet.height <= TILE:
        return sheet.crop((0, 0, TILE, TILE))
    cell = Image.new("RGBA", (TILE, TILE))
    for i, q in enumerate(autotile.QUARTERS[shape]):
        c, r = (q - 1) % 6, (q - 1) // 6
        cell.paste(sheet.crop((c * 16, r * 16, c * 16 + 16, r * 16 + 16)),
                   ((i % 2) * 16, (i // 2) * 16))
    return cell


class _Art:
    """Tileset and autotile PNGs of one tileset, and a cache of drawn cells."""

    def __init__(self, ts, graphics_dir):
        g = Path(graphics_dir)
        name = ts.ivars["@tileset_name"].text
        self.tiles = Image.open(g / "Tilesets" / (name + ".png")).convert("RGBA") if name else None
        self.sheets = []
        for n in ts.ivars["@autotile_names"]:
            f = g / "Autotiles" / (n.text + ".png")
            self.sheets.append(Image.open(f).convert("RGBA") if n.text and f.is_file() else None)
        self.cache = {}

    def cell(self, tid):
        if tid not in self.cache:
            self.cache[tid] = self._draw(tid)
        return self.cache[tid]

    def _draw(self, tid):
        if tid >= autotile.TILESET_FIRST:
            local = tid - autotile.TILESET_FIRST
            sx, sy = (local % 8) * TILE, (local // 8) * TILE
            if self.tiles is None or sy + TILE > self.tiles.height:
                return None
            return self.tiles.crop((sx, sy, sx + TILE, sy + TILE))
        k = autotile.kind_of(tid)
        if k is None or self.sheets[k] is None:
            return None
        return autotile_cell(self.sheets[k], tid % 48)


def _tile_image(m, ts, graphics_dir):
    w, h = m.ivars["@width"], m.ivars["@height"]
    data = rpg.Table.from_userdef(m.ivars["@data"])
    art = _Art(ts, graphics_dir)
    img = Image.new("RGBA", (w * TILE, h * TILE), (0, 0, 0, 255))
    for z in range(3):
        for y in range(h):
            for x in range(w):
                tid = data.get(x, y, z)
                cell = art.cell(tid) if tid else None
                if cell is not None:
                    img.alpha_composite(cell, (x * TILE, y * TILE))
    return img.resize((w * CELL, h * CELL), Image.NEAREST)


# ---------------------------------------------------------------- events

def sight_cells(x, y, direction, sight, free):
    """Cells a trainer at (x, y) sees: up to `sight` tiles in `direction`, stopping before the
    first cell where free(x, y) is False (a wall, water, the map edge)."""
    dx, dy = DIRECTION_STEP[direction]
    out = []
    for i in range(1, sight + 1):
        cx, cy = x + dx * i, y + dy * i
        if not free(cx, cy):
            break
        out.append((cx, cy))
    return out


def map_events(m):
    """One dict per event: name, kind (warp trainer item npc sign), x, y, direction, sight."""
    out = []
    for e in m.ivars["@events"].values():
        if not e.ivars["@pages"]:
            continue
        name = e.ivars["@name"].text
        page = e.ivars["@pages"][0]
        g = page.ivars["@graphic"].ivars
        char = g["@character_name"].text
        codes = {c.ivars["@code"] for c in page.ivars["@list"]}
        t = TRAINER_NAME.match(name)
        sight = int(t.group(1)) if t else 0
        if t:
            kind = "trainer"
        elif TRANSFER_CODE in codes:
            kind = "warp"
        elif char == ITEM_BALL_GRAPHIC:
            kind = "item"
        elif char:
            kind = "npc"
        elif page.ivars["@trigger"] == TRIGGER_ACTION and TEXT_CODE in codes:
            kind = "sign"
        else:
            continue
        out.append({"name": name, "kind": kind, "x": e.ivars["@x"], "y": e.ivars["@y"],
                    "direction": g["@direction"], "sight": sight})
    return out


def _overlay(img, m, ts):
    w, h = m.ivars["@width"], m.ivars["@height"]
    tables, tiles = _tables(ts), rpg.Table.from_userdef(m.ivars["@data"])

    def free(x, y):
        return 0 <= x < w and 0 <= y < h and build.walkable(tables, tiles, x, y)

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    events = map_events(m)
    for e in events:
        if e["kind"] == "trainer" and e["direction"] in DIRECTION_STEP:
            for cx, cy in sight_cells(e["x"], e["y"], e["direction"], e["sight"], free):
                d.rectangle((cx * CELL, cy * CELL, cx * CELL + CELL - 1, cy * CELL + CELL - 1),
                            fill=SIGHT_RGB + (95,))
    for e in events:
        rgb = KINDS[e["kind"]][0]
        x0, y0 = e["x"] * CELL, e["y"] * CELL
        d.rectangle((x0, y0, x0 + CELL - 1, y0 + CELL - 1), fill=rgb + (90,), outline=rgb + (255,), width=3)
        d.ellipse((x0 + 20, y0 + 20, x0 + 43, y0 + 43), fill=rgb + (255,), outline=(255, 255, 255, 255), width=2)
        if e["kind"] == "trainer" and e["direction"] in DIRECTION_STEP:
            dx, dy = DIRECTION_STEP[e["direction"]]
            d.line((x0 + 32, y0 + 32, x0 + 32 + dx * 24, y0 + 32 + dy * 24), fill=(255, 255, 255, 255), width=4)
    img.alpha_composite(layer)


def _legend(width, kinds_present):
    font = ImageFont.load_default(size=16)
    items = [KINDS[k] for k in KINDS if k in kinds_present] + [(SIGHT_RGB, "Sight line")]
    x, y, rows = 8, 8, 1
    placed = []
    for rgb, label in items:
        need = 22 + int(font.getlength(label)) + 14
        if x + need > width and x > 8:
            x, y, rows = 8, y + 26, rows + 1
        placed.append((x, y, rgb, label))
        x += need
    strip = Image.new("RGBA", (width, 16 + 26 * rows), (24, 24, 24, 255))
    d = ImageDraw.Draw(strip)
    for x, y, rgb, label in placed:
        d.rectangle((x, y + 1, x + 15, y + 16), fill=rgb + (255,))
        d.text((x + 22, y), label, fill=(235, 235, 235, 255), font=font)
    return strip


# ---------------------------------------------------------------- render

def render_map(map_id, data_dir=DATA_DIR, graphics_dir=GRAPHICS_DIR, overlays=True):
    """The map area only: RGBA, width*64 by height*64."""
    m, ts = load_map(map_id, data_dir)
    img = _tile_image(m, ts, graphics_dir)
    if overlays:
        _overlay(img, m, ts)
    return img


def render(map_id, data_dir=DATA_DIR, graphics_dir=GRAPHICS_DIR):
    """The map area with the legend strip below it."""
    m, _ = load_map(map_id, data_dir)
    img = render_map(map_id, data_dir, graphics_dir)
    strip = _legend(img.width, {e["kind"] for e in map_events(m)})
    out = Image.new("RGBA", (img.width, img.height + strip.height))
    out.paste(img, (0, 0))
    out.paste(strip, (0, img.height))
    return out


def content_map_ids(content_dir=ROOT / "content"):
    return sorted(build.map_id_of(p) for p in (Path(content_dir) / "maps").glob("*.tmj"))


def main(argv):
    argv = list(argv)
    out_dir = DEFAULT_OUT
    if "--out" in argv:
        i = argv.index("--out")
        out_dir = Path(argv[i + 1])
        del argv[i:i + 2]
    try:
        ids = [int(a) for a in argv] or content_map_ids()
    except ValueError:
        print("usage: python tools/maps/preview.py [--out DIR] [map_id ...]")
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)
    for mid in ids:
        try:
            img = render(mid)
        except FileNotFoundError as e:
            print("preview failed: map %d: %s" % (mid, e))
            return 1
        path = out_dir / ("%d.png" % mid)
        img.save(path)
        print("wrote %s (%dx%d)" % (path, img.width, img.height))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
