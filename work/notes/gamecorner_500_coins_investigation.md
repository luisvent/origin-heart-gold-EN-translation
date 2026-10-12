# gamecorner-500-coins: investigation (2026-10-12)

Verdict: REPRODUCED (CN ROM and rc7, forced state), fixed. Forced: $60000, 0 coins, script run from L7575 after ScriptOverlayCmd 3 0 (the coin commands need the overlay the clerk's script loads); the raised-price menu itself needs the magnet-cheater scene and badge 14 (D-1415).

| case | CN | rc7 | rc7 + fix |
|---|---|---|---|
| L7575 '500 coins for $50000' | $60000 -> $10000, coins 0 -> 50 (GiveCoins 50) | same | $60000 -> $10000, coins 0 -> 500 (GiveCoins 500) |
| L7501 '50 coins for $5000' (control) | $-5000, +50 | - | $-5000, +50 |

Static: file 903 @7596 CheckGiveCoins 50, @7617 SubMoneyImmediate 50000, @7623 GiveCoins 50; the normal menu (L3657/L3731) gives 50 for $500 and 500 for $5000; text bank 591 #94/#95.

Recipe: the 2026-10-06 verification recipes (git 2e6fe55^: work/tools/emu_guide0813.py `case_fortune`/`case_ssanne_tm`, emu_hackbugs.py `case_coins`, copies in /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/old, runner /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/run.py; py-desmume, one case per process, no suite). ROMs: untouched Chinese ROM (sha256 4807ab2c...95c8), testers/rc7.nds (released rc7), rc7 + this fix (built with narcpatch via mkrom.py, /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/roms/). Raw JSON per case: /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/out/<tag>_<case>_<variant>.json, screenshots in /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/out/<tag>/.

Not verified: melonDS, a full from-source English build (the fix was applied to rc7 with narcpatch, same stage as build.py), the in-game menu path to the raised Game Corner prices, the haircut after-party flow.
