# TRAINER AI row on Options page 2

2026-10-13. Phase 4 of the advanced trainer AI port (`work/advanced-ai/PLAN.md`,
decision 4). Page 2 gains a fourth row, TRAINER AI, with three values: OFF,
KEY (important trainers only) and ALL. The row only stores the setting. The AI
that reads it is installed later by `work/advanced-ai/builder/install.py`; the
row works the same with or without it.

## Storage

Two saved event flags, not the Options word (`work/advanced-ai/docs/build-contract.md`, Settings):

| Value | 0x2C2 | 0x2C3 |
|---|---|---|
| OFF | clear | written clear (read: ignored) |
| ALL | set | clear |
| KEY | set | set |

OFF clears both flags, as the Spanish build's Pokémon Centre NPC did. Codec:
`dg_ai_decode` and `dg_ai_encode` in `native/settings.c`.

The row reads and writes the flags through the hack's own routines, the same
path the AI's selector reads (disassembly of the rc8 standard build):

| Address | Routine | Body |
|---|---|---|
| 0x02001194 | GetSaveData | `ldr r0,=0x021106A8; ldr r0,[r0,#0x20]` |
| 0x0204F858 | Save_VarsFlags_Get | `SaveArray_Get(save, 4)` (0x02027740) |
| 0x0204F864 | CheckFlag(vars, flag) | GetFlagAddr, then tests bit `flag & 7`; returns 0 or 1 |
| 0x0204F890 | SetFlag(vars, flag) | GetFlagAddr, then ORs the bit into the byte |
| 0x0204F8B8 | ClearFlag(vars, flag) | GetFlagAddr, then ANDs the byte with the inverted bit |
| 0x0204F8E4 | GetFlagAddr | `vars + 0x2E0 + flag / 8` for flags below 0x4000; null for flag 0 |

The emulator check hooks SetFlag and ClearFlag. Every write it sees for 0x2C2
or 0x2C3 comes from the difficulty resident code, and the harness reads the
result through its own SaveData global (0x021D11B4), which holds the same
pointer as GetSaveData's.

## Transaction

The row joins the existing draft/apply/cancel transaction (`native/options.c`).

- Opening Options reads the flags once into `page.ai_original` and `page.ai_draft`.
- Changing the row changes only the draft.
- Confirm (APPLY) writes both flags at exit, only when the draft differs. It
  writes them only after the Options word's own apply has succeeded.
- If the flags changed while the page was open, Apply is refused on the page
  (the help shows the existing "Settings changed" message) and again at exit
  (`DG_SETTINGS_STALE`). Nothing is written in either case.
- Back, B and Cancel discard the draft. Confirm on page 1 also commits the
  page-2 draft, as for the other difficulty rows.
- Saving is the player's normal Save. There is no auto-save.

## Layout

Rows keep the native 20-pixel pitch. TRAINER AI is drawn at window y 65, the
native row-3 position, so the native red outline (021E5944, BG0 scroll table
by row) frames it with no change.

The row cannot borrow native slot 3 the way rows 0–2 borrow slots 0–2: the
native renderer 021E53EC runs a preview for slot 3 (0x0200589C calls
0x020C6CA4 with the value and stores it at 0x021CF438). The row is therefore drawn with
the renderer's own steps:

1. Erase the value area: `0x0201E2A4(window, 0x22, 108, 65, 320, 20)`.
2. Print OFF, KEY and ALL at x 108, 156 and 204 (the 48-pixel pitch of native
   rows 0 and 1). The chosen value uses the SELECTED colour.

The emulator check confirms that 0x0200589C never runs while page 2 is shown.

| Input | Effect |
|---|---|
| Up, Down | Six positions, wrapping: the four rows, CANCEL (right button), APPLY (left button, CONFIRM) |
| Left on the row | Previous value, wrapping |
| Right or A on the row | Next value, wrapping |
| Touch y 82–101 | x 108–159 OFF, 160–207 KEY, 208–247 ALL; x 8–107 moves the focus only |

## Text

| Text | Width (font 0) | Space |
|---|---|---|
| `TRAINER AI` | 58 | 104 (x 4–107) |
| `OFF`, `KEY`, `ALL` | 18 each | 44 (48-pixel pitch) |
| `Advanced AI: OFF for no trainers, KEY` | 204 | 212 (help line 1) |
| `for important trainers, ALL for all.` | 192 | 212 (help line 2) |

Widths are from `work/tools/font_widths.json`; both font sets give the same
values. The help needs a comma, so `glyph()` now maps `,` to 0x1AD (charmap.tbl).
The labels follow the plan's OFF / KEY / ALL, which is still marked "labels to confirm".

## Binary layout

`page` gains two words at its end: `ai_original` at +352 and `ai_draft` at +356.
The struct is now 360 bytes. Earlier offsets that native test drivers read
(+24, +36, +48, +52, +336) are unchanged. With Apple clang 17 the resident
section grows from 8940 to 9776 bytes of the 16 KiB reservation.

## Tests

- Host: `tests/drivers/options_check.c` (ASan/UBSan) covers:
  - the codec;
  - the four flag pairs with B, touch Cancel and an unchanged Apply, none of
    which writes;
  - the D-pad walk over six positions and the native cursor row;
  - Left, Right and A wrapping;
  - touch band edges;
  - the help text;
  - shared Confirm and B from page 1;
  - flags changed before Apply and at exit, and an Options word changed at
    exit, none of which writes.

  Thirteen scratch mutants of the row, including writing on Cancel, the wrong
  touch band, no stale check and writing after a failed word apply, are all
  rejected.
- Native: `work/advanced-ai/testbench/checks/options_trainer_ai.py`, 13 cases on
  the development build, including save and reload in a second emulator process.
- The difficulty suite's native UI driver now walks six focus positions
  (`tests/support.py` `FOCUS_COUNT`, `native_ui.py`, `evidence.py`,
  `native_ui_oracles.py`, `test_framework.py`). That driver needs
  `work/build/memcheck/*.sav` and the save core, so it was not run here.
