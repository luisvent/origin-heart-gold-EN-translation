# RC7 validation runner fixes (2026-10-10)

Prepared against `release/rc7-prep` at `5c35282092b6ded7b807ab23c19b524cf965552e`.
These changes affect validation tools and tests; they do not change game patches or ROM data.

## Healing: retain observation errors across trials

`emu_battle_heal.py` reset the trace before each trial but used only the final trial's
errors for its verdict. An earlier observation failure followed by a clean trial could pass.
Each trial now records a copy of its `hook_errors`; the top-level error list and verdict
use their aggregate. The existing top-level report fields remain compatible with `emu_fixes.py`.

Regression tests exercise the production runner, installed callbacks, exception guard,
and JSON reporting with synthetic emulator transport. They inject a failed memory read
in the first, middle, final, or multiple trials and require failure and retained diagnostics.
A clean multi-trial run must still pass. Restoring the original runner makes this regression
fail. Fault injection establishes reporting behavior, not a naturally occurring emulator fault.

Native DeSmuME validation used the existing RC7 artifact and existing control artifact
with the healing fix removed, with all eight default delays:

- RC7: eight menu recoveries, eight skipped off-field heals, no NULL reads, and no hook errors.
- Control: eight menu recoveries, a bar without a sprite and a NULL read in every trial,
  and no hook errors. This passes the expected-original-defect check.
- Both reports confirm unchanged ROM and save inputs.

## Struggle: expect the original last-PP rejection on turn two

`emu_struggle.py --without` previously excluded `last-pp` from rejection handling on both
turns. Turn one now retains its normal execution; the exhausted second turn follows the
original-ROM rejection path. The fixed ROM still must submit Struggle on turn two.

The turn input/dispatch code is extracted into `run_turn` for regression coverage.
An expected rejection now requires a current-turn usability observation for the selected
move and actor, no submitted action, return to the battle command menu, and unchanged
zero PP on the same battler. A timeout or missing observation cannot count as rejection.

Offline tests cover both modes and both last-PP turns, the other supported cases,
missing or stale usability observations, unexpected actions, absent menu recovery,
and nonzero/changed PP. Restoring the old condition makes the control test fail.

Fresh native runs confirm RC6 consumes its last Growl PP, then rejects the next selection
with zero actions; RC7 consumes its last Growl PP, then submits native Struggle with damage
and recoil. Both modes also pass `four-zero`, `one-zero`, `positive`, and `trainer5`.
Separate fresh processes pass `double,enemy` in both modes, completing all seven cases
across split runs.

The single default sequence stops at `double command absent`, before the changed turn
handler is called. The unmodified runner at the base commit reproduces the same failure
on the same RC7 artifact and seed. Both the original and changed runners pass the double
case in a shorter sequence. This pre-existing sequence limitation remains unresolved;
these results do not claim a passing single-process seven-case run.

## Checks and local evidence

- Targeted runner suites: 19 tests passed, zero skips.
- `test_emu_fixes.py` and `test_zero_pp_struggle.py`: 59 tests passed; four assembly tests
  skipped because the pinned armips tool is unavailable in this checkout.
- Independent read-only review found no concrete defects and repeated the 19 runner tests.
- `git diff --check`: clean.

Commands are run from this worktree root. Existing `.venv`, save-core build, ROMs and seed
were reused locally; no dependency downloads or ROM builds were performed.

```sh
.venv/bin/python -m unittest work/tools/test_emu_battle_heal.py work/tools/test_emu_struggle.py -v
.venv/bin/python -m unittest work/tools/test_emu_fixes.py work/tools/test_zero_pp_struggle.py -v
```

Ignored evidence is under `work/build/validation-fixes/`: `inputs.json`,
`summary.json`, `initial-runs.json`, `healing-red-green.json`,
`struggle-red-green.json`, `remaining-runs.json`, `sequence-runs.json`,
`healing-rc7/report.json`, `healing-control/report.json`, and the Struggle logs/results.
Runtime command arguments are retained by `initial-runs.json`, `run_remaining.py`, `check_sequence.py`,
and their JSON summaries. ROMs and saves must remain untracked.

Final SHA-256 checks confirm all three ROM artifacts and the seed are unchanged.
Prepared and validated in the `fix/rc7-validation-runners` worktree for integration
into `release/rc7-prep`. Local evidence remains in that validation worktree.
