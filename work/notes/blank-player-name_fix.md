# blank-player-name fix (2026-10-12)

Fix id `blank-player-name` (`work/patches/blank-player-name/fix.toml`), decisions D-2331..D-2336 (ids may be renumbered at merge).
Authority: user, 2026-10-12 ("we are way past this point since the Chinese rom contains too many bugs.. so lets create a fix in a worktree").
A third-party patch only pointed at two locations; everything below was derived from the Chinese ROM.

## Cause
A message tag `{VAR:0103:n}` prints message-buffer n. Each script run starts with empty buffers: emulator test, a script that buffers
the name and shows it, followed by a second script whose line reads buffer 0, prints no name in the second. So a script must put
the name into exactly buffer n before the message. Three scripts do not:

1. a/0/1/2 member 111 entry 4 (map 253 Dragon's Den, Clair, object at 24,14; text bank 127): `BufferPlayersName [0]` at 213 but 127#29 reads buffer 1.
2. member 733 entry 1 (map 49 Pallet Town photographer; bank 439): NPCMsg 20 (starts with {VAR:0103:0}) at 1026, BufferPlayersName only at 1033.
3. member 171 entry 4 (map 417, Route 2, Brock; bank 315): NPCMsg 26 (reads buffer 0) at 463/1457/1565, BufferPlayersName 17 bytes later in all three branches. (Found by the scan below; same pattern as 2.)

## Fix (same size, same offsets)
- 111: byte 215 00 -> 01.
- 733: bytes 1026..1035 rotated: Buffer, NPCMsg 20, WaitButton, CloseMsg (the only jump into the block, GoToIf at 257, targets 1026 and now lands on the buffer command; NPCMsg 29 at 1036 untouched).
- 171: the same rotation (22 bytes incl. alignment) at 462, 1456, 1564; no jump target inside the moved ranges. The ApplyMovement [255, n] inside the rotated block moves 3 bytes later and its relative operand (offset from the instruction end) is lowered by 3 (1806->1803, 744->741, 704->701), so it still ends at 2284 / 2216 / 2284. (First commit 47a3db1 forgot this; fixed in the follow-up commit.)
Guards: member SHA-1 + expected bytes (narcpatch). English text: the EN strings keep the tags (0127#29 "Oh, {VAR:0103:1}, ...", 0439#20 "{VAR:0103:0}, choosing ...", 0315#26), so the EN build had the same blank (", choosing the hard road"); nothing to change in text.

## Verification
- Static: scripts decoded with romdata.disasm; unit test work/tools/test_blank_player_name.py (6 tests, bytes, structure, guards); test_narcpatch OK.
- Emulator (DeSmuME via emu_harness `run_script(file=, index=, msg_bank=)`, fresh save with flags 408,1288 set / 768,1088 clear for 733): Chinese ROM shows the line with no name (111, 733, 171 all three-page capture of the first page); the patched Chinese ROM and the patched EN build show "Shishio" (player name) in 111, 733 (CN and EN), 171 (CN). The script was started with run_script (no walking to the NPC), so object/map-event conditions were not exercised. 171, all three branches (player at 5,6 / 4,5 / 5,4 of zone 417 with run_script, 15 A presses and 200 frames): patched ROM shows the name on page 1 and the full two-screen frame after the scene is identical to the Chinese ROM in each branch (a negative control with the first, wrong patch differs). The player's coordinates read the same before and after in every run, so movement was judged by the final frame only. The EN build for 171 was not run.
- NOT verified: the walk-up play-through, other branches, 881 (see below).

## Other cases (not fixed)
Scan: all 700+ scripts of a/0/1/2, path-sensitive over every entry; a message with literal id whose Chinese text has {VAR:0103:n} and buffer n not yet filled on some path (CallStd and native ScrCmd_* treated as possibly filling, so those are excluded: Battle Frontier/Union room/shop/team scripts 122, 143, 151, 953 are not listed). Only a/0/1/2 was scanned. Emulator-confirmed blank on the unfixed ROM: 168 entry 257 (Route 1 kid "是镇上的哥", unbound entry) and 228 entry 256 (Route 30 "你是真新镇的吧？").
Types: (A) same pattern as 2 (buffer later on the same path, safe rotation): member 881 entry 149 NPCMsg 5 (Silver, 61 bytes before BufferPlayersName; rotation worked out, not emulator-verified because the line is ~30 pages in, so left out); (B) no BufferPlayersName in the entry at all, needs an inserted 3-byte command (changes size/offsets): everything else.
Ranking (reachable from a map event first; zone = event zone id; id = text-bank id):
- reachable member 22 entry@976 bank a027/0057 ids [43] zones [6]
- reachable member 25 entry@2346 bank a027/0060 ids [173, 176] zones [96]
- reachable member 31 entry@1149 bank a027/0065 ids [97] zones [187]
- reachable member 55 entry@124 bank a027/0084 ids [17] zones [492]
- reachable member 110 entry@2023 bank a027/0126 ids [89] zones [179]
- reachable member 111 entry@205 bank a027/0127 ids [29] zones [253]
- reachable member 115 entry@595 bank a027/0130 ids [159] zones [147]
- reachable member 119 entry@518 bank a027/0133 ids [104] zones [173]
- reachable member 156 entry@609 bank a027/0252 ids [13, 14] zones [307]
- reachable member 169 entry@354 bank a027/0313 ids [15] zones [10]
- reachable member 171 entry@238 bank a027/0315 ids [31, 38] zones [417]
- reachable member 171 entry@383 bank a027/0315 ids [26] zones [417]
- reachable member 196 entry@516 bank a027/0338 ids [22] zones [489]
- reachable member 196 entry@570 bank a027/0338 ids [22] zones [489]
- reachable member 216 entry@281 bank a027/0356 ids [2, 3] zones [29]
- reachable member 228 entry@256 bank a027/0369 ids [16, 17] zones [127]
- reachable member 733 entry@216 bank a027/0439 ids [20] zones [49]
- reachable member 734 entry@82 bank a027/0440 ids [33] zones [503]
- reachable member 741 entry@429 bank a027/0447 ids [22, 23] zones [496]
- reachable member 753 entry@621 bank a027/0457 ids [33] zones [471]
- reachable member 782 entry@719 bank a027/0483 ids [199, 207] zones [364]
- reachable member 783 entry@1188 bank a027/0484 ids [133] zones [55]
- reachable member 783 entry@1761 bank a027/0484 ids [171] zones [55]
- reachable member 821 entry@478 bank a027/0519 ids [70] zones [305]
- reachable member 840 entry@1768 bank a027/0535 ids [14] zones [61]
- reachable member 842 entry@668 bank a027/0537 ids [175] zones [63]
- reachable member 855 entry@78 bank a027/0549 ids [2, 3] zones [157]
- reachable member 856 entry@443 bank a027/0550 ids [55, 56] zones [135]
- reachable member 865 entry@70 bank a027/0558 ids [4] zones [136]
- reachable member 871 entry@457 bank a027/0563 ids [44] zones [164]
- reachable member 881 entry@149 bank a027/0572 ids [5] zones [385]
- reachable member 883 entry@51 bank a027/0574 ids [14] zones [137]
- reachable member 900 entry@2320 bank a027/0588 ids [23] zones [195]
- reachable member 907 entry@920 bank a027/0595 ids [16] zones [77]
- reachable member 918 entry@264 bank a027/0605 ids [8] zones [80]
- reachable member 923 entry@734 bank a027/0608 ids [23] zones [85]
- reachable member 933 entry@3351 bank a027/0616 ids [102, 103] zones [133]
- reachable member 942 entry@96 bank a027/0624 ids [7] zones [289]
- reachable member 964 entry@96 bank a027/0338 ids [22, 27, 33] zones [176]
- reachable member 964 entry@186 bank a027/0338 ids [38, 48] zones [176]
- UNBOUND   member 103 entry@94 bank a027/0122 ids [3] zones []
- UNBOUND   member 109 entry@498 bank a027/0448 ids [50, 51] zones []
- UNBOUND   member 109 entry@978 bank a027/0448 ids [91] zones []
- UNBOUND   member 109 entry@1438 bank a027/0448 ids [94, 96, 98, 100, 101, 102] zones []
- UNBOUND   member 109 entry@2264 bank a027/0448 ids [101] zones []
- UNBOUND   member 168 entry@257 bank a027/0312 ids [8, 9] zones []
- UNBOUND   member 741 entry@92 bank a027/0447 ids [22, 23] zones []
- UNBOUND   member 964 entry@564 bank a027/0338 ids [27] zones []

Notes: members 196 and 964 share bank 338 in the index (964 may be another map's copy: treat as "same text, verify"). Tags other than 0103 and the other script NARCs were not scanned. The list is a static scan: a few may be fed by native code the tools do not model.
