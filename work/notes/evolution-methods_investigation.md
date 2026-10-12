# Evolution methods the hack never checks (D-1481), investigated 2026-10-12

Verdict: **REPRODUCED under forced state (Rare Candy), no fix built, JUDGMENT NEEDED** (D-2370, question D-2371).

## 1. Table (a/0/3/4, untouched Chinese ROM, 1441 members x 10 records)

Records with a method the evolution check (arm9 0x020700FC, level-up switch) never implements:

| Member | Species | Method, param | Target | Official condition | Base species obtainable? |
|---|---|---|---|---|---|
| 299 | Nosepass | 24, 0 | 476 Probopass | magnetic field | yes; record 1 is Thunder Stone (83), which works |
| 133, 1414 | Eevee | 25, 0 | 470 Leafeon | Moss Rock | yes; record 4 is Leaf Stone (85), which works |
| 674 | Pancham | 31, 32 | 675 Pangoro | Lv 32 + Dark-type in party | no source |
| 1053 | Galarian Farfetch'd | 33, 3 | 865 Sirfetch'd | 3 critical hits | no source (Farfetch'd Lv 40 works) |
| 999 | Gimmighoul | 34, 650 | 1000 Gholdengo | 999 coins | no source |
| 891 | Kubfu | 35, 1 | 892 Urshifu | scroll | no source |
| 1177 | Galarian Yamask | 36, 2 | 867 Runerigus | HP loss + arch | only by breeding Runerigus (not in game) |
| 1362 | Basculin (White-Striped) | 38, 294 | 902 Basculegion | recoil damage | no source (Basculin Lv 35 works) |
| 922, 953 | Pawmo, Rellor | 40, 1000 | 923 Pawmot, 954 Rabsca | walk 1000 steps | no source |
| 963 | Finizen | 41, 38 | 964 Palafin | Lv 38 in Union Circle | no source |

Code (jump table at 0x02070212 re-decoded 2026-10-12): methods 31-36 branch to 0x020704A4 (no evolution); methods above 37 fail
`cmp r0,#0x25` and leave the switch; 24-26 compare the evolution map code passed by the caller with the method number, and the
caller's code comes from the stub at 0x0203AAA0 (`movs r0,#0; bx lr`), so they never match. The trade context handles
5-6 only, item use 7/16/17 only.

## 2. Is anyone locked out?

No. Every affected base species is unobtainable already (work/tools/site/not_in_game.json, work/docs/pokemon_*.md "never met in
play"), so the blocked evolutions only matter if they are first given a source. Eevee and Nosepass keep their stone evolutions
(the author's species sheet lists Nosepass "Thunderstone" and Leafeon "use a Leaf Stone"). The sheet
(work/docs/author_notes/pokemon.md) has no row for Pancham, Kubfu, Gimmighoul, Pawmo, Rellor, Finizen or the
Galarian/White-Striped forms, so it cannot say which method the author meant. A level-up substitution would be invention
(D-1500).

## 3. Emulator (py-desmume, harness `emu_harness.py`, one process per case; script scratch `evo_probe.py`)

Method: save `work/build/memcheck/full_bag_6mons.sav`, species made with the hack's generator at the level before, only
Tackle, one Rare Candy / stone from the bag, A through the scenes, party record read back. ROMs: untouched Chinese v4.0.3
(sha256 4807ab2c...95c8) and released rc7. All checksums valid.

| Case | Chinese | rc7 |
|---|---|---|
| Roggenrola Lv24 -> 25 (control) | Boldore | Boldore |
| Pancham Lv31 + Umbreon in party -> 32 | stays Pancham | stays Pancham |
| Pancham Lv31, no Dark-type | stays | not run |
| Finizen Lv37 -> 38 | stays | stays |
| Pawmo Lv30 -> 31 | stays | stays |
| Rellor, Gimmighoul, Kubfu, Galarian Yamask | stay | not run |
| Galarian Farfetch'd Lv30 -> 31 | stays | stays |
| White-Striped Basculin Lv30 -> 31 | stays | stays |
| Nosepass + Thunder Stone | Probopass | Probopass |
| Eevee + Leaf Stone | (not completed) | Leafeon |

Forced state: the Pokémon are generated; they cannot be met in play. Conditions that cannot be set by candy (critical hits,
coins, scroll, arch, steps, Union Circle) were not simulated; the code reading above covers them (the switch never reaches
a handler).

## 4. Options (author's call)

- Leave as documented (guide/known-issues.md "Evolutions that cannot happen"): nothing a player can reach is blocked.
- Data-only: only the level conditions (Pancham Lv 32, Finizen Lv 38) have a plain level-up equivalent, but the other
  conditions would be dropped or invented, and none of the species can be reached; not recommended.
- Native code: smallest piece is a real map-code stub for 24-26 (Moss Rock, Ice Rock, magnetic-field maps), only useful
  if Eevee/Nosepass should evolve by location besides the stones; 31 (Dark-type in party) is a small party scan;
  33-36, 38, 40, 41 need new counters/flags that the save has no field for.

Not verified: the caller-side map code (only read from the stub); Eevee/Leaf Stone on the Chinese ROM; rc7 runs of
Rellor/Gimmighoul/Kubfu/Yamask.
