#!/usr/bin/env python3
"""Draw docs/region/region_map.png: a labelled schematic of the region's route network.

A diagram, not game art. Positions are schematic (north is up, not to scale).
Usage: python tools/region/draw_region_map.py   (needs Pillow and the Windows Arial fonts)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "region" / "region_map.png"
W, H = 1700, 1370
FONT_DIR = Path("C:/Windows/Fonts")

OCEAN = (207, 230, 245)
COAST = (60, 70, 80)
INK = (30, 34, 40)
SLICE = (210, 40, 40)
BIOMES = {
    "Temperate forest and coast": (156, 203, 107),
    "Outback": (232, 164, 98),
    "Tropical north and reef": (92, 198, 184),
    "Rainforest": (46, 139, 87),
    "Alpine": (224, 234, 244),
    "Cities": (170, 170, 186),
}

CONTINENT = [(260, 330), (360, 260), (470, 250), (560, 170), (650, 150), (760, 110),
             (860, 140), (930, 230), (1000, 280), (1060, 250), (1150, 120), (1200, 80),
             (1240, 200), (1300, 300), (1390, 380), (1470, 520), (1540, 660), (1565, 780),
             (1500, 900), (1400, 985), (1280, 1035), (1150, 1055), (1020, 985), (930, 965),
             (860, 1005), (760, 965), (600, 925), (450, 935), (300, 1005), (200, 965),
             (160, 820), (140, 650), (160, 520), (200, 420)]
ISLAND = [(1090, 1120), (1200, 1095), (1320, 1125), (1345, 1220), (1270, 1300),
          (1160, 1290), (1100, 1215)]
OUTBACK = [(120, 300), (1250, 300), (1300, 560), (1200, 760), (880, 790), (820, 1010),
           (430, 1010), (250, 800), (120, 770)]
TROPICS = [(120, 60), (1600, 60), (1600, 300), (120, 300)]
RAINFOREST = [(1250, 300), (1460, 300), (1530, 570), (1300, 570)]

# name: (x, y, kind, line2, label side)   kind: start | town | gym | league | stop
NODES = {
    "Lyrebird Cove": (1180, 1000, "start", "Start", "w"),
    "Ford": (1265, 945, "stop", "", ""),
    "Wattlebrook": (1335, 855, "gym1", "Gym 1  Dragon  cap 14", "e"),
    "Port Halyard": (1480, 725, "gym2", "Gym 2  Water  cap 21", "n"),
    "Bend": (1235, 765, "stop", "", ""),
    "Snowgum Heights": (1075, 870, "gym3", "Gym 3  Ice  cap 28", "s"),
    "Redgum Wharf": (895, 880, "town", "", "n"),
    "Mallee Downs": (690, 860, "gym4", "Gym 4  Fire  cap 35", "s"),
    "Opal Hollow": (760, 680, "gym5", "Gym 5  Rock  cap 42", "e"),
    "Telegraph Wells": (820, 470, "town", "", "e"),
    "Westhaven": (235, 880, "town", "City", "n"),
    "Ironvale": (330, 400, "gym6", "Gym 6  Steel  cap 49", "s"),
    "Mangrove Landing": (760, 190, "gym7", "Gym 7  Poison  cap 56", "s"),
    "Coralhaven": (1210, 285, "town", "", "n"),
    "Mistwood": (1360, 440, "gym8", "Gym 8  Bug  cap 63", "w"),
    "Strait Landing": (1175, 1150, "stop", "", ""),
    "Crux Summit": (1250, 1235, "league", "Pokémon League  cap 72", "e"),
}

# (a, b, label, style)  style: slice | route | ferry | rail
EDGES = [
    ("Lyrebird Cove", "Ford", "R1", "slice"),
    ("Ford", "Wattlebrook", "R2", "slice"),
    ("Wattlebrook", "Port Halyard", "R3", "route"),
    ("Port Halyard", "Bend", "R4", "route"),
    ("Bend", "Snowgum Heights", "R5", "route"),
    ("Snowgum Heights", "Redgum Wharf", "R6", "route"),
    ("Redgum Wharf", "Mallee Downs", "R7", "route"),
    ("Mallee Downs", "Opal Hollow", "R8", "route"),
    ("Opal Hollow", "Telegraph Wells", "R9", "route"),
    ("Telegraph Wells", "Westhaven", "R10", "route"),
    ("Westhaven", "Ironvale", "R11", "route"),
    ("Ironvale", "Mangrove Landing", "R12", "route"),
    ("Mangrove Landing", "Coralhaven", "R13", "route"),
    ("Coralhaven", "Mistwood", "R14", "route"),
    ("Mistwood", "Port Halyard", "Coast Line (train)", "rail"),
    ("Lyrebird Cove", "Strait Landing", "Ferry", "ferry"),
    ("Strait Landing", "Crux Summit", "Victory Road", "route"),
]


def font(size, bold=False):
    return ImageFont.truetype(str(FONT_DIR / ("arialbd.ttf" if bold else "arial.ttf")), size)


def dashed(d, a, b, colour, width, dash=18, gap=12):
    (x1, y1), (x2, y2) = a, b
    length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    n, t = int(length // (dash + gap)) + 1, 0.0
    for _ in range(n):
        s, e = t / length, min((t + dash) / length, 1.0)
        d.line([(x1 + (x2 - x1) * s, y1 + (y2 - y1) * s),
                (x1 + (x2 - x1) * e, y1 + (y2 - y1) * e)], fill=colour, width=width)
        t += dash + gap
        if t > length:
            break


def boxed_text(d, xy, lines, anchor_side):
    """Draw text lines in a white box placed on one side of xy."""
    fonts = [font(26, True), font(20)]
    sizes = [d.textbbox((0, 0), s, font=fonts[i]) for i, s in enumerate(lines)]
    w = max(b[2] - b[0] for b in sizes) + 16
    h = sum(b[3] - b[1] for b in sizes) + 10 + 6 * (len(lines) - 1)
    x, y = xy
    off = 30
    if anchor_side == "e":
        left, top = x + off, y - h / 2
    elif anchor_side == "w":
        left, top = x - off - w, y - h / 2
    elif anchor_side == "n":
        left, top = x - w / 2, y - off - h
    else:
        left, top = x - w / 2, y + off
    d.rounded_rectangle([left, top, left + w, top + h], radius=6, fill=(255, 255, 255, 225),
                        outline=(120, 120, 130), width=1)
    cy = top + 5
    for i, s in enumerate(lines):
        b = sizes[i]
        d.text((left + 8, cy - b[1]), s, font=fonts[i], fill=INK)
        cy += (b[3] - b[1]) + 6


def main():
    img = Image.new("RGB", (W, H), OCEAN)
    land = Image.new("L", (W, H), 0)
    ImageDraw.Draw(land).polygon(CONTINENT, fill=255)
    ImageDraw.Draw(land).polygon(ISLAND, fill=255)

    biome = Image.new("RGB", (W, H), BIOMES["Temperate forest and coast"])
    bd = ImageDraw.Draw(biome)
    bd.polygon(OUTBACK, fill=BIOMES["Outback"])
    bd.polygon(TROPICS, fill=BIOMES["Tropical north and reef"])
    bd.polygon(RAINFOREST, fill=BIOMES["Rainforest"])
    bd.ellipse([960, 800, 1190, 940], fill=BIOMES["Alpine"])
    bd.ellipse([1190, 1170, 1310, 1290], fill=BIOMES["Alpine"])
    for name in ("Port Halyard", "Westhaven"):
        x, y = NODES[name][:2]
        bd.ellipse([x - 60, y - 60, x + 60, y + 60], fill=BIOMES["Cities"])
    img.paste(biome, (0, 0), land)

    d = ImageDraw.Draw(img, "RGBA")
    d.polygon(CONTINENT, outline=COAST, width=3)
    d.polygon(ISLAND, outline=COAST, width=3)
    # reef line offshore of Coralhaven
    dashed(d, (1260, 170), (1420, 420), (40, 120, 140), 4, dash=8, gap=8)

    for a, b, label, style in EDGES:
        pa, pb = NODES[a][:2], NODES[b][:2]
        if style == "slice":
            d.line([pa, pb], fill=SLICE, width=10)
        elif style == "route":
            d.line([pa, pb], fill=INK, width=7)
        elif style == "rail":
            dashed(d, pa, pb, (90, 50, 140), 6)
        else:
            dashed(d, pa, pb, (20, 80, 160), 6)

    for name, (x, y, kind, line2, side) in NODES.items():
        if kind == "stop":
            d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=INK)
            continue
        if kind == "league":
            r = 24
            d.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], fill=(250, 210, 60),
                      outline=INK, width=3)
        elif kind.startswith("gym"):
            r = 22
            d.ellipse([x - r, y - r, x + r, y + r], fill=(192, 57, 43), outline=INK, width=3)
            f = font(24, True)
            num = kind[3:]
            bb = d.textbbox((0, 0), num, font=f)
            d.text((x - (bb[2] + bb[0]) / 2, y - (bb[3] + bb[1]) / 2), num, font=f,
                   fill=(255, 255, 255))
        elif kind == "start":
            d.ellipse([x - 20, y - 20, x + 20, y + 20], fill=(255, 255, 255), outline=(20, 120, 60),
                      width=6)
        else:
            d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=(255, 255, 255), outline=INK, width=4)
        boxed_text(d, (x, y), [name] + ([line2] if line2 else []), side)

    # route labels last so nothing covers them
    f = font(20, True)
    nudge = {"R1": (8, -22), "R2": (-24, -6), "Coast Line (train)": (70, 0), "Ferry": (-42, 0),
             "Victory Road": (-90, 26), "R4": (0, -24), "R12": (-20, 0), "R10": (0, -20)}
    for a, b, label, style in EDGES:
        (x1, y1), (x2, y2) = NODES[a][:2], NODES[b][:2]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        nx, ny = nudge.get(label, (0, 0))
        bb = d.textbbox((0, 0), label, font=f)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        left, top = mx + nx - tw / 2 - 6, my + ny - th / 2 - 4
        d.rounded_rectangle([left, top, left + tw + 12, top + th + 8], radius=5,
                            fill=(255, 255, 255), outline=INK, width=2)
        d.text((left + 6, top + 4 - bb[1]), label, font=f, fill=INK)

    # title
    d.text((40, 24), "Crux region (working name): route schematic", font=font(36, True), fill=INK)
    d.text((40, 70), "Approved (D-031, D-032), 2026-10-19. North is up; not to scale.",
           font=font(22), fill=INK)

    # legend
    lx, ly = 40, 1048
    d.rounded_rectangle([lx - 12, ly - 12, lx + 640, ly + 310], radius=8,
                        fill=(255, 255, 255, 235), outline=(120, 120, 130), width=2)
    lf = font(22)
    for i, (name, col) in enumerate(BIOMES.items()):
        cx, cy = lx + (i % 2) * 320, ly + (i // 2) * 40
        d.rectangle([cx, cy, cx + 34, cy + 26], fill=col, outline=INK)
        d.text((cx + 44, cy + 1), name, font=lf, fill=INK)
    sy = ly + 130
    d.ellipse([lx + 4, sy, lx + 32, sy + 28], fill=(192, 57, 43), outline=INK, width=3)
    d.text((lx + 44, sy + 2), "Gym town (badge order)", font=lf, fill=INK)
    d.ellipse([lx + 324, sy, lx + 352, sy + 28], fill=(255, 255, 255), outline=INK, width=4)
    d.text((lx + 364, sy + 2), "Town", font=lf, fill=INK)
    sy += 44
    d.ellipse([lx + 4, sy, lx + 32, sy + 28], fill=(255, 255, 255), outline=(20, 120, 60), width=6)
    d.text((lx + 44, sy + 2), "Home town", font=lf, fill=INK)
    d.polygon([(lx + 338, sy), (lx + 352, sy + 14), (lx + 338, sy + 28), (lx + 324, sy + 14)],
              fill=(250, 210, 60), outline=INK, width=2)
    d.text((lx + 364, sy + 2), "Pokémon League", font=lf, fill=INK)
    sy += 44
    d.line([(lx, sy + 14), (lx + 36, sy + 14)], fill=INK, width=7)
    d.text((lx + 44, sy + 2), "Route", font=lf, fill=INK)
    dashed(d, (lx + 120, sy + 14), (lx + 170, sy + 14), (20, 80, 160), 6, dash=12, gap=8)
    d.text((lx + 178, sy + 2), "Ferry", font=lf, fill=INK)
    dashed(d, (lx + 260, sy + 14), (lx + 310, sy + 14), (90, 50, 140), 6, dash=12, gap=8)
    d.text((lx + 318, sy + 2), "Train", font=lf, fill=INK)
    dashed(d, (lx + 400, sy + 14), (lx + 440, sy + 14), (40, 120, 140), 4, dash=8, gap=8)
    d.text((lx + 448, sy + 2), "Reef", font=lf, fill=INK)
    sy += 40
    d.line([(lx, sy + 14), (lx + 36, sy + 14)], fill=SLICE, width=10)
    d.text((lx + 44, sy + 2), "Routes in the first-gym slice (home town to Gym 1)", font=lf, fill=INK)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)} ({W}x{H})")


if __name__ == "__main__":
    main()
