# Blackthorn Move Tutor teaches Flail instead of Play Rough (fix `tutor-blackthorn-play-rough`)

**Status: disabled** (`enabled = false`). A separate, switched-off patch, like the other 2026-10-12 hack-bug fixes; the
standard build keeps the Chinese behaviour; build it with `build.py --only tutor-blackthorn-play-rough`. Findings
D-1305 (hack bug), D-2355 (this fix). Source of truth: the untouched Chinese ROM (`work/rom/origin_v4.0.3_cn.nds`).
Investigation: `work/notes/tutor-wrong-moves_investigation.md`.

## Cause

`a/0/1/2` member 944 (Blackthorn Move Tutor house, bank a027/0626 #58-#68) offers two lessons. The Draco Meteor half
uses move 434 everywhere. The Play Rough half uses move 175 in four places:

    pc 1925  MonHasMove 0x800C, 175, 0x8006        ('already knows it?')
    pc 3461  SetMonMove slot, free slot, 175       (pupil with fewer than four moves)
    pc 3551  PokemonSummaryScreen 1, slot, 175     (summary of the forget-a-move path)
    pc 3619  SetMonMove slot, chosen move, 175     (after the forget confirmation)

In v3 slot 175 was Play Rough (嘻闹). In v4 Play Rough has its own id 583 (嬉闹) and 175 is Flail again (Normal,
variable power, PP 15). The dialogue, the author's item sheet (`Items.xlsx`, 3.2道具 row 585: 嘻闹, Blackthorn, free) and
the Gym hint ('super effective against Dragon types') all say Play Rough, so the intended move is unambiguous.

## Fix

Four two-byte edits `AF 00` -> `47 02` (175 -> 583) at member offsets 0x789, 0xD8B, 0xDE4, 0xE29. Size, offsets, flags
and every message stay as in the Chinese ROM; nothing is deleted or invented (D-1500). The text is not touched (it
already says Play Rough; the English matches the Chinese). Guards: whole-member SHA-1 `9c0d1c89...c0d5` and the
expected bytes of each edit.

## Verification

* `work/tools/test_tutor_blackthorn_play_rough.py` (6 tests, needs the Chinese ROM): the original script has Flail in
  exactly these four commands; after the fix only those eight bytes differ, the decode is identical elsewhere and
  shows Play Rough in the same four commands; names 抓狂 / 嬉闹 in bank 0739; both guards reject a changed source.
* Emulator (DeSmuME, 2026-10-12, see the investigation note): Chinese ROM and rc7: 3 moves -> Flail, 4 moves ->
  Flail, summary names Flail. rc7 + fix: see the table in the investigation note.

## Where a reviewer should look hardest

* That no other Blackthorn script refers to move 175 as Play Rough (the compare at pc 2462 is on a species id, 0x8005).
* That a Pokemon that already knew Flail is not blocked now: the 'already knows it?' check now looks for Play Rough.
* The tutor's compatibility list is species based and unchanged; whether every listed species can legally know
  Play Rough is the hack author's design, not checked here.
