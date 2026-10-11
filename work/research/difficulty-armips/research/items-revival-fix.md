# All-mode battle revival correction

Scope: D-2322 conditional fidelity, baseline already recorded in D-2323. Original
Chinese field Revive and candidate field Revive both healed once (0→15/max31,
quantity3→2). Both native wild controls hide Revive. Original CN trainer stock
has no28/29/37. Matching dormant code does not prove original reachable battle
doubling. This correction applies only to the newly enabled All trainer path.

## Cause and seam

The item-effect loop at022217C8 iterates19 native entries at0224D19C. Its
attribute getter at022218C0 is the only new hook. The original frame is0x48
bytes; actor is saved atSP+8 and resolved target atSP+20h. The table reads an
8-bit attribute at each8-byte entry. Attr23 (entry8) calls02221E30; attr38
(entry18) calls02221B84. Item records28/29/37 have both bits and original battle
mask0. Attr54 isFE (half max) for28, FF (full) for29/37.

Revival ancestry:02221E30→02223610→0222ADFC→02217834 at0222AE0A,
then the legitimate revival event31. Ordinary heal ancestry:
02221B84→02221BEC→0221F968→0222A0A0→02217834 at0222A0C2.
The second callback can see a now-living target and enqueue a second heal.
Trace79a7c9c917f445ac82d36a3bfa2be1fe confirms the two HP-write return addresses
and15+15 on consecutive frames; the complete callback ancestry above is static
source proof, not a claim that the old trace captured every intervening call.

The new wrapper returns0 only for attr38 of28/29/37 when the shared snapshot is
valid, allowed, nonzero epoch, known flags and All; current root must match and
setup must pass bounds/trainer/special vetoes. Actor AND target must be local
owner0 IDs1..6 and match root resolver slots at1D0h+4*ID. This includes bench and
both local doubles actors, excludes NPC/partner IDs and forged local IDs.
Native getter runs first for valid items. Invalid IDs fail before archive access.
All other attributes, contexts and items retain native results. Attr23 and its
messages, HP write, inventory and turn handling remain native. The redundant
ordinary-heal callback is omitted, not a generic event31 or HP-add suppression.
Full revivals also omit it rather than relying on max-HP clipping.

## Lifetime and ABI

There is no new mutable state, token, allocation or pending-event identity.
Actor/target are live native locals while the synchronous effect loop owns them.
The provider dg_growth_snapshot() retains its existing current setup/root/save
identity and generation validation; no provider ABI change. Every getter call
revalidates context, so epoch/root changes cannot carry a suppression token into
another battle or action. The resolved target's identity is checked independently
of the actor. Concurrent pending native events and other doubles commands are
neither read nor written.

The armips Thumb entry switches to ARM, preservesr4/LR, loads originalSP+8/+20h,
aligns the C callSP to8, supplies target as fifth argument, and restores exact
entrySP. Temporary stub stack is16 or20 bytes. Return flags are caller-clobbered:
022218C4 immediately establishes flags with adds r2,r0,#0. Existing instruction
replacement hooks retain their stronger NZCV/register contracts. Items stub
reservation grows272→336 bytes; linker symbols determine placement. Pointer
checks exclude resident memory at023DC000 and above. No instruction encoding in
Python, no global getter patch, no archive edit.

## Guard and verification contract

items-revival-pins.json pins14 source ranges covering frame/locals, effect loop,
table, attribute decoder and both callback chains. All matched independently in
fresh CN, pinned completed English input and previous47f802... candidate.
Installer checks these dependencies in addition to whole-section and exact-hook
bytes. Seventh items hook is BL at022218C0, expected54f6a6fd. Exact-diff installer
must reject every undeclared edit and preserve original NARC bytewise.

Host driver compiles shipping C under sanitizers, exhausts65536 IDs×8 modes,
all attributes0..58 for three revivals, all36 local actor/target combinations,
invalid ownership/context/bounds, epoch changes and NPC interleaving. It checks
unchanged simulated HP, pending commands and native getter calls. Mutation tests
exercise wrong attribute, missing All scope and missing actor binding. Actual
assembled ABI model covers7 seams×256 register/flag/alignment cases (1792).
These are not gameplay acceptance; parent must verify28/29/37 one heal/setter,
correct target, one quantity decrement/turn and ordinary messages. Keep the
existing field/wild baselines and Mill effect trace contracts unchanged.

Parent native commands (not run by this implementation task):

```
.venv/bin/python work/research/difficulty-armips/tests/run.py --native --native-phase items --items-item 28 --native-timeout 180
```

Repeat with29 and37. Require half-HP15 for28 at max31, and one callback/write even
for full revivals; clipping must not mask a duplicate. Native controls remain
work/build/difficulty-v2/tests/native-tests/items-field/ffa3cc3dec2c4f178f649cd4898a8d67
and items-controls/7ae998382378477cadf60508a189ab88.

ARM clang stack report: dg_bag_effect_attr24 bytes; local_mon8 bytes.
The wrapper also calls the existing snapshot provider and native getter; these
figures describe individual generated frames, not total native call-chain stack.
Implementation host run:124 passing tests; native acceptance remains pending.
Candidate resident6692 bytes (+320), within16384 reserved.
