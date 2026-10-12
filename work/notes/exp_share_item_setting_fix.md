# Exp. Share item and the SHARE setting (rc8 #bugs report, konando)

Status: FIXED on `fix/exp-share-item-setting` (decision D-2346, amends D-2301). Not merged, not pushed.

## Report
Setting SHARE to OFF (Options page 2/2, DIFFICULTY) also stopped a held Exp. Share (item 216) from giving EXP to the holder.

## Decision
First pass of this note found it was the documented design (D-2301, research/growth.md, guide). The maintainer then decided (2026-10-12): a held Exp. Share keeps working with SHARE OFF. The holder gets the same half EXP and EVs as with SHARE ON (the hack's share amounts), still clamped by CAP; non-holders stay off. The Chinese hack has no SHARE setting (sharing is always on and the per-recipient routine never reads the held item), so there is no D-1002 reference.

## Root cause
`dg_growth_share_enabled()` (native/growth.c) replaces the always-true getter call at overlay 14 `0x022289EA` and took no argument, so with SHARE OFF it returned 0 for every non-participant, holders included.

## Fix (research/difficulty-armips, the resident payload)
- `native/growth.c|h`: `dg_growth_share_enabled(uintptr_t battle_mon)`. Snapshot missing: native getter (1). SHARE ON: 1. SHARE OFF: 1 only if the recipient is a verified local BattleMon (id 1..6, resolver maps back to it, backing pointer in RAM) whose held item, read with the engine's own `GetMonData` (`0x0206D848(backing, 6, 0)`, as Lucky Egg is read at `0x02228A18`), is 216; otherwise 0. The item is not read with SHARE ON.
- `native/runtime.asm`: new `adapter_r4` used for `DG_Share`: first ARM word `mov r0,r4` (r4 is the recipient BattleMon at the call site; the original getter ignored its arguments). Stub area 160 -> 176 bytes (`runtime_hooks.json`, `build.py`).
- `native/integration_contract.json`: source overrides for growth.c/h (pinned sources).
- Docs: guide `site/.../difficulty.md` (SHARE bullets, Known issue for rc7), faq.md, research/growth.md, IMPLEMENTATION.md, CHANGELOG [Unreleased] Fixed.
- Decision D-2346 (technical/optional-difficulty), source `agent:exp-share-item-setting`; renumber at merge if D-2346 is taken.

## Proof (DeSmuME, fresh builds, SDL_AUDIODRIVER=dummy)
Driver: `tests/native_battle.py --scope holder --kind wild|trainer|double --expect fixed|baseline`. Party: fighter 1 (Lv12), fighter 2 (Lv8), one Lv11 bench slot 3 EXP below the cap-12 threshold holding an Exp. Share or nothing. Wild = scripted WildBattle (Magikarp Lv15 HP1); trainer = TrainerBattle 5 (singles, enemy HP1 Splash-only); double = TrainerBattle 6,6 (flags 3; fighter 1 Swift, fighter 2 Splash, two foes KO'd; foes' HP1 Splash-only). Options set through the real menu (held L), no outcome writes. Bench slot EXP / HP-EV gain:

| battle | build | SHARE ON holder | SHARE OFF holder | SHARE OFF plain | SHARE OFF + CAP ON holder | SHARE OFF + CAP ON plain |
|---|---|---|---|---|---|---|
| wild single | rc7 (without fix) | 95 / +1 | **0 / 0** | 0 / 0 | 0 / 0 | 0 / 0 |
| wild single | with fix | 95 / +1 | **95 / +1** | 0 / 0 | **3 / +1** (clamped to cap) | 0 / 0 |
| trainer single | rc7 | 79 / +1 | **0 / 0** | 0 / 0 | 0 / 0 | 0 / 0 |
| trainer single | with fix | 79 / +1 | **79 / +1** | 0 / 0 | **3 / +1** | 0 / 0 |
| trainer double | rc7 | 158 / +2 | **0 / 0** | 0 / 0 | 0 / 0 | 0 / 0 |
| trainer double | with fix | 158 / +2 | **158 / +2** | 0 / 0 | **3 / +2** | 0 / 0 |

Every run also passes the strict per-event oracles (singles: lifecycle, snapshot, share wrapper result per recipient with the BattleMon argument checked, eligibility, EV pass, application/command/cache/backing checksum; doubles: lifecycle, snapshot, share results, amounts, party deltas). Fighters get identical amounts in all runs. The pre-existing `--scope matrix` (6 wild battles, 3 slots) still passes on the fixed build. Result files: `work/build/difficulty-v2/tests/native-tests/rerun-{fixed,baseline}-{wild,trainer,double}/result.json` (baseline from worktree `~/Developer/poke-fix-exp-share-item-setting-baseline`, detached develop e21ab4b + the same test files).

Regression tests (default suite, `tests/run.py`: 220 tests pass): `drivers/growth_check.c` (SHARE ON/OFF x item 216/other/none, unverifiable recipients, ID gate), `runtime_abi_model.py` (DG_Share passes r4, restores r4..r11, sp), `ExpShareHolderOracleTests` (oracle accepts the fix, rejects each regression, accepts baseline under `--expect baseline`).

`check.py`: asm-synth, registry, fixes-md PASS. `tests` step fails only on pre-existing items identical on develop: `test_honey_gather` setUpClass (needs built data) and `test_hardcoded.test_scan_finds_outfit_chooser`; ruff E501 in `work/tools/fixes.py:1787` (also on develop).

## Notes and open points
- Not run: link battles, Battle Frontier, Safari, replays (excluded from the settings anyway), wild doubles, a holder that is also a participant (unchanged native path), eggs/fainted/Lv100 holders (native eligibility `0x0221F6EC` unchanged and still applies).
- Harness observation, not investigated: a 4-slot party where a Pokemon in slot 4 holds an item came back with a garbled record right after a wild battle in some runs (sampled 180 frames after the battle; with 900 frames it was fine in the first run and not reproduced on the 3-slot fixtures used here). Probably mid-processing sampling, but unverified; it may be worth a look if players report corrupted 4th-slot Pokemon.
- The rc7 tester xdelta is unaffected; a fixed ROM needs the next `build.py --enable-difficulty` run (resident bytes 8500 -> 8620).
- Question for Shishio: guide Known issue says "fixed for the next release after rc7"; reword at release (like the story-battle fix).
