# Screen captures

## Task 4: 480x320, integer scaling (D-017), 2026-10-19

The game runs at 480x320 (twice the GBA's 240x160) in a 960x640 window, integer scaling, no smoothing
(`game/mkxp.json`, `game/Plugins/PSC_Screen/screen.rb`). Each capture in `task4/` is the game's own frame
(480x320, taken in-engine with `Graphics.snap_to_bitmap`) scaled 2x nearest-neighbour: the same pixels the
960x640 window shows. Window client size measured at 960x640 on every run.

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
| Double battle | `battle_double_command.png`, `battle_double_fight.png`, `battle_double_target.png` | Fixed in `ui_battle.rb`: four battlers, both databoxes per side visible, foes raised clear of the player's databoxes, target buttons centred. |
| Party | `party.png` | Needs art: the right column of panels is cut at x 480, the bottom row sits under the "Choose a Pokémon." box, the Cancel button is off-screen. |
| Summary | `summary_1_info.png` to `summary_5_ribbons.png`, `summary_4_moves_detail.png` | Needs art: the right panel and the fifth tab are cut at x 480 (e.g. Exp. Points is clipped), and the bottom 64 pixels (To Next Lv., Exp. bar, Moves page's fourth move PP, Ribbons' last row) are off-screen. |
| Bag | `bag.png` | Needs art: the item list box and its scroll arrows are cut at the right; only the first line of the item description shows. |
| Pokédex | `pokedex.png` | Needs art: the list's scroll bar is cut at the right and the Seen/Owned counters at the bottom are cut. The entry page was not opened. |
| Options | `options.png` | Clean (first five rows; the rows below, e.g. Screen Size, were not scrolled to). |
| Save | `save.png` | Clean. |
| Poké Mart | `mart_menu.png`, `mart_buy.png` | Menu clean. Buy screen needs art: the Money window covers the first letters of the item names, and the description's third line is cut at the bottom. |
| PC | `pc_menu.png`, `pc_storage.png` | PC menu clean. Box storage needs art: the box and the party panel are cut at the right and bottom. |
