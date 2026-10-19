# Status board

Cap: 150 lines. Edited only by the merge role, in a board PR after each merge, from the merged
PR's "Board and log" section. History rolls to `docs/archive/status_<month>.md`.

## Phase
Current phase: **0 — Foundations** (gate: CI proves it rejects a lowered floor, a trainer over
the cap, an unregistered added file and a planted secret). Gate signer: the lead.
Gate proof PRs (closed; red where intended): #5, #10 and #12 lowered floor, #6 over cap, #7
unregistered file, #8 planted secret; baselines #4 and #11. The lead has not signed the gate yet.

## Agents

| Agent | State | Item | Branch / PR | Since |
|-------|-------|------|-------------|-------|
| Lead | awaiting director | starter sprite approval; Task 5 battle layout pick | — | 2026-10-19 |

States: working · running a check · awaiting director · blocked · available.

## Assigned items (in order; an item starts only when it is listed here)

Plan: `docs/superpowers/plans/2026-10-19-first-gym-slice.md`.

### Phase 0
| Task | Item | State |
|------|------|-------|
| 1 | Import Essentials, licence register | merged #2 |
| 2 | Test harness, CI, check floors | merged #1 |
| 3 | Content validators and the gate proof | merged #13 |
| 4 | 480x320, integer scaling | merged #18 |
| 5 | Gen 9 data, Mega-only (D-011, D-040, D-044) | branch `claude/gen9-mega` 91345ff1, no PR; awaits the director's layout pick |
| 6 | Difficulty and level caps | merged #17 |
| 7 | Quality-of-life set | not started |
| 8 | Ruby Marshal reader and writer | merged #9 |
| 9 | Tiled JSON to RMXP map | merged #14 |
| 10 | Events from objects | merged #15 |
| 11 | Map previews and art review | merged #16 |
| 13, 14 | Region and story drafts | merged #3 (D-029 to D-042) |
| — | Starter sprites, 12 frames (D-041, D-043) | awaiting director approval; not in the game |
