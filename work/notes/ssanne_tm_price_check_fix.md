# ssanne-tm-price-check (fix id `ssanne-tm-price-check`)

Branch `fix/ssanne-tm-price-check`, 2026-10-12, user instruction: D-1337 no longer blocks fixes (see register). Single [[narc_bytes]] script operand edit in a/0/1/2, guarded by the whole-member SHA-1 and the expected bytes.

Fix: member 156 @4332 u32 amount 400 -> 4000 (halfword 0x0190 -> 0x0FA0).
Not changed (text, not money): menu label "TM63" while item 348 is TM21 Frustration (also in the Chinese).

Tests: work/tools/test_ssanne_tm_price_check.py (member SHA-1, only the operand bytes change, instruction set and every other operand identical, new operand value, guard refuses a tampered member).

Reviewer: check the operand arithmetic against the dump (`python3 work/tools/docs/scriptdump.py <member>`), that no other branch uses the edited instruction (jump targets are unchanged: the instruction stream is the same length), and that the English text already says the corrected value.
