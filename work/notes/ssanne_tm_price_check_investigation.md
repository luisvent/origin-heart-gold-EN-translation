# ssanne-tm-price-check: investigation (2026-10-12)

Verdict: REPRODUCED (CN ROM and rc7), fixed. Path: S.S. Anne ship shop clerk (zone 307, object 12, script 20 via run_script as the clerk stands behind a counter), menu item 2 (touch); money forced, flag 1440 cleared.

| case | CN | rc7 | rc7 + fix |
|---|---|---|---|
| $1000 | msgs 28,37,25,88 (given); reached @4349; $1000 -> $0 | same | msgs 28,38 (not enough) then the clerk's closing lines; $1000 stays; @4349 not reached |
| $5000 | $5000 -> $1000 (guide) | - | $5000 -> $1000; msgs 28,37,25,88 |

The bag count could not rise (the test save holds 99 of each TM), so the item was judged by the 'obtained' lines. Static: file 156 @4328 check 400 (0x190), @4349 sub 4000 (0xFA0); menu text bank 252 #31 "$4000"; siblings check = take (1500/1500, 800/800, 800/800).

Recipe: the 2026-10-06 verification recipes (git 2e6fe55^: work/tools/emu_guide0813.py `case_fortune`/`case_ssanne_tm`, emu_hackbugs.py `case_coins`, copies in /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/old, runner /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/run.py; py-desmume, one case per process, no suite). ROMs: untouched Chinese ROM (sha256 4807ab2c...95c8), testers/rc7.nds (released rc7), rc7 + this fix (built with narcpatch via mkrom.py, /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/roms/). Raw JSON per case: /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/out/<tag>_<case>_<variant>.json, screenshots in /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/out/<tag>/.

Not verified: melonDS, a full from-source English build (the fix was applied to rc7 with narcpatch, same stage as build.py), the in-game menu path to the raised Game Corner prices, the haircut after-party flow.
