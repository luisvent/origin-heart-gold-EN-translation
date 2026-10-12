# blank-player-name-batch fix (2026-10-12)

**Status: disabled** (`enabled = false`), like `blank-player-name` (follow-up of D-2340). Fix id `blank-player-name-batch`
(`work/patches/blank-player-name-batch/fix.toml`), decisions D-2343..D-2345 (renumbered at merge).
Authority: user, 2026-10-12 (D-2335). Everything below was derived from the Chinese ROM; nothing from the Spanish patch.

## Cause
`{VAR:0103:n}` prints message buffer n; each script run starts with empty buffers (emulator-proved in the first fix). A script
must run `BufferPlayersName n` before the message. In 53 places it does not, on any path.

## Re-derivation (scan)
Decoder: `docs/romdata.py disasm` over all 966 members of a/0/1/2. For every entry (std-script files only through their bound
entries and their callers), a path-sensitive walk over (file, pc, buffer state, call stack): GoTo/GoToIf/Call/CallIf/CallStd
(std scripts decoded and followed inline, Return pops), all branches taken (so a path can be infeasible; "blank on every path"
is still sound). State per buffer: player name / other Buffer* fill / unknown fill. Text banks: every bank that uses the member
(file 109 serves banks 121, 446, 448). A message site (NPCMsg, GenderMsgBox) is flagged when its Chinese text reads
`{VAR:0103:n}` and buffer n is empty on a path.
Result: 132 blank (site, bank) keys; after inserting one command per site in path order (greedy, then pruned) 0 remain.
Classes:
- **A (fixed, 53 sites in 36 members):** blank on every path; no command that could fill a buffer without being decoded lies
  before the message. Vetted harmless: control flow, flags/vars, messages, menus, movement, sound, `ScrCmd_609` (emulator:
  member 196 and 169 show a blank name after it), `Buffer*` commands with a constant buffer. 8 of the 53 are scripts bound
  to no map event (103/94, 109 x4, 168/257 Route 1 kid, 741/92, 964/564): kept, they are the hack's text.
- **B (blank on some paths only):** none; every mixed site also had another fill (X) or an unknown on some path, so a blind
  insert could overwrite a real name: not touched.
- **C (not fixed, 15 sites):** an undecodable native command is on the path: member 109 at 2785/7169 (ScrCmd_102), 115 at 5832
  (GiveLoanMon), 143 x4 (ScrCmd_465 fills the Union group names: not a bug), 151 x2 (Bug-Catching Contest results:
  JudgeBugContest/BufferBugContestWinner), 736 at 1812 (ScrCmd_522/147/490: the emulator shows the name, not a bug), 738 x2
  (ScrCmd_452), 829 x2 (ScrCmd_452/453), 953 at 141 (Union Room partner name, not the player). Also excluded as unknown: 119
  and 122 (Safari/shop natives 823/741 fill their own buffer), 953 (592). Sites whose same message also reads a buffer with
  another tag (side effects) were checked: only the 143 Union texts, left alone.
- Already handled by `blank-player-name`: 111@216, 171@463/1457/1565, 733@1026 (not repeated).
The old note's "881 entry 149" (Silver, buffer 61 bytes later) is in class A here (insert before NPCMsg 5).

## Mechanism: `[[script_insert]]` (work/tools/scriptinsert.py, applied by narcpatch.py)
Member layout: header (4-byte slot per entry = offset from the slot end, then 0xFD13), commands, movement blocks
({action,count} pairs through action 0xFE) in the gaps and at the end (the last block may end after the 2-byte marker).
Everything pointing inside is relative: header slots and the last operand of GoTo, ObjectGoTo, BGGoTo, DirectionGoTo, Call,
GoToIf, CallIf, GoToIfTrainerDefeated and ApplyMovement (offset from the instruction end). `insert()`:
- inserts at a command start reachable from an entry; a target exactly at the insertion point lands on the inserted bytes;
- rewrites every header slot and every relative operand, including dead (unreachable) commands in gaps;
- keeps each movement block's position modulo 4 (the generator aligns them): zero padding goes in front of a block when the
  bytes inserted before it are not a multiple of 4 (so a member grows by 3 + 1 bytes in the usual case);
- refuses (ScriptInsertError) on bytes it cannot explain (not a reachable command, a movement block, or whole commands
  decoding to the gap end; all-zero runs are padding), on a 4-byte operand that is not known to be a relative offset or an
  immediate (ScrCmd_661, ScrCmd_705, RAM-address commands), on an insert that is not whole commands or contains a jump.
narcpatch: runs after `[[narc_bytes]]`; guards: `member_sha1` (list: the hack's member, plus member 171 after
`blank-player-name`), `expect` (the command bytes at offset); report rows carry the final offset; `verify()` checks the
inserted bytes and the member SHA-1; `[[narc_bytes]]` rows in a grown member are marked `relocated` (SHA-1 only).
fixes.py: schema, ids unique, footprint (the expect range), FIXES.md. Fix build with the fix disabled: unchanged (no entry
is selected; a report row only gains `relocated` when a script_insert touched the member).

## Tests (work/tools/test_script_insert.py)
Synthetic script (forward/backward jumps, ApplyMovement, movement block, dead code): decode equals the original plus the
insert; jump to the insertion point runs the insert; movement block content and alignment; refusals (bad offset, duplicate,
partial command, jump in the insert, broken block, 4-byte unknown operand, unexplained bytes); stage guards, idempotence
(second run refused), narc_bytes in the same member. Real ROM: all 36 patched members: the decode is the original plus exactly
the inserted commands, every relative operand reaches the same command / an identical movement block with the same alignment,
header slots hit the same commands, every member still decodes with no unexplained byte; only those 36 members change;
together with `blank-player-name` member 171 gets both and keeps its movement blocks.

## Emulator (see the report at the end of this file)

Method: DeSmuME via emu_harness `run_script(file=, index=, msg_bank=)` (no walking; the player stands near a warp/object of the
script's own map), Chinese ROM vs the Chinese ROM with the fix applied (narcpatch on the original a/0/1/2), 4 pages, then 10 more
A presses and an end frame plus the player's map/x/y/direction. 15 entries were run; in all 15 the player's position and
direction are identical before and after. The name appears (blank before, "Shishio" after) in 9 members:
168 (Route 1 kid, unbound script 5), 228 (Route 30 woman), 216 (Misty at the festival; 13.8 kB member, the pages after it and
the end frame are the same apart from animation noise), 741 (Viridian Gym entry), 855, 169, 156 (Blue on the S.S. Anne), 865
and 31 ("League Champion Shishio?"). In the other 6 runs the tagged line was not within the 4 captured pages (frames identical,
nothing proved). Member 168's end frame is a battle in both runs, one effect message apart (timing of the A presses). The
English build (rc7 plus the fix, same member hashes) was run for 168 and 228: "Oh! It's Big Bro Shishio from town!" and
"You're Shishio from Pallet Town," (blank before). `ScrCmd_609` was vetted on members 196 and 169 (blank name after it). A
probe of member 736 (Daisy) showed the name already there, so its natives fill it: left out (class C).
NOT verified: the walk-up path to each NPC (map-event conditions), most branches, the other ~40 sites, the effect of the extra
padding bytes on a real console (the movement blocks keep their 4-byte alignment).
Disk/tools: not run: `check.py --full` (needs a full build). `check.py --fast` passes registry, FIXES.md and asm-synth; its unit
test step fails here only because work/save-core/dist is not built (same on develop).
