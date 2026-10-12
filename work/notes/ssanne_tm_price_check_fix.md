# ssanne-tm-price-check (fix id `ssanne-tm-price-check`)

**Status: disabled** (`enabled = false`). Reviewed by a separate reviewer (approved with notes); merged into develop on 2026-10-12 as a separate, switched-off patch by the user's decision. The standard build keeps the Chinese behaviour; build it with `build.py --only ssanne-tm-price-check`. A tester xdelta (rc7 plus this fix) is available on request.

Branch `fix/ssanne-tm-price-check`, 2026-10-12, user instruction: D-1337 no longer blocks fixes (see register). Single [[narc_bytes]] script operand edit in a/0/1/2, guarded by the whole-member SHA-1 and the expected bytes.

Fix: member 156 @4332 u32 amount 400 -> 4000 (halfword 0x0190 -> 0x0FA0).
Not changed (text, not money): menu label "TM63" while item 348 is TM21 Frustration (also in the Chinese).

Tests: work/tools/test_ssanne_tm_price_check.py (member SHA-1, only the operand bytes change, instruction set and every other operand identical, new operand value, guard refuses a tampered member).
