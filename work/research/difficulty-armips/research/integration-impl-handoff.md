# Difficulty v2 native integration candidate

2026-10-10. Sequential sole-agent implementation, no subagents or downloads.
Built and installed an opt-in candidate; **native gameplay/UI/save acceptance is
still pending the next test agent**. No original ROM/save, production tool,
TEXT SPEED source, historical foundation, or unrelated dirty file was modified.

## Repeatable repository-root command

```sh
.venv/bin/python work/research/difficulty-armips/build.py --enable-difficulty --input work/build/double-target-armips/final/origin_hg_v4.0.3_en_wip.nds
```

Output is `work/build/difficulty-v2/integration-impl/candidate.nds`, with
`receipt.json` and a fresh `run-*` directory of source-bound ELF/map/stack usage,
assembly symbols, staged sections, resident image and logs. Everything generated
is ignored and local; do not distribute or commit the ROM. Each run is isolated;
only a successfully reopened/verified ROM enters recoverable two-file publication.
Ordinary publication failures restore the previous candidate/receipt pair; a
failed rollback is explicitly reported as RECOVERY REQUIRED, with its journal
retained. A process crash may leave a mixed public pair until recovery on the next
invocation. See [publication protocol and limits](publication.md). Failed builds
write a FAILED marker in their own run.
`install.py` is the build command's guarded library, not a production registry
entry. No default build installs this feature.

Actual input SHA256:
`a5a418b277bf07390e7282413923ec34f1c364f4a96c88936d65a73a80d51f40`.
The freshly inspected top-level `work/build/origin_hg_v4.0.3_en_wip.nds` has hash
`6fa7b4e739391ca9ea9bfcf90d83eec6407c3c04102e52432bb41bc8ae44a7d3` and lacks TEXT
SPEED: ITCM1568/overlay50 vanilla, versus required ITCM4032/overlay505916.
It is rejected. The selected completed fixture preserves its targeting and
other existing code; there is no silent merge/substitution of current WIP code.
Its overlay14 hash is `f1eb02be522dae0a44418aba17926d1e6652eac0eb584401457f5ec435dab9e8`,
which differs from the items agent's top-level WIP. All six item signatures and
all three frame/control-flow dependency ranges match on the selected fixture.
The installer pins full input ROM, whole ARM9/ITCM/overlay9/14/50, and dependencies;
it does not weaken guards to accept nearby matching instructions.

## Added and changed source files

Added under `work/research/difficulty-armips/`:

- `native/runtime.h`, `native/runtime.c`: real snapshot provider and lifecycle.
- `native/caps.h`, `native/caps.c`: native badge/flag binding and pure resolver.
- `native/link.ld`: resident Thumb C placement and bounded BSS.
- `native/runtime.asm`, `native/runtime_hooks.json`: five growth/lifecycle BLs,
  four ARM/Thumb stack-aligning adapters, and guarded arena-high literal.
- `native/integration_contract.json`: entry-control/owner contracts and explicit
  Options help-edit source override/provenance.
- `build.py`, `install.py`: real compiler/linker/armips build, opt-in guards,
  actual autoload installer, logical verification and recoverable publication.
- This handoff.

Necessary existing integration changes:

- `native/options.c`: ONLY CAP help's second line becomes
  `Candy and Day Care unchanged.`
- `research/options-handoff.md`: describes that help edit and changed-source
  validation boundary.
- `research/options-source-pins.json`: current Options/help hashes, preserved
  previous Options hash and explicitly historical old check/artifact records;
  fresh sanitizer host-check artifact pins. Old tests are not represented as
  acceptance for the edited file.
- `research/progression.md`: replaces only the obsolete unresolved-native-reader
  paragraph with the now-implemented bindings and remaining runtime caveat.

`foundation.asm`, `hooks.asm`, `fix.toml`, `check.py`, historical `README.md`,
policy/growth/items sources and ASM, settings sources, Options hooks and ASM,
compatibility sources, and all production TEXT SPEED/tools remain unchanged.
Subsequent D-2312 update: the user confirmed gym-only caps that never decrease.
The schedule JSON records this accepted policy separately from untouched actual
gym maxima. The resolver now uses their running maximum through the earliest
unfinished row. CAP help reflects this policy; the earlier cursor fix is retained.
The original unchanged-source statements above describe the initial integration
pass, not these subsequent authorized changes.

## Runtime contract

At overlay14 `02214CA2`, an assembled BL enters resident `DG_Begin`, which invokes
actual linked Thumb `dg_battle_begin`. That calls original `02215D15` FIRST,
invalidates the old snapshot, advances a nonzero generation even for reused
addresses, validates root0x274/setup0x1D4, and captures flags/cap BEFORE returning
to `02214CA6` and engine/items/reward initialization. No lazy first-KO provider.
At `02214DA6`, `DG_Free` invalidates first, then calls `0201B33D` exactly once
with unchanged r0 and preserves its return value. Cold/reset loader zeros cover
all runtime and menu state. There is no diagnostic bootstrap, host getter
routing, persistent pointer, or always-NULL shipping provider.

The current save comes from native `02001195`, whose publication occurs after
construction/load. Require it to equal setup+`1C0`. Fresh constructor disassembly
`02051074..02051256` takes SaveData in r2, obtains Options at `020510AA`, copies
it into setup+`130` at `02051188..190`, and binds the same save at `02051250..252`.
Require valid aligned Options halfwords and agreement of only difficulty bits
between current Options and the setup copy. Snapshot uses the copy, with cap
resolved from that same current save. No borrowed Options pointer survives.

`caps.c` binds profile `0202933D(save)`, badge `02029429(profile,id)`, VarsFlags
`0204F859(save)`, flag `0204F865(vars,id)`. It queries native badge IDs0..15 and
flags1220/209, then selects first unfinished guide-order gym. Caps:
`12,20,25,38,55,65,80,100`, then100 throughout Johto and after all gyms (D-2312). Badge order:
`0,1,2,3,5,6,4,7,8,9,10,11,13,12,14,15`. Erika badge3 OR1220; Clair badge15
OR209. Return the running maximum of actual gym maxima through that row.
Later completed rows never bypass a gap or raise its cap; filling the gap skips
already completed later rows. Adding completion predicates cannot lower the cap.
No badge-count approximation, persistent high-water mark, downlevel or writes.
Clair completion remains flag/badge-based even though both sides now cap at100.

Ordinary flags at control0 use EXACT values `0,1,3,13h,4Ah,4Bh,100h,801h`.
801h (loss-allowed story `TrainerBattle`, third operand nonzero) was added
2026-10-12; see runtime-classifier.md.
The subsequent native review establishes one additional exact pair: **flags0,
control8**, the scripted WildBattle path. Handler `0204352A..3A` passes implicit
argument5=1, separately from form argument6; caller `02050448..58` ORs8 before
battle overlay entry. Trace constructor LR02050433 identifies that caller.
Original begin remains first and does not write setup control; capture stays
before engine initialization. See [runtime-classifier.md](runtime-classifier.md)
for exact evidence, source pins, scope and fresh checks. The earlier zero-only
claim was incorrect for this scripted-wild path, not proven wrong for random
encounters. No masking or global acceptance of control8 was added.

Replay loader `0203054C..5C` ORs10h: both control10h and scripted replay18h are
excluded. Special control1, tutorial400h, link4 and facility80h remain excluded.
Classification is frozen at entry: later control-word changes cannot invalidate
an otherwise owned snapshot. Owner/flags/save validation is unchanged. No
exhaustive proof of control-word lifetime immutability is claimed; random wild,
trainer/double positives and real replay/special negatives remain native tests.

Provider reads never recapture cap/settings mid-battle. It invalidates on lost
published save, root/setup identity, bound save identity, or changed setup flags;
restoring a stale address cannot revive the generation. Native battle entry/free
supply real lifetime boundaries; pointer equality alone is insufficient. There
is no independent native save-generation getter: reset/load and root-reuse
fixtures remain acceptance work. Native saves can only be loaded outside an
active ordinary battle; a subsequent entry refreshes even if addresses repeat.

All three growth BLs are installed. Existing shipping growth calls native
eligibility first, then clamps final per-recipient award before message/apply,
with local IDs1..6 and resolver identity; EV's eligibility seam is untouched.
No redistribution or overflow banking. All six item hooks run actual resident
C through the existing ARM/Thumb adapters, preserving native command/backstop
register contracts. Item scope still requires player owner0/trainer Bag;
wild/held/NPC/special paths retain native behavior. The exact20 medicine additions
and original berry/flute masks remain in shipping items/policy C; archive unchanged.

## Deliberate field-growth exceptions

Candy is **deferred under D-2304**, not implemented with a stub. Its early
eligibility seam is feasible, but no proven field-party/current-save/menu
lifetime spans the delayed effect callback. Native consumption at `0207A8FA`
precedes delayed effect `020804EC`; the UI does not check the effect return.
The early eligibility decision would need to bind the same party slot/mon,
current save, settings and cap through that callback, including menu teardown
or owner replacement. The battle snapshot cannot supply field ownership.
A newly unavailable or changed policy at that callback can therefore consume
an item before refusing it and even run success UI. An early-only check without
that lifetime proof cannot certify the no-mutation-at-cap requirement either.
The bounded integration cannot certify that contract, so neither Candy callsite
is patched; all native healthy/fainted/no-effect/consumption behavior remains.
There is no rollback, refund, or new save format. Day Care is explicitly skipped
under D-2304 because no-banking would require separate persisted accounting
coupled to breeding. Menu and instructions state both exceptions.

Hold **L while opening field Options** for DIFFICULTY; regular Options still
has seven rows including TEXT SPEED. Defaults: Berries/flutes, Share ON, Cap OFF
(logical0, stored mask8028). Apply changes RAM; save normally to persist. Native
save checksums/mirrors own persistence; no migration tag distinguishes arbitrary
old reserved bits or guarantees downgrade equivalence.

## Layout, patch guards and receipts

Measured current resident image: **6324 bytes** in `[023DC000,023E0000)`.
No 24KiB expansion is needed. C text5096 + rodata615 + one alignment zero +
BSS108 =5820; item stubs272, Options72, runtime160 follow. BSS is materialized
as initialized zero bytes BEFORE stubs, not claimed as trailing BSS. The new
ndspy Section has bssSize0. `.su` files record frames; maximum single frame is
Options text136, input→finish→draw→text312 excluding native callees. Runtime
begin48 plus cap32/resolver16/native calls; getter24. Tight native heap/stack
scenarios remain untested.

Original main ends021106A0; original BSS ends021E4980. Max overlay+BSS end equals
original ArenaLow02264920. ArenaHigh literal020D1970 changes023E0000→023DC000.
Original main/BSS endpoints, DTCM initialized96+BSS32, ITCM4032 and its arena
end01FF8FC0 stay fixed. ARM7 startup/backup `[023E0000,023F9EF0)` is excluded.

Real local clang ARM946E-S Thumb, freestanding/no-builtins/warnings-as-errors,
real Rust ld.lld `--no-undefined --fatal-warnings`, explicit linker script, and
armips assemble every instruction patch. Final ELF32 section/symbol ranges,
Thumb state, absent unresolved symbols/relocations, stub extents, all20 BL/pointer
hook destinations/reach, and actual veneer LDR/BLX C targets are checked.
No hardcoded provisional C addresses and no Python-generated instruction words.

Reopen verification allows only20 hooks +24 compatibility halfwords + arena
literal, the first12 code-settings autoload bookkeeping bytes, and one appended
resident section. Every other logical file/section and both raw overlay tables,
ARM7 and item archive are byte-identical. Repacking moves container offsets/FAT/
header checksum and ndspy's NSMBe RSA-container pointer at ROM1000; the exact
pointer delta is recorded and its target checked, all other header padding and
RSA bytes preserved. Production TEXT SPEED verifier is intentionally not called
or weakened: the companion checks precisely its declared five mask edits, with
all other ITCM bytes/symbols unchanged.

Receipt binds input/output, all research sources/protected inputs, compiler/
linker/assembler drivers and their actual Xcode/Rust binaries, Python/ndspy code,
commands, ELF sections/symbols, zero ranges, stubs, guards and exact logical byte
differences. Input/source/tool hashes are rechecked before promotion. Build
refuses WIP/guard mismatch/double install/bad bounds or missing opt-in.

## Checks actually run and remaining native proof

Passed on current shipping source:

- Combined real ARM compile/link, armips hooks/compatibility, install, reopen,
  exact logical preservation and source/tool/input rehash.
- 52 bounded negative rejections: every declared hook/edit mutation, out-of-site
  mutations of each of five whole guarded files, double autoload, bad overlay
  bounds. CLI separately rejects top-level incompatible WIP and missing opt-in;
  neither replaces the existing candidate.
- Runtime/caps host C with ASan/UBSan:262144 badge/flag combinations,262144
  flags/control cases,56 option/context lifecycles, native-original-first/free,
  frozen settings/cap/control, root reuse and owner/identity/bounds failures.
  Initial scratch-test pointer arithmetic caused UBSan reports; corrected the
  TEST helper and reran with halt_on_error. No shipping failure was masked.
- Edited Options/settings host C with ASan/UBSan:524288 codec cases, protected
  aligned halfword, no-store no-op, invalid/stale transactions, all8 flags,
  D-pad/touch/cancel/hidden rows/fallback/cleanup ABI mocks. No native UI claim.
- Fresh DeSmuME loader-only smoke, copied trainer battery, NO old `.dst`:
  full6324-byte resident RAM equals the installed image after360 frames;
  ArenaHigh literal matches; interior BSS is zero. Poison BSS, emulator reset,
  another360 frames: native loader restores the entire image/zeros. This proves
  copy/placement/reset initialization, **not** a playable field, in-game soft
  reset, native page or battle. The captured360-frame screens are blank; do not
  present them as visual startup acceptance. Sandbox emulator startup aborted;
  approved escalated rerun completed. `loader-smoke/result.json` pins candidate.
- Subsequent **baseline/candidate fresh boot progress comparison** reached title
  at frame3106, Continue at3312, and real overworld/field menu at4218 in separate
  emulator processes using copied batteries, no `.dst`. Candidate screenshots
  were visually reviewed at all three stages; baseline field was also reviewed.
  Both have the same title image and match all three native field-overlay
  signatures. Candidate resident immutable bytes still match after reaching
  field. The early white screen is transient, not the final startup result.
  Both runs recorded the identical returning native assertion at frame2412,
  PC02025B30/LR0200B1BD; neither hit monitored undefined/prefetch-abort/data-abort
  vectors. Final ARM9 PC020D2D28/LR020D0FB8/SP021E0928/CPSR1F is identical and
  is not exception mode. This establishes startup/Continue/field progress only,
  not difficulty gameplay or native soft reset. `boot-comparison.json` pins
  script, copied source battery, both result files and six milestone screenshots;
  `boot-baseline/` and `boot-candidate/` retain diagnostics. Candidate tested:
  `a3d2760214e183cbde8e6a9101863615b0ca35c6c28b1e8a1f593fe3ba214aee`.

The next sequential native test owner must boot candidate anew, preferably from
a COPIED battery save. Old `.dst` files embed old ARM9/overlays and REMOVE the
new code when loaded; they are not installed-candidate evidence. Required proof:
actual begin/free and every C wrapper execution, two battles with root reuse,
all7 ordinary positive contexts plus real replay/link/facility/special negatives,
control-word lifecycle traces, glyph/Options preview/input/Apply/Cancel/native
save/reload/mirror/soft-reset, each20 medicine/effect/no-effect/doubles slot,
share+late-cap message/EV/EXP/identity/aggregate-KO invariants, progression both
delayed badges/defeat/skipped gyms/removal of both former decreases, and tight English arena/heap/stack
transitions. GPT6 review and fixes remain parent-owned subsequent stages.
