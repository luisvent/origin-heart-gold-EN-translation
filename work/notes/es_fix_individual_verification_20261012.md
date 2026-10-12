# Individual emulator verification of the four disabled hack-bug fixes (2026-10-12)

Method: py-desmume (DeSmuME), one bug at a time, control `rc7.nds` against rc7 + only that fix. No `check.py --emu`, no sweep. English builds; ROMs in the session scratchpad `testers/` (git-ignored, not in the repo). Chinese ROM hash checked: 4807ab2c...95c8. Evidence root: `<scratchpad>/verify/<bug>/` (`ribbon`, `petilil`, `mail`, `name`; driver scripts in `verify/tools_v/`). Harness: old guide0813 recipe (git 2e6fe55^, op-trace hook on RunScriptContext) for the ribbon, mail and name cases; current `emu_harness` for Petilil.

## 1. sibling-ribbon-freeze: VERIFIED
All seven siblings (members 225, 232, 243, 246, 934, 937, 958 = Tuscany, Frieda, Arthur, Sunny, Wesley, Santos, Monica), real talk on their weekday, var 0x4094 = 7, lead without ribbons.
- rc7: GiveRibbon runs, then bad opcode 2009 at offsets 3985/12121/2334/764/5653/2784/1078, message window still open (shot: `ribbon/run1/rc7/guide08_13/en/ribbon_tuscany_after.png`, "Pikachu put on the Shock Ribbon!" still up). Player still walks, X menu opens, SAVE prompt appears.
- patched: no bad opcode, trace ends `... CloseMsg, ReleaseAll, End`, window closed, walks, X menu opens, SAVE prompt (`ribbon/run1/patched/guide08_13/en/ribbon_tuscany_after.png`). Same for all seven (`ribbon/run1/*_rc7.log`, `*_patched.log`).

## 2. petilil-hisuian-lilligant: VERIFIED
Petilil Lv10, FOUR moves (Tackle, Growl, Absorb, Sweet Scent), Rare Candy, 160 A presses (move-forget prompts answered by A), `petilil/run1/`.
- Day 12:00, Black Belt: rc7 -> species 548 form 1, ability 20, Black Belt consumed, Lv11. patched -> 549 form 1, ability 55 (Hustle), Black Belt consumed, Lv11, learned move 837 (replacing Tackle). Summary screen: patched "Lilligant", Grass/Fighting, dex 0535 (`patched_day_bb/petilil_day_bb_summary.png`); rc7 "Petilil", Grass (`rc7_day_bb/...summary.png`).
- Night 00:00, Black Belt: both ROMs: no evolution, 548 form 0, Lv11, Black Belt kept (control OK).
- Sun Stone (12:00, no belt): both ROMs: 549 form 0 (normal Lilligant), identical (control OK).

## 3. romance-mail-mismatch: VERIFIED
Fixture: Mail pocket 137/139/143/144 x3 each, var 0x40B5 = 7 (842) or 6 (843), badge 1, flag 106 clear, flags 2141/2142/2143 SET and 2144 CLEAR (the partner flags are inverted: the scripts pick a partner whose flag is clear; with the other three clear Yellow's branch (HasItem 143) runs; see `mail/run2`). Not the "2144 set" fixture the task assumed.
- (a) 842 "I'm busy" (real talk to Cynthia, obj 8 script 15): rc7 msgs [217, 212]; patched [217, 218].
- (b) 842 rest option: rc7 TakeItem 139, bag 139 3->2, 144 untouched; patched TakeItem 144, 144 3->2, 139 untouched.
- (c) 843 love letter (run_script file 843 index 0): rc7 TakeItem 143, 143 3->2, 144 untouched; patched TakeItem 144, 144 3->2, 143 untouched.
Evidence: `mail/run3/*.log` (RESULT lines), `mail/run3/rc7_busy/mail_busy_menu00.png`. Messages were identified by the op trace (NPCMsg ids), not by screenshot of the line.

## 4. blank-player-name: VERIFIED (with caveats)
`name/run1/`, contact sheet `name/run1/page1_sheet.png`: first page, rc7 vs patched.
- 733 Pallet photographer: REAL walk-up (warp beside him, A). rc7 ", choosing the hard road ..."; patched "Shishio, choosing ...".
- 111 Clair: rc7 "Oh, , did you come..."; patched "Oh, Shishio, ...". (run_script; Clair not live at that moment.)
- 171 Brock, zone 417, positions (5,6), (4,5), (5,4), run_script: rc7 "So this is where you were, ." ; patched "... Shishio." In all three branches (and the (5,9) default) the end-of-scene frame is pixel-identical to rc7's and the player position is the same before/after; messages the same ([26,27,28], branch 5,4 adds a 0 entry on both).
- Caveat: only 733 was a real walk-up; Brock's scene is a map trigger (no talk object) and Clair was not live, so those used run_script (position set by warp).
