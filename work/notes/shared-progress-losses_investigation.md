# Shared-progress losses (queue rank 10, D-1578..D-1581): emulator investigation, 2026-10-12

Authorization: D-2300 (scoped the four problems), D-1337 no longer blocks fixes (user, 2026-10-12), D-1002 and D-1500 still
apply. Earlier work, not redone: work/notes/issue10_shared_progress_{investigation,reproduction,fix}_20261009.md (offline
native-script execution; no emulator then) and the disabled fixes `expedition-completed-progress`,
`hooh-panel-silver-marker`, `mortar-invalid-flag-noop` (D-2321 took the first two out of RC7 because their consequences
"may be intentional"; the user has not re-enabled them).

Method: py-desmume through work/tools/emu_harness.py (`E.start_at`, `h.warp`, `h.run_script`, `h.get_flag/get_var`),
one scenario per process, seed save work/build/memcheck/full_bag_6mons.sav with flags/vars forced as labelled, clock
2026-10-09 noon. ROMs: untouched Chinese ROM (sha256 4807ab2c...95c8), rc7 (b16f81be...10df), rc7 plus the fix under test
(built by narcpatch from rc7, `--only`-style). Runners, logs and screenshots are in the session scratchpad
`scratchpad/inv/shared-progress-losses/` (leader.py, tower.py, hooh.py, forest.py, deoxys.py, mkpuzzle.py, mkforce.py,
montage.py; folders `*-cn-*`, `*-rc7-*`, `*-fix-*`, montages `m-*.png`), not in git.

## Verdicts

| Finding | Verdict | What |
|---|---|---|
| D-1579 expedition leader erases the Burned Tower beasts | REPRODUCED (state 11 forced; the rest natural) | fix exists, disabled (D-2321) |
| D-1580 Ho-Oh panel clears Silver's dream marker | REPRODUCED (puzzle result forced; flags natural) | fix exists, disabled (D-2321) |
| D-1581 bug hunt / Forest of Time | REPRODUCED, permanent loss shown (hunt state forced) | new fix `forest-of-time-sammy-guard` (disabled) |
| D-1578 Deoxys loss kills the Lucky Meowth God chain | REPRODUCED; JUDGMENT NEEDED (no fix) | question recorded |

## D-1579 (leader at Mt. Mortar, var 0x409F)

State 11 is Lance's post-game home visit (file 842 @2223). Zone 250, event 236 object 4 (51,81), script 2 of file 962.
Player placed at (51,80) facing down (forced: 0x409F = 11, flag 461 clear), A, A on "Yes", Lv100 Mewtwo wins:

| ROM | 0x409F before -> after | what the player sees |
|---|---|---|
| Chinese | 11 -> 3 (frame ~57) | "Are you a really strong Trainer?", battle, win (leader-cn-11c, m-leader-cn-11c.png) |
| rc7 | 11 -> 3 | same (leader-rc7-11) |
| rc7 + expedition-completed-progress | stays 11 | "Whether you're the League Champion or not, you're our expedition partner!", no battle (leader-fix-11, m-leader-fix-11.png) |

Consequence on the Chinese ROM (tower.py, Burned Tower zone 7, step from (12,20) up to the trigger (12,18)): with 0x409F = 11
the Entei/Suicune/Raikou release scene plays (m-tower-cn-11.png, speaker lines about "the three beasts' power"); with 3 nothing
happens (tower-cn-3). 0x409F = 3 is not 11 again by any later script, so the beasts are gone for good.

## D-1580 (Ho-Oh panel clears flag 565)

The puzzle UI cannot be driven, so the success branch is forced: a scratch copy of the ROM has file 45 offset 34..38
(`AlphPuzzle 3` + `RestoreOverworld`) replaced by `BufferPlayersName 0` + `Noop`, flag 2426 set before, then
`run_script(file=45, index=0)` runs the panel script natively from there (HidePerson 1, ClearFlag 273, SetFlag 546,
ClearFlag 565, warp). Then the dream map (zone 325) is entered at its arrival warp (61,50), with 1902 clear, 1980 and 1981
set, var 0x40AB = 3 (the "gather the three companions" state):

| ROM | flag 565 after the panel | dream-world arrival |
|---|---|---|
| Chinese | cleared | nobody gathers (m-hooh-cn-panel.png) |
| rc7 | cleared | same |
| control (no panel run) | set | Silver, Gold and the others gather (m-hooh-cn-nopanel.png) |
| rc7 + hooh-panel-silver-marker | still set; 273 cleared, 546 set as before | gathering as in the control (m-hooh-fix-panel.png) |

Silver's own battle is therefore skipped by the same marker (file 50 @2556 treats a clear 565 as "Silver finished"); that last
step was read from the script, not played. Natural order: the panel needs no story step.

## D-1581 (bug hunt vs Forest of Time, var 0x4099)

Reading the scripts gives a sharper picture than D-1429: in the hunt 0x4099 = 3/4 names the rock that will be the last one
(file 92 L1878/L1963: rock script 2 is blocked at 4, script 5 at 3; L4468/L4586: the closing chain), 5 = every rock done,
and Bugsy's closing talk, the reward and the reset to 2 (@667, @2879, @5713) need exactly 5. The Forest of Time (zone 327,
file 52) has two triggers on 0x4099 with no check that the Sammy chapter runs: script 1 at the entrance clearing on 3 (empty
arrival scene, then 4) and script 3 at the top of the maze on 5 (Marauder scene and double battle, ending 0x4099 = 6, flag 2110).

Emulator (forest.py, flags 2105 clear = hunt, 1120 set as in a fresh game):

| Case | Chinese | rc7 | rc7 + guard |
|---|---|---|---|
| 0x4099 = 3, step onto (16,81) | scene plays without Sammy, Celebi, ranger; 3 -> 4 | same | nothing plays, stays 3 |
| 0x4099 = 5, step onto (15,38), battles forced to a win* | whole scene; ends 6, flag 2110 set, 2105 clear | same | nothing plays, stays 5 |
| Bugsy (map 117, (45,65)) at 5 | closing talk "the bug Pokemon ... have all been dealt with ... heading back to the Gym" | | |
| Bugsy (39,61) at 6 | only "leave the Pokemon near this rock to me": the hunt can never be closed | | |

*The Marauder double battle is lost by a Lv100 Mewtwo, so for the scene run a scratch ROM replaces both `TrainerBattle 763`
commands by Noops and the `CompareVarToValue 32780, 0` after each by `, 99` (forced win; mkforce.py, labelled).

So the permanent loss is real: a player whose hunt is at 5 and who walks into the Forest of Time before going back to Bugsy
loses the hunt's closing (and the 0x409F reset that the later expedition steps rely on), and the Sammy chapter is marked
finished (2110) before it began. A hunt at 3 gets its last-rock marker changed to 4.

Genuine Sammy control (flag 2105 set, 1120 clear, 0x4099 3, then 5): rc7 and rc7 + guard are identical frame by frame
(84 screenshots equal for the arrival scene; the 5 case ends identically: 4099 6, 2105 clear, 2110 set, same frame count).

Fix: `forest-of-time-sammy-guard` (work/notes/forest-of-time-sammy-guard_fix.md).

## D-1578 (Deoxys): reproduced, intent disputed, NOT fixed

deoxys.py (forced: both Orbs in the key pocket, flag 2261 set, 2188 clear, 1331 set; talk to the Fallen Red Star at
(213,68) from (213,69)): the Star scene plays, Deoxys Lv95 attacks, a Lv5 Magikarp loses: both Chinese ROM and rc7 whiteout
to the Pokemon Center (map 501) with flag 2188 set (the Star is hidden before the battle, file 943 @3623) and flag 1331
unchanged (the chief's claim, @5026..6397, only runs on a non-loss result; @5019 sends loss/draw to WhiteOut @3755).
A retry path does exist structurally (the Orbs are not consumed, the Star's script re-checks 2261 and the Orbs, Deoxys's
object is re-shown by the script), so `ClearFlag 2188` in front of the WhiteOut would restore the encounter. It is not
unambiguous: running away and a knockout consume the Star in exactly the same way (same hide before the battle), so a loss that
keeps the Star would be an exception the hack does not make anywhere else, and it would change defeat recovery. Question
recorded for the user (see the register); no fix.

## Not verified

* Natural play of any of these to the trigger state (0x409F = 11 after Lance's visit; a hunt at 5; 565 set from new game;
  the Star): states are forced, the triggers (talk, step, scene, battle outcome) run natively.
* The puzzle UI itself, Silver's battle after a cleared 565, the Burned Tower scene on the fixed ROM, the hunt's reward and
  0x409F reset after the fix, DeSmuME only (no melonDS/hardware).
* D-1581's maze copy (file 106, bounce at 0x4099 = 2 and 4): left as is.
