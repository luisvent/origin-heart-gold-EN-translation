# Saffron Dojo tutor teaches Charge instead of Volt Switch (fix `tutor-saffron-volt-switch`)

**Status: disabled** (`enabled = false`). Reviewed (approved); merged into develop on 2026-10-12 as a separate, switched-off patch by the user's decision. The standard build keeps the Chinese behaviour; build it with `build.py --only tutor-saffron-volt-switch`. A tester xdelta (rc7 plus this fix) is available on request.

Findings D-1347 (hack bug), D-2357 (this fix). Source of truth: the
untouched Chinese ROM. Investigation: `work/notes/tutor-wrong-moves_investigation.md`.

## Cause

`a/0/1/2` member 829 (Saffron Fighting Dojo, bank a027/0525 #61-#72, 'Loose, Lively, Springy, Shaky Lightning Whip',
10000 yen). After the pupil is picked, `CountMonMoves` (pc 4309) and `GoToIf LE 3` (pc 4321) split the script:

    four moves:   PokemonSummaryScreen 521 @4369, SetMonMove 521 @4437            (Volt Switch, correct)
    <= 3 moves:   BufferPartyMonNick @6363, SetMonMove (free slot) 268 @6368       (Charge)
    retry path (four moves, 'no' to the first forget prompt, then 'yes' again at pc 6641):
                  PokemonSummaryScreen 268 @6680, SetMonMove 268 @6748             (Charge)

268 is the id v3 gave Volt Switch; in v4 it is Charge (Electric status, Sp. Def +1), and Volt Switch is 521. The
tutor's text (0525 #61-#72) and the author's item sheet (3.2道具 row 554: 伏特替换, Saffron Dojo, 10000) name Volt
Switch, and the script's own main path already uses 521, so the intended move is unambiguous. This is a plain data
slip in the script, not an engine quirk: the engine's move-learning is not involved.

## Fix

Three two-byte edits `0C 01` -> `09 02` (268 -> 521) at member offsets 0x18E6, 0x1A1D, 0x1A62. Size, offsets, fee
(SubMoneyImmediate 10000) and messages stay as in the Chinese ROM; nothing is deleted or invented (D-1500). Guards:
whole-member SHA-1 `c19ec306...303e` and the expected bytes of each edit. The Counter lesson of the same script
(move 68) is untouched.

## Verification

* `work/tools/test_tutor_saffron_volt_switch.py` (7 tests, needs the Chinese ROM): the original has Volt Switch on
  the main path and Charge in exactly these three commands; the free-slot branch really is the target of the
  `GoToIf LE 3`; after the fix only six bytes differ and the decode shows 521 everywhere; guards reject changed
  sources.
* Emulator (DeSmuME, 2026-10-12): see the investigation note.

## Where a reviewer should look hardest

* The retry path (second summary, SetMonMove @6748) is not reachable from a normal run without answering 'no' twice;
  it was exercised by a custom driver (see the investigation note).
* Money: the fee is taken once on every path, as before.
