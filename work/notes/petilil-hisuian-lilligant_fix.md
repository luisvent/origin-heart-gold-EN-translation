# Petilil + Black Belt by day -> Hisuian Lilligant (`petilil-hisuian-lilligant`, D-2334)

Fixed 2026-10-12 after the user lifted D-1337 for reproduced hack bugs ("We are way past this point since the
Chinese rom contains too many bugs.. So lets create a fix in a worktree"). It answers the hack finding D-1485.

## Symptom
A Petilil that levels up in the daytime holding a Black Belt "evolves into Petilil" (the Black Belt is used up, the
form byte becomes 1); a Sun Stone then turns that form-1 Petilil into Hisuian Lilligant. Untouched Chinese ROM too.

## Cause (decoded from the Chinese ROM)
- Petilil's evolution records (`a/0/3/4`, member 548): record 0 = method 7 (item use), parameter 80 (Sun Stone),
  target 549; record 1 = method 18, parameter 241 (Black Belt), target **1361**. 1361 is the hack's own
  "Hisuian Lilligant" species id (personal data, `work/docs/form_names.json`).
- Evolution scene setup, arm9 `0x02074048` (r2 = target id): ids above 1025 are decoded into a base species and
  form 1 (`[sp+0x24] = 1`, later `SetMonData(mon, 0x70 FORM)`): 1034 -> 26, 1057 -> 103, 1058 -> 105, 1059 -> 110,
  1109 -> 263, 1348 -> 58, 1361 -> 548, 1371 -> 550. For 1361 the case at `0x02074148` is
  `movs r5,#0x89 ; ... ; lsls r5,r5,#2` = 548 = Petilil. Lilligant is 549.
- Only 1361 is reachable (only Petilil's record names it; the Raichu, Exeggutor, Marowak and Weezing records name
  1034, 1057, 1058, 1059). 1109, 1348 and 1371 are named by no record and were left alone (not analysed further).

## Fix
`work/patches/petilil-hisuian-lilligant/` (armips, arm9, one 10-byte region, expect-guarded):
`2589 1C38 2170 AA09 00AD` -> `1C38 2170 AA09 008D 3565` at arm9 `0x74148`: the arguments of the SetMonData call
are set first and the species is built as `lsl r5, r1, #2 ; add r5, #0x65` with r1 = 0x70 (448 + 101 = 549).
The call (`bl 0x0206DF70` at `0x02074152`) and the branch after it are untouched. The evolution-moves fix edits
`0x70870-0x70923` and `0x74BD4` only: no overlap, and both apply together (test).

## Verified
- Static: decode above; `fixes.py check`, `asmpatch.py check`, listing; `test_petilil_hisuian_lilligant.py`
  (the exact 10 bytes change, nothing else, also together with evolution-moves).
- Emulator (DeSmuME, clock 2026-10-09 12:00, Petilil Lv 10 holding a Black Belt, one Rare Candy):
  - Chinese ROM and the `--without` build: species 548, form 1, Lv 11, ability 20 (Own Tempo), item used up.
  - Build: species 549, form 1, Lv 11, **ability 55 (Hustle**, the form's ability), stats recomputed from the
    form's base stats (HP 36 Atk 28 Def 21 Spe 28 SpA 16 SpD 21 at Lv 11), nickname = the species name of 549,
    Black Belt used up once the scene finishes (four known moves, evolution-move prompts declined with B).
  - `emu_harness.py fixes --case petilil-hisuian-lilligant` (scenario `petilil-evo`): build `fixed`, control
    (`--without`) `original`. `emu_harness.py scenarios --only petilil`: pass on the build, FAIL on the control.
  - The evolution-moves fix still runs for the new species (the evolved Pokemon is asked for its level-0 moves;
    with a full move set the scene waits for the answers, so the held item is cleared only after them).
- Scenario `evolve.toml`: the daytime Petilil case moved to `petilil.toml` (the two ROMs now differ on purpose); the
  night control stays in `evolve.toml`.

## Not verified
- The summary sprite/name text of Hisuian Lilligant in the English build was not looked at (the species name was
  read from the nickname bytes only); the earlier Sun Stone route showed it is the same species/form.
- Evolution by other methods, the day care, and the other form ids (1109, 1348, 1371) were not tested.
- Site data (`site/src/data/species.json`, Pokedex pages) and `work/docs/pokemon_1026-1440.md` ("use a Sun Stone on a
  Petilil that leveled up by day") are generated and still describe the old route; regenerate them with the next
  data build. `HACK_FINDINGS.md` is generated from the register (D-1485 is resolved in it).
