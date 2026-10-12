# fortune-ideal-price-check: investigation (2026-10-12)

Verdict: REPRODUCED (CN ROM and rc7), fixed. Natural path: walk up to the fortune-teller (Goldenrod, zone 206, object 0), menu item "My ideal Pokemon"; money, flags 2289/1617/1618/1287/1288 forced. Natural reachability of the money state: any player with $300-$9999 after the League.

| case | CN | rc7 | rc7 + fix |
|---|---|---|---|
| $5000 | msgs 0,5,6,25,88,7,8; item 247 given; $5000 -> $0; flag 1617 set | same | msgs 0,9 ("not enough"); $5000 stays; no item; flag 1617 clear |
| $20000 | (earlier run, D-1545) -> $10000 | - | msgs 0,5,6,25,88,7,8; $20000 -> $10000; item 247; flag 1617 |

Static: file 895 script 1: @228 HasEnoughMoneyImmediate 300; @313/@537/@589 SubMoneyImmediate 10000; love branch @334/@612 check 10000; texts #0, #8, #9 say $10000.

Method: py-desmume, one case per process (case_fortune, from the retired 2026-10-06 verification recipes, git 2e6fe55^). ROMs: the untouched Chinese ROM (sha256 4807ab2c...95c8), the released rc7, and rc7 plus this fix (patched with narcpatch, the same stage as build.py).

Not verified: melonDS; a full from-source English build; the love-reading branch (not part of this fix).
