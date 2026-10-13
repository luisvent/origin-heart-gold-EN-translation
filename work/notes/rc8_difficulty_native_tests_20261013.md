# rc8 difficulty feature: native test changes (2026-10-13)

Scope: only test recipes and oracles under `work/research/difficulty-armips/tests/`
changed. The candidate ROM (`work/build/difficulty-v2/integration-impl/candidate.nds`,
SHA-256 `d0185cfa...`), `native/policy.c`, the installer pins and all game code are
untouched. Native runs: `run.py --native --native-plan comprehensive --native-timeout 360
--require-complete` (102 jobs, 79 required cases).

## (a) Trainer-constructor return address

The double-battle-single-fallback fix wraps the trainer-battle constructor call, so the
observed return address is `0x02048EEF` (wrapper) as well as the original `0x020507AD`.
All oracles that check the constructor caller now accept both. Files:
`native_battle_oracles.py`, `native_entries_oracles.py`, `native_exclusions_oracles.py`,
`native_items_oracles.py`, `native_items_doubles.py`, `native_items_fixture.py`,
`native_items_persistence.py`, `native_multiko_fixture.py`, `native_multiko_oracles.py`.

## (b) Scripted double battle fixture

`native_entries.py`, fixture `trainer13`: the party is topped up to two Pokemon. With the
double-battle-single-fallback fix on, a scripted double battle where the player has one
Pokemon becomes a single battle, which is not what the entry-constructor case tests.

## (c) Roster id override

`native_battle_input.py`: the `roster_ids` override applies only when the run has `slots`.
The earlier change (commit 6d81d87) applied it to every run and broke MultiInput's id 14.

## (d) ITEMS recipes after D-2412 (DEFAULT = Chinese item rules)

Finding, derived from the untouched Chinese ROM (`a/0/1/7`, battle mask = bits 11..15 of the
u16 at offset 8, the same field `prepare()` already pins) for every item in
`native_items_cases.CASES`:

- Allowed in DEFAULT (nonzero Chinese mask): Potion 17 (mask 4), and the four items that
  were already native-eligible: Pecha Berry 151 (8), Oran Berry 155 (4), Leppa Berry 154
  (16), Blue Flute 65 (8).
- Mask 0 (denied in DEFAULT, ALL-only): the other 20 medicines, 18-25, 27-29, 34, 35,
  37-42, 54. Potion is therefore the only item in `CASES` outside the twenty additions
  that DEFAULT allows; no other item in `CASES` is allowed. (The Chinese table has 56
  nonzero masks in all: Poke Balls 1-16, Super Potion 26 and the other drinks/powders/juice,
  X items 55-64, further berries and flutes, items 492-500; none of those beyond the
  five above is in `CASES`.)

Changes:

- `native_items_cases.py`: Potion has `restricted_allowed=True` (visible and usable in both
  modes, same treatment as the berries). New `GATE_ITEM = 25` (Hyper Potion): an
  addition with the same HP-1 fixture as Potion, used wherever a probe needs an item that
  DEFAULT denies.
- Gate probes (`native_items_gates.py`, `_gates_oracles.py`, `_gates_matrix.py`,
  `native_items_doubles.py`, `native_items_remembered.py`, `evidence.py`,
  `native_composites.py`, `run.py --items-gate-item`): the stocked medicine, the
  injected selected-item input, the "restricted list excludes it" check and the
  evidence claim use `GATE_ITEM`. The injection bytes in the doubles driver derive from
  `GATE_ITEM`. Invalid-id slices (791, 65535) are unchanged.
- Persistence (`native_items_persistence.py`): the first battle uses Hyper Potion in ALL
  (expected HP is `min(maxhp, hp + healing)` instead of the Potion constant 21), the
  second battle (DEFAULT) must natively deny the remembered Hyper Potion and not list it.
- Job ids: gate and doubles jobs `...-item-00017` became `...-item-00025`
  (`gate-persistence-item-00025`, `gate-<gate>-item-00025`,
  `gate-doubles-<gate>-slot<n>-item-00025`) via `PERSISTENCE_ID` / `GATE_ITEM` in
  `native_plan.py`. The Potion pair `item-017-category-0-{all,restricted}` and its
  no-effect pair remain and now run the "native-eligible in both modes" path.
- Host tests: `test_native_items.py` restricted-denial tests use the Antidote sample (a
  DEFAULT-denied item) instead of Potion. New tests:
  `test_default_and_all_visibility_contrast` (a DEFAULT-allowed item hidden in DEFAULT
  fails, an addition visible in DEFAULT fails, an addition hidden in ALL fails, Potion
  hidden in ALL fails; each asserts the specific oracle message) and
  `test_default_allowed_flag_matches_untouched_chinese_item_metadata` (reads the Chinese
  ROM and checks `restricted_allowed` / `usable()` for every `CASES` item; skipped when the
  ROM is absent). Gate, doubles, persistence, remembered, composite and suite tests follow
  `GATE_ITEM`. `tests/README.md` has a short DEFAULT revision section.
- Host result: 222 tests (was 220) OK; `ruff check` clean.

Note: the native suite binds the test sources (README included) to each run, so no file
under `tests/` may be edited while a native run is in progress (a README edit mid-run
produced "stale slice binding" and a wasted run).

## Results

- Host: 222 tests OK, ruff clean.
- Bounded slice (`--native-phase items --items-item 18 --items-scope single`): 2 jobs
  passed.
- Comprehensive plan, invocation 896cef6a (log under `work/build/rc8-harness/`): 102/102
  jobs passed, native cases 72/79. One transient failure on the way: `entries-grass`
  ("natural encounter absent", the random grass encounter did not trigger in the allotted
  time); retried with `--resume-suite ... ` (retry of failed/unstarted jobs) and passed.
  It does not touch items or any change above.
- The 7 cases not passed: `ui.visible_glyphs` (needs the visual attestation of the five
  focus PNGs, `--record-focus-review`, not run here) and six cases the manifest itself
  marks "No complete native driver assigned; requirement remains open"
  (`runtime.frozen_control`, `progression.erika_routes`, `items.contexts`,
  `items.reopen_pagination`, `runtime.exclude_replay`, `runtime.exclude_facility`).
  They have no job in the 102-job plan; this gap predates rc8.
- No genuine candidate defect was found; every failure was a stale test premise or flake.
