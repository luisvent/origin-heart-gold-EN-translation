# lib: shared code of the test bench

The emulator runner, the ROM data readers, the pools and the shared tables that every other test bench directory
imports. Most modules are ports of the Spanish workspace's tools (commit `dc8577c`, by Luis Ventura, reused with his
permission); each module's docstring says what changed.

## Import convention

Every test bench script starts with:

```python
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))
import tbpaths  # noqa: E402,F401  (puts every test bench directory on sys.path)
```

and then imports any test bench module by its bare name (`import emu`, `import aibench`, `import aiteams`), wherever
it lives. Module names are unique across the test bench. Run every tool with the project venv:
`.venv/bin/python work/advanced-ai/testbench/<dir>/<tool>.py ...`.

## Modules

| Module | What it is | From the Spanish |
|---|---|---|
| `tbpaths.py` | Paths (`WORK`, `ADV`, `TESTBENCH`, `BUILD`, `RUNS`, `SAVES`), the import convention | new |
| `payload.py` | `load(--payload)` → `Layout`: every AI-build address the tools read (`adv_code`, `orig_code`, `slot_range`, `debug_addr()`, `tune`, the test words), from the build's `payload.json` | replaces `build.ITCM_SYMS`, `require_itcm_match` and fixed constants |
| `emu.py` | `Runner`: headless DeSmuME with hooks, pinned clock, text and heap guards; `set_ai_setting(r, 'off'\|'all'\|'important')` writes flags 0x2C2/0x2C3 into the save in RAM | `tools/emu.py` |
| `emupool.py` | The machine-wide emulator pool (shared with `work/tools/emu_harness.py`'s slots) | `tools/emupool.py` |
| `simpool.py` | The machine-wide simulator pool | `tools/simpool.py` |
| `aidata.py` | `Data(rom)`: species, moves, type chart, stats, damage; names from `names.json` | `tools/aidata.py` |
| `names.json`, `names.py` | The frozen English names by ROM id (species, moves, abilities, items, trainer classes, natures); `names.py make` regenerates the JSON | Spanish `text/en` 0232, 0720, 0033 and `glossary/names_*.json` |
| `savetool.py` | `Save`, `Mon`: battery saves and party Pokémon | `tools/savetool.py` (without `make`) |
| `saves.py` | `path(name)`: a test save checked by SHA-256; `make` writes them from the Spanish commit | replaces the Spanish `tests/*.dsv` |
| `text.py` | `codes_to_text`, `text_to_codes`, `decode_bank` (our `work/tools/charmap_en.tsv`) | `tools/gen4text.py` |
| `romio.py` | `read_file`, `read_narc`, `replace_file` | `tools/romio.py` (no fixed paths) |
| `randteams.py` | Random teams and item/move lists | from `tools/aifuzz.py` |
| `failures.py` | Sorting battle failures (inherited, by design, review); `move_id` reads English and Spanish messages | from `tools/aifuzz.py` |
| `seeds.py` | Round and held-out seeds, the tuning ledger | from `tools/aitune.py` |
| `boot.txt` | The boot script: title screen → Continue → the field | `tests/scenarios/boot.txt` |

## What it needs

- The project venv (py-desmume 0.0.9, ndspy, pillow).
- An AI build's `payload.json` (`--payload`, or `ADVAI_PAYLOAD`), for every tool that runs the AI.
- The test saves: `ADVAI_ES_REPO=/path/to/spanish/repo .venv/bin/python work/advanced-ai/testbench/lib/saves.py make`
  (reads the Spanish repository at `dc8577c` with `git show`; `--es-repo DIR` works too).

## Environment

| Variable | Default | Meaning |
|---|---|---|
| `ADVAI_PAYLOAD` | — | the payload (set by every tool from its `--payload`) |
| `ADVAI_RUNS` | `work/build/advanced-ai/runs` | run output |
| `ADVAI_XDG` | `RUNS/xdg` | DeSmuME's config folder (battery saves); never `~/.config` |
| `ADVAI_EMU_SLOTS` | `EMU_HARNESS_MAX_EMULATORS` or 6 | emulator pool size (0: no pool) |
| `ADVAI_SIM_SLOTS` | 6 | simulator pool size |
| `ADVAI_FPT` | 8 | frames per tile when walking |
| `ADVAI_ES_REPO` | — (required by `saves.py make` and `names.py`; or `--es-repo`) | the Spanish workspace repository |

## Self-tests

```
.venv/bin/python work/advanced-ai/testbench/lib/emupool.py --selftest
.venv/bin/python work/advanced-ai/testbench/lib/simpool.py --selftest
.venv/bin/python work/advanced-ai/testbench/lib/names.py check
.venv/bin/python work/advanced-ai/testbench/lib/saves.py check
.venv/bin/python work/advanced-ai/testbench/lib/payload.py show --payload PAYLOAD [--rom ROM]
```
