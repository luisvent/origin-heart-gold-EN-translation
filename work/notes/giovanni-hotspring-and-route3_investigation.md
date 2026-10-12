# Giovanni hot-spring loss and Route 3 Misty actors: investigation, 2026-10-12

Two issues from the Spanish-patch comparison (work/notes/es_patch_comparison_20261012.md, section 4). Both derived
from the untouched Chinese ROM (sha256 4807ab2c...95c8) and checked on it and on rc7
(sha256 b16f81be...10df). The Spanish ROM was not used as evidence. Emulator: py-desmume through
work/tools/emu_harness.py (`E.start_at`, `h.warp`, hooks), one run at a time. Runners and screenshots live in the
session scratchpad (`scratchpad/inv/giovanni-hotspring-and-route3/`: gio.py, gio_win.py, r3.py, montage.py), not in git.

## 1. Giovanni at the Mt. Silver hot spring: REPRODUCED (forced loss, natural scene)

Static (scriptdump.py 844): zone 65 (Mt. Silver), script file a/0/1/2 member 844, script 3. Coordinate event at
23,139 (var 0x40A2 = 8): Lance and Lorelei arrive, "Giovanni, we meet again.", "You wish to know? Then ask with your
strength!", then at offset 801 `TrainerBattle 701,701,0,0` (a double battle, loss not allowed), 809 CheckBattleWon,
813 CompareVarToValue 0, 819 `GoToIf = -> L1890`. L1890 is the hot spring's generic soak block ("The warm spring
water washes over you", heal, "After the hot spring, <name> rested on Mt. Silver for a while longer", warp to map 384,
var 0x4110 = 5), also used by the hot spring's stage 4 (offset 1783). The win path continues at 826 (Lance's call,
the President, the Silver Conference staff, var 0x40A2 = 9). The member has no WhiteOut.

Is it a must-win battle? The trainer battle has the "no loss" option (third byte 0) like every other must-win; the
story after a win is Giovanni's escape and the Conference scene. The loss branch is a shortcut that reuses the soak
block; it skips the escape scene, leaves Lance, Lorelei and Giovanni on the map and keeps var 0x40A2 = 8.

Emulator (map 65, Magikarp Lv 5 with Splash, party of 2 so no forced switches, clock 2026-10-09 noon):
natural setup = warp to 24,139 with var 0x40A2 = 8 and flag 2266 clear / 1366 set (the scene's own entry state; this
state was forced, the earlier story was not played), then walk LEFT onto the trigger. The scene plays (messages 14-36),
the double battle starts, both Magikarp faint.

| ROM | result |
|---|---|
| Chinese ROM | CheckBattleWon result 2 / won 0, GoToIf 819 -> 1890 taken, then no message opens (NPCMsg [0] of L1890 never runs) and the screen is garbage / black, field False, PC in garbage (0x5000010, 0x7f000008) |
| rc7 | same, black screen |
| Chinese ROM, battle bytes at 807/808 patched in RAM to 1,0 and to 1,1 (loss allowed) | same blank screen: the hot-spring branch cannot run with any value of the option bytes tried |
| Chinese ROM, RAM patch of 819 into WhiteOut/ReleaseAll/End | native whiteout: messages 43-45 (Pokemon Center), field True on map 501, party healed, control returns |

So the Chinese loss branch never works; "heal text then continue" is not what the game does, it is a freeze. Whether
the author wanted the soak as a story shortcut cannot be proven, and no setting makes it run, so the fix uses the
same native whiteout every other loss branch of the hack uses (rock-tunnel-corner-loss, magcargo-loss-whiteout).
Fix branch fix/giovanni-hotspring-loss (see its notes).

## 2. Route 3 Misty/Gyarados scene prefix: REPRODUCED under forced state, cosmetic

Flag 1303 is the hide flag of Route 3 objects 8, 9 and 28 (Misty, her second object, the Gyarados). Script 17
(member 175 offset 1171, trigger x 1149 z 119-123 with var 0x4086 = 0) ApplyMovement/NPCMsg/HidePerson them but never
ShowPerson. Writers of 1303: members 212, 738, 739 (first-hour scenes on Route 22 / Pallet / Viridian set it, with
flags 410/411/1057/1244/1355/1356/1371), member 175 (end of the scene, both answers), member 115 offset 5497 clears it
together with `SetVar 0x4086 = 0` (Misty's Viridian Forest scene: "picked up the Poke Ball", Misty gives TM and her
number). So 1303 is set and var 0x4086 is 0 from the first-hour scenes until the forest scene.

The forest scene starts when you talk to Misty (member 115 script 1, object 9 at 51,66; objects 9/10 in a
corridor?). Checked with the harness's grid on map 147: the shortest south-to-north path is 159 steps with or without
the tiles of Misty and her partner blocked, i.e. the corridor is not blocked by them, so talking to Misty is optional.
A player who walks past her reaches Route 3 with flag 1303 set and var 0x4086 = 0: not played end to end, but each
step is a script fact.

Emulator (forced state: flag 1303 set, var 0x4086 = 0, warp to 1147,121, walk RIGHT; party of one Magikarp Splash):
| ROM, flag | what is on screen |
|---|---|
| CN, 1303 clear (control) | Misty and the Gyarados stand on the map, the talk looks as intended |
| CN, 1303 set | no Misty and no Gyarados on the map; the cries, "Stop, Gyarados!", the battle and the whole "Misty: I'm so sorry" talk happen with an empty field; the scene still ends (var 0x4086 = 1, 1303 set) |
| rc7, 1303 set / clear | same as CN |

Fix branch fix/route3-misty-actors (prefix: if 1303 is set, clear it and ShowPerson 28, 9, 8).

## Not verified

* Natural reachability of the Route 3 state by a full play-through (forest skipped); only the path argument above.
* Giovanni: the hot spring's authorial intent (shortcut vs unfinished); the double battle's win path was checked only
  with a RAM-forced result (battle code replaced by SetVar 0x800C = 1), not by winning the Lv 100 battle.
* Hardware: the black screens were seen in DeSmuME only (the engine reads a bad address; melonDS was not run).
