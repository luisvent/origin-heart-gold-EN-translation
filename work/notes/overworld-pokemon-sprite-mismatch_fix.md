# Stationary overworld Pokemon: text and cry follow the drawn sprite

Reported in Discord #bugs ("Inconsistent Overworld Pokemon", "Pewter Pokemon Center Jigglypuff is Patrat"): in the Pewter Pokemon
Center the Pokemon beside the man who talks about Jigglypuff says "Jigglypuff: Buli, buli!" and plays Jigglypuff's cry, but is
drawn as a Patrat; the Ampharos ("Amphy: Ammm-pha!") in the Olivine Lighthouse is drawn as an Audino. Branch
`fix/overworld-pokemon-sprite-mismatch`. Decisions on this branch (renumber at merge): D-2349 (the rule), D-2350 (what is left,
questions), D-2346 (first approach, superseded), D-2347 and D-2348 (resolved).

## Decision (Shishio, 2026-10-12)

Do NOT change the sprites. Text (speaker labels) AND cry follow the DRAWN sprite, for every mismatched stationary overworld Pokemon,
including the judgment calls (Onix/Lairon, Sylveon/Leafeon) and all 29 cry mismatches. Precedent: the Abra text was changed to the
Simisage that is drawn ("maybe leftover from 3.x.x"). Lines that describe species-specific behaviour are not touched and are listed
as questions. Every changed object has to be looked at again when 4.1.0 releases (checklist at the end).

The first approach of this branch (fix `overworld-pokemon-sprites`: 50 sprite-id edits) is superseded: its fix.toml is kept but
`enabled = false`, and test_overworld_pokemon_sprites.py still pins its bytes.

## What changed

1. Fix `overworld-pokemon-cries` (enabled, 54 `[[narc_bytes]]`, member SHA-1 guarded): the species argument of 54 PlayCry commands in
   `a/0/1/2` is set to the national dex id of the drawn species (form halfword untouched).
2. English text, 35 strings in 18 a027 banks (status `draft`, origin `agent`, `notes` cite D-2349): 33 speaker labels change only the
   species name before the colon (the sound word after it is the Chinese one and is kept: "Simisear: Maaaa-cho!"), plus the two
   Route 21 lines described below.

### Route 21 is a translation error, not a hack mismatch

The Chinese of a027/0732#18 and #19 says 可多拉 (Lairon: the drawn sprite 766), the English said Onix. Now "Lairon, smash through Mr.
Mime's barrier with Iron Head!" and "Lairon: Laaa-ro!" (the Chinese sound), and the two PlayCry of Onix (95) in that script play
Lairon (305). Mr. Mime's cry (122) and the speaker's own "my Onix" (#21, zh 大岩蛇) are untouched.

## Every difference between the Chinese ROM and this build

Sprite = what the Chinese ROM draws (and this build still draws). "Text species" is the English speaker label (the Chinese ROM's
Chinese label names the old species; for Route 21 it already names the drawn one). A "-" means no change there. One row per object
event; objects that share a script (Route 43 Sentrets, Slowpoke Well Slowbros, Cerulean Gym Seels, Department Store Machoke, Safari
warden Aipoms, Red's house Butterfrees, Sinjoh Shiftry) share their strings and PlayCry offsets.

| Map | Event member / object | Drawn sprite | Text species (old -> new) | Cry (old -> new) | Changed strings a027 bank#id | Script member@offset of the PlayCry argument |
|---|---|---|---|---|---|---|
| Route 6 (zone 14) | ev 11 / obj 17 | 520 Cloyster | - -> - | Magmortar -> Cloyster | - | m184@0x232 |
| Route 26 (zone 30) | ev 27 / obj 11 | 581 Chikorita | - -> - | Bayleef -> Chikorita | - | m218@0x254 |
| Route 32 (zone 36) | ev 33 / obj 2 | 874 Shieldon | - -> - | Bastiodon -> Shieldon | - | m232@0x27C |
| Route 43 (zone 45) | ev 42 / obj 5 | 591 Sentret | - -> - | Smoochum -> Sentret | - | m254@0x114, m254@0x3BB |
| Route 43 (zone 45) | ev 42 / obj 7 | 591 Sentret | - -> - | Smoochum -> Sentret | - | m254@0x114, m254@0x3BB |
| Viridian (zone 50) | ev 47 / obj 14 | 617 Politoed | - -> - | Rattata -> Politoed | - | m739@0x462 |
| Viridian (zone 50) | ev 47 / obj 20 | 514 Dodrio | Doduo -> Dodrio | - -> - | 445#137 | - |
| Cianwood (zone 75) | ev 72 / obj 10 | 583 Meganium | - -> - | Corsola -> Meganium | - | m872@0x238 |
| Cianwood (zone 75) | ev 72 / obj 21 | 739 Wingull | - -> - | Heracross -> Wingull | - | m872@0x30C |
| Ecruteak Pokecenter 1F (zone 81) | ev 78 / obj 11 | 586 Quilava | - -> - | Typhlosion -> Quilava | - | m919@0x1E9 |
| Ecruteak Dowsing Machine House (zone 84) | ev 81 / obj 14 | 444 Pidgey | - -> - | Pichu -> Pidgey | - | m925@0x264 |
| Route 21 (zone 93) | ev 90 / obj 15 | 766 Lairon | Onix -> Lairon | Onix -> Lairon | 732#18, 732#19 | m957@0x106, m957@0x264 |
| Slowpoke Well B1F (zone 177) | ev 170 / obj 23 | 509 Slowbro | - -> - | Slowpoke -> Slowbro | - | m60@0x1F7 |
| Slowpoke Well B1F (zone 177) | ev 170 / obj 33 | 509 Slowbro | - -> - | Slowpoke -> Slowbro | - | m60@0x1F7 |
| Slowpoke Well B1F (zone 177) | ev 170 / obj 34 | 509 Slowbro | - -> - | Slowpoke -> Slowbro | - | m60@0x1F7 |
| Slowpoke Well B1F (zone 177) | ev 170 / obj 35 | 509 Slowbro | - -> - | Slowpoke -> Slowbro | - | m60@0x1F7 |
| Goldenrod Radio Tower 2F (zone 186) | ev 179 / obj 2 | 1004 Patrat | Jigglypuff -> Patrat | Jigglypuff -> Patrat | 64#3 | m30@0x75 |
| Goldenrod Department Store 6F (zone 196) | ev 189 / obj 17 | 475 Paras | - -> - | Scizor -> Paras | - | m901@0x535 |
| Goldenrod Department Store Basement (zone 200) | ev 193 / obj 1 | 1014 Simisear | Machoke -> Simisear | Machoke -> Simisear | 116#2 | m95@0xD7 |
| Goldenrod Department Store Basement (zone 200) | ev 193 / obj 2 | 1014 Simisear | Machoke -> Simisear | Machoke -> Simisear | 116#2 | m95@0xD7 |
| Goldenrod Department Store Basement (zone 200) | ev 193 / obj 3 | 1014 Simisear | Machoke -> Simisear | Machoke -> Simisear | 116#2 | m95@0xD7 |
| Olivine Lighthouse Light Room (zone 225) | ev 211 / obj 1 | 1031 Audino | - -> - | Ampharos -> Audino | - | m66@0xAA9, m66@0xD04, m66@0xD47 |
| Olivine Lighthouse Light Room (zone 225) | ev 211 / obj 2 | 1031 Audino | - -> - | Ampharos -> Audino | - | m66@0xAA9, m66@0xD04, m66@0xD47 |
| Cianwood Kirks House (zone 232) | ev 218 / obj 8 | 946 Leafeon | Sylveon -> Leafeon | Lumineon -> Leafeon | 568#108 | m877@0x2E3 |
| Cianwood Pokecenter 1F (zone 236) | ev 222 / obj 8 | 659 Unown | - -> - | Flaaffy -> Unown | - | m875@0x90 |
| Battle Tower (zone 265) | ev 240 / obj 8 | 999 Pignite | Pikachu -> Pignite | - -> - | 94#78 | - |
| Battle Tower (zone 265) | ev 240 / obj 9 | 999 Pignite | Pikachu -> Pignite | Pikachu -> Pignite | 94#81 | m69@0x14B1 |
| Battle Frontier Battle Hall (zone 276) | ev 247 / obj 5 | 1016 Simipour | Slowbro -> Simipour | Slowbro -> Simipour | 106#62 | m85@0xA07 |
| Pokeathlon Dome (zone 280) | ev 251 / obj 4 | 1008 Stoutland | Meowth -> Stoutland | Meowth -> Stoutland | 135#10 | m122@0x105 |
| Pokeathlon Dome (zone 280) | ev 251 / obj 6 | 1010 Liepard | Psyduck -> Liepard | Psyduck -> Liepard | 135#24 | m122@0x209 |
| Pokeathlon Dome (zone 280) | ev 251 / obj 7 | 1015 Panpour | Slowpoke -> Panpour | Slowpoke -> Panpour | 135#22 | m122@0x1D3 |
| Pokeathlon Dome (zone 280) | ev 251 / obj 8 | 1006 Lillipup | Oddish -> Lillipup | Oddish -> Lillipup | 135#8 | m122@0xD7 |
| Pokeathlon Dome (zone 280) | ev 251 / obj 10 | 445 Pidgeotto | Pidgey -> Pidgeotto | - -> - | 135#16 | - |
| Pokeathlon Dome (zone 280) | ev 251 / obj 12 | 1016 Simipour | Slowbro -> Simipour | Slowbro -> Simipour | 135#18 | m122@0x177 |
| Pokeathlon Dome (zone 280) | ev 251 / obj 14 | 1013 Pansear | Machop -> Pansear | Machop -> Pansear | 135#20 | m122@0x1A5 |
| Pokeathlon Dome (zone 280) | ev 251 / obj 15 | 1017 Munna | Farfetch’d -> Munna | Farfetch’d -> Munna | 135#23 | m122@0x1EE |
| Pokeathlon Dome Interior 2F (zone 282) | ev 253 / obj 15 | 996 Servine | Rattata -> Servine | Rattata -> Servine | 137#18, 137#19 | m124@0x6C6 |
| Pokeathlon Dome Interior 2F (zone 282) | ev 253 / obj 16 | 994 Victini | Butterfree -> Victini | Butterfree -> Victini | 137#22, 137#23 | m124@0x73A |
| Pokeathlon Dome Interior 2F (zone 282) | ev 253 / obj 17 | 1013 Pansear | Machop -> Pansear | Machop -> Pansear | 137#20, 137#21 | m124@0x700 |
| Pokeathlon Dome Interior B1F Solidarity Room (zone 284) | ev 255 / obj 4 | 996 Servine | Rattata -> Servine | Rattata -> Servine | 138#10 | m125@0x115 |
| Pokeathlon Dome Interior B1F Solidarity Room (zone 284) | ev 255 / obj 6 | 1005 Watchog | Zubat -> Watchog | Zubat -> Watchog | 138#12 | m125@0x130 |
| Pokeathlon Dome Interior B1F Trust Room (zone 285) | ev 256 / obj 5 | 1012 Simisage | Abra -> Simisage | - -> - | 139#14 | - |
| Pokeathlon Dome Interior B1F Trust Room (zone 285) | ev 256 / obj 6 | 1027 Woobat | Dratini -> Woobat | Dratini -> Woobat | 139#15 | m126@0x106 |
| Pokeathlon Dome Interior B1F Potential Room (zone 286) | ev 257 / obj 3 | 1018 Musharna | Dodrio -> Musharna | Dodrio -> Musharna | 140#24 | m127@0x422 |
| Pokemon League Entrance (zone 300) | ev 271 / obj 3 | 1012 Simisage | Abra -> Simisage | Abra -> Simisage | 514#2 | m816@0xCB |
| Ss Aqua 1F Northwest Rooms (zone 328) | ev 299 / obj 28 | 429 Ivysaur | Bulbasaur -> Ivysaur | - -> - | 255#56 | - |
| Vermilion Pokemon Fan Club (zone 362) | ev 319 / obj 9 | 602 Pichu | - -> - | Raticate -> Pichu | - | m780@0x199 |
| Celadon Department Store 3F (zone 372) | ev 329 / obj 8 | 920 Munchlax | - -> - | Machamp -> Munchlax | - | m789@0x12D |
| Celadon Condominiums Roof (zone 379) | ev 336 / obj 2 | 670 Granbull | - -> - | Floette -> Granbull | - | m797@0x7F |
| Saffron Copycat House 1F (zone 404) | ev 361 / obj 2 | 1036 Palpitoad | - -> - | Greedent -> Palpitoad | - | m837@0x98 |
| Cerulean Gym (zone 427) | ev 382 / obj 10 | 515 Seel | - -> - | Goldeen -> Seel | - | m758@0x4B7 |
| Cerulean Gym (zone 427) | ev 382 / obj 38 | 515 Seel | - -> - | Goldeen -> Seel | - | m758@0x4B7 |
| Cerulean North House (zone 429) | ev 384 / obj 9 | 1007 Herdier | - -> - | Solgaleo -> Herdier | - | m761@0x241 |
| Pewter Pokecenter 1F (zone 475) | ev 428 / obj 5 | 1004 Patrat | Jigglypuff -> Patrat | Jigglypuff -> Patrat | 456#1 | m751@0xE9 |
| Fuchsia Safari Zone Warden House (zone 483) | ev 436 / obj 1 | 1033 Gurdurr | Aipom -> Gurdurr | Aipom -> Gurdurr | 510#1 | m811@0x2F |
| Fuchsia Safari Zone Warden House (zone 483) | ev 436 / obj 2 | 1033 Gurdurr | Aipom -> Gurdurr | Aipom -> Gurdurr | 510#2 | m811@0x4A |
| Fuchsia Safari Zone Warden House (zone 483) | ev 436 / obj 3 | 1033 Gurdurr | Aipom -> Gurdurr | Aipom -> Gurdurr | 510#3 | m811@0x65 |
| Ruins Of Alph Underground Hall Sinjoh Event 2 (zone 492) | ev 444 / obj 12 | 796 Zangoose | - -> - | Ursaring -> Zangoose | - | m55@0x144 |
| Ruins Of Alph Underground Hall Sinjoh Event 2 (zone 492) | ev 444 / obj 14 | 736 Shiftry | - -> - | Flygon -> Shiftry | - | m55@0x265 |
| Ruins Of Alph Underground Hall Sinjoh Event 2 (zone 492) | ev 444 / obj 16 | 736 Shiftry | - -> - | Flygon -> Shiftry | - | m55@0x265 |
| Viridian Northeast House (zone 497) | ev 449 / obj 2 | 996 Servine | - -> - | Rattata -> Servine | - | m744@0x78 |
| Viridian Northeast House (zone 497) | ev 449 / obj 3 | 997 Serperior | - -> - | Spearow -> Serperior | - | m744@0x5D |
| Pallet Town Reds House 1F (zone 503) | ev 455 / obj 2 | 440 Butterfree | - -> - | Spinda -> Butterfree | - | m734@0x31F |
| Pallet Town Reds House 1F (zone 503) | ev 455 / obj 15 | 440 Butterfree | - -> - | Spinda -> Butterfree | - | m734@0x31F |
| Sinjoh Ruins Cabin (zone 523) | ev 475 / obj 3 | 1012 Simisage | Abra -> Simisage | Abra -> Simisage | 145#13 | m132@0x396 |

Cry ids are national dex numbers. Herdier and Palpitoad played 791 and 820 (exactly 284 above their real ids 507 and 536) and now
play 507 and 536. Nicknamed Pokemon keep their text (Amphy, Megaree, Peeko, Exbo, Bucktooth, Skyfiend) and only get the drawn species'
cry. The Lighthouse "Amphy" script is a cutscene shared by both Ampharos objects; its three PlayCry now play Audino.

## Not changed (question D-2350)

| Where | Why |
|---|---|
| Indigo Plateau hall "Metagross" object 27 (zones 85 and 195, events 82 / 188, drawn Tyranitar 709) | shares script 25 and text 608#213 / 588#213 with the correct Metagross objects (drawn 837); changing either would break those. Needs a new script for the object |
| Kyogre room (zone 525, events 477 object 0, drawn Venipede 1043) | the whole scene, its texts (a027/0147 #0-#4) and the wild battle are Kyogre; renaming it would break the story. Cry stays Kyogre |
| Victory Road 2F object 16 (Venusaur drawn, Blastoise cry, fake-Red scene) | impostor scene, not a plain stationary Pokemon |
| Pewter a027/0456#2 | the joke "When Jigglypuff sings ... fall asleep" is species-specific; now stands next to a Patrat |
| Kirk's house 568#106 | Sylveon facts, next to a Leafeon |
| Viridian 445#68 / #131 ("my Doduo") | owner's Doduo, drawn Dodrio |
| Battle Tower 94#77 ("Right, Pikachu?"), Battle Hall 106#61 ("My Slowbro") | address / own Pokemon, now a Pignite / Simipour |
| Department Store basement 116 (Machop vs Machoke economics, #0-#26) | the Machoke objects are drawn Simisear; the text is about the species |
| Abra offers 514#1 and 145#10 ("My Abra can Teleport you") | species-specific ability, now Simisage |
| Lighthouse (zone 225) text about Ampharos / Amphy | story text (Amphy is a nickname) |
| Silent objects drawn wrong: Mount Moon Clefairy event x6 (events 465, drawn Samurott 1003), Moomoo Farm x5 (events 201, Tympole 1035), Pokeathlon Dome Poliwrath x2 (events 251 / 253 obj 1, 1011) | no text or cry to change; the sprites stay as the Chinese ROM has them |

## Reproduction, root cause, proof

Root cause (a hack bug, present in the Chinese ROM): sprite ids 428..1894 are the hack's following-Pokemon sprites (id = 428 + the
base offset of the species in `data/pokemon_overworld_info.narc`, file index = species; resolver arm9 0x0206900C / 0x0206959C).
Vanilla HeartGold's stationary Pokemon use the ids 994..1046 in dex order (read from the USA ROM's objects and PlayCry species:
Jigglypuff 1004, Machoke 1014, Ampharos 1031, Kyogre 1043 ...). The hack's table puts Generation 5 species on those ids (1004 Patrat,
1014 Simisear, 1031 Audino), so every vanilla Pokemon object the authors did not retarget draws a Gen 5 Pokemon, while its text and cry
still name the vanilla species. Audit: every object event of every zone (`a/0/3/2` via `bank_maps.json` events_bank, 1586 objects with
sprite id >= 428); for each the script entry was followed (jumps included) for PlayCry species and speaker labels and the sprite id
resolved to a species. The table above is every object whose label or cry disagreed, minus the exclusions.

Reproduced on the Chinese ROM and on a build of develop (e21ab4b); proof of the final state (DeSmuME, `work/tools/emu_overworld_sprites.py
--case pewter-talk`: battery save `full_bag_6mons.sav`, clock 2026-10-09 12:00, teleport to the Pewter Pokemon Center door, out and back
in, walk to (5, 14), face the Pokemon, press A; a hook on the arm9 `bl` to the cry player inside the PlayCry command (0x020487F0)
records r1 = species):

| ROM | Text box | Cry species (PlayCry) |
|---|---|---|
| Chinese ROM | 胖丁『Buli,Buli！ | 39 (Jigglypuff) |
| build without the fix (develop) | Jigglypuff: Buli, buli! | 39 (Jigglypuff) |
| fixed build | Patrat: Buli, buli! | 504 (Patrat) |

All three show the Patrat on screen. Screenshot (game data, not committed): `<scratchpad>/ow/shots/pewter_talk_cn_base_fixed.png`.
The earlier sprite screenshots (Patrat / Audino drawn identically on the Chinese ROM and on develop) are `pewter_cn_base_fixed.png` and
`lighthouse_cn_base_fixed.png` there. Not shown on screen (data checked only): every other object; the Department Store basement
teleport crashes the emulator on all three ROMs.
Tests: `work/tools/test_overworld_pokemon_cries.py` (after the fix every stationary Pokemon's PlayCry species equals its drawn species,
over all zones, with the listed exclusions) and `test_overworld_pokemon_sprites.py` (superseded fix). `check.py` fast: registry, fixes-md,
asm-synth pass; remaining ruff / test failures exist on develop (fixes.py E501, test_script_insert F841, test_honey_gather needs armips on
PATH). `expected.toml` is not updated (record at merge with `check.py --full --update-expected`). `qa.py check` on the 19 touched banks:
0 errors; the glossary warnings are the expected ones (the Chinese still names the old species).

## Recheck when 4.1.0 releases

4.1.0 may change these sprites. Look at every object again in the game (stand next to it, talk to it, listen to the cry); if 4.1.0
draws the vanilla species again, revert that row (text: restore the old label from the table, cry: restore the old id).

- [ ] Pewter Pokemon Center: the Pokemon beside the man (Patrat now): text, cry, and 456#2 (Jigglypuff joke)
- [ ] Goldenrod Radio Tower 2F (Patrat): 64#3
- [ ] Olivine Lighthouse light room x2 (Audino now, "Amphy"): cry only; Ampharos story text
- [ ] Goldenrod Department Store basement x3 (Simisear): 116#2 and the Machop/Machoke text
- [ ] Mount Moon Square Clefairy event x6 (Samurott drawn), Moomoo Farm x5 (Tympole), Pokeathlon Poliwrath x2: silent, still wrong
- [ ] Indigo Plateau hall Metagross object 27 (Tyranitar), Kyogre room (Venipede), Victory Road 2F object 16
- [ ] every other row of the table above (map, object id, bank#id and cry offset are given there)
- [ ] Sylveon (Kirk's house), Lairon (Route 21), Herdier / Palpitoad cries, Doduo -> Dodrio, Pidgey -> Pidgeotto, Bulbasaur -> Ivysaur labels
- [ ] sound words of relabelled lines ("Simisear: Maaaa-cho!"): ask whether they should become species-specific
- [ ] the superseded sprite-id fix (`overworld-pokemon-sprites`, 50 object edits) is the alternative if 4.1.0 keeps the sprites but the user wants them corrected
