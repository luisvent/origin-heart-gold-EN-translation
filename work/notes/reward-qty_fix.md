# reward-qty: reward scripts say how many (finding D-2409, fix D-2411)

2026-10-12. Branch `fix/reward-qty`, fix `work/patches/reward-qty/` (kind narc, `enabled = false`, user decision D-2387).

## The bug (reproduced)

Standard reward script 2033 (script file `a/0/1/2` member 3, entry 34, pc 1985) gives `GiveItem(item = var 0x8004, qty = var 0x8005)`
and then calls the shared block at pc 2063, which buffers the item name (slot 0) and shows a027/0038#25 `Obtained the {item}!`
(zh 得到了X！) for every pocket except 7 (key items: pc 2046, #28, coloured name, no quantity in the US game either).
Standard script 2008 (entry 9, pc 1922) has the same two CallIf sites and the same shared block, so it has the same flaw.
Nothing reads var 0x8005 for the message. The Bag gets the right quantity; only the text hides it.

US HeartGold, member 3, entry at pc 2133 (the same routine): after `GiveItem` and the pocket test, pc 2211 is
`CompareVarToValue 0x8005, 1; GoToIf GT -> pc 2235`; at pc 2235 it runs command 844 (`BufferItemNamePlural 0, 0x8004`),
otherwise `BufferItemName 0, 0x8004`, then `NPCMsg 25`: the same text 'Obtained the {VAR:0108:0}!', with the plural name in
the buffer. The pocket message that follows does the same (pc 2260, slot 1). The hack's script command table ends at
command 842 (the arm9 table at 0x020F793C has no entry 844), so the plural command does not exist here.

Reproduction (`work/tools/emu_reward_qty.py`, DeSmuME, standing in the Academy (zone 159, message bank 552, script file
859) and running the teacher's real reward bytes, file 859 @976-1037, as a one-off script):

| ROM | messages shown | Bag |
|---|---|---|
| untouched Chinese ROM | 38, 25, 88, 25, 88, 25, 88, 51 (screenshot: 得到了高级球！) | Ultra Ball +2 |
| standard English build (rom sha1 b3779e0c, = expected.toml) | the same ids, 'Obtained the Ultra Ball!' | Ultra Ball +2 |
| standard build + reward-qty | 38, **66**, 88, 25, 88, 25, 88, 51 ('Obtained Ultra Ball x2!') | Ultra Ball +2 |

Other cases (all four runs in the table in the section Verification): 5 Potions through CallStd 2033 and 2008, 1 Potion,
5 x TM28, a key item (Rule Book), and the academy reward with 999 Ultra Balls already in the Bag.

## What the fix does

Two edits in member 3 (`fix.toml`): the 8 bytes `BufferItemName 0, 0x8004; NPCMsg 25` at pc 2063 become four Noops, and a
35-byte block is inserted in front of the old `GoTo` at pc 2071 (the member grows by 36 bytes, 1 of them padding for the
movement blocks):

```
BufferItemName 0, 0x8004
CompareVarToValue 0x8005, 1
GoToIf GT -> L2
NPCMsg 25                  ; qty 1: the old message, unchanged
GoTo -> end of block
L2: BufferInt 1, 0x8005    ; qty > 1
    NPCMsg 66              ; 'Obtained {VAR:0108:0}{NEWLINE}x{VAR:0133:1}!'
```

Why this layout: the insert tool can only jump inside its own block, and a message id is an immediate, so the old
BufferItemName/NPCMsg pair cannot be made conditional in place. Both paths fall through into the old `GoTo` (to the
fanfare and pocket message), so everything after the quantity message is as before. Both std scripts reach pc 2063
by `CallIf`, so one change fixes 2033 and 2008. `work/tools/test_reward_qty.py` checks this with a small interpreter over the
disassembly (key item and one-item gifts have identical traces, quantities 2/5/10 show #66 with BufferInt slot 1).

Message #66 is the existing line (a027/0038, so far unused); the only text change is the added "the" (user choice 2026-10-13, D-1496), so it matches #25: `Obtained the {VAR:0108:0}{NEWLINE}x{VAR:0133:1}!` for
zh `{VAR:0108:0}　{VAR:0133:1}{NEWLINE}入手！`. {VAR:0108:0} is the item name (slot 0), {VAR:0133:1} the number buffered by
`BufferInt` into slot 1; the screenshot (taken before the wording change) shows 'Obtained Ultra Ball / x2!'; the shipped text now reads 'Obtained the Ultra Ball / x2!'. The fix adds no new bank string, but the edited #66 moved the default build's text hash (expected.toml re-recorded).

Not changed: the pocket message (`#88`, 'put the Ultra Ball in the POKé BALLS Pocket'; the US game uses the plural name there
too, the hack has no plural command), the bag-full behaviour (the std scripts never check space; the callers do, or do not:
the Academy reward does not, so with 999 Ultra Balls it still says 'Obtained ... x2' and the Bag stays at 999, the same on the
Chinese ROM; that is a separate caller issue), the fanfare, any caller.

## Callers

825 `CallStd 2033/2008` sites in all script files, of which 163 have a constant quantity above 1 (161 via 2033, 2 via 2008),
in 64 script files, quantities 2 to 20. 652 give 1; 10 have a quantity the static scan cannot resolve (files 29, 30,
144, 217, 250, 754, 871 via 2033; 901 x3 via 2008). Three of the 163 give TMs (items 355 TM28 in file 761, 366 TM39 in
file 750, 381 TM54 in file 115, each x5) and go through the same general message, so they are fixed too. Table (script
file, pc of the CallStd, item, quantity):

| file | pc | std | item | qty |
|---|---|---|---|---|
| 32 | 2520 | 2033 | 41 Max Elixir | 3 |
| 32 | 2536 | 2033 | 93 Heart Scale | 2 |
| 56 | 2789 | 2033 | 53 PP Max | 2 |
| 58 | 2786 | 2033 | 42 Lava Cookie | 3 |
| 58 | 2802 | 2033 | 54 Old Gateau | 3 |
| 60 | 3267 | 2033 | 492 Fast Ball | 5 |
| 60 | 3283 | 2033 | 493 Level Ball | 5 |
| 60 | 3299 | 2033 | 494 Lure Ball | 5 |
| 60 | 3315 | 2033 | 495 Heavy Ball | 5 |
| 60 | 3331 | 2033 | 496 Love Ball | 5 |
| 60 | 3347 | 2033 | 497 Friend Ball | 5 |
| 60 | 3363 | 2033 | 498 Moon Ball | 5 |
| 60 | 3469 | 2033 | 503 Tidal Bell | 5 |
| 61 | 4187 | 2033 | 53 PP Max | 3 |
| 82 | 1945 | 2033 | 89 Big Pearl | 2 |
| 92 | 3053 | 2033 | 94 Honey | 3 |
| 92 | 3113 | 2033 | 94 Honey | 5 |
| 92 | 3173 | 2033 | 94 Honey | 10 |
| 92 | 4182 | 2033 | 5 Safari Ball | 10 |
| 92 | 5437 | 2033 | 34 EnergyPowder | 3 |
| 92 | 5471 | 2033 | 34 EnergyPowder | 3 |
| 92 | 6443 | 2033 | 94 Honey | 3 |
| 115 | 1510 | 2033 | 381 TM54 | 5 |
| 115 | 2772 | 2033 | 94 Honey | 2 |
| 173 | 314 | 2033 | 152 Rawst Berry | 2 |
| 175 | 2736 | 2033 | 13 Dusk Ball | 3 |
| 175 | 2796 | 2033 | 13 Dusk Ball | 5 |
| 175 | 2856 | 2033 | 13 Dusk Ball | 10 |
| 190 | 3513 | 2033 | 209 Micle Berry | 3 |
| 190 | 3573 | 2033 | 210 Custap Berry | 7 |
| 197 | 1201 | 2033 | 154 Leppa Berry | 2 |
| 197 | 1718 | 2033 | 150 Chesto Berry | 2 |
| 197 | 2203 | 2033 | 154 Leppa Berry | 2 |
| 197 | 3045 | 2033 | 53 PP Max | 3 |
| 197 | 3361 | 2033 | 154 Leppa Berry | 2 |
| 199 | 1756 | 2033 | 155 Oran Berry | 2 |
| 199 | 1772 | 2033 | 158 Sitrus Berry | 2 |
| 199 | 1788 | 2033 | 212 Rowap Berry | 2 |
| 200 | 441 | 2033 | 89 Big Pearl | 3 |
| 200 | 504 | 2033 | 89 Big Pearl | 9 |
| 202 | 2561 | 2033 | 50 Rare Candy | 2 |
| 202 | 3334 | 2033 | 50 Rare Candy | 2 |
| 203 | 3862 | 2033 | 14 Heal Ball | 2 |
| 205 | 81 | 2033 | 15 Quick Ball | 10 |
| 216 | 4718 | 2033 | 50 Rare Candy | 4 |
| 216 | 8822 | 2033 | 50 Rare Candy | 2 |
| 219 | 937 | 2033 | 111 Weak. Policy | 5 |
| 219 | 997 | 2033 | 111 Weak. Policy | 10 |
| 219 | 1057 | 2033 | 111 Weak. Policy | 20 |
| 219 | 1177 | 2033 | 275 Focus Sash | 5 |
| 219 | 1237 | 2033 | 275 Focus Sash | 10 |
| 219 | 1297 | 2033 | 275 Focus Sash | 20 |
| 225 | 3836 | 2033 | 492 Fast Ball | 2 |
| 225 | 3852 | 2033 | 493 Level Ball | 2 |
| 225 | 3868 | 2033 | 494 Lure Ball | 2 |
| 225 | 3884 | 2033 | 495 Heavy Ball | 2 |
| 225 | 3900 | 2033 | 496 Love Ball | 2 |
| 225 | 3916 | 2033 | 497 Friend Ball | 2 |
| 225 | 3932 | 2033 | 498 Moon Ball | 2 |
| 236 | 6825 | 2033 | 7 Dive Ball | 5 |
| 240 | 3297 | 2033 | 143 Heart Mail | 3 |
| 240 | 4164 | 2033 | 157 Lum Berry | 2 |
| 243 | 1896 | 2033 | 94 Honey | 3 |
| 243 | 1954 | 2033 | 94 Honey | 5 |
| 243 | 2012 | 2033 | 94 Honey | 10 |
| 244 | 1259 | 2033 | 14 Heal Ball | 3 |
| 244 | 1275 | 2033 | 16 Cherish Ball | 3 |
| 247 | 1070 | 2033 | 50 Rare Candy | 2 |
| 247 | 1086 | 2033 | 42 Lava Cookie | 2 |
| 249 | 2966 | 2033 | 33 Moomoo Milk | 3 |
| 249 | 3024 | 2033 | 33 Moomoo Milk | 8 |
| 249 | 3082 | 2033 | 33 Moomoo Milk | 12 |
| 252 | 473 | 2033 | 494 Lure Ball | 3 |
| 254 | 1211 | 2033 | 157 Lum Berry | 2 |
| 734 | 291 | 2033 | 93 Heart Scale | 2 |
| 738 | 4384 | 2033 | 4 Poké Ball | 5 |
| 742 | 268 | 2033 | 22 Parlyz Heal | 2 |
| 748 | 736 | 2033 | 158 Sitrus Berry | 2 |
| 748 | 1631 | 2033 | 497 Friend Ball | 2 |
| 748 | 4213 | 2033 | 238 Hard Stone | 2 |
| 750 | 633 | 2033 | 366 TM39 | 5 |
| 756 | 1592 | 2033 | 149 Cheri Berry | 2 |
| 761 | 943 | 2033 | 355 TM28 | 5 |
| 771 | 1373 | 2033 | 224 Cleanse Tag | 10 |
| 774 | 2379 | 2033 | 149 Cheri Berry | 2 |
| 774 | 7785 | 2033 | 87 Big Mushroom | 2 |
| 781 | 223 | 2033 | 44 Sacred Ash | 3 |
| 782 | 7309 | 2033 | 33 Moomoo Milk | 2 |
| 782 | 7325 | 2033 | 158 Sitrus Berry | 2 |
| 783 | 333 | 2033 | 110 Eviolite | 5 |
| 792 | 2819 | 2033 | 2 Ultra Ball | 10 |
| 792 | 2835 | 2033 | 3 Great Ball | 10 |
| 792 | 3138 | 2033 | 63 Poké Doll | 2 |
| 792 | 3154 | 2033 | 64 Fluffy Tail | 2 |
| 794 | 965 | 2033 | 50 Rare Candy | 2 |
| 794 | 1009 | 2033 | 42 Lava Cookie | 2 |
| 794 | 1025 | 2033 | 54 Old Gateau | 2 |
| 795 | 273 | 2033 | 50 Rare Candy | 3 |
| 795 | 2577 | 2033 | 50 Rare Candy | 10 |
| 803 | 562 | 2033 | 158 Sitrus Berry | 10 |
| 803 | 654 | 2033 | 158 Sitrus Berry | 10 |
| 803 | 899 | 2033 | 158 Sitrus Berry | 5 |
| 803 | 962 | 2033 | 158 Sitrus Berry | 5 |
| 803 | 1025 | 2033 | 158 Sitrus Berry | 5 |
| 803 | 1088 | 2033 | 158 Sitrus Berry | 5 |
| 803 | 1151 | 2033 | 158 Sitrus Berry | 5 |
| 804 | 2669 | 2033 | 5 Safari Ball | 5 |
| 804 | 2729 | 2033 | 5 Safari Ball | 10 |
| 812 | 1661 | 2033 | 221 King’s Rock | 5 |
| 840 | 2912 | 2033 | 50 Rare Candy | 5 |
| 840 | 2928 | 2033 | 53 PP Max | 5 |
| 840 | 3023 | 2008 | 17 Potion | 5 |
| 840 | 3374 | 2033 | 53 PP Max | 2 |
| 840 | 3574 | 2008 | 17 Potion | 5 |
| 842 | 9368 | 2033 | 33 Moomoo Milk | 3 |
| 847 | 6561 | 2033 | 14 Heal Ball | 5 |
| 847 | 6854 | 2033 | 51 PP Up | 6 |
| 847 | 7110 | 2033 | 4 Poké Ball | 10 |
| 853 | 1560 | 2033 | 157 Lum Berry | 2 |
| 853 | 1576 | 2033 | 33 Moomoo Milk | 5 |
| 854 | 596 | 2033 | 147 Mosaic Mail | 2 |
| 854 | 612 | 2033 | 148 Brick Mail | 2 |
| 859 | 995 | 2033 | 2 Ultra Ball | 2 |
| 872 | 2507 | 2033 | 33 Moomoo Milk | 3 |
| 872 | 2523 | 2033 | 27 Full Heal | 2 |
| 872 | 3132 | 2033 | 6 Net Ball | 3 |
| 872 | 3148 | 2033 | 7 Dive Ball | 3 |
| 872 | 3164 | 2033 | 11 Luxury Ball | 2 |
| 872 | 3975 | 2033 | 50 Rare Candy | 3 |
| 872 | 3991 | 2033 | 53 PP Max | 3 |
| 872 | 4007 | 2033 | 93 Heart Scale | 2 |
| 883 | 164 | 2033 | 252 Air Balloon | 10 |
| 896 | 1481 | 2033 | 252 Air Balloon | 3 |
| 896 | 1539 | 2033 | 252 Air Balloon | 5 |
| 896 | 1597 | 2033 | 252 Air Balloon | 10 |
| 901 | 2401 | 2033 | 36 Heal Powder | 3 |
| 901 | 2459 | 2033 | 36 Heal Powder | 5 |
| 901 | 2517 | 2033 | 36 Heal Powder | 10 |
| 907 | 3047 | 2033 | 24 Max Potion | 2 |
| 907 | 3063 | 2033 | 29 Max Revive | 2 |
| 907 | 3079 | 2033 | 91 Star Piece | 2 |
| 907 | 3407 | 2033 | 111 Weak. Policy | 5 |
| 907 | 3467 | 2033 | 111 Weak. Policy | 10 |
| 907 | 3527 | 2033 | 111 Weak. Policy | 20 |
| 907 | 3943 | 2033 | 158 Sitrus Berry | 3 |
| 907 | 4003 | 2033 | 158 Sitrus Berry | 5 |
| 907 | 4063 | 2033 | 158 Sitrus Berry | 10 |
| 907 | 4535 | 2033 | 154 Leppa Berry | 3 |
| 907 | 4595 | 2033 | 154 Leppa Berry | 5 |
| 907 | 4655 | 2033 | 154 Leppa Berry | 10 |
| 915 | 1758 | 2033 | 157 Lum Berry | 2 |
| 916 | 3802 | 2033 | 149 Cheri Berry | 3 |
| 916 | 4005 | 2033 | 152 Rawst Berry | 3 |
| 916 | 5554 | 2033 | 149 Cheri Berry | 3 |
| 916 | 5760 | 2033 | 152 Rawst Berry | 3 |
| 916 | 6921 | 2033 | 292 Power Band | 2 |
| 919 | 1093 | 2033 | 31 Soda Pop | 12 |
| 931 | 414 | 2033 | 182 Durin Berry | 15 |
| 937 | 3530 | 2033 | 53 PP Max | 5 |
| 937 | 4499 | 2033 | 29 Max Revive | 3 |
| 937 | 4695 | 2033 | 34 EnergyPowder | 3 |
| 945 | 1431 | 2033 | 37 Revival Herb | 3 |
| 958 | 2540 | 2033 | 495 Heavy Ball | 2 |

(Item names: a027/0219. Direct `GiveItem` commands with their own messages are not affected and not listed.)

## Verification

Static: `.venv/bin/python -m unittest work.tools.test_reward_qty` (10 tests), `fixes.py check`, `test_fixes`, `test_emu_fixes`
(145 tests OK), `qa.py check a027/0038` (0 errors, text untouched).

Emulator (`emu_reward_qty.py`, DeSmuME, one process per case; builds: `build.py` default = the standard build, rom sha1
b3779e0c = expected.toml, and the same build with `--only <all enabled fixes>,reward-qty`, rom sha1 d9e509c7; the Chinese ROM
for the first row). Messages are NPCMsg ids in order; 'BufferInt' is the script operand (slot 1, var 0x8005 = 32773):

| case | Chinese ROM / standard build | with reward-qty |
|---|---|---|
| academy (2 Ultra Balls, 493, 494) | 38, 25, 88, 25, 88, 25, 88, 51; Bag +2 +1 +1 | 38, **66**, 88, 25, 88, 25, 88, 51; BufferInt; Bag +2 +1 +1 |
| qty5: 5 Potions, std 2033 | 25, 88; Bag +5 | **66**, 88; BufferInt; Bag +5 |
| std2008: 5 Potions | 25, 30; Bag +5 | **66**, 30; BufferInt; Bag +5 |
| tm5: 5 x TM28 | 25, 88; Bag +5 | **66**, 88; BufferInt; Bag +5 |
| qty1: 1 Potion | 25, 88; Bag +1 | 25, 88; no BufferInt; Bag +1 (unchanged) |
| key: Rule Book (key item) | 28, 88 | 28, 88; no BufferInt (unchanged) |
| fullbag: academy with 999 Ultra Balls | 38, 25, 88, ... ; Ultra Ball +0, 493 +1, 494 +1 | 38, 66, 88, ...; same Bag (the Bag result is the same, the message of the full case is caller behaviour) |

All 7 cases PASS on the build with the fix and on the control. The Chinese ROM academy case (zh message 得到了高级球！ for two
balls) reproduced the finding on the untouched hack (`work/build/rq/emu_cn`, local). Screenshot of the fixed academy case:
'Obtained Ultra Ball / x2!', then 'Shishio put the Ultra Ball in the POKé BALLS Pocket.'

## Open questions

- Wording: 'Obtained Ultra Ball x2!' (the unused #66 as it stands, from the v3 draft) against the US's 'Obtained the Ultra Balls!'
  (needs a plural-name command the hack lacks). #25 has 'the', #66 has not. Kept #66 unchanged; changing it would be a
  text change for the user (D-1496 is about corrections, this is new wording).
- Pocket message (#88) still names one item for a quantity above 1.
- TMs and key items: no change for key items (as in the US).
