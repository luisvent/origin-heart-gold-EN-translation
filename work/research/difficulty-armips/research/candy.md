# Rare Candy cap: bounded native handoff

2026-10-09, research only. **Feasible candidate: two ARM9 call-site wrappers,
with an immutable, valid field-cap provider during the party-menu transaction.**
No new save format, generic EXP setter interception or broad item-effect rewrite.
The user requested Candy/DayCare coverage, then explicitly allowed either to be
skipped if complexity/risk outweighs its value. Coordinator selected **Day Care
unchanged**; this is an intentional cap exception, not unfinished implementation.
Candy remains conditional on the bounded integration/test contract below. If
field ownership or preconsumption/effect consistency cannot be established,
defer Candy under that authorization rather than add a refund/rollback engine.

Authority is untouched CN ROM SHA-256
`4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8`.
Native addresses below were freshly read from decompressed ARM9, base02000000.
`work/build/difficulty-v2/growth/candy-*.txt`, `candy-callers.json`,
`candy-guards.json`, and `progression-readers.txt` hold ignored evidence.
No historical commands executed, emulator run, ROM built or implementation edited.

## Selected hooks and exact ABI

Patch **only these call sites**, preserving original callee bodies:

| Site / ARM9 offset | Original bytes | Original Thumb callee | Candidate wrapper |
|---|---|---|---|
| `0207A8E6` / `0x7A8E6` | `15 f0 a7 f8` | `0208FA39` | party UI eligibility |
| `020804EC` / `0x804EC` | `0f f0 9e fd` | `0209002D` | Candy UI effect |

```c
uint32_t dg_candy_party_eligible(void *party, uint32_t item,
    uint32_t slot, uint32_t move_slot, uint32_t heap);
uint32_t dg_candy_party_effect(void *party, uint32_t item,
    uint32_t slot, uint32_t move_slot, uint32_t location, uint32_t heap);
```

r0–r3 carry the first four arguments. At wrapper entry, eligibility heap is at
original `[sp]`; effect location and heap are at original `[sp]` and `[sp+4]`.
Location's native consumer loads its low16 bits. Forward arguments without
reinterpretation. Standard ARM/Thumb ABI, r4–r11 preserved, stack alignment and
all stacked arguments maintained across calls; preserve original return for
allowed/pass-through paths. Indirect C native pointers must set Thumb bit0.
No raw prologue replacement or instruction trampoline is required.

Rare Candy's actual item ID is **50 / 0x32**, cross-checked against the local
CN-derived item-name bank `a027/0219#50` (not a glossary taxonomy ID). Native
item attribute0x19 marks the level-increase effect: classifier `0207F5A8`
returns category2 at `0207F63C–650`, and dispatcher `0207FCDC` category2 stores
callback `02080469` via literal at0207FD58. Thus the selected effect call is in
the dedicated Candy callback, not a guessed neighboring medicine callback.
The implementation must guard item==50 even at this specialized site.

## Guard behavior and field cap

Integration supplies a read-only **field** policy view for the current live save
owner and the actual player party. Do not reuse a battle snapshot, a cached
battle root, or a hardcoded cap. View needs: current owner/generation, party
identity, decoded CAP_ON, gym cap1..100, and validity/context. Settings and gym
progression cannot change while this field party menu is applying the item;
provider must remain valid with the same flags/cap from the eligibility call
through its delayed effect callback. Re-resolve for the next menu session after
story progress, a different save or reset. No stale borrowed field pointer.
The minimal implementation may read a stable current-save view each time rather
than allocate a new persisted transaction: this relies on the proven menu owner
lifetime, not merely on equal pointers. Provider lifecycle is settings/UI work.

For item50 on the owned field party with CAP_ON:

1. Validate slot against native party count `02073399(party)`, resolve the same
   party Pokémon with `0207339D(party,slot)`, and require it belongs to that party.
   These are native pointer-returning helpers, not a BattleMon cache.
2. Read native Pokémon level using `0206D849(mon,0xA1,0)`; for valid game data,
   reject when level>=cap. Also read EXP field8 and species field5, and reject
   EXP>=`0206F09D(species,cap)` so an inconsistent higher-EXP record cannot grow
   through the cap. Native getter may decrypt/re-encrypt internally; require
   byte-identical stable records after the check in tests.
3. Return0 **without invoking native eligibility/effect** when denied. In
   particular, HP==0 must not exempt the guard. Do not set EXP, HP, friendship,
   status, moves, level or any cache to enforce a refusal.
4. Below cap, invoke the original routine with every argument intact. Candy
   increases one level to the next native threshold; cap-1→cap is allowed.
   Keep native HP restoration, moves, friendship, evolution and item semantics.
5. Non-Candy, capOFF and explicitly out-of-scope contexts call the original.
   Do not apply this field rule to facility/debug/other parties. Invalid owned
   CAP_ON/cap state must be refused at eligibility before consumption; the
   provider must not first become unavailable after the item has been removed.

No clamp on an already-applied Candy and no downlevel or saved excess. Unlike
battle EXP, the Candy operation is allowed or denied as a whole. The battle
`dg_clamp_exp` core is not a replacement for Candy's native effect operation.
For consistent native records, level+1<=cap guarantees the next native threshold
cannot exceed the cap threshold. Native `0206F060`/`0206F068` computes that
next-threshold remainder using native species growth and derived level.

## No-consume/no-mutation proof boundary and failure handling

Eligibility call0207A8E6 is followed by `cmp r0,1` and branch to0207A950 on any
other result. That branch uses the existing no-effect message flow. Quantity1
is removed via `02076AA4` at0207A8FA **only on success**. Item dispatch follows
at0207A94A→0207FCDC, before the later Candy callback02080468 and effect call.
Returning0 at the selected eligibility site therefore prevents consumption and
the Candy callback entirely. It uses existing UI behavior without new text.

Effect party wrapper0209002C resolves the mon, forwards four registers plus
heap on stack to `0208FA50` at02090044. The selected hook rejects **before that
wrapper**, hence before all native effect writes. Native effect writes can
occur before its Candy-specific level check: status processing is earlier,
and HP processing calls020901C4 before0208FB9E. Candy then calls0206F060,
adds EXP through0206E8F4, recalculates stats0206D558 and can restore fainted HP
at0208FBEE. Lowering only comparison0208FBB8 is consequently not a full no-op
for disallowed targets. Early effect refusal avoids all of those writes.

**Important limitation:** Candy UI immediately continues after020804EC; it
**does not check the effect return** before reading updated level and pursuing
its UI flow. A denial first discovered there cannot restore an already-consumed
item and may show inappropriate success UI. Thus the effect guard is defense
in depth; normal capped use MUST be denied by the preceding eligibility guard.
Do not claim the late guard alone gives transactional failure handling. A test
forcing stale/mismatched policy between the calls must expose a provider bug;
do not ship that state or hide it with success return/refunding guesses. If a
stable provider cannot be integrated simply, omit Candy entirely and report the
exception. This bounded research does not prescribe a new consumption protocol.

For valid stable field policy: already-at-cap, above-cap and fainted targets
return0 before removal and before any effect; healthy/fainted cap-1 targets run
native Candy and reach cap. At level100, preserve capOFF's native denial and
capON's early denial. No actual runtime no-consume/no-mutation pass is claimed
until the integrated UI test below; the control-flow proof identifies the path.

## All observed consumers and why these two sites are narrow

Fresh direct Thumb-BL scan covers decompressed ARM9/autoload sections and all
120 ARM9 overlays. It is an instruction-pattern inventory, not an exhaustive
indirect/ARM-call proof. Selected sites were manually disassembled in context.

- Eligibility party wrapper0208FA38 has one observed direct caller0207A8E6;
  it resolves the mon and calls lower eligibility0208F51C at0208FA4A.
- Party effect wrapper0209002C direct callers:0207FDB6,0207FED4,0207FFF6,
  **020804EC**,020811A4. Only the dedicated Candy site is patched. Others stay
  byte-identical, even though all eventually share the same native effect core.
- Lower effect0208FA50 callers:02090044 (party wrapper),020802AE (another
  party-menu operation), and ov80:0223D4C6. Neither the common lower effect
  nor the ov80 caller is patched.
- Pointer value0209002D also occurs at ov92:021F62F8. Treat it as an additional
  potential indirect consumer; its surrounding data does not establish a direct
  call. This is another reason to avoid global effect-entry rewriting.
- No literal Thumb pointers to0208F51D,0208FA39 or0208FA51 were found by that
  scan; absence is not a guarantee against computed/ARM calls.

Only item50 on the validated player field party changes at the broad eligibility
site. Only the Candy callback changes at the effect site. Other medicines,
facilities, battle items, Day Care and scripted growth remain unmodified.

## Native badge/flag readers, newly resolved

These are actual CN functions found through script-command table020F793C.
They fill the callback-address gap in `progression.md`; that separate file was
not edited by this scoped task. Save/FieldSystem pointer validity remains the
integration owner's responsibility. Do not infer an active save from these
accessors themselves.

| Purpose | Thumb C address and ABI | Verified entry bytes / chain |
|---|---|---|
| Profile from current save | `void *profile(void *save)` at `0202933D` | `08 b5 01 21 fe f7 fe f9 00 1d 08 bd`; SaveArray_Get(save,1)+4 |
| Badge reader | `u32 badge(void *profile,u32 id)` at `02029429` | `10 29 01 db 00 20 70 47`; use IDs0..15 only |
| VarsFlags from current save | `void *vars_flags(void *save)` at `0204F859` | `01 4b 04 21 18 47 c0 46 41 77 02 02`; tail SaveArray_Get(save,4) |
| Flag reader | `u32 flag(void *vars_flags,u32 id)` at `0204F865` | `38 b5 0c 1c 00 f0 3c f8`; native resolver0204F8E4 then bit test |
| Field convenience flag read | `u32 field_flag(void *field,u32 id)` at `0203FB39` | `10 b5 c0 68 0c 1c 0f f0 8b fe 21 1c 0f f0 8e fe 10 bd`; reads save at field+0xC |

Command294 CheckBadge→0204DB20, native calls0202933C at0204DB58 then02029428
at0204DB5E. Command295 GiveBadge calls setter02029458 (do not use the setter
for cap resolution). Profile badge bytes are+0x1C for IDs0..7 and+0x1F for8..15.
Command32 CheckFlag→020404D8 calls0203FB38 at020404EA. VarsFlags flag resolver
uses base+0x2E0+(id>>3) for nonzero IDs below0x4000, with a native range assertion;
flags0x04C4/1220 and0x00D1/209 are inside this persistent range. Use the native
reader instead of hardcoding raw offsets. ID0 returns false; high temporary
flags have another base, irrelevant to these completion predicates.

Implementation can now bind the existing pure gym resolver to one validated
save: badge(profile(save),id), flag(vars_flags(save),id). Read badges and the two
completion flags in one stable field scene/menu or battle-entry snapshot. No
battle or Candy should observe Erika's scripted clear-flag/badge-award transient.
Validate against actual UI/save fixtures, including both delayed badge rows,
before declaring progression acceptance. No new progression table policy here.

## Required bounded acceptance, or defer Candy

- Native party UI capOFF versus capON, levels cap-1/cap/cap+1/100, healthy and
  fainted, using copied fixture saves. At/above cap: bag count unchanged, all236
  Pokémon bytes unchanged, original refusal path taken, no effect callback.
- Below cap: one Candy consumed, one native level gained, native EXP threshold,
  HP and checksum valid; include cap-level move learning/evolution and cancelling
  those optional prompts. Repeat use: first reaches cap, second refuses.
- Direct guarded effect call for capped healthy/fainted Pokémon returns0 and
  retains all bytes. This proves effect guard isolation, not UI consumption.
- Non-Candy medicines, stones and capOFF behavior unchanged; no ov80/ov92 code
  changes. Verify field party identity and slot validation before native access.
- Confirm field policy remains identical from eligibility through delayed effect;
  close/reopen, switch save, reset and progress milestones refresh it. If this
  requires broad new ownership machinery, defer under the user's risk allowance.
- Host ABI/mocks cover fifth/sixth stacked arguments and native fallbacks; native
  tests exercise the actual compiled wrappers and original callees, not only
  host-return interception. Keep current TEXT SPEED and other dirty work intact.

Local old growth states contain no freshly validated Candy bag/menu fixture.
Create a controlled copy for the sequential test step; historical synthetic
Candy results are not acceptance for these newly selected UI call-site hooks.
