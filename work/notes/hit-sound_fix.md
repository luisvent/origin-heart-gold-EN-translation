# Battle hit sound (fix `battle-hit-sound`, D-2342)

Discord reports (rc5 era): "When you're in battle you don't hear the noise of your attack hitting. You hear the
animation of the attack but not the noise when it hits." and "Pikachu's Electro Ball has no sound when the
animation goes off." An rc6 tester mentioned "missing audio" in general.

## How sound was observed

The harness runs DeSmuME and melonDS without audio, so no test listens. Instead:

- **DeSmuME (execution hooks).** Every sound effect and sequence goes through
  `NNS_SndArcPlayerStartSeqEx` (arm9 `0x02006B64`, sequence number as its stack argument). `PlaySE(u16 seq)`
  is arm9 `0x02005F5C` (US arm9 `0x0200604C`, the function called most often with constants 1500-1999);
  it calls the start through `0x02005FCC`, which returns at `0x02006006` with r0 = 1 when the sequence
  started. The probes logged every start with its frame, together with the battle messages (MsgLog) and the
  damage action described below.
- **melonDS (data watchpoints, no execution hooks).** The sequence's INFO record in the SDAT (in RAM since
  boot) is read by `0x0200540A` when PlaySE starts that sequence. A read watch on the records of 1788, 1789,
  1790 and of Tackle's animation sound 1833 shows which sounds start.

Sequence names come from the SDAT's symbol block (identical in the USA and Chinese ROMs): 1788
`SEQ_SE_DP_KOUKA_H`, 1789 `SEQ_SE_DP_KOUKA_L`, 1790 `SEQ_SE_DP_KOUKA_M` (the hit sounds), 1833
`SEQ_SE_DP_050` (Tackle's animation).

## Cause

**HeartGold** plays a hit sound with every damaging hit: battle script command 215 (PlayMoveHitSoundEffect,
US overlay 12 command table `0x0226C6C8`) sends client command 0x3F, whose handler (US overlay12
`0x0225B3D4`) plays 1790 (normal), 1788 (super effective) or 1789 (not very effective), panned to the target's
side.

**The hack** replaced the battle code with its own engine (overlay 14, `0x022007E0`); the subscripts in
a/0/0/1 are no longer loaded (their command words never appear in RAM during a battle). The engine drives the
screen with a list of commands; the command table is at `0x0224ABC0` (0x5E handlers, dispatched at
`0x0220466E`), and entry 8 is the move-damage command `0x02204CF0` (the faint-waits-for-hp-bar fix calls it
command 8 too) (args: target count, effectiveness class, move id; per target a battler id and the
damage at BattleClient +0x98 / +0x9C). It starts the blink (`0x0222EF1C`) and the HP-bar drain
(`0x022013E0`) but plays no sound. No code anywhere in the hack (arm9, every overlay) loads 1788-1790, and in
battle nothing requests them:

| ROM | Tackle on Snorlax (class 1) | Thunderbolt on Gyarados (class 2, 2#74) | Tackle on Onix (class 3, 2#75) |
|---|---|---|---|
| Chinese v4.0.3 | 1833 only | 2114, 1952 (animation) only | 1833 only |
| develop build (d244c4a) | the same | the same | the same |
| this fix | 1833, then **1790** | 2114, 1952, then **1788** | 1833, then **1789** |

So the bug is the hack's, not ours (text speed and the other fixes do not touch sound). The effectiveness
class values 1/2/3 were read from the action's arguments next to the effectiveness messages.

**Electro Ball** is a second, separate gap: its move animation (a/0/1/0 #486) has no sound command at all
(opcodes 22/24/25/26 carry a sequence number in every other animation). The same holds for the hack-added
animations listed in D-1598 and the FAQ (Synchronoise, Electro Ball, Soak, Flame Charge, Coil, Low Sweep, Acid
Spray, Foul Play, Simple Beam, After You, Round, Echoed Voice, Chip Away, Clear Smog, Venom Drench; also
files 568, 590, 691, 914). HeartGold has no animation for these Gen 5+ moves, so there is no sourced sound to
add; they are not changed. With this fix they still play the hit sound when they deal damage.

## Fix

Overlay 14 `0x02204D0E`-`0x02204D4F` (66 bytes, step 0 of command 8): the hack's loop that builds the target
and damage lists is rewritten in fewer instructions, and the bytes it frees call `PlaySE(1786 + (class == 1 ?
4 : class))`: class 1 → 1790, 2 → 1788, 3 → 1789, any other class → no sound. The lists, their count and the
stack slots and registers the unchanged code after it uses are the same (checked: the blink and HP-bar
arguments equal the BattleClient values in single and double battles, e.g. Surf on two foes: count 2,
positions [1, 3], damages [25, 42]). One sound per action: once for a move hitting two targets, once per
hit of a multi-hit move (Double Kick: two hits, two sounds). Unlike HeartGold the sound is centred (no room
for the pan).

## Tests

- `emu_harness.py fixes --case battle-hit-sound` (scenario `hitsound`, DeSmuME): Pikachu Lv50 uses Tackle on a
  wild Snorlax, Thunderbolt on a wild Gyarados and Tackle on a wild Onix. Fixed build: `fixed` (1790, 1788,
  1789, each started in the frame of its damage action, start result 1); control build without the fix:
  `original` (no hit sound); the untouched Chinese ROM: `original`.
- melonDS 1.1, Route 1 save (`route1_path_2mons.sav`), a trainer battle with Tackle: the fixed build starts
  1790 about 32 frames after each Tackle animation sound (3 of 3); the control none; no ARM9 abort, the
  battle ends normally.
- Double battle (Giovanni, `TrainerBattle 402 402`, Blissey with Surf), Double Kick (two hits) and the foe's
  Tackle on our Pokémon: the sound plays each time; the lists match.

## Review (2026-10-09)

- The rewrite was re-read against the hack's loop (0x02204D0E): for every count the same objects (from
  `0x02215704` with the battler id's low byte) and damages (low halfword at +0x9C) land at sp+0x18 / sp+0x10,
  count 0 skips the loop in both; the code after it reads only [sp], [sp+4], sp+0x10, sp+0x18 and r7
  (r4-r6 are restored by the pop; [sp+8] / [sp+0xC] are not read again). PlaySE (`0x02005F5C`) is
  straight-line: it starts the sequence and returns, nothing waits for it. The built bytes equal the listing,
  the control's equal the Chinese ROM.
- HeartGold's sound by effectiveness (US overlay 12 `0x02264228`, the sender of client command 0x3F): flag 2
  (super effective) -> 2 -> 1788, else flag 4 (not very effective) -> 1 -> 1789, else 0 -> 1790. Only US
  battle subscripts 2 (move damage) and 90 (substitute hit) contain command 215; the confusion self-hit
  (subscript 39) plays the confusion animation and updates the HP bar without it.
- DeSmuME, fixed build and control (`work/build/review/cases*.py`), command 8 and every sequence logged; in all
  13 / 12 commands the blink and HP-bar arguments equal the BattleClient lists:

| Case | Hack | Fixed | HeartGold |
|---|---|---|---|
| Seismic Toss, Dragon Rage, Double-Edge (main hit), Future Sight (hit 2 turns later) | command 8, class 1 | 1790 | 1790 |
| Double Kick (super effective, 2 hits) | 2 x command 8, class 2 | 1788 twice | 1788 per hit |
| Fly hitting the player's Pokemon | command 8, class 1 | 1790 | 1790 |
| Surf / Earthquake on Mewtwo + Tyranitar (doubles, Giovanni 402) | one command 8, count 2, class 2 | one 1788 | one sound per target |
| Miss (Tackle on a flying Crobat), Protect, immune (Tackle on Gastly, Seismic Toss on Gastly) | no command 8 | none | none |
| Recoil of Double-Edge, poison, Leech Seed, sandstorm | no command 8 | none | none |
| Guillotine (one-hit KO) | command 12 | none | 1790 (by the scripts: the damage goes through subscript 2; not run) |
| Tackle on a substitute | command 7, message only | none | 1790 (subscript 90; not run) |
| Hurt itself in its confusion | commands 48 + 28 (as residual damage) | none | none (subscript 39) |

  Struggle could not be reached by the harness (a move at 0 PP only shows "out of PP"); not tested.

