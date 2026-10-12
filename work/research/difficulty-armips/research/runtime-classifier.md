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
Control0 still accepts only the existing seven exact flag values (eight since
0x801 was added, see the loss-allowed section below). Control8 with
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

## Loss-allowed story trainer battles (0x801), 2026-10-12

Player report on rc7 (Cap ON, Share OFF): Blue in Pewter City still gave EXP
above the cap and gave EXP to benched Pokémon. The script is
`TrainerBattle 535,0,1,0` (file748 @2481). A nonzero third operand marks a
battle the player may lose: the script reads `CheckBattleWon` and continues
the scene on a loss instead of `WhiteOut`.

Static evidence (pinned in `runtime-classifier-pins.json`, identical in the
untouched CN ROM and candidate81ec4501):

1. Command213 handler `02048B64`: `02048BAE` reads the third operand byte,
   `02048BDA` stores it as constructor stack arg0; the fourth operand is arg1.
2. Constructor `02050768`: second opponent nonzero and different gives 13h or
   4Bh; equal opponents give3; otherwise flags1, and `02050798..A2` ORs
   `1<<11` when arg0 is nonzero. Flags are not changed again before
   `02050C34`, and nothing here writes setup+18C.
3. `MultiBattle` handler `02048BF8` stores constant0 as arg0 (`02048C4E..50`);
   its last byte is arg1, which only clears setup byte1CDh/1CEh
   (`020507D6..F4`). Command223 (`02048EC8`) also passes arg0=0. No other
   caller reaches this constructor.

So 0x801 is the only value the loss-allowed path can produce. All60 CN/EN
uses are `TrainerBattle x,0,1,0` (49 trainers, single battles). The four
`MultiBattle 7xx,733,734,1` commands in file111 white out on a loss and
construct ordinary 4Bh.

Native evidence (DeSmuME, fixed RTC, injected script, Lv12 lead at exact Lv12
EXP plus benched Lv5 Pidgey, badges cleared so cap12):

Old = published rc7 candidate 81ec4501; new = this fix, candidate 1e4bc802
(`1e4bc8028dfd9503e6ed13387988b14fca3ce2b3ba5fcd351fd36ba5ba4b2fca`).

| ROM | Battle | Options | Setup | Snapshot | Lead awards (native→final) | Bench |
|---|---|---|---|---|---|---|
| old | 535,0,1,0 | Share OFF, Cap ON | 801h/0 | none | 104/118/152/102 unchanged | 95/99/103/65 (Lv5→9) |
| new | 535,0,1,0 | Share OFF, Cap ON | 801h/0 | allowed | 104/118/152/102 → 0 | 0 |
| old, new | 535,0,1,0 | Share ON, Cap OFF | 801h/0 | none / allowed | unchanged | 95/99/103/65 (Lv5→9) |
| old, new | Route22 Blue 8,0,0,0 | Share OFF, Cap ON | 1h/0 | allowed | 16/24/55 → 0 | 0 |
| old, new | WildBattle 19 Lv10 | Share OFF, Cap ON | 0h/8 | allowed | 87 → 0 | 0 |
| old, new | MultiBattle 736,733,734,1 | Share OFF, Cap ON | 4Bh/0 | allowed | entry only | |
| old, new | 535,0,1,0, lost on purpose | Share OFF, Cap ON | 801h/0 | none / allowed | no awards | |

The lost battle (single Lv3 Magikarp with Splash) returns `CheckBattleWon` 0,
leaves the player on the same map and tile with the party healed, with no
blackout, identically on both ROMs.

Shipping change: `dg_runtime_ordinary` accepts exactly flags0x801 at control0.
It is not a mask: 0x800 alone, 0x803, 0x813, 0x84B, 0x881, 0x901, 0xC01,
0x1801 and every other value carrying 0x800 stay excluded, as do 0x801 with
control 1, 8 or 10h. Because ITEMS policy uses the same snapshot (plus its own
trainer-bit and 80h/400h vetoes), the Berries/flutes Bag restriction now also
applies in these battles, consistent with every other trainer battle. Host
driver and two new mutation tests pin both the acceptance and the exactness.
