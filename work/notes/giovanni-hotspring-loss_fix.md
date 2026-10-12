# giovanni-hotspring-loss: fix notes (2026-10-12)

**Status: disabled** (`enabled = false`). Reviewed (approved with notes); merged into develop on 2026-10-12 as a separate, switched-off patch by the user's decision. The standard build keeps the Chinese behaviour; build it with `build.py --only giovanni-hotspring-loss`. A tester xdelta (rc7 plus this fix) is available on request.

Cause, evidence and runs: work/notes/giovanni-hotspring-and-route3_investigation.md, section 1. Decisions D-2349
(finding, resolved), D-2350 (fix).

## Change

work/patches/giovanni-hotspring-loss/fix.toml, one `[[script_insert]]` in a/0/1/2 member 844 (member SHA-1
09942d22..., guard bytes `1C 00 01 28 04 00 00` = GoToIf = -> L1890 at offset 819):

```
GoToIf != +6      1C 00 05 06 00 00 00   win (result != 0) skips the next three commands
WhiteOut          DB 00
ReleaseAll        61 00
End               02 00
GoToIf = -> L1890   the old loss branch, kept; after a win it is evaluated and does not jump
```

The win path: the new GoToIf jumps to the old GoToIf, which does not jump either (result != 0), and the script goes
on to HidePerson 7 as before. The loss path (CheckBattleWon returns 0 for a loss or a draw): the new GoToIf falls
through into the native WhiteOut block. The old GoToIf and the hot-spring block L1890 stay (L1890 is still used by
the hot spring's own stage-4 soak at offset 1783).

Tool change (strictly needed): `scriptinsert.check_block` refused every relative operand in inserted bytes. It now
accepts GoTo/GoToIf whose target stays inside the inserted block (or at its end, the command the block is put in
front of): such an offset is identical wherever the block lands. Calls, movement and jumps leaving the block are
still refused. Tests: work/tools/test_script_insert.py (refusals extended), work/tools/test_giovanni_hotspring_loss.py.

## Verified

* Unit tests (no emulator): only member 844 changes (+13 bytes, +3 zero padding for the movement blocks); every
  jump and movement target of the old member maps to the same command in the new one; the two users of L1890 stay;
  guards reject a changed member.
* Emulator (DeSmuME), on rc7 + this fix, loss forced as in the investigation (Splash Magikarp party, natural
  trigger walk): `GoToIf 819` falls to WhiteOut at 826, whiteout task, messages 43-45, ReleaseAll/End, field True on map
  501 (Pokemon Center), party healed. The same run on the Chinese ROM and on rc7 ends on a black screen.
* Win path with a RAM-forced result (the battle commands replaced in RAM by SetVar 0x800C = 1): Chinese ROM and the
  fixed build run messages 14-69 identically, no WhiteOut, final var 0x40A2 = 9, flag 2266 set, field True.

## Not verified

* A real win against Giovanni's Lv 100 double team (the forced result above is a substitute).
* melonDS / hardware (the freeze was seen in DeSmuME as a garbage-address crash; the fixed build does not reach it).
* Whether the author wanted a soak shortcut: no setting of the battle's option bytes makes it run (1,0 and 1,1 tried
  on the Chinese ROM), so it cannot be restored; whiteout is the native, working loss handling.
* After a whiteout the scene stays at var 0x40A2 = 8, so walking onto 23,139 again replays it (retry); not tested.

## Reviewer: look hardest at

1. The new `check_block` rule (a jump inside inserted bytes) and its tests.
2. The condition code 5 (= "not equal") in the inserted GoToIf, against romdata's compare table.
3. That a draw / escape cannot reach the win path wrongly (CheckBattleWon yields 0 for raw results 2 and 3).
