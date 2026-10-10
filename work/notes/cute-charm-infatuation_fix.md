# Cute Charm: "fell in love!" without infatuation

2026-10-09. Fix: `work/patches/cute-charm-infatuation/` (overlay 14, one 8-byte region), D-2315 (user-approved
exception to D-1337). Related finding: D-2316 (the per-turn line's names are swapped; not fixed here).

## Report

A reviewer (DeSmuME, Chinese and English identical): with Cute Charm, "fell in love!" (battle_string 1#444)
prints after contact again and again (6 times in one battle on the Chinese ROM), but the per-turn infatuation
line never follows and the Pokémon keeps attacking normally. Attract and Destiny Knot infatuate correctly.

## Cause

Overlay 14 is the hack's battle engine. Each battle record (bpp) keeps its conditions in 8-byte entries at
bpp+0x38+n*8; infatuation is condition 7 at bpp+0x70. The second word's low 3 bits are the kind of the
condition's continuation (0 none, 1 turns, 2 permanent, 3 linked to a Pokémon: Pokémon id in bits 3..8).

- Ability 56 (Cute Charm) has one handler, `0x02232A70` (event 0xBB, after a hit; table of ability getters at
  `0x0224FF2C`, getter `0x02232A64`). It returns unless the holder is the target (event var 0xB), checks event
  var 0x37 and `0x0222383C`, reads the attacker (event var 0xA), and requires both genders to be known
  (`[bpp+0x239]` != 2) and different. Then it builds the continuation and calls `0x0223ACDC` (holder, 7,
  continuation, chance 0x32): that helper checks the target again, Shield Dust (0x37), contact (event var
  0x51) and the chance (`0x022264C0`: random(100) < 50), then queues the add-condition action with the
  message.
- The continuation comes from `0x02225520(out, 7, holder)`, the constructor of the status conditions 0..5
  (a jump table for 0..5; sleep gets its turn count there). Condition 7 falls to its default case: kind 0.
  No other caller passes a condition above 5 (all 20 callers checked).
- The action stores the entry and prints "fell in love!", but an entry of kind 0 is no condition: the attacker
  is never infatuated, no per-turn line, and the next successful roll passes again (the add only refuses a
  Pokémon that is already infatuated). That is the repeated message.
- Attract (`0x022255F6`, the default continuation of condition 7) and Destiny Knot (`0x0220AF0C`) use
  `0x022251D0(out, id, id)`: kind 3, linked to that Pokémon.

The gender, genderless and Oblivious checks work in the hack (below): the only fault is the continuation.

## Fix

`0x02232ACE`: `movs r1, #7; adds r2, r5, #0; bl 0x02225520` -> `adds r1, r5, #0; adds r2, r5, #0;
bl 0x022251D0` (r5 = the holder). The entry is now the one Attract writes (`0d000000 6b000000` for holder 13:
kind 3, linked to 13; Attract by Pokémon 1 writes `01000000 0b000000`, byte for byte the Cute Charm entry with
holder 1). Not changed: the 50 % chance (vanilla Gen 4 is 1/3, Gen 5+ 30 %; the hack's number stays, D-1002),
the message, every check.

## Evidence

DeSmuME, `full_bag_6mons.sav`, scripted wild battle against Nidoqueen Lv100 (Splash only; ability written
to 56), 8 turns, genders fixed by the species. Builds: `fixed` (`--no-patch` full build), `control`
(`--without cute-charm-infatuation`), the untouched Chinese ROM. "fell" = 1#444-447, "per turn" = 1#452-455,
"immob." = 1#456-459; entry = the attacker's bpp+0x70 at the end.

| Case | Chinese ROM | control | fixed |
|---|---|---|---|
| Nidoking (male) Tackle -> Cute Charm Nidoqueen | fell 1-4x, no per-turn line, Tackle every turn, entry `0d000000 00000000` | fell 3x, same | fell 1x, per-turn line every turn after, immobilised 3 of 7, entry `0d000000 6b000000` |
| Player's Cute Charm Nidoqueen (Splash), wild Nidoking Tackle | fell (445) 2x, wild entry kind 0 | fell 4x, kind 0 | fell 1x, then 453 every turn, 457 immobilised 4 of 8, until Nidoqueen fainted (the entry is then cleared, no message) |
| Nidorina (female) Tackle (same gender) | nothing | nothing | nothing |
| Nidoking with Oblivious, Tackle | rolls pass, no message, entry 0 | same | same (4 passing rolls, entry 0) |
| Nidoking Water Gun (non-contact) | nothing | nothing | nothing |
| Magnemite (genderless) Tackle | nothing | nothing | nothing |

`emu_harness.py fixes --case cute-charm-infatuation` (scenario `cutecharm`, the first row, 10 turns):
fixed `fixed` (fell 1, per turn 9, immobilised 5, entry linked to the holder), control `original` (fell 8,
per turn 0, Tackle every turn, entry kind 0).

melonDS 1.1 (headless backend, no execution hooks; `trainer.sav`, Route 1, Picnicker Amelia's female Bidoof
with Tackle/Growl; lead edited in the save to Nidoking with Cute Charm and Splash, 10 turns): the Chinese ROM
and the control store `01000000 00000000` in Bidoof's entry and Bidoof keeps attacking (the control's message
window, read from screenshots: "The foe's Bidoof fell in love!" 5 times in 10 turns); the fixed build stores
`01000000 0b000000` after the first "fell in love!" (shown once), then the per-turn line every turn and "is immobilized by
love!" on 3 of them. No
ARM9 abort on any ROM. Attract (Nidoking, same battle, DeSmuME) writes the same `01000000 0b000000` on all
three ROMs.

## Not fixed: the per-turn line (D-2316)

The per-turn line names the two Pokémon the wrong way round, on the untouched Chinese ROM too and with
Attract as well: "大牙狸让对手的(错误)Blazor着迷了！" / "The foe's (错误)Blazor fell in love with Bidoof!" (the
player's Blazor is the Attract user or Cute Charm holder, Bidoof the infatuated foe). The variant (1#454,
"foe's") follows the infatuated Pokémon, but VAR 0 gets the other one, and the name expander prints "(错误)"
("error") for the mismatch. This was already visible with Attract and Destiny Knot; Cute Charm now reaches it
too. Left as a finding for the user.

Not tested: double battles, Cute Charm's out-of-battle effect (wild gender), real hardware.
