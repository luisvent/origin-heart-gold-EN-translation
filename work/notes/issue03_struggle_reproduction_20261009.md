# Issue 3 — zero-PP Struggle reproduction, 2026-10-09

**Reproduced on untouched Chinese v4.0.3 and pinned English RC7.** This is a real
rejected attack selection, not a `battle_turn()` timeout. No production patch,
ROM build, decision edit, source-save edit, download, or commit was made.
Authorization is D-2300; the earlier finding is D-1576.

## Inputs and exact commands

All commands were launched from the repository root. Existing local `.venv`,
DeSmuME 0.9.12 ARM64, ROMs, and save were used. One emulator ran at a time.

| Input | SHA-256 |
|---|---|
| `work/rom/origin_v4.0.3_cn.nds` | `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8` |
| `work/build/rc7/candidate/origin_hg_v4.0.3_en_wip.nds` | `b16f81bec13b07730ee544fbe24aead4229eccf04368f186aa71abe0b48710df` |
| `work/build/memcheck/full_bag_6mons.sav` | `b3aca10747cd0f1adc3d5852a50dddaaa36ed8680f5ba04012cfe3110faad90f` |
| Scratch `reproduce.py`, final version | `79198e63e49ec1cb74e40a932d6e72e423d3b1da821195f17bdec3729e720833` |

```sh
.venv/bin/python work/build/bugfix-sequential-20261009/issue03/reproduce.py --rom work/rom/origin_v4.0.3_cn.nds --out work/build/bugfix-sequential-20261009/issue03/repro-cn
.venv/bin/python work/build/bugfix-sequential-20261009/issue03/reproduce.py --rom work/build/rc7/candidate/origin_hg_v4.0.3_en_wip.nds --out work/build/bugfix-sequential-20261009/issue03/repro-rc7
```

Native emulator startup aborted with host exit 134 inside the sandbox before
game execution. The required command was rerun with `require_escalated`; both
completed normally outside the sandbox. This host abort is not a game defect.
An initial probe also exposed a relative output path failure after the harness
changed its process directory. The scratch runner now resolves paths before
starting the harness; this failed before any battle evidence was captured.

## Fixture and reachability limits

`start_at(109, 16, 14)` copies the untouched save into its private temporary
directory. At noon 2026-10-09, the hack's native debug generator creates a level
20 Gastly. Its closed encrypted record is strictly decoded/checksum-validated,
copied to party slot 0, and the private party count becomes 1. Only the specified
move/PP fields are then changed with the existing strict codec. This never
changes the original battery save; both result files verify its final hash.

The battle is injected with exactly `TrainerBattle 185, 0, 1, 0`, retaining the
Route 12 must-lose argument. This proves trainer-battle move selection on a valid
actor. It does **not** establish a natural story route to Newt or loss cleanup.
The fixture retains the seed's Bag and Leppa Berries, so this report makes no
claim of an inescapable trainer-battle softlock. Trainer 5 and wider regression
cases are deferred to the separate fix stage at the coordinator's request.

Each case starts from the same generated field state. Each move/input attempt
restores its own ROM's command-menu state. The UI actor PP/moves are read from
native battle memory, not from a possibly open/decrypted party record. No
in-battle encrypted-party snapshot is decoded or repaired.

## Results

| Case | Native moves / PP | CN | RC7 |
|---|---|---|---|
| Four known moves exhausted | `[122,101,247,310]` / `[0,0,0,0]` | All four touch choices return usability code 2 | All four touch choices return code 2; D-pad/A slot 0 also returns 2 |
| One known move, three empty slots | `[122,0,0,0]` / `[0,0,0,0]` | Lick returns code 2 | Lick returns code 2 with touch and D-pad/A |
| One available move control | `[122,101,247,310]` / `[0,0,1,0]` | Lick rejected; Shadow Ball passes and consumes its PP | Same; Lick D-pad/A rejected too |

The Chinese run's original A-only attempts did not enter the move validator and
are **not evidence of rejection**. The RC7 runner adds UP before A, activates
the selection cursor, and records the same native rejection as touch. This is
why input timeout was not used as an oracle. The final runner includes UP/A for
both ROMs; CN touch evidence is complete without rerunning solely for that input.

Native UI actor addresses differ as expected: CN `0x02307AE0`, RC7 `0x02307A3C`.
Known move count is 4 or 1 as appropriate; maximum PP are `[30,15,15,15]` or
`[30,0,0,0]`. All rejected selections preserve HP and native PP. Screenshots show
`舌舔PP用尽了！！` in CN and `Lick is out of PP!` in RC7, with the ordinary four
move menu still displayed. After dismissal, menu setup runs again. No zero-PP
attempt reaches the action validator. No Struggle move 165 appears in the trace.

In the positive control, usability returns 0; action validator returns 0 with
the first two record halfwords both 247 (Shadow Ball). Native battle PP falls
from 1 to 0. CN action actor is `0x023084A0`, RC7 `0x023083FC`; these are executor
actors distinct from the UI actor, with matching moves/PP. The record's first 16
bytes are `f700f700500067480702000000000000` in both. Thus normal inputs and turn
submission work on the same fixture, and the failure is specifically exhaustion.

## Native rejection path and repair recommendation

Live RC7 trace and byte-identical CN neighborhoods establish this path:

1. Move-choice state handler `0x02202F4C` extracts the selected move from its
   command data at `0x02202FE2..0x02202FF2` and calls wrapper `0x0222C640` at
   `0x02202FF4` (live wrapper LR `0x02202FF9`).
2. Wrapper calls usability function `0x0222C304` at `0x0222C658` (live LR
   `0x0222C65D`). The selected ordinary move is passed unchanged.
3. That function checks move PP through `0x02216EDC` at `0x0222C330` and returns
   **2** at `0x0222C338..33C` when it is zero. It already accepts Struggle 165
   immediately at `0x0222C310..318`.
4. Wrapper returns **1** to the handler for each exhausted move (0 for the
   positive control), builds the ordinary rejection message, and the handler
   enters state 6 at `0x02203016..18`, later reopening the move menu.
5. Passing selection enters state 3 at `0x0220301C..1E`, subsequently submits
   the action, and reaches `0x0221D7A8`. Exhausted selections never get this far.

The repair should restore an aggregate zero-PP fallback in **command selection**,
before ordinary per-move rejection. Start at handler `0x02202F4C`, especially
its initial state: guard `0x0222C550` call at `0x02202F7C`, followed by the move
menu activation `0x02211774` at `0x02202F9C`. Trace the guard and command-record
construction before choosing the exact production hook. Generate a Struggle
action through the existing executor/target path only when every **known** move
has zero PP; empty slots must not count as available moves. Preserve this
reproduced normal positive-PP selection and zero-PP individual rejection.

Do not patch either validator to simply accept ordinary moves with zero PP.
Do not alter Newt's party/script, erase the UI's known moves, or patch the
`0x02218EE0` fallback getter without proving its role. Disabled/Taunt/Encore/
Choice restrictions, enemy exhaustion, doubles, recoil and outcome remain
implementation-stage regression questions, not claimed fixes here.

## Evidence and reproducibility

Everything executable/data-heavy is ignored scratch under
`work/build/bugfix-sequential-20261009/issue03/`:

- `reproduce.py`: bounded runner; default three cases, finite menu wait/input
  loops; imports existing strict harness. Supports `--trainer` and `--cases`.
- `repro-cn/result.json` and `repro-rc7/result.json`: full native entry/return
  traces, closed field fixture validation, hashes, per-attempt final actor PP.
- Same directories: field and per-case same-ROM command savestates, choice,
  command, FIGHT and after-dismissal PNGs. Do not load a CN state into RC7.
- `verified_summary.json`: independently asserted from both completed results:
  every exhausted touch choice returned 2, reached no action validator, and
  preserved PP; positive selection passed both validators and consumed last PP.
- `live-sites.txt`, `live-callers.txt`, `command-selection.txt`,
  `command-guards.txt`: local overlay disassembly for the live path above.

| Evidence | SHA-256 |
|---|---|
| CN `result.json` | `04f5cb2e11692a7868653a4e3e865b238bab5d2ca68338380af3dac7e8671ac2` |
| RC7 `result.json` | `0ac1f4e8801bd8fc2ddb2e731cd1973c6a781bbefd8b8fc8e6a67dc10347cef1` |
| CN `four-zero-command.dst` | `c252046438cccc37e2fb90a55a4312d2f5de08a26ac7414a7955bec871e4f508` |
| RC7 `four-zero-command.dst` | `b5de3b2550be7b5c9f3b4b7cdc1aad1ef92ea962878ed1657d1f4bc4f96ada3b` |

Falsified hypotheses: translation-only regression (same CN failure), malformed
empty slots as sole cause (four real moves also fail), bad party crypto (strict
closed-record validation and correct native actors), ordinary touch failure
(validator receives exact chosen move, plus working positive and RC7 pad
controls), and execution-stage PP rejection as the cause (never reached).
