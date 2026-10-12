# Issue 10 — supported shared-progress repairs, 2026-10-09

**Two guarded repairs are enabled locally and verified offline.** D-2300
supplies the specific exception to behavior fidelity; D-2308 records the two
operand choices and verification limits. D-2309 records the unresolved hunt
compatibility design and excluded Deoxys retries. No emulator was launched or
requested, no download/commit/publication occurred, and source saves are intact.

## Changes

| Finding | Enabled patch | Exact member change in `a/0/1/2` |
|---|---|---|
| D-1579, expedition erases beasts eligibility | `expedition-completed-progress` | 962: byte136 `01→04`; condition at134 becomes unsigned greater-or-equal after unchanged Compare409F,10 |
| D-1580, Ho-Oh panel skips Silver | `hooh-panel-silver-marker` | 45: bytes184–185 `35 02→00 00`; ClearFlag565 becomes native no-op ClearFlag0 |

The first guard pins halfword136 `0x3601→0x3604`, including unchanged
first displacement byte137. Its entire6788-byte source member SHA-1 is
`33cb77c9032d91186fa1680ae2b28919b4f58be5`. Existing target5827 gives
completed dialogue for10/11/12 without recruitment, battle or progress writes.
States0..9 retain their previous choices; native Lance10→11 and beasts11→12
remain unchanged. Partner dialogue checks and every other409F use are intact.

The second guard pins halfword184 `0x0235→0x0000` and the entire638-byte
source member SHA-1 `278274f4576dfe1234847d3e487ca3605a83ad56`.
The actual native flag0 resolver returns null and ClearFlag performs no save
write. Solved-panel HidePerson1, Clear273, Set546 and Warp315/5/24/0 remain
native; unsolved-panel behavior and every dream byte remain unchanged.
Legitimate Silver nonloss completion still clears565. A previously cleared
marker stays clear; the patch does not replay or unlock Silver.

These prevent future unrelated writes. They **do not repair old damaged saves**:
409F=3 can be legitimate recruitment, and565clear can be legitimate Silver
completion. No reset, new state allocation, migration or save hook is added.

## Reusable native execution and focused checks

`work/tools/native_script_state.py` promotes the private bounded executor,
without any ROM/member dumps, game text or embedded native instruction payload.
It reads local ROM code and dispatches the actual command table020F793C.
`Scene.run` has no script-memory patch option. The caller supplies local source
pins/variants. Native instruction ranges, private memory mappings, instruction
and script budgets and unsupported-command rejection remain explicit.

`work/tools/test_shared_progress.py` applies the real NARC registry entries to
local CN bytes. Nine tests check exact member/operand changes, unchanged entry
and command addresses, independent expected-byte and entire-member guards,
actual native state predicates/writes and bounded-executor rejection. With the
existing NARC suite, **18 tests pass**. Ruff check/format and registry checks pass.

Native controls include:

- Gate states0..12 and unsigned65535. States0..9 retain destinations;10/11/12
  reach5827 without persistent writes. The65535 case verifies the unsigned
  comparison boundary, not natural quest reachability.
- Full late leader paths10/11/12 × Yes/No × raw battle outcomes0..7: no battle
  is reached and the input progress value remains intact. An original native
  state11/Yes/nonloss/accept control really writes3.
- Full precompletion0/1/2/4/6/7/8/9 with accept/nonloss, decline, loss and draw:
  actual cursor/write/outcome traces agree after normalizing the intentionally
  changed condition operand. Native Lance and beast-release segments still
  write11 then12. Beast event eligibility is parsed from actual event records.
- Solved/unsolved panel × marker565set/clear, both original and patched.
  Native ClearFlag0 emits zero persisted writes, while native puzzle flags and
  warp arguments remain correct. Arrival selects3499 with marker retained,
  3305 with marker already clear. All raw Silver outcomes0..7 retain their
  original native result handling and legitimate marker clear.

Fixtures supply menu choices, puzzle output, battle outcome, coordinates and
save allocation. Message/movement/fade/battle-render/map-service commands are
logged boundaries. HidePerson's native handler and flag setter run; object
lookup supplies real event hide flags, while object destruction is omitted.
Parsed event selection is not native coordinate-trigger execution. See the
reproduction note for the complete fixture/native boundary.

## Paired current-tree builds

Both builds use local armips0.11.0, all current text/graphics and
`--no-regen-graphics --no-patch`. Both pass the full builder verification:
text/export equality, NARC round trips, glyphs, graphics, hardcoded patches and
text-speed checks. Outputs exist only under ignored
`work/build/bugfix-sequential-20261009/issue10/fix/{without,fixed}/`.

| Artifact | SHA-256 |
|---|---|
| Without both repairs; identical to preceding issue06-fixed ROM | `1f955bf433e69ba47d688749d70a635da8c5d9c024e838ed7cd8499dd76bbfa2` |
| Fixed current tree | `50a5b4a91a401f85392068cc15731406c46c15c5ea703c013c1e93e90f3bee5c` |
| Fixed member45 | `a7a0f4623faf11e053f0e71be695ac1cd1c7490d15046fccd7b4785dc024b4cd` |
| Fixed member962 | `61d3570360f6a938c2c3f96525da197d47c749b1745b89b33787e9477ddf57cb` |

Private `pair_check.py` / `pair-summary.json` independently prove equal ROM
size278780608, only fileID132 changed, only NARC members45/962 changed, and
exact raw ROM differences at136242708,136242709,137578140. Member45 offsets
184/185 and member962 offset136 are the complete changes. ARM9/ARM7 and
both overlay tables are identical. Entire overlay14 and script members17/129
match the preceding verified build, preserving all three earlier repairs.

Root English ROM, RC7, source battery and existing `expected.toml` hashes were
captured before work and independently checked afterward. They remain intact.
The coordinator retains final expected-hash refresh; this stage leaves it alone.
`FIXES.md` was regenerated from the registry, preserving earlier enabled fixes.

## Actual built-ROM matrix

Private `fix/matrix.py` reruns the preceding native matrix against **both actual
paired built ROMs**, through the promoted executor. No handpatched script is
substituted. **104 passing cases per ROM; zero unsupported bounded-matrix
cases.** Historical candidate-label permutations remain as17 repeated controls
in each variant (87 distinct scenario configurations); all fixed permutations
execute the same fixed ROM bytes. Expectations follow the actual build variant.

All **56 unaffected quest/dream cases produce identical complete traces**.
Affected leader/panel cases assert the intended new state/destination directly.
All used script members except45/962 and all ten event members are identical.
The retained separate full Forest attempt fails closed at52@1290 ScrCmd_459
in both builds and is never counted as a completed scene or passing matrix case.

The matrix executes401 distinct native instruction addresses and reads1030
ARM9 byte addresses, all checked for equality between builds. Address-plus-byte
SHA-256 `fe7573ce9f5584b7e1416804103c4588f85b67ebbfdc2f908325f5814a3e866a`
also matches the preceding CN/EN reproduction. Code range and command-table
pins are retained in private `summary.json`; complete per-case handler/cursor,
write/compare/stub/instruction traces are in `matrix.json`.

## Deferred/excluded cases and remaining limits

**D-1581 remains deferred.** The hunt/Forest/Route25 collision is proven and
unchanged by these patches. Before allocating a separate domain, audit native
and computed/script-header/event uses of the candidate variable, define an
old-save compatibility policy covering legitimate Sammy progress and ambiguous
hunt values, and demonstrate the relevant continuation beyond command459.
Do not globally remap4099 or infer a reset/migration from literal-use inventory.

**D-1578 remains excluded from retry/unlock repair.** The native loss/draw
transition consumes the Red Star without the chief claim, but an intended
loss continuation is unproved. Restoring2188 introduces another legendary
attempt; clearing1331 skips the chief scene; bypassing whiteout changes defeat
recovery. None is implemented. Further work requires narrative evidence and a
deliberate pending-scene/recovery design, outside this narrow fix.

**Verification is offline native execution, not full-game emulator validation.**
No naturally reached full expedition, puzzle, Silver or beast scene, map load,
rendering, complete battles, save/reload or hardware behavior was exercised in
this stage. Structural ordering comes from the preceding investigation. Host
emulator approval remains unavailable; no new request was made.

## Reproduction commands

Run from repository root:

```sh
.venv/bin/python -m unittest work/tools/test_narcpatch.py work/tools/test_shared_progress.py
.venv/bin/ruff check work/tools/native_script_state.py work/tools/test_shared_progress.py
python3 work/tools/fixes.py check
python3 work/tools/fixes.py docs --out work/patches/FIXES.md
.venv/bin/python work/tools/build.py --armips $HOME/Developer/armips/build/armips --work-dir work/build/bugfix-sequential-20261009/issue10/fix/without --without expedition-completed-progress,hooh-panel-silver-marker --no-regen-graphics --no-patch
.venv/bin/python work/tools/build.py --armips $HOME/Developer/armips/build/armips --work-dir work/build/bugfix-sequential-20261009/issue10/fix/fixed --no-regen-graphics --no-patch
.venv/bin/python work/build/bugfix-sequential-20261009/issue10/fix/pair_check.py
.venv/bin/python work/build/bugfix-sequential-20261009/issue10/fix/matrix.py
```
