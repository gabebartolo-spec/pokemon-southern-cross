# Decisions log

Cap: 400 lines; oldest roll to `docs/archive/`. One decision per entry, newest first. A decision
that is not here does not exist. Format: date · id · who decided · the decision · why · what it
changes. Only the merge role edits this file, from the "Board and log" section of merged PRs.
D-001 to D-023 match D1 to D23 in the design spec
(`docs/superpowers/specs/2026-10-19-southern-cross-design.md`).

## 2026-10-19 · D-038 · Director · Major trainers' moves: Claude drafts a team sheet, the director edits it
Each major trainer gets one sheet (legal moves at level, checked against the game's data) for him to change before it is built.

## 2026-10-19 · D-037 · Director · Gym 1 (Dusty) team: Larvitar 12, Totodile 13, Gible 14 (ace)
On hard the ace holds an Oran Berry; normal mode removes it (D-021).

## 2026-10-19 · D-036 · Director · The director picks the full team and signature Pokémon of every major trainer
Gym leaders, rival, Elite Four, Champion, villain leaders and admins. Never written before he answers; route trainers may be drafted.

## 2026-10-19 · D-035 · Director · New Pokémon names come from Claude's shortlists, picked by the director

## 2026-10-19 · D-034 · Director · Starters: three new regional lines, with art made now
- A regional Sandile line: Water.
- A regional Ekans line: Fire, later Fire/Ground, with a new third stage.
- A new pre-evolution of Komala, a regional Komala and a new third stage: Grass/Poison.
Their sprites are made for the slice: AI-assisted, cleaned to match the Essentials sprites, each spend asked first. This supersedes "no new art in the slice" for the starters only.

## 2026-10-19 · D-033 · Director · Story and scenes come from an interview with the director, not drafts for approval
The five slice scenes drafted in docs/region/STORY.md were not approved. They are rewritten from his interview answers (D-039).

## 2026-10-19 · D-039 · Director · Slice story answers (interview)
- **Opening:** the professor's welcome, then you wake up at home.
- **Player:** a newcomer who lives with Mum and Dad.
- **Professor:** Professor Gum, a dry-humoured field ecologist in muddy boots. Her partner is Kangaskhan.
- **Rival:** Kit, gender left open, a friendly and proud local. Kit is drawn into Firebreak, then comes back, and takes the starter strong against yours.
- **Home town:** Lyrebird Cove, a small surf and fishing town.
- **First Firebreak sighting:** grunts netting introduced birds on Route 2.

## 2026-10-19 · D-032 · Director · Gym 1 is Dragon (reptile Pokémon), led by Dusty, a reptile-park keeper, in Wattlebrook; gym 8 (Mistwood) is Bug
This supersedes the drafted Flying gym 1 and Dragon gym 8. The other gyms, the Elite Four types and the level caps are as approved in D-031.

## 2026-10-19 · D-031 · Director · Region and gym table approved as drafted (docs/region/REGION.md)
Caps 14, 21, 28, 35, 42, 49, 56, 63, then 72 for the league. Gym types are as drafted, except where D-032 changes them.

## 2026-10-19 · D-030 · Director · Villains are Team Firebreak; the player is a newcomer
Firebreak is a former chief ranger's team that wants to drive out every Pokémon and person "not born of the land".

## 2026-10-19 · D-029 · Director · Battle sprites: the modern Essentials style for every Pokémon (supersedes D-023)
Why: no community pack draws Gens 4–9 in the Gen 3 style. The Gen 3 look (D-016) still applies to maps and screens. Changes: the "dex sprites must not be base files" content rule is removed.

## 2026-10-19 · D-040 · Director · Download yes: Generation 9 Pack, Emerald Outdoors tileset, Voltseon's Emerald UI Pack
All free. Each is credited and registered before it lands; stop and report any download over 200 MB.

## 2026-10-19 · D-028 · Director · The repo is public (reverses D-018's private)
Why: GitHub would not run checks on the private repo because of an account billing block; public
repos get free checks. Accepted cost: the project can be found before it is playable. Changes:
the "repo stays private" rule is gone; still no builds shared until the director says so.

## 2026-10-19 · D-027 · Director · Started with the shared kickoff scaffold
The engine-neutral parts (CLAUDE.md, PR template, board and log, handoffs, project skills). The
Godot test harness and workflows were left out; Phase 0 replaces them with Essentials equivalents.

## 2026-10-19 · D-026 · Director · Pillar: "Every battle rewards the team you built."
Why: Radical Red-style team building is the hook. Changes: any feature that does not make
building or using a team more interesting is cut.

## 2026-10-19 · D-025 · Director · Stay with Pokémon Essentials, not pokeemerald-expansion
Why: a standalone fan game, not a ROM hack, with room for richer colour than GBA hardware allows.
pokeemerald-expansion, mGBA and Porymap were found cloned on this PC (`Documents/GitHub/pokemon-hack`,
`pokemon-tools`) and offered; declined. Changes: nothing from those folders enters this repo.

## 2026-10-19 · D-024 · Director · Design spec approved
Changes: the build plan may be written. Claude's calls inside it (director may overrule): some
double battles, as in the main games, with the battle screen laid out for doubles; maps authored
in Tiled's text format.

## 2026-10-19 · D-023 · Director · Every battle sprite matches the Gen 3 look
The dex leans on Pokémon with existing Gen 3-style community sprites; AI-assisted art fills gaps later.

## 2026-10-19 · D-022 · Director · Level caps: exp stops at the next gym's cap, shown in the menu; hard mode only

## 2026-10-19 · D-021 · Director · Normal mode: same trainer teams, softer AI, trimmed items and EVs
Why: hard is the real, balanced game; one set of teams to build and check.

## 2026-10-19 · D-020 · Director · Agents build every map; the director does not paint tiles
Changes: a text map source, converter and preview renderer come before any content map.

## 2026-10-19 · D-019 · Director · New pixel art is AI-assisted, checked against the slop rules
Each spend still needs a separate written yes, asked in stages.

## 2026-10-19 · D-018 · Director · Private GitHub repo, gabebartolo-spec/pokemon-southern-cross
Note: GitHub Free does not enforce branch protection on private repos; protection is by rule.

## 2026-10-19 · D-017 · Director · Screen 480x320 (2x GBA), integer scaling, no smoothing

## 2026-10-19 · D-016 · Director · Look: Gen 3 GBA, "on steroids" (richer colours, more detail)

## 2026-10-19 · D-015 · Director · Claude proposes story, gym leaders and map; the director approves each part

## 2026-10-19 · D-014 · Director · Full Radical Red quality-of-life set
No HMs needed, reusable TMs, visible IVs/EVs, mints and stat training, a move relearner nearby.

## 2026-10-19 · D-013 · Director · About 10 Australian regional forms, after the slice

## 2026-10-19 · D-012 · Director · Working title "Pokemon Southern Cross"; name decided later

## 2026-10-19 · D-011 · Director · Mega Evolution is the only battle gimmick

## 2026-10-19 · D-010 · Director · Story: classic, with a darker villain team that has a real motive

## 2026-10-19 · D-009 · Director · Region based on Australia

## 2026-10-19 · D-008 · Director · Hard by default (Radical Red-style), plus a normal mode

## 2026-10-19 · D-007 · Director · Regional dex of about 250, from every generation

## 2026-10-19 · D-006 · Director · Spend: buy RPG Maker XP (about US$25) on the director's Steam account
The only approved spend. Anything else needs a new written yes here.

## 2026-10-19 · D-005 · Director · PC (Windows) only; Android via JoiPlay parked

## 2026-10-19 · D-004 · Director · Plan the whole region on paper, build a slice to the first gym, director playtests, then grow

## 2026-10-19 · D-003 · Director · Engine: Pokémon Essentials v21.1

## 2026-10-19 · D-002 · Director · New region and story, with Radical Red-style battle AI and team building

## 2026-10-19 · D-001 · Director · Real Pokémon; free fan game, never sold; not a fusion game
Why: the director's call, made knowing Nintendo/TPC routinely take fan games down. Changes: no
money of any kind tied to the game; the repo stays private until the director chooses.
