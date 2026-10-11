# Scripted wild entry control correction

2026-10-10. Sole-agent shipping classifier correction; no emulator, download,
subagent or battle input-sequence change. D-2312 monotonic cap implementation,
Options and item policy are unchanged.

## What the native trace actually establishes

`work/build/difficulty-v2/tests/native-tests/battle/result.json`, battle0, was
recorded against candidate
`cf22e4173fd116f614ebfac5e5d2549a6bc7ac7f7faeb396b2af9486621b28e4`.
This is **scripted WildBattle129/15/form0**, not a random encounter.
Constructor02050C34 returns at frame6408, LR02050433, flags0/control0, setup36349892.
At capture frame6528, the same setup has flags0/control8 and matching bound and
published save36118324, root36441916, copied Options512. Generation advances to1,
but the old zero-only classifier rejects it and leaves the snapshot invalid.
The trace contains no completed reward calculation; it does not establish that
every ordinary wild battle bypasses policy, nor explain the unsuccessful four
attack/switch fixture. Those are distinct native-test questions.

## Why this bit is a scripted wild marker here

Fresh disassembly is bound to completed EN input a5a418b2…51f40 in
`runtime-classifier-pins.json`; full numeric disassembly and reviewed spans are
under ignored `work/build/difficulty-v2/integration-impl/runtime-classifier-*`.

1. Script handler020434E8 resolves species and level. At0204352A..2C it stores
   **constant1** into outgoing stack argument5. At0204352E/34 it reads the third
   script operand as a byte and stores it separately as argument6 (form).
   At0204353A it calls02050418. Thus the fixture's operand0 is not a mode selector
   that disables bit8; normal uses of this command receive the implicit1.
2. Caller02050418 calls02050C34 with flags0 at0205042E. The trace's LR02050433
   identifies this exact return, not an inferred constructor family. After
   native setup/save population and enemy creation,02050448 tests argument5
   at its current SP+20h. If nonzero,0205044E..58 computes offset18Ch and ORs8.
   It then launches the battle through0204FCE4 at0205047E. The mutation is
   **before overlay entry**, not inside displaced original_begin.
3. Native leaf02215D14..84 has no calls and stores only root+0/+4/+C. It reads
   setup flags and team identifiers but never writes setup+18C. Moving capture
   before that leaf would therefore not recover control0 and would unnecessarily
   violate the original-first contract.
4. This script command is used for ordinary catchable story encounters. The
   existing source/scene audit `work/notes/issue06_magcargo_investigation_20261009.md`
   documents WildBattle219, native win/loss/capture/flee outcomes and explicit
   script loss handling. The sibling handler02043494 calls the same constructor
   with argument5=0; the distinction is the script entry variant, not species129.
   The separate constructor0205064E..54 writes control1; replay reconstruction
   at0203054C..5C ORs10h; tutorial flags400h are separately classified. There is
   no basis to relabel this ordinary catchable-script caller as replay/tutorial
   merely because the field is called a special/control word.

This proves the caller-level meaning and timing needed for the bounded pair.
It is **not** an exhaustive account of downstream bit8 effects, all script
variants, or a claim that this fixture completed ordinary rewards. In particular,
the low-HP/switch observations are not attributed to bit8 without evidence.

## Shipping change and unchanged safeguards

`dg_runtime_ordinary` now additionally accepts exactly flags0/control8.
Control0 still accepts only the existing seven exact flag values. Control8 with
trainer/double/unknown flags is still excluded pending evidence; bit8 is not
masked away. Replay0/10h and0/18h, special control1 (including9), tutorial400h,
link4 and facility80h remain excluded. Save/root/setup/copy validation and
generation invalidation are untouched; classification/settings/cap remain frozen
after entry. Original begin still runs first exactly once.

The battle oracle now requires the **specific** scripted constructor LR02050433,
control0 at constructor return, and control8 at capture. This changes no input
sequence and does not waive the snapshot, reward, party, teardown or outcome
assertions. Parent owns the corrected fixture and subsequent native execution.

## Validation and handoff boundary

Durable host driver covers 262144 flag/control combinations plus all65536 low
control words against seven allowed flags (458752 cases), high control bits,
64 settings/context lifecycles including scripted0→8 before begin, frozen live
control, ownership failure and reuse. It retains all D-2312 cap-state/monotonic
tests. Mutation tests reject restored zero-only rejection, overly broad control8
acceptance and replay acceptance. A source-ROM test checks the seven reviewed
native spans against untouched CN as well as the pinned completed EN evidence.

Fresh host/static results and final candidate/source pins are recorded in the
ignored `runtime-classifier-checks.json` and final build `receipt.json`.
No new native acceptance is claimed. Parent must compare ordinary random wild
entry, retry this scripted fixture through actual rewards/free, and exercise
replay/special/link/facility exclusions on the rebuilt candidate. Historical
boot/UI/save evidence is not fresh gameplay evidence for changed runtime bytes.
