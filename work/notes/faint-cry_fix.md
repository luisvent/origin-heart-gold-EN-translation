# Faint cry and faint sound (fix `battle-faint-cry`, D-2341)

Known gap (D-1598 item 3, site FAQ "Some moves have no sound"): opposing Pokémon don't cry when they faint. The
user asked on 2026-10-09 to fix it ("We want to fix these bugs, so for each issue create a worktree per issue,
and use a separate subagent to fix, test and review.").

## What HeartGold does

HeartGold's faint task (USA overlay 12, the state machine around `0x022601FA`) does, for a Pokémon of either
side, before the sprite slides down:

1. state 4: `PlayCryWithChatter` (USA arm9 `0x0207204C`) with **mode 5** (the faint cry: lower and slower),
   the sprite's species and form, volume 127, heap 5, no delay, and pan **+117** when the sprite faces front
   (the foe) or **-117** (the player's side, back sprite);
2. state 5: wait while a cry is playing (USA arm9 `0x02006360`);
3. state 6: `PlaySEWithPan(1795, pan)`: `SEQ_SE_DP_POKE_DEAD3`, the falling sound, same pan;
4. then lower a raised sprite, set up the partial draw and slide it down 8 px a frame.

Sequence names are from the SDAT's symbol block (`SEQ_PV` = 2 is the sequence every cry plays through).

## What the hack does

The hack's own battle engine (overlay 14) shows a faint with client command 21; its handler calls
`Faint_Run` (`0x0222CB7C`) every frame until it returns 1. `Faint_Run` keeps its state in `0x02255EDD`
(`0x02255EDC` + 1): 0 prepare (`0x0222DBB0`), 1 wait while a cry plays (arm9 `0x02006258`, the hack's copy of the
USA wait) then start the health-box task (`0x0222DF40`), 2 lower a raised sprite (attribute 0x29), 3 partial
draw, 4 slide, 5 wait for the health box. It is HeartGold's task without states 4 and 6: no cry, no
sound, and state 1 waits for nothing. The other callers of the cry routine (`0x02006898`) are the send-out
cries (`0x02230684`, mode 0) and the arm9 `PlayCry`; nothing plays mode 5 or 1795 in battle.

Observed on the untouched Chinese ROM (DeSmuME hooks on `Faint_Run`, the cry routine, `PlaySEWithPan` and
`NNS_SndArcPlayerStartSeqEx` `0x02006B64`): a wild Magikarp fainting and the player's Magikarp fainting both run
`Faint_Run` (states 0, 1, 2/3, 4, 5) with no cry and no sound. Both sides are affected, not only the foe's.

## Fix

`work/patches/battle-faint-cry`: `Faint_Run` is rewritten in its own 352 bytes (same entry, same states, the
same calls in the same order). Compacting frees the room: the facing value (0 back, 2 front) without its
stack round trip and byte mask, one shared "set state" tail, state 3 reading species, form and gender from
the MonView directly (the three getters are single loads), and state 4's `y += 8` as `Sprite_AddAttr(1, 8)`
(arm9 `0x02008BC8`; attribute 1 is the same halfword +0x26 as get/set). The freed bytes add:

- state 0, when the preparation is done: the hack's cry routine `0x02006898(mode 5, species, pan, 127, heap 5,
  delay 0, form)`, pan = (facing - 1) × 117;
- state 1, once the cry has ended (the existing wait): `PlaySEWithPan(1795, pan)` (arm9 `0x02005F3C`).

Not as in HeartGold: Chatot plays its normal cry, never a Chatter recording (the hack's send-out cries do the
same and the hack has no chatter-aware cry call here). Command 21's handler and its table entry are not
touched (another branch moves that handler).

## Tests (2026-10-09)

ROMs: the untouched Chinese ROM; this branch's build (`build.py --no-patch`); the control
(`--without battle-faint-cry`, SHA-1 `85d0c887…`, the develop build's hash).

**DeSmuME**, `emu_harness.py fixes --case battle-faint-cry` (scenario `faintcry`): PASS, build `fixed`,
control `original`; the same scenario on the Chinese ROM judges `original`.

| Case | Build: cries (species, pan) then 1795 (pan) | Control / Chinese ROM |
|---|---|---|
| wild Magikarp KO'd by Thunderbolt | 129 +117, then 1795 +117 (68 frames later, after the cry) | faint, no sound |
| our Magikarp (1 HP) KO'd by a wild Rattata | 129 -117, then 1795 -117 | faint, no sound |
| Golem's Explosion on a wild Snorlax | 76 -117, 1795 -117; 143 +117, 1795 +117 | two faints, no sound |
| trainer 252 (two Pokémon) | 81 +117 / 345 +117, each with 1795 | no sound |
| double battle `TrainerBattle 252 252`, Heat Wave KOs both foes in one turn | 81 +117, 1795; 345 +117, 1795 (back to back) | no sound |

Every cry has mode 5, volume 127, heap 5, delay 0 and its SEQ_PV start in the same frame. The sprite
attribute calls of a whole faint (raise, partial draw, the eight slide steps, the height) were logged with and
without the fix: the same values in the same frames relative to the state changes.

**melonDS 1.1** (headless backend, `MELONDS_SHIM` from the main checkout), `route1_path_2mons.sav`, a wild
battle on Route 1; read watches on the SDAT INFO records of sequences 2 and 1795, a write watch on the state
byte:

| ROM | Psycho Boost KO | Explosion (both faint) |
|---|---|---|
| this build | SEQ_PV read in the frame state 0 → 1, 1795 started (PlaySE path `0x0200540A`) 28 frames later, then the slide; battle ends | the same for each of the two faints |
| control | states 0 → 1 → 3 → 4 → 5 in five frames, no sequence | the same, twice |
| Chinese ROM | – | the same as the control |

No ARM9 abort on any run. Not tested on hardware.

`check.py` and `check.py --full` pass (see the commit).

## Verifier hardening (2026-10-12)

The review found that `judge_faintcry` could report `fixed` after both sounds played even when the faint
stalled. It ignored the recorded turn results, field return and state history; incomplete silent controls
could likewise be labelled `original`.

Both verdicts now require a successful terminal turn (`field`, or `fled` in the player-faint case), only
`menu` results before it, and `in_field = true`. Every faint window must record the complete entry-state
path `0,1,3,4,5` or `0,1,2,4,5`. The latter is the raised-sprite path: state 2 executes state 3 in the same
call, so the entry hook does not see a separate state-3 call. State 5 alone cannot prove completion because
it waits for the health box; the successful field return is required too. Missing evidence fails closed
as `unclear`. Older observations without this evidence need a new run.

Verification: 140 fault cases (failed/missing turns, failed/missing field return, truncated or reordered
states, across all five scenarios with and without sounds) failed against the previous judge and pass
after this change. Complete observations, successful player escape and both sprite paths retain their
expected verdicts. All 74 tests in `test_emu_fixes` pass. This is verifier-only validation; no new emulator
run or ROM build was performed. The judge checks sequence-start ordering, not actual cry-end timing or
audible output; its docstring now states that limit.
