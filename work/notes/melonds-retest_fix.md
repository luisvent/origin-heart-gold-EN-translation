# melonDS retest of three player reports (2026-10-09)

Three Discord reports had not reproduced on DeSmuME the day before. They were retested on melonDS 1.1 (headless
backend, `--emulator melonds`) and on DeSmuME, on the untouched Chinese ROM (`origin_v4.0.3_cn.nds`) and on a
develop build (`d244c4a`, SHA-256 `34fbcd66…`, equal to the control build below). RTC 2026-10-09 12:00.
Only the first one reproduced; it is fixed by `work/patches/battle-heal-hpbar-switched-out` (D-2314).

| Report | melonDS 1.1 | DeSmuME | Verdict |
|---|---|---|---|
| Maxie gauntlet freeze after a Potion (Lavender Town tower) | **freezes** (CN and develop) | runs on (reads address 0) | hack bug, fixed |
| Battle Bag quick exit hardlock (Mt. Moon; 3DS with a third-party fork) | 810 trials, no hang | 810 trials, no hang | not reproduced |
| Minimize makes the player's HP box top border flicker | border unchanged on every frame | the same | not reproduced |

## Setup

The waves of Maxie's gauntlet are script file 17, script 31 (zone 155): wave 1 `MultiBattle 211, 529, 530`
(Blue), wave 2 `MultiBattle 524, 527, 528` (Green; Red 525 for a female player), wave 3 `TrainerBattle 526`.
melonDS has no execution hooks, so `run_script` cannot start them there. Instead, test copies of the ROMs (never
the builds that ship) had four coordinate-trigger entries of script file 17 repointed: script 2 → offset 4804
(wave 1, then the rest of the scene, waves 2 and 3), script 4 → 4986 (wave 2 with Green), script 8 → 6365
(wave 2 with Red), script 7 → 6506 (wave 3). The player stands next to the trigger and steps on it. The party:
generator Pokémon made on DeSmuME (`generate_pokemon` gives junk on melonDS) and copied into the save: Marshtomp
Lv100, Blissey, Snorlax, Clefairy, Marshtomp Lv60, all at half HP, moves Surf / Growl / Protect / Splash; the
Medicine pocket holds Potions and Super Potions. Scripts and logs: the session scratchpad (`fix/melonds-retest/`),
outputs under `work/build/retest/` of the worktree (git-ignored).

## 1. Maxie gauntlet: Potion, then Roar (reproduced, fixed)

Potion from the battle Bag on each party slot, turn 1 and turn 2, every wave, both partners, both emulators,
Chinese ROM and develop. melonDS: **wave 2 with Green, Potion on the lead (slot 0): the game freezes on
"Shishio used the Potion!"** (Chinese and develop), a data abort with fault PC `0x02210C9E` (`ldr r0, [r0]`),
CPSR `0x40000097`, abort LR `0x02210CA6`. Wave 2 with Red froze on turn 2 on the Chinese ROM. Benched slots,
wave 1 and wave 3 never froze; DeSmuME never froze. Running the whole gauntlet (Potion every other turn, Surf
otherwise, from wave 1 into wave 2 as in play): the develop control froze in wave 2 with the same fault.

Cause (overlay 14, the hack's battle engine; it computes a turn first and then plays it back):

- Call chain at the abort: bar task `0x0222DFE8` → `0x02210AE8` (update HP gauge) → `0x02210DF0` → `0x02210C94`
  (draw gauge), which loads `bar->sprite` (+0x34) and reads through it. The bar at `0x022C14C0` was all zero:
  health bar 0 of the array at G + 0x2AC (0x3C bytes each), which a double battle never sets up.
- The task was started by `0x0222E024` (the Potion's playback handler `0x022053D0` passes the healed Pokémon's
  id byte): battler = `0x02228740(id)` (5 = not on the field), bar index = `0x022156C4(battler)`, table
  `0x0224D134` = `03 05 00 00 | 02 04 00 00` (double battles) or `battler & 1` (single). Battler 5 → bar 0.
- Why 5: the player's party list in the battle engine had changed from `[1, 2, 3, 4, 5]` to `[5, 2, 3, 4, 1]`
  at the moment the Potion was chosen. A logging stub (written into RAM of a melonDS state, not into any ROM)
  on the party-swap routine `0x02218F54` and its callers showed `0x02220B94(Houndoom, Marshtomp Lv60)` →
  `0x02220D9C` → switch-in `0x022202C0(battler 0, slot 0, slot 4)`: Houndoom's **Roar** (trainer 528 has Roar)
  dragging Marshtomp Lv60 in. The server had already run the whole turn (Potion, then Roar), so when the
  client played the Potion back, the healed Pokémon was no longer on the field.
- DeSmuME reads address 0 and goes on. The battle RNG there gave other outcomes (Roar on the partner), so the
  same session never froze. On DeSmuME with a fixed clock, the partner's Azumarill eats its Sitrus Berry and
  Roar then drags it out: the berry's healing playback goes through the same routine and reads address 0 too.
  In single battles the lookup's 5 maps to the opponent's bar (no crash, a wrong bar animates).
- "Speed-up" in the report: emulator speed-up changes no emulated timing; a freeze while speeding up fits the
  same cause (a Potion or a berry, then Roar), but that is inferred.

Fix: `0x0222E024` returns early, with the done flag set, when the lookup gives 5 (fix.toml, the .asm and the
.listing have the details; the routine is re-laid in place, and the handler passes the id in r0).

Results after the fix (melonDS 1.1; test copies with the repointed triggers):

| Run | Chinese | control (develop) | fixed |
|---|---|---|---|
| wave 2 Green, Potion on each slot ×2 turns | slot 0 aborts | slot 0 aborts | all pass |
| wave 2 Green, 6 trials (RAM move patch had no effect; natural Roar) | 6 × abort | 6 × abort | 6 × pass, lead dragged out |
| whole gauntlet from wave 1, 80 turns | stayed in wave 1, no abort | abort in wave 2 | 80 turns, no abort |

DeSmuME (`emu_harness.py battle-heal`, also the fix's scenario in `emu_harness.py fixes`): the control animates
a bar without a sprite and reads address 0 in every trial; the fixed build skips that playback and still
animates the lead's bar (`fixes --case battle-heal-hpbar-switched-out`: PASS, fixed / original). On the Chinese
ROM the turn plays differently (Chinese text timing), so that scenario does not reach the condition there.

## 2. Battle Bag: open and leave at once (not reproduced)

A wild battle in Mt. Moon (zone 107), command menu saved; from it, BAG touched, then after n frames
(n = 0, 2, …, 160) one of: B once; B mashed 15 times; the return button; HP/PP RESTORE then the return button
twice; the pocket then B twice. If the menu did not come back within 600 frames, extra return/B presses.
405 trials per ROM and emulator (melonDS and DeSmuME; Chinese and develop): every trial got back to the command
menu, no ARM9 abort, no hang. A single early B never leaves the Bag (the Bag ignores it while it opens); the
extra presses then do. The reporter used a 3DS with a third-party English fork, which this cannot cover.
Note: the DeSmuME develop run overlapped a rebuild of that ROM file; its result is reported as is.

## 3. Minimize: HP box border flicker (not reproduced)

Test copies with trainer 526 (wave 3, single) changed to a Clefairy Lv45 with Minimize ×4; our lead uses Splash.
Every frame of four turns captured (three Minimize animations, then the evasion-maxed turn), the top border rows
of the player's HP box (screen y 92–100, x 160–255) compared with their usual state in that turn: on melonDS
and DeSmuME, Chinese and develop, the border differs only in the last three frames of each turn (the box starts
bobbing when the command menu returns). No flicker during the Minimize animation.
