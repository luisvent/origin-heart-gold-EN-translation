# S.S. Anne party softlock: fix `ss-anne-softlock`

Status: enabled in fix.toml (the merge step decides). 2026-10-12, agent ss-anne-softlock. D-1549, D-2347.
Investigation and evidence: `work/notes/ss-anne-softlock_investigation.md`.

## Fix

One edit in `a/0/1/2` member 155 (harbor sailor, script 1), offset 152 (0x98):
`CheckFlag 235` (`20 00 EB 00`) -> `SetFlag 1440` (`1E 00 A0 05`). The replaced instruction is dead: ClearFlag 235 runs at 117
and nothing sets it before 152. The GoToIf [1, 151] after it is not taken before and after (the compare register holds the
CompareVarToValue result of offset 139). Nothing jumps into the run, same size, no offset shifts. The Soul Badge branch (new
S.S. Anne) jumps away at 145 and is untouched. Guards: whole-member SHA-1 6baec9e7... and the expected bytes.

Why here (not the speech at 156 @385): the flag must be set before the hall map loads so the guests stay hidden; a SetFlag mid-scene
leaves already-spawned objects until the map reloads (tested with an earlier variant at 156 @385: logic fine, guests linger).
Re-boarding with the party running cannot happen (the gangway sailor stays until the hijack), and after the hijack 1440 is already set.

## Behaviour change versus the Chinese ROM (author's call)

Restores the order the scripts were written for: guests and hall shop hidden until the party starts; Captain gives HM01 (253#55-59)
and sets 1424; Honey sets 1423; whichever comes second announces the party; old boy and Blue say their pre-party lines
(old boy no battle until the party). The Chinese ROM instead always plays 'the party's already started'. Judgment for the user.

## Verification (DeSmuME, individually, 2026-10-12)

Paired on CN (`run2` vs fixed CN `run6`), rc7 (`run3`) and built EN control (`run8`, font-glyphs only) vs built EN fix (`run7`,
`build.py --only ss-anne-softlock`): fix: oldboy_first, blue_first, captain_first, captain_blue_oldboy, honey_then_captain all end
with var 0x40A4 = 3, flags 1423/1424/1440 cleared by the party start, Archie's hall speech (156 script 18) runs; flag 1440 is written
once at boarding (pc 0x0204F8B6) and cleared at the party start; guests_visible 0 at boarding; HM01 given by the Captain.
Control: Honey first and Blue first end stuck (0x40A4 = 0, no trigger, gangway blocked).
Tests: `python3 work/tools/test_ss_anne_softlock.py` (6 tests: only writers/readers of 1440 over the whole archive, the replaced
instruction is dead, only 4 bytes differ, decode otherwise identical, guards).
Not verified: the party and hijack beyond Archie's speech; stuck saves; hardware; expected.toml not updated (merge step).
Reviewer: check the dead-code argument at offsets 117-156 of member 155 and that no other voyage reaches 152 with the party running.

## Review (2026-10-12): APPROVED WITH NOTES

A separate reviewer re-derived the analysis with its own decoder over every a/0/1/2 member and patched its own copy of the Chinese ROM.
- Confirmed: the only `SetFlag 1440` is 156 @6350; clears at 157 @550 and 161 @1901; checks at 157 @124 and 156 @714, 1023, 1068, 1098, 1159, all
  jumping away when the flag is clear. HM01 is given only in member 157 (81 and 191 only check for it). Boarding writes 1440 once (pc 0x204f8b6).
- The edit (member 155 offset 152: `20 00 EB 00` -> `1E 00 A0 05`) is the end of a linear run 117-156 that nothing jumps into; the compare
  register still holds the offset-139 result; the badge branch at 145 jumps away first.
- Emulator, own runs: Chinese ROM Honey-first ends stuck (0x40A4 = 0); with the fix honey_then_captain, blue_first, oldboy_first and
  captain_reboard all end with 0x40A4 = 3 and the hall trigger running; leaving and re-boarding before the party keeps flags 1423/1424/1440.
- Edge case (low): re-boarding AFTER the party has started re-sets 1440; guests and shop vanish again and the Captain offers HM01 again; the party
  still proceeds. Not compared on the Chinese ROM (harness hit 'pocket full').
- Behaviour changes for the user's decision (D-1002): see the list in `work/patches/ss-anne-softlock/fix.toml` (`what`). The user chose on 2026-10-12
  to merge this fix DISABLED so testers can judge.
- Not verified: 'Soul Badge' label for CheckBadge 4; saves already stuck; the hijack beyond Archie's speech; hardware. The harness 'honey_first'
  variant crashes on the fixed ROM (it expects an old-boy battle that no longer happens): harness limit.
- Reviewer slip: it deleted its own scratch output directory once; nothing in the repo or work/rom was affected.
