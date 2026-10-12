# ssanne-tm-price-check: investigation (2026-10-12)

Verdict: REPRODUCED (CN ROM and rc7), fixed. Path: S.S. Anne ship shop clerk (zone 307, object 12, script 20 via run_script as the clerk stands behind a counter), menu item 2 (touch); money forced, flag 1440 cleared.

| case | CN | rc7 | rc7 + fix |
|---|---|---|---|
| $1000 | msgs 28,37,25,88 (given); reached @4349; $1000 -> $0 | same | msgs 28,38 (not enough) then the clerk's closing lines; $1000 stays; @4349 not reached |
| $5000 | $5000 -> $1000 (guide) | - | $5000 -> $1000; msgs 28,37,25,88 |

The bag count could not rise (the test save holds 99 of each TM), so the item was judged by the 'obtained' lines. Static: file 156 @4328 check 400 (0x190), @4349 sub 4000 (0xFA0); menu text bank 252 #31 "$4000"; siblings check = take (1500/1500, 800/800, 800/800).

Method: py-desmume, one case per process (case_ssanne_tm, from the retired 2026-10-06 verification recipes, git 2e6fe55^). ROMs: the untouched Chinese ROM (sha256 4807ab2c...95c8), the released rc7, and rc7 plus this fix (patched with narcpatch, the same stage as build.py).

Not verified: melonDS; a full from-source English build; the TM arriving in the bag (the test save already holds 99 of each TM, so the purchase was judged by the "obtained" lines).
