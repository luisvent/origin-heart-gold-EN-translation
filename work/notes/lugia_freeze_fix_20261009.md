# Lugia entrance freeze fix — 2026-10-09

**RC7 integration:** [current validation](rc7_validation.md). The parked finding and authorization
used IDs D-2276/D-2277, which collided with later decisions; they are now D-2297/D-2298.
The dispatcher bytes are retained after review. Production hardening adds dependency mutation tests,
a maintained state/recovery oracle, input/output guards and fresh tests against the exact release ROM.

The following records the earlier prototype investigation; its ROM hashes are historical.

The reported freeze is reproduced and fixed on melonDS 1.1. The fix is enabled as
`lugia-animation-state-bounds`, with user authorization recorded in D-2298, the
specific exception to D-1337 for finding D-2297. Nothing has been published.

## Cause and change

After Lawrence's first battle, script 104 moves Lugia (object 13, sprite 426) with
action `0x0D`, repeated ten times. Generic walking initialization at `0x02061684`
calls the animation-state setter at `0x0205E4A4` with state **3**. The special-model
renderer at `0x021F80C0` uses this value to index the callback table at `0x02208F70`.
It has only two entries: `0x021F819D` and `0x021F81C5`. The following words are a
scale vector, `0x1000, 0x1000, 0x1000`. Index 3 therefore makes `BLX r3` execute
`0x1000`, producing melonDS's `ARM9: prefetch abort (00001004)`.

The same event, dispatcher and callback table exist in the Chinese hack. A fresh
Chinese boot reproduces the abort with the two preceding battles bypassed in
temporary script RAM. This establishes the original-hack origin, beyond the
earlier static script comparison. The existing texture-frame guard does not fix
this distinct prefetch abort.

The fix replaces 24 bytes at overlay 1 offset `0x13760` (`0x021F80E0`). An unsigned
bounds check permits only states 0 and 1 to index the table. Unsupported states
retain the current model animation frame and the last valid cached animation
state. Position and visibility updates still run. Animation advancement resumes
when a supported state returns. This is a renderer safety fix; it does not invent
an animation for the unsupported walking state. Scripts, battles, graphics and
saves are unchanged, and no overlay grows.

The original callbacks preserve r6 and do not change the object's animation state.
Recovering the selected state from r6 replaces the redundant state-getter call,
leaving space for the check. Read-only assembly guards cover the enclosing routine,
both callbacks and their table. The registry limits writes to the 24-byte block.

## Evidence

All ROMs, saves, screenshots and machine-readable traces below are local and
ignored under `work/build/lugia-fix-20261009/`. Emulator: existing headless melonDS
1.1, commit `b86390e4428bf38ce4c1ce0e9ca446d6d25955e8`, interpreter, software renderer,
built-in BIOS, direct boot. The supplied battery save remains unchanged:
SHA-256 `6dcb4b9acd82a7dc349e3d7432445fb10f2c9d9dd52d51f08c86b9dd5f86f04d`.

| Test | Original | Fixed |
|---|---|---|
| Natural English checkpoint after Lawrence, obtained by winning both preceding battles with ordinary controls | Freezes before Lugia appears; exact reported picture and prefetch abort | Lugia appears, scene continues, Lugia battle reaches its command menu |
| Normal Lugia battle continuation with ordinary controls | Unreachable due to the entrance freeze | Battle plays turns, party switch works, a loss returns to the Pokémon Center without CPU exceptions |
| Fresh Chinese boot and supplied save, accelerated diagnostic | Prefetch abort, story variable `0x40A4 = 7` | Scene reaches its ending, variable becomes 8; no CPU exceptions |
| Fresh English boot and supplied save, accelerated diagnostic | Same prefetch abort, variable 7 | Scene reaches its ending, variable 8; no CPU exceptions |
| Forced valid animation states 0 and 1, three frames each | Reference callback reads, animation IDs/frames and cache | Identical results to original |
| Forced unsupported states 2, 3, `0x7FFFFFFF`, `0xFFFFFFFF` | Not run in this state matrix | No callback-table reads; frame and cache preserved; no CPU exceptions |

The natural replay loads the pre-crash melonDS checkpoint from the original
investigation, then synchronizes the renderer's 24 bytes and the existing texture
guard branch to the tested ROM. Savestates contain executable RAM, so loading an
old state without synchronizing code would continue running the original bug.
There are no event, party or battle bypasses in this replay. Its initial evidence
is `candidate/appearance.png`, `candidate/result.png` and `candidate/report.json`.
The continuation is saved under `natural-battle/`, `natural-finish/` and
`natural-ceruledge/`. It used Bulk Up, Roost and Brave Bird with Corviknight,
then switched to Ceruledge. The party lost; this is evidence for battle and loss
cleanup, not a natural victory-path test. `natural-ceruledge/poltergeist.png`
shows the Pokémon Center after the battle. The battle-turn helper's timeout in
`natural-finish.log` is the mandatory replacement screen after Corviknight fainted;
ordinary touch input subsequently continued that same battle.
`natural-ceruledge/loss_return_control.json` confirms ordinary DOWN input moves
the player from map 236 (8,13) to (8,15), with no CPU exceptions after the loss.

The fresh-boot tests load executable code from the actual ROM. `emu_lugia.py`
verifies script 104's hash and substitutes three GoTo commands in disposable RAM:
offsets 469→494, 881→906 and 1270→1295. These skip the Rocket, Lawrence and Lugia
battles and their win checks. Everything else in the scene runs. Consequently
these tests prove the scene reaches its ending, not a normal battle victory or
post-battle walking. The first diagnostic attempted a walking assertion; it failed
despite reaching variable 8 with no abort. Those reports are preserved under
`fresh-*-fixed/`, and are not counted as passed tests. The narrower final oracle
is explicit in the checked-in runner and the `verified-*-fixed/` reports.

Reports: `verified-chinese-original/report.json`, `fresh-english-original/report.json`,
`verified-chinese-fixed/report.json`, `verified-english-fixed/report.json`.
The animation-state watchpoint matrix is `state-checks/report.json`; its scratch
runner is `check_states.py`. It compares actual callback table bus reads and model
animation state, rather than merely recognizing patch bytes.

## Build and validation

The full default English build passes the normal build verifier (message NARC
round trips, exported text, names, glyphs, graphics, hardcoded patches and text
speed). It is byte-identical to the previous English development ROM with only
this new registry fix applied. `test_asmpatch.py` and `test_emu_fixes.py`: **86 tests
passed**, including guarded real-ROM assembly, synthetic assembly, individual
golden hashes and all fixes together. The shared overlay's original size and
overlay table are preserved.

The local `Origin_HeartGold_v4.0.3_EN_lugia_fix.xdelta` is built against the clean
USA HeartGold ROM (CRC32 `C180A0E9`). The build reapplied it and verified an exact
match with the fixed ROM. It is a development test patch, not a published release.

| ROM | SHA-256 |
|---|---|
| Original Chinese | `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8` |
| Chinese plus this fix only | `e640dcb19bf2075617fc31eb10858fd338d1534e8fc59617bd7a2352be2acdd6` |
| English development control (existing other fixes enabled) | `d5442d367ebfa552d4cc4e6a014350fda426e310a7180f2a41151dafc9d1aed7` |
| Full fixed English build | `2ad557dfee60d96eca1424505505d2d552343ffdc47ad2f5289ef0b34b4a9e45` |

Example diagnostic (from the repository root, with the supplied save available):

```sh
.venv/bin/python work/tools/emu_lugia.py \
  --rom work/build/lugia-fix-20261009/full-fixed.nds \
  --sav '$HOME/Downloads/Pokemon - HeartGold Version (USA)-patched.sav' \
  --out work/build/lugia-fix-20261009/recheck --expect fixed
```

Use `--expect original` for the original Chinese or English control ROM. Use a
fresh output directory each time. This supplied private save is not a standard
fixture, so `emu_fixes.py` lists this separate regression explicitly in its
coverage gaps instead of claiming the generic `fixes` suite runs it.

Hardware and Delta remain untested. No claim is made about unrelated animation
dispatchers or other Lugia encounters.
