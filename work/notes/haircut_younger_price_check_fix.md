# haircut-younger-price-check (fix id `haircut-younger-price-check`)

Branch `fix/haircut-younger-price-check`, 2026-10-12, user instruction: D-1337 no longer blocks fixes (see register). Single [[narc_bytes]] script operand edit in a/0/1/2, guarded by the whole-member SHA-1 and the expected bytes.

Fix: member 94 @2810 u32 amount 500 -> 300 (halfword 0x01F4 -> 0x012C). The player was refused at $300-$499 for a service that costs $300 (in your disfavour only, no money is lost, so lower priority).

Tests: work/tools/test_haircut_younger_price_check.py (member SHA-1, only the operand bytes change, instruction set and every other operand identical, new operand value, guard refuses a tampered member).

Reviewer: check the operand arithmetic against the dump (`python3 work/tools/docs/scriptdump.py <member>`), that no other branch uses the edited instruction (jump targets are unchanged: the instruction stream is the same length), and that the English text already says the corrected value.
