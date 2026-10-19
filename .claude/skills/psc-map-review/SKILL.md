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

## Checks (one yes/no question each, with the preview open; write the crop where the answer is the bad one)

Repeats
1. Is there any row with a run of 6 or more identical tiles in a line that no building, sign or water edge explains? (yes = FIX)
2. Is there any column with a run of 6 or more identical tiles in a line that nothing explains? (yes = FIX)

Path edges
3. Does every path edge show its autotile border, with no hard square corner where a curve is expected? (no = FIX)
4. Does every shore edge show its autotile border, with no hard square corner? (no = FIX)
5. Does at least one path bend or wander by a tile, rather than run dead straight edge to edge? (no = FIX)

Trees, cliffs and roofs
6. Is the upper half of every tree on the top layer, so a figure below it would walk behind the canopy? (no = FIX)
7. Is every cliff face closed by a base row? (no = FIX)
8. Is every cliff face closed by a top lip, with no floating cap or missing corner? (no = FIX)
9. Is every roof on the top layer, so a figure at the door is not drawn over the eaves? (no = FIX)

Doors
10. Can you trace a walkable route from the entry warp or spawn to the cell in front of every building door, crossing no water, fence, tree or cliff? (no = FIX)
11. Is every door's blue warp marker exactly on the door cell, not one cell off? (no = FIX)
12. Is every warp's way back present, a blue marker on the target map? (no = FIX)

Sight lines
13. Does every red sight line stop at the first wall, tree, fence or water tile? (no = FIX; a line drawn past a blocked tile means the preview or the map is wrong, find which)
14. Does every sight line cross the path the player must take, not only open grass beside it? (no = FIX unless the design says optional)
15. Can the player reach the next map exit without crossing the sight line of a trainer the design did not place there? (no = FIX)

Events
16. Is every item ball on a walkable, open cell, not inside a tree or fence? (no = FIX)
17. Is every person off every warp cell? (no = FIX)
18. Is every sign beside the path, not on it? (no = FIX)

Edges
19. Does the map border end in trees, water or cliff, or an intended exit, rather than bare ground stopping? (no = FIX)
20. Is every cell free of black (an empty tile on all three layers)? (no = FIX)

Biome (see the table below)
21. At game scale, in one glance, does the map show the "yes" signs for the biome its route claims? (no = FIX)
22. Does the map show none of that biome's "no" signs? (no = FIX)

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

PASS only when all 22 answers are right and the evidence is attached (full preview, the crops you judged,
the build command output). FIX lists each defect as: preview crop (x, y, size), what is wrong, what right looks
like. REJECT when the tileset cannot reach the claim (see the note above). Only a PASS goes to the director,
as one decision with labelled images (follow `ask-the-director`).
