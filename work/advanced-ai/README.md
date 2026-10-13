# Advanced trainer AI

An optional, stronger trainer AI for the English build. It is ported from the Spanish translation's advanced AI (release
rc44, Spanish workspace commit `dc8577c`, by Luis Ventura, reused with his permission).

When it serves a trainer, it:
- values every move, switch and item by simulating the turn;
- vetoes moves that cannot work;
- picks its lead;
- reads the player's committed action under a gate.

For any battle it does not support, it hands the turn back to the hack's own AI. It is off by default, and the player
switches it on in Options (D-1575: an optional feature for English players).

Everything for the feature lives in this directory. Its tests live in [testbench/](testbench/).

## Status

| Phase | State |
|---|---|
| Plan | Written: [PLAN.md](PLAN.md) |
| 0. Environment and measurements | Tools installed; rc8 standard build and rc8 release reproduced; measurements in progress |
| 1. Faithful extraction | Done: sources vendored (0db9bb3), golden test reproduces rc44 byte for byte (7b12fad) |
| 2. English build of the engine | English payload built (7b12fad); installer in progress |
| 3. Test bench and runtime verification | In progress |
| 4. Options setting | In progress |
| 5. Review and merge | Not started |

## Layout

| Path | What it holds | Added in |
|---|---|---|
| `README.md` | This overview: status, layout, rules, touch points | plan |
| `PLAN.md` | The port plan: decisions, what comes from the Spanish build, memory layout, phases, risks | plan |
| `docs/` | Research, design notes and test reports | plan |
| `PROVENANCE.md` | Every file taken from the Spanish workspace: its path there, commit, sha256, and the permission | phase 1 |
| `src/` | The AI sources: the Spanish files as taken, then our changes as separate reviewed commits | phase 1 |
| `builder/` | `build.py` (compiles and links the AI, `--layout es` or `en`), `install.py` (writes it into an AI build), `verify.py` (re-reads the result independently) | phases 1–2 |
| `payload/` | The reviewed compiler output and its symbols, which normal builds install without a compiler | phase 2 |
| `data/` | The trainer-mark lists (important trainers, keep-lead trainers) and the rule that selects them | phase 2 |
| `testbench/` | Every test and test tool, in three tiers: [testbench/README.md](testbench/README.md) | phases 1–3 |

Every directory gets its own README when it is created: what it holds, what it needs, how to run it.

## Documents

| Document | Contents |
|---|---|
| [PLAN.md](PLAN.md) | The port plan |
| [docs/research-2026-10-13.md](docs/research-2026-10-13.md) | What the Spanish patch's AI is, how it was verified, why it is rebuilt from source, the constraints in this project |
| [testbench/README.md](testbench/README.md) | Test layout, tiers, pass rules, what comes from the Spanish test bench |
| `docs/memory-layout.md` | The chosen placement and the measurements behind it (phase 0) |
| `docs/test-report-*.md` | Test reports (phase 3 onwards) |

Earlier context, outside this directory: `work/notes/es_patch_comparison_20261012.md` compared the Spanish patch with
our rc7 from its bytes alone, before its source was available.

## Rules

- **No game data in git.** Never commit ROMs, saves, extracted files or ROM bytes. Build output and test runs go to the
  ignored `work/build/advanced-ai/`.
- **Provenance.** Every file that comes from the Spanish workspace is listed in `PROVENANCE.md`. A change to such a file
  is its own commit, so the diff from the Spanish original stays readable.
- **Toolchain.**
  - The AI is built with arm-none-eabi-gcc 16.2.0 and binutils 2.47, and the builder refuses other versions.
  - Normal builds install the committed payload and need no compiler.
  - The release repro check recompiles and requires identical bytes.
- **Settings.** Flags 0x2C2 (on) and 0x2C3 (important trainers only), the same as the Spanish build.
- **Scope.** The AI core only. The Spanish battle-experience lines, VS intro, boss aura, luck steering, hard mode and
  NPC are not ported ([PLAN.md](PLAN.md), "Not ported").

## Touch points outside this directory

The feature changes only these files elsewhere. Each change is listed here when it is made.

| File | Change | Phase |
|---|---|---|
| `work/tools/check.py` | Run the static tier; add the `ai` part to `--emu` | 3 |
| `RELEASING.md` | Require the deep tier for a release candidate | 3 |
| `.gitignore` | Build output of `testbench/sim/` and `testbench/hostai/` | 3 |
| `work/research/difficulty-armips/native/options.c` and its settings | The TRAINER AI row on Options page 2 | 4 |
| `CHANGELOG.md`, release notes, credits | The optional feature and its Spanish origin | 5 |
| `AGENTS.md` | One line pointing to this directory | 5 |
