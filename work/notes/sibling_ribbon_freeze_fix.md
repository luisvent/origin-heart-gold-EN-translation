# Weekday siblings' ribbon scene: invalid opcode 2009 (fix `sibling-ribbon-freeze`)

2026-10-12, agent sibling-ribbon-freeze. Findings D-1331 / D-1558; fix authorised by the user's statement of
2026-10-12 (D-2331). Source of truth: the untouched Chinese ROM (`work/rom/origin_v4.0.3_cn.nds`, SHA-256
4807ab2c...95c8), decoded with `romdata.disasm`.

## Cause

In `a/0/1/2` members 225 (Route 29), 232 (Route 32), 243 (Route 36), 246 (Route 37), 934 (Lake of Rage),
937 (Blackthorn) and 958 (Route 40) the ribbon hand-over reads

    GetStdMsgNaix / MsgBoxExtern / BufferMonSpeciesName / MsgBoxExtern / GiveRibbon 0x8002, 59..65
    PlayFanfare 20            4E 00 14 00
    ??? 0x07D9 (2009)         D9 07            <- stray 2 bytes
    CloseMsg                  35 00
    ReleaseAll                61 00
    End                       02 00

The hack's script command table (arm9 0x020F793C, count word at 0x020F78CC) has 843 entries (0-842).
`RunScriptContext` (arm9 0x0203F474) compares the opcode with the count; at or above it, it takes the bad-opcode
path (0x0203F4C4), asserts and sets the context mode to 0, so the script stops. CloseMsg, ReleaseAll and End never
run: the ribbon is given, but the message stays on screen and the script context stays locked (D-1558 observed
that the player can still walk, X opens the menu and SAVE works: a stuck message window, not a freeze). Nothing
jumps into the two bytes (no branch targets offset or offset+2 in any of the seven).

## Scan of the whole archive

All 966 members of `a/0/1/2` were decoded from every script header entry. Commands at or above 843 stop only
these seven places (offsets 3985, 12121, 2334, 764, 5653, 2784, 1078, all value 2009). Two other decoder stops
(member 3 at 983, member 894 at 5355) are data after an unconditional `GoTo`, not code. No other script has an
out-of-range command id. `test_sibling_ribbon_freeze.py` re-derives this.

## Fix

Seven two-byte edits, `D9 07` -> `00 00`. Command 0 is `Noop` (no arguments, two bytes; the table entry exists
and the interpreter accepts it), so size and every offset stay identical and the code that was already there
(CloseMsg, ReleaseAll, End) now runs. Ribbon id, flags, variables and messages are untouched, nothing deleted,
nothing invented (D-1500). Why Noop and not WaitFanfare (command 79, what the US script has here): WaitFanfare
would add behaviour the Chinese hack does not have (the box would wait for the jingle), and what the hack's author
meant by the bytes is unknown; Noop is the smallest change that makes the existing script valid. The fanfare then
plays while the box closes. Removing the two bytes would shift every later offset and break all jumps: rejected.
Guards: whole-member SHA-1 and the expected bytes per entry (`work/patches/sibling-ribbon-freeze/fix.toml`).

## Verification

* `work/tools/test_sibling_ribbon_freeze.py` (5 tests, needs the Chinese ROM): exactly seven members have an
  out-of-range command, at the seven offsets; after the fix only those 2 bytes per member differ; every
  previously decoded instruction is identical; the decode runs PlayFanfare 20, Noop, CloseMsg, ReleaseAll, End;
  no out-of-range command remains; both guards reject a changed source.
* Emulator, 2026-10-12 (DeSmuME; the old `guide0813 --case ribbon` recipe, taken from git 2e6fe55^ and run from a
  scratch copy of the tools; it is not in develop): the Chinese ROM versus the Chinese ROM with this fix applied
  (no English build was made). Each of the seven siblings on their weekday, var 0x4094 = 7, lead without ribbons,
  plus the arthur A/B and daily-gift control variants:
  - Chinese ROM: all seven: GiveRibbon runs, then bad opcode 2009, message window still open (as in D-1558).
  - Fixed ROM: all seven: GiveRibbon runs (same lead ribbon byte changes), no bad opcode, message window closed,
    player walks, X menu opens, SAVE prompt appears. The trace shows PlayFanfare, Noop, CloseMsg, ReleaseAll, End
    for Route 29, 37 and 40; for the other four the 80-op trace window ends in the follow-up conversation. The
    daily-gift control is identical on both ROMs.
* Not verified: a full English build (`work/patches/expected.toml` hashes are NOT updated; the merge step must run
  `check.py --full --update-expected`), a fix scenario in `emu_fixes.py` (registered as uncovered), the
  fanfare/BGM behaviour by ear. The third-party Spanish patch was used only as a location pointer.
