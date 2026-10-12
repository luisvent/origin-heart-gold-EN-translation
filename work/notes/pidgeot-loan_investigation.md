# Pidgeot loan investigation (2026-10-12)

Verdict: REPRODUCED, JUDGMENT NEEDED (question D-2346, related D-1392 / D-1552). No fix written.

## What happens
Viridian Forest flower lady, file 115 script 11. Lending: party menu pick (L4827) -> `ReturnLoanMon` (L7012) removes that party slot. Return after flag 2404: L5794 `GiveLoanMon 6 20 75` (L5818) adds a fresh Pidgeot from trade record 6. The queue text "replaces one of the player's Pokemon" is inaccurate: only the lent Pidgeot is destroyed. A species check (18) means no other Pokemon can be picked; the lend is refused with a one-Pokemon party; the return is refused with a full party (msg 158, L7001).

## Run
Old recipe `emu_guide0107.py` case `pidgeot` (git 8f920a6; copy in the scratchpad, symlinked rom/memcheck) on the untouched Chinese ROM and testers/rc7.nds, save full_bag_6mons.sav (6 Pokemon, Lv60 Pidgeot with Leftovers and four set moves added):
`python work/tools/emu_harness.py guide0107 --case pidgeot --lang both --rom-en testers/rc7.nds --out .../pidgeot-loan/out/run2`
Report: scratchpad/inv/pidgeot-loan/out/run2/guide01_07/report_pidgeot_both.json (screenshots beside it).

| | CN | rc7 |
|---|---|---|
| party after lend (species) | 5 left (others untouched) | same |
| messages | 149, 155, 156 then 157, 159 | same |
| returned | Pidgeot Lv20, item 0, moves 28/16/98/18, IVs 31, OT ID 1981092080 (0x761510F0), blank OT name | same |

Both ROMs: the player's own Pidgeot (level, moves, EVs, item, nickname) is gone for good. Forced state (run_from into the script, flag 2404 set); the party-menu step is the real UI.

## Why no fix
Vanilla `ReturnLoanMon`/`GiveLoanMon` serve NPC loans; the hack reuses them. Giving back the original needs new native code and a place in the save to hold a 236-byte party Pokemon (nothing free is known; Pal Park array 28 would collide with Pal Park). Whether the author wanted a replacement Pidgeot (record 6 exists for it) or the original back is the author's call.

## Not verified
Party with space (only the 6-Pokemon save was used; the code path is the same), the second-lend sequence, the real Hall of Fame flag, melonDS.
