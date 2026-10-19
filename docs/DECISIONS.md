# Decisions log

Cap: 400 lines; oldest roll to `docs/archive/`. One decision per entry, newest first. A decision
that is not here does not exist. Format: date · id · who decided · the decision · why · what it
changes. Only the merge role edits this file, from the "Board and log" section of merged PRs.
D-001 to D-023 match D1 to D23 in the design spec
(`docs/superpowers/specs/2026-10-19-southern-cross-design.md`).

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
