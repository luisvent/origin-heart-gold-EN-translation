# Issue 3: zero-PP Struggle investigation — 2026-10-09

Investigation-only handoff. No emulator run, ROM build, production patch, shared-tool edit,
download or commit was performed. D-1576 is the historical finding; D-2300 records the
user's authorization for this scoped bugfix sequence. Goldenrod issue 4 is outside this work.

## Verified evidence

- D-1576 reports Chinese and English observations against trainer 185 and trainer 5:
  all four moves had zero PP, FIGHT opened the move menu, each choice was rejected,
  and no turn could be submitted. Historical evidence remains at
  `work/build/harness/bugreports-20261006/struggle/`. The folder contains screenshots
  and a ROM-data cache, but no runnable reproducer, result JSON, trace or savestate.
  This stage inspected `zero_en_full.png` and `tap_185_en/d_move0_afterA.png`:
  they visibly show Gastly with four zero-PP moves against trainer 185's Rattata.
  Screenshots alone do not independently prove all rejection messages or an endless loop.
- The guide's report identifies the original Route 12 command as
  file 199 `TrainerBattle 185, 0, 1, 0` (the must-lose parameter differs from
  `Harness.trainer_battle()`, which uses `0,0,0`). Preserve that distinction.
- The Chinese ROM still contains Struggle handling in overlay 14. Therefore
  deleting/replacing move data is not a justified starting point.
- All seven inspected code neighborhoods below are byte-identical in untouched CN,
  pinned RC7, and the current root English ROM. This does not prove the whole battle
  overlay identical; current English contains unrelated patches elsewhere.

Input identities, measured in this stage:

| Input | SHA-256 |
|---|---|
| `work/rom/origin_v4.0.3_cn.nds` | `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8` |
| `work/build/rc7/candidate/origin_hg_v4.0.3_en_wip.nds` | `b16f81bec13b07730ee544fbe24aead4229eccf04368f186aa71abe0b48710df` |
| `work/build/origin_hg_v4.0.3_en_wip.nds` | `6fa7b4e739391ca9ea9bfcf90d83eec6407c3c04102e52432bb41bc8ae44a7d3` |
| `work/build/memcheck/full_bag_6mons.sav` | `b3aca10747cd0f1adc3d5852a50dddaaa36ed8680f5ba04012cfe3110faad90f` |

## Native sites for the reproduction trace

Addresses are Thumb addresses in overlay 14, base `0x022007E0`. Descriptions are
derived from disassembly of the supplied local CN ROM, not imported upstream symbols.

| Address | Verified instruction behavior / useful observation |
|---|---|
| `0x02211D64` | Move-menu setup. Reads the active actor from UI-global `0x02255B90` + 4, then actor pointer at UI object + `0x1F4`. Copies every recorded move, current PP and maximum PP into the menu. The loop uses move count, not a count of moves with PP. |
| `0x02216E34` | Returns actor byte at `+0x29E`, used as move count. |
| `0x02216E40` | For slot `i`, returns move halfword at `actor + 0x25A + 0x12*i`, writes current PP byte `+0x25C + 0x12*i` through r2 and maximum PP byte `+0x25D + 0x12*i` through r3. |
| `0x02216F14` | Returns current PP from `actor + 0x25C + 0x12*slot`. Useful read-only hook to prove native battle PP, rather than merely save-record PP. |
| `0x02218EE0` | Returns the halfword at `actor + 0x252 + 0x12*slot`; returns 165 when slot >= 4 or the halfword is zero. **Caution:** this uses `+0x252`, while ordinary selected-move access uses `+0x25A`. This is a fallback getter in the engine, not yet proved to be the FIGHT/Struggle dispatch. Do not patch it based only on its return value. |
| `0x0221D7A8` | Move validation. r0 is actor; r1 points at an action record, whose first halfword is read as move. At `0x0221D850..0x0221D87C`, it resolves a move at record+2 to a slot and returns rejection code 1 when that slot has zero current PP, subject to existing bypass conditions. Its caller is `0x0221D71C`, call at `0x0221D722`; trace which path reaches it during choice. |
| `0x0222C304` | Separate move-usability check. Struggle (r1 == 165) immediately returns 0 at `0x0222C310..318`; a zero return from its actor/move PP lookup at `0x0222C330` yields code 2. Caller wrapper `0x0222C640`, call at `0x0222C658`. Distinguish this validator from `0x0221D7A8` when tracing. |

Additional useful native helpers: `0x022151BC` resolves actor by battler number
using global `0x02255BAC`, `0x02216E60` returns the selected-move halfword at
`+0x25A + 0x12*slot`, and `0x02216E70` searches that move list and returns slot 4
if absent. Struggle-specific exclusions also exist at `0x0221DB7C`, `0x0221DC68`
and later execution paths. They demonstrate existing support, not that a Struggle
turn executes correctly.

Ignored scratch evidence: `work/build/bugfix-sequential-20261009/issue03/` contains
`static_inputs.json` (ROM identities, exact compared ranges), `fight_entry.txt`,
`guards.txt`, `ui.txt`, `pp_callers.txt`, `validation_callers.txt`, `selection.txt`,
`callers.txt`, and immediate/constant searches. These are local native code evidence;
do not commit the disassembly dumps or ROM cache.

## Unproved cause and expected scope

The likely missing behavior is a command-selection fallback when the active
Pokémon has no usable move. Ordinary move validation rejecting a zero-PP move is
correct; bypassing every individual zero-PP rejection would let ordinary moves
execute without PP and is too broad. The move-menu setup legitimately displays
recorded moves, so changing its count to zero is also unsafe without tracing the
caller and action construction. The exact missing predicate or dispatcher has
**not** been located. The reproduction agent should follow the failing FIGHT
selection into these validators and capture caller/return values before choosing a hook.

Minimum requested behavior: FIGHT can submit Struggle when every known move has
zero PP, retaining ordinary move selection when any usable move has PP. Use the
existing Struggle executor, recoil, targeting and action-record rules. Whether
all moves disabled, Taunt/Encore/Choice lock, or other restrictions should also
trigger Struggle must be established from the native usability path, not invented
as an extension of the zero-PP fix. Do not change Newt's party or must-lose script
to work around the global bug.

## Reproduction handoff

Use existing dependencies and the untouched save. `start_at` copies the seed into
a private temporary directory; all fixture changes below affect only RAM/the copy.
Run one emulator at a time. No isolated checkout is needed for this read-only
reproduction; additive per-issue tools and patch files can avoid unrelated dirty
root work. If shared tool changes become extensive, take per-file snapshots first.

The following is a minimal runnable exploration recipe; it was **not executed**
in this investigation stage. The reproduction agent should turn it into a bounded
runner with assertions and hashes, native actor/action traces and saved screenshots.
Run it separately with CN and RC7; update the `ROM` and output path per invocation.

```sh
.venv/bin/python - <<'PY'
import datetime, sys
from pathlib import Path
sys.path.insert(0, 'work/tools')
from emu_harness import start_at, script_bytes, moveset, BATTLE_BUTTONS, MOVE_BUTTONS, ARR_PARTY
ROM = Path('work/rom/origin_v4.0.3_cn.nds')
OUT = Path('work/build/bugfix-sequential-20261009/issue03/repro-cn-zero')
OUT.mkdir(parents=True, exist_ok=False)
with start_at(109, 16, 14, rom=ROM,
              sav=Path('work/build/memcheck/full_bag_6mons.sav'),
              clock=datetime.datetime(2026, 10, 9, 12), out=OUT) as h:
    mon = h.generate_pokemon(92, level=20, item=0)  # native Gastly record
    party = h.array(ARR_PARTY)
    raw = h.read(party + 8 + 236 * mon['slot'], 236)
    h.write(party + 8, raw)
    h.w32(party + 4, 1)
    h.edit_party_mon(0, **moveset([122, 101, 247, 310], [0, 0, 0, 0]))
    h.log('fixture party', h.party())
    h.run_script(program=script_bytes(('LockAll',), ('TrainerBattle', 185, 0, 1, 0),
                                      ('ReleaseAll',), ('End',)))
    for _ in range(60):
        if h.on_screen('battle_menu'):
            break
        h.press('B', after=30)
    if not h.wait_screen('battle_menu', 1200):
        raise RuntimeError('trainer command menu absent')
    h.screenshot('command')
    h.save_state(OUT / 'command.dst')
    h.touch(*BATTLE_BUTTONS['fight'], frames=10, after=40)
    h.screenshot('fight')
    h.touch(*MOVE_BUTTONS[0], frames=10, after=60)
    h.screenshot('choice')
    for i in range(12):
        h.press('B', after=30)
        h.screenshot(f'after-choice-{i:02d}')
PY
```

Do not call `battle_turn()` as the initial oracle: it assumes a move can submit,
so its timeout alone cannot distinguish this bug from input/menu detection mistakes.
After save-state capture, restore that **same-ROM** state before testing each slot,
touch and D-pad/A inputs. Record native actor move ids/PP at the menu (above) and
the selected action/validator return code. The seed still has Leppa Berries in the
Bag; this is sufficient to prove rejected attack submission, but a fixture without
Leppa and with one usable party Pokémon is needed before claiming an inescapable
trainer battle. Reproduce trainer 5 with `h.trainer_battle(5)` as a generic control.
Use the full Route 12 event separately to validate story loss cleanup after a fix;
the injected command reproduces battle behavior but does not prove natural event reachability.

Recommended bounded matrix for the later fix: four known zero-PP moves; one known
zero-PP move plus three empty slots; one available PP slot (normal selection);
consume the last PP naturally and observe the next turn; player and enemy exhaustion;
single and double target selection; Leppa restoration and switching after exhaustion;
Struggle damage/recoil and a completed battle outcome. First prove the narrow core
on CN/RC7 before widening. For release validation use paired same-tree English
fixed/without-fix builds, plus untouched CN as original reference. melonDS/hardware
coverage can be added after DeSmuME's execution hooks locate the actual cause.
