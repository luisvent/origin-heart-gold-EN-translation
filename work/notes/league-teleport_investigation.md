# League teleport Abra drawn as Simisage (D-2281): investigation 2026-10-12

Verdict: REPRODUCED (under forced state: flag 223 cleared) on the untouched Chinese ROM and the released rc7. Not fixed here: the
branch fix/overworld-pokemon-sprite-mismatch (~/Developer/poke-fix-overworld-pokemon-sprite-mismatch, unmerged) already changes this exact object
(Pokemon League Entrance, zone 300, events member 271, object 3, sprite 1012 Simisage -> 492 Abra, id at m271@0x6A). Resolve D-2281 when that branch merges.

## Static
a/0/3/2 member 271 (Chinese ROM, sha256 4807ab2c...95c8): object 1 = sprite 330 at (9,14) script 3 (the man, a027/0514#1); object 3 = sprite 1012
at (8,14) script 4 (a027/0514#2 "凯西『A——bra!"). 1012 is the Gen 5 range sprite (Simisage), the same table bug as the Pewter Jigglypuff report.

## Emulator (py-desmume, each ROM run singly)
Harness: emu_harness.py drive --map 300 --x 10 --y 16 flag:223=0 warp:300,8,15,0 w200 UP/30 A/30 ... with save work/build/memcheck/full_bag_6mons.sav.
Without flag:223=0 the hall NPCs (appearance flag 223) are hidden in this save, so the reproduction is under forced state; the natural flag state
was not established. Screens: /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/league-teleport/h_cn/drive/{a,b,c}_cn.png, /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/league-teleport/h_en/drive/*_en.png, pairs pair_{a,b,c}.png. Chinese ROM and rc7 both show a green Simisage
beside the man, text box "凯西『A——bra!" / "Abra: A-bra!". English text is a correct translation; the sprite is the hack's.

## Not verified
Natural visibility (flag 223); the fixed build in this room (the branch's own emulator checks covered Pewter and Lighthouse only; this row is covered by its data test).
