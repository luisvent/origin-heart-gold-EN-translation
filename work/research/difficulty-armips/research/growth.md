# Native battle EXP/EV and cap contract

Bounded research handoff complete, 2026-10-09. Implementation can use the confirmed
hook ABI below. This is a battle-growth contract, not a universal level cap. This document is the growth research deliverable; production code is
owned by integration. Commands run from the main repository root. No historical
command has been executed, no ROM/save source changed, no downloads or commits.

## Implementable hook contract

Untouched CN ROM SHA-256:
`4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8`.
Overlay 14 base `0x022007E0`, decompressed size `337216` (`0x52540`), SHA-256
`6429a2e023b8b3f4bb90076a29e30a3aaa204c94f3e6d1986161102a22559312`.
All addresses below are Thumb instruction addresses; native C function pointers
must set bit 0. Byte guards are in file order, not displayed halfword order.

| Hook | Overlay offset | CN original bytes | Original callee | Replacement |
|---|---:|---|---|---|
| Sharing getter call `0x022289EA` | `0x2820A` | `ec f7 e9 fe` | `0x022157C0` | snapshot-aware sharing getter |
| First EXP pass eligibility call `0x0221F778` | `0x1EF98` | `ff f7 b8 ff` | `0x0221F6EC` | late cap eligibility wrapper |
| Deferred EXP pass eligibility call `0x0221F83E` | `0x1F05E` | `ff f7 55 ff` | `0x0221F6EC` | same late cap eligibility wrapper |

**Do not hook the EV pass's eligibility call at `0x0221F682`; do not zero
the raw reward record when a cap rejects EXP.** EV application happens first,
inside `0x0221F650`, via `0x0222AC50`. Its native eligibility requires positive
raw EXP. Changing the shared helper globally or the early raw record would
incorrectly suppress capped fighters' EVs.

Proposed public functions, using the integration-owned snapshot and shared core:

```c
uint32_t dg_growth_share_enabled(void);
uint32_t dg_growth_eligible(uint32_t *amount, uint32_t *deferred,
                            void *battle_mon, const void *raw_reward);
/* Supplied by native/policy.h, not reimplemented in the wrapper: */
uint32_t dg_clamp_exp(uint32_t current, uint32_t requested,
                     uint32_t ceiling, uint32_t enabled);
```

Both eligibility call sites use the exact four-argument ABI above (r0–r3).
Call original `0x0221F6ED` first; keep its boolean return and `*deferred`.
If the snapshot is valid, context allowed, recipient local, CAP_ON set, and
original output EXP is positive, compute:

```c
ceiling = native_species_threshold(*(uint16_t *)battle_mon,
                                    snapshot.cap_level); // 0x0206F09D
*amount = dg_clamp_exp(load32(battle_mon + 0x18), *amount,
                      ceiling, 1);
```

No direct write to the Pokémon or reward record. No retained rejected amount.
Zero accepted EXP follows the existing caller's zero-output branch and skips
EXP messages/application; the EV pass has already happened. Positive accepted
EXP follows the existing message, application and accumulation paths unchanged.
Native eligibility false/zero, cap OFF, invalid snapshot or excluded context
returns the original result/outputs unchanged. Validate cap in 1–100 before
calling the native threshold function; invalid integration state falls back to
baseline, not an arbitrary cap.

Sharing wrapper returns `!(snapshot.flags & SHARE_OFF)` only for an allowed,
validated battle snapshot; otherwise returns native baseline `1`. The original
getter is `01 20 70 47` at `0x022157C0`, followed by the level-100 constant getter
`64 20 70 47`. Preserve the participant search and native calculation exactly.
Use the shared flag definitions SHARE_OFF=1, CAP_ON=2; the growth wrappers do not
use the item flag. `dg_exp_eligible` can model the policy in host tests but must
not replace the game's native eligibility checks or participation lists.

## Snapshot, owner and integration boundary

Integration owns the settings codec, UI, dispatcher, gym-cap getter, resident
layout and lifecycle. Growth needs an immutable snapshot containing flags,
cap level, allowed ordinary battle context, battle root and a
battle generation/epoch. Snapshot before the first ordinary battle operation
(item operation or reward); reset on actual battle entry/end and reset/load.
**Pointer equality alone is not a lifetime check: battle heaps can reuse an
address.** Invalid or unavailable snapshot means faithful native behavior.

Fresh CN disassembly establishes:

- `*(uint32_t *)0x02255BAC` is the battle root used by these helpers.
- `0x022156B4` reads `setup = load32(root + 0x10)`, then
  `battle_flags = load32(setup)` (two dereferences); native reward gate
  `0x02215A78` returns false for `flags & 0x2A4`. Do not bypass this gate.
  This is a native veto, not a complete positive allowlist of ordinary modes.
- Native local owner getter `0x02215640` returns 0 in this hack.
- Owner range table at `0x0224D130` is `01 0d 07 13`: owner0 IDs1–6,
  owner1 IDs13–18, owner2 IDs7–12, owner3 IDs19–24.
- BattleMon recipient ID is byte `+0x14` (`0x022167A0`). Resolver
  `0x022151BC` returns `*(root + 0x1D0 + 4*id)` with no range validation.
- Before cap logic, require ID1–6 and resolver result identical to the
  supplied BattleMon, in addition to the integration context/snapshot guard.
  Never classify by odd/even recipient ID. Never call the resolver with an
  unchecked ID. Owner helper `0x022157D4` defaults to owner0 even for invalid
  IDs, so its result alone cannot establish ownership.

### Exact initialization and teardown seams

| Site / overlay offset | Guard bytes | Native call | Wrapper ABI |
|---|---|---|---|
| `0x02214CA2` / `0x144C2` | `01 f0 37 f8` | `0x02215D14` | `void dg_battle_begin(void)` |
| `0x02214DA6` / `0x145C6` | `06 f6 c9 fa` | `0x0201B33C` | `void dg_battle_root_free(void *root)` (r0) |

Both are four-byte Thumb BL replacements, not function-entry overwrites.
`0x02214C10` is a stateful overlay initializer. Its state0 branch allocates and
zeroes **0x274 bytes** for the root, publishes it at `0x02214C6E`, and stores
setup r6 at root+0x10 at `0x02214C70`. At CA2, call original `0x02215D15`
first, then invalidate the old snapshot, advance its generation (skip zero),
and capture settings plus the gym cap and context. This original callee derives
root+0 (single/double: bool(flags&2)), root+4 (multi layout), root+0xC (battle
category). It uses no input arguments and no return value is consumed here.
Snapshot must be ready before returning to CA6; engine setup follows at CA6,
CAА and CAE. Do not defer capture until the first KO. This path runs once for
each newly constructed battle even if its heap address equals the previous root.

At DA6, invalidate the shared snapshot **before** calling original free
`0x0201B33D` with the unchanged r0. The root slot is not nulled by native teardown;
never interpret its residual value as a live battle. Free exactly once and
preserve normal ABI/calculated return if the native free returns one. Both
wrappers preserve r4–r11 and stack alignment as required by the native ABI.
Teardown is `0x02214D14`; this seam is its root free, after battle resources and
party objects were released. Snapshot access between final teardown start and
root free must never initiate new item/award work.

Initialize snapshot invalid in resident bootstrap/BSS and invalidate it on
integration's game reset/load paths too. A coherent emulator savestate restores
its resident snapshot together with battle state; a pre-feature savestate must
not be treated as a newly initialized candidate session. Tests need two battles
with deliberate root reuse, plus exit/reset/reload, to prove the lifecycle.

Provider validates full root range0x274 and setup allocation0x1D4 before reading
fields, in aligned ARM9 RAM, and ties them to the current generation. The growth
wrapper itself only needs root0x1EC/setup4 and BattleMon0x1C for its reads; these
are bounds checks, not independent heap-ownership proof. No native function in
this contract returns a generation token: generation is resident state owned by
integration and advanced at the actual initialization seam.

### Positive ordinary-battle classifier

Implement an **exact-value switch**, not `(flags & veto)==0` or a permissive
bitmask. The following values have current CN constructor evidence:

| Setup flags | Ordinary construction evidence |
|---:|---|
| `0x000` | Wild default in ov2 `0x02248704–0C`, calls `0x02050C34` with r1=0 |
| `0x001` | One trainer in `0x02050798–A8` with optional special argument zero |
| `0x003` | Same opponent trainer IDs / doubles branch `0x02050790–96` |
| `0x013` | Two distinct opponents, no partner: `0x0205077A–8A` |
| `0x04A` | Hack wild doubles: ov2 `0x02247124–2C` and `0x0224713A–42` |
| `0x04B` | Two opponents plus NPC partner: `0x02050782–8E` |
| `0x100` | Wild constructor branch ov2 `0x02247094–9E`; also explicitly grouped with wild0/4A by native outcome handler `0x020509D2–DE` |
| `0x801` | Loss-allowed story trainer battle: script `TrainerBattle` with a nonzero third operand; one trainer in `0x02050798–A2` with that argument nonzero (added 2026-10-12, see below) |

Allow only those values in this candidate (each with control0; scripted wild
also flags0/control8, see runtime-classifier.md). For item restrictions also require
bit0 (trainer), local owner0 and the native command/target eligibility checks.
Growth keeps the native reward veto `flags & 0x2A4` as a redundant defense.
Do not reject ordinary doubles based on root+0 being1: that is the double flag,
not a link-mode marker. Only local IDs1–6 receive growth policy in partner modes.

Every other exact value bypasses difficulty: this includes link bit4, facility
bit0x80, Safari0x20, the constructor at `0x02050DD0` producing0x1000, the
constructor at `0x02050DF4` producing0x200, and the special constructor at
`0x02050E08` producing0x400. Do not infer their semantics from vanilla names;
in current CN ov2 the contest branch calls `0x02050DD0` and produces0x1000.
Unknown upper bits must not be stripped. Raw0x2/0xB are not silently added
merely because their bits seem familiar.

**0x801 (added 2026-10-12).** This audit first left0x801 excluded because the
meaning of the stack argument behind `0x02050798–A2` was not established. It is
now: script command213 `TrainerBattle` (handler `0x02048B64`) reads its third
operand as a byte at `0x02048BAE` and stores it as constructor stack arg0 at
`0x02048BDA`; the constructor `0x02050768` ORs `1<<11` into flags only on the
single-trainer path (`0x02050798–A2`: no second opponent). The two-opponent
paths (0x13/0x4B) and same-trainer doubles (3) never test it. Every other caller
passes arg0=0: `MultiBattle` (`0x02048C4E–50` stores constant0; its last byte
is stack arg1, which only clears setup byte0x1CD/0x1CE at `0x020507D6–F4`) and
command223 (`0x02048ED8–DA`). So0x801 is the only value this bit can produce.
The scripts that use it are story battles the player may lose: e.g. Pewter
City Blue (file748 @2481, `TrainerBattle 535,0,1,0`) checks `CheckBattleWon`
and continues the scene on a loss instead of `WhiteOut`. All60 CN uses are
single-trainer with third operand1 and fourth operand0. The four `MultiBattle`
commands whose last byte is1 (file111) still white out on a loss and get plain
0x4B. Native trace on candidate81ec4501: Pewter Blue arg1 gives setup flags
0x801/control0 and a full ordinary save/options binding, yet the snapshot was
not published, so Cap ON and Share OFF were silently ignored (lead 104/118/152/102
EXP above cap, benched Pidgey 95/99/103/65 with Share OFF). The classifier now
accepts exactly0x801 at control0; no other value carrying0x800, and no control
variant of it, is accepted. Native rewards in these battles are not vetoed by
`flags & 0x2A4`.

This is an implementable conservative classifier backed by native constructors.
Actual link/facility/replay entry fixtures must confirm the snapshot is disallowed;
no replay runtime has been exercised here. If a replay uses an otherwise allowed
exact value, its independent entry marker must be added to the shared provider's
veto before acceptance. Do not claim those fixtures passed based on switch tests.
Current safari-double bugfix can alter which constructor is reached; leave that
separate fix intact and compare against the current integrated baseline.

Install interface: link the two exported Thumb wrappers into the integration
payload and patch the three growth BL sites plus the two shared lifecycle BL
sites above. The latter are installed once by integration, shared with items.
No separate growth autoload, fixed global scratch address, global EXP setter
patch or overlay-tail payload is required. Integration must declare resident
code/data bounds, initialize state before any hook, check BL reachability/state,
guard original bytes, and patch the ROM overlay so reloads retain the hooks.
If a veneer is needed, integration owns its allocated bounds and guard.
Preserve the current TEXT SPEED changes. This research does not establish the
old foundation's reserved memory is a sufficient complete payload allocation.

## Why the historical application-only clamp is insufficient

At `0x0221F7B8` / `0x0221F7D2`, the first pass queues native message IDs
`0x1E` / `0x1D` with the amount from `[sp+0x1C]`. This is **before** the call
at `0x0221F7DA` to EXP application `0x0222AC30`.
That function resolves the BattleMon, calls `0x02218888`, then dispatches command
`0x1F` carrying the applied amount. Hooking only `0x0222AC3A` can make the EXP
bar/application amount correct while leaving the earlier message and caller's
accumulator wrong. Historical claims that observing command `0x1F` proved the
printed message are not sufficient evidence.

The proposed two eligibility call-site wrappers alter the stack output that
feeds both the message and subsequent application/accumulation. The deferred
pass uses `[sp+0x10]`; it reaches `0x0222AC30` at `0x0221F85A` and accumulates
that same amount at `0x0221F85E–64`. The original record's deferred flag selects
one pass, so the two wrappers do not apply EXP twice to one recipient.

The application at `0x02218888` uses BattleMon cached EXP `+0x18`, adds the
award, stores that cache at `0x022188B0`, and writes backing Pokémon field8
via `0x0206DF70` at `0x022188BA`; backing pointer is BattleMon `+0x10`.
Keep this native cache/write/level flow. Threshold uses the BattleMon species
halfword at `+0`, exactly as native growth does, not an independently remapped
alternate-form personal record.

## Distribution, caps and aggregate KOs

Native per-recipient calculation `0x022289B4` checks the defeated BattleMon's
participation list using `0x02216C38` (count byte+0x1F1, IDs starting+0x1F2).
It does not replace that list when sharing changes. At `0x02228A2E–38`, neither
participation nor sharing returns zero raw EXP. Participants take the original
full calculated amount; nonparticipants take its half at `0x02228A5C`, before
later native modifiers. The formula/rounding/modifiers stay upstream and intact.
There is no new participant count, party division, pool or redistribution step.
Two participants each keep **their own native award**, not a new equal split.
A capped fighter must not be removed from participation to enlarge anyone else's
award. **Amended (D-2403, amends D-2301; user decision 2026-10-12):** with Share OFF a
local recipient holding Exp. Share (item 216) keeps the native bench share: the
SHARE wrapper is now recipient aware (`dg_growth_share_enabled(battle_mon)`; the
DG_Share stub passes the per-recipient routine's r4 in r0, and the held item is
read with `0x0206D848(backing, 6, 0)` like Lucky Egg at `0x02228A18`). Its EXP and
EVs equal Share ON and the per-recipient cap clamp still applies; non-holders
stay at zero. The item is read only with Share OFF and a verified local ID 1..6.

`0x022288E8` calculates a temporary six-entry reward array for one defeated
opponent, then accumulates into the caller's array. EXP is u32 at each entry+0,
EV fields occupy bytes+4..9, stride0x10. At `0x02228916–1C` EXP is added;
EV bytes are added individually. Boosted marker+0xB is retained if already set;
deferred/share marker+0xC is **overwritten** from the latest temporary record.
The outer `0x0221F4F0` can process multiple pending defeated entries before
`0x0221F5E8` runs EV, immediate EXP and deferred EXP passes.

Therefore cap the per-recipient **aggregate already calculated by the engine**,
not each defeated opponent's early raw record. Preserve the native pass choice,
including its last-record marker semantics. No retained rejected growth survives
an award. For sequential KOs, the next award reads updated BattleMon EXP; for
aggregated KOs, clamp their summed request once. EVs are the native aggregated
EVs, even when EXP is rejected. A Pokémon benched for the whole group receives
zero EXP/EV with sharing OFF because its aggregate raw EXP is zero. Mixed
participation across two simultaneously defeated foes needs a baseline comparison:
native EV aggregation can include both foes once aggregate EXP is positive.
Do not silently rewrite that native behavior as a difficulty change.

Cap threshold is the **start of the cap level**, from native species growth
`0x0206F09D(species, cap)`. For current E and request R: if E>=T accept0;
otherwise accept min(R,T-E). Never subtract previously earned EXP, lower a level,
use the next level threshold, retain fractional overflow, or bank rejected EXP.
For two recipients independently use each one's species/current EXP and native R.
An illustrative test (not an observed reward): T=560, requests26/26, current550/500
accepts10/26; it must never become10/42. If the first is already560, accept0/26
and still retain both fighters' native EVs.

## Reconciliation with native/growth.c checkpoint

Read `native/growth.c` and `native/growth.h`; did not edit them. They implement
the correct four-argument native wrapper, original-first eligibility, both late
hook ABI definitions, local ID1..6 plus resolver identity, native species threshold,
and shared `dg_clamp_exp`. Their native function pointers set Thumb bit0 correctly.
`DG_GROWTH_HOST_TEST` supplies read/native-call primitives while compiling the same
policy-bearing wrapper; FFI tests should link this file with `native/policy.c`.

Accepted snapshot ABI on ARM is20 bytes: flags+0, cap_level+4, allowed+8,
root+12, epoch+16. Local owner is fixed0 by this CN build and need not be another
field. `dg_growth_snapshot()` is responsible for current-generation validity;
checking epoch!=0 in growth.c alone does not prove freshness. No implementation
change in this checkpoint supplies lifecycle or the positive classifier: those
are still integration work using the seams above. `allowed` must mean this exact
classification, not merely native reward gate success. Growth's span0x1EC/setup4
checks are adequate for its own reads; provider owns the fuller allocation checks.

Original native eligibility runs before wrapper guards, so host mocks must model
valid native caller arguments; the wrapper is not a general safe API for arbitrary
untrusted BattleMon/output pointers. Invalid recipient identity must bypass only
the optional cap, leaving original outputs intact. Share getter has no recipient
argument: it supplies the calculation setting, while native local-roster traversal
and the separate cap identity check enforce the recipient context.

## Candy, Day Care and other growth: explicit scope boundary

The three growth hooks implement **gym-based battle EXP caps**. The user later
selected Candy/DayCare coverage, then explicitly authorized skipping either when
complexity/risk outweighs its worth. Coordinator selected **Day Care unchanged**
because strict no-banking needs persistent bookkeeping coupled to breeding. This
is an intentional exception, not a claim the user initially wanted battle-only.
Rare Candy is a bounded conditional addition described in [candy.md](candy.md);
include it only after its preconsumption/effect/provider tests pass. UI/help and
acceptance reports must state the shipped scope and the Day Care exception, with
no universal cap claim.

Rare Candy is a practical follow-up. Fresh ARM9 disassembly verifies the party UI
calls eligibility `0x0208FA38` at `0x0207A8E6`; result!=1 branches to refusal
`0x0207A950`. It removes quantity1 at `0x0207A8FA` via `0x02076AA4` **before**
effect dispatch `0x0207FCDC` at `0x0207A94A`. A refusal inside only the late effect
can consume the item. Add a Candy-specific preconsumption eligibility guard and
an effect-entry guard, snapshotting the same field cap throughout the transaction.
Preserve other items, native effect flow below cap, and no-change failure above
cap including fainted Pokémon. Historical `/root/resolve_growth` line617 documents
why merely changing the two level comparisons allowed other mutations on fainted
targets. This is design evidence, not a new tested Candy implementation. The
subsequent [Candy handoff](candy.md) supplies two exact UI call-site guards and
native progression readers; field provider integration and runtime acceptance
remain separate work.

Day Care preview `0x0206B398` obtains slot accrued steps with `0x020297F0`, passes
them to preview helper `0x0206B350`, which adds them to a copied boxed Pokémon's
EXP. Withdrawal `0x0206B274` reads the same accrued steps at `0x0206B2D2`, adds
at `0x0206B2DA`, writes field8 at `0x0206B2E2`, then runs native level processing.
Preview and withdrawal must use identical accepted growth or the fee/level quote
will disagree. The slot stride is0xEC, accrued counter at slot+0xE8.

A withdrawal-only clamp banks rejected growth until the cap rises or is disabled,
which conflicts with the requested no-banking rule if applied to Day Care.
Fresh step-loop disassembly proves why saturating the raw counter is wrong:
`0x0206BFE2` increments each occupied slot, then `0x0206C002–10` reads slot1's
counter and checks its low byte equals0xFF for breeding. The hatch counter is a
separate byte read through `0x02029818` and updated at `0x0206C046`. Neither is
spare storage. Strict discard requires separately persisted accepted-growth
accounting, deposit/withdraw lifecycle and migration, while preserving raw step
and hatch/breeding behavior. **Current decision:** under the user's explicit
risk/complexity allowance, coordinator skipped Day Care and left it unchanged.
Do not engineer that additional save format or silently substitute withdrawal
banking. Its native growth remains a documented cap exception. The historical
analysis above explains this deliberate scope choice.

Historical line1102 also identifies Pokéwalker return-growth `ov103:0x021ED910`
and its one-level native limit; this address was not freshly audited here.
Generators, gifts, captures, trades, facility normalization and imported/overlevel
Pokémon stay outside these battle hooks. A global EXP setter patch is not an
acceptable shortcut because it would affect those paths and cache/message flow.

## Fixture inventory and concrete remaining acceptance

`work/build/difficulty-v2/growth/fixtures.json` records paths, sizes and SHA-256
for locally present fixtures; presence is not evidence of compatibility with a
new ROM. Historical states must be treated as immutable input copied into each
new isolated test scope, with a fresh candidate boot preferred for lifecycle tests.

| Existing local input | Use / limitation |
|---|---|
| `work/build/exp-share-research/trainer-field.dst` | Prebattle trainer fixture used by historical native constructor/partner work; inspect before reuse |
| `.../two-ready.dst` | Field fixture with synthetic second party slot; its screenshot is overworld, not proof of two fighters |
| `.../battle.dst`, `.../test-battle.dst`, `.../afterattack.dst` | Older battle inputs; validate root/roster/PC and original hook signatures before use; cannot test constructor capture by starting after it |
| `.../wild.dst`, `.../en-field.dst` | Wild/English research inputs; no current-candidate compatibility claim |
| `.../baseline.log`, `.../baseline-stats.log`, `.../cheat-stats.log` | Prior one-participant/one-bench CN control26/13 and OFF26/0; HP EVs1/1 versus1/0, documented in `work/notes/exp_share_research.md` |

Main `work/build/difficulty-exp-caps/` is absent. Historical `/root/resolve_growth`
line971 describes partner, eggs, Lucky Egg, multi-level evolution and move-learning
results, but those result files were not recovered or rerun in this step. In
particular no existing verified **two-player-participant** or simultaneous-KO
fixture is established by the available screenshots/logs. Construct them before
claiming those requirements tested; partner+one-player is a different case.

Sequential implementation/test acceptance still needs:

1. Guarded installer wires all five seams to actual linked payload; native begin
   and free each execute once, including consecutive battles reusing the root.
   Set cap/settings between battles and prove snapshot refresh; clear stale state
   on teardown, reset, and load. Compare current TEXT SPEED baseline unchanged.
2. Fresh baseline/treatment battles with two player participants and a third bench:
   shareON/OFF × capOFF/ON, one fighter capped, one crossing, neither capped.
   Verify native raw per-recipient rewards are identical before late clamp and
   no reward moves to another Pokémon. EVs remain on capped fighters, bench gets
   none when OFF. Include eggs, fainted and level100 native eligibility.
3. Capture message queue calls `0x02224C50` for IDs0x1D/1E (amount first stack
   argument), application `0x0222AC30`, command0x1F via `0x02224BF8`, cached
   EXP+0x18, checksum-valid backing EXP and caller accepted totals. Zero accepted
   must skip the EXP flow while keeping EVs; partial/multi-level awards must match
   message/bar/backing values, prompts and evolution outcomes.
4. Sequential and simultaneous KOs; mixed participation per foe; Lucky Egg231;
   held Exp. Share216 on bench with sharingOFF; partner ownership IDs; battle-end
   gym award uses the prebattle cap and the next battle resolves the raised cap.
5. Positive cases for every allowlisted flags value; negative actual link,
   facility, replay, Safari, contest and special entry cases, plus unknown flags
   and0x801. Host switch tests alone are not native negative-fixture evidence.
6. Host FFI wrapper tests with native mocks verify shared clamp calls, cap1/100,
   threshold/current/request overflow boundaries, invalid ID/root/snapshot, native
   false/zero outputs, native eligibility level100, and preserved raw/deferred
   fields. They complement, rather than substitute for, compiled ARM hook tests.

Fresh research verification: five guarded call-site bytes and decoded BL targets
match the untouched CN overlay (`guards.json`). Native disassembly files under
ignored `work/build/difficulty-v2/growth/` include lifecycle, constructors,
context initialization, reward/cache consumers, Candy UI and Day Care counters.
No emulator process or ROM build was run in this research step. No implementation,
ROM, source save, production patch registry or unrelated dirty file was changed.
