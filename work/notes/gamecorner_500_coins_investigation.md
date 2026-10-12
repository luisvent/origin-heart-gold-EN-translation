# gamecorner-500-coins: investigation (2026-10-12)

Verdict: REPRODUCED (CN ROM and rc7, forced state), fixed. Forced: $60000, 0 coins, script run from L7575 after ScriptOverlayCmd 3 0 (the coin commands need the overlay the clerk's script loads); the raised-price menu itself needs the magnet-cheater scene and badge 14 (D-1415).

| case | CN | rc7 | rc7 + fix |
|---|---|---|---|
| L7575 '500 coins for $50000' | $60000 -> $10000, coins 0 -> 50 (GiveCoins 50) | same | $60000 -> $10000, coins 0 -> 500 (GiveCoins 500) |
| L7501 '50 coins for $5000' (control) | $-5000, +50 | - | $-5000, +50 |

Static: file 903 @7596 CheckGiveCoins 50, @7617 SubMoneyImmediate 50000, @7623 GiveCoins 50; the normal menu (L3657/L3731) gives 50 for $500 and 500 for $5000; text bank 591 #94/#95.

Method: py-desmume, one case per process (emu_hackbugs.py case_coins, from the retired 2026-10-06 verification recipes, git 2e6fe55^). ROMs: the untouched Chinese ROM (sha256 4807ab2c...95c8), the released rc7, and rc7 plus this fix (patched with narcpatch, the same stage as build.py).

Not verified: melonDS; a full from-source English build; the in-game menu path to the raised prices (it needs the magnet-cheater scene and badge 14); the script was run from the option's label with forced money.
