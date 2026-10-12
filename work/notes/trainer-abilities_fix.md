# trainer-abilities fix (rc8, Discord #bugs "Trainers with the wrong abilities")

Branch `fix/trainer-abilities`, fix `work/patches/trainer-abilities/` (kind narc, disabled at merge), decisions D-2401 (fix) and D-2402 (open question: ambiguous leftovers). Decision ids were renumbered at merge (branch D-2346/D-2347).

## Reproduced

Yes, on the Chinese ROM and on a fresh build of develop. `work/tools/emu_trainer_abilities.py` starts the battle with the game's own TrainerBattle command and hooks the party loader (arm9 0x0207285C, right after the loader applied the stored ability; r4 = the finished Pokémon). One trainer per process:

| Trainer record | Pokémon | Chinese ROM | develop build | with fix |
|---|---|---|---|---|
| 356 Lass Danni (Toxic Orb, Spore/Substitute/Leech Seed/Focus Punch) | Breloom Lv38 | 101 Technician | 101 Technician | 90 Poison Heal |
| 230 Executive Petrel (Life Orb) | Nidoking Lv40 | 38 Poison Point | 38 Poison Point | 125 Sheer Force |
| 71 Officer Felix (Toxic Orb) | Gliscor Lv65 | 52 Hyper Cutter | 52 Hyper Cutter | 90 Poison Heal |
| 984 Executive Archie (Damp Rock) | Pelipper Lv72 | 51 Keen Eye | 51 Keen Eye | 2 Drizzle |
| 450 Executive Maxie (Heat Rock) | Ninetales Lv50 | 18 Flash Fire | 18 Flash Fire | 70 Drought |

(Petrel's row: only the fixed build was run for record 230; the CN/develop value comes from the ROM bytes, which are identical.) The loader hook proves what the game builds; I did not play a turn in battle to see Poison Heal heal or Toxic Orb poison.

## Root cause

Not a regression of our build: `a/0/5/6` (trainer Pokémon), `a/0/5/5` and the personal table `a/0/0/2` are byte-identical between the Chinese ROM and our develop build (checked member by member). Each 28-byte trainer Pokémon record stores an explicit ability id (u16 at +4; the ability slot byte at +1 is not what decides, see work/notes/trainer_runtime_review.md: the CN loader applies the stored id after creation). In 54 slots the hack author left the species' default-slot ability although item and moves of the same record are built around another ability, while the author's later teams for the same characters carry the intended one (Petrel's Nidoking Lv70/87/95 have Sheer Force, his Gliscor Poison Heal, Archie's Lv88/95 Pelipper Drizzle, Maxie's Lv50/88 Ninetales Drought, Sammy's and Kiyo's Breloom Poison Heal). The author's spreadsheets (repo root `*.xlsx`) cover species data, items, moves and encounters, not trainer sets, so there is no sheet to confirm against; the evidence is the item/move pattern and the same character's other teams.

## Fix

Only the stored ability halfword of 54 slots changes (`[[narc_bytes]]`, each pinned by the member SHA-1 and the original bytes). Rules (a slot is changed only if one applies):

1. Toxic Orb / Flame Orb holder whose ability does not use the status and whose species has exactly one ability that does (Poison Heal, Guts, Flare Boost, Marvel Scale).
2. Pelipper with Damp Rock and no Rain Dance: Drizzle.
3. Ninetales or Torkoal with Heat Rock and no Sunny Day: Drought.
4. Executive Petrel's Life Orb Nidoking: Sheer Force (all his later teams use it).

| Record | Trainer | # | Pokémon | Lv | Item | Stored ability | New ability |
|---:|---|---:|---|---:|---|---|---|
| 10 | Rich Boy Howard | 4 | Drifblim | 82 | Flame Orb | Aftermath | Flare Boost |
| 56 | Team Rocket Grunt | 3 | Raticate | 64 | Flame Orb | Run Away | Guts |
| 61 | Rival Blue | 4 | Rattata | 14 | Flame Orb | Run Away | Guts |
| 71 | Officer Felix | 2 | Gliscor | 65 | Toxic Orb | Hyper Cutter | Poison Heal |
| 94 | Battle Girl Rika | 4 | Gliscor | 65 | Toxic Orb | Hyper Cutter | Poison Heal |
| 99 | Karate King Walt | 3 | Breloom | 64 | Toxic Orb | Technician | Poison Heal |
| 104 | Black Belt Ryan | 1 | Hariyama | 64 | Flame Orb | Iron Fist | Guts |
| 140 | Karate King Kazu | 3 | Breloom | 23 | Toxic Orb | Technician | Poison Heal |
| 141 | Rival Blue | 3 | Raticate | 23 | Flame Orb | Run Away | Guts |
| 155 | Sage Zhishen | 3 | Hariyama | 24 | Flame Orb | Iron Fist | Guts |
| 156 | Gentleman Norris | 1 | Raticate | 24 | Flame Orb | Run Away | Guts |
| 193 | Firebreather Chong | 1 | Ninetales | 26 | Heat Rock | Flash Fire | Drought |
| 230 | Executive Petrel | 1 | Nidoking | 40 | Life Orb | Poison Point | Sheer Force |
| 233 | Veteran Bailey | 4 | Gliscor | 65 | Toxic Orb | Hyper Cutter | Poison Heal |
| 234 | Fisherman Mick | 1 | Pelipper | 28 | Damp Rock | Keen Eye | Drizzle |
| 238 | Firebreather Stellan | 1 | Torkoal | 32 | Heat Rock | White Smoke | Drought |
| 251 | Team Rocket Grunt | 3 | Milotic | 64 | Flame Orb | Cute Charm | Marvel Scale |
| 284 | Team Rocket Grunt | 1 | Raticate | 64 | Flame Orb | Run Away | Guts |
| 304 | Battle Girl Tina | 3 | Machoke | 33 | Flame Orb | Steadfast | Guts |
| 330 | Karate King Sheldon | 2 | Machamp | 65 | Flame Orb | Steadfast | Guts |
| 335 | Shady Guy Bunta | 3 | Machamp | 50 | Flame Orb | Steadfast | Guts |
| 356 | Lass Danni | 2 | Breloom | 38 | Toxic Orb | Technician | Poison Heal |
| 364 | Fisherman Nate | 1 | Pelipper | 49 | Damp Rock | Keen Eye | Drizzle |
| 403 | Team Rocket Tanaka | 2 | Gliscor | 63 | Toxic Orb | Hyper Cutter | Poison Heal |
| 407 | Team Rocket Grunt | 2 | Pelipper | 64 | Damp Rock | Keen Eye | Drizzle |
| 433 | Shady Guy Arthur | 1 | Torkoal | 36 | Heat Rock | White Smoke | Drought |
| 445 | (unnamed) | 2 | Gliscor | 50 | Toxic Orb | Hyper Cutter | Poison Heal |
| 446 | Executive Petrel | 1 | Nidoking | 50 | Life Orb | Poison Point | Sheer Force |
| 449 | (unnamed) | 1 | Pelipper | 50 | Damp Rock | Keen Eye | Drizzle |
| 450 | Executive Maxie | 1 | Ninetales | 50 | Heat Rock | Flash Fire | Drought |
| 450 | Executive Maxie | 3 | Torkoal | 50 | Heat Rock | Shell Armor | Drought |
| 475 | Picnicker Heather | 1 | Raticate | 45 | Flame Orb | Run Away | Guts |
| 516 | Rival Blue | 2 | Rattata | 18 | Flame Orb | Run Away | Guts |
| 522 | Rival Blue | 3 | Raticate | 26 | Flame Orb | Run Away | Guts |
| 560 | Bird Keeper Finch | 2 | Gliscor | 72 | Toxic Orb | Hyper Cutter | Poison Heal |
| 573 | Team Rocket Grunt | 2 | Hariyama | 63 | Flame Orb | Iron Fist | Guts |
| 581 | Picnicker Cece | 1 | Breloom | 57 | Toxic Orb | Technician | Poison Heal |
| 584 | Youngster Elvin | 2 | Ninetales | 57 | Heat Rock | Flash Fire | Drought |
| 624 | Executive Maxie | 1 | Torkoal | 73 | Heat Rock | White Smoke | Drought |
| 625 | (unnamed) | 3 | Ninetales | 74 | Heat Rock | Flash Fire | Drought |
| 654 | Black Belt Doyle | 1 | Breloom | 72 | Toxic Orb | Effect Spore | Poison Heal |
| 663 | Sailor Stuart | 1 | Pelipper | 71 | Damp Rock | Keen Eye | Drizzle |
| 664 | Ace Trainer Macy | 4 | Gliscor | 65 | Toxic Orb | Hyper Cutter | Poison Heal |
| 690 | Super Nerd Eugene | 2 | Breloom | 58 | Toxic Orb | Technician | Poison Heal |
| 693 | Scientist Hayden | 1 | Ninetales | 59 | Heat Rock | Flash Fire | Drought |
| 698 | Super Nerd Eric | 1 | Ninetales | 62 | Heat Rock | Flash Fire | Drought |
| 741 | Sailor Thor | 1 | Pelipper | 65 | Damp Rock | Keen Eye | Drizzle |
| 829 | Karate King Seamus | 2 | Hariyama | 63 | Flame Orb | Iron Fist | Guts |
| 834 | Team Rocket Grunt | 2 | Raticate | 64 | Flame Orb | Run Away | Guts |
| 855 | Aroma Lady April | 1 | Ninetales | 62 | Heat Rock | Flash Fire | Drought |
| 856 | Guitarist Zenith | 2 | Raticate | 63 | Flame Orb | Run Away | Guts |
| 947 | Fisherman Barrett | 1 | Pelipper | 62 | Damp Rock | Keen Eye | Drizzle |
| 970 | Rival Blue | 2 | Raticate | 23 | Flame Orb | Run Away | Guts |
| 984 | Executive Archie | 1 | Pelipper | 72 | Damp Rock | Keen Eye | Drizzle |

Judgement calls worth the user's eye (all follow the rules above, but change early-game difficulty or override an explicit hidden-ability choice): Rival Blue's Flame Orb Rattata/Raticate (records 61, 141, 516, 522, 970) now have Guts; Fisherman Mick's Lv28 Pelipper now brings Drizzle; Breloom with explicit Technician + Toxic Orb (5 slots) are now Poison Heal; Maxie's Lv50 Torkoal (record 450) had an explicit Shell Armor and now has Drought. Any group can be dropped by deleting its entries from fix.toml.

## Not changed (ambiguous, D-2402)

- Espeon (Psychic Maud, record 404) Magic Bounce with Flame Orb: no ability of Espeon uses burn.
- Magcargo (record 875) Sunny Day + Heat Rock with Drought available; Relicanth (54), Steelix (51) Smooth Rock with Sandstorm; Hippowdon (Ariana, 631) Strong Jaw with fang moves and Smooth Rock; Wingull (639) Damp Rock without Drizzle.
- Cloyster/Ambipom/Heracross with 2-3 multi-hit moves but not Skill Link (a weaker set, not a broken one).
- Life Orb Nidoking/Nidoqueen/Kingler/Feraligatr/Tauros of other trainers without Sheer Force (Life Orb alone does not prove Sheer Force).
- Brutus' Machamp (610) Facade + Life Orb with No Guard.

## Proof and tests

- `work/tools/test_trainer_abilities.py`: applies the fix to the Chinese ROM's `a/0/5/6`, checks that exactly 54 slots change and only their ability halfword, that the reported slots hold the expected ability, that every new ability is one of the species' abilities, and that no Toxic/Flame Orb holder with a single status-using ability is left (the same check fails on the unpatched data).
- `python3 work/tools/check.py --full --update-expected`: tests 1104 OK (GOLDEN with armips), build PASS; `expected.toml` updated (ROM cfb60b42..., xdelta b73373f0...). ruff reports two failures that are not in my files (fixes.py:1787, test_script_insert.py:88); test_honey_gather's setUpClass errors in this worktree in fast mode only.
- Not run: `check.py --emu` (no scenario in the unified runner, listed under UNCOVERED in emu_fixes.py with the reason).
