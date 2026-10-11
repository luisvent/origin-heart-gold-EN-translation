# Native trainer Bag items implementation handoff

2026-10-10. Implemented and locally checked; **not native gameplay acceptance**.
Only `native/items.h`, `items.c`, `items.asm`, `items_hooks.json` and this handoff
were added. Scratch work is ignored `work/build/difficulty-v2/items/impl/`.
No ROM built/installed, downloads, commits, provider/lifecycle changes, shared
policy/growth/menu edits, item archive edits, or field/held/effect hooks.

## Correction after first native trainer proof

The initial host fixtures mirrored a wrong setup+168h offset and mislabeled
TrainerInfo as party. Actual native trainer5 showed the restriction bypass.
The shipping correction binds to setup+108h (`0x42 << 2`) and retains identity
checks; [items-binding-fix.md](items-binding-fix.md) and its source pins supersede
the original pointer contract and isolated compilation figures below. Current
validation uses durable tests/drivers/items_check.c with observed-address
regressions and the integrated candidate receipt, not the old scratch driver.

## Provider and C interface

Link shipping `items.c` with `policy.c` and the existing `growth.h` ABI. The only
external production provider is **the existing**
`const DG_GrowthSnapshot *dg_growth_snapshot(void)`. No extra shared ABI was
introduced. The isolated link's `impl/provider.c` always returns NULL and is
strictly a test fixture: DO NOT SHIP IT.

The real provider must certify a CURRENT, immutable battle snapshot with
nonzero epoch and positive ordinary interactive `allowed` classification.
Return NULL when unavailable/stale/unclassified; invalidate on actual battle
entry/end and reset/load even when root addresses repeat. Capture settings
before the first item/reward operation and hold them for command selection.
Pointer equality and absence of known exclusion bits do not establish a valid
lifetime or ordinary mode. Singles, doubles, partner and special classifications
remain the integration owner's responsibility and need runtime certification.

Items additionally validates known option bits, current root at `02255BAC`,
root/setup alignment and main-RAM bounds, setup trainer bit0, native known
special/tutorial veto bits `0x480`, Bag owner0, tutorial argument0, and equality
of args' Bag/TrainerInfo with setup+108h/+F8h. Setup bounds include the full referenced
0x10C bytes; Bag and TrainerInfo bounds cover0x864 and0x20 bytes respectively. It never classifies a battler by parity or by command slot.
`allowed` must describe the full ordinary context, not merely trainer bit0.
These checks fall back to native behavior when they cannot certify the scope.
They do not sanitize arbitrary corrupt pointers that native displaced loads
already require to be valid, nor independently prove epoch freshness.

Exports (all normal C AAPCS Thumb functions):

- `dg_bag_item_attr(item,attr,heap,ui)`: the list call-site's original getter
  `02076411` runs first for valid IDs; non13 attrs return unchanged. Attr13 uses
  the shared `dg_item_battle_mask`, not a second policy implementation.
- `dg_bag_remembered(bag,item,quantity,heap,ui)`: fifth UI argument is stack-passed.
  Original `02076B21` inventory result runs first and is preserved exactly on
  success outside scope or when allowed; in scope denial returns0. Native caller
  clears its UI remembered item/category. No inventory mutation here.
- `dg_bag_accept(ui)`: policy denial clears args+18h to0 and +1Ah to4, returns
  **native UI state13**. Allowed/out-of-scope calls original `021EB299`, preserving
  its capture/escape/target/battle-state validation and original state result.
- `dg_bag_commit_item(args)`: returns displaced r7 item, or clears selected
  item/category and returns0 for native cancel. Never edits a command.
- `dg_bag_commit_target(controller,party_args)`: returns original target byte+D,
  or clears selected item/category and returns6 for native reopen/cleanup.
  Already-cancelled target6 passes through. Reads Bag args at controller+5C8h;
  controller owner must agree with args owner. Does not alter other doubles
  command data, destinations, actor or slot counters.

Items1..790 are valid; 0,791+,FFFF and wide sentinels never reach a metadata
getter (including indirectly through the original inventory lookup). Invalid
selected IDs use native cancellation even outside optional policy scope. This
is explicitly a corrupt/stale-input safety case, not a change to valid wild,
NPC or special-mode behavior. Invalid UI/context preserves native delegation.

Restricted means IDs149..212 and65..67 with their **original** masks. Held-only
berries and field/key flutes gain no use. ALL is original OR exactly the20
medicine additions in `items.md`: Full Restore12, PP medicines16, HP/revival4,
status8. Keys, vitamins, Candy and arbitrary medicine-pocket items gain nothing.
All remaining native validation/effect/consumption paths are unchanged.
Day Care (D-2304) and conditional Candy support are outside this module.

## Stub and hook integration

`items_hooks.json` is a plain six-element array, each row exactly
`{file,offset,address,expect,target,kind}`. `expect` is four bytes in file order;
all `kind` values are `bl` because installation writes a Thumb BL, including
at the two instruction-replacement sites. Targets are emitted stub symbols,
NOT C functions. Normal and tutorial acceptance share the same stub. Tutorial
is included among the six sites and is gated through the same full context.
The early native whole-Bag ban at02202348 is untouched.

Invoke armips0.11.0 from repo root with absolute source/staging paths:

```text
armips ABS/native/items.asm -root ABS/STAGE -sym ABS/STAGE/items.sym
  -definelabel ITEM_STUB_BASE ALIGNED_LINKED_END
  -definelabel dg_bag_item_attr ODD_ELF_ADDRESS
  -definelabel dg_bag_remembered ODD_ELF_ADDRESS
  -definelabel dg_bag_accept ODD_ELF_ADDRESS
  -definelabel dg_bag_commit_item ODD_ELF_ADDRESS
  -definelabel dg_bag_commit_target ODD_ELF_ADDRESS
```

Without any further flag this creates **only** `item_stubs.bin`. It is272 bytes
(260 code/literals +12 zero padding), four-byte aligned, at externally supplied
`ITEM_STUB_BASE`; emitted extent labels are `DG_ItemStubsStart`,
`DG_ItemStubsCodeEnd`, `DG_ItemStubsEnd`. armips `-sym` lowercases names; resolve
JSON targets case-insensitively. All external function symbols retain ELF Thumb
bit. Input alignment, main-RAM upper bound023E0000 and odd C targets are checked.
C does not call stubs. Place stubs after the complete C initialized AND BSS owned
extent; materialize interior BSS as zeros or use a separate loader section.
Final combined arena reservation, source pins, branch reach and loader bounds
remain installer responsibilities; the isolated test address is not a layout.

Optional `-definelabel DG_ITEMS_PATCH_HOOKS 1` patches staged `overlay9.bin` and
`overlay14.bin` using six exact-byte guards and six four-byte armips areas. It
also guards the original parent frame prologue. Supply only fresh, validated
staged input copies; never run this against source ROMs. Final installer must
install the complete C/provider/stub payload before promoting hooked outputs.
Do not accept partial or already-patched inputs. The optional mode does not
replace full-file/dependency checks or install a resident loader.

All adapters enter Thumb and `bx pc` into aligned ARMv5TE code without using a
scratch register. They dynamically align SP to8 for C, restoring the exact
incoming SP afterward. Remembered-item preserves original r0-r3 and supplies
UI r4 as the fifth AAPCS argument. List supplies UI as r3. Accept preserves its
single original argument. These three use normal call-clobber semantics.

AD8/BF0 are **not normal calls**: save all r0-r12 plus hook LR, call C, replace
only saved r7/r1, then restore everything. Before resuming, reload original LR
from original hook-SP+2Ch. The enclosing `02202954` prologue is
`push {r4-r7,lr}; sub sp,#1Ch`, and state3/state5 dispatch-to-hook paths contain
no preceding BL/BLX; thus that saved LR is the exact pre-hook native LR. Merely
preserving hook-BL LR would not be equivalent. Finally ARM CMP reproduces all
NZCV of `cmp r7,0` / `cmp r1,6`; ARMv5 `ldr pc` interworks to Thumb continuations
`02202ADC` / `02202BF4` without clobbering any restored register or flags.
Native stack layout, parent saved LR, and the other doubles action remain intact.

This restoration depends on three additional **unmodified input ranges**. Final
installer must guard them (end exclusive), not merely the four-byte prologue:

| Overlay14 range | SHA256 |
|---|---|
|02202954–0220297E (frame/dispatch/table)|c0e1c2238dc930beb13445bd0e936066f3cd47b1b681472b6efa1255b5fd3304|
|02202AC2–02202ADC (state3 through displaced pair)|63d4cdb09516692fd75aa819fe3e632d9822e0698bd662377cbdffa7809c872c|
|02202BE0–02202BF4 (state5 through displaced pair)|36db224ad0f945fe9d0ba83cf7ad5efb74e054c04a25b50612fe0b9bd39de2fc|

Fresh CN/current EN both match these ranges and all six hook guards. Preserve
all unrelated EN changes: EN overlay14 differs from CN. Current checked inputs:

- CN ROM SHA2564807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8.
- EN WIP ROM SHA2566fa7b4e739391ca9ea9bfcf90d83eec6407c3c04102e52432bb41bc8ae44a7d3.
- overlay9 (both),39040 bytes: f66e9ff1ec5525797654017d246c4d61f2ae70382d25e83df0e1680dbb890b0d.
- EN overlay14,337216 bytes: 0a5fa31299fb7b97d48cc55403fad7a85610ea8142ffd3d2fb254dcb05d4e09b.
- Item archive (both), preserved bytewise: e28535d77ab2c5fdb7914279b2338a354122303a864c65ed524b79f7c0648637.

These identify the current check, not permission to substitute an old ROM or
overwrite future changes. Full fresh raw ranges and identities are in
`impl/inputs.json`; existing research documents native callee dependencies.

## Measured compilation and checks

Used local clang with `--target=arm-none-eabi -mcpu=arm946e-s -mthumb -Os
-ffreestanding -fno-builtin -fno-unwind-tables -fno-asynchronous-unwind-tables
-fstack-usage -Wall -Wextra -Werror`; local Rust `ld.lld --no-undefined` linked
items+policy with a **NULL-only fixture provider**. No undefined helpers or
runtime library dependencies. No writable globals/BSS in items. Isolated link:
text912 + rodata148 =1060 bytes, including policy and fixture provider; stubs272
more. Test placement023DC000 gives stub base023DC424 and end023DC534. **Recompute
all symbols/bounds after linking the real integration.**

Compiler stack frames: attr24, remembered24, accept16, commit-item16,
commit-target16, denied16, context24, mask24 bytes; pure policy0. Stub maximum
stack depths for both possible incoming word alignments: list12, remembered20,
accept12, each backstop60. Largest own call-chain bound is116 bytes at a backstop,
excluding native getter/provider stacks and the existing parent48-byte frame.
Provider/native stack budgets and actual interrupt behavior still need integration
review; these are not whole-game stack limits.

Actual fresh checks, all passed:

- `impl/host_check.c` linked shipping items.c+policy.c with
  `DG_ITEMS_HOST_TEST`, AddressSanitizer and UndefinedBehaviorSanitizer:524288
  list cases (8 flag combinations ×65536 IDs); valid non13 delegation; all
  item/flag combinations through accept, remembered and both commit gates;
  sixteen missing/stale/invalid-root/setup/context/owner/identity fallbacks;
  native inventory failure and exact nonboolean success passthrough;
  invalid/sentinel-before-getter; target6; owner mismatch; cancel-state13.
- Whole synthetic-RAM comparisons permit changes ONLY at selected item/category;
  nonzero command buffers/destination/slot/actor state remain unchanged. These
  are synthetic memory checks, **not proof of both native doubles slot mappings**.
- Fresh actual CN archive checks:791 ×34-byte records; all20 additions have
  native dispatch2/discriminator1 and original mask0; full stocked category
  counts CN11/10/25/10, ALL23/19/25/10, restricted3/10/0/0; no4+16 duplicate.
- `impl/check_stubs.py`: actual armips binary generation and six BL target
  disassemblies; only declared windows change on both CN and current EN staged
  overlays. Corrupt each of six guards and the frame guard: all seven fail and
  leave staged overlays byte-identical. Standalone and patch-mode stub output
  identical. No Python-generated instruction words.
- Restricted instruction model over **actual emitted ARM/Thumb stub bytes**:
  1536 cases across all six hooks, SP mod8=0/4, all initial NZCV combinations,
  and boundary outputs. Mock C clobbers volatile registers/flags. Verifies
  argument forwarding including fifth stack argument, aligned C SP, exact
  restored SP/live registers/original LR and final CMP NZCV/Thumb continuation.
  This intentionally small model is **not an emulator or execution of ARM C**.
- `impl/check_inputs.py`: fresh read-only CN/current EN guards/identities,
  dispatch/table targets and absence of calls on the entry-to-backstop paths.
  Source-bound hashes and compiled sizes are in `impl/receipt.json`.

Host mocks are only native memory/primitive calls and the shared snapshot
provider; optional policy and guards execute the same shipping C. No host
substitute policy, pass-through candidate ROM, emulator outcome, or visual
acceptance is claimed. Scratch test commands (run from repo root):

```sh
work/build/difficulty-v2/items/impl/host_check
.venv/bin/python work/build/difficulty-v2/items/impl/check_inputs.py
.venv/bin/python work/build/difficulty-v2/items/impl/check_stubs.py
```

Remaining serial owners: integration supplies lifecycle/context/provider and
complete guarded loader/installer; test agent promotes appropriate tests and
runs actual native ARM/UI gameplay. Required gameplay still includes all20
medicines/effects and no-effect semantics, stale last-use/accept/both backstops,
turn and inventory preservation, repeated reopen/pagination, each local doubles
slot/backtracking/other pending action, partner/NPC/held paths, wild/tutorial/
special modes, setting changes between battles and reset/load. Hardware/DeSmuME
interworking and stack behavior must be checked on the combined candidate.
