# Reports to close (reminder, 2026-10-12)

The user's reminder: close the open report channel(s) for the items below. They were investigated in the emulator harness on
2026-10-12 and could NOT be reproduced on rc7 or the untouched Chinese ROM, so they can safely be ignored on our side
(user: "all not reproducible can be safely ignored").

| Report | Register | What was tried | Why it can be closed |
|---|---|---|---|
| Saffron move-relearner black screen | D-1589 (new evidence D-2299) | Full NPC flow, 6 visits each on rc7 and the Chinese ROM (DeSmuME, no reset; Gallade L100 with 28 moves, Gardevoir, Alolan Ninetales, Mewtwo), 5 visits each on melonDS: no faults. The relearner heap has >= 32,460 B spare on rc7 (7,366 B on the Chinese ROM). | It was reported fixed, and the reporting player was not playing our ROM (user, 2026-10-12). The crash only existed in the third-party NoBigText ROM. |
| PC wallpaper load crash | branch investigate/crash-reports-relearner-wallpaper | melonDS, every picker thumbnail, wallpaper values 0-255 over all 24 boxes: 120 views per ROM, 0 aborts. | Not reproducible. |
| Quick battle-Bag exit freeze | same branch | 240 judged trials (+120 earlier) on DeSmuME and melonDS. | Not reproducible; always recovered. |
| Silph Co elevator | same branch | 84 rides on rc7 (DeSmuME) and 21 on melonDS. | Not reproducible. |
| S.S. Anne 'black screen' (Discord #bugs) and the move-learning freeze | older notes (discord-bugfix programme, 2026-10-09) | Not reproduced earlier; the move-learning freeze was judged a probable antipiracy leak. | Not reproducible. |

Limits to remember if one of these ever comes back: only rc7 was tested (not the develop build), no hardware, no reporter saves,
the Primo bonus wallpapers only via RAM values, elevator start floor set directly (no Chinese control).

**To do for the user:** close the open Discord thread/channel for the reports above (ask the reporter for a save and a platform only if they
say it still happens on rc7).
