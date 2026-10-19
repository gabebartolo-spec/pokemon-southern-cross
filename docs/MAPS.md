# Maps: authoring and building

Cap: 150 lines.

Maps are text: Tiled JSON (`.tmj`) in `content/maps/`, tilesets as JSON in `content/tilesets/`.
`game/Data/MapNNN.rxdata`, `MapInfos.rxdata` and `Tilesets.rxdata` are build output, committed
in the same PR as the content that made them.

```bash
python tools/maps/build.py              # content/maps/*.tmj -> game/Data
python tools/maps/export_tmj.py 2       # base Map002 -> content/maps/002_<slug>.tmj (to start from)
```

## Map files

- Name: `content/maps/<map_id>_<slug>.tmj`, id 1..999, slug `a-z 0-9 _` (`900_builder_test.tmj`).
  An id that belongs to a base Essentials map is rejected unless the map sets `replaces_base: true`.
- Fixed size, 32x32 tiles, one tileset given by `source` (`../tilesets/<name>.json`).
- Layers: three tile layers `ground`, `mid`, `top` (RMXP layers 0, 1, 2) as plain number lists,
  and one object layer `events`. Any other layer is an error; flipped tiles are an error.
- Map properties (all optional): `name` (shown in MapInfos; default the slug), `parent_id`,
  `bgm`, `bgm_volume` (80), `bgm_pitch` (100), `autoplay_bgm`, `bgs`, `bgs_volume`, `bgs_pitch`,
  `autoplay_bgs`, `encounter_step` (30), `replaces_base`.

## Tile numbers

A tile number in a layer is `firstgid + local`. Local ids follow the RMXP tileset palette:

| local | RMXP tile id | meaning |
|---|---|---|
| 0 | 0 | empty |
| 1..7 | 48 x local + shape | the autotile key: autotile slot local-1; the builder picks the shape |
| 8+ | 376 + local | the tileset PNG's tiles, left to right, top to bottom, 8 per row |

Autotile cells are drawn with one key tile per autotile; `tools/maps/autotile.py` expands each
to one of RMXP's 48 shapes from its 8 neighbours in the same layer (same autotile = joined; the
map edge counts as joined). Full surround is shape 0, isolated is shape 46, shape 47 (the
editor preview) is never used. The full table is in `autotile.py`'s docstring.

## Tileset files

`content/tilesets/<name>.json` (export writes it from Tilesets.rxdata):

- `tileset_id`; `name`; `tileset_name` = the PNG in `game/Graphics/Tilesets/`.
- `autotiles`: 7 slots `{name, passage, priority, terrain_tag}`; `name` is the PNG in
  `game/Graphics/Autotiles/`, blank for an empty slot.
- `tiles`: `passage`, `priority`, `terrain_tag` lists, one entry per PNG tile (local id 8+).
  Passage bits: 1 down, 2 left, 4 right, 8 up blocked; 15 = wall. Priority 0..5 = drawn over
  the player at that height. Terrain tags are Essentials' (7 water, 2 grass, 13 neutral, ...).
- Panorama, fog and battleback fields, defaults as in the base files.
- Ids 1..25 are base tilesets: the json must match the base entry exactly (it is checked, not
  written) unless it sets `replaces_base: true`. New tilesets take ids 26, 27, ... with no gaps.

The tileset json is our format, not Tiled's: Tiled cannot open these maps yet. Maps are
authored as text by agents and checked by the builder; previews come from the built data.

## Objects (`events` layer)

Rectangles; the cell is `floor(x/32), floor(y/32)`. Object `type` (or Tiled `class`):

- `warp`: properties `target_map`, `target_x`, `target_y` (ints), optional `direction`
  (retain, down, left, right, up) and `sound` (an SE, e.g. `Door exit`). Built as a
  player-touch event in Essentials' own door pattern: fade out, wait, transfer, fade in. The
  target map must be a content map or a base map, and the target cell inside it.
- `spawn`: an arrival or start point. Not built into an event; it must sit on a walkable cell
  (Essentials' `playerPassable?`: top layer down, skip empty, neutral and bridge tiles, passage
  15 blocks, priority 0 decides).

Any other type is an error. Errors name the file, the object and the cell.

## What the builder guarantees

- Deterministic: same content, same bytes; files are rewritten only when their bytes change.
- Base entries untouched: MapInfos keeps every base entry byte for byte and in its order; our
  maps follow, sorted by id, `order` continuing after the base. A content map that is removed
  is dropped from MapInfos (its MapNNN.rxdata stays until deleted by hand). `replaces_base`
  maps keep their base MapInfos entry.
- `tests/python/test_maps.py` rebuilds `content/` into a copy of `game/Data` and checks the
  committed files are identical.

## Autotiles in base maps

The neighbour rule reproduces every autotile cell of the 9 base maps drawn with the RMXP
editor's automatic shapes (Map002, 005, 007, 021, 023, 028, 031, 035, 052: 361 cells). Eleven
base maps hold hand-placed or stale shapes (coastlines, sea-deep borders): 1,630 of their 5,799
autotile cells differ (Map039, 040, 041, 044, 045, 068, 069, 070, 071, 072, 073); overall the
rule matches 4,530 of 6,160 base autotile cells (73.5%). `export_tmj.py` refuses those maps
rather than change them; the test pins each map's mismatch count. Hand-placed shapes are not
supported in content maps yet.

## Data structures (Essentials v21.1 base files, read with tools.rmxp.marshal)

Built objects use exactly these ivars in this order. Where base files differ in order (Ruby 1.8
hash order), the most common one is used. Strings are `RString` (UTF-8, `E` ivar set).

- `RPG::Map` (39 of 69 maps): `@bgm` AudioFile, `@events` Hash{id => Event}, `@tileset_id` int,
  `@bgs` AudioFile, `@autoplay_bgm` bool, `@data` Table(w, h, 3) dim 3, `@autoplay_bgs` bool,
  `@height` int, `@encounter_step` int, `@width` int, `@encounter_list` [] (always empty).
  The other 30 maps put `@tileset_id` before `@events`.
- `RPG::AudioFile`: `@volume` int, `@name` String, `@pitch` int.
- `RPG::Event`: `@pages` [Page], `@name` String, `@y` int, `@x` int, `@id` int.
- `RPG::Event::Page` (323 of 688 pages): `@move_type`, `@list` [EventCommand], `@condition`,
  `@direction_fix`, `@move_route`, `@trigger`, `@step_anime`, `@move_frequency`, `@graphic`,
  `@always_on_top`, `@walk_anime`, `@move_speed`, `@through`.
- `RPG::Event::Page::Condition`: `@switch2_valid`, `@self_switch_ch` String, `@switch1_id`,
  `@switch1_valid`, `@variable_value`, `@self_switch_valid`, `@variable_id`, `@variable_valid`,
  `@switch2_id`.
- `RPG::Event::Page::Graphic`: `@opacity`, `@character_name` String, `@pattern`, `@tile_id`,
  `@direction`, `@blend_type`, `@character_hue`.
- `RPG::MoveRoute`: `@list` [MoveCommand], `@skippable`, `@repeat`. `RPG::MoveCommand`:
  `@parameters`, `@code`. `RPG::EventCommand`: `@parameters`, `@indent`, `@code`.
- `RPG::MapInfo` (MapInfos.rxdata is a Hash{id => MapInfo}, not in id order): `@scroll_x` int,
  `@name` String, `@expanded` bool, `@order` int, `@scroll_y` int, `@parent_id` int.
- `RPG::Tileset` (Tilesets.rxdata is an Array, [0] = nil, ids 1..25): `@terrain_tags` Table,
  `@panorama_hue` int, `@fog_sy` int, `@name` String, `@fog_opacity` int, `@priorities` Table,
  `@panorama_name` String, `@fog_sx` int, `@fog_hue` int, `@passages` Table, `@autotile_names`
  [7 String], `@fog_zoom` int, `@fog_name` String, `@battleback_name` String, `@tileset_name`
  String, `@id` int, `@fog_blend_type` int. Tables are 1-D, 384 + tile count long; ids 0..47
  hold 0 (priority of id 0 is 5); each autotile's 48 ids share one value.
- `Tone` (in event commands): user-dumped, 4 little-endian doubles (red, green, blue, gray).
