# Shipping Bag binding correction after native trainer proof

2026-10-10. Sole active implementation; no emulator or subagent launched.
Runtime classification, D-2312 never-decreasing gym caps, options, policy,
assembly hooks and native effect logic remain unchanged.

## Observed failure and cause

The parent's source-bound `items_all/result.json` and
`items_restricted/result.json` belong to candidate
`bb625d52cc2d90fad69708d1d198d5c15d4ce76fdd36b524e703a0fa77848cf4`.
Both trainer5 entries have flags1/control0 and a valid allowed snapshot. At
frame5503, Potion17 native mask4 incorrectly returns4 even with flags0.
The former `context()` read setup+168h as Bag, found0, and correctly bypassed
optional policy on an invalid identity—but the identity offset itself was wrong.
The original host fixture mirrored that error, so its exhaustive tests missed it.

The actual creator uses **hex42 shifted left2 = hex108**, not168. The historical
research arithmetic was wrong. The shipping code now reads **setup+108h** and
still requires its pointer to equal args+4. It also still binds args+0 to the
owner0 identity at setup+F8, now correctly named **TrainerInfo**. Pokémon party
pointers are setup+4+4*owner; these must not replace the TrainerInfo check.

The captured raw setup dumps independently establish:

| Mode | setup | root | args+4 = setup+108h | args+0 = setup+F8h | setup+168h |
|---|---:|---:|---:|---:|---:|
|All|36349884|36441908|36360736|36351872|0|
|Restricted|36349964|36441988|36360816|36351952|0|

The trace keys named `party` were actually TrainerInfo. Trace `context.bag=0`
was the same wrong-offset observation, not evidence that the real Bag was absent.
The All run's Potion healing1→21 is a native baseline action; it does not prove
ALL additions worked. Its recorded inventory bytes/counts were taken through
address0 and are invalid evidence. No consumed quantity is inferred from them.

## Fresh native allocation, copy, creator and consumption proof

Ten reviewed spans are byte-identical in fresh untouched CN, pinned completed
EN input `a5a418b2…51f40`, and the observed candidate. Exact paths, hashes,
ranges and selected trace events are in `items-binding-pins.json`; full numeric
disassembly stays in ignored `work/build/difficulty-v2/items-binding-fix/`.

- `02050CDE` allocates a Bag through `020767F4(heap)`; `02050CE2..E6`
  computes42h<<2 and stores the returned pointer at setup+108h. The allocator
  allocates/zeros **864h bytes**. This is an owned battle allocation.
- `02051092` reads the source SaveData Bag via **02076E28** (Thumb02076E29).
  That accessor sets entry index3 and tail-calls02027740. `02051170..78`
  copies from this source to **the distinct setup+108h destination**, through
  `02076820(source,destination)` (Thumb02076821), copying864h bytes. Therefore
  comparing the live battle pointer directly with the SaveData Bag is wrong.
- `02202A4A..56` follows current root→setup and copies setup+108h into UI args+4.
  `02202A58..76` copies setup+F8h+4*controller.owner into args+0 and the same
  controller owner byte into args+C. Owner0 is required by shipping policy.
- `02050CA4..B6` allocates Pokémon parties at setup+4+4*owner and TrainerInfo
  at setup+F8+4*owner separately;02029370 allocates32-byte TrainerInfo objects.
- `02215A2C` distinguishes owner0 from NPC owners; its owner0 path at
  `02215A66..6E` reads the same setup+108h and calls native remove02076AA4.
  NPC owners retain their trainer-slot path. `02050FBC..C2` frees this Bag clone.

Shipping validation now covers the referenced setup10Ch bytes and full native
Bag864h/TrainerInfo20h ranges, alignment and exact identity. It retains all
snapshot/root/epoch/known-flags/owner/tutorial/special guards. It neither drops
ownership checks nor accepts an arbitrary aligned pointer. Invalid/unclassified
contexts still preserve native baseline; they never enable ALL additions.

Installer `validate_item_binding()` independently guards all ten reviewed spans
before compilation/installation, in addition to full pinned input and existing
hook/control-flow guards. The source-ROM test checks the spans against untouched
CN and explicitly decodes42h<<2 from the real creator instruction pair.

## Regression and validation boundary

The durable shipping-C driver first recreates both observed pointer layouts,
with setup+168h left zero, and tests all eight option combinations for Potion17
and newly enabled Antidote18. It **failed before the fix** on restricted Potion
returning4. Corrected code passes. Its exhaustive65536-ID ×8flags suite now uses
setup+108h, with an unrelated nonzero decoy at+168h to prove that old field has
no influence. All four policy gates retain coverage. Twenty-two fallback cases
include null, misaligned, mismatched and insufficient-range Bag/TrainerInfo
pointers. Cancellation still changes only selected item/category; original
inventory and validation delegation and other command buffers remain covered.

Mutation tests explicitly reject restoring168h and removing Bag identity
comparison. Independent installer negatives corrupt each of the ten native
contract spans and require rejection. The usual host/static suite additionally
checks current ARM/link/armips ABI, source pins, guarded installation, metadata
preservation and unchanged deferred field exceptions. No native pass is claimed
for the rebuilt candidate; the final candidate/source identities and test result
are in the current ignored integration receipt and tests/report.json.

The next test agent should separately repair `tests/native_items_trace.py`:
both Bag reads use108h, `party` on args+0/setup+F8 is renamed TrainerInfo, and
the inventory oracle must validate an actual Bag pointer and real native pocket
layout before reading. Native Bag size is864h, including the trailing fields;
verify chosen inventory spans/offsets instead of inheriting the old garbage
comparison. Those trace/oracle files are intentionally unchanged by this fix.
Parent then reruns restricted empty-list/cancel behavior and an ALL-only medicine,
followed by the remaining stale/accept/backstop/doubles/context cases. Old native
proof is source-stale and cannot be credited to the rebuilt candidate.
