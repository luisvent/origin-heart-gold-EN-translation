# Unit tests

The static tier's own tests for the advanced AI: builder, golden test, ids, and later the installer and trainer
marks. Standard `unittest` files named `test_*.py`, with no emulator.

```sh
.venv/bin/python -m unittest discover -s work/advanced-ai/testbench/unit            # all of them
.venv/bin/python -m unittest discover -s work/advanced-ai/testbench/unit -p 'test_golden*.py'
```

Run from the repository root with the worktree's `.venv/bin/python`.

| File | What it checks | Needs (skips without it) |
|---|---|---|
| `test_build.py` | The toolchain pin refuses other versions and writes nothing. The en payload's schema, region limits, symbols, hooks and words. Steering compiled out (only `ai_serves` calls `check_flag`). No overlay 11 bytes in the payload. Two builds are byte-identical. The committed `payload/` equals a fresh build. The en layout's `before` bytes equal the rc8 release's and the Chinese ROM's | Toolchain; the Chinese ROM and rc8 release for the ROM checks |
| `test_golden.py` | `build.py --layout es` reproduces rc44's overlay 10 slot code, y9 entry, ITCM code, main-RAM AI code and the five hook BLs byte for byte. The sha256s are recorded in the test | Toolchain; the Spanish repository; `work/build/advanced-ai/es/rc44.nds` for the byte comparison |
| `test_ids.py` | Every id in `src/ids.h` names the right move, ability or item in our text banks. `src/IDS.md` lists exactly those ids. `ids.h` equals a fresh Spanish generation. `test_ids.py --write` rewrites `IDS.md` | The Spanish repository with its `work_es/rom/` ROMs and the toolchain, for the generation check only |

## Inputs

| Input | Where |
|---|---|
| arm-none-eabi-gcc 16.2.0, binutils 2.47 | `PATH` |
| Spanish workspace repository (read only; archived at commit `dc8577c` into a temporary directory) | `ADVAI_ES_REPO`, default `~/Downloads/Origin_HeartGold_v4.0.3_EN_v1.0.0-rc3` |
| Untouched Chinese ROM | `work/rom/origin_v4.0.3_cn.nds` |
| English rc8 release | `work/build/advanced-ai/base/rc8_release.nds` |
| Spanish rc44 | `work/build/advanced-ai/es/rc44.nds` |

The ROMs and the Spanish archive are read at test time and never copied into the repository. Each test that lacks
an input skips and names it.

Time: about 10 s for `test_build.py` (two builds), 10–20 s each for `test_golden.py` and `test_ids.py`.
