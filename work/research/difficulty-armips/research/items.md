# Native trainer Bag item policy — implementation contract

Research date: 2026-10-09. Scope: optional **Berries/flutes / ALL**, player trainer-battle Bag actions only. This document specifies native implementation seams; no production hook, ROM or save was modified in this research. All addresses below were extracted afresh from the untouched Chinese ROM, and all listed hook guards also match the current English WIP. Native runtime tests are still required; static control-flow proof is distinguished below from runtime acceptance.

## Native-proof correction (2026-10-10)

The first implementation miscomputed `0x42 << 2` as168h. It is108h.
This caused context validation to bypass restricted policy in actual trainer5
entry. Args+0/setup+F8 is TrainerInfo, not a Pokémon party; Pokémon parties
are setup+4+4*owner. See [shipping correction and source proof](items-binding-fix.md)
and `items-binding-pins.json`. The corrected identity check still binds to the
current setup's own Bag clone; it does not accept arbitrary RAM or compare
the clone to the separate SaveData Bag pointer.

## Handoff first

Use the shared `native/policy.h` / `policy.c` function:

```c
uint32_t dg_item_battle_mask(uint32_t item_id, uint32_t original_mask,
    uint32_t all_mask, uint32_t player_trainer_bag, uint32_t items_all);
```

`DG_ITEMS_ALL == 4`. Pass `(snapshot_flags & DG_ITEMS_ALL) != 0`, not the complete flags word. Keep berry IDs149..212 and flute IDs65..67 as the core specifies. Retain the original mask for allowed families: do not grant battle use to held-only berries, White/Black Flutes, the Poké Flute/radio, or arbitrary keys. Potion17, Super Potion26, drinks30..33, Heal Powder36 and Berry Juice43 are all deliberately excluded in restricted mode even though CN exposes them.

The principal seam is **overlay9**, not the field Bag overlay17 or overlay16. Battle Bag and its party-target UI coexist in overlay9. Overlay14 owns command construction and item execution.

| Purpose | File/base | Address / file offset | Original bytes (hex, little endian) | Original operation |
|---|---|---|---|---|
| Visible lists | ov9 / `021E4DA0` | `021EC308` / `7568` | `8A F6 82 F8` | BL `02076410` (`Item_GetAttr`) |
| Remembered last-item eligibility | ov9 | `021EC266` / `74C6` | `8A F6 5B FC` | BL `02076B20` (inventory availability) |
| Normal Use acceptance | ov9 | `021EB264` / `64C4` | `00 F0 18 F8` | BL `021EB298` (native item validation) |
| Tutorial's separate acceptance call | ov9 | `021EB6B8` / `6918` | `FF F7 EE FD` | BL `021EB298` |
| Returned Bag item, before category dispatch | ov14 / `022007E0` | `02202AD8` / `22F8` | `0F 8B 00 2F` | `ldrh r7,[r1,#18h]; cmp r7,#0` |
| Returned party target, before command creation | ov14 | `02202BF0` / `2410` | `51 7B 06 29` | `ldrb r1,[r2,#0Dh]; cmp r1,#6` |

Implement **all three layers**: menu/last-item visibility, Use acceptance, and the two command-construction backstops. Do not claim the menu patch alone enforces the rule. The tutorial call can also use the acceptance wrapper provided its context test passes wild/tutorial calls through; alternatively leave that call untouched and explicitly demonstrate it cannot run in an affected trainer context.

### Proposed C/native interface

These are suggested adapter APIs, not additional definitions to impose on the portable core:

```c
/* Call-site adapter at 021EC308 supplies original r0-r2 plus r3=r4. */
u32 dg_bag_item_attr(u32 item, u32 attr, u32 heap, void *bag_ui);
/* Reads attr13 with the native getter; invokes the shared core. */
u32 dg_bag_effective_mask(u32 item, u32 heap, u32 trainer_owner);
/* Original function 021EB298 takes one argument and returns a UI state. */
u32 dg_bag_accept(void *bag_ui);
/* Assembly adapters can call one shared gate at either ov14 backstop. */
u32 dg_bag_allowed(u32 item, u32 heap, u32 trainer_owner);
```

`bag_ui` begins with a pointer to Bag args. The useful Bag args fields are:

| Offset | Type | Meaning/evidence |
|---|---|---|
| `+00` | pointer | owner TrainerInfo, populated from setup+F8h+4*owner at `02202A64..68`; not a Pokémon party |
| `+04` | pointer | cloned battle Bag, from setup+108h at `02202A54..56` |
| `+08` | u32 | heap ID, set to5 at `02202A6A..6C` |
| `+0C` | u32 | trainer/party owner, copied from controller byte+2 at `02202A74..76` |
| `+10` | u32 | tutorial mode, set by native `0400h` flag test at `021EAD4C..5C` |
| `+18` | u16 | selected item; zero means cancel |
| `+1A` | u8 | selected displayed category (0 HP/PP, 1 status, 2 balls, 3 battle items; 4 cancel) |
| `+1B` | u8 | remembered last-item category |
| `+1C` | u16 | remembered last item |
| `+22` | u8 | child UI finished flag |
| `+23..27` | bytes | category cursor positions |
| `+28..2C` | bytes | category page positions |

`dg_bag_item_attr` must first call unmodified Thumb `02076411(item, attr, heap)` and return its value unchanged for every attr except13. It is a **call-site wrapper**, never a replacement for the global getter. For attr13 call the shared core with the table below. Acceptance and both backstops must re-read the same native attr13 and call the same core, not trust the displayed list or category.

The last-item call already uses all four argument registers: `(bag, item, quantity=1, heap)`. Its assembly adapter must preserve those values, call the original `02076B21`, and AND successful availability with policy eligibility using the UI pointer held in native r4. Do not replace the inventory test with the policy test. A small assembly adapter may pass an explicit fifth UI argument on an aligned stack or call a C helper with `(bag_ui, native_result)` and have it read item/heap/owner from args. Preserve original result outside the policy's context.

The module must import the settings owner's **valid, opt-in runtime setting snapshot**, without reserving save bytes or editing text-speed itself. A snapshot fixed for the duration of command selection avoids changing policy between selection and execution. No module-specific ARM9 autoload region is necessary: export these wrappers from the candidate's declared resident payload, generate their actual linked addresses, and patch only these guarded overlay sites. The installer must install that complete payload before enabling its BLs; a resident diagnostic bridge is not the feature. Keep the shared core in the shipping link so host tests exercise shipping policy.

## Battle-context and ownership contract

`022156B4()` (Thumb pointer `022156B5`) returns setup flags in concrete steps: load global pointer at02255BAC, load +10h setup pointer, load setup+0 flags. Guard16: `02 48 00 68 00 69 00 68 70 47 C0 46 AC 5B 25 02`. Trainer classification is bit0. Wild mode must return **original mask**, including currently disabled medicines, irrespective of ALL.

The Bag creator copies owner `controller[2]` into Bag args+0Ch. Treat this as an owner index, not an even/odd battler index. Native item consumption at `02215A2C(owner,item)` distinguishes **owner0**, which removes from player Bag, from nonzero owners, which remove from their own four trainer-item slots. This is strong binary evidence for restricting the policy gate to owner0. Confirm it at runtime for both locally controlled doubles slots and a partner fixture; do not implement “only battler0” or “all player-side battlers.” Party-mon internal indices are grouped by owner through `022157D4`; its table at0224D130 is `[1,13,7,19]`, not a simple parity mapping.

The narrowly affected context is: resident settings valid/active, local player owner0, trainer flag set, ordinary interactive battle. Preserve every native precondition. The existing Bag command denial at `02202348..56` calls the flags getter then tests80h. **Never change `80 21` at0220234C to8121**: that historical whole-Bag denial is rejected. Keep the native special-mode exclusion/context classification supplied by the battle/settings owner; this item module does not invent a complete CN flags enum. Link/recorded/facility/tutorial/special-mode classification beyond the observed native80h and400h tests still requires runtime/initializer confirmation. Where classification is not certified, pass through rather than enable new items in that mode. Ordinary singles/doubles and ordinary partner battles must be affirmatively covered before completion.

The overlay9 wrapper sites affect human menu calls, not AI item choice. The final core predicate alone does not enforce special-mode bans: the wrapper and unchanged native UI/action checks do. No hook belongs in held-item dispatch, field Bag, global inventory removal, or global item-effect functions.

## Item metadata and ALL expansion

Native ARM9 functions, **actual CN addresses**:

- `0207638C(item, selector, heap)` loads item data. Selector0 calls archive ID17 (`a/0/1/7`) with member=item directly at0207639E..A6. Thus CN item IDs here really are archive member IDs. There are791 records (IDs0..790), each34 bytes.
- `02076410(item, attr, heap)` loads selector0, calls `02076434(data,attr)`, and frees the allocation through0201B3B0. Do not return a retained pointer into this allocation.
- Attr12 (ordinary pocket): halfword+8 low5 bits at020764A0. Attr13: `(u16(data+8) >> 11) & 31` at020764A8, guard `00 89 00 04 C0 0E 08 BD`. Attr7: byte+0Bh (battle-use dispatch type). Attr14: byte+0Ch (effect-data discriminator). Attr15+ dispatch through020764D0 into the effect payload when discriminator=1.
- `02076DA8(bag,pocket,index)` returns the native inventory slot or zero; overlay9 enumerates all eight physical pockets. `02076B20` checks inventory availability; `02076AA4` removes quantity. Do not modify these globally.

For ALL, preserve native `original_mask`, adding only these validated ordinary medicine masks to the twenty records CN sets to zero:

| IDs | Names | Added battle mask |
|---|---|---:|
|18,19,20,21,22|Antidote, Burn Heal, Ice Heal, Awakening, Parlyz Heal|8|
|23|Full Restore|12 (HP + status)|
|24,25|Max Potion, Hyper Potion|4|
|27|Full Heal|8|
|28,29|Revive, Max Revive|4|
|34,35,37|Energy Powder, Energy Root, Revival Herb|4|
|38,39,40,41|Ether, Max Ether, Elixir, Max Elixir|16|
|42,54|Lava Cookie, Old Gateau|8|

`all_mask = original_mask | added_mask[item]`; for every other valid item, `all_mask = original_mask`. Reject invalid/sentinel selected IDs before calling the archive getter. Do not infer usability from ordinary pocket=medicine: vitamins, Rare Candy, etc. share medicine structures but are not ordinary battle actions. Do not import the entire US archive by record index: the CN loader/data layout is what was proven. Preserve the native masks of custom balls and all other hack items, and allow native validation to reject trainer captures.

This deliberately differs from blindly copying Bradams' byte9 edits: Bradams gives PP items mask4 and Full Restore mask4, whereas this table exposes PP in its native category and Full Restore in both appropriate lists. This is a **proposed menu categorization**, not a measured Bradams runtime result. The item's healing/status/PP quantities and effects remain untouched. The underlying twenty-item addition set is exactly the static audit in `work/notes/bradams_items_moves_analysis.md`; all20 have native dispatch type2 and effect discriminator1 in CN. The effect engine has handlers for their native payload attributes; no effect-mask override is needed to make their native handlers reachable once selected.

Native list construction at021EC2CC enumerates owned nonempty slots, requests attr13, and interprets bits0..4 using table021EE3B4 = `[2,3,0,1,0]`: balls, battle, HP/PP, status, HP/PP. Each category has36 slots (90h-byte stride, four bytes per entry), with count bytes at UI+114Fh. Counts for an inventory containing every distinct eligible item once:

| Policy | HP/PP | Status | Balls | Battle | spare category |
|---|---:|---:|---:|---:|---:|
|CN|11|10|25|10|0|
|ALL proposed|23|19|25|10|0|
|Berries/flutes|3|10|0|0|0|

No category exceeds36. Avoid returning both4 and16 for an item: both bits map to the same category and would append duplicate entries. Full Restore12 maps to different categories and is safe. Runtime must still test maximum stocked lists, pagination, last-used category and repeated reopening; corrupted duplicate inventory entries are not part of this capacity proof.

## Visibility, Use, cancel, and commitment

1. At021EACD4, native Bag init allocates115Ch bytes, restores last-item state, calls021EC250 to validate the remembered item, then starts the task. `021EC250` checks item count but **does not check battle-pocket eligibility**. Hence menu filtering alone leaves a last-item bypass, including an item remembered from a wild battle. When its wrapped availability call returns0, native021EC26E..76 clears only the UI's remembered item and category; preserve persistent inventory.
2. `021EC2CC` constructs filtered lists via the wrapped attr13 read. The “last item” button at021EAFC6 separately tests args+1Ch, so the preceding last-item hook is required to hide it.
3. Normal Use at021EB234..64 records selected item/category, starts a UI transition, then calls021EB298. The tutorial has a second call at021EB6B8. `dg_bag_accept(ui)` re-reads effective mask. If in scope and denied, write args+18h=0 and args+1Ah=4, return13. Native state13 (`021EB4D8`) fades out; state14 (`021EB500`) releases the UI and sets args+22h=1. The parent sees cancel. If allowed, call original021EB298 unchanged; retain its battle-state, target and item-type rejection paths.
4. `021EB298` must be guarded **before** its native code, because escape-type items can remove inventory early: category3 reads attr7; type3 in a wild battle calls021EBA64 at021EB340, which calls02076AA4 at021EBA7C and remembers the item. Trainer mode instead displays the native rejection. We leave this intact. Restricted trainer use must never reach an effect/consumption path by a stale shortcut. Do not simply return0 from021EB298: its return value is a UI state, not an allow Boolean.
5. Parent handler02202954 state3 reads the child's finished flag, clears it, loads selected item at02202AD8, and branches to native cancel if item=0. Categories2/3 go directly to command creation; categories0/1 go to party-target selection. The proposed AD8 adapter rechecks policy and, on rejection, clears args+18h and gives r7=0; reproduce `cmp r7,#0` flags and resume02202ADC. Native02202B3A sets state6 (cleanup), and the final selected-item test at02202D24 sends cancel to command-selection function02202444 instead of action completion02202124. No command is constructed on this path.
6. State5 polls party completion at02202BE0. At02202BF0 the native target index6 means cancel: state becomes2 (reopen Bag), then native02202C4E..64 clears completion and frees the temporary party and UI args. A BF0 adapter rechecks selected item from `*(controller+5C8h)+18h`; on denial give r1=6 and reproduce `cmp r1,#6` flags, resume02202BF4. Keep r2 pointing to the original party args and preserve r0 (5C4h offset), r4 controller, all other registers, and SP. For policy denial it is reasonable also to set Bag selected item=0; do not alter previously accepted commands for the other doubles slot.
7. Accepted direct actions remember the last item at02202B16 and encode an item command at02202B26. Targeted actions do so at02202C22 and02202C44. Both call02200A30, which zeros the12-byte command and writes type2, item bits4..19, target and move-selection metadata. **Neither encoding call performs policy validation**, so retain both earlier backstops. Do not replace these calls with a no-op: their callers would still advance to action completion.
8. Controller+584h is the current actor, +588h the current12-byte command destination, +599h the command-slot index. `02202068` selects the actor/destination; `02202124` advances slots. This explains why the same parent handler/backstops apply to both doubles actions without hardcoding a battler number. Native cancellation avoids incrementing the current slot. Final proof must watch both destinations and counters, not merely unchanged HP.

The AD8 and BF0 sites are **instruction replacements, not ordinary ABI calls**. Their wrappers must restore all live registers except the stated native outputs and set NZCV exactly as the displaced CMP does. Save/restore LR, align SP for C calls, preserve Thumb interworking and original stack layout. BL reach must be checked from both overlays to the linked resident payload; do not assume historical foundation addresses provide enough space. All actual hook replacements need exact-byte guards and size-bounded armips areas; branches into the resident payload use linker symbols, not guessed absolute offsets.

## Native effect/consumption trace — leave this code intact

The accepted action dispatcher `0222019C` selects type2 and calls `02221674(actor,item,arg2,arg3)` at022201CE. That routine allocates an effect result, calls `022217C8`, and checks result+4. Only a true result+4 reaches `02215A2C(owner,item)` at022216B8. Owner is derived from the actor's internal index (`022167A0` returns actor+14h, then022157D4 maps it to an owner). `02215A2C` removes player inventory via02076AA4 only for owner0; nonzero owner removes its own trainer-item slot. This shared path must not become a global trainer-item ban.

`022217C8` zero-initializes its result, resolves target/context (`02221C38`), leaves native capture and escape special cases intact, and calls02221C98 for applicability. It does **not** read attr13 to authorize the action: the menu mask is not a late effect validator. At022218BA..E4 it walks19 attr/callback entries at0224D19C; a successful effect callback sets the consume result at02221918. Attributes are15..23,27..33,36..38. Native PP handlers are02221F68/02221FFC, reading quantity attr55, and the native healing/status/HP handlers remain present. Native no-effect behavior is distinct from policy cancellation and must not be overwritten.

Therefore the implementation's policy action validation belongs **before command commitment**, with the same metadata policy read again, not inside the effects loop. A guard added only at02221674 would be too late to promise no turn consumption. A debug fault injection that corrupts an already committed action cannot be claimed to cancel through these UI hooks; that is outside normal user entry paths. No-effect target selection/turn semantics must match CN independently of this optional restriction.

## Install and evidence contract

Fresh source ROM: `work/rom/origin_v4.0.3_cn.nds`, SHA256 `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8`.

- ov9 base021E4DA0, length39040, SHA256 `f66e9ff1ec5525797654017d246c4d61f2ae70382d25e83df0e1680dbb890b0d`.
- ov14 base022007E0, length337216, SHA256 `6429a2e023b8b3f4bb90076a29e30a3aaa204c94f3e6d1986161102a22559312`.
- CN item archive SHA256 `e28535d77ab2c5fdb7914279b2338a354122303a864c65ed524b79f7c0648637`.

These whole-overlay hashes identify the research input, not permission to overwrite concurrent English fixes. Installer must stage from the intended current EN build, verify each modified window and dependency, and preserve all unrelated differences including text speed and battle-targeting changes. Retain the original item archive byte-for-byte. Original ROM/save paths are read-only inputs; all candidate outputs and reports belong in ignored `work/build/difficulty-v2/<scope>/`.

Reproducible, newly written, read-only-input analysis scripts:

```sh
.venv/bin/python work/build/difficulty-v2/items/analyze.py
.venv/bin/python work/build/difficulty-v2/items/evidence.py
.venv/bin/python work/build/difficulty-v2/items/analyze.py ov9 0x021ec2cc 0x021ec3ac
```

They produce ignored extracted binaries, disassembly, item metadata and `guards.json`. The latter verifies16 windows against CN and `work/build/origin_hg_v4.0.3_en_wip.nds`; all matched on this pass. Snapshot hashes identify the particular WIP checked; future builds must be checked anew. No historical command was executed. Historical inventory was consulted for scope/provenance: `/root/battle_rules` record lines240,305,362,396,424,544 document the superseded whole-Bag experiment, not a usable per-item implementation. The inventory is at sibling `poke-difficulty-research/work/research/difficulty-recovery/record-inventory.json`.

## Required concrete proof before claiming complete

- Fresh emulator traces at all six proposed sites: log mode flags, native mode getter022157C8, owner, item, original/effective masks, selected category and command slot. Certify the active ordinary/special context predicate, owner0 for both local doubles slots, and nonzero owner for partner/NPC consumption. These mappings have static evidence but not a fresh runtime result in this research.
- Restricted trainer: Potion, Super Potion, all drinks and X items absent; eligible berries and three flutes visible. Seed last-used Potion from a wild battle, reopen trainer Bag, prove shortcut absent. Force a stale selected Potion before acceptance and at both parent backstops; verify count/HP/status/PP/action type/turn and current slot unchanged, then Fight/Switch work.
- ALL trainer: test each of20 enabled medicines with a meaningful damaged/status/fainted/PP-depleted target, including Full Restore's two list locations and Ether's move-selection UI. Cancel at every stage and compare inventory/action/turn counters. Native no-effect cases must retain CN behavior.
- Test ALL→restricted between battles and repeat Bag reopening/pagination with every eligible item stocked. Confirm last-used revalidation, no duplicate4/16 category entries, no UI overflow.
- Trainer doubles: deny/cancel for each controlled slot; backtrack after choosing the first slot; confirm allowed item on bench/each active target consumes exactly once, without erasing the other pending action. Partner trainer: local policy applies while partner's own item and held-berry behavior remains native.
- Wild, capture tutorial, scripted wild, wild doubles, Safari/Contest/Pal Park, link/facility/recorded battles: preserve native visibility and existing bans. In particular ALL must not re-enable CN medicine availability in wild encounters. Field medicine, held items, NPC items remain unchanged.
- Negative installer checks: any guard mismatch or incomplete payload/layout aborts before output promotion. Verify declared autoload destination/BSS/arena bounds and instruction-cache requirements with the integration owner, not just compiled policy unit tests. Current text-speed behavior must remain intact.

Open uncertainty is explicitly the runtime context certification and end-to-end behavior above. The item table, native metadata reader, separate remembered-item bypass, both native cancellation continuations, command encoding and effect/consumption seams are concrete enough to implement now. This contract does not claim a late effect-only guard can refund a turn or that a static matched guard proves the feature works in-game.
