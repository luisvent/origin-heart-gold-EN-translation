# fortune-ideal-price-check: investigation (2026-10-12)

Verdict: REPRODUCED (CN ROM and rc7), fixed. Natural path: walk up to the fortune-teller (Goldenrod, zone 206, object 0), menu item "My ideal Pokemon"; money, flags 2289/1617/1618/1287/1288 forced. Natural reachability of the money state: any player with $300-$9999 after the League.

| case | CN | rc7 | rc7 + fix |
|---|---|---|---|
| $5000 | msgs 0,5,6,25,88,7,8; item 247 given; $5000 -> $0; flag 1617 set | same | msgs 0,9 ("not enough"); $5000 stays; no item; flag 1617 clear |
| $20000 | (earlier run, D-1545) -> $10000 | - | msgs 0,5,6,25,88,7,8; $20000 -> $10000; item 247; flag 1617 |

Static: file 895 script 1: @228 HasEnoughMoneyImmediate 300; @313/@537/@589 SubMoneyImmediate 10000; love branch @334/@612 check 10000; texts #0, #8, #9 say $10000.

Recipe: the 2026-10-06 verification recipes (git 2e6fe55^: work/tools/emu_guide0813.py `case_fortune`/`case_ssanne_tm`, emu_hackbugs.py `case_coins`, copies in /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/old, runner /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/run.py; py-desmume, one case per process, no suite). ROMs: untouched Chinese ROM (sha256 4807ab2c...95c8), testers/rc7.nds (released rc7), rc7 + this fix (built with narcpatch via mkrom.py, /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/roms/). Raw JSON per case: /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/out/<tag>_<case>_<variant>.json, screenshots in /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/out/<tag>/.

Not verified: melonDS, a full from-source English build (the fix was applied to rc7 with narcpatch, same stage as build.py), the in-game menu path to the raised Game Corner prices, the haircut after-party flow.
