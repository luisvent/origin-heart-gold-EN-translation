# Multi-hit KO: the HP bar vanishes instead of draining (fix `faint-waits-for-hp-bar`, D-2318)

Report (Discord 'Scyther bug', 2026-10-07): "When I use Fury Cutter it one-shots everything; the health bar just
vanishes." A second player: with Iron Bash on Scizor and Fury Cutter on Scyther, "if the attack is a KO the
health bar just completely goes instead of draining; damage is calculated correctly. If it's not a KO or they
hold a Focus Sash it looks normal." User request 2026-10-09: "We want to fix these bugs, so for each issue create
a worktree per issue, and use a separate subagent to fix, test and review." This makes the fix a user-approved
exception to D-1337 (D-2318).

## What happens

Reproduced on the untouched Chinese ROM, on a build of `develop` (207caca) and on the same build without the fix,
on DeSmuME and on melonDS 1.1. A generated Lv50 Scyther's Fury Cutter (in this hack 40 power, two hits) against a
scripted wild Lv20 Rattata: the first hit KOs. The enemy HP bar drains for about 22 frames (48 -> 26 pixels),
then in one frame it is drawn full again (48 pixels) and the box slides off while the Rattata faints; then
"Hit 1 time(s)!", then "The wild Rattata fainted!". The same with Double Kick and Bullet Seed, and on the player
side (a wild Lv50 Scyther's Fury Cutter against our Lv10 Magikarp). A one-hit KO (X-Scissor, Slash) drains to
empty. A multi-hit KO whose last hit takes only a few HP (Fury Attack, a second hit of 4 HP) also looks normal,
as does a critical hit (seed 3 of the Double Kick runs: "A critical hit!", battle_string 2#77, is shown between).

## Cause

The hack's battle client (overlay 14, RAM 0x022007E0) plays a whole turn from a list of commands the battle
engine writes at the start of the turn (bit-packed; reader 0x02224CD8, interpreter 0x02204608, handler table
0x0224ABC0 with 0x5E entries, one handler call per frame until it returns non-zero). This is not vanilla
HeartGold's client: the US battle overlay (US overlay 12) has no such table.

Command trace (hook on the interpreter's `blx r3` at 0x02204690), frames from the turn's start:

| One-hit KO (X-Scissor) | Multi-hit KO (Fury Cutter, first hit KOs) |
|---|---|
| 8 hit, 18 frames | 8 hit, 18 frames |
| 53, 54, 52 | 53, 54, 52 |
| 3 message 'The wild Rattata fainted!', 54 frames | |
| 21 faint (cry, HP box, sprite drops) | 21 faint |
| 57, 58, 56, ... | 57, 58, 56, 2 'Hit 1 time(s)!', 3 'fainted!', ... |

- Command 8 (0x02204CF0) starts the hit's blink and the HP-bar task (0x022013E0 -> task 0x02201328) and waits
  only for the blink (byte 0x02255EDC). The bar drains on in the task, one step per frame; when every bar it
  drives is at its new value the task writes the new HP into the bar (0x02210AE8: hp -= damage) and sets the
  byte 0x02252D3E to 1. 0x022013E0 clears that byte when it starts. Command 12 (one bar, 0x02204C6C) waits for it.
- Command 21 (handler 0x02205124 -> Faint_Run 0x0222CB7C) does not wait. Its first steps redraw the HP box
  through 0x0222DF40 -> 0x0222DF58 -> 0x02210934 (flags -1): that resets the bar (0x02210A64 with damage 0) and
  draws it from the bar's HP field, which still holds the HP before the hit until the task ends. That is the
  jump back to full; then the box slides off.
- After a one-hit KO the 54-frame 'fainted!' message sits between commands 8 and 21, longer than any drain (the
  bar drains one pixel per frame, at most 48), so the bar finishes in time. After the KO hit of a multi-hit move
  the faint comes straight after the hit.

RAM at the first call of Faint_Run (`[0x02255C74] + 0x2AC + 0x3C * i`: {value, hp, max hp, damage}):

| ROM | 0x02252D3E | enemy bar |
|---|---|---|
| Chinese v4.0.3 | 0 | 6631, 46, 46, 46 (draining; HP field still 46) |
| build without the fix | 0 | 6199, 43, 43, 43 |
| build with the fix | 1 | 0, 0, 43, 43 (drained; HP field 0) |

Vanilla HeartGold: the healthbar task of the USA battle overlay (US overlay12 0x0225FFDC, cited in fix.toml as
US overlay12 0x0225FFE2) sets the bar, steps it until it returns -1 and only then reports the command done to the
battle engine, so the engine cannot start the faint while the bar drains. Not compared in an emulator (the
harness cannot start a battle on the USA ROM); the code reading is the evidence that this is not vanilla
behaviour.

## Fix

`work/patches/faint-waits-for-hp-bar/` (overlay 14, three regions, 48 bytes; listing in the folder):

1. Command 21's handler returns 0 ('not done, ask again next frame') while 0x02252D3E is 0, then calls Faint_Run
   as before. It moves 2 bytes earlier into the alignment padding (0x02205122) to make room for the literal,
   and the table entry 21 (0x0224AC14) follows it. The old `& 0xFF` of the battler is dropped: command 21's
   argument is read as one byte (argument type 1, table 0x0224D234). Faint_Run's 1/0 is returned as it is (the
   interpreter only tests for non-zero).
2. 0x02252D3E is in overlay 14's .bss, so it is 0 when a battle starts; a faint before the first HP bar of the
   battle would then wait for ever. The battle client's set-up 0x02200B64 (called once from 0x02224E9C) zeroes
   0x02252D30..0x02252D3B with six halfword stores; it now does it with three word stores and sets 0x02252D3E to
   1 with the 4 bytes this frees.

Other users of the byte: the HP-bar task (0, then 1), the level-up effect 0x022115C0 / task 0x02211604 (0, then
1), command 12 and the level-up step at 0x0222F88C (read). Each starts its own task before it reads the byte, so
the start value changes nothing for them. Values are only 0 and 1.

Not changed: the order of the messages ('Hit N time(s)!' and 'fainted!' still come after the faint, as in the
hack), command 8 (a hit still does not wait for its bar, so messages after a non-KO hit still overlap the drain,
as in the hack), the damage, the HP-bar code.

## Tests (2026-10-09)

DeSmuME (`emu_harness.py fixes --case faint-waits-for-hp-bar`, scenario `multihit-ko`, enemy and player side):
the build is `fixed`, the control (`build.py --no-patch --without faint-waits-for-hp-bar`) `original`; the
Chinese ROM judges `original` too. Ad-hoc runs (scripts not kept; work/build is git-ignored):

| Case | Chinese | without the fix | with the fix |
|---|---|---|---|
| Fury Cutter, first hit KOs (enemy) | bar jumps back, done 0 | same | drains to 0, done 1 |
| Double Kick, Bullet Seed (enemy) | same bug | same bug | drains to 0 |
| Fury Cutter KOs our Magikarp (player) | bug | bug | drains to 0/24, then slides |
| Double Kick with a critical hit | no bug | no bug, faint at frame 815 | same, frame 815 |
| Fury Attack, KO by a 13-HP hit | no bug | faint at frame 251 | frame 251 |
| X-Scissor one-hit KO | no bug | faint at frame 268 | frame 268 |

So the fix only delays a faint while a bar is still draining; everything else keeps its timing to the frame.

melonDS 1.1 (Route 1 save, wild Rufflet Lv6 found by walking, generated Lv50 Scyther with Fury Cutter):
Chinese ROM and the build without the fix: the bar jumps back to full at 26 pixels and the box slides off; with
the fix the bar drains to 0, the Rufflet faints and the game returns to the field (no hang).
