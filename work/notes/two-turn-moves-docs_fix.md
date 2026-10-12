# Two-turn moves: investigation and docs (Discord #bugs "Bounce move")

**Verdict: not a bug. The Chinese hack makes Bounce, Razor Wind, Skull Bash and Sky Attack one-turn moves on purpose. No fix; docs only.**

## Data (Chinese ROM `extra/new_move_data.narc`, flags word at +32, bit 1 = charge flag)

Charge flag set (two-turn): Fly (effect 155), Solar Beam (151), Dig (256), Dive (255), Shadow Force (272), Sky Drop (311), Freeze Shock (331), Ice Burn (332), Phantom Force (272), Geomancy (365), Solar Blade (151), Meteor Beam (effect 0), Electro Shot (effect 0).
Charge flag clear: Bounce (effect 263, the vanilla two-turn effect id, 80/100/10), Razor Wind (effect 39), Skull Bash (effect 145, power 120), Sky Attack (effect 75). Bide (effect 26) is its own mechanic.
The author's own sheets call Bounce one-turn (work/notes/sheet_mismatch_verification.md 4.3, D-1350). Chinese descriptions: Bounce 0738#340 still says 第１回合 / 第２回合 (stale, English kept faithful, already logged in D-1350); Razor Wind, Skull Bash and Sky Attack descriptions were rewritten as one-turn. The Speedoption mod restores Bounce's charge flags (bradams_items_moves_analysis.md), against the author's design.

## Emulator (DeSmuME; old vqueue/probe recipe from git 2e6fe55^ run against the Chinese ROM and a fresh build of develop e21ab4b)

Lv. 100 Mewtwo with one move vs a wild Lv. 100 Shuckle with only Splash, or only Protect (fast enough that Mewtwo moves second). A "cycle" is one command until the menu returns; the number of foe actions in it is the number of battle turns.

| move | foe actions per cycle | Protect on the first command |
|---|---|---|
| Bounce | 1 (CN, EN) | blocked at once (CN, EN) |
| Razor Wind, Skull Bash, Sky Attack | 1 (CN, EN) | blocked at once |
| Fly, Dig, Dive, Solar Beam, Solar Blade | 2 (CN; EN for Fly, Dig, Solar Beam) with the charge message (1#714, 726, 722, 746) | charge not stopped, attack turn blocked |
| Shadow Force, Phantom Force | 2 (CN) | attack got through |
| Freeze Shock, Ice Burn | 2 (CN) | charge not stopped, attack turn blocked |
| Geomancy, Meteor Beam, Electro Shot | 2 (CN); Meteor Beam and Electro Shot raise Sp. Atk on the charge turn | not relevant / not analysed |
| Bide | 2 (CN) | |
| Sky Drop | 0: nothing happened (2#441) against Shuckle in 3 cycles; not analysed | |

Raw results were in the scratchpad (res_*.json); recipe: probe.py around `emu_open.wild_battle` / `emu_sweeps.b_turn`.

## Descriptions (English, no edits made)

Only Bounce's description (0738#340, "turn 1 ... turn 2") contradicts its behaviour, and the Chinese says the same. Proposed change for the user to approve: none required (D-1350 records it); an optional fix would replace it with a one-turn wording not present in the Chinese, which D-1496/D-1500 forbid without approval.

## Docs

guide/known-issues.md: new section "One-turn and two-turn moves" under "Moves that work differently" and a pointer from the Bounce bullet. The site move pages already carry the Bounce tested note.

## Questions for Shishio

1. Sky Drop did nothing in the test (no foe action, no message beyond 2#441). Look into it, or leave it (can players get it)?
2. Do you want Bounce's description changed to a one-turn wording (needs your approval per D-1496)?
3. Only tested one-move-each setups; the Sky Drop result and Shadow/Phantom Force "ignoring Protect" were one run each.
