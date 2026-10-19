# Pokemon Southern Cross: working rules for every Claude Code session

Pokémon Essentials v21.1 (Ruby on mkxp-z, RPG Maker XP project). A free, non-commercial
Pokémon fan game: real Pokémon, never sold. The approved design is
`docs/superpowers/specs/2026-10-19-southern-cross-design.md`. Read this file, then your handoff (`agent-handoffs/<role>.md`), then only the
roadmap section you were assigned (`docs/ROADMAP.md`, by section, never whole). The general
rules every project shares live in `~/.claude/CLAUDE.md` and the skills it names
(`ask-the-director`, `ai-game-dev-playbook`, `github-hygiene`, `game-architecture`,
`art-qa-critic`); this file holds only what is true for Pokemon Southern Cross.

## Philosophy (permanent)

**Designed by a person, developed with AI, never designed by AI.** The director supplies vision,
taste and final judgement. Agents supply execution, evidence and honest pushback.

- **Every battle rewards the team you built.** Every system is judged by whether it serves that. A system that does not change
  what the player sees, decides or remembers is cut, not polished.
- **A roadmap item is context, not authorisation.** Start only what `docs/STATUS.md` lists as
  assigned. When an assigned task is done: stop, report with evidence, recommend the next step, wait.
- **Simplest viable option first.** Fewer systems, fewer numbers, fewer files. Challenge
  over-ambitious items and say what the simpler alternative is.
- **Challenge the director** when a request conflicts with these rules or `docs/VISION.md`. One
  paragraph, a better option, then do what the director decides.
- **Ask, don't ponder.** A judgement call that is the director's is asked at once, the
  `ask-the-director` way. Never park a question in a wall of text; never guess at a visual.

## Hard rules

1. **No runtime AI.** No LLM, diffusion or network model in the shipped game. AI is a
   development tool only.
2. **Never sold, never monetised.** No price, donations, Patreon, ads or paid builds tied to the
   game; the repo stays private and no build is shared until the director says so.
3. **Essentials stays Essentials.** Game changes live in `Plugins/` and PBS data, not edits to
   Essentials' own scripts, so an Essentials or plugin update stays mergeable.
4. **Data, not code, holds content and balance** (PBS files and `content/`, validated in CI by
   `tools/validate/`). Maps are authored as text in `content/maps/` and built by `tools/maps/`;
   the `.rxdata` files are build output. Magic numbers in plugins are rejected in review.
5. **Licensing and credits.** Nothing enters the project unless `docs/LICENSING_REGISTER.md` lists
   it as CLEARED with its credit line; terms must allow use in a free fan game.
6. **No spend** without the director's written yes in `docs/DECISIONS.md`.
7. **Proof before "done".** A change is done when its evidence is in the PR body. "It works" is
   not evidence; what the game did is.
8. **Change method after two failed fixes.** Gather different evidence and rethink.

## Machine rules (shared PC, one GPU)

- One game process per agent; never kill `Game.exe` by image name, kill by the PID you recorded.
- GPU jobs (renders, generation, local models) one at a time; the art role owns them.
- Worktrees: `git worktree add -b claude/<topic> ../PokemonSouthernCross-wt/<topic> origin/main`. Remove
  the worktree when the PR merges. More than four live worktrees is a violation.
- Only the merge role edits `docs/STATUS.md` and `docs/DECISIONS.md`, in a docs-only board PR
  after each merge; every other PR states its board and log changes in its body.
- Stage files by name, never `git add -A`; never `git stash`; revert `.import` churn.
- Windowed game runs never steal the director's focus; map previews render headless in CI.

## Sessions and context

- Fresh session at every task boundary; write `agent-handoffs/<role>.md` first (120-line cap,
  rewrite not append). Routine work at 50-100k tokens; past 150k, hand off.
- End every turn with your state: working, running a check, awaiting director, blocked, available.

## Skills

Project skills live in `.claude/skills/psc-*` and extend the general ones; each has a
`references/learnings.md` with the evidence bar from `~/.claude/CLAUDE.md`. General lessons go
to the general skill's log so every project benefits.
