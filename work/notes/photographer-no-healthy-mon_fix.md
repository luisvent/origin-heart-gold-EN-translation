# photographer-no-healthy-mon fix (2026-10-12)

**Status: disabled** (`enabled = false`), not merged. Fix id `photographer-no-healthy-mon`
(`work/patches/photographer-no-healthy-mon/fix.toml`), decision D-2346. Authority: user 2026-10-12 ("lets create a fix in a worktree",
D-1337 no longer blocks fixes). Investigation: `photographer-no-healthy-mon_investigation.md`.

## Cause
Cameron's Yes branch (a/0/1/2 member 733, script 7, offset 109..153) goes straight to PhotoAlbumIsFull and the photo scene
(CameronPhoto). That scene reads the party lead through GetMonData; with no Pokémon that can fight the pointer is NULL
and real hardware / melonDS abort (0x0206D84C). The Chinese ROM and rc7 are the same.

## Fix (member grows by 39 + 1 bytes)
One `[[script_insert]]` at offset 136 (the PhotoAlbumIsFull command), 39 bytes:
`CountAliveMons 0x800C,6` / `CompareVarToValue 0x800C,0` / `GoToIf !=` over the next 20 bytes / a verbatim copy of the
existing decline reply at 851 (GetStdMsgNaix, MsgBoxExtern 5, WaitButton, CloseMsg, ReleaseAll, End). Healthy party:
the jump lands on the album check and the original script runs. Otherwise the player gets the No reply and the scene ends.
CountAliveMons (opcode 357, handler 0x0204CE60) counts party members with HP > 0 that are not Eggs; 6 skips no slot.
No text added or removed.

## Tool change (scriptinsert.py)
`check_block` refused every jump in an inserted block. It now accepts a GoTo / GoToIf whose operand lands on a command
inside the block or just after it (the operand is the same wherever the block goes: nothing to relocate). Everything
else is still refused (Call, CallIf, ApplyMovement, any jump out of the block). `test_script_insert.py` covers both.
Commit f448115 on this branch; the department-store-double-one-mon branch starts from it.

## Combination with other fixes
- blank-player-name (develop) rewrites bytes 1026..1035 of the same member: the insert accepts the member before and after
  them (`member_sha1` lists both hashes); `test_photographer_no_healthy_mon.py` applies both and checks the rotation survives.
- It touches no code, so double-battle-targeting, safari-no-wild-double and every code fix are unaffected.

## Verification
Unit tests: `python3 -m unittest work/tools/test_photographer_no_healthy_mon.py work/tools/test_script_insert.py work/tools/test_narcpatch.py work/tools/test_fixes.py`.
Emulator (melonDS and DeSmuME, rc7 + fix and Chinese + fix): see the investigation note: no abort, refusal shown, scene ends,
control free; the healthy control is unchanged. Tester ROM: rc7 + this fix (not distributed; xdelta on request).
Reviewer: look hardest at the insert bytes (`work/patches/photographer-no-healthy-mon/fix.toml`) and the scriptinsert change.
