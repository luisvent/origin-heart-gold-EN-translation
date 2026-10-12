# haircut-younger-price-check: investigation (2026-10-12)

Verdict: REPRODUCED (CN ROM and rc7, forced state), fixed. Forced: script file 94 run from @2806 (the younger brother's money check) with money set; the party-selection UI after the check was not played (static: @2912 takes 300). Natural reachability: the Pokemon Salon younger Haircut Brother, any player with $300-$499.

| case | CN | rc7 | rc7 + fix |
|---|---|---|---|
| $400 | not-enough branch (@4562, msg 22); no service | same | passes to party selection (@2827, msg 18) |
| $299 | - | - | not-enough branch (msg 22) |

Static: bank 115 #17 "just $300", @2806 HasEnoughMoneyImmediate 500, @2912 SubMoneyImmediate 300; older brother #10 $500, @2547 check 500, @2653 take 500.

Recipe: the 2026-10-06 verification recipes (git 2e6fe55^: work/tools/emu_guide0813.py `case_fortune`/`case_ssanne_tm`, emu_hackbugs.py `case_coins`, copies in /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/old, runner /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/run.py; py-desmume, one case per process, no suite). ROMs: untouched Chinese ROM (sha256 4807ab2c...95c8), testers/rc7.nds (released rc7), rc7 + this fix (built with narcpatch via mkrom.py, /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/roms/). Raw JSON per case: /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/out/<tag>_<case>_<variant>.json, screenshots in /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/out/<tag>/.

Not verified: melonDS, a full from-source English build (the fix was applied to rc7 with narcpatch, same stage as build.py), the in-game menu path to the raised Game Corner prices, the haircut after-party flow.
