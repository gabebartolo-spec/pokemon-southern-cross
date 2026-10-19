# Screen captures

## Task 4: 480x320, integer scaling (D-017), 2026-10-19

The game runs at 480x320 (twice the GBA's 240x160) in a 960x640 window, integer scaling, no smoothing
(`game/mkxp.json`, `game/Plugins/PSC_Screen/screen.rb`). Each capture in `task4/` is the game's own frame
(480x320, taken in-engine with `Graphics.snap_to_bitmap`) scaled 2x nearest-neighbour: the same pixels the
960x640 window shows. They show the game window only (engine frames), never the desktop. Window client
size measured at 960x640 on every run.

Party used: Grovyle 18, Zigzagoon 15 (a third of its HP), Taillow 14, Lotad 12 (poisoned), Wurmple 8,
Poochyena 11; Lappet Town; wild battles against Zigzagoon (single) and Zigzagoon + Wurmple (double).

"Needs art" means the screen is laid out on a 512x384 background image whose panels do not fit 480x320;
it cannot be made clean by moving things in code. It waits for the licensed Gen 3 UI art.

| Screen | Capture | State |
|---|---|---|
| Title | `title.png` | Fixed in `ui_title.rb`: image top-aligned so the logo is whole, "Press Enter" moved into the black band. The Essentials placeholder's "Version 21.1" line (bottom of the image) is cropped; our own title art replaces it. Splash screens centred. |
| Load screen | `load_screen.png` | Fixed in `ui_load.rb`: panels centred on 480. The Continue panel (needs a save) was not exercised. |
| Overworld | `overworld.png` | Clean (camera centre recomputed in `screen.rb`). |
| Message box | `message.png` | Clean. |
| Single battle | `battle_single_command.png`, `battle_single_fight.png` | Fixed in `ui_battle.rb`: bases moved for the 224-pixel scene, message and command boxes narrowed, move buttons narrowed so the type/PP box fits. |
| Double battle | `battle_double_command.png`, `battle_double_fight.png`, `battle_double_target.png` | Fixed in `ui_battle.rb`: four battlers, both databoxes per side visible, each side's two battlers spread apart so neither covers its ally, foes raised clear of the player's databoxes, target buttons centred. |
| Party | `party.png` | Needs art: the right column of panels is cut at x 480, the bottom row sits under the "Choose a Pokémon." box, the Cancel button is off-screen. |
| Summary | `summary_1_info.png` to `summary_5_ribbons.png`, `summary_4_moves_detail.png` | Needs art: the right panel and the fifth tab are cut at x 480 (e.g. Exp. Points is clipped), and the bottom 64 pixels (To Next Lv., Exp. bar, Moves page's fourth move PP, Ribbons' last row) are off-screen. |
| Bag | `bag.png` | Needs art: the item list box and its scroll arrows are cut at the right; only the first line of the item description shows. |
| Pokédex | `pokedex.png` | Needs art: the list's scroll bar is cut at the right and the Seen/Owned counters at the bottom are cut. The entry page was not opened. |
| Options | `options.png`, `options_screen_size.png`, `options_screen_size_3x.png` | Clean. Screen Size offers 1x, 2x, 3x and Full (`screen_size.rb`); measured window: start 960x640, 3x 1440x960, 2x 960x640, 1x 480x320, back to 2x 960x640. Saved sizes no longer offered (0.5x, 1.5x) become 2x (measured 960x640). Fullscreen not exercised. |
| Save | `save.png` | Clean. |
| Poké Mart | `mart_menu.png`, `mart_buy.png` | Menu clean. Buy screen needs art: the Money window covers the first letters of the item names, and the description's third line is cut at the bottom. |
| PC | `pc_menu.png`, `pc_storage.png` | PC menu clean. Box storage needs art: the box and the party panel are cut at the right and bottom. |

## Task 6: difficulty and level caps (D-008, D-021, D-022), 2026-10-19

Engine frames (`Graphics.screenshot`, 480x320) scaled 2x nearest-neighbour, from one debug run driven by a
scratch harness (scripted keys; not committed). Hard mode, 0 badges, cap 14 (`game/Data/psc_caps.json`).
Party: Zigzagoon, Poochyena; wild Magikarp Lv.2 on Route 1. The difficulty copy is from the story draft
(docs/region/STORY.md, slice scene 1, PR #3) and waits for the director's story approval.

| Check | Capture | What the run showed |
|---|---|---|
| Difficulty choice | `01_choice_acacia_line.png`, `02_choice_hard.png`, `03_choice_normal.png` | Acacia's line, then "Normal" / "Hard" with the help line per option; cursor starts on Hard. A second call returned :hard without asking. |
| Pause menu | `04_pause_hard.png`, `05_pause_normal.png` | "Level cap: 14" on hard; no line on normal. |
| Exp stops at the cap | `06_exp_clamped_to_cap.png` | Zigzagoon Lv.13, 1 Exp short of Lv.14: "got 1 Exp. Points!", then Lv.14 with exp exactly 2744 (Lv.14's minimum). |
| Battle at the cap | `07_battle_cap_message.png` | "Zigzagoon can't grow any stronger until the next badge."; exp unchanged (2744). |
| Rare Candy at the cap | `08_rare_candy_refused.png` | The same message; Rare Candies still 5 of 5. |
| Exp Candy quantity | `10_exp_candy_max_offered.png` | Poochyena Lv.12 needs 1016 Exp to reach Lv.14: the prompt's top is x011 (11 Exp Candy XS), not the 20 held. Cancelled; still 20. |
| Normal-mode trim | `11a_trim_inspect.png`, `11b_trim_inspect.png`, `11c_trim_inspect.png` | Brock's Onix as an opposing trainer: normal no item, EVs 0, AI skill 50; hard Sitrus Berry, EVs 21 each, AI skill 100. As a partner on normal it keeps Sitrus Berry and EVs 21 (the harness printed the values in a message). |
| Old save | `12_old_save_pause_hard.png` | A save written with no @psc_mode at all loads as hard: "Level cap: 14". |

## Manual re-check (each mkxp-z update)

mkxp-z 2.4.2 resets `Graphics.scale` to 1.0 one frame after the first `Graphics.resize_screen`, so without
a fix the game opens in a 480x320 window (measured 2026-10-19; later scale changes hold).
`PSC::Screen.set_window_scale` (`game/Plugins/PSC_Screen/screen_size.rb`) checks the scale one frame after
every change and sets it again. After updating mkxp-z: start the game and check the window opens at 960x640,
then switch Options > Screen Size to 3x and back to 2x (1440x960, then 960x640). If the scale holds without
the check, the check can go.

## Task 5: Gen 9 Pack sprites, Mega Evolution only (D-011, D-044), 2026-10-19

Engine frames (`Graphics.screenshot`, 480x320) scaled 2x nearest-neighbour, from one debug run driven by a
scratch harness (scripted keys; not committed; removed before the final plugin compile). Wild battles on
Route 1; party set by the harness. The battle layout in `game/Plugins/PSC_Screen/ui_battle.rb` was redone
for the pack's sprites: back sprites shrunk from 3x to 2x pixels, player side raised 16, single-battle foe
24 lower with the player's databox dropped into the strip above the message bar, doubles pair spread.

| Check | Capture | What the run showed |
|---|---|---|
| Command menu | `01_command_menu.png` | Venusaur Lv.50 (Venusaurite, Mega Ring in the bag) against a wild Fuecoco. |
| Fight menu | `02_fight_menu_mega_only.png` | Moves plus one gimmick button, Mega Evolution; no Tera, Dynamax or Z-Move option exists. |
| Mega selected | `03_mega_selected.png` | The Mega button switched on. |
| Mega Evolution | `04_mega_evolved.png` | "Venusaur has Mega Evolved into Mega Venusaur!", Mega back sprite and Mega icon on the databox. |
| A Gen 9 Pokémon | `05_gen9_battle.png` | Sprigatito (back) against a wild Quaxly (front), both from the pack. Sprigatito's back art is pale cream and green: the pack's colours, fully opaque. |
| Double battle | `06_double_command.png`, `07_double_fight.png`, `08_double_target.png` | Venusaur and Sprigatito against Kingambit and Quaxly. Both player Pokémon and Quaxly read clearly. Kingambit's head is above the screen: the foes cannot stand lower in doubles without covering the player's two databoxes (measured: 334 of 1,251 pack fronts lose more than 32 px of their top even in singles at the old height; in singles the new height cuts that to 114). |
