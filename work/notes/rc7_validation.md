# RC7: historical planned contents and prior candidate validation

Current 14-fix combined preparation and its actual gates/runtime results are in
[RC7 release preparation](rc7_release_prep_20261010.md). The contents and packaging statements below
are historical; the older Lugia-only artifacts remain untouched.

## Planned contents

The user has requested the reviewed `double-battle-targeting` fix as part of RC7 alongside
`lugia-animation-state-bounds`. Targeting is already enabled in
[fix.toml](../patches/double-battle-targeting/fix.toml). It retains an eligible remembered foe or
opens on a living eligible foe, left first; vertical and horizontal retries give D-pad access to
eligible foes and allies, CANCEL stays selected, and spread targeting keeps its original behavior.

[Targeting validation](double_target_horizontal_validation.md) records 26/26 fresh CN/EN emulator
cases and 130 target screens on the identified targeting builds, plus the strengthened validator's
successful revalidation of those reports and 28 passing focused tests. The
[armips port note](double_target_armips_port.md) records implementation and approval provenance.
These are separate from the prior Lugia-only artifact below. They do not establish a combined RC7
release-gate pass; the targeting note records the limits of later whole-workspace checks.

Packaging and release are deferred. No new combined RC7 candidate, package, metadata or checksums
were created for this inclusion. Existing `work/build/rc7/` and `work/release/v1.0.0-rc7/` artifacts
remain the prior Lugia-only candidate and must not be treated as containing the targeting fix.

## Prior Lugia-only candidate — 2026-10-09

The previously assembled local RC7 candidate integrates the reviewed
`lugia-animation-state-bounds` fix on the RC6 baseline
(`a657a13`). D-2297 records the finding; D-2298 authorizes this exception to D-1337.
The parked branch's D-2276/D-2277 were already assigned to unrelated decisions on
this branch, so those records were recreated through the decision tool under new IDs.

## Change and hardening

Lugia's walking state 3 indexes past a two-entry animation callback table into a
scale vector. The original renderer branches to `0x1000` and prefetch-aborts.
The 24-byte replacement checks the state **unsigned** before indexing; states 0/1
retain their callbacks and cache behavior, while unsupported states keep the last
frame/cache and continue the existing position/visibility updates. No overlay grows.
The prototype's machine code was retained after review and additional validation.

Production integration adds:

- Independent hand-encoded expected bytes and complete overlay/table boundary checks.
- Seven mutation cases outside the write region: NULL/inactive dispatch exits,
  position-update continuation, literal pointer, both callbacks and both table entries.
  Assembly must fail when these dependencies change.
- A maintained melonDS state matrix (`work/research/lugia/check_states.py`), with
  assertions for callback reads, frame/cache parity, unsupported states and recovery.
- A fresh-boot scene runner (`work/tools/emu_lugia.py`) that pins the save and event
  script identities, requires a fresh output directory under ignored `work/build`,
  preserves CPU exception counters from boot and verifies inputs remain unchanged.
  Its oracle rejects missing evidence, unrelated faults and the wrong final scene.
- Current registry documentation, disassembly listing, expected build hashes,
  coverage-gap declaration, release notes and local release packaging.

## Exact prior artifact

| Artifact | SHA-256 |
|---|---|
| Released RC6 ROM, local comparison input | `2cac407119f3bb5ee85568c06242fcbac3484331f8f6539ab5fe32187234a005` |
| Prior Lugia-only RC7 ROM, local only | `b16f81bec13b07730ee544fbe24aead4229eccf04368f186aa71abe0b48710df` |
| Prior Lugia-only RC7 xdelta | `790bdc11b585588548b27f134a7b7e0d8ebee1126669d03a60806726407251e1` |

The prior RC7 ROM differs from released RC6 at **20 bytes**, all inside overlay 1's
24-byte dispatcher region (`0x021F80E0..0x021F80F7`). No other ROM byte differs:
text, scripts, graphics, other fixes and save layout are identical. Comparison:
`work/build/rc7/rc6-diff.json`.

Prior local deliverables are under `work/release/v1.0.0-rc7/`: the xdelta, ZIP, README,
checksums and metadata. The ZIP contains the patch, instructions, changelog and
unchanged RC6 game documentation. No ROM or save is included. Nothing is published.
The clean USA source CRC32 is `C180A0E9`; the final packaged patch was reapplied
and its output SHA-256 matched the candidate. The ZIP CRCs and embedded patch
hash were checked too.

## Prior candidate validation

All RC7 results below refer to the exact Lugia-only artifact above, before targeting inclusion.

`work/build/rc7/strict.log`: `check.py --full --strict-release` **passed** all
11 stages: registry, generated docs, lint, synthetic assembly, prerequisites,
real-ROM assembly, listings, USA references, tests, build and reproducibility.
Tests: 943 tool tests (26 skips), 46 docs tests, 36 site tests. Skips are recorded
in the normal suite; they are not counted as runtime coverage. Both builds and
their patches/reports were identical under different paths, locale, timezone and
hash seed. The native text-speed payload reproduced from source.

`work/build/rc7/artifact/`: independent artifact check **passed**, including fresh
workspace export, text/NARC round trips, glyphs, graphics, code, evolution data
and native text-speed verification. Text speed's runtime implementation is
byte-identical to RC6; its entire historical runtime/fault matrix was not rerun.

Fresh-boot melonDS 1.1 scene comparisons, all with the same unchanged battery save:

| Run under `work/build/rc7/` | Result |
|---|---|
| `scene-chinese/report.json` | Original Chinese reproduces `prefetch abort (00001004)`, story variable 7 |
| `scene-rc6/report.json` | Released RC6 reproduces the same abort, story variable 7 |
| `scene-fixed/report.json` | Exact RC7 reaches story variable 8 in map 244, no CPU exceptions |
| `states/report.json` | Valid states 0/1 equal original; 2, 3, `0x7FFFFFFF`, `0x80000000`, `0xFFFFFFFF` never read the callback table and preserve frame/cache; state 1 resumes afterward |

The three scene tests bypass the two trainer battles and Lugia battle in temporary
script RAM. They exercise the event and renderer from actual ROM code, but do not
prove normal battle cleanup. The state matrix is an explicitly isolated routine
test using the reviewed appearance checkpoint and synchronizing only its dispatcher
from each input ROM. It is not a fresh boot of the entire RC7 executable state.
Earlier natural-control reproduction, battle and loss-cleanup evidence is preserved
in [the prototype investigation](lugia_freeze_fix_20261009.md).

Hardware, Delta, every other user of this shared renderer, and every encounter
outcome have not been exhaustively tested. The fix does not invent a walking
animation for unsupported states. Existing engine exits and non-animation updates
are unchanged.

## Prior candidate reproduction

Run from the repository root using the existing local dependencies, ROMs and private
save. No downloads are required. Use a new output directory for each runtime run.
The runtime commands below use the preserved Lugia-only ROM. The full-check command uses current
sources and would validate/build those sources, rather than reproduce the prior candidate's hashes.
It has not been rerun for this planned RC7 inclusion.

```sh
ARMIPS=/path/to/armips .venv/bin/python work/tools/check.py --full --strict-release --work-dir work/build/rc7-recheck
.venv/bin/python work/tools/emu_lugia.py --rom work/build/rc7/candidate/origin_hg_v4.0.3_en_wip.nds --sav /path/to/reviewed-save.sav --out work/build/rc7-recheck-scene --expect fixed
.venv/bin/python work/research/lugia/check_states.py --rom work/build/rc7/candidate/origin_hg_v4.0.3_en_wip.nds --control work/rom/origin_v4.0.3_cn.nds --state work/build/lugia-fix-20261009/candidate/appearance.ml1 --sav /path/to/reviewed-save.sav --out work/build/rc7-recheck-states
```

The first `check.py --full --update-expected` run caught a coverage test that assumed
all uncovered fixes were graphics. It now tests the graphics subset, while the
existing full coverage accounting still requires every fix to be covered or have
an explicit gap. The subsequent strict suite passed; the earlier failure remains
in `work/build/rc7/check-update.log`.

An additional exploratory battle run (`battle-fixed`, `battle-fixed-v2`,
`battle-fixed-v3`) reached the actual Lugia command menu from a fresh RC7 boot,
bypassing only the two preceding trainer fights. It was **not counted as a passed
gate**: its proposed flee/field-cleanup oracle was invalid. Script 104 at offset
1270 is trainer battle opcode `0x00D5`, trainer **998**, not the later catchable
Lugia encounter; normal escape is unavailable. Early automation also confused
button focus with activation. The experimental runner is retained only under
`work/build/rc7/exploratory_battle_runner.py`, not shipped as a supported test mode.
The validated scene-only runner and state/recovery tests remain the release gates.
A follow-up checkpoint input probe (`battle-probe/`) showed normal move-menu and
battle-message progression without CPU exceptions, but is supplemental evidence,
not a fresh complete battle-outcome test. No game behavior was changed to satisfy
this exploratory test. Normal loss cleanup was verified in the earlier prototype
investigation; a fresh complete victory/loss path on RC7 remains outside this pass.

After the final tooling edits, 109 targeted assembly/coverage/scene-oracle tests
passed (`final-targeted-tests.log`); the scene-oracle tests and lint were repeated
once more after removing the unsupported exploratory mode. `git diff --check`
was clean. The existing unrelated website/docs edits in this checkout were left
in place; the release ZIP uses the already released RC6 documentation.
