# Stationary overworld Pokemon drawn as the wrong species: the sprites follow the Chinese text and cry

Reported in Discord #bugs ("Inconsistent Overworld Pokemon", "Pewter Pokemon Center Jigglypuff is Patrat"): in the Pewter Pokemon
Center the Pokemon beside the man who talks about Jigglypuff says "Jigglypuff: Buli, buli!" and plays Jigglypuff's cry, but is drawn as
a Patrat; the Ampharos in the Olivine Lighthouse is drawn as an Audino. Branch `fix/overworld-pokemon-sprite-mismatch`. Decisions
(renumber at merge): D-2349 (the rule), D-2350 (left alone), D-2351 (Route 21 finding), D-2346 / D-2347 (sprite approach, restored).

## Decision history (Shishio, 2026-10-12)

1. First: change the sprite ids (fix `overworld-pokemon-sprites`, commit ab420ca).
2. Then: do not change sprites, text and cry follow the sprite (fix `overworld-pokemon-cries`, 35 English strings, commit de59b87).
3. Final, after a user report: the text and cry were right and the sprites are wrong. Sprites follow the Chinese text and cry; text and
   cries stay exactly as the Chinese ROM has them. This commit restores ruling 1 (re-enabled and re-scoped) and disables ruling 2
   (`overworld-pokemon-cries` kept, `enabled = false`; its 35 string edits reverted, nothing deleted).

Rules used: (1) sprite = the species the Chinese speaker label and the cry agree on; (2) where label and cry disagree the Chinese label
decides and the object is listed "needs user check"; where the text itself is ambiguous (nickname, sound word that fits two species)
or silent the sprite is left; (3) species-neutral objects are only changed when cry and/or dialogue prove the vanilla species.

## What changed in this build compared with the Chinese ROM

* Fix `overworld-pokemon-sprites` (enabled, 37 `[[narc_bytes]]` in `a/0/3/2`, member SHA-1 guarded): only the 2-byte sprite id of 37
  object events changes (table below). Position, flag, script, movement, facing, text and cries are the Chinese ROM's.
* English text: exactly one correction, a027/0732#18 "Onix, smash through Mr. Mime's barrier ..." -> "Lairon, ..." and #19 "Onix: Oooo-ni!"
  -> "Lairon: Laaa-ro!" (Route 21): the Chinese says 可多拉 = Lairon and the sprite is already Lairon; the English was a mistranslation
  (D-1496 style, text only, from the Chinese; the sound word is the Chinese 'Laaa-ro'). The two PlayCry of that script still play Onix
  (95) as in the Chinese ROM: finding D-2351.
* Nothing else (no other string, no cry, no other sprite).

## The 37 sprite changes (the list to re-verify visually for 4.1.0)

Sprite column: what the Chinese ROM draws -> what this build draws. "Cry" is the species the script plays (unchanged).

| Map | Event member / object | Sprite: Chinese ROM -> now | Chinese label (a027 bank#id) | English label | Cry species (unchanged) | Events member@offset of the sprite id | Note |
|---|---|---|---|---|---|---|---|
| Goldenrod Radio Tower 2F (zone 186) | ev 179 / obj 2 | 1004 Patrat -> 468 Jigglypuff | 胖丁 (64#3) | Jigglypuff | Jigglypuff | m179@0x86 |  |
| Goldenrod Department Store Basement (zone 200) | ev 193 / obj 1 | 1014 Simisear -> 496 Machoke | 豪力 (116#2) | Machoke | Machoke | m193@0x3E |  |
| Goldenrod Department Store Basement (zone 200) | ev 193 / obj 2 | 1014 Simisear -> 496 Machoke | 豪力 (116#2) | Machoke | Machoke | m193@0x5E |  |
| Goldenrod Department Store Basement (zone 200) | ev 193 / obj 3 | 1014 Simisear -> 496 Machoke | 豪力 (116#2) | Machoke | Machoke | m193@0x7E |  |
| Olivine Lighthouse Light Room (zone 225) | ev 211 / obj 1 | 1031 Audino -> 612 Ampharos | 小明 (92#27) | Amphy | Ampharos | m211@0x2A |  |
| Olivine Lighthouse Light Room (zone 225) | ev 211 / obj 2 | 1031 Audino -> 612 Ampharos | 小明 (92#27) | Amphy | Ampharos | m211@0x4A |  |
| Battle Tower (zone 265) | ev 240 / obj 8 | 999 Pignite -> 453 Pikachu | 皮卡丘 (94#78) | Pikachu | - | m240@0x146 |  |
| Battle Tower (zone 265) | ev 240 / obj 9 | 999 Pignite -> 453 Pikachu | 皮卡丘 (94#81) | Pikachu | Pikachu | m240@0x166 |  |
| Battle Frontier Battle Hall (zone 276) | ev 247 / obj 5 | 1016 Simipour -> 509 Slowbro | 呆河马 (106#62) | Slowbro | Slowbro | m247@0xBE |  |
| Pokeathlon Dome (zone 280) | ev 251 / obj 4 | 1008 Stoutland -> 481 Meowth | 喵喵 (135#10) | Meowth | Meowth | m251@0x116 |  |
| Pokeathlon Dome (zone 280) | ev 251 / obj 6 | 1010 Liepard -> 483 Psyduck | 可达鸭 (135#24) | Psyduck | Psyduck | m251@0x156 |  |
| Pokeathlon Dome (zone 280) | ev 251 / obj 7 | 1015 Panpour -> 508 Slowpoke | 呆呆兽 (135#22) | Slowpoke | Slowpoke | m251@0x176 |  |
| Pokeathlon Dome (zone 280) | ev 251 / obj 8 | 1006 Lillipup -> 472 Oddish | 走路草 (135#8) | Oddish | Oddish | m251@0x196 |  |
| Pokeathlon Dome (zone 280) | ev 251 / obj 12 | 1016 Simipour -> 509 Slowbro | 呆河马 (135#18) | Slowbro | Slowbro | m251@0x216 |  |
| Pokeathlon Dome (zone 280) | ev 251 / obj 14 | 1013 Pansear -> 495 Machop | 腕力 (135#20) | Machop | Machop | m251@0x256 |  |
| Pokeathlon Dome (zone 280) | ev 251 / obj 15 | 1017 Munna -> 512 Farfetchd | 大葱鸭 (135#23) | Farfetch’d | Farfetch’d | m251@0x276 |  |
| Pokeathlon Dome Interior 2F (zone 282) | ev 253 / obj 15 | 996 Servine -> 447 Rattata | 小拉达 (137#19) | Rattata | Rattata | m253@0x1EA |  |
| Pokeathlon Dome Interior 2F (zone 282) | ev 253 / obj 16 | 994 Victini -> 440 Butterfree | 巴大蝴 (137#23) | Butterfree | Butterfree | m253@0x20A |  |
| Pokeathlon Dome Interior 2F (zone 282) | ev 253 / obj 17 | 1013 Pansear -> 495 Machop | 腕力 (137#21) | Machop | Machop | m253@0x22A |  |
| Pokeathlon Dome Interior B1F Solidarity Room (zone 284) | ev 255 / obj 4 | 996 Servine -> 447 Rattata | 小拉达 (138#10) | Rattata | Rattata | m255@0x166 |  |
| Pokeathlon Dome Interior B1F Solidarity Room (zone 284) | ev 255 / obj 6 | 1005 Watchog -> 470 Zubat | 超音蝠 (138#12) | Zubat | Zubat | m255@0x1A6 |  |
| Pokeathlon Dome Interior B1F Trust Room (zone 285) | ev 256 / obj 5 | 1012 Simisage -> 492 Abra | 凯西 (139#14) | Abra | - | m256@0x1AE |  |
| Pokeathlon Dome Interior B1F Trust Room (zone 285) | ev 256 / obj 6 | 1027 Woobat -> 576 Dratini | 迷你龙 (139#15) | Dratini | Dratini | m256@0x1CE |  |
| Pokeathlon Dome Interior B1F Potential Room (zone 286) | ev 257 / obj 3 | 1018 Musharna -> 514 Dodrio | 嘟嘟利 (140#24) | Dodrio | Dodrio | m257@0xE2 |  |
| Pokemon League Entrance (zone 300) | ev 271 / obj 3 | 1012 Simisage -> 492 Abra | 凯西 (514#2) | Abra | Abra | m271@0x6A |  |
| Pewter Pokecenter 1F (zone 475) | ev 428 / obj 5 | 1004 Patrat -> 468 Jigglypuff | 胖丁 (456#1) | Jigglypuff | Jigglypuff | m428@0xBE |  |
| Fuchsia Safari Zone Warden House (zone 483) | ev 436 / obj 1 | 1033 Gurdurr -> 621 Aipom | 长尾怪手 (510#1) | Aipom | Aipom | m436@0x2A |  |
| Fuchsia Safari Zone Warden House (zone 483) | ev 436 / obj 2 | 1033 Gurdurr -> 621 Aipom | 长尾怪手 (510#2) | Aipom | Aipom | m436@0x4A |  |
| Fuchsia Safari Zone Warden House (zone 483) | ev 436 / obj 3 | 1033 Gurdurr -> 621 Aipom | 长尾怪手 (510#3) | Aipom | Aipom | m436@0x6A |  |
| Viridian Northeast House (zone 497) | ev 449 / obj 2 | 996 Servine -> 447 Rattata | 大板牙 (449#3) | Bucktooth | Rattata | m449@0x4A |  |
| Viridian Northeast House (zone 497) | ev 449 / obj 3 | 997 Serperior -> 449 Spearow | 空鬼 (449#2) | Skyfiend | Spearow | m449@0x6A |  |
| Sinjoh Ruins Cabin (zone 523) | ev 475 / obj 3 | 1012 Simisage -> 492 Abra | 凯西 (145#13) | Abra | Abra | m475@0x6A |  |
| Embedded Tower Kyogre Room (zone 525) | ev 477 / obj 0 | 1043 Venipede -> 843 Kyogre | 盖欧卡 (147#0) | Kyogre | Kyogre | m477@0xA |  |
| Ecruteak Southwest House (zone 85) | ev 82 / obj 27 | 709 Tyranitar -> 837 Metagross | 巨金怪 (608#213) | Metagross | Metagross | m82@0x36A |  |
| Goldenrod Department Store 5F (zone 195) | ev 188 / obj 27 | 709 Tyranitar -> 837 Metagross | 巨金怪 (588#213) | Metagross | Metagross | m188@0x392 |  |
| Cianwood Kirks House (zone 232) | ev 218 / obj 8 | 946 Leafeon -> 1200 Sylveon | 仙子精灵 (568#108) | Sylveon | Lumineon | m218@0x10A | needs user check |
| Ss Aqua 1F Northwest Rooms (zone 328) | ev 299 / obj 28 | 429 Ivysaur -> 428 Bulbasaur | 妙蛙种子 (255#56) | Bulbasaur | Ivysaur | m299@0x38A | needs user check |

Vanilla HeartGold's own stationary Pokemon use the ids 994..1046 (dex order: Butterfree 994, Rattata 996, Spearow 997, Pikachu 999,
Jigglypuff 1004, Machoke 1014, Ampharos 1031, Aipom 1033, Kyogre 1043 ..., read from the USA ROM's objects and PlayCry); the hack's
following-Pokemon table (id = 428 + base offset in `data/pokemon_overworld_info.narc`) puts Generation 5 species on those ids (1004 Patrat,
1014 Simisear, 1031 Audino, 1033 Gurdurr, 1043 Venipede). The hack's authors retargeted some (Machop 495, Groudon 844, Herdier 1007,
Palpitoad 1036) and missed the rest. The Indigo Plateau Metagross object 27 (zones 85 and 195; Tyranitar 709) is hidden by flag 1366 and
shares script 25 with the Metagross objects drawn 837: label and cry both Metagross.

## Needs user check (not changed unless the Note column above says so)

### Changed although label and cry disagree (label decided)

* Kirk's house (zone 232, events 218 / object 8): label Sylveon (仙子精灵), cry Lumineon (457), was drawn Leafeon -> now Sylveon.
* S.S. Aqua 1F north-west rooms (zone 328, events 299 / object 28): label Bulbasaur (妙蛙种子, sound Bul-ba), cry Ivysaur (2), was drawn
  Ivysaur -> now Bulbasaur.

### Label agrees with the sprite, the cry disagrees (29 objects, sprite and cry left as the Chinese ROM has them)

Rule (2) lets the label decide, and the sprite already is the label's species, so nothing changes; the cry stays. Nickname rows (Megaree,
Peeko, Exbo) have species-neutral text: sprite left, cry disagrees.

| Map | Event member / object | Sprite (unchanged) | Chinese text species | Cry species | Sprite chosen |
|---|---|---|---|---|---|
| Route 6 (zone 14) | ev 11 / obj 17 | 520 Cloyster | Cloyster | Magmortar | unchanged (sprite agrees with the text) |
| Route 26 (zone 30) | ev 27 / obj 11 | 581 Chikorita | Chikorita | Bayleef | unchanged (sprite agrees with the text) |
| Route 32 (zone 36) | ev 33 / obj 2 | 874 Shieldon | Shieldon | Bastiodon | unchanged (sprite agrees with the text) |
| Route 43 (zone 45) | ev 42 / obj 5 | 591 Sentret | Sentret | Smoochum | unchanged (sprite agrees with the text) |
| Route 43 (zone 45) | ev 42 / obj 7 | 591 Sentret | Sentret | Smoochum | unchanged (sprite agrees with the text) |
| Viridian (zone 50) | ev 47 / obj 14 | 617 Politoed | Politoed | Rattata | unchanged (sprite agrees with the text) |
| Cianwood (zone 75) | ev 72 / obj 10 | 583 Meganium | (nickname) | Corsola | unchanged: nickname text is species-neutral, sprite left; needs user check |
| Cianwood (zone 75) | ev 72 / obj 21 | 739 Wingull | (nickname) | Heracross | unchanged: nickname text is species-neutral, sprite left; needs user check |
| Ecruteak Pokecenter 1F (zone 81) | ev 78 / obj 11 | 586 Quilava | (nickname) | Typhlosion | unchanged: nickname text is species-neutral, sprite left; needs user check |
| Ecruteak Dowsing Machine House (zone 84) | ev 81 / obj 14 | 444 Pidgey | Pidgey | Pichu | unchanged (sprite agrees with the text) |
| Slowpoke Well B1F (zone 177) | ev 170 / obj 23 | 509 Slowbro | Slowbro | Slowpoke | unchanged (sprite agrees with the text) |
| Slowpoke Well B1F (zone 177) | ev 170 / obj 33 | 509 Slowbro | Slowbro | Slowpoke | unchanged (sprite agrees with the text) |
| Slowpoke Well B1F (zone 177) | ev 170 / obj 34 | 509 Slowbro | Slowbro | Slowpoke | unchanged (sprite agrees with the text) |
| Slowpoke Well B1F (zone 177) | ev 170 / obj 35 | 509 Slowbro | Slowbro | Slowpoke | unchanged (sprite agrees with the text) |
| Victory Road 2F (zone 178) | ev 171 / obj 16 | 430 Venusaur | Venusaur | Blastoise | unchanged (sprite agrees with the text) |
| Goldenrod Department Store 6F (zone 196) | ev 189 / obj 17 | 475 Paras | Paras | Scizor | unchanged (sprite agrees with the text) |
| Cianwood Pokecenter 1F (zone 236) | ev 222 / obj 8 | 659 Unown | Unown | Flaaffy | unchanged (sprite agrees with the text) |
| Vermilion Pokemon Fan Club (zone 362) | ev 319 / obj 9 | 602 Pichu | Pichu | Raticate | unchanged (sprite agrees with the text) |
| Celadon Department Store 3F (zone 372) | ev 329 / obj 8 | 920 Munchlax | Munchlax | Machamp | unchanged (sprite agrees with the text) |
| Celadon Condominiums Roof (zone 379) | ev 336 / obj 2 | 670 Granbull | Granbull | Floette | unchanged (sprite agrees with the text) |
| Saffron Copycat House 1F (zone 404) | ev 361 / obj 2 | 1036 Palpitoad | Palpitoad | Greedent | unchanged (sprite agrees with the text) |
| Cerulean Gym (zone 427) | ev 382 / obj 10 | 515 Seel | Seel | Goldeen | unchanged (sprite agrees with the text) |
| Cerulean Gym (zone 427) | ev 382 / obj 38 | 515 Seel | Seel | Goldeen | unchanged (sprite agrees with the text) |
| Cerulean North House (zone 429) | ev 384 / obj 9 | 1007 Herdier | Herdier | Solgaleo | unchanged (sprite agrees with the text) |
| Ruins Of Alph Underground Hall Sinjoh Event 2 (zone 492) | ev 444 / obj 12 | 796 Zangoose | Zangoose | Ursaring | unchanged (sprite agrees with the text) |
| Ruins Of Alph Underground Hall Sinjoh Event 2 (zone 492) | ev 444 / obj 14 | 736 Shiftry | Shiftry | Flygon | unchanged (sprite agrees with the text) |
| Ruins Of Alph Underground Hall Sinjoh Event 2 (zone 492) | ev 444 / obj 16 | 736 Shiftry | Shiftry | Flygon | unchanged (sprite agrees with the text) |
| Pallet Town Reds House 1F (zone 503) | ev 455 / obj 2 | 440 Butterfree | Butterfree | Spinda | unchanged (sprite agrees with the text) |
| Pallet Town Reds House 1F (zone 503) | ev 455 / obj 15 | 440 Butterfree | Butterfree | Spinda | unchanged (sprite agrees with the text) |

### Label disagrees with sprite and cry, text ambiguous: sprite left

* Viridian (zone 50, events 47 / object 20): label Doduo (嘟嘟) but sound "Do-drio", drawn Dodrio and cry Dodrio.
* Pokeathlon Dome (zone 280, events 251 / object 10): label Pidgey (波波) but sound "Piiii-geo", drawn Pidgeotto and cry Pidgeotto.

### Not changed for other reasons

* Silent objects drawn wrong, no Chinese text or cry proves the vanilla species (the USA ROM does: Clefairy, Miltank, Poliwrath): Mount Moon
  Square Clefairy event x6 (events 465 objects 0-5, drawn Samurott 1003), Moomoo Farm house x5 (events 201 objects 1,3,4,5,6, Tympole
  1035), Pokeathlon Dome Poliwrath x2 (events 251 and 253, object 1, 1011).
* Route 21 Lairon (events 90 / object 15, 766): text and sprite are Lairon, cry plays Onix (D-2351).
* Victory Road 2F object 16 (events 171, Venusaur drawn, label Venusaur, cry Blastoise): fake-Red scene, not a plain stationary Pokemon.
* Cutscene actors whose scripts move several actors (Slowpoke Well Gold/Crystal, Team Rocket HQ B2F Pryce/Green) are not stationary
  Pokemon objects.

## Reproduction, root cause, proof

Reproduced on the Chinese ROM and on a build of develop (e21ab4b). Audit: every object event of every zone (`a/0/3/2`, 1586 objects with
sprite id >= 428); for each the script entry was followed (jumps included) for PlayCry species and speaker labels and the sprite id was
resolved to a species. Proof (DeSmuME, `work/tools/emu_overworld_sprites.py`, battery save `full_bag_6mons.sav`, clock 2026-10-09 12:00;
teleport to the door, out and back in, walk next to the Pokemon; case `pewter-talk` faces it, presses A and records the arm9 cry call
0x020487F0, r1 = species):

| ROM | Pewter Pokemon drawn | Text box | Cry species | Lighthouse Pokemon drawn |
|---|---|---|---|---|
| Chinese ROM | Patrat | 胖丁『Buli,Buli！ | 39 | Audino |
| develop build (no fix) | Patrat | Jigglypuff: Buli, buli! | 39 | Audino |
| fixed build | Jigglypuff | Jigglypuff: Buli, buli! (text unchanged) | 39 (unchanged) | Ampharos |

Screenshots (game data, not committed): `<scratchpad>/ow/shots/pewter_talk_cn_develop_fixed3.png` and `lighthouse_cn_develop_fixed3.png`
(Chinese ROM | develop | fixed). Not shown on screen: the other 35 objects (data test only); the Department Store basement teleport crashes the
emulator on all three ROMs. Tests: `work/tools/test_overworld_pokemon_sprites.py` (every changed id, only sprite bytes change, no vanilla id
left in 994..1046 except Herdier, Palpitoad and the silent objects), `test_overworld_pokemon_cries.py` (the disabled cry fix's bytes).
`check.py` fast: registry, fixes-md, asm-synth pass; remaining ruff / test failures exist on develop (fixes.py E501, test_script_insert F841,
test_honey_gather needs armips on PATH). `expected.toml` is not updated (record at merge).

## Recheck when 4.1.0 releases

4.1.0 may change these sprites. Walk to each object, talk to it, listen to the cry; if 4.1.0 already draws the right species, drop that row.

- [ ] all 37 rows of the table above (map, events member / object and the sprite-id offset are given there)
- [ ] Kirk's Sylveon and the S.S. Aqua Bulbasaur (label vs cry disagree)
- [ ] the 29 cry-mismatch objects (cry still wrong in the Chinese ROM; is the cry fixed in 4.1.0?)
- [ ] Viridian Doduo/Dodrio and Pokeathlon Pidgey/Pidgeotto (ambiguous text)
- [ ] silent objects still wrong: Mount Moon Clefairy x6, Moomoo Farm x5, Pokeathlon Poliwrath x2
- [ ] Route 21 Lairon (English corrected, cry still Onix), Victory Road 2F object 16
- [ ] the disabled `overworld-pokemon-cries` fix (cries follow sprites) is the alternative if 4.1.0 keeps the old sprites
