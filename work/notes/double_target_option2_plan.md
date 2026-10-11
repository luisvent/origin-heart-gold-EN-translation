> Historical implementation/validation record from the isolated worktree, preserved on 2026-10-09.
> Its clang generator and legacy manifest references describe that checkout. Current armips source,
> tests and commands: [double_target_armips_port.md](double_target_armips_port.md).

# Double-battle targeting: Option 2

The user approved implementation in an isolated worktree on 2026-10-06 and requested sequential
subagent review and production-readiness testing. This is a specific exception to D-1002/D-1337;
it does not authorize fixing other inherited gameplay bugs. The eight `dbltarget2-*` patches are
enabled in this worktree's `code_patches.json`. No release has been published.

## Player-visible behavior

The untouched v4.0.3 hack can trap a double-battle target cursor on an ally after either foe slot
becomes empty. It also carries a partner's self-target choice into the next battler's selection.
Option 2 opens on a living eligible foe, left first, retaining an eligible remembered foe.
It keeps the hack's straight-line navigation, but retries the other column when a vertical search
would otherwise stay stuck. CANCEL remains selected instead of being repaired away every frame.

Target memory remains shared. Deliberate ally selections are not remembered on re-entry; Up from
CANCEL uses the right column, as in the hack. Per-battler memory and full vanilla behavior (Option 4)
are outside this change. Spread moves retain the native first-eligible order and engine value.

## Implementation

`work/translate/hardcoded/double_target_option2.s` is original Thumb assembly for ARMv5TE.
`work/tools/double_target.py` assembles it with local clang and reproduces the eight manifest entries.
It reads expected bytes from the user's untouched CN ROM and refuses regeneration if they differ
from the checked-in expectations. The normal build's stage 3c applies these entries through
`hardcoded.apply`; no new build stage is needed.

Overlay 14 base: `0x022007E0`.

| Patch | Runtime address | Purpose |
|---|---|---|
| code | `0x02212784`–`0x02212827` | Exactly 164 bytes, replacing first-eligible and navigation in place |
| navcall1–4 | `0x02212880`, `0x02212896`, `0x022128AE`, `0x022128C4` | Call new navigation at `0x022127BC` |
| entry | `0x02212596` | Call entry wrapper at `0x022127AA` |
| fallback | `0x02212A2C` | Single-target repair calls foe-first entry at `0x02212788` |
| cancel | `0x02212A1A` | Preserve CANCEL; unsigned check still rejects invalid negative/large values |

The native-order entry remains at `0x02212784`. All five spread callers retain their original bytes.
There is no overlay growth, memory allocation, ITCM change, save-format change or ARM9 patch.
Every patch checks its expected original halfwords before writing. Regeneration from an already-patched
ROM is rejected. Saved-ROM comparison confirms exactly 164 changed bytes, all in overlay 14; every
other filesystem file, ARM9, ARM7 and both overlay tables is identical to its input.

## Harness reliability

The game temporarily decrypts party records in place. Harness party reads/edits now wait at most
120 frames for encrypted, checksum-valid data without the Bad Egg flag. Swaps validate both slots
in the same frame. Writes are read back; the encoder rejects corrupt input rather than calculating
a fresh checksum over it. Waiting inside emulator hooks is rejected to prevent recursive emulation.
Tests cover transient records, timeouts, corrupt records, swapping, generation and write failures.
This affects test tooling only, not the ROM.

## Reproduction

Run from the worktree root with the existing local project venv (ndspy, capstone, py-desmume, Pillow).
No downloads are required. Supply your local ROM and save paths; keep all generated ROMs, states,
screenshots and reports in ignored scratch storage.

```sh
.venv/bin/python work/tools/double_target.py --rom work/rom/origin_v4.0.3_cn.nds --check
.venv/bin/python -m unittest -v work/tools/test_hardcoded.py work/tools/test_double_target.py work/tools/test_emu_harness.py
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy EMU_HARNESS_DATA=/path/to/main/work \
  .venv/bin/python work/tools/emu_double_target.py --rom /scratch/cn.nds --case lastR --out /scratch/cn-lastR
```

The headless SDL setting avoids a macOS application-registration abort before ROM boot.
The test tool pins the clock and verifies party checksums before battle setup.

## Validation

- All 63 unit/host tests pass, with local-ROM tests enabled.
- Real assembled bytes: 16 native-order masks, 16 foe-first masks, 320 navigation cases,
  256 repair cases and 224 entry cases. Exactly 11 previously stuck navigation cases change.
- Tests verify stack balance, callee-saved registers, mask-builder arguments and caller-saved
  register/flag clobbering at external calls.
- Isolated copies of CN and current EN WIP were patched through `hardcoded.apply`, saved, reloaded
  and verified. Original ROMs and `work/build/` were not written.
- Regression suite `open,arceus,vqueue`: all six CN/EN checks pass.
- Negative control: the untouched CN ROM fails the same harness on the original CANCEL repair
  behavior. Removing a required command from a field/spread report also fails validation.
- Final live matrix: **22/22 pass**, 11 cases on both CN and EN, completed 2026-10-07.
  Cases: lastR, lastL, leak, field, spread, multi, wildR, wildL, cancel, empty, single.
  The multi scenario explicitly knocks out both replacements; an initial test that relied on
  the AI partner to finish the second foe was rejected by the empty-slot assertion and corrected.
- Field/spread checks observe the actual representative returned to the battle engine, require
  all four planned commands, and verify the next turn. CANCEL covers A, B and re-entry; empty
  foe touch is rejected before key navigation; singles complete three turns without target selection.
- Machine-readable summary and input/output fingerprints: `double_target_option2_validation.json`.
  Raw screenshots, states and logs remain local under `work/scratch/double-target-option2/`.

## Release-note wording and credit

Fixed a double-battle D-pad targeting trap after an opponent runs out of Pokémon. Target selection
now starts on a living foe, left first, and CANCEL remains reachable. Spread-move targeting is unchanged.

Credit the Bradams/Speedoption fork for independently diagnosing the same issue. No code or patch
bytes from that fork are used. Distribute only the normal xdelta patch, never a ROM.
