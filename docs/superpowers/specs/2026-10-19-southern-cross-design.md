# Pokémon Southern Cross: design

Status: approved by the director, 2026-10-19. Working title; renaming is cheap.
Engine re-confirmed the same day over pokeemerald-expansion (D-025 in `docs/DECISIONS.md`).

## 1. Intent

A free, standalone Pokémon fan game built from scratch, not a ROM hack. Infinite Fusion only
shows the format; there is no fusion mechanic. The player gets a classic Pokémon adventure in a
new region based on Australia, but battles have the depth of Radical Red: smart trainers, real
movesets, held items and natures, level caps, and team building that rewards planning.

The director's reason to exist: a new region and story, with Radical Red's battle AI and focus on
team building.

## 2. Decisions (director, 2026-10-19)

| # | Question | Decision |
|---|----------|----------|
| D1 | IP scope | Real Pokémon. Free fan game, never sold. |
| D2 | Hook | New region and story, with Radical Red-style battle AI and team building |
| D3 | Engine | Pokémon Essentials (v21.1, on RPG Maker XP / mkxp-z) |
| D4 | Size | Plan the whole region on paper, build a slice that ends at the first gym, director playtests it, then grow |
| D5 | Platform | PC (Windows) download only. Android (JoiPlay) is parked. |
| D6 | Spend | Written yes: buy RPG Maker XP, about US$25, on the director's own Steam account |
| D7 | Roster | Regional dex of about 250, hand-picked from every generation |
| D8 | Difficulty | Hard by default (Radical Red-style), plus a normal mode |
| D9 | Region | Australia |
| D10 | Story tone | Classic (rival, 8 gyms, league), with a darker villain team that has a real motive and stakes (like Black/White) |
| D11 | Gimmick | Mega Evolution only |
| D12 | Name | Working title "Pokemon Southern Cross"; decide later |
| D13 | Regional forms | About 10 Australian forms, added after the slice |
| D14 | Quality of life | The full Radical Red set: no HMs needed, reusable TMs, visible IVs/EVs, mints and stat training, a move relearner close by |
| D15 | Writing | Claude proposes story, gym leaders and map; the director approves or changes each part |
| D16 | Look | Gen 3 GBA look "on steroids": richer colours, more detail (Unbound / Radical Red territory) |
| D17 | Screen | 480x320 (exactly 2x the GBA), integer scaling, no smoothing |
| D18 | Repo | Private GitHub repo, `gabebartolo-spec/pokemon-southern-cross` |
| D19 | New pixel art | AI-assisted pixel art (e.g. Retro Diffusion), cleaned up and checked against the slop rules. Each spend still needs the director's written yes, asked in stages. |
| D20 | Map making | Agents do it all: maps are built by script, not hand-painted by the director |
| D21 | Normal mode | Same trainer teams, softer AI, trimmed items and EVs. Hard is the real, balanced game. |
| D22 | Level caps | Exp stops at the next gym's cap, shown in the menu. Hard only; normal has no caps. |
| D23 | Sprite style | Every battle sprite matches the Gen 3 look. The dex leans on Pokémon with existing Gen 3-style community sprites; AI-assisted art fills gaps later, each spend asked first. |

Claude's calls (director may overrule): singles plus some double battles, as in the main games,
with the battle screen laid out for doubles from the start; no money of any kind tied to the game
(see anti-goals).

## 3. Goals

- The first-gym slice feels like a real Pokémon game: walk a town and routes, catch, train,
  battle trainers who play smart, and beat a gym leader under a level cap.
- Trainers play well enough on hard that team building and switching matter.
- The whole region exists as an approved paper plan before content grows past the slice: map,
  route order, gyms, story beats, dex placement.

## 4. Non-goals

- No fusion mechanic.
- No Android, web or console build for now.
- No online play, trading or battles between players.
- No Terastal, Z-Moves or Dynamax.
- No new art in the slice: it uses existing sprites and credited community resources.

## 5. Anti-goals (fails even if it technically works)

- **Any money tied to the game**: no price, donations, Patreon, paid builds or ads. Charging money
  is what most often triggers a takedown. *(Claude's guess at the director's intent; confirm.)*
- **Public before the director chooses:** the repo stays private and no build is shared until the
  director says so.
- **Unfair difficulty:** hard means trainers play well with the same rules as the player, not stat
  cheats or hidden level boosts. Every trainer team is visible to anyone who looks it up.
- **AI-slop art:** smeared pixels, mixels, off-palette sprites or broken tile seams never ship.
- **Uncredited community assets:** every tile, sprite, script or plugin taken from the community
  has an entry in the credits and the licence register before it lands.

## 6. The region (to be proposed for approval, per D15)

Australia, with routes and towns drawn from real biomes: outback desert, tropical north and reef,
rainforest, alpine snow country, temperate forest and coast, and cities. Eight gyms and a league.
Claude drafts the following for the director to approve, in this order:

1. Region map: towns, routes, the order the player meets them, where the gyms are.
2. Story outline: the player, the rival, the villain team and its motive, the key beats per gym.
3. Gym leaders: type, town, level cap and ace for each.
4. Regional dex of about 250: which Pokémon, and on which route or area each is found.
5. The ten regional forms: which Pokémon, their new type, and the story behind each.

Only items 1–3, plus the slice's part of item 4, are needed before the slice is built.

## 7. The first-gym slice

What the director playtests:

- An intro: new game, choose a starter, meet the rival.
- A starting town, about two routes and the first gym town, with wild encounters from the
  regional dex.
- Several route trainers on hard AI, with real movesets and held items.
- The first gym: puzzle or layout, gym trainers, the leader, a badge.
- A level cap for the first gym, shown to the player.
- The QoL set from D14 working where it applies this early.
- Normal and hard difficulty, chosen at new game.
- A save and load that survive a game restart.
- Playable at 480x320 in the Gen 3-plus look, using credited community resources.

The gate: the director plays the slice and says whether the battles and exploring feel right.
Nothing grows past the slice until that playtest passes.

## 8. Constraints

- **Engine:** Pokémon Essentials v21.1 (latest stable release, June 2023), runs on mkxp-z;
  maps are edited in RPG Maker XP. Gen 9 data comes from the community "Generation 9 Pack"
  plugin. Essentials ships Mega Evolution and a rewritten AI ("AI XL") in v21.
- **Screen:** Essentials' interface is laid out for 512x384. Moving to 480x320 means re-laying out
  every interface screen (bag, summary, party, Pokédex, battle UI). This is real work and belongs
  early in the plan.
- **Testing:** RPG Maker XP cannot be driven headlessly the way Godot can. What can be checked by
  a machine (game data files, trainer teams against level caps, dex placement, credits coverage)
  is checked in CI; battle behaviour is checked through Essentials' debug tools and recorded
  playtests.
- **Maps by script (D20):** RPG Maker XP stores maps as binary Ruby data, and its editor is
  point-and-click. Agents need a text source they can write and diff, plus a converter into the
  game's map files and a rendered preview image of every map for visual checks. This toolchain
  comes before any content map. Claude's suggested route (builder may change it): author maps in
  Tiled's text format with the community tilesets, convert to `.rxdata`, render a PNG preview of
  each map in CI. Generated maps must not look blocky or repetitive: every map preview passes an
  art review before the director sees it.
- **Licences:** Essentials and community resources each carry their own credit terms. A licence
  register lists every tool, plugin, tileset and sprite source with its terms.
- **Spend:** RPG Maker XP is approved (D6). Nothing else is spent without a new written yes.
- **Standards:** the repo follows the director's shared standards (project-kickoff scaffold:
  CLAUDE.md, CI, PR template, decision log, status board, handoffs, project skills), adapted for
  an Essentials project rather than Godot.

## 9. Left to the builder

- The exact plugin list beyond the Gen 9 Pack (level caps, QoL), as long as each is credited and
  registered.
- How hard-mode AI is tuned inside Essentials' AI (skill levels, trainer flags), provided it meets
  the anti-goal on fairness.
- Which community tilesets and sprite packs the slice uses, inside the Gen 3-plus look.
- The CI checks and their tooling (e.g. a Python validator for the game's text data files).
