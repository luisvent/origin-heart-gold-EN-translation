# Romance Mail mismatch fix (fix id `romance-mail-mismatch`)

**Status: disabled** (`enabled = false`). Merged into develop on 2026-10-12 at the user's request as a separate, switched-off patch; built only on request (`build.py --only <fix-id>`), tester xdeltas exist. The standard build keeps the Chinese behaviour.

Branch `fix/romance-mail-mismatch`, 2026-10-12. Decisions D-2332 (fix), D-2333 (open question, Misty branch). Authority: user 2026-10-12, "the Chinese rom contains too many bugs.. So lets create a fix in a worktree" (lifts D-1337 for provable bugs). Replaces the "documented, not fixed" status of finding D-1398 for the Cynthia part.

## Evidence (static, from the untouched Chinese ROM, decoded with `work/tools/docs/scriptdump.py 842|843`)
Item ids: 137 Grass, 139 Bubble, 143 Heart, 144 Snow Mail. Each partner is gated by a flag: Yellow 2143, Green 2141, Misty 2142, Cynthia 2144 (file 843 dispatcher @363-418).

File 843 (2F PC love letter), check -> take:
| partner | HasItem | TakeItem | verdict |
|---|---|---|---|
| Cynthia (2144) | 144 @1318 | 143 @2438 | MISMATCH, fixed (-> 144) |
| Yellow (2143) | 143 @1345 | 143 @2836 | ok |
| Green (2141) | 137 @1372 | 137 @3234 | ok |
| Misty (2142) | 137 @1399 | 139 @3637 | mismatch, NOT fixed (judgment) |

File 842 (1F house, partner standing in the living room), check -> take of the "Rest in my room" path:
Yellow 143 @6462 -> 143 @7811 ok; Green 137 @6707 -> 137 @8075 ok; Misty 139 @6887 -> 139 @8246 ok; Cynthia 144 @7063 -> 139 @8417 MISMATCH, fixed (-> 144).

Speaker line: in the Cynthia branch with the rest option (L7063), the menu fall-through ("I'm busy") at 842@7161 is `NPCMsg 212` = "Misty: Hurry home when you're done, OK?...". Misty's identical fall-throughs use 212 (@6985, 7052, 8218); Cynthia's other fall-throughs use 218 (@7228, 8389) = "Cynthia: Hurry home when you're done. I'll be waiting for you." Fixed to 218 (copy-paste of the Misty block).

## Fix
`work/patches/romance-mail-mismatch/fix.toml`, three `[[narc_bytes]]` in a/0/1/2, guarded by whole-member SHA-1 + expected bytes:
- member 842 byte 7163: 0xD4 -> 0xDA (msg 212 -> 218)
- member 842 byte 8419: 0x8B -> 0x90 (Bubble Mail 139 -> Snow Mail 144)
- member 843 byte 2440: 0x8F -> 0x90 (Heart Mail 143 -> Snow Mail 144)
No text, no English, no new content. No other byte of any script changes.

## Not fixed: Misty love letter (843@1399/3637, D-2333)
Check 137 (Grass Mail, same item as Green) vs take 139 (Bubble Mail). In 842 Misty's rest branch checks and takes 139, which hints at 139 being hers, but changing the check makes the branch require an item nothing gives (D-1343), and changing the take to 137 would consume Green's mail. Which was intended is a judgment, so the branch stays as in the Chinese hack. Question for the user: pick (a) leave, (b) check -> 139, (c) take -> 137.

## Reachability
Snow Mail and Bubble Mail cannot be obtained in the vanilla hack (D-1343), so the corrected Cynthia branches are reachable only with an item the player has otherwise obtained (cheat/trade-in). The `flag 106` gate in 843 (@1301, @3592) also routes some paths away. The fix is therefore consistency hardening; it changes no behaviour for a normal playthrough.

## Verified / not verified
- Verified: structural decode (above); `work/tools/test_romance_mail_mismatch.py` (only 3 bytes differ, instruction set identical, check item == take item for Cynthia, other branches untouched, Misty branch unchanged, guards reject changed sources); `check.py --fast` registry and fixes-md pass.
- NOT verified: no emulator run (no controlled fixture for giving Snow Mail and entering the house with flag 2144 was built; would need a full build, disk is tight). `check.py --fast` "tests" step fails in this worktree only because `work/save-core/dist` is not built (unrelated). `work/patches/expected.toml` nontext_sha1 (and rom/xdelta hashes) NOT updated: a/0/1/2 is non-text, so the next `check.py --full --update-expected` on the merged branch must record it.
