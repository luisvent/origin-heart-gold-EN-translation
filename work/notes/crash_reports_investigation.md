# Crash reports: relearner, PC wallpaper, quick Bag exit, Silph elevator (2026-10-12)

Slug `crash-reports-relearner-wallpaper`, branch `investigate/crash-reports-relearner-wallpaper`. Decisions D-2377 (relearner), D-2378 (wallpaper), D-2379 (Bag exit and elevator), all "NOT REPRODUCIBLE (harness limits)". No fix was made because nothing reproduced. ROMs: rc7 (sha256 b16f81be...710df, `scratchpad/testers/rc7.nds`) and the untouched Chinese ROM (4807ab2c...95c8, checked). DeSmuME 0.9.12 and melonDS 1.1 (aborts counted with `cpu_exceptions()`), one emulator per process. Scripts are in `work/tools/investigations/crash_reports/` (they assume the local save `work/build/memcheck/full_bag_6mons.sav`, the older English test save and an in-game save made with `mksave.py`; all git-ignored game data).

## 1. Saffron relearner (D-1589, D-2299)

- DeSmuME, `emu_saffron_retry.py` (research harness from 76295b3, patched here for the newer generator checks): real NPC, party picker, app, scroll every move, cancel, field. Gallade L100 (28 eligible moves), Gardevoir, Alolan Ninetales, Mewtwo, full party, Bag before each visit, no reset. rc7: 6/6, 679 heap checks; Chinese: 6/6, 678. No assert, NULL allocation, string overflow or heap corruption.
- Headroom (allocator hook, Gallade + Gardevoir): relearner heap 66 minimum spare 32,460 B on rc7 (biggest request 6,448 B) vs 7,366 B on the Chinese ROM; heaps 32/64/68/69 identical on both. `memcheck.py static --rom rc7`: 0 whole-bank loads left. So English banks 3x the size cannot exhaust heap 66 once msgload-all is in; D-2299's NoBigText failure needs the pre-msgload build.
- melonDS: no hooks, so the NPC cannot be started with `run_script`. The in-game save was made on DeSmuME (`mksave.py`: Gallade generated, warp to map 399 (8,6), save). On melonDS: A x8 (dialogue, Yes), touch party slot 3 (Gallade) or the generated slot, A, scroll 30x, B, A (give up), field. 5 visits (Gallade, Gardevoir, Ninetales, Mewtwo, Gallade), Bag before each: rc7 and Chinese 5/5, 0 data aborts, screenshots show the move list down to RETURN.
- Not done: develop build, NoBigText ROM (not on disk now), hardware, reporter save, actually learning a move (heart scale) and all six slots on melonDS.

## 2. PC wallpaper

- melonDS: field talk handler patched in RAM (`0x21e5d5e/66/6a`, thumb `movs r1,#251; lsls r1,r1,#3; adds r1,#2` = std script 2010) so A anywhere runs the Pokémon Center PC. Menu: A x3, DOWN, A = Organize Boxes.
- `wall2.py`: box title, Wallpaper, all 4x7 picker thumbnails (pages 0-2 normal and special, 3-4 black = locked, then wraps) and CHANGE WALLPAPER: rc7 and Chinese, 29 steps each, 0 aborts.
- `wall3.py`: live storage wallpaper array found in RAM (24 bytes `00..0f 00..07`, 0x2299adc). Values 0-23, 24-47, 32-55, 40-63, 255 downward written, all 24 boxes paged: 120 views per ROM, 0 aborts, 0 black screens; the wallpaper crop is pixel-identical between rc7 and Chinese in all 120; 0-39 draw wallpapers, higher draw a grey R tile.
- Not done: reporter's save (the claimed index 0 -> argument 206 was not seen: box 1 FOREST loaded every time), real Primo unlocks, DeSmuME sweep, hardware.

## 3. Quick Bag exit

`bagexit.py`: Route 29 wild battle, touch BAG, then B tap / held B / B mash / back touch after 0-60 frames. The first B after a touch only shows the cursor, the second leaves; always recovered; Bag reopened after every trial. 6 runs x 40 (rc7 DeSmuME x2, melonDS x2, Chinese DeSmuME, Chinese melonDS) + 3 earlier weaker-judge runs: 0 stuck/hung/aborts. Earlier 1,620-trial comparison agrees.

## 4. Silph elevator

`elev2.py`: map 445 natural entry script, var 16579 start floor, floor chosen by touch. rc7 DeSmuME 84 rides, rc7 melonDS 21; all arrive or fall back as the script (file 836) reads: flag 1208 clear = only 1F/2F stop, 1366 clear refuses 7F. 2F arrival (1208 clear) can start a trainer battle that stays responsive. 0 hangs, 0 aborts. Not done: real play progression, Chinese control, develop build, hardware.
