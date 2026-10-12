# fortune-ideal-price-check (fix id `fortune-ideal-price-check`)

Branch `fix/fortune-ideal-price-check`, 2026-10-12, user instruction: D-1337 no longer blocks fixes (see register). Single [[narc_bytes]] script operand edit in a/0/1/2, guarded by the whole-member SHA-1 and the expected bytes.

Fix: member 895 @232 u32 amount 300 -> 10000 (halfword 0x012C -> 0x2710). Intended value is unambiguous: text, deduction and the sister branch all say 10000.
Not part of the fix: D-1546 (love reading refusal leaves the touch menu hidden, cosmetic) and D-1547 (Goldenrod crash with both NPC groups, separate).

Tests: work/tools/test_fortune_ideal_price_check.py (member SHA-1, only the operand bytes change, instruction set and every other operand identical, new operand value, guard refuses a tampered member).

Reviewer: check the operand arithmetic against the dump (`python3 work/tools/docs/scriptdump.py <member>`), that no other branch uses the edited instruction (jump targets are unchanged: the instruction stream is the same length), and that the English text already says the corrected value.
