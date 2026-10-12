# overworld-pokemon-sprites: stationary Pokemon drawn as the wrong species

Reported in Discord #bugs ("Inconsistent Overworld Pokemon", "Pewter Pokemon Center Jigglypuff is Patrat"): in the Pewter
Pokemon Center the Pokemon beside the girl who talks about Jigglypuff says "Jigglypuff: Buli, buli!" and plays Jigglypuff's
cry, but is drawn as a Patrat; the Ampharos ("Amphy: Ammm-pha!") in the Olivine Lighthouse is drawn as an Audino. Branch
`fix/overworld-pokemon-sprite-mismatch`, fix `overworld-pokemon-sprites` (decisions D-2346, D-2347, D-2348 on this branch;
they are renumbered at merge).

## Reproduced

Yes: on the Chinese ROM, and on a build of develop (e21ab4b) without the fix; the fixed build draws the right species.
Harness (`work/tools/emu_overworld_sprites.py`, DeSmuME, battery save `work/build/memcheck/full_bag_6mons.sav`, clock pinned to
2026-10-09 12:00): teleport next to the Pewter Pokemon Center door (zone 475, x 8, z 18), walk out and back in so the map loads
with its objects, walk to (6, 15), screenshot the top screen. Chinese ROM and build without the fix: a Patrat stands left of the
counter, beside the man who talks about Jigglypuff; fixed build: a Jigglypuff. The screenshots are game data and are not committed.

## Root cause: a hack bug, present in the Chinese ROM

Object events name their sprite with an id. Ids below 428 are the vanilla overworld sprites. Ids 428..1894 are the hack's
following-Pokemon sprites: `data/pokemon_overworld_info.narc` has a 6-byte record per species (file index = species; first u16 =
base offset, second = alternative/female offset, third = first form offset) and the arm9 resolver (0x0206900C with 0x0206959C)
returns 428 + offset (Bulbasaur 428, Charmander 432, Jigglypuff 468, Patrat 1004).

Vanilla HeartGold's own stationary Pokemon (Jigglypuff, Machoke, Ampharos, Pikachu, Clefairy, Miltank, Kyogre, ...) use the ids
994..1046, a block in dex order (Butterfree 994, Rattata 996, Spearow 997, Pikachu 999, Clefairy 1003, Jigglypuff 1004, ...,
Machoke 1014, ..., Ampharos 1031, Aipom 1033, Miltank 1035, Kyogre 1043; read from the USA ROM's objects and PlayCry species).
The hack's table puts Generation 5 species on those ids (994 Victini, 1004 Patrat, 1014 Simisear, 1031 Audino, 1033 Gurdurr,
1043 Venipede), so every vanilla Pokemon object the authors did not retarget draws a Gen 5 Pokemon. The authors did retarget some
(the Machop objects in the Department Store basement use 495, Groudon uses 844, and Herdier 1007 and Palpitoad 1036 are exactly
those species' follower ids), so the rest are accidents, not design (D-1002 does not protect them).

## Audit

Every object event of every zone's event file (`a/0/3/2`, found through the events_bank of `bank_maps.json`) was decoded: 1586
objects with sprite id >= 428. For each object the script entry was followed (jumps included) for PlayCry species and message
speaker labels, and the sprite id was resolved to a species through the follower table. Before the fix: 992 match, 549 are silent
(no PlayCry, no speaker label) and 45 disagree. After the fix: 1029 match, 549 silent, 8 disagree (3 nicknames that fit the sprite, Victory Road 2F object 16,
and 4 cutscene actors). Silent objects were covered separately: the whole vanilla block 994..1046 was listed against the USA
ROM, so every object in it is in the table below or is Herdier/Palpitoad. Ids below 428 are vanilla's own sprites and were not
audited further. The full per-object audit (all 1586 rows) is a local scratch file, not committed.

The 45 are: 37 talking Pokemon that are fixed (listed below; 13 of the 50 fixed objects are silent and were found through the vanilla block),
3 nicknames that agree with the sprite (Megaree = Meganium, Peeko = Wingull, Exbo = Quilava), Victory Road 2F object 16 (impostor scene)
and 4 cutscene actors whose script moves several actors (Slowpoke Well Gold and Crystal, Team Rocket HQ B2F Pryce and Green; the speaker
is a person, not the object).

### Fixed (50 object events, only the 2-byte sprite id)

| Map (zone, events member) | Object | Sprite now | Species it is | Fixed to | How the species is known |
|---|---|---|---|---|---|
| Goldenrod Radio Tower 2F (186, 179) | 2 | 1004 Patrat | Jigglypuff | 468 | speaker "Jigglypuff", cry Jigglypuff |
| Goldenrod Department Store Basement (200, 193) | 1 | 1014 Simisear | Machoke | 496 | speaker "Machoke", cry Machoke |
| Goldenrod Department Store Basement (200, 193) | 2 | 1014 Simisear | Machoke | 496 | speaker "Machoke", cry Machoke |
| Goldenrod Department Store Basement (200, 193) | 3 | 1014 Simisear | Machoke | 496 | speaker "Machoke", cry Machoke |
| Route 39 Moomoo Farm House (214, 201) | 1 | 1035 Tympole | Miltank | 702 | silent object; USA ROM object with the same id / same map |
| Route 39 Moomoo Farm House (214, 201) | 3 | 1035 Tympole | Miltank | 702 | silent object; USA ROM object with the same id / same map |
| Route 39 Moomoo Farm House (214, 201) | 4 | 1035 Tympole | Miltank | 702 | silent object; USA ROM object with the same id / same map |
| Route 39 Moomoo Farm House (214, 201) | 5 | 1035 Tympole | Miltank | 702 | silent object; USA ROM object with the same id / same map |
| Route 39 Moomoo Farm House (214, 201) | 6 | 1035 Tympole | Miltank | 702 | silent object; USA ROM object with the same id / same map |
| Olivine Lighthouse Light Room (225, 211) | 1 | 1031 Audino | Ampharos | 612 | speaker "Amphy", cry Ampharos |
| Olivine Lighthouse Light Room (225, 211) | 2 | 1031 Audino | Ampharos | 612 | speaker "Amphy", cry Ampharos |
| Battle Tower (265, 240) | 8 | 999 Pignite | Pikachu | 453 | speaker "Pikachu", cry  |
| Battle Tower (265, 240) | 9 | 999 Pignite | Pikachu | 453 | speaker "Pikachu", cry Pikachu |
| Battle Frontier Battle Hall (276, 247) | 5 | 1016 Simipour | Slowbro | 509 | speaker "Slowbro", cry Slowbro |
| Pokeathlon Dome (280, 251) | 1 | 1011 Pansage | Poliwrath | 491 | silent object; USA ROM object with the same id / same map |
| Pokeathlon Dome (280, 251) | 4 | 1008 Stoutland | Meowth | 481 | speaker "Meowth", cry Meowth |
| Pokeathlon Dome (280, 251) | 6 | 1010 Liepard | Psyduck | 483 | speaker "Psyduck", cry Psyduck |
| Pokeathlon Dome (280, 251) | 7 | 1015 Panpour | Slowpoke | 508 | speaker "Slowpoke", cry Slowpoke |
| Pokeathlon Dome (280, 251) | 8 | 1006 Lillipup | Oddish | 472 | speaker "Oddish", cry Oddish |
| Pokeathlon Dome (280, 251) | 12 | 1016 Simipour | Slowbro | 509 | speaker "Slowbro", cry Slowbro |
| Pokeathlon Dome (280, 251) | 14 | 1013 Pansear | Machop | 495 | speaker "Machop", cry Machop |
| Pokeathlon Dome (280, 251) | 15 | 1017 Munna | Farfetchd | 512 | speaker "Farfetch’d", cry Farfetch’d |
| Pokeathlon Dome Interior 2F (282, 253) | 1 | 1011 Pansage | Poliwrath | 491 | silent object; USA ROM object with the same id / same map |
| Pokeathlon Dome Interior 2F (282, 253) | 15 | 996 Servine | Rattata | 447 | speaker "Rattata", cry Rattata |
| Pokeathlon Dome Interior 2F (282, 253) | 16 | 994 Victini | Butterfree | 440 | speaker "Butterfree", cry Butterfree |
| Pokeathlon Dome Interior 2F (282, 253) | 17 | 1013 Pansear | Machop | 495 | speaker "Machop", cry Machop |
| Pokeathlon Dome Interior B1F Solidarity Room (284, 255) | 4 | 996 Servine | Rattata | 447 | speaker "Rattata", cry Rattata |
| Pokeathlon Dome Interior B1F Solidarity Room (284, 255) | 6 | 1005 Watchog | Zubat | 470 | speaker "Zubat", cry Zubat |
| Pokeathlon Dome Interior B1F Trust Room (285, 256) | 5 | 1012 Simisage | Abra | 492 | speaker "Abra", cry  |
| Pokeathlon Dome Interior B1F Trust Room (285, 256) | 6 | 1027 Woobat | Dratini | 576 | speaker "Dratini", cry Dratini |
| Pokeathlon Dome Interior B1F Potential Room (286, 257) | 3 | 1018 Musharna | Dodrio | 514 | speaker "Dodrio", cry Dodrio |
| Pokemon League Entrance (300, 271) | 3 | 1012 Simisage | Abra | 492 | speaker "Abra", cry Abra |
| Pewter Pokecenter 1F (475, 428) | 5 | 1004 Patrat | Jigglypuff | 468 | speaker "Jigglypuff", cry Jigglypuff |
| Fuchsia Safari Zone Warden House (483, 436) | 1 | 1033 Gurdurr | Aipom | 621 | speaker "Aipom", cry Aipom |
| Fuchsia Safari Zone Warden House (483, 436) | 2 | 1033 Gurdurr | Aipom | 621 | speaker "Aipom", cry Aipom |
| Fuchsia Safari Zone Warden House (483, 436) | 3 | 1033 Gurdurr | Aipom | 621 | speaker "Aipom", cry Aipom |
| Viridian Northeast House (497, 449) | 2 | 996 Servine | Rattata | 447 | speaker "Bucktooth", cry Rattata |
| Viridian Northeast House (497, 449) | 3 | 997 Serperior | Spearow | 449 | speaker "Skyfiend", cry Spearow |
| Mount Moon Square Clefairy Event (513, 465) | 0 | 1003 Samurott | Clefairy | 464 | silent object; USA ROM object with the same id / same map |
| Mount Moon Square Clefairy Event (513, 465) | 1 | 1003 Samurott | Clefairy | 464 | silent object; USA ROM object with the same id / same map |
| Mount Moon Square Clefairy Event (513, 465) | 2 | 1003 Samurott | Clefairy | 464 | silent object; USA ROM object with the same id / same map |
| Mount Moon Square Clefairy Event (513, 465) | 3 | 1003 Samurott | Clefairy | 464 | silent object; USA ROM object with the same id / same map |
| Mount Moon Square Clefairy Event (513, 465) | 4 | 1003 Samurott | Clefairy | 464 | silent object; USA ROM object with the same id / same map |
| Mount Moon Square Clefairy Event (513, 465) | 5 | 1003 Samurott | Clefairy | 464 | silent object; USA ROM object with the same id / same map |
| Sinjoh Ruins Cabin (523, 475) | 3 | 1012 Simisage | Abra | 492 | speaker "Abra", cry Abra |
| Embedded Tower Kyogre Room (525, 477) | 0 | 1043 Venipede | Kyogre | 843 | speaker "Kyogre", cry Kyogre |
| Ecruteak Southwest House (85, 82) | 27 | 709 Tyranitar | Metagross | 837 | speaker "Metagross", cry Metagross |
| Goldenrod Department Store 5F (195, 188) | 27 | 709 Tyranitar | Metagross | 837 | speaker "Metagross", cry Metagross |
| Cianwood Kirks House (232, 218) | 8 | 946 Leafeon | Sylveon | 1200 | speaker "Sylveon", cry Lumineon |
| Route 21 (93, 90) | 15 | 766 Lairon | Onix | 524 | speaker "Onix", cry Crystal Onix |

Position, hide flag, script, movement and facing of every object are untouched; each entry is guarded by the member's SHA-1 and the
old bytes.

### Judgment calls (kept in the fix; D-2347, drop an entry if it was intended)

* Route 21 "Onix: Oooo-ni!" with Onix's cry (events 90, object 15): sprite 766 is Lairon; fixed to 524 (Onix). The id was chosen by
  the authors, not inherited from vanilla.
* Kirk's house "Sylveon: Syyy-veo!" (events 218, object 8): sprite 946 is Leafeon; fixed to 1200 (Sylveon). Its cry id is 457 (Lumineon).
* Second Indigo Plateau "Metagross" (events 82 and 188, object 27, hide flag 1366): sprite 709 is Tyranitar; the same script is used by
  Metagross objects drawn with 837, so fixed to 837.

### Not changed

* Herdier (Cerulean north house, 1007) and Palpitoad (Saffron Copycat house, 1036): the ids are those species' own follower sprites,
  so the authors set them on purpose and speaker and sprite agree.
* Victory Road 2F object 16 (Venusaur 430, cry Blastoise): part of the fake-Red scene; not a plain stationary Pokemon.
* Cutscene actors (Slowpoke Well Gold/Crystal, Team Rocket HQ B2F Pryce/Green).
* Pokeathlon Poliwrath (1011, two silent objects): species from the USA ROM's Pokeathlon Dome object with the same id; fixed to 491.
  Silent Moomoo Farm Miltank (1035, five objects) and Mount Moon Clefairy (1003, six objects): same method.

## Findings that are not sprite bugs (logged, not fixed; D-2348)

In 29 places the PlayCry species of a stationary Pokemon differs from its sprite and its speaker (the player hears another species).
Herdier plays #791 and Palpitoad #820, both exactly 284 above their real ids (507, 536); the others look like wrong ids. Three more
have a speaker label that disagrees with sprite and cry (Viridian "Doduo" drawn and crying as Dodrio, Pokeathlon "Pidgey" drawn and
crying as Pidgeotto, S.S. Aqua "Bulbasaur" drawn and crying as Ivysaur).

| Map (zone) | Event member / object | Sprite | Speaker | PlayCry species id |
|---|---|---|---|---|
| Route 6 (14) | 11 / 17 | 520 Cloyster | Cloyster | 467 (Magmortar) |
| Route 26 (30) | 27 / 11 | 581 Chikorita | Chikorita | 153 (Bayleef) |
| Route 32 (36) | 33 / 2 | 874 Shieldon | Shieldon | 411 (Bastiodon) |
| Route 43 (45) | 42 / 5 | 591 Sentret | Sentret | 238 (Smoochum) |
| Route 43 (45) | 42 / 7 | 591 Sentret | Sentret | 238 (Smoochum) |
| Viridian (50) | 47 / 14 | 617 Politoed | Politoed | 19 (Rattata) |
| Viridian (50) | 47 / 20 | 514 Dodrio | Doduo | 85 (Dodrio) |
| Ecruteak Dowsing Machine House (84) | 81 / 14 | 444 Pidgey | Pidgey | 172 (Pichu) |
| Slowpoke Well B1F (177) | 170 / 23 | 509 Slowbro | Slowbro | 79 (Slowpoke) |
| Slowpoke Well B1F (177) | 170 / 33 | 509 Slowbro | Slowbro | 79 (Slowpoke) |
| Slowpoke Well B1F (177) | 170 / 34 | 509 Slowbro | Slowbro | 79 (Slowpoke) |
| Slowpoke Well B1F (177) | 170 / 35 | 509 Slowbro | Slowbro | 79 (Slowpoke) |
| Goldenrod Department Store 6F (196) | 189 / 17 | 475 Paras | Paras | 212 (Scizor) |
| Cianwood Kirks House (232) | 218 / 8 | 946 Leafeon | Sylveon | 457 (Lumineon) |
| Cianwood Pokecenter 1F (236) | 222 / 8 | 659 Unown | Unown | 180 (Flaaffy) |
| Pokeathlon Dome (280) | 251 / 10 | 445 Pidgeotto | Pidgey | 17 (Pidgeotto) |
| Ss Aqua 1F Northwest Rooms (328) | 299 / 28 | 429 Ivysaur | Bulbasaur | 2 (Ivysaur) |
| Vermilion Pokemon Fan Club (362) | 319 / 9 | 602 Pichu | Pichu | 20 (Raticate) |
| Celadon Department Store 3F (372) | 329 / 8 | 920 Munchlax | Munchlax | 68 (Machamp) |
| Celadon Condominiums Roof (379) | 336 / 2 | 670 Granbull | Granbull | 670 (Floette) |
| Saffron Copycat House 1F (404) | 361 / 2 | 1036 Palpitoad | Palpitoad | 820 (Greedent) |
| Cerulean Gym (427) | 382 / 10 | 515 Seel | Seel | 118 (Goldeen) |
| Cerulean Gym (427) | 382 / 38 | 515 Seel | Seel | 118 (Goldeen) |
| Cerulean North House (429) | 384 / 9 | 1007 Herdier | Herdier | 791 (Solgaleo) |
| Ruins Of Alph Underground Hall Sinjoh Event 2 (492) | 444 / 12 | 796 Zangoose | Zangoose | 217 (Ursaring) |
| Ruins Of Alph Underground Hall Sinjoh Event 2 (492) | 444 / 14 | 736 Shiftry | Shiftry | 330 (Flygon) |
| Ruins Of Alph Underground Hall Sinjoh Event 2 (492) | 444 / 16 | 736 Shiftry | Shiftry | 330 (Flygon) |
| Pallet Town Reds House 1F (503) | 455 / 2 | 440 Butterfree | Butterfree | 327 (Spinda) |
| Pallet Town Reds House 1F (503) | 455 / 15 | 440 Butterfree | Butterfree | 327 (Spinda) |

## Proof

* `work/tools/test_overworld_pokemon_sprites.py`: pins the named objects (Pewter, Radio Tower, Lighthouse, Machoke, Pikachu, Clefairy,
  Kyogre, Metagross), that only sprite bytes change, and that after the fix no object in the whole `a/0/3/2` has an id in 994..1046
  except Herdier and Palpitoad.
* Emulator, `work/tools/emu_overworld_sprites.py --rom ROM --out DIR [--case pewter,lighthouse,machoke]`: the Pewter Pokemon Center,
  the Lighthouse light room and the Department Store basement on the Chinese ROM, on a build without the fix
  (`build.py --without overworld-pokemon-sprites`) and on the fixed build. See the run results at the end of this file.

### Emulator results (2026-10-12, DeSmuME headless, `emu_overworld_sprites.py --case pewter,lighthouse`)

Pixels in the Pokemon's tile box of the top screen (Pewter x 100-145, y 50-85; Lighthouse x 85-135, y 60-95):

| Case | Chinese ROM vs build without the fix | Build without the fix vs fixed build | What is drawn |
|---|---|---|---|
| Pewter Pokemon Center | 0 of 1575 px differ (identical) | 222 px differ | Patrat / Patrat / Jigglypuff |
| Olivine Lighthouse light room | 0 of 1750 px differ (identical) | 364 px differ | Audino / Audino / Ampharos |

Over the whole top screen the Lighthouse differs only in that box; the Pewter screens also differ elsewhere between the Chinese and the
English ROM (714 px, English-ROM text and graphics), but never inside the Pokemon's box. Screenshots (not committed, game data):
`<scratchpad>/ow/shots/pewter_cn_base_fixed.png` and `lighthouse_cn_base_fixed.png` (Chinese ROM | without fix | fixed).
The Department Store basement Machoke could not be shown: the teleport to that map crashed the emulator identically on all three ROMs
(undefined instruction at 0x05000188), so it is covered by the unit test only. Gap: the Mount Moon, Moomoo Farm, Pokeathlon, Safari warden,
Viridian, Battle Tower, Battle Hall, Sinjoh and Kyogre objects are verified from the data (test), not on screen.

The build without the fix is `build.py --without overworld-pokemon-sprites` (here: develop e21ab4b); `check.py` fast: registry, fixes-md and
asm-synth pass; ruff and tests fail only on findings that exist on develop (fixes.py E501, test_script_insert F841, test_honey_gather
needing armips on PATH). `expected.toml` is not updated (the default build's hashes move with any enabled fix; record them at merge with
`check.py --full --update-expected`).
