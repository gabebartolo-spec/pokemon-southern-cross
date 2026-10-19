# Southern Cross First-Gym Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A private, playable Pokémon Essentials build that runs from a new game to the first gym badge in the Gen 3-plus look at 480x320. Hard and normal modes, level caps and the QoL set all work, and every map is built by script from text sources.

**Architecture:** The unmodified Essentials v21.1 project lives in `game/`. Our behaviour goes in small plugins (`game/Plugins/PSC_*`), each a thin adapter over a pure Ruby module that is unit-tested outside the engine. Content is authored as text in `content/` (Tiled JSON maps, tileset definitions, progression and dex lists). Python tools in `tools/` validate it and build the binary `.rxdata` files the engine reads. CI runs the Python and Ruby test suites, the content validators, the check floors, the doc caps and gitleaks. Map previews are rendered to PNG artefacts.

**Tech Stack:** Pokémon Essentials v21.1 (Ruby 3 on mkxp-z), RPG Maker XP (only to open and play the project), Generation 9 Pack plugin, Python 3.12+ (stdlib + Pillow), Ruby 3.x + minitest for plugin logic, Tiled 1.10+ JSON (`.tmj`) as the map source, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-19-southern-cross-design.md`. Decision ids D-001 to D-027 are in `docs/DECISIONS.md`.

## Global Constraints

- Free fan game, never sold: no price, donation, Patreon, ad or paid-build text or link anywhere (D-001).
- Repo private; no build leaves the PC or CI artefacts until the director says so (D-018).
- Screen 480x320, integer scaling only, smoothing off (D-017).
- Mega Evolution is the only battle gimmick: Terastal, Z-Moves and Dynamax are off (D-011).
- Level caps: exp stops at the cap, shown in the menu, hard mode only (D-022). The difficulty is chosen at new game.
- Normal mode = same trainer teams, softer AI, held items and EVs trimmed (D-021).
- Every battle sprite in the dex is Gen 3 style (D-023). Every map is built by tools from `content/` (D-020).
- Every third-party file is CLEARED in `docs/LICENSING_REGISTER.md` with its credit line before it lands (CLAUDE.md rule 5).
- No spend beyond RPG Maker XP (D-006). Free downloads (Essentials, Gen 9 Pack, Tiled, RubyInstaller, tilesets) still need the director's yes per download (global safety rules): state name, source and size.
- Essentials' own scripts are never edited; changes go in `game/Plugins/PSC_*` (CLAUDE.md rule 3).
- Player-facing copy is natural Pokémon language, not engine terms.

## Review Focus

1. **Rare Candy and other exp sources above the cap.** A player expects the cap to hold for every exp source, not just battles. Test in Task 6: `test_rare_candy_blocked_at_cap`.
2. **Loading a save made before a plugin changed.** A player expects old saves to load. Test in Task 6: `test_mode_defaults_to_hard_when_missing_from_save`.
3. **A warp that points at a missing map or an off-map tile.** A player expects never to fall into a black void. Test in Task 9: `test_warp_target_must_exist`.
4. **A species placed on a route without a Gen 3-style sprite.** A player expects no "?" placeholder in a battle. Test in Task 3: `test_every_encounter_species_has_gen3_sprites`.
5. **Fullscreen or a resized window.** A player expects crisp pixels, not blur. Check in Task 4: `test_mkxp_json_integer_scaling`.

---

## Phase 0: Foundations

### Task 1: Import Essentials, licence register, repo hygiene

**Files:**
- Create: `game/` (Essentials v21.1 as downloaded, unmodified), `docs/LICENSING_REGISTER.md`, `docs/CREDITS.md`, `game/.psc_base_manifest.txt`
- Modify: `.gitattributes`, `.gitignore`

**Interfaces:**
- Produces: `game/.psc_base_manifest.txt`, one line per file shipped by Essentials: `<sha256>  <path relative to game/>`. Task 3 uses it to tell base files from added files.

- [ ] **Step 1:** Ask the director's yes for the download (Essentials v21.1 from the official release page, name and size stated). Then download it into a new empty folder in the scratchpad and copy it to `game/`.
- [ ] **Step 2:** Write `game/.psc_base_manifest.txt` with a Python one-off: sha256 of every file under `game/`, sorted by path.
- [ ] **Step 3:** In `.gitattributes`, add `*.rxdata binary`, `*.dat binary`, `*.png binary` (PNGs stay out of LFS, per the template comment), and LFS rules for `*.ogg *.mid *.wav`. In `.gitignore`, add `game/Data/*.dat` (compiled PBS) and `game/Game.ini` local edits.
- [ ] **Step 4:** In `docs/LICENSING_REGISTER.md`, make a table: `| Item | Source URL | Version | Terms (one line) | Credit line | Status |`. Add rows for Essentials and RPG Maker XP, status CLEARED, with each one's terms quoted from its release page. Copy the credit lines into `docs/CREDITS.md`.
- [ ] **Step 5:** Verify by opening `game/Game.exe`. It reaches the Essentials title screen. Record a screenshot path in the PR's Evidence section.
- [ ] **Step 6:** Commit: `git add game .gitattributes .gitignore docs/LICENSING_REGISTER.md docs/CREDITS.md`, then `git commit -m "Import Pokémon Essentials v21.1 unmodified, licence register"`.

### Task 2: Test harness, CI and check floors

**Files:**
- Create: `tools/run_tests.sh`, `tools/check_floors.py`, `tests/expected_checks.txt`, `tests/python/test_harness.py`, `tests/ruby/test_harness.rb`, `tools/check_doc_sizes.py`, `.github/workflows/tests.yml`, `.github/workflows/lint.yml`, `.claude/skills/psc-essentials-tests/SKILL.md`, `.claude/skills/psc-essentials-tests/references/learnings.md`

**Interfaces:**
- Produces: `tools/run_tests.sh [suite]`, where suite is `python`, `ruby` or `content`, and the default runs all. Each suite prints `SUITE <name> CHECKS <n>` on success. `tools/check_floors.py <run log>` exits 1 if any suite's count is below its line in `tests/expected_checks.txt` (format `<suite> <floor>`).

- [ ] **Step 1:** Write `tests/python/test_harness.py::test_floor_rejects_lower_count`. It runs `check_floors.py` on a fake log, `SUITE python CHECKS 3` against floor `python 4`, and asserts exit code 1. Add the passing twin, `test_floor_accepts_equal_count`.
- [ ] **Step 2:** Run `python -m pytest tests/python -q`. Expected: FAIL, script missing.
- [ ] **Step 3:** Implement `tools/check_floors.py` (stdlib only), then `tools/run_tests.sh`, which runs pytest and `ruby -Itests/ruby -e 'Dir["tests/ruby/test_*.rb"].each{|f| require "./"+f}'` and prints the SUITE lines. Add `tools/check_doc_sizes.py`, which fails if a must-read doc (CLAUDE.md, STATUS, DECISIONS, ROADMAP) exceeds its `Cap:` line count.
- [ ] **Step 4:** Run `bash tools/run_tests.sh python`. Expected: `SUITE python CHECKS 2`, exit 0. Ruby is not installed locally: ask the director's yes for RubyInstaller 3.x (free), or rely on CI for the Ruby suite until then.
- [ ] **Step 5:** Write `tests.yml` (ubuntu-latest, `actions/setup-python` 3.12, `ruby/setup-ruby` 3.3, `bash tools/run_tests.sh | tee run.log`, `python tools/check_floors.py run.log`, job name `test`). Write `lint.yml` with jobs `doc-caps` and `gitleaks` (gitleaks-action, `.gitleaks.toml`). Concurrency: cancel-in-progress only for PR refs, never for `main`.
- [ ] **Step 6:** Write the `psc-essentials-tests` skill (extends `game-architecture`). It covers how to run each suite, how to add a suite and floor, and that Essentials itself is tested by playtest captures, not CI.
- [ ] **Step 7:** Commit and push. Make the repo private with `gh repo create gabebartolo-spec/pokemon-southern-cross --private`. Confirm CI is green on `main`.

### Task 3: Content validators and the gate proof

**Files:**
- Create: `tools/validate/pbs.py`, `tools/validate/content.py`, `content/progression.json`, `content/dex.json`, `tests/python/test_validate.py`, `docs/audits/kickoff_gate.md`

**Interfaces:**
- Produces: `pbs.read_section_file(path) -> dict[str, dict[str, str]]`, which parses an Essentials PBS file of `[SECTION]` headers and `Key = Value` lines. `content.validate(repo_root) -> list[str]` returns error strings, and an empty list means valid. `content/progression.json` has the shape `{"segments": [{"id": "gym1", "cap": <int>, "trainers": ["TRAINERTYPE,Name[,version]"], "maps": [<map ids>]}]}`. `content/dex.json` has the shape `{"regional": ["SPECIES_ID", ...]}`.

- [ ] **Step 1:** Write the failing tests:
  - `test_trainer_over_cap_rejected`: a trainers.txt Pokémon at level 16 in segment `gym1` with cap 15 gives one error naming the trainer.
  - `test_encounter_species_must_be_in_dex`
  - `test_every_encounter_species_has_gen3_sprites`: each dex species needs `game/Graphics/Pokemon/Front/<ID>.png` and `Back/<ID>.png`, and neither may match a hash in the base manifest. Base Essentials sprites are not Gen 3 style, so each one must come from the chosen Gen 3 pack.
  - `test_added_file_needs_register_entry`: any file under `game/` not in the base manifest must match a path glob in the licence register's "Paths" column.
- [ ] **Step 2:** Run them; expected FAIL. Implement `pbs.py` and `content.py`; run again; expected PASS. Add `bash tools/run_tests.sh content`, which runs `content.validate` on the real repo, and set the floors to the real counts.
- [ ] **Step 3:** Prove the gate with four deliberately broken PRs, each closed unmerged once CI goes red: a lowered floor; a trainer over cap; an unregistered added file; a planted `PSC_TEST_SECRET_` plus 16 characters. Record each run id in `docs/audits/kickoff_gate.md`. Commit the audit file.

## Phase 1: Engine setup

### Task 4: 480x320, integer scaling, battle screen ready for doubles

**Files:**
- Create: `game/Plugins/PSC_Screen/meta.txt`, `game/Plugins/PSC_Screen/screen.rb`, `tests/python/test_screen_config.py`, `docs/captures/README.md`
- Modify: `game/mkxp.json`

- [ ] **Step 1:** Write `test_mkxp_json_integer_scaling`. It asserts that `mkxp.json` has `"smoothScaling": false`, `"fixedAspectRatio": true` and `"integerScaling": {"active": true}`, plus `defScreenW` 480 and `defScreenH` 320. Use the key names in the mkxp-z version Essentials ships, and fix the test if the shipped `mkxp.json` names them differently. Run it: FAIL. Edit `mkxp.json`: PASS.
- [ ] **Step 2:** In `screen.rb`, override the `Settings::SCREEN_WIDTH` and `SCREEN_HEIGHT` constants (find their exact names in `game/Data/Scripts/001_Settings.rb`) to 480 and 320, without editing that file.
- [ ] **Step 3:** Take screen captures at 2x of every screen the slice uses: title, overworld, message box, single battle, double battle, party, summary (all pages), bag, Pokédex, options, save, Poké Mart, PC. Save them under `docs/captures/task4/` with a README listing each screen and whether anything is cut off or misplaced.
- [ ] **Step 4:** For each faulty screen, add a layout fix in `game/Plugins/PSC_Screen/` (one file per screen, e.g. `ui_party.rb`), re-capture, and run the `art-qa-critic` check at 2x crops. Done when every listed screen has a clean capture, including the double battle.
- [ ] **Step 5:** Commit plugins, `mkxp.json`, test and captures.

### Task 5: Gen 9 data, Mega-only gimmicks

**Files:**
- Create: `game/Plugins/Generation 9 Pack/` (as downloaded), `game/Plugins/PSC_Gimmicks/gimmicks.rb`, `tests/python/test_gimmicks.py`
- Modify: `docs/LICENSING_REGISTER.md`, `docs/CREDITS.md`

- [ ] **Step 1:** Ask the director's yes for the download (Gen 9 Pack, PokeCommunity thread, version and size stated). Register its terms and credit line.
- [ ] **Step 2:** Write `test_no_tera_dynamax_zmove_enabled`. It greps `game/Plugins/**/*.rb` and `meta.txt` for the switches that enable Terastal, Dynamax and Z-Moves and asserts each is off or absent. Find the switch names in the pack's settings file and write them into the test. Run it: FAIL or PASS depending on the pack's defaults. Set `gimmicks.rb` so it passes.
- [ ] **Step 3:** Verify in game with the debug menu: give a Pokémon a Mega Stone, battle, and Mega Evolve. Confirm the Tera option is absent. Save the capture to `docs/captures/task5/`. Commit.

### Task 6: Difficulty and level caps

**Files:**
- Create: `game/Plugins/PSC_Difficulty/lib/psc_rules.rb` (pure), `game/Plugins/PSC_Difficulty/difficulty.rb` (engine adapter), `game/Plugins/PSC_Difficulty/meta.txt`, `tests/ruby/test_psc_rules.rb`, `content/caps.json` (generated from `progression.json` by `tools/validate/content.py --emit-caps`)

**Interfaces:**
- Produces (pure, no engine constants): `PSC::Rules.cap_for(badges:, mode:) -> Integer or nil` (nil on normal); `PSC::Rules.exp_after_cap(level:, exp_gain:, cap:) -> Integer` (0 at or above the cap); `PSC::Rules.trim_for_mode(pokemon_hash, mode:) -> Hash` (on normal: `:item` nil and `:ev` all 0; on hard: unchanged); `PSC::Rules.ai_skill(base_skill, mode:) -> Integer` (normal: `[base_skill / 2, 0].max`, hard: unchanged); `PSC::Rules.mode_from_save(value) -> :hard or :normal` (anything unknown, including nil, is `:hard`); `PSC::Rules.item_level_up_allowed?(level:, cap:) -> Boolean` (true when cap is nil). Caps per badge count come from `content/caps.json`: `{"0": 15, ...}`. The values are set in Task 13.

- [ ] **Step 1:** Write the failing tests in `test_psc_rules.rb`:
  - `test_cap_nil_on_normal`
  - `test_exp_zero_at_cap`
  - `test_exp_clamped_to_cap_boundary`: level 14, cap 15, the exp gain is reduced to exactly the amount that reaches level 15.
  - `test_rare_candy_blocked_at_cap`: `PSC::Rules.item_level_up_allowed?(level: 15, cap: 15)` is false.
  - `test_trim_strips_items_and_evs_on_normal`
  - `test_ai_skill_halved_on_normal`
  - `test_mode_defaults_to_hard_when_missing_from_save`
- [ ] **Step 2:** Run `bash tools/run_tests.sh ruby`. Expected: FAIL. Implement `psc_rules.rb` and run again. Expected: PASS.
- [ ] **Step 3:** In `difficulty.rb`, write engine adapters with `alias_method` hooks, each calling `PSC::Rules`:
  - the exp award in `Battle` (find the v21.1 method in `Data/Scripts/011_Battle/`);
  - the Rare Candy and exp candy item handlers;
  - the trainer build (`GameData::Trainer#to_trainer`);
  - the AI skill read.
  The mode is stored as `$PokemonGlobal.psc_mode`. It is set by a "Hard / Normal" choice after the intro, and the choice cannot be changed later.
- [ ] **Step 4:** Show the current cap in the pause menu ("Level cap: 15"), on hard only.
- [ ] **Step 5:** Verify in game with captures:
  - a battle at level 15 on hard gives no exp, and the message reads "<Name> can't grow any stronger until the next badge.";
  - Rare Candy is refused at the cap;
  - a save from before this plugin loads as hard.
  Commit.

### Task 7: Quality-of-life set

**Files:**
- Create: `game/Plugins/PSC_QoL/*.rb` (one file per feature), `tests/ruby/test_psc_qol.rb`, `game/Plugins/PSC_QoL/meta.txt`

**Interfaces:**
- Produces: `PSC::QoL.field_move_allowed?(move_id, badges:, has_move_on_team:) -> Boolean`. No HM needed: a field move is allowed once its badge is earned, whether or not a Pokémon knows it. Field-move badge requirements come from `content/progression.json` (`"field_moves": {"CUT": 1, ...}`). `PSC::QoL.consume_tm? -> false`.

- [ ] **Step 1:** Write the failing tests:
  - `test_cut_allowed_with_badge_without_move`
  - `test_cut_blocked_without_badge`
  - `test_tm_not_consumed`: `PSC::QoL.consume_tm?` returns false.
- [ ] **Step 2:** Run (FAIL), implement, run (PASS).
- [ ] **Step 3:** Engine adapters for the D-014 set:
  - field moves without HMs;
  - reusable TMs;
  - IVs and EVs shown on the summary screen (a new page, laid out for 480x320);
  - mints (nature change) and a stat trainer NPC event template, both used in Task 17;
  - a move relearner NPC in the first Pokémon Centre.
  If Essentials v21.1 already does any of these, use its setting instead of a plugin and note it in the PR.
- [ ] **Step 4:** In-game captures of each feature to `docs/captures/task7/`. Commit.

## Phase 2: Map toolchain (D-020)

### Task 8: Ruby Marshal reader and writer

**Files:**
- Create: `tools/rmxp/marshal.py`, `tools/rmxp/rpg.py`, `tests/python/test_marshal.py`

**Interfaces:**
- Produces: `marshal.loads(data: bytes) -> object` and `marshal.dumps(obj) -> bytes` for Marshal 4.8. They cover nil, true, false, Fixnum, Bignum, Float, String (with encoding ivar), Symbol and symlinks, Array, Hash, Object (`RubyObject(cls: str, ivars: dict)`) and user-dumped `Table`, `Color` and `Tone` (`UserDef(cls, raw: bytes)`). `rpg.Table(xsize, ysize, zsize, data: list[int])` provides `to_userdef()` and `from_userdef()`, using the `<5 x int32 LE><int16 LE data>` layout.

- [ ] **Step 1:** Write the failing tests:
  - `test_roundtrip_every_base_map`: for every `game/Data/Map*.rxdata`, `Tilesets.rxdata` and `MapInfos.rxdata`, `dumps(loads(b)) == b` byte for byte.
  - `test_table_roundtrip`
- [ ] **Step 2:** Run (FAIL), implement without third-party packages, then run (PASS). The byte-for-byte round trip over the real base files is the proof.
- [ ] **Step 3:** Commit.

### Task 9: Tiled JSON to RMXP map

**Files:**
- Create: `tools/maps/build.py`, `tools/maps/autotile.py`, `content/tilesets/<name>.json`, `content/maps/<map_id>_<slug>.tmj`, `tests/python/test_maps.py`, `docs/MAPS.md` (authoring guide, cap 150 lines)

**Interfaces:**
- Consumes: `marshal`, `rpg` from Task 8.
- Produces: `python tools/maps/build.py`, which writes every `content/maps/*.tmj` to `game/Data/MapNNN.rxdata` and updates `MapInfos.rxdata` and `Tilesets.rxdata`. `build.map_from_tmj(path) -> RubyObject("RPG::Map")`. `autotile.resolve(grid: list[list[int|None]], x, y) -> int` returns 0..47, the RMXP autotile shape from the 8 neighbours.
- Map conventions (in `docs/MAPS.md`): three tile layers named `ground`, `mid` and `top`; one object layer named `events`; a `content/tilesets/*.json` gives per-tile `passage`, `priority` and `terrain_tag`, and names the source PNG; autotile cells use Tiled tiles from a 7-cell "autotile key" strip that the builder expands.

- [ ] **Step 1:** Write the failing tests:
  - `test_autotile_isolated_cell_is_shape_0`
  - `test_autotile_full_surround_is_shape_47`: the 47-shape table follows the RMXP layout written out in `autotile.py`'s docstring.
  - `test_built_map_dimensions_match_tmj`
  - `test_warp_target_must_exist`: a warp to map 999, or to a tile outside the target map, raises `MapBuildError` with the source file and object name.
  - `test_impassable_spawn_rejected`
- [ ] **Step 2:** Run (FAIL), implement, run (PASS).
- [ ] **Step 3:** Rebuild one Essentials base map from a `.tmj` written by `tools/maps/export_tmj.py` (the reverse direction, created in this task). Prove that `build(export(base)) == base` for the tile data. Commit.

### Task 10: Events from objects

**Files:**
- Create: `tools/maps/events.py`, `tests/python/test_events.py`

**Interfaces:**
- Produces: `events.build(obj: dict) -> RubyObject("RPG::Event")` for the object `type` values `warp`, `sign`, `npc`, `item`, `trainer`, `script`.
  - `trainer` takes the properties `trainer` (`"TYPE,Name"`), `sight` (int), `intro`, `lose` and `doubles` (bool).
  - It emits the Essentials trainer event pattern: a `Trainer(n)` comment, then `pbTrainerBattle` or `pbDoubleTrainerBattle`. Copy the exact command list from a base Essentials trainer event, recorded as a fixture.

- [ ] **Step 1:** Write the failing tests:
  - `test_trainer_event_matches_base_fixture`: the command codes and parameters equal those of a trainer event read from a base map.
  - `test_warp_event_transfers_player`
  - `test_unknown_type_rejected`
- [ ] **Step 2:** Run (FAIL), implement, run (PASS). Commit.

### Task 11: Map previews and the art review loop

**Files:**
- Create: `tools/maps/preview.py`, `tests/python/test_preview.py`
- Modify: `.github/workflows/tests.yml` (upload `out/previews/*.png` as an artefact)

**Interfaces:**
- Produces: `python tools/maps/preview.py [map_id]`, which writes `out/previews/<map_id>.png` at 2x with event markers (warps blue, trainers red with their sight line). The renderer uses Pillow, which must first get its licence-register row.

- [ ] **Step 1:** Write `test_preview_size_is_map_tiles_times_64`. Run (FAIL), implement, run (PASS).
- [ ] **Step 2:** Write `.claude/skills/psc-map-review/SKILL.md` (extends `art-qa-critic`). Its checks: no long straight tile repeats, natural path edges, trees and cliffs layered correctly, every building door reachable, trainer sight lines not crossing walls, routes reading as Australian biomes. A map preview reaches the director only after this check.
- [ ] **Step 3:** Commit.

## Phase 3: The region on paper (D-004, D-015: Claude proposes, the director approves each)

These tasks produce documents and images, not code. Each one ends with one `ask-the-director` question with labelled images, and the decision goes in the log.

### Task 12: Art sources for the look

**Files:**
- Create: `docs/art/SOURCES.md`, `docs/captures/task12/*.png`

- [ ] **Step 1:** Shortlist 2 or 3 free community Gen 3-style tileset packs and one Gen 3-style battle-sprite pack covering Gens 1–9, with their terms and credit lines (for D-016 and D-023).
- [ ] **Step 2:** Build one sample route in each tileset through Tasks 9 to 11, at 480x320, labelled A, B and C. Run the `art-qa-critic` and `psc-map-review` checks, then ask the director which look is closest to "Gen 3 on steroids." Register and import only the chosen pack. Commit.

### Task 13: Region map, route order, gyms and caps

**Files:**
- Create: `docs/region/REGION.md` (cap 200 lines), `docs/region/region_map.png`

- [ ] **Step 1:** Draft the Australian region (D-009): towns, routes, biomes, the order the player meets them, eight gym towns, the league. Draw a labelled overview image.
- [ ] **Step 2:** Make a gym table: town, type, leader name, level cap, ace. Give the first gym's cap as a number. Ask the director to approve the map, then the gym table, as two questions. Write the approved caps into `content/progression.json`. Commit.

### Task 14: Story outline

**Files:**
- Create: `docs/region/STORY.md` (cap 200 lines)

- [ ] **Step 1:** Draft the player, the rival, the villain team and its motive (D-010), and one beat per gym. Write the slice's scenes in full: intro, choosing a starter, the rival battle, the first villain sighting and the first gym.
- [ ] **Step 2:** Ask the director to approve the outline, then the slice scenes. Commit.

### Task 15: Slice dex and encounters

**Files:**
- Create: `docs/region/DEX.md`; modify `content/dex.json`, `game/PBS/encounters.txt` (generated from `content/encounters.json` by `tools/validate/content.py --emit-encounters`)

- [ ] **Step 1:** Propose the starters and the 20 to 30 Pokémon of the slice's routes. Every one must have a Gen 3-style sprite in the chosen pack (D-023), and each needs a one-line reason it lives in that biome. Ask the director to approve them.
- [ ] **Step 2:** Write `content/encounters.json`. Run `bash tools/run_tests.sh content` and expect a PASS. Commit.

## Phase 4: The slice

### Task 16: Slice maps

**Files:**
- Create: `content/maps/*.tmj` for the player's house, starting town, the lab, Route 1, Route 2, the gym town, the Pokémon Centre, the Mart and the gym. Generated `game/Data/Map*.rxdata`.

- [ ] **Step 1:** Author each map against `docs/MAPS.md` and build it. Run `bash tools/run_tests.sh`; expect a PASS.
- [ ] **Step 2:** Render the previews and run the `psc-map-review` check on each one. Fix and re-render until it passes. Show the director the passing previews as one labelled board and ask for approval. Commit.

### Task 17: Trainers, NPCs and the QoL NPCs

**Files:**
- Modify: `game/PBS/trainers.txt`, `game/PBS/trainer_types.txt`, `content/progression.json`, `content/maps/*.tmj` (trainer and npc objects)

- [ ] **Step 1:** Write teams for every route and gym trainer, with movesets, natures, held items and EVs in Radical Red style. Every level is at or under the gym 1 cap. The leader's ace sits exactly at the cap. Add one double battle on Route 2. Place the mint seller, the stat trainer and the move relearner (Task 7).
- [ ] **Step 2:** Run the content suite; expect a PASS (no trainer over the cap). Playtest each trainer on hard and on normal, and record the win or loss and the turn count in `docs/playtests/slice_trainers.md`. Commit.

### Task 18: Intro, story events and the gym

**Files:**
- Modify: `content/maps/*.tmj` (script objects), `game/Plugins/PSC_Story/*.rb`

- [ ] **Step 1:** Build the approved Task 14 scenes: new game, the difficulty choice, the starter, the rival battle, the villain sighting, the gym puzzle, the leader battle and the badge, with the cap rising after the badge.
- [ ] **Step 2:** Run the full slice from a new game twice, once on hard and once on normal. Save and quit mid-route, restart, and load. Record a clip of each run. Commit.

### Task 19: Slice playtest packet

**Files:**
- Create: `docs/playtests/2026-xx-slice.md`, a Windows build zip as a private CI artefact only

- [ ] **Step 1:** Compile the build (Essentials debug off, PBS compiled), then smoke-test it from a clean folder.
- [ ] **Step 2:** Write the packet: how to start the build, what to try, the known gaps, and the "Not exercised" list.
- [ ] **Step 3:** Ask the director to playtest it, with one question: do the battles and the exploring feel right? Record the verdict in `docs/DECISIONS.md`. Nothing grows past the slice until it passes (D-004).

---

## Not in this plan

These come after the slice playtest passes:
- the remaining seven gyms and the league;
- the full regional dex of about 250;
- the ten regional forms and their AI-assisted art, each spend asked first (D-013, D-019);
- doubles-heavy trainers beyond the slice;
- Android (parked, D-005).
