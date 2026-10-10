# Double-battle targeting: armips port (2026-10-09)

The root `2v2BATTLE_CONTROL.md` stops at a proposed, unapproved implementation. Investigation found
later work in `.claude/worktrees/double-target-option2/` (branch `codex/double-target-option2`): the
Option 2 source, eight enabled legacy patch entries, host interpreter, tests, and a 2026-10-07
validation report. Its plan records user approval on 2026-10-06 as a specific D-1002/D-1337 exception.
The preserved [historical plan](double_target_option2_plan.md) and
[validation report](double_target_option2_validation.json) provide the evidence; no new policy is inferred.

## Result

`work/patches/double-battle-targeting/fix.toml` registers the enabled fix; its `.asm` writes all eight
regions through the normal armips stage. The replacement occupies the same 164-byte first-eligible /
navigation block and redirects four navigation calls, entry and fallback, plus the CANCEL validity check.
Every edited halfword has an original-byte guard. There is no growth, ITCM payload, allocation or new
build stage. GNU numeric labels, instruction spellings, literal pooling and placeholder branches were
converted to armips syntax. No clang generator or duplicate replacement-byte manifest is needed.

Single-target entry retains a living eligible remembered foe, otherwise chooses a living eligible foe
left first. Vertical navigation retries the other column only after the original search fails. The
separately approved horizontal extension below retries the other Pokémon row after an ineligible
adjacent Pokémon slot. CANCEL remains selected. Spread order and representative engine value remain unchanged. Memory is still shared;
Option 4's per-battler memory was a design proposal and is not implemented here. Bradams/Speedoption is
credited for independently diagnosing the issue; no code or patch bytes from that fork are reused.

## Initial port baseline (before horizontal extension)

- Local armips v0.11.0 assembled against untouched Chinese v4.0.3 with guards enabled.
- The initial eight replacements matched the approved legacy values byte for byte. Baseline replacement SHA-256:
  `033684cfa3318d513f840443e0f270918950b57f66da3d981084e7da6ec1f675`.
- The initial `test_double_target.py` executed the assembled machine code: 16 native-order masks, 16 foe-first masks,
  320 navigation cases (exactly 11 formerly stuck cases change), 256 repair cases, 224 entry cases.
  It checks stack balance and saved registers while external-call stubs clobber volatile registers/flags.
  All five spread call sites are unchanged. The replacement digest pins equivalence to the old work.
- Individual overlay14 SHA-1: `4b11c7caeb9a2e2ff553a74e75dc6ca17ff0792c`.
  Combined armips overlay14 SHA-1: `433f58508ecf77d5242412d8966b83e780130351`.
  Both golden pins were derived by applying the old manifest's values independently; the previous combined
  golden was checked before adding this fix. Assembly refuses changes outside the declared regions.
- Full `check.py --full` passed (52.5 s): registry/docs/lint, synthetic assembly, guarded real-ROM
  assembly, snapshots, 20 USA claims, 949 tool tests (26 skipped), 46 docs tests, 36 site tests, and
  a fresh full build matching the updated expected hashes. Log: `work/build/double-target-armips/final-check.log`.
- Unified emulator coverage explicitly lists this fix as outside that runner; historical live evidence
  is kept separate from the current exhaustive host tests.

The 22/22 CN/EN emulator matrix and six open/arceus/vqueue runs are **historical**, dated 2026-10-07;
they are not claimed as new runs. The initial migration verified byte equivalence and host behavior anew.
Original ROMs, saves and the old worktree are unchanged. Local generated build artifacts stay ignored.

## Separately approved horizontal fallback (2026-10-09)

Review found a remaining graph gap: mode 9 with presence mask 7 has eligibility `[1,1,0,0]` and
entry target foe 1. Historical Option 2's D-pad transitions from foe 1 and CANCEL 4 only reached
each other, leaving eligible ally 0 unreachable. The user explicitly approved the following extension:
horizontal movement tries its adjacent slot first, then the other Pokémon row in the same direction
only if that adjacent Pokémon slot is ineligible. Horizontal movement on CANCEL and outward edges
retain native behavior. Vertical search, target entry, repair and spread behavior retain Option 2 results.

The navigation routine now starts at `0x022127B8`; first-eligible, foe-first and entry addresses are
unchanged. It still fits **164/164 bytes**, including its aligned literal pool, with all eight original
guarded regions unchanged. Updating the grid index directly saves four bytes: validate the destination
column, add `dx + 2*dy`, then check the index with unsigned `<=5` before reading the grid. Underflow
therefore exits safely. Both retry types share the same one-retry guard, using start-index XOR 1 for
vertical and XOR 2 for horizontal. An ineligible horizontal neighbor is necessarily in a Pokémon row,
because both CANCEL cells are accepted before eligibility is consulted.

The entry wrapper saves another four bytes by testing the remembered target's low bit with LSR/carry.
Valid odd slots are exactly foes 1 and 3. Other odd unsigned values remain stored only until the native
unsigned repair rejects them; no invalid value indexes the eligibility buffer. Even values are still
invalidated before repair. Final entry results are unchanged, including spread and invalid boundaries.

Current implementation-step verification (host only; no ROM build or live emulator run):

- Armips v0.11.0 assembles with original-byte guards and the no-outside-write/size-change checks.
- Nine `test_double_target.py` tests pass: 16 native and 16 foe-first masks; 160 exact vertical transitions
  (the same 11 historical changes); 160 exact horizontal transitions (16 additional changes); 256 repair
  cases; 416 entry cases including odd/even values near `0x80000000` and `0xFFFFFFFF`; all five unchanged
  spread call sites; the explicit mode-9 eligibility regression; graph reachability for all 48 eligible/
  CANCEL starts across 16 masks. All starts reach every eligible slot and CANCEL. The interpreter guards
  four-byte eligibility indexing, stack balance and saved registers while external calls clobber volatile
  registers and flags.
- `expected_replacement_regions()` independently encodes the reviewed Thumb design, including calculated
  branches/literal loads, without reading armips output. The assembled full overlay equals the native
  overlay with only those expected regions replaced. New replacement SHA-256:
  `259a43fbdd573c8f7eb6d754af01dcbd13438d7a56ffd6233466e92085bc1914`.
- Updated individual overlay14 SHA-1: `2d68b430e5dc83264b870d5c4c35c0f40c47060b`.
  Updated combined armips overlay14 SHA-1: `bac3f158bec872b177b3b049e35c76baf60c1345`.
  Both derive from independently encoded expected regions; prior individual/combined golden pins were
  verified against the historical snapshot first. Local derivation: `work/build/horizontal-fallback/derive_pins.py`.
- Targeted suite: **129 tests pass** (`test_double_target.py`, `test_asmpatch.py`, `test_asmlisting.py`,
  `test_emu_fixes.py`). Registry/docs and generated listing checks pass.
- Updated snapshot: `work/patches/double-battle-targeting/double-battle-targeting.listing`.

The initial byte equality and historical 22/22 matrix establish the prior Option 2 baseline only.
The separately approved horizontal extension now has fresh **26/26 CN/EN emulator cases** (130 target
screens), including both mirrored ally-selection cases, A acceptance/engine submission and next-turn
progression. A separate fresh historical Option 2 control fails the intended missing ally transition.
The reviewed full build was compared independently and its expected hashes updated; later whole-workspace
checks also observed unrelated concurrent fix/research integration failures, so no current full-gate
PASS is claimed. See [fresh validation and reproduction](double_target_horizontal_validation.md) for
ROM/save identities, the dedicated runner, raw artifact paths and exact check results.

## Reproduce

Run from the repository root using the existing venv and local armips (set `ARMIPS` to its executable).
No downloads are required.

```sh
.venv/bin/python work/tools/fixes.py check
.venv/bin/python work/tools/asmpatch.py check --only double-battle-targeting
.venv/bin/python -m unittest work/tools/test_double_target.py work/tools/test_asmpatch.py work/tools/test_asmlisting.py
.venv/bin/python work/tools/check.py --full --work-dir work/build/double-target-armips/recheck
```

Use `build.py --without double-battle-targeting` for a control build. Distribute only xdelta patches.
