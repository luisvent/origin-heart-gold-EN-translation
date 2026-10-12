# Ice Stone (and eight more evolution items) had no USE in the Bag (fix `evolution-items-use`)

Report: Discord #bugs "Ice stone unusable" ("there is no 'use' option for ice stone, all other stones tested can be used").

## Reproduced (2026-10-12, DeSmuME, fresh build of develop e98854f)

`emu_harness.py drive` with `bagfirst:606,1,items bag t64,56 s:menu`: the item menu of the Ice Stone (item 606) shows
TRASH / GIVE / MOVE / CANCEL and no USE; the Fire Stone (82) shows USE. The untouched Chinese ROM
(`origin_v4.0.3_cn.nds`) shows the same (no USE), so it is a data error of the hack, not of our build (D-1002 asks
the question; the answer is "accidental": the hack's own evolution table names the item, so it must be usable).
The US ROM has no Ice Stone.

## Root cause

Item table `a/0/1/7`, 34 bytes per item. Bytes 10..15 hold the Bag/party use data. The stones have
`14 00 01 00 00 08` there (Sun, Moon, Fire, Thunder, Water, Leaf, Shiny, Dusk, Dawn, and the hack's usable
Twisted Spoon 248, which Pikachu uses). The Ice Stone has zeros, and so do eight more items that evolution
records (a/0/3/4) name with method 7 ("use item"):

| Item | id | Evolves (method 7) |
|---|---|---|
| Ice Stone | 606 | Mr. Mime (122), Crabrawler (739), Cetoddle (974), Darumaka (1173), Sandshrew (1035), Vulpix (1037) |
| Cracked Pot | 624 | Sinistea (854) |
| Galarica Cuff / Wreath | 631 / 633 | Slowpoke (1050) |
| Sweet / Tart Apple | 641 / 642 | Applin (840) |
| Auspicious / Malicious Armor | 646 / 653 | Charcadet (935) |
| Dragon Scale | 235 | Exeggcute (102) -> Exeggutor form 1 (record target 1057) |

## Audit of all evolution items

Every evolution record of the Chinese ROM with method 7 or 17 (Dawn Stone) was compared with the Fire Stone record:
the nine classic stones and Twisted Spoon are fine; the nine items above are the only ones without use data.
Methods 18/19/20/37 (held item, trade with item, level up with item) need no Bag use and are untouched. Linking Cord (635),
Peat Block (637) and Black Augurite (614) are named by no evolution record at all (nothing evolves with them; the
Cord was already noted as unobtainable in `trade-evolutions_fix.md`): nothing to fix, logged as a finding (D-2348).
Dragon Scale is also the held trade item of Seadra; see the question D-2347 (is the Alolan Exeggutor evolution by
Dragon Scale intended?). It is fixed like the rest because the hack's own record uses it by use.

## Fix

`work/patches/evolution-items-use/fix.toml` (kind narc, 9 `[[narc_bytes]]` entries, enabled): bytes 10..15 of the
nine item records `00 00 00 00 00 00` -> `14 00 01 00 00 08`; each only when the member still has the recorded SHA-1.
Decision D-2346. `expected.toml` re-recorded (`check.py --full --update-expected`).

## Proof (DeSmuME, scenario `stone-use`, `emu_harness.py fixes --case evolution-items-use`)

Per item: a Pokémon from the generator at Lv 20 with Tackle only, the item first in the Items pocket, Bag > item >
USE > Pokémon, A through the evolution scene.

| Case | Build without the fix (control) | Build with the fix |
|---|---|---|
| Vulpix + Fire Stone (control) | Ninetales | Ninetales |
| Crabrawler + Ice Stone | Crabrawler (no USE) | Crabominable |
| Sinistea + Cracked Pot | unchanged | Polteageist |
| Slowpoke + Galarica Cuff / Wreath | unchanged | Slowbro / Slowking |
| Applin + Sweet / Tart Apple | unchanged | Appletun / Flapple |
| Charcadet + Auspicious / Malicious Armor | unchanged | Armarouge / Ceruledge |
| Exeggcute + Dragon Scale | unchanged | Exeggutor, form 1 (Leaf Stone gives form 0, Fire Stone does nothing) |

Result: `PASS evolution-items-use stone-use  fixed ROM: fixed  control: original`. The Ice Stone item menu with the
fix shows USE (screenshot in the run folder, not committed). Chinese ROM: no USE for the Ice Stone (above).
Unit tests: `test_emu_fixes.py` (`test_stone_use`, `test_stone_use_cases_follow_the_fix`).

## Checks

`check.py` fast: registry, fixes-md, asm-synth, tests pass; ruff fails on `work/tools/fixes.py:1787` (E501) and
`work/tools/test_script_insert.py:88` (F841), neither touched by this branch (present on develop e98854f).
`check.py --full --update-expected`: everything but ruff passes.

## Follow-up 2026-10-12 (Shishio's two questions)

### 1. Dragon Scale -> Alolan Exeggutor: intended by the hack author

Checked directly in the untouched Chinese ROM (`origin_v4.0.3_cn.nds`):

- Evolution table `a/0/3/4` member 102 (Exeggcute): `(7, 85, 103)` = Leaf Stone -> Exeggutor 103, and `(7, 235, 1057)` =
  Dragon Scale -> species 1057. Both are method 7 (use item), so both records exist.
- Personal data `a/0/0/2`: 103 is Grass/Psychic; 1057 is Grass/Dragon with the same stats (95/120/85/45/125/85), i.e. the
  Alolan Exeggutor typing (the hack added a dedicated entry for it).
- In the game (harness, build and Chinese ROM): Exeggcute + Leaf Stone -> species 103 form 0; Exeggcute + Dragon Scale
  (build with this fix) -> species 103 form 1 (the form table maps 1057 to form 1); Fire Stone does nothing.
- The author's own documentation ties it: `work/notes/spreadsheet_crossref.md` §1.2 row 109 lists Exeggcute as
  "Leaf Stone (Exeggutor) or Dragon Scale (Alolan Exeggutor)" (class a: the ROM differs from the sheet's "35" but the
  Dragon Scale is a v4 addition; the v3 ROM has the Leaf Stone only, `sheet_mismatch_verification.md` §4.2 row 109);
  `work/docs/pokemon_0001-0151.md` shows the same from the ROM. No item description or NPC text mentions it (the Dragon
  Scale text is the plain item description and the shrine cleaner's sale, bank 0127 #42-47).
- Pattern: the hack gives other regional forms their own trigger item instead of the vanilla stone, e.g. Pikachu +
  Twisted Spoon (248) -> species 1034 (Electric/Psychic, Alolan Raichu typing), which the author did make usable.

Conclusion: deliberate (a new record plus a new Grass/Dragon species entry); not a mix-up with the Leaf Stone. The Dragon
Scale had simply been left without its use bytes, like the other eight. The fix stands. D-2347 can be resolved as
"intended" if Shishio agrees (not resolved by me).

### 2. Where players can get the nine items (Chinese ROM = build for these data)

| Item | Obtainable? | Where |
|---|---|---|
| Ice Stone (606) | yes | Celadon Department Store 2F shop, 3000 (docs `items.md`, site `items.json`: shop source) |
| Dragon Scale (235) | yes | Dragon's Den (gift, and bought 2500 from the shrine cleaner, bank 0127 #42-47), Route 12 and Route 35 item balls; wild held item of Horsea (116), Seadra (117), Dratini line (147-149), Dratini line and Chinchou-type species per `a/0/0/2` held-item slots: 116, 117, 147, 148, 149, 230 |
| Cracked Pot, Galarica Cuff, Galarica Wreath, Sweet Apple, Tart Apple, Auspicious Armor, Malicious Armor | **no** | the reviewed list `work/tools/site/items_not_in_game.json` (two independent passes, 2026-10-05, `availability_audit.md`): no gift, shop, item ball, hidden item, prize, Pickup, held item or engine reward. Re-checked today on the Chinese ROM for wild held items (`a/0/0/2`), hidden items and trainer held items: none of the seven appears; D-1493 also records Tart/Sweet Apple as sourceless |

So with the fix only the Ice Stone and the Dragon Scale change anything a player can do; the other seven become usable
but stay unobtainable (the fix is data-correct and harmless; they matter for save-edited or cheat-given items).
Of the Ice Stone evolutions the species themselves must also be met (not checked here, the site's species pages decide).

Site/guide check (read only, nothing edited): `site/src/data/items.json` lists Ice Stone with its shop source, Dragon Scale
with its sources, and the seven others with `unavailableReason` set; `guide/known-issues.md` line 1398 says Applin's
apples cannot be obtained, consistent. Mismatches found: none about availability. One thing the release notes / known
issues should mention: nothing in the guide says the Ice Stone could not be used, so no guide text goes stale; the
Ice Stone evolutions listed on the site ("use Ice Stone") become true only with this fix (before it, they were
impossible in play, although the site listed the stone as buyable).
