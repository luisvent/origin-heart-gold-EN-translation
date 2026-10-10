# 'The wild' / 'The foe's' on the wrong Pokémon (fix `battle-message-variant`)

**Status (2026-10-09): fixed on branch `fix/destiny-knot-side`.** D-2319 is the user-approved exception to D-1337
(user, 2026-10-09: "Please fix"). Round 2 (user: "Yes, same branch"): the move lines with the same mix-up are fixed
too, see 'Round 2'. Not fixed: Lock-On 1#878, 1#1410.

## Report

- Found by the reviewer of `fix/battle-text-chinese`: a wild Chansey's Attract hits a Tauros holding a Destiny
  Knot, so the wild Chansey falls in love too. The line read "Chansey fell in love because of the Destiny Knot!"
  without "The wild".
- Same class: an older, unreproduced player report of an ally's Pokémon called "Foe's".

## How the form of a bank-1 line is chosen

- battle_string bank 1 has four forms of each line: plain (the player's Pokémon), 野生的 'The wild', 对手的
  'The foe's', and '<trainer>'s'. The prefix stands before one Pokémon-name parameter (usually {0}).
- The server sends a line as stream op 3 with a variant battler and the parameters (0x02224C50). The client's
  printer 0x02225EA8 gets {variant battler, params...}, picks the form from the battler's side (0x02225E40) and
  fills the template from the parameters. So the variant battler must be the Pokémon the prefix belongs to.
- A message record (MsgRec_Init 0x02225DC0, MsgRec_AddArg 0x02225DEC) of type 2 is sent by 0x0222934C(record,
  variant battler); the record holds only the parameters. Whoever calls 0x0222934C chooses the variant.

## Cause

1. **Condition applier** 0x0221E53C (called by ApplyCondition 0x0221F87C through 0x0221E46C, and by its queued
   path 0x0221E05C). Its struct has the source (the Pokémon whose move, Ability or item causes the condition,
   struct [0]) and the target ([1], the one that gets it), and the caller's record at struct + 0x30. The variant
   is the source's battler when there is a source, else the target's (0x0221E548 `cmp r0, #0; beq`). The
   applier's own default message (built when the caller gives no record) names the target and uses the target.
   Destiny Knot (0x0220AECC) is: source = the holder, target = the attacker (battle var 0x0A), record 1#448
   ({0} = the attacker, {1} = the item). So the holder's form was used for the attacker's name.
2. **HP-change applier** 0x0221F968 (struct: source [0], target [1], record at + 0x20) sends its record with the
   source's battler (0x0221FA1C `ldrb r1, [r4]`).
3. Same function, Heal Block: 1#1200 '{0} can't heal because of Heal Block!' is emitted with the source's
   battler and the target as {0} (0x0221FA4A `ldrb r0, [r4]`).

## Static audit (overlay 14 of the Chinese ROM)

Scripts in the session scratchpad (`fix/destiny-knot-side/sym.py`, `sym2.py`, `sym3.py`): a linear symbolic pass
from each function's push to the call, recording the struct's source / target stores and the record's type, id and
parameters; the prefixed parameter is read from the template of the wild form (base id + 1). Branches are not
followed, so each flagged site was also read by hand.

**ApplyCondition 0x0221F87C, 51 calls.** Every call whose record names a Pokémon and whose source and target differ
names the **target** in the prefixed slot. None names the source there. So "target first" fixes all of them and
changes nothing where source = target:

| Call | Record | Source → target |
|---|---|---|
| 0x0220AF48 | 1#448 Destiny Knot | holder → attacker (var 0x0A) |
| 0x0220C88C | id from the caller ({0} = target) | helper 0x0220C838; its four callers have source = target or no record |
| 0x02234F0A | 1#638 'was poisoned' (Poison Point type) | holder → attacker (var 0x0B) |
| 0x0223A158 | 1#324 | holder → var 0x0B |
| 0x0223D11A | 1#1442 Curse ({1} = the cursed one) | user → target (var 0x62) |
| 0x0223DB54, 0x022440A0, 0x0224429A | 1#1180 'can no longer escape' | user → target |
| 0x0223E28C | 1#754 | user → target |
| 0x02240FA8 | 1#762 'Ability was suppressed' | user → target |
| 0x02242378 | 1#1530 Smack Down | user → target |
| 0x02243BB8 | 1#1604 Electrify | user → target |
| 0x02243E44 | 1#1624 Powder | user → target |
| 0x022444EA | 1#1840 | user → target |
| 0x022449C4 | 1#1836 'Ability was nullified' | holder → var 0x0B |
| 0x022456DE | 1#1958 Octolock | user → target |

Not covered: 0x0223CFDA, 1#878 '{0} took aim at {1}' (Lock-On / Mind Reader). The condition is on the user
(source = target = the user) and the prefix is on {1}, the aimed-at Pokémon, so neither rule gives the right
form. It needs a different change (report below).

**HP-change applier 0x0221F968, 21 calls.** The record's first parameter is the prefixed Pokémon in every call (all
prefix {0}). Four callers name the target while the source differs: 1#524 'HP was restored' at 0x0223AA2E,
0x0223DF22, 0x022445FE and 0x02246480. Two name the source while the target differs: 1#944 (Wish) and 1#2138.
So "the record's first parameter" is the rule that is right for all of them.

## Fix, round 1 (`work/patches/battle-message-variant`, overlay 14, 18 bytes in 3 regions; round 2 adds 12 halfwords)

1. 0x0221E548 (10 bytes): `cmp r5, #0; bne` to the old target path (0x0221E55A); `cmp r0, #0; beq` to the
   no-variant exit; `b 0x0221E55C`, the old target path's call, with r0 = the source. The variant is the target's,
   the source's only without a target. The old source path's last four instructions are no longer reached.
2. 0x0221FA1C (6 bytes): `adds r0, r4, #0; adds r0, #0x20; ldrb r1, [r0, #4]`. The record goes out with the
   battler of its first parameter.
3. 0x0221FA4A (2 bytes): `ldrb r0, [r4, #1]`. Heal Block's line uses the target's battler.

Not changed: message ids and parameters, which Pokémon gets the condition, the stored source (the per-turn
infatuation message still names the attracter), the default messages, and every line where the old and new
choice are the same Pokémon. The full build differs from the `--without battle-message-variant` build only in
these bytes of overlay 14 (byte compare; 29 bytes after round 2). No overlap with the other open overlay-14 branches (battle-text-
chinese, type-change-message, heal-bell-status, multihit-ko-hpbar, cute-charm-infatuation).

## Evidence (2026-10-09)

A runtime check hooks the client printer 0x02225EA8 and compares the variant battler with the parameter in the
prefixed slot (`cases.py` in the scratchpad). Battler 1 = the player's lead, 13 = the wild / foe Pokémon.

| Battle (DeSmuME) | Chinese ROM | `--without` build | full build |
|---|---|---|---|
| wild Chansey (Attract) vs Tauros + Destiny Knot, 1#448 | variant 1, {0} 13: 红线让吉利蛋着迷了！ | 'Chansey fell in love because of the Destiny Knot!' | 'The wild Chansey fell in love because of the Destiny Knot!' |
| player's Chansey (Attract) vs wild Tauros + Destiny Knot | variant 13, {0} 1: 红线让野生的吉利蛋着迷了！ (own Chansey called wild) | same mismatch | variant 1 = {0} |
| Gengar Mean Look vs wild Rattata, 1#1180 | – | variant 1, {0} 13 | variant 13 |
| Gengar Mean Look vs Camper Ward's Nuzleaf | 长鼻叶 已经无法逃走了！ (no 对手的) | 'Nuzleaf can no longer escape!' | 'The foe's Nuzleaf can no longer escape!' |
| Gengar Curse vs wild Rattata, 1#1442 ({1}) | variant 1, {1} 13 | '... put a curse on Rattata!' | '... put a curse on the wild Rattata!' |
| Magnemite Lock-On, 1#878 | variant 1, {1} 13 | same | same (not covered) |
| Pikachu vs wild Jolteon (Volt Absorb), 1#524 | – | variant = {0} | variant = {0} (unchanged) |

- `emu_harness.py fixes --case battle-message-variant` (scenario `battle-variant`, ten battles after round 2): PASS.
  Fixed build 'fixed' (variant = {0} in all ten), control and Chinese ROM reference 'original' (another Pokémon in
  all ten).
- **melonDS 1.1** (headless backend), Gengar (Mean Look) against a wild Shroomish in the Route 24 grass. Full build:
  'The wild Shroomish can no longer escape!'. `--without` build: 'Shroomish can no longer escape!'. No ARM9 data
  abort, prefetch abort or undefined instruction on either; no hang. Round 2 build: the same Mean Look line, and
  Toxic used again: 'The wild Shroomish is already poisoned.' (control: 'Shroomish is already poisoned.'), no
  aborts.
- Regions 2 and 3 were not seen in a battle: their handlers (heal another Pokémon; Heal Block against another
  Pokémon's heal) are hard to set up in a single battle. They are covered by the static audit above.

## Round 2: move lines sent by the move code

Each line was checked in battle where it could be set up (the runtime check above, `cases.py`; also the scenario
`battle-variant`, which now has ten battles), else by reading the code: the variant battler is another Pokémon than
the one in the prefixed slot. Each fix is one halfword: the variant becomes the register or field that already
holds the named Pokémon.

| Line | Site | Old variant → new | Proof |
|---|---|---|---|
| 1#296 'It had no effect at all on {0}' (OHKO move, higher level) | 0x0221A7B8 | attacker (r6) → target (r4) | battle: CN / control 1 vs {0} 13; fixed 13 |
| 1#288 'It doesn't seem to affect {0}' | 0x0221AE92 | attacker's battler → r4 (= {0}) | static: same function as the next row, other branch |
| 1#288 (type immunity, Tackle on Gastly) | 0x0221AEB6 | attacker's battler → r4 (= {0}) | battle: CN / control 1 vs 13; fixed 13 |
| 1#288 (loop over a move's targets) | 0x0221AF34 | attacker (r6) → target (r4) | static: {0} = r7 = the target's battler |
| 1#288 (immunity dispatcher 0x0221B1EC) | 0x0221B228 | r5 (the attacker, its r0) → r2 (= {0}) | static |
| 1#706 '{0} protected itself from the attack!' | 0x0221B384 | attacker (r6) → r2 (= {0}) | battle: CN / control 1 vs 13 'Rattata protected itself'; fixed 'The wild Rattata ...' |
| 1#288 (sent only when the target is not the struct's source) | 0x0221B8F6 | struct source ([r5]) → r2 (= {0}) | static: the code compares the two and prints only when they differ |
| 1#1220 '{0} had its energy drained!' | 0x0221C1FC | drainer (r4) → r2 (= {0}) | battle: CN / control 1 vs 13; fixed 13 |
| Condition check 0x0221E0AC → 0x02229944: 1#340 'is already poisoned', the other 'already ...' lines, 1#288 | 0x0221E0E8 | struct source → struct target ({0} is always the target there) | battle (Toxic again): CN / control 1 vs 13; fixed 13; melonDS too |
| 1#1468 '{0} couldn't stay airborne because of gravity!' | 0x0220E4DA | Gravity's user ([sp]) → r2 (= {0}, each grounded Pokémon) | battle (Gravity during Fly): CN / control 1 vs 13; fixed 13 |
| 1#1000 '{0} anchored itself with its roots!' (Roar / Whirlwind against Ingrain) | 0x02220B78 | Roar user (r6) → r2 (= {0}) | battle: CN / control 1 vs 13; fixed 13 |
| 1#1554 '{0} is waiting for {1}...' (Pledge; prefix on {1}) | 0x02222DE2 | {0} (r4) → {1} (r7) | static (double battles only; the partner is normally on the same side, so the visible change is small) |

Battles on the full build (DeSmuME), all ten scenario cases plus Curse, Levitate, Leech Seed, Ingrain, Volt Absorb
and Mean Look against a trainer: every bank-1 line had variant = the Pokémon in its prefixed slot, except 1#878
(Lock-On, below) and 1#452 (the per-turn infatuation line, fixed by `battle-message-references` on
`fix/battle-text-chinese`).

**Not fixed.**
- Lock-On / Mind Reader 1#878 '{0} took aim at {1}!' (0x0223CFDA). The prefix stands before {1}, the aimed-at
  Pokémon, but the line is the record of a condition the user puts on itself (source = target = the user), so the
  applier can only give the user's battler. A fix would have to send the line itself, after the condition is
  applied, with {1}'s battler: about 12 bytes more than the handler has, so it needs new code space (a code
  cave or overlay growth). Rare moves. Left for the user to decide.
- 1#1410 '{0} is all fired up!' at 0x02221F56 (a handler in the table at 0x0224D218, id 0x24): its variant is a
  stack argument whose caller was not found, and the line printed with the right form in the battles tried
  (Focus Energy sends it through a record). Not confirmed, so not changed.
