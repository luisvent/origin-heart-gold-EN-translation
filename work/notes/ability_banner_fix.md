# Ability-banner clipping investigation — 2026-10-13

Status: disabled. Worktree `ability-banner/poke`, branch `fix/ability-banner`.
Merged into main disabled after separate review. Finding D-2500
was renumbered from worktree D-2413 during integration.

## Cause and Chinese / US comparison

The untouched Chinese ROM uses the same custom banner renderer as English:
overlay 14 `0x02226658`. It reads ability bank 711, expands the nickname template,
creates a 15 × 5 tile window (120 × 40 pixels), measures both strings with font 5,
and prints the nickname at y=3 and the ability at y=14. It anchors the ability
at x=132 minus its width. It then attempts a 12-pixel horizontal overlap between the staggered rows,
shifting the nickname right and the ability left when their combined widths
are short. Long English labels do not receive that inward adjustment.

The hack is based on Japanese HeartGold (IPKJ), but this is an added banner in
the modified engine, not evidence of a Japanese character-count limit. There
is no truncation by character count here: the whole string reaches the printer.
Chinese has shorter names: native Battle Armor (战斗盔甲) measures 40 pixels;
English measures 82. Chinese Battle Armor is brought inward to x=64, ending at x=104 and fitting.
English retains x=50, ending at x=132 and clipping. The character-count limit
is not responsible. Chinese control screenshots are preserved privately.

The US overlay 14 has a different purpose/layout (load address 0x021E5900,
size 0x13A80 versus hack 0x022007E0, size 0x52540). Copying US battle code into
this routine is not a safe repair. The hack has added abilities, scripts and UI.
We can safely repair this English layout locally while preserving its engine;
this patch does not claim to restore a corresponding US banner implementation.

## Final patch

Two guarded Thumb halfwords in overlay 14, no growth:

- `0x0222670A`: anchor 132 -> 112 (eight pixels of right padding).
- `0x0222670C`: nickname padding 8 -> 16. Settled player-side screenshots showed
  that eight pixels still clips the leading letter at the screen's left edge;
  sixteen clears that edge without overflowing the ten-character name row.


Font, graphics, window allocation, slide-in animation, duration, battle scripts,
ability effects and name text are unchanged. This uses no generated graphics.
All 327 nonempty current ability names measure at most 84 pixels in miniature
font member 12. Its metrics match native font5 samples: Battle Armor 82,
EmbodyAspect 84, Feraligatr’s 78. Ability text occupies x>=28 through x=112;
Feraligatr’s occupies x=16 through x=94; WWWWWWWWWW’s measures 83 pixels
and ends at x=99. The original staggering adjustment is retained: it can move
a short pair inward, keeping both rows within the window. Wider non-Latin
nickname symbols have not been exhaustively tested.

## Verification

`work/tools/test_ability_banner.py`: three tests passed using pinned armips
v0.11.0. Tests assemble against the Chinese ROM and verify the exact two
halfwords, unchanged other ROM files/ARM9/overlay table, disabled selection,
guard rejection without mutation, and every current ability's miniature width.
Registry `fixes.py check` passed; assembly listing generated.

Fresh-boot DeSmuME native renderer tests:

- Untouched Chinese: `work/build/ability-banner/cn` and `final-cn`.
- Exact released rc7 roundtrip: `both-rc7`; Battle Armor x=50, width=82,
  ending at 132 beyond the 120-pixel window, on both sides.
- rc7 + intermediate three-edit fix: `rc7-final-both`; Battle Armor x=30, nickname x=16,
  complete on both sides; battle reaches the command menu.
- Current English build + intermediate three-edit fix: `final-both`; maximum-width EmbodyAspect
  x=28/width84, Feraligatr’s width78/x16, complete on both sides.
- rc7 + final two-edit fix: `rc7-two-final`; EmbodyAspect and Feraligatr’s
  fit on both sides, retaining the original row staggering.
- Original report's natural trigger: Heracross uses Aerial Ace against Drapion
  with Battle Armor, `en2` versus earlier two-instruction `fixed` captures.

The reusable runner `emu_ability_banner.py` uses Mold Breaker on both Pokémon
to trigger both banners, then overrides ONLY the banner renderer's ability-id
argument to request the diagnostic label. This is a display fixture, not a test
that Battle Armor has Mold Breaker's effect. Both sides' native font widths,
window dimensions, text coordinates and settled screenshots are captured.
No doubles-specific screenshot or real-hardware replay was performed; doubles
use this shared renderer but their screen placement remains unverified.

Run from worktree root:

```
ARMIPS=/path/to/armips /path/to/venv/bin/python -m unittest discover -s work/tools -p test_ability_banner.py -v
/path/to/venv/bin/python work/tools/emu_ability_banner.py --rom <ROM> --sav <existing-save> --out work/build/ability-banner/<case> --ability 4
```

Private inputs (SHA256): Chinese
`4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8`;
released rc7 roundtrip
`81ec4501ef92c01872e97fc61d1e763c84cb1e7fcb92164ed1aa1623e1b9ec39`;
rc7 + final fix
`ba524e4d06a5b04f1bdf1a59069ee24fb5c9c0f60ee9ee64ae6b974c9e57b0f2`.
No ROM or third-party game text is committed or published.

## Review

Separate reviewer confirmed the disassembly and recommended retaining the
original row staggering. Follow-up review verified the final two-constant fix
and its bounds; corrected the maximum Latin nickname example from Feraligatr’s
to WWWWWWWWWW’s (83 pixels). Native single-battle tests cover both sides;
no doubles-specific visual acceptance is claimed.
