# Oak Pikachu line ", ," investigation (2026-10-12)

Verdict: REPRODUCED (forced script start, named player). The player's name is NOT the cause: the save's player is "Shishio" (visible in the
start menu in every screenshot) and the slot still prints blank.

Method: scratch /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/oak-comma/oak1.py, DeSmuME, map 505 (6,12), flags 1288/106 clear, run_script(file=738, index=8, msg_bank=444), A through the pages.
- Untouched Chinese ROM (sha256 4807ab2c...95c8): cn/p1.png reads "但是因为你来的实在太晚了": the {VAR:0103:0} slot between 因为 and 你 is blank, although
  the menu shows the name Shishio. So the Chinese hack itself prints nothing there; the Chinese reads fine without it, the English wrapped the blank in commas.
- Released rc7 (testers/rc7.nds): rc7/p1.png "But you were so late, , that my" (double comma), menu shows Shishio.
Cause: the ball script (a/0/1/2 member 738 entry 8) never runs BufferPlayersName 0 before NPCMsg 44 and each script run starts with empty buffers (as the
oak-starter-name-buffer note says); the buffer being empty is a script property, independent of the save's name. It is shown for every player of the Pikachu route, not only empty-named ones.
Ruled out: another bank/id (only a027/0444 has this wording); namelen and text-speed (the untouched Chinese ROM shows the same blank).
Not verified: natural walk-up to the ball on a fresh new game (script start forced via the talk handler redirect, but it is the real script and bank);
the second copy at 0x828; Discord reports not read (platform/save unknown; needs the discord script and the user's token location).
Fix: already on fix/rc8-text-fixes (patch oak-starter-name-buffer); no new fix made here.
