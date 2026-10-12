# HM use: our build vs the Chinese hack (issue "Potential HM use timing issue", reporter touyakun21)

Investigation only. Nothing in the repo behaviour, guide or site was changed. 2026-10-12, branch `fix/hm-use-consistency`.

## Verdict

**Our build is identical to the Chinese hack (v4.0.3) in every HM / field-move rule. No bug in the build.** What the reporter saw is the hack's own design (D-1002, D-1428): a field move is gated **only by the Badge**. The HM item in the bag is never checked, and no story flag or Badge count switches the "first Pokémon can use it" feature on.

## Rules (decoded from the Chinese ROM, then compared byte for byte with our build)

1. **Obstacle in the overworld** (Cut tree, Rock Smash rock, Strength boulder, Rock Climb wall, Waterfall, Whirlpool; std scripts 10000-10005, 10016, file 146 of a/0/1/2). The script runs `GetPartySlotWithMove` and then `CheckBadge`:
   - Badge missing: only the description ("This tree looks like it can be cut down!"), no prompt.
   - Badge present: the "Use X?" prompt, then the move is used. No `HasItem` anywhere in the file, so the HM item is never needed.
   - `GetPartySlotWithMove` (cmd 141, arm9 0x0204C8D4) ignores the move id and returns the first healthy non-Egg party slot. So "nobody knows the move" (slot 6) never happens, and the move is used by the lead. This is the "first Pokémon" feature.
2. **Surf** (water tile, overlay 1 0x021E65E4): water prompt needs only the Rainbow Badge (id 3) and a surfable tile. Surf script 10004 has no Badge or HM test. **Waterfall** also has the Earth Badge test (id 7) inside script 10005, as above.
3. **Party menu** (arm9 field-move table 0x020FB5D0, 14 check/use function pairs at 0x02067200-0x02067D00): the entry is listed only if the Pokémon **knows the move**, and for 7 moves the Badge is tested in the check function. No item test.
4. **When does the first-Pokémon feature start?** At once, per Badge. There is no "4th Badge" or story switch. Nothing reads CountBadges or a flag in these scripts.
5. HM items are used only to teach the move (bag, then party). Vanilla HeartGold has the same "Badge + a Pokémon that knows the move" rule. The two things the hack changed are the Badge per move and the missing "knows the move" test for obstacles.

Badge per move (CheckBadge id; matches the guide's table):

| Move | Check | Badge id | Where tested |
|---|---|---|---|
| Rock Smash | script 10001 + party menu | 0 Boulder | both |
| Cut | script 10000 + party menu | 1 Cascade | both |
| Strength | script 10002 + party menu | 2 Thunder | both |
| Surf | water tile (ov1) + party menu | 3 Rainbow | both (script itself none) |
| Fly | party menu | 4 Marsh | party menu only |
| Whirlpool | script 10016/10012 + party menu | 6 Volcano | both |
| Waterfall | script 10005 + party menu | 7 Earth | both |
| Rock Climb | script 10003 + party menu | 15 Rising | both |
| Flash, Defog, Teleport, Dig, Sweet Scent, Headbutt | no Badge test | none | location rules only |

## Why the reporter saw it

Several Badges come before the matching HM item in this hack. Examples (from the guide, which cites the scripts): the Cascade Badge opens Cut trees, but HM01 comes only after the Saffron Badge (the new S.S. Anne captain); the Rainbow Badge opens water, while HM03 Surf lies in the Fuchsia forest after that gym; HM07 Waterfall comes from Misty's scene in the Celadon arc. With the Badge only, the lead Pokémon uses the move. The reporter's "after the 4th Badge" is most likely the Rainbow Badge (Surf); I could not confirm which Badge they meant. In other hacks that add this feature, the HM item is usually also required; this hack never does that.

## Harness proof (DeSmuME, fresh build of develop e21ab4b and the Chinese ROM)

Method: `emu_harness` session on `full_bag_6mons.sav`. Every party Pokémon set to know only Splash (slot 1 of the fixture has a corrupt checksum and cannot be edited; it knows no field move). Items 420-427 (HM01-08) removed from the bag RAM, or left in (99 each). Badge set in the player profile. The std script was run with `run_script` and the commands logged with `OpTrace`. Answer "Yes" to prompts. Four cases per move: Badge only without HMs / HMs only / neither / both. Driver script and outputs are in the scratchpad (`hm/drive.py`, `hm-cn/all.txt`, `hm-en/all.txt`); the pre-cleanup recipe modules `emu_guide0107`, `emu_guide0813`, `emu_skitty` were taken from git history (8c16d8d^) and not committed.

| Move (script) | Badge only, no HM item | HMs only, no Badge | neither | both |
|---|---|---|---|---|
| Cut 10000 | prompt (msg 0), uses it (msg 1) | description (msg 2) | description | prompt, uses it |
| Rock Smash 10001 | prompt, uses it (3, 5) | description (4) | description | prompt, uses it |
| Strength 10002 | prompt, boulder moves (7, 11, 12) | description (9) | description | same as Badge only |
| Rock Climb 10003 | prompt, `RockClimb` runs (20, 21) | description (22) | description | same |
| Waterfall 10005 | prompt, `Waterfall` runs (24, 25) | description (26) | description | same |
| Whirlpool 10016 | prompt, `Whirlpool` runs (29, 30) | description (31) | description | same |
| Surf 10004 | runs (no Badge test in the script) | runs | runs | runs |

Result: **the Chinese ROM and our build give identical message lists, identical command traces and identical outcomes in all 28 cases** (`diff` of both logs is empty). The Badge decides; the HM item makes no difference. The Surf row shows the script itself has no Badge test; the Badge test is in the water-tile code (ov1 0x021E65E4), checked by disassembly, and the guide's earlier emulator test (ch13/surf_*) shows no prompt without the Rainbow Badge. I did not re-walk to real water or trees this time.

Static comparison, Chinese ROM vs our build (ndspy, byte for byte): field-move tables (arm9 0x020FB5D0-0x020FB700), party-menu check/use functions (0x02067200-0x02067D00), cmd 141 and the first-healthy-slot helper, the Flash check, the Badge test (0x02029428), overlay 1 water check and surrounding code: all identical. Script file 146 (std scripts) is identical; only a/0/1/2 files 17, 129 and 928 differ (not field-move scripts). The few code differences between the two ROMs (listed by region) are the build's other fixes (name length, text speed, evolution moves and similar) and none lies in these ranges.

## Guide / site check

`guide/13-dungeons-and-common.md` ("Field moves: which Badge each one needs", mirrored in `site/src/content/docs/guide/dungeons-and-common.md`), `guide/known-issues.md` ("Field moves without the move") and `site/src/content/docs/mechanics.mdx` ("Field moves") match the Chinese behaviour on every Badge and on "no Pokémon with the move needed". Nothing is wrong. Proposed edits (all optional wording, nothing to correct):

1. **State the HM item point plainly.** The table never says an HM item is not needed, which is the reporter's question. Add to the Notes bullet of ch13 (and the mechanics paragraph): "You also don't need the HM item itself. Only the Badge counts, so you can cut, climb, surf and so on before the story gives you the HM, and the same from the first Badge on. There is no story switch." Suggested for `known-issues.md` too: change "You only need the Badge" to "You only need the Badge (not the HM item, and no Pokémon that knows the move)".
2. **Say when it starts.** Add: "There is no condition beyond the Badge: it works from the moment you hold that Badge."
3. **Table gaps.** "Flash, Headbutt: no Badge" is correct. Defog, Teleport, Dig and Sweet Scent are also Badge-free (party menu only, the Pokémon must know the move); the table doesn't list them. Suggest adding them to that row.
4. **Wording of the first note.** "the game uses your first healthy Pokémon" is right (first healthy non-Egg slot); keep. The note "Fly and Flash do need a Pokémon that knows them" should read "the party menu moves (Fly, Flash, Defog, Teleport, Dig, Sweet Scent) need a Pokémon that knows them". Flash also exists as an obstacle script (10013, `FlashAction`), whose reading was not run.
5. **Surf row.** No change: the table and the partner note are right.

## Flags for Shishio

- **No bug.** Behaviour is the same as the Chinese hack, so under D-1002 it stays. If you want the stricter rule (HM item required), that would be a deliberate change from the hack, not a fix; not proposed.
- Open question for the reporter: which Badge they called "the 4th".
- Not covered: real tree/water walks this time, party-menu Fly/Teleport/Dig/Sweet Scent in the emulator, Flash and Defog obstacles. The code for all of these is byte-identical, so a difference would have to come from data, which the earlier ch13 tests also match.
