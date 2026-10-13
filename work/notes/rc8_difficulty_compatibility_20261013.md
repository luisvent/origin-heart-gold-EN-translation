# RC8 difficulty input compatibility review — 2026-10-13

The completed 69-fix English rc8 baseline (`work/build/rc8-harness/baseline69.nds`,
identical to `work/build/check/origin_hg_v4.0.3_en_wip.nds`, SHA-256
`f23e22632620454698c9a8f96b6e834737327b86fa5e5b9c3247d58f7a4d492d`, SHA-1
`5e09a6886bd330cf15910ad1b88b2ca5a5356eb1`) was compared byte for byte with the
rc7 baseline the installer pinned (`work/build/rc7-playtest-20261010/origin_hg_v4.0.3_en_wip.nds`,
SHA-256 `18b6d1478af1740ec693cb30b02da2a8d37b0f715d105f0410466bc4dd355940`, SHA-1
`7ebeaee8...`, the `rom_sha1` that `expected.toml` records at tag `v1.0.0-rc7`,
47 fixes). The historical input `a5a418b2...` is no longer on disk; its comparison
is the retained rc7 audit (`work/build/rc7-completion-20261010/input-audit.json`).
The older `work/build/rc7-final` ROM (42 fixes, `af0641ce...`) is not the rc7 release
baseline and was only used as a cross-check (same hook/dependency result).
Audit script output is in the scratchpad of the 2026-10-13 session; every figure
below is reproducible by diffing the two ROMs with `install.sections()`.

## Result

All 46 hook/edit declarations (24 edits plus hooks) still match their expected
bytes. All 18 dependency ranges, the ten item-ownership ranges, the revival pins
and the three item-frame ranges are byte-identical in rc7 and rc8. Options
overlay50 (5916 bytes), overlay9 (39040 bytes) and the complete 4032-byte ITCM
section are byte-identical. ARM9 size, the three autoload sections, BSS bounds,
overlay RAM addresses, BSS sizes, static-init bounds and compression flags,
the ARM7, ARM7/ARM9 overlay tables and the banner are identical. Only 5 of 551
files differ: overlay14 and four NARCs (a/0/1/2, a/0/1/7, a/0/2/7, a/0/3/2).

## Changed spans and their fixes (no unattributed byte)

ARM9 (4 spans, all in the build report's code regions):
- `0x02048EC8` (33 bytes) and `0x02048EEC` (8): double-battle-single-fallback hook
  (dead script command 223 handler, 44 bytes).
- `0x020507A4` (8): double-battle-single-fallback call inside the trainer battle setup.
- `0x02074148` (10): petilil-hisuian-lilligant.

Overlay14 (17 spans):
- `0x02204D0E` (17) and `0x02204D20` (48): battle-hit-sound (command 8 step 0, the
  66-byte loop at `0x452E`).
- `0x0222CB92..0x0222CCDC` (15 spans, 352-byte Faint_Run at `0x2C39C`): battle-faint-cry.

NARC members (all listed in the build report's `narc_bytes`):
- a/0/1/2 (scripts), 57 members: blank-player-name (3), blank-player-name-batch (36),
  blank-player-name-class-c (3), sibling-ribbon-freeze (7), romance-mail-mismatch (2),
  and one each of reward-qty, forest-of-time-sammy-guard, haircut-younger-price-check,
  ssanne-tm-price-check, photographer-no-healthy-mon, victory-road-arch-movement-wait,
  tutor-saffron-volt-switch, tutor-blackthorn-play-rough, giovanni-hotspring-loss,
  fortune-ideal-price-check, gamecorner-500-coins.
- a/0/1/7, 9 members: evolution-items-use. a/0/3/2, 19 members: overworld-pokemon-sprites.
- a/0/2/7 (text), 7 members (38, 133, 142, 484, 732, 738, 816): approved text
  commits since rc7 (reward-quantity line, Bounce description, Rock Tunnel tutor,
  Skitty kid, safari dead string and the like); text only.

## Analysis of the code changes

None of the changed spans lies inside, or within 7 KB of, any difficulty hook, edit,
dependency or revival range (nearest: the Faint_Run rewrite is 7538 bytes from
`revival_hp_event`, the hit-sound loop 8474 bytes from an item hook). The
`ordinary_hp_dispatch` revival dependency is unchanged from rc7, so the rc7 review of
its two message-variant edits stands. battle-faint-cry and battle-hit-sound
add calls only to ARM9 sound and cry routines (`0x02006898`, `0x02005F3C`,
`0x02005F5C`, `0x02008BC8`) that no difficulty hook or dependency covers, and keep the
handlers' entry points, frames and register contracts (the listings guard every
original halfword). They are client-side presentation and do not touch battle
context EXP, party or bag state. petilil-hisuian-lilligant changes one species
constant 9 KB from the nearest pinned range.

double-battle-single-fallback interacts with the loss-allowed story-battle
classifier: the classifier's flag `0x800` is ORed at `0x02050798..A2` on the
single-trainer path only, and the new call at `0x020507A4` runs afterwards. The hook
acts only on plain double types (bits `0x42` equal to `0x02`: types 3 and 0x13) and
only with fewer than two party members; type 1, 0x801 and the multi type 0x4B pass
unchanged. A downgraded battle is type 1 without `0x800`, which is the ordinary
single-trainer flag set the classifier already accepts (flags 1). So the downgrade
cannot create a battle the classifier treats as loss-allowed, and does not alter
the bytes the classifier reads. This was reasoned from the disassembly, not run natively.

Script bytes changed in a/0/1/2 (e.g. giovanni-hotspring-loss); difficulty reads the
`TrainerBattle` third operand at runtime, so scripts matter only to native cases.

## Pins revised (only after this review)

- `install.py`: `INPUT_SHA` 18b6d147 -> f23e2263; `OV_PINS[14]` d6ec23a4 -> 7c98bd20.
- `compatibility.json`: `full_input_guards.en.arm9` 5590ddbb -> 4b55c2e7; `roms.en`
  path and sha (18b6d147 -> f23e2263).
- `research/items-revival-pins.json`: `inputs.en` path and sha, as above.
- `native/integration_contract.json`: `source_overrides` pin of `compatibility.json`
  ff5bffc2 -> 842cfa16.

ITCM, overlay50 and overlay9 pins are unchanged. No hook guard, overlap check, memory
limit, source/tool check or logical-preservation check was disabled.

## Not established

This is static compatibility only. The 79 required native cases
(`tests/required_native.json`) have not been run for this candidate (0/79), including
the item positive/negative validation, the Share/Cap battle cases, loss-allowed story
battles, and a native check that a forced double downgrade then plays under the
difficulty settings. Native runs need the user's separate approval.
