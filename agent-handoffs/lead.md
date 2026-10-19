# Lead handoff, 2026-10-19 evening (written for the account switch)
## State: awaiting director

## Task
Lead of Pokémon Southern Cross (Essentials v21.1, PC only; real Pokémon, free, never sold: D-001).
The previous lead session ("Pokémon fan game: design and plan") is archived. No agents are running.
Boot: CLAUDE.md, this file, `docs/STATUS.md`, `docs/DECISIONS.md` (newest first), the plan
`docs/superpowers/plans/2026-10-19-first-gym-slice.md`.

## Branch and commit
- main 160b180a (#19). Board refresh + this handoff: branch `claude/lead-handoff-2026-10-19`.
- Task 5: `claude/gen9-mega` 91345ff1, pushed, NO PR, worktree `../pokemon-southern-cross-wt/gen9`.
  Gen 9 Pack v3.3.8 + v21.1 Hotfixes, Mega Evolution only, battle layout for the pack's sprites
  (backs shrunk 3x to 2x). Carries D-044 in DECISIONS.md (not on main yet). Behind main by
  #13-#19: merge main in before the PR. Untracked captures in docs/captures/task5/compare/.
- Worktrees: main checkout + gen9 only (the detached `sdd` worktree was removed, it was clean).

## Unfinished changes
1. Task 5 layout pick: the director chooses from the captures in
   `../pokemon-southern-cross-wt/gen9/docs/captures/task5/compare/` (optionA/B/C, single and
   double, plus party.png, summary.png): 480x320 with sprites at 2x, the same at 1x, or
   Essentials' native 512x384. Known flaw in the committed layout: tall foes lose their top in
   double battles. After the pick: apply it, sync main, open the PR, CI, merge.
2. Starter sprites (Koaleaf, Eucalord, Taiparch): 12 frames (front, back, shiny front, shiny back),
   all pass the grid audit. Copies in `../pokemon-southern-cross-wt/starter_art_pending/`
   (board: starters_full_set.png). Waiting on the director's approval of the full set.
   Picks already applied: croc back B (head up); shinies albino croc, black taipan with a blue
   flame, silver-dollar Koaleaf. After approval: size into the pack's 192 px front and 288 px back
   frames, register them in the licence register, then a PR.

## Evidence so far
CI rejects a lowered floor, a trainer over the cap, an unregistered file and a planted secret
(gate PRs #4-#12, closed). Map tools round-trip every base map byte for byte (#9).

## Open decisions
- Task 5 battle layout (above). Starter set approval (above).
- Story, still open: the Bug gym leader; the name of Firebreak's leader.
- NOT LOGGED: the director's spend yes for Retro Diffusion art, a US$10 cap (about US$5.58
  spent; one croc back job ran twice, US$0.36). D-041 says "each spend asked first", but the
  cap itself is not in DECISIONS.md. Ask him to confirm the wording and log it before more spend.
- Starter picks above are in chat only: log them under "Board and log" in the starter PR.

## Running jobs
None.

## Findings for the lead
Retro Diffusion edits ran in the in-app browser on the director's account. The first sprite
outline check only caught light edge pixels; it missed mid-brown edges (fixed by checking every
edge pixel). A back sprite was first the front pose with the face painted over.
Playbook: nothing new from this shift.

## Rules learnt the hard way (under 10 lines)
- Grid-audit every sprite before he sees it: no unoutlined edge, no stray pixels, no holes or
  leftover background, 2 px clear of the canvas edge.
- A back sprite must be a real view from behind (front and back outlines must not mostly overlap).
- Shiny recolours: mask the exact pixels; check small features (dewdrop, flame glow) by eye at 2x.
- A pushed branch with no PR gets no CI here; open the PR as soon as the branch is ready.

## Queue (only when assigned)
Task 5 PR -> starter sprites into the game -> Task 7 (QoL) -> Task 12 art sources -> slice tasks 15-19.
