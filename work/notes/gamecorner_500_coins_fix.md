# gamecorner-500-coins (fix id `gamecorner-500-coins`)

**Status: disabled** (`enabled = false`). Reviewed by a separate reviewer (approved with notes); merged into develop on 2026-10-12 as a separate, switched-off patch by the user's decision. The standard build keeps the Chinese behaviour; build it with `build.py --only gamecorner-500-coins`. A tester xdelta (rc7 plus this fix) is available on request.

Branch `fix/gamecorner-500-coins`, 2026-10-12, user instruction: D-1337 no longer blocks fixes (see register). Single [[narc_bytes]] script operand edit in a/0/1/2, guarded by the whole-member SHA-1 and the expected bytes.

Fix: member 903 @7600 CheckGiveCoins count 50 -> 500 and @7625 GiveCoins count 50 -> 500 (two entries; the second spans 7624-7627 because the count is odd-aligned). Money check and charge are unchanged: the price stays $50000 (ten times the normal $5000: that is the cheater penalty, text #95 says $50000). Whether 500 coins is the intended count is read from the menu text and the normal-price branch.

Tests: work/tools/test_gamecorner_500_coins.py (member SHA-1, only the operand bytes change, instruction set and every other operand identical, new operand value, guard refuses a tampered member).
