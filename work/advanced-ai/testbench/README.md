# Advanced AI test bench

Every test and test tool for the advanced trainer AI lives here: our own unit tests and the test bench ported from the
Spanish translation (commit `dc8577c`). Nothing is ported yet: phase 1 adds `unit/`, and phase 3 adds the rest
([PLAN.md](../PLAN.md)).

An **AI build** is our standard build, then the difficulty installer, then the AI installer. A change to any of the
three makes a new AI build, and the tiers below run on it.

## Layout

| Directory | What it holds | Tier |
|---|---|---|
| `run.py` | The one entry point: `run.py static`, `run.py quick`, `run.py deep`. The list of what each tier runs lives here and nowhere else | all |
| `lib/` | Shared code: the emulator runner, ROM data readers, emulator, simulator and build pools | – |
| `unit/` | Our own tests: builder, golden test, `ids.h`, trainer marks, installer guards, fix-region overlap, sizes | static |
| `bench/` | Graded decisions from set-up positions: `aibench`, its scenarios, batches and claim checks | static (claims), quick (runs) |
| `checks/` | Pass/fail behaviour checks: the setting, the lead pick, reading the player's action, foresight, stuck menus, story battles with the AI on, the Options row | quick, deep |
| `props/` | Property tests on random positions (`aiprops`) | quick (short), deep (full) |
| `versus/` | AI-vs-AI games against the hack's AI, their report, team generation, the live view, play mode, analysis helpers | deep |
| `fuzz/` | Random doubles positions (`aifuzz`) | deep |
| `sim/` | The PC battle simulator (C), driven by the ROM's data | static, development |
| `hostai/` | The AI built for the PC (C) and its unit tests | static |
| `dev/` | Tools no tier runs: `aibuild`, `aibatch`, `aitune`, `aicalc`, `aitime`, engine probes | – |
| `references/` | Recorded reference results: bench scores, AI-vs-AI log digests, property-test seeds. No ROM bytes | all |

Every directory gets its own README when it is created: what is in it, what it needs, how to run it.

Run output goes to the ignored `work/build/advanced-ai/runs/`. Pre-battle saves are made locally by a script and found
by SHA-256, like our `--emu` saves, and are never committed (`*.dsv` and `*.sav` are ignored). The simulator's and the
host build's build output gets its own ignore rule when they are ported.

## Tiers

| Tier | When | What runs | Time |
|---|---|---|---|
| Static | Every `check.py` run, fast and `--full` | `unit/`; the bench's claim checks against ROM data (no emulator); `hostai/` unit tests; the simulator's bench check; the `aitune` tests | seconds (simulator build not yet timed) |
| Quick | Every AI build: the `ai` part of `check.py --full --emu` | `bench/` (365 graded scenarios); `checks/`: settings (each setting, doubles, partner, Gym trainer, story character), lead pick, reading the player's action, stuck menus; a short `props/` run | ~10–15 min with 9 emulators (estimate; Spanish figure: 7 s per bench run per worker) |
| Deep | Any change to the AI, to the overlay-14 code it hooks, or to the engine code it calls; every release candidate | `versus/`: 80 games (seed 101) compared with the reference; the full `props/` run; foresight (`checks/`); `fuzz/` (doubles); story battles with the AI on | 35–80 min (Spanish rc42 and rc44 runs) |

**Quick tier passes when:**
- the bench scores at or above the reference, with 0 fallbacks;
- every check in `checks/` passes;
- the property tests find 0 violations.

**Deep tier passes when** the 80 game logs are byte-identical to the reference. The Spanish logs are deterministic
(synced luck, pinned clock): rc42's 80 logs were byte-identical to rc41's.

If the logs differ, the report must name the change that caused it, and the win count must stay within the Spanish 95%
range (80–94%). A new reference is recorded only with a reviewer's sign-off.

## What comes from the Spanish test bench

| Spanish file | Lines | Goes to |
|---|---|---|
| `tools/emu.py`, `aidata.py`, `romio.py`, `melon.py`, `emupool.py`, `simpool.py`, `buildpool.py` | 1,849 | `lib/` |
| `tools/aibench.py`, `tests/ai_scenarios.py`, `tests/ai_checks.py`, `tests/ai_helpers.py`, `tests/ai_batches/` (27 files) | 2,584 + batches | `bench/` |
| `tools/aimode_check.py` (rewritten for the Options row), `lead_check.py`, `read_check.py`, `fscheck.py`, `qa/ai_research/menulock.py`, the `storycheck --ai` cases | 1,944 + cases | `checks/` |
| `tools/aiprops.py` | 1,181 | `props/` |
| `tools/aivsai.py`, `aivsai_report.py`, `aiteams.py`, `aivsai_live.py`, `aiplay.py`, `qa/aivsai/human_games.py`, `score_round.py`, `mirror_check.py`, `fix_outcomes.py` | 4,619 | `versus/` |
| `tools/aifuzz.py` | 460 | `fuzz/` |
| `tools/sim/` | ~17,300 together with `hostai/` (C and Python) | `sim/` |
| `tools/hostai/` | (above) | `hostai/` |
| `tools/aibuild.py`, `aibatch.py`, `aitune.py` (+ `tests/aitune/`), `aicalc.py`, `aitime.py`, `qa/ai_research/` probes (`aiprobe`, `factprobe`, `paraprobe`, `effectcheck`, `bpp_dump`, `animcheck`) | 6,397 + tests | `dev/` |

Not ported: the checks for features we do not port (`ainpc_check.py`, `uxcheck.py`, `impactcheck.py`,
`pokeanimcheck.py`, `aura_check.py`, `vscheck.py`, `hardmode_check.py`).

## What the ported tools need changed

- **Imports.** The Spanish tools sit in one flat folder and import each other by name. Here they import through
  `lib/` and their new directories.
- **Symbols.** Read our ROM and our AI build's symbol file, in place of the Spanish `build.ITCM_SYMS` and
  `require_itcm_match`.
- **Speed toggle.** `aivsai`, `aiprops` and `emu.py` import the Spanish speed toggle, which is not ported. Run fast
  through the emulator instead.
- **English text.** Use English strings wherever a tool reads battle text, e.g. the winner line in `aivsai`.
- **Turning the AI on.** Set flags 0x2C2/0x2C3 in RAM, as the Spanish tools do, so the tests do not depend on the
  Options row.
- **Emulator.** py-desmume 0.0.9 with execution hooks. Our harness has hooks on DeSmuME; melonDS has none.
