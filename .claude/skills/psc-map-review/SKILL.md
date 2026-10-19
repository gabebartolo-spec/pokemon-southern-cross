---
name: psc-map-review
description: Art review of a Pokemon Southern Cross map preview before the director sees it. Extends the general `art-qa-critic` skill (read it first; its verdicts PASS / FIX / REJECT and its rule that art never reaches the director unchecked apply here). Use whenever an agent has built a map from Tiled text (content/maps) and is about to show out/previews/<id>.png, a route, town or gym map, or ask the director to approve a map look.
---

# Map review (extends `art-qa-critic`)

Director rule (D-020, 2026-10-19): agents build every map from text, and **every map preview passes this
review before the director sees it**. You are the critic: specific, unsentimental, "looks fine" is not a review.
Do the general procedure in `~/.claude/skills/art-qa-critic/SKILL.md` (claim first, evidence, verdict);
this file adds the map-specific checks. General lessons go to that skill's log, map-only ones to
`references/learnings.md` here.

## Get the evidence

1. Rebuild and render from built data: `python tools/maps/build.py && python tools/maps/preview.py <map_id>`
   writes `out/previews/<id>.png`: the map at 2x (width*64 by height*64) with a legend strip below.
   Blue = warp, red = trainer plus its sight line, amber = item ball, violet = person, grey = sign.
2. Open the whole PNG once for the overall read, then crop at 2x of each area you judge, nearest-neighbour
   so pixels stay honest (a 4x crop of a 512x512 region is 2048 px):
   `python -c "from PIL import Image; Image.open('out/previews/9.png').crop((x,y,x+512,y+512)).resize((1024,1024),Image.NEAREST).save('crop.png')"`
   Never judge from the downscaled view of the whole map. Never re-open a crop already judged.
3. Write what the map claims in one line (e.g. "Route 1 is a temperate coast route with two trainers and one
   building") and what must not change (warps, tile ids other maps rely on).

## Checks (each: open the preview, answer yes or no, note the crop where it is no)

1. **Repeats.** Pick any row and any column: is there a run of 6 or more identical tiles in a line (a wall of the
   same tree, a ruler-straight fence or path edge) that no building, sign or water edge explains? Yes = FIX.
2. **Path edges.** Does every path or shore edge show its autotile border (no hard square corners where a curve
   is expected), and does the path wander by at least one tile somewhere instead of running dead straight edge to edge?
3. **Trees and cliffs layering.** For every tree, cliff top and roof: is its upper half on the top layer, so a
   figure standing on the cell below would walk behind the canopy and not through a trunk cut in half? Is every
   cliff face closed with a base row and a top lip, with no floating cap or missing corner?
4. **Doors reachable.** For every building door and cave mouth: trace with a finger from the spawn or entry
   warp to the cell in front of the door over cells the player can walk on. Can you reach it without crossing
   water, a fence, a tree or a cliff? No = FIX. Is the door's own warp (blue) on the door cell and not one cell off?
5. **Sight lines.** For every red trainer: does its red sight line stop at the first wall, tree, fence or
   water tile, and does it cover the path the player must take (not only open grass beside it)? Does any line
   cross a wall (a line drawn past a blocked tile means the preview or the map is wrong: stop and find which)?
   Can the player reach the trainer's line's start from the entry without a detour through another trainer's line,
   unless the design says so?
6. **Events.** Is every event marker on a cell that makes sense (item ball not inside a tree, person not on a
   warp, sign beside the path not on it)? Does every warp have a way back, a second blue marker on the target map?
7. **Australian biome.** Does the map read as the biome its route claims, in one glance at game scale, with the
   concrete signs below? A temperate-looking map labelled outback is a FIX.
8. **Edges.** Does the map border fade into something (trees, water, cliff) with an intended exit, or does the
   ground just stop? Any black cell (an empty tile in all three layers) inside the map is a FIX.

### What "reads as an Australian biome" means (design spec: outback, tropical north and reef, rainforest, alpine, temperate forest and coast, cities)

| biome | yes if you see | no if you see |
|---|---|---|
| Outback desert | red-orange ground, sparse low scrub and dead trees, wide empty space, rock outcrops, a dry creek bed, long open sight lines | green grass fields, dense pines, snow, water everywhere |
| Tropical north and reef | palms, mangroves, sand and shallow turquoise water with a reef or sandbar edge, boardwalks, humid greens | conifers, bare red dirt as the main ground, snow |
| Rainforest | dense mixed canopy, ferns and tree ferns, dark undergrowth, a creek, narrow walkable gaps | open lawns, a tidy tree grid, pine-shaped trees |
| Alpine snow country | white ground, snow gums (twisted pale trunks), granite boulders, frozen creek, ski-lodge style timber buildings | fields of green, palms, sand |
| Temperate forest and coast | gums and tea tree mix, ferns, sandy beach with a break, cliffs over sea, weatherboard houses, tin roofs | desert red ground, tropical palms as the main tree |
| Cities | grid of paved streets, tall buildings, trams or rail, laneways, parks as small green squares, harbour or river edge | winding dirt tracks, a single house on grass |

Base Essentials tilesets are European/Japanese (pines, red tile roofs, Lappet Town is the evidence): until our
own Australian tiles exist (art role), a map that can only show pines may only claim the temperate-forest read,
and the review says so rather than passing it as outback.

## Verdict

PASS only when all eight answers are right and the evidence is attached (full preview, the crops you judged,
the build command output). FIX lists each defect as: preview crop (x, y, size), what is wrong, what right looks
like. REJECT when the tileset cannot reach the claim (see the note above). Only a PASS goes to the director,
as one decision with labelled images (follow `ask-the-director`).
