# haircut-younger-price-check: investigation (2026-10-12)

Verdict: REPRODUCED (CN ROM and rc7, forced state), fixed. Forced: script file 94 run from @2806 (the younger brother's money check) with money set; the party-selection UI after the check was not played (static: @2912 takes 300). Natural reachability: the Pokemon Salon younger Haircut Brother, any player with $300-$499.

| case | CN | rc7 | rc7 + fix |
|---|---|---|---|
| $400 | not-enough branch (@4562, msg 22); no service | same | passes to party selection (@2827, msg 18) |
| $299 | - | - | not-enough branch (msg 22) |

Static: bank 115 #17 "just $300", @2806 HasEnoughMoneyImmediate 500, @2912 SubMoneyImmediate 300; older brother #10 $500, @2547 check 500, @2653 take 500.

Method: py-desmume, one case per process (a forced run of his script, from the retired 2026-10-06 verification recipes, git 2e6fe55^). ROMs: the untouched Chinese ROM (sha256 4807ab2c...95c8), the released rc7, and rc7 plus this fix (patched with narcpatch, the same stage as build.py).

Not verified: melonDS; a full from-source English build; the party-selection screen after the check (static check only: the deduction takes $300).
