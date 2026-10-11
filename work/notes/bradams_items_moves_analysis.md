# Bradams fork: healing items, move flags and HM replacement

Audit date: 2026-10-05. This report describes decoded Speedoption versus untouched Chinese v4.0.3 and NoBigText. It is a static binary audit, not an in-game test. Evidence inventory and scratch disassembly are in ignored `work/build/bradams-audit/`; the [chat audit](bradams_fork_audit.md) supplies release claims and message citations. No changes have been adopted into our translation.

## Healing items: twenty availability edits

The live item archive `a/0/1/7` changes exactly twenty records. Each is 34 bytes; in each changed record the **only difference is byte9**, previously zero. Healing quantities, prices, status-effect fields and all remaining bytes are unchanged. The complete list is:

| Item ID | Item | Byte9, old → new | Battle-pocket value |
|---:|---|---|---:|
|18|Antidote|00 → 40|8|
|19|Burn Heal|00 → 40|8|
|20|Ice Heal|00 → 40|8|
|21|Awakening|00 → 40|8|
|22|Parlyz Heal|00 → 40|8|
|23|Full Restore|00 → 20|4|
|24|Max Potion|00 → 20|4|
|25|Hyper Potion|00 → 20|4|
|27|Full Heal|00 → 40|8|
|28|Revive|00 → 20|4|
|29|Max Revive|00 → 20|4|
|34|Energy Powder|00 → 20|4|
|35|Energy Root|00 → 20|4|
|37|Revival Herb|00 → 20|4|
|38|Ether|00 → 20|4|
|39|Max Ether|00 → 20|4|
|40|Elixir|00 → 20|4|
|41|Max Elixir|00 → 20|4|
|42|Lava Cookie|00 → 40|8|
|54|Old Gateau|00 → 40|8|

These bits are the battle-pocket portion of the item flags: bit13 of the little-endian halfword at+8 is battle-pocket value4, and bit14 is value8. The retail layout names these HP restore and status restore respectively; PP restore is value16. Thus Ether and Elixir are assigned value4, not their usual PP-specific value16. Retail combines HP/PP into one displayed list, but this audit does not claim to have exercised every modified-hack bag consumer. Full Restore receives only value4, not both HP and status flags. Primary structural references: [ItemData definition](https://raw.githubusercontent.com/pret/pokeheartgold/master/include/item.h), [battle-pocket constants](https://raw.githubusercontent.com/pret/pokeheartgold/master/include/constants/items.h). The changed bytes themselves were measured in the supplied binaries.

This enables availability in battle menus; it is **not a repaired healing calculation**. Potion, Super Potion, ordinary drinks, Heal Powder, Sacred Ash and other unlisted records are unchanged. The change is unconditional: the hard-mode flag does not gate these records.

Crucially, the original author's [item notes](../docs/author_notes/items.md) explicitly restrict battle use of Antidote, Burn Heal, Ice Heal, Awakening, Parlyz Heal, Full Restore, Max Potion, Hyper Potion, Full Heal, Revive, Max Revive, Energy Root, Revival Herb, Elixir, Max Elixir, Lava Cookie and Old Gateau. Those restrictions agree with the Chinese binary's zero battle-pocket bits. Not every affected item's note states the restriction, but enough do to establish deliberate balance design. Calling the whole set broken healing items would erase that evidence. Adoption would change the hack's intended battle resource economy and requires a gameplay decision, especially alongside hard mode.

## “Two-turn moves”: the actual live-data difference is Bounce

Among all 921 records in `extra/new_move_data.narc`, only move340, Bounce, changes. Its 40-byte record changes the flags word at offset32:

```
Chinese / NoBigText: 0x00021449
Speedoption:        0x0982144B
Added bits:         0x09800002 = bits 1, 23, 24, 27
```

The upper half of the eight-byte flags area is unchanged. The resulting flags equal Fly's (`move19`) flags. Bounce's power80, accuracy100, PP10, physical category, Flying type, effect263 and 30% secondary-effect chance remain unchanged. There is no corresponding new live-record edit to Fly, Dig, Dive, Sky Attack, Skull Bash or Razor Wind. Therefore this is not evidence of a general two-turn battle-engine repair.

The actual move-attribute reader is ARM9 `0201A274`, which reads the expanded archive. Its dispatch exposes flag bit0 as attribute29 and bit1 as attribute30. The bit1 extraction is at `0201A42A`; veneer `0201A780` requests attribute30 (`0x1E`). Battle code at overlay14 `0221DE74` calls this veneer and takes the additional path through `022230E4` when set. This links the changed bit to existing charge handling, rather than interpreting a flag merely from a retail structure. That battle routine itself is unchanged. Bits23,24,27 are exposed as attributes52,53,56; call sites include `0223DC1A`, `0223F55C`, `02244A0E`. Their complete semantic names and effects have not been independently established, so the patch should not be simplified to “only turns charging back on”: it copies four flags.

The author's move sheet explicitly calls Bounce a one-turn move. Existing project [sheet-to-ROM verification](sheet_mismatch_verification.md#43-moves-5-a--1-b) established that its cleared charge bit agrees with that sheet; the two-turn description is stale. Other deliberately converted one-turn moves also clear that bit. Accordingly, Speedoption restores charge-related flags contrary to the documented original design. Whether all four flags together produce correct animation, invulnerability and interruption behavior needs runtime tests; no such tests were obtained in this audit.

## Additional change: remove HM classification for replacement guards

Speedoption overwrites the entry of ARM9 function `020766EC` with `00 20 70 47` (`movs r0,#0; bx lr`). The Chinese/NoBigText function instead scans eight move IDs and returns1 on a match, otherwise0. The table contains Cut15, Fly19, Surf57, Strength70, Whirlpool250, Rock Smash249, Waterfall127 and Rock Climb431.

The concrete effect is that every caller now sees “not an HM.” Direct Thumb-call references include ARM9 `020884AA`, `0208857A`, and bag overlay17 `021FABD0`. For example, `020884AA` checks the chosen old move, compares the result with1, and enters the refusal path only on a match; the stub makes that branch unreachable. This removes HM-specific replacement restrictions in these menu paths. It does not delete the moves, change their battle effects, remove field scripts or prove that every possible teaching interface uses this predicate. The function identity is consistent with the retail [MoveIsHM implementation](https://raw.githubusercontent.com/pret/pokeheartgold/master/src/item.c), but the claim here rests on the actual table and callers in this hack.

This is a convenience/gameplay change not separately explained by the opening-post healing/two-turn claims. It is independent of hard mode and speed settings. Review it separately before adoption.

## Validation and adoption boundary

Archive-level comparison checks every member and every byte, rather than searching only known IDs. Disassembly checks the live expanded move-data consumer and HM callers. No in-game item use, two-turn battle or HM-teaching test was completed. Reproduction should cover each item category, Full Restore with both HP/status damage, Ether/Elixir menu placement, all four added Bounce flags, and forgetting each HM through the affected interfaces. These findings do not authorize changing original-hack behavior under D-1002/D-1337; they identify decisions and tests needed if the user chooses an optional gameplay fork.
