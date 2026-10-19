"""RMXP autotile shapes: which of the 48 shapes a cell takes from its 8 neighbours.

Tile ids: 0 is empty; 48..383 are 7 autotiles x 48 shapes (autotile k, 0-based, uses ids
48*(k+1) .. 48*(k+1)+47, shape = id % 48); 384 and up are the tileset's own tiles.

An autotile PNG is 96x128: 3x4 tiles of 32px, read as 6x8 quarters of 16px numbered 1..48,
row by row. Row 0 of tiles: (0,0) the editor preview, (1,0) unused, (2,0) the four inner
corners (quarters 5 TL, 6 TR, 11 BL, 12 BR). Rows 1..3: a 3x3 block, outer border to centre.

Every shape is four quarters (TL, TR, BL, BR). Each quarter's piece depends on its two
orthogonal neighbours and the diagonal between them ("same" = same autotile in the same
layer; outside the map counts as same):

    vertical same, horizontal same, diagonal same  -> F  full (block centre)
    vertical same, horizontal same, diagonal other -> I  inner corner (tile (2,0))
    vertical same only                             -> V  side edge (block left/right column)
    horizontal same only                           -> H  top/bottom edge (block top/bottom row)
    neither                                        -> O  outer corner (block corner)

RMXP's shape table, as quarter numbers (TL, TR, BL, BR) and pieces:

     0 27 28 33 34 FFFF    1  5 28 33 34 IFFF    2 27  6 33 34 FIFF    3  5  6 33 34 IIFF
     4 27 28 33 12 FFFI    5  5 28 33 12 IFFI    6 27  6 33 12 FIFI    7  5  6 33 12 IIFI
     8 27 28 11 34 FFIF    9  5 28 11 34 IFIF   10 27  6 11 34 FIIF   11  5  6 11 34 IIIF
    12 27 28 11 12 FFII   13  5 28 11 12 IFII   14 27  6 11 12 FIII   15  5  6 11 12 IIII
    16 25 26 31 32 VFVF   17 25  6 31 32 VIVF   18 25 26 31 12 VFVI   19 25  6 31 12 VIVI
    20 15 16 21 22 HHFF   21 15 16 21 12 HHFI   22 15 16 11 22 HHIF   23 15 16 11 12 HHII
    24 29 30 35 36 FVFV   25 29 30 11 36 FVIV   26  5 30 35 36 IVFV   27  5 30 11 36 IVIV
    28 39 40 45 46 FFHH   29  5 40 45 46 IFHH   30 39  6 45 46 FIHH   31  5  6 45 46 IIHH
    32 25 30 31 36 VVVV   33 15 16 45 46 HHHH   34 13 14 19 20 OHVF   35 13 14 19 12 OHVI
    36 17 18 23 24 HOFV   37 17 18 11 24 HOIV   38 41 42 47 48 FVHO   39  5 42 47 48 IVHO
    40 37 38 43 44 VFOH   41 37  6 43 44 VIOH   42 13 18 19 24 OOVV   43 13 14 43 44 OHOH
    44 37 42 43 48 VVOO   45 17 18 47 48 HOHO   46 13 18 43 48 OOOO   47  1  2  7  8 preview

So a fully surrounded cell is shape 0 and an isolated cell is shape 46. Shape 47 (the
preview tile) is never produced by the rule; the editor never stores it either.

Verified against the Essentials v21.1 base maps by tests/python/test_maps.py
(test_autotile_matches_base_maps); some base maps hold hand-placed shapes, listed there.
"""

AUTOTILE_FIRST, TILESET_FIRST = 48, 384

# The 48 shapes as quarter numbers (TL, TR, BL, BR), RMXP order.
QUARTERS = [
    (27, 28, 33, 34), (5, 28, 33, 34), (27, 6, 33, 34), (5, 6, 33, 34),
    (27, 28, 33, 12), (5, 28, 33, 12), (27, 6, 33, 12), (5, 6, 33, 12),
    (27, 28, 11, 34), (5, 28, 11, 34), (27, 6, 11, 34), (5, 6, 11, 34),
    (27, 28, 11, 12), (5, 28, 11, 12), (27, 6, 11, 12), (5, 6, 11, 12),
    (25, 26, 31, 32), (25, 6, 31, 32), (25, 26, 31, 12), (25, 6, 31, 12),
    (15, 16, 21, 22), (15, 16, 21, 12), (15, 16, 11, 22), (15, 16, 11, 12),
    (29, 30, 35, 36), (29, 30, 11, 36), (5, 30, 35, 36), (5, 30, 11, 36),
    (39, 40, 45, 46), (5, 40, 45, 46), (39, 6, 45, 46), (5, 6, 45, 46),
    (25, 30, 31, 36), (15, 16, 45, 46), (13, 14, 19, 20), (13, 14, 19, 12),
    (17, 18, 23, 24), (17, 18, 11, 24), (41, 42, 47, 48), (5, 42, 47, 48),
    (37, 38, 43, 44), (37, 6, 43, 44), (13, 18, 19, 24), (13, 14, 43, 44),
    (37, 42, 43, 48), (17, 18, 47, 48), (13, 18, 43, 48), (1, 2, 7, 8),
]


def _piece(q):
    """The piece letter of quarter number q (1..48), from its place in the autotile PNG."""
    if q in (5, 6, 11, 12):
        return "I"
    col, row = (q - 1) % 6, (q - 1) // 6
    side, end = col in (0, 5), row in (2, 7)
    return "O" if side and end else "V" if side else "H" if end else "F"


# pieces "TL TR BL BR" -> shape; the preview (47) is left out.
_SHAPE_OF = {"".join(_piece(q) for q in qs): s for s, qs in enumerate(QUARTERS[:47])}

# Per quarter: (vertical neighbour, horizontal neighbour, diagonal) as (dx, dy).
_CORNERS = (((0, -1), (-1, 0), (-1, -1)), ((0, -1), (1, 0), (1, -1)),
            ((0, 1), (-1, 0), (-1, 1)), ((0, 1), (1, 0), (1, 1)))


def kind_of(tile_id):
    """Autotile index 0..6 of an RMXP tile id, or None if it is not an autotile."""
    if AUTOTILE_FIRST <= tile_id < TILESET_FIRST:
        return tile_id // 48 - 1
    return None


def resolve(grid, x, y):
    """Shape 0..46 for grid[y][x] (an autotile kind; None = not an autotile) from its neighbours."""
    h, w = len(grid), len(grid[0])
    me = grid[y][x]

    def same(dx, dy):
        xx, yy = x + dx, y + dy
        if not (0 <= xx < w and 0 <= yy < h):
            return True
        return grid[yy][xx] == me

    key = ""
    for v, hz, d in _CORNERS:
        sv, sh = same(*v), same(*hz)
        key += ("F" if same(*d) else "I") if sv and sh else "V" if sv else "H" if sh else "O"
    return _SHAPE_OF[key]
