# Double-battle horizontal fallback: fresh validation (2026-10-09)

The separately approved horizontal fallback passes **26/26 fresh CN/EN emulator cases**,
covering the historical 22-case matrix and four new ally-selection cases. A separate fresh boot of the
historical Option 2 Chinese ROM reproduces the missing Left-to-ally transition and fails the new oracle
for that intended defect. The extra focused CN confirmation and discarded setup attempts are outside
these counts.

## Builds and identities

All local artifacts are under ignored `work/build/double-target-horizontal-validation/`. No original input or old-worktree file was modified; no ROM or patch was published. Every completed case records
ROM/save SHA-256 before and after execution and requires equality. The ROM is booted anew from a copied
battery fixture; savestates are created only afterward for direction probes within that same ROM.
No target-navigation instructions are replaced in RAM.

- Original Chinese source SHA-256: `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8`.
- Chinese ROM, only the targeting fix applied through guarded armips: `7be3bacda92805cdb64acdc30838f6a285594bb34e27651fc4775d8bea2fb259`.
- English full build at the reviewed 36-fix snapshot: `81017f681a3687108528f88e57adbd0f705036f1ce4004ea0f7af13fc8e4a98a`.
- Historical Option 2 Chinese negative control, copied from the old worktree: `ce01ef2496f8665e493a2c39bb87735b56d06c6c87403ef153263916cc3491cb`.
- Unchanged six-mon input save SHA-256: `b3aca10747cd0f1adc3d5852a50dddaaa36ed8680f5ba04012cfe3110faad90f`.

The full English build differs from the prior verified armips-port build only in `file14`
(ARM9 overlay 14), still 337,216 stored bytes. The decompressed overlay changes 105 bytes relative
to historical Option 2. Independently encoded Thumb replacements reproduce the complete new overlay;
text and every other ROM part match. `delta-review.json` records this comparison. Relative to untouched
Chinese, the standalone targeting patch changes 166 bytes in overlay 14 and no other file.

The reviewed full-build pins, recorded in `work/patches/expected.toml`, are:

| Part | SHA-1 |
| --- | --- |
| non-text | `a93a1719f8f7dc4746c107997b6e9332d860caaa` |
| text | `922a51f5639fda62fce76bc678793c050fac7a46` |
| ROM | `6ddf616418052a0fbf15ea28e790f436a2bc21ac` |
| xdelta | `c3b78a38286fb3e32fc4d9a65f6e21049ca401bc` |

## Fresh emulator matrix

[emu_double_target.py](../tools/emu_double_target.py) uses the current main harness, py-desmume,
headless SDL, read-only execution hooks and a geometry oracle independent of the assembler/Thumb model.
Direction probes test two repeated presses and Down/Up from each entry target. The cases advance real
battle commands and turns, and field/spread tests observe the actual native representative returned
to the engine. Wild cases find real double encounters; fainted foes and replacement behavior are real.
Only a disposable battery copy's moves/PP and scenario flags/location are prepared before boot; trainer
cases invoke an existing battle script through the harness.

| Case | CN | EN | Target screens, CN / EN |
| --- | --- | --- | --- |
| lastR | PASS | PASS | 6 / 6 |
| lastL | PASS | PASS | 6 / 6 |
| leak | PASS | PASS | 6 / 6 |
| field | PASS | PASS | 4 / 4 |
| spread | PASS | PASS | 4 / 4 |
| multi | PASS | PASS | 3 / 3 |
| wildR | PASS | PASS | 6 / 6 |
| wildL | PASS | PASS | 6 / 6 |
| cancel | PASS | PASS | 6 / 6 |
| empty | PASS | PASS | 6 / 6 |
| single | PASS | PASS | 0 / 0 |
| allyL | PASS | PASS | 6 / 6 |
| allyR | PASS | PASS | 6 / 6 |

Total: **130 target screens**, plus two singles runs with no target screen. CANCEL stays
selected under Left/Right, A and B both cancel and reentry picks an eligible foe. Empty-foe touch is
rejected. Single battles complete three commands without target selection. Spread/field modes keep
the first eligible representative and their original controls.

The new cases require all six target screens in order (`t1_c0` through `t3_c1`), actor sequence
`[1,2,1,2,1,2]`, a critical A acceptance and engine submission, then an actual next-turn actor-1 menu
after that submission:

- `allyL`, both languages: mode 9, eligibility `[1,1,0,0]`, empty foe 3, entry foe 1. Left selects ally 0;
  A accepts 0 and the engine receives 0. The next turn proceeds.
- `allyR`, both languages: mode 8, eligibility `[0,0,1,1]`, empty foe 1, entry foe 3. Right selects ally 2;
  A accepts 2 and the engine receives 2. The next turn proceeds.

The read-only hooks are `0x02212634` (`r6`, accepted UI slot) and `0x0221266E` (`r2`, target passed to
battle command submission). Native `0x02212A3C` converts slots 0–3 identically. These addresses and the
validator were reviewed independently. Historical Option 2 completes the same six-screen negative
control but stays on foe 1 after Left; it accepts/forwards 1. The new oracle rejects it with:
`('t2_c1', 'LEFT', 'foeR(FR)', 0)`.

All reports were revalidated against the final oracle. `matrix-summary.json` and `final-summary.json`
contain the matrix and fingerprints; `matrix/<language>-<case>/report.json`, screenshots and logs retain
raw evidence. `old-cn-allyL-v3/report.json` is the separate negative control.

## Gates and limits

Fourteen targeting-specific tests pass (nine assembled machine-code tests and five harness-evidence
tests); targeted ruff passes. Evidence tests reject historical behavior, missing/wrong acceptance,
wrong engine targets, missing or incomplete next-turn/command evidence, and check adjacent priority,
mirrored fallback and CANCEL/outward edges. Independent review additionally rejected nine corruptions
of the actual old-ROM evidence and verified the historical oracle across all 320 geometry inputs.

The reviewed snapshot's full check passed assembly, guards/listings, USA claims, build verification and
958 tool tests (26 skipped), 46 docs tests and 36 site tests. Its update run recorded the reviewed hashes;
that run's overall result was FAIL because concurrent unrelated difficulty research had three unused
imports. `check-full-final.log` preserves the exact result.

A final current-workspace recheck also reports concurrent, unrelated `zero-pp-struggle` integration
changes: stale `FIXES.md`, its missing listing, five dependent global registry/coverage/golden tests,
those research unused imports, and a changed full-build non-text hash. That newer 37-fix build has ROM
SHA-1 `fb29a56cff4c83b7cc428ae9d034b91d0a2fcc12`; it is not the English artifact exercised in this matrix
and was not re-pinned here. `check-full-recheck.log` records the failures. The targeting task does not
claim the current whole-workspace gate passes.
A post-documentation targeting/coverage test run executes 64 tests: the 14 targeting tests and
49 other coverage tests pass; its sole failure is the unrelated new `zero-pp-struggle` missing from
the unified coverage register (`targeted-final-tests-with-coverage.log`).

Earlier RAM fixture setup attempts were discarded: a frame boundary can pause the native XOR crypt
loop while flags are still zero, so a diagnostic party read does not prove the record is safe to edit.
The final runner uses strict preboot edits on a copied battery and waits read-only until all live
records have valid checksums/closed flags and the prepared species/moves. It never relaxes the shared
codec's checksum gates. This is emulator validation; no hardware result is claimed.

## Evidence oracle strengthening (2026-10-09)

The validator now requires exactly `UP`, `DOWN`, `LEFT`, `RIGHT`, and `DOWN,UP` on every target
row. Each cardinal probe must contain two sample pairs; the composed probe must contain one flat
final pair. Every recorded slot must be known and match the expected transition. Single-target
initial and probe quadrants must match the recorded/expected slot, including self modes 4/6 and
CANCEL. For spread modes 1/2/3/5/7, a group highlight's classified region is independent of its
representative; only an actual CANCEL cursor requires the CANCEL region.

The current focused gate passes **28 tests**: nine assembled machine-code tests and **19 harness
evidence tests**, plus targeted ruff. Complete, independently authored fixtures cover both ally
directions and historical navigation. Mutation tables reject missing/unknown probes, incomplete or
extra repeated samples, malformed pairs, unknown/wrong slots, wrong/missing visual quadrants,
missing/wrong engine acceptance, and incomplete subsequent command/turn evidence. Synthetic tests
cover both self modes and all five spread modes, including mode 5 absent from the emulator matrix.

The stronger oracle revalidated the **existing 26 reports and 130 target screens** successfully;
this was **zero new emulator runs**. The preserved historical control passes `horizontal=False`
and fails the current oracle at `('t2_c1', 'LEFT', 'foeR(FR)', 0)`. Copies of the real CN allyL log
with all probes removed except the critical LEFT, or every probe quadrant replaced by FR, are
both rejected. Historical reports remain byte-for-byte unchanged. The ignored artifact directory
`work/build/double-target-evidence-strengthening/` contains `targeted-tests.log`, `targeted-ruff.log`,
`revalidation.log`, and `revalidation-summary.json` with report fingerprints and the reproducible
`revalidate.py`. This focused recheck does not change the earlier full-workspace gate claims.

## Reproduce

Run from the repository root with the existing local dependencies; no downloads:

```sh
ARMIPS=$HOME/Developer/armips/build/armips .venv/bin/python -m unittest -v work/tools/test_double_target.py work/tools/test_emu_double_target.py
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy EMU_HARNESS_EMULATOR=desmume .venv/bin/python work/tools/emu_double_target.py --rom work/build/double-target-horizontal-validation/horizontal-cn.nds --case allyL --out work/build/double-target-horizontal-validation/repeat-cn-allyL
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy EMU_HARNESS_EMULATOR=desmume .venv/bin/python work/tools/emu_double_target.py --rom work/build/double-target-horizontal-validation/full/origin_hg_v4.0.3_en_wip.nds --case allyR --out work/build/double-target-horizontal-validation/repeat-en-allyR
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy EMU_HARNESS_EMULATOR=desmume .venv/bin/python work/tools/emu_double_target.py --rom work/build/double-target-horizontal-validation/option2-cn.nds --case allyL --expect-option2 --out work/build/double-target-horizontal-validation/repeat-old-cn-allyL
```

Use a new output directory each time. The supported cases are the 13 table rows; `--sav` allows an
explicit local battery fixture. The local `run_matrix.py`, `build_cn.py`, `review_delta.py` and
`summarize.py` scripts under the artifact folder preserve the exact execution recipe and review.
