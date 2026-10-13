# Builder

Turns the AI sources in [../src/](../src/) into the payload that the installer writes into a ROM. The interface
between the builder, the installer and the test bench is [../docs/build-contract.md](../docs/build-contract.md).

| File | What it is |
|---|---|
| `build.py` | Compiles and links the AI for one layout and writes the payload. Ported from the Spanish build's `link_ai` (see [../PROVENANCE.md](../PROVENANCE.md)) |
| `layouts/` | The memory layouts: `en.json` (the English payload) and `es.json` (the Spanish rc44 layout, for the golden test). [layouts/README.md](layouts/README.md) explains the fields |
| `install.py` | `install.py --input ROM --out ROM [--payload DIR] [--marks JSON]` writes the AI into a copy of an English build with difficulty and writes `<out>.receipt.json`. It refuses an input without difficulty, one that already has the AI, and any site that does not hold the expected bytes |
| `verify.py` | `verify.py ROM [--input ROM]` re-reads an installed ROM with its own parser (not the installer's) and checks every write; with `--input` it also checks that nothing else changed. The placement is explained in [../docs/memory-layout.md](../docs/memory-layout.md) |

## What it needs

- arm-none-eabi-gcc 16.2.0 and GNU binutils 2.47 on `PATH` (Homebrew: `/opt/homebrew/bin`). `build.py` checks
  `gcc`, `as`, `ld`, `objcopy`, `objdump` and `readelf` first and refuses any other version, because another
  compiler gives other bytes. A binutils 2.47 release-branch build (`2.47.YYYYMMDD`) counts as 2.47.
- Python 3.12 or later, standard library only. Run it with the worktree's `.venv/bin/python`.
- No ROM. The installer reads the ROM; the builder only compiles.
- For `--layout es` only: the Spanish workspace repository (read only), for the Spanish asm sources that come
  before the AI in its ITCM block.

## How to run

From the repository root:

```sh
# the English payload, into the committed payload/ (review the diff before committing)
.venv/bin/python work/advanced-ai/builder/build.py --layout en --out work/advanced-ai/payload

# the Spanish rc44 layout, where the test bench looks for it
.venv/bin/python work/advanced-ai/builder/build.py --layout es \
    --es-repo /path/to/spanish/repo --out work/build/advanced-ai/es/payload
```

| Option | Meaning |
|---|---|
| `--layout en\|es` | Which file in `layouts/` to build |
| `--out DIR` | Where to write the payload. Default: `work/build/advanced-ai/payload-<layout>/` (ignored by git) |
| `--work DIR` | Keep the objects, `ai.elf` and the link map `ai.map` in this directory, for inspection |
| `--es-repo DIR` | The Spanish repository: `git archive dc8577c work_es/tools/asm` into a temporary directory |
| `--es-tree DIR` | Or a directory that already holds that archive |

It prints the room line (used and free bytes per region) and what it moved between regions.

## What it does

1. Assembles the layout's asm sources in order (`*.s.o`: `link.ld` puts them first in ITCM).
2. Compiles `advai.c`, `replace.c` and `lead.c` as one unit with the Spanish flags plus the layout's `cflags`.
3. Finds the sections that `ai_replace` and `ai_lead` reach. They must stay resident, because they run while the
   battle slot holds another overlay. Those shared with the selection AI go to ITCM, the rest to main RAM.
4. Links with `src/link.ld` and a `MEMORY` block written from the layout. If the slot code does not fit,
   `slot_spill` moves the fewest bytes to ITCM. If ITCM does not fit, `largest_first` moves the largest sections to
   main RAM.
5. Writes `slot.bin`, `itcm.bin`, `main.bin` and `payload.json`: the regions, every placed symbol with the Thumb bit
   on functions, the hooks with their new bytes, the arena words, and the sha256 of every source and `.bin`.
   With the layout's `zero_work_ram` (en), the itcm region's `bss` runs from the end of its code through
   `.itcm_bss` (en: 0x01FFECAC–0x01FFFDD8, 0x112C B). The boot's autoload then zeroes the AI's work RAM; the
   test records from 0x01FFFF8C stay outside it.

The output depends only on the sources, the layout and the toolchain. Two builds are byte-identical
(`testbench/unit/test_build.py`).

## Room

| Layout | Slot code + bss (free) | ITCM code (free) | ITCM work RAM (free) | Main RAM code (free) | Moved ITCM → main |
|---|---|---|---|---|---|
| `es` | 34,144 + 2,528 (2,688) | 25,836 (756) | 4,056 (436) | 24,184 (41,352 of 64 KB) | 17,192 B, 6 sections |
| `en` | 32,800 + 2,656 (3,904) | 22,444 (340) | 4,056 (436) | 25,784 (6,984 of 32 KB) | 18,788 B, 8 sections |

`es` reproduces the Spanish build's own room line. In `en`, ITCM holds only `aiselect.s` and `check_flag.s` before
the AI, instead of the Spanish build's other asm, but the region is smaller. The slot is 1,344 B smaller, because
the compiler drops the code behind the steering gate. `largest_first` moves the Spanish build's six sections
(`value_move`, `value_status`, `vetoed_vs`, `mixed1`, `entries_from`, `read_mon`) and two more: `reply_odds`
(788 B) and `value_switch` (808 B).

## The English itcm origin

The ITCM block before the AI differs per locale, so the en `itcm` region starts at a fixed 0x01FF9500 that clears
the largest block any locale can have:

| Part | Bytes | Source |
|---|---|---|
| Text speed's ITCM code ends at | 0x01FF8FC0 | `work/patches/text-speed` (fixed native payload) |
| Trainer full-name block (D-2487): code + literal pool | 112 + 12 | `trainer_display.py` `CODE`, `expected_payload` |
| Its table: 5 aliases + a terminating entry, 16 B each | 96 | `IDS` |
| Its names: 5 × at most 64 units × 2 B | 640 | `encoded()` refuses more than 64 units |
| Worst-case end, rounded up to its 32-byte step | 0x01FF9320 | `apply()` |
| Rounded up to 0x100, plus 0x100 margin | **0x01FF9500** | 0x1E0 to spare: one more alias at full length takes 0x90 |

English on main today ends the block at 0x01FF9140. 0x01FF9420 would also satisfy the margin, but it moves the
same two sections to main RAM, so the rounder origin costs nothing. `test_build.py` recomputes the worst case from
`trainer_display.py` and fails if the origin no longer clears it by 0x100.

## Steering

The English build compiles luck steering out. `layouts/en.json` defines `AI_NO_STEER`; with it, `steer_marked` in
`src/advai.c` returns 0. That makes `steer_gate` (singles) and `dsteer_wanted` (doubles) false, so no path reads
flag 0x218 and nothing can switch steering on. `steer_stash`, `steer_ledgers` and `steer_dstash` (the Spanish
build kept them in `steer.s`) become zeroed slot bss that nothing arms. `es.json` leaves the switch undefined, so
its bytes stay the Spanish ones.
