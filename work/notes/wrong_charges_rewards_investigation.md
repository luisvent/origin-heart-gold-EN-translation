# Wrong charges / rewards (queue rank 15), investigation 2026-10-12

Slug wrong-charges-rewards. Method: static scan of every script member in a/0/1/2 (`/private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/scan.py`: a money/coin check followed by a different charge/gift, and charges with no check; dumps with work/tools/docs/scriptdump.py), then py-desmume, one case per process, on the untouched Chinese ROM (sha256 4807ab2c...95c8), testers/rc7.nds, and rc7 + fix. Recipes: the retired 2026-10-06 verification recipes (git 2e6fe55^, emu_guide0813 / emu_hackbugs) plus `/private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/run.py`; raw JSON in /private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad/inv/wrong-charges-rewards/out.

## Processed (5 of the budget of 8)
| # | finding | verdict | where |
|---|---|---|---|
| 1 | Goldenrod fortune-teller ideal-Pokemon check $300 vs charge $10000 (D-1545) | REPRODUCED CN + rc7, FIXED | branch fix/fortune-ideal-price-check |
| 2 | S.S. Anne TM checks $400, takes $4000 | REPRODUCED CN + rc7, FIXED | fix/ssanne-tm-price-check |
| 3 | Game Corner raised price: $50000 for 50 coins, menu says 500 (D-1415) | REPRODUCED (forced state), FIXED | fix/gamecorner-500-coins |
| 4 | Younger Haircut Brother checks $500, says and takes $300 | REPRODUCED (forced state), FIXED | fix/haircut-younger-price-check |
| 5 | Sprout Tower monks take $3000/$5000/$10000 with no money check | REPRODUCED CN + rc7 ($1000 -> $0, flag 2107 set), JUDGMENT NEEDED | D-2346 here (no fix: a branch for a poor player does not exist in the Chinese) |

## Follow-ups not processed (not a loss, or other owners)
- Fortune-teller love reading refusal leaves the touch menu hidden (D-1546, cosmetic); Goldenrod entry crash (D-1547).
- Charcoal Kiln HM01: TakeItem 420 without HasItem (file 871 L1773/L1796); the player who has HM01 loses it as the line intends, players without it still get the Leek: exploit, no loss.
- Pidgeot loan returns a fixed Lv. 20 Pidgeot (separate investigation, judgment, D-2346 there).
- Six Island Shell Bell and the Route 10 Bellsprout seller: charge less / nothing (in the player's favour).
- S.S. Anne menu label says TM63 but the item is TM21 Frustration (text only, in the Chinese too).
- Post-battle Pickup rewards rejected by the Bag (D-2326, code).
- Tutor fees (file 829 dojo @6415.., Blackthorn, Rock Tunnel): checks are made up front; the wrong-move problems belong to the tutor investigations.
- Story-scene debits without a check are intended fines/robberies (files 203, 216, 845, 737); Pokeathlon (file 123) check/charge pairs differ per option and match.
- The Pokemon prizes of the Game Corner (TakeCoins 200/700/2100 etc.) check coins through GetCoinAmount compares, not decoded in detail.

## Not verified
Menu paths to the raised Game Corner prices and the haircut after-party flow; melonDS; a from-source build (fixes were applied to rc7 with narcpatch).
