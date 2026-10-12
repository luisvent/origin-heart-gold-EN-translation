# Throat Chop freeze (Discord #bugs, xaidras): not reproduced; move sweep

**Status (2026-10-12): no fix.** The reported freeze ("Game freeze when Meowscarada use Throat Chop", no save, platform unknown) could not be reproduced. Decisions D-2346..D-2349 (branch numbers, renumbered at merge) record the findings below as open hack-findings.

## What was tried (all on a fresh develop build e98854f, and the untouched Chinese v4.0.3 ROM)
- Throat Chop as player and as foe, singles and doubles (trainer 6), wild and trainer AI (trainers 185, 4, 44, 607, with the foe's moves forced), 2-6 turns, Meowscarada (908, also with Protean 168) and other species, DeSmuME and melonDS 1.1 (data aborts are visible there): no hang, no abort.
- Silence follow-up: foe or player picks a sound move (Hyper Voice, Growl) while Throat Chopped: the game shows "The effects of Throat Chop prevent X from using certain moves!" and stays on the move menu. That is a refusal, not a freeze.
- Options: TEXT SPEED FAST, BATTLE SCENE OFF, BATTLE BG GEN 4 / NEW / GEN 5, five maps (Pal Park, Route 1, Safari, gym, town): no change.
- The Throat Chop animation (a/0/1/0 #675) executes only valid opcodes (traced through the animation interpreter, overlay 8 0x021E4DD0, both sides). Its move record has condition 24 (kind 2, 2 turns), which only it uses; the engine handles it.
- Meowscarada is "never met in play" in this hack, so the reporter must have edited the save or used a cheat.
Open: the reporter's platform, patch version and situation (anything besides one-on-one use).

## Move sweep (all 920 moves, each as player and as foe)
Method: `work/tools/emu_move_sweep.py` (melonDS state at a Pal Park wild battle; the actor's move records are overwritten; 2 turns each; data aborts counted). Full run: 1840 cases. A DeSmuME run with an opcode trace (not committed) covered moves 1-749 (1492 cases, then stopped to wrap up) and found no invalid opcode in them.

Findings (all identical on the Chinese ROM, none reachable in normal play):
| move | result |
|---|---|
| Shell Trap 704 | data abort at 0x02229350 when the trap triggers (player or foe): NULL third argument to 0x0220F3B8 -> 0x0222934C. DeSmuME does not show it. Only Turtonator learns it, never met in play. |
| Psychic Noise 917 | its animation makes the interpreter execute 0xFFFFFF8B: endless loop on DeSmuME, prefetch abort on melonDS. Nobody learns it. |
| "move #622, 624 ... 656" (even ids, 0 PP) | data abort at 0x020262D8 if used by the player (no animation target). Unobtainable. |
| Pursuit 228, Sky Drop 507, Happy Hour 603, Celebrate 606, Hold Hands 607, Revival Blessing 863 | cannot be selected in singles, no message (Belch 562 and Stuff Cheeks 747 show a message). Not a freeze; game stays responsive. |
| Gigaton Hammer 893, Blood Moon 901 | cannot be used twice in a row (refused on turn 2). Expected. |
| Teleport, Memento, Explosion, Self-Destruct, Misty Explosion, Final Gambit, Bide, OHKO moves | end the battle (harness reports field/black); not faults. |

Everything else ran 2 turns on both sides without abort or hang. Not covered: doubles for every move, and branches not taken in these fixed one-on-one fights.

## Fix
None: no accidental bug that real players can reach was found. Shell Trap could get a NULL guard in overlay 14 (0x0220F3D2 region, needs a trampoline: no free halfword); Psychic Noise's script needs a corrected a/0/1/0 member. Both left for Shishio to decide (D-1337 history; unobtainable moves).

## Re-run
`for each shard: .venv/bin/python work/tools/emu_move_sweep.py --rom R --sav work/build/memcheck/full_bag_6mons.sav --out DIR [--moves 675,704]` and restart while the exit status is 3 (after an abort the core must be restarted; finished rows are skipped).
