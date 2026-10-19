# Licensing register

Nothing enters the project unless it is listed here as CLEARED with its credit line (CLAUDE.md rule 5).
`Paths` is a glob of repo paths each item covers; `tools/validate/content.py` checks every file under
`game/` that is not in `game/.psc_base_manifest.txt` against these globs. The Pokémon Essentials row
covers manifest files only (its Paths cell carries the `base-manifest` marker): it never clears an
added file, so `game/**` there does not match everything.

| Item | Source URL | Version | Terms (one line) | Credit line | Status | Paths |
|---|---|---|---|---|---|---|
| Pokémon Essentials (scripts, data, graphics, audio as shipped in the kit) | https://github.com/Maruno17/pokemon-essentials | v21.1 (2023-07-30) | Repo LICENSE is Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0): share and adapt with credit, non-commercial only, adaptations under the same licence | Pokémon Essentials, by Maruno, Flameguru, Poccil and others | CLEARED | `game/**` (base-manifest: only files listed in `game/.psc_base_manifest.txt`) |
| mkxp-z (runtime bundled in the kit: Game.exe, DLLs) | https://github.com/mkxp-z/mkxp-z | v2.4.2 (c9378cf, built 2023-07-07, per the kit's scripts) | GPL-2.0 per the upstream repo (to verify: the kit ships no licence or notice file); used unmodified, credited in the kit's in-game credits | "mkxp-z" by Roza and contributors, based on "mkxp" by Ancurio et al. (the kit's credits read: mkxp-z by Roza, based on mkxp by Ancurio et al.) | CLEARED | `game/Game.exe`, `game/*.dll` |
| RPG Maker XP | https://store.steampowered.com/app/222730/RPG_Maker_XP/ | Steam copy bought by the director | Editor only, not shipped; nothing copied from it into the repo | "RPG Maker XP" by Enterbrain | CLEARED | none (editor only, not shipped) |
| pytest | https://github.com/pytest-dev/pytest | pip | MIT; dev-only test runner, never shipped | none required | CLEARED | none (dev-only, never shipped) |

Pokémon names, characters and graphics belong to Nintendo, Creatures, GAME FREAK and The Pokémon Company
(see `docs/CREDITS.md`). This is a free, never-sold fan game.
