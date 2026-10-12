# blank-player-name-class-c (2026-10-12)

**Status: disabled** (`enabled = false`). Reviewed (approved); merged into develop on 2026-10-12 as a separate, switched-off patch by the user's decision. The standard build keeps the Chinese behaviour; build it with `build.py --only blank-player-name-class-c`. A tester xdelta (rc7 plus this fix) is available on request.

Fix id `blank-player-name-class-c` (`work/patches/blank-player-name-class-c/fix.toml`), follow-up of `blank-player-name-batch` (D-2343..D-2345; this note answers D-2345). Everything was derived from the Chinese ROM
(`work/rom/origin_v4.0.3_cn.nds`, sha256 4807ab2c...95c8); nothing from the Spanish patch.

## What "class C" was
`blank-player-name-batch` left 15 sites alone because an undecodable native command lies between the script start and a message
that reads `{VAR:0103:n}`: the native might fill buffer n. Method here: decode the natives in the Chinese arm9 (handler table at
0x020F793C, `work/tools` capstone, thumb), and run every path in DeSmuME (harness `emu_harness.py`: `start_at`, `h.warp`,
`run_script(file, index, msg_bank[, program])`, savestate reload between cases) on the Chinese ROM, rc7 (released English), and
the same two with the fix applied.

## Native commands (arm9 decode)
`BufferPlayersName` (op 190) = `GetMsgFormat(env, 0x10)`, read buffer id, `BufferPlayerName(msgfmt, id, player)` (0x0200bde8).
- `ScrCmd_102` (0x02041731): builds a graphics object (calls 0x205d358/0x205eae0...), takes no message format. Fills nothing.
- `ScrCmd_452` (0x020421a5): draws a window and a picture (0x0200df30/0x0200eff4), `ScrCmd_453` (0x020422cd) sets a byte to 1.
  Neither touches a message format. Fill nothing.
- `GiveLoanMon` (op 362, 0x02044a21): reads two bytes + a var and calls an overlay function (0x0225c064); no message format
  is passed. Emulator: leaves buffer 0 empty.
- `BufferBugContestWinner` (op 786) lives in overlay 1 at 0x022019ac: gets the message format (`GetMsgFormat(env, 0x10)` as above),
  the contest object and the placement byte and passes them to overlay 0x0225c14c: it fills the buffers itself.
- `JudgeBugContest` (op 787), `ScriptOverlayCmd` (op 784, group/command dispatch): contest overlay stubs.

## Verdict per site (emulator = Chinese ROM unless noted; rc7 in the last column)
| site | text | path run | Chinese ROM | rc7 | verdict |
|---|---|---|---|---|---|
| 115 @5832 (script 11, Route 36 gardener) | 130#159 "{name}拿回了比雕！" | tail of the real script from NPCMsg 157 through GiveLoanMon (party of 3; flags set up so the natural entry took another branch) | blank | " got Pidgeot back!" | **blank, fixed** |
| 738 @2030 (script 9, Oak's Pikachu offer) | 444#44 "但是因为{name}你来的实在太晚了" | whole script 9 from its entry (flags 1288/106 clear) | blank | "But you were so late, , that my" | **blank, fixed** |
| 738 @2088 (same script, other branch) | same | tail from WaitMovement, ScrCmd_452, PlayCry, NPCMsg 44 | blank | same | **blank, fixed** |
| 829 @2407 (script 11, Hitmonlee) | 525#81 "{name}得到了沙瓦郎！" | whole script 11 (flags 1876 clear, 1652 set, party 3, "Yes") | blank | " received Hitmonlee!" | **blank, fixed** |
| 829 @2543 (script 12, Hitmonchan) | 525#86 | whole script 12 (1875 clear, 1652 set) | blank | " received Hitmonchan!" | **blank, fixed** |
| 109 @2785 | 448#121 has no tag; 446#121 has one | n/a | n/a | n/a | **not a bug**: the only entry reaching it (23) is bound in text bank 448 (zone 178, coord event) where line 121 ("Gold: ...") has no `{VAR:0103}`; bank 446, which has the tag, never binds entry 23 |
| 109 @7169 | 121#17 (Eusine) has the tag; 448#17 has none | n/a | n/a | n/a | **not a bug**: entry 20 is bound in bank 448 (zone 178) where line 17 is a plain info line; bank 121 never binds entry 20 |
| 151 @901/@910 (Bug-Catching Contest results) | 239#30/#31 "Placing third is {species} {class} {name}" | static only | - | - | **not a bug (static)**: `BufferBugContestWinner n` hands the message format to the contest overlay, and the same line reads buffers 1 (species), 2 (class) and 3 (score) that no other command in the script fills, so the native fills buffer 0 (the contestant's name, who is not necessarily the player). A blind `BufferPlayersName` would overwrite a real name |

NOT verified for 151: emulator. Forcing the contest (start script 6 with a one-Pokémon party on a Saturday, then the results
script, with and without a copied tail of the results script after `BugContestAction 0`) never reached the results messages in the
harness (the contest start runs, then the "time's up" script loops; the copied tail ran without a window). Not a proof.
Re-verified without a new run: 143 (Union group names: ScrCmd_465 receives the message format, established), 953 (Union Room
partner, not the player), 736 (name shows in the emulator, established in `blank-player-name-batch`).

## Fix
Five `[[script_insert]]` entries `BE 00 00` (BufferPlayersName 0) in front of the NPCMsg: 115@0x16c8, 738@0x7ee and @0x828,
829@0x967 and @0x9ef. Same mechanism as the batch (`scriptinsert.py`, offsets and movement-block alignment relocated; guards:
member SHA-1 and expected bytes). Members 115, 738, 829 are touched by no other fix.

## Verification
- Unit test `work/tools/test_blank_player_name_class_c.py` (5 tests): registry entry, only members 115/738/829 change, each
  decode is the original plus exactly the inserted commands (same helper as the batch test: every relative operand reaches the
  same command or an identical movement block, same alignment), the inserted command sits right before the intended NPCMsg, all
  three blank-name fixes together in any order, the SHA-1 guard refuses. `test_script_insert.py` and `fixes.py check` still pass.
- Emulator, per site, on the Chinese ROM + fix and rc7 + fix: the name appears ("Shishio", the harness save's name; "Shishio got
  Pidgeot back!", "But you were so late, Shishio, that my", "Shishio received Hitmonlee!") and the final frame (pixel diff of the
  screenshot after 10 more A presses) is identical to the unpatched run (one exception: rc7's 115 tail differs in 247 of 98304 pixels, an ambient sprite animation on the route), as is the player's map/x/y/direction.
  The tail runs for 115 and 738b were rebuilt from the patched member's own commands (copied bytes of the unpatched member
  would not contain the insert).
- NOT verified: a walk-up play-through to each NPC (map-event conditions), the 738 branch choice with the natural object position,
  real hardware.

## Review leftovers of the batch (answered here)
(a) m783-1769 (0484#171, Erika's photo offer) also reads `{VAR:0200:0}`: that code is the Yes/No prompt control (the question
"要不要跟我一起合张相？" is followed by the answer boxes), not a buffer. Emulator on the Chinese ROM: the line is blank before
the insert ("哎呀！") and "哎呀Shishio！" on the batch ROM; the prompt shows in both. Nothing to fix.
(b) Unbound-script inserts. The speaker label is the player in every one: 103/122#3 (Whirl Islands, 122#4 addresses the
Champion by the same buffer), 964/338#27 (Zapdos: "{name}: Stop!", 338#22 calls the player the League Champion), 741/447#22/23,
168/312#8/9 ("Big Bro {name} from town"), 109 lines in banks 121/446/448 (Yellow "Big Bro {name}", Green "{name}, go on ahead").
All run on the Chinese ROM and the batch ROM (blank before, the name after, same position and frames). But a re-check of the
event tables by (text bank, entry) shows 9 inserts in member 109 (offsets 842, 1462, 2278, 2726, 3794, 3821, 3848, 3875, 4440,
not 4) sit in (bank, entry) combinations that no map event binds: they are dead code in the hack (the three maps share script file
109 and each binds only its own entries), harmless and not wrong. 103@100, 168@265, 741@136 and 964@572 are unbound entries
too. No batch insert is wrong; none needs to be reverted (reverting the nine member-109 ones would only shrink the footprint).
