# First native trainer ITEMS checkpoint

2026-10-10. Test-only addition; parent owns native execution. Shipping sources,
installer, harness and production ROM are unchanged. No emulator was started by
the implementation agent. Candidate 47f80277b9abedd35e554b4f30fb0844559d78d21ccf32d14a359afc94271e9a
is validated through its receipt, implementation inputs and artifact hashes.

Durable files: `tests/native_items.py`, `native_items_fixture.py`,
`native_items_trace.py`, `native_items_oracles.py`, `test_native_items.py`.
Runner/evidence/manifest registration and explicit ov9 identities extend the
existing test framework. Current checkpoint does not satisfy full ITEMS coverage.

## Input provenance and entry

Use the strict valid slot0 of local `work/build/memcheck/trainer.sav`, via the
existing `native_battle_fixture.py` sealed save-core API. Candidate personal and
growth archives recalculate level12 Rattata. Candidate move150 supplies Splash
PP40; closed typed edits remove other moves. Player slot0 starts at HP1; two
other player slots and the enemy are full HP. All held items/statuses are zero.
Candidate Potion record17 verifies dispatch2, effect discriminator1 and HP20.
The copied battery uses typed `setPocket` transactions: only Potion17 quantity3
in Medicine. Source battery, prepared battery, raw records and numeric metadata
are hashed under ignored build output. No official text is added to tests.

Fresh candidate ARM9 disassembly establishes the bounded ordinary trainer path:

- `02050798..A8`: flags1 for different first/second IDs with no special operand;
  calls constructor02050C34. Require native return LR020507AD and flags1/control0.
- Constructor02050CA4..AA allocates Pokémon parties through02073214 and stores
  them at setup+4,+8,+C,+10 (four-byte stride). That allocator reserves5B0h
  bytes and initializes capacity6/count0. Constructor02050CAC..B6 allocates
  **32-byte trainer-info records** at setup+F8,+FC,+100,+104; these are not
  Pokémon parties. `020507B0` copies player inputs; `020507C4` builds the
  trainer team via02072544, which calls0207272C for each occupied trainer.
  At0207273C..46 the builder reads setup+4+4*owner and initializes capacity6
  before populating the team. Thus the existing field launch seam is after
  population; the enemy party is at **setup+8**.
- `02050810` calls field launch0204FCE4 with r1=setup. Require LR02050815 and
  matching setup/save ownership. At this seam, before any begin, strict decode
  and archive metadata must confirm trainer5 has one valid live party record.
  Preserve its raw bytes even on decode failure, and never repair an invalid
  native record. Replace that valid input with the prepared healthy Splash-only
  record. No setup flags/control/options, live BattleMon, policy result or
  eligibility is written. Trace captures must independently confirm flags1/
  control0, published save, snapshot epoch/generation and copied Options.

Trainer5 metadata has one mon, singles and no trainer inventory. Static evidence
does not prove the live party copy layout: the native run checks those pointers,
capacity/count, hashes, HP and move inputs and fails on disagreement.

The parent's first run passed72 host tests but both modes stopped at the enemy
capacity/count assertion. The test incorrectly used setup+FC, reading trainer
info. No enemy write, begin or Bag observation occurred. This is a test pointer
error, not a demonstrated shipping bug. The corrected callback first persists
`trainer-launch-diagnostic.json`: launch registers, all1D4h setup bytes, and
bounded raw32-byte headers for all four party pointers and all four trainer-info
pointers. Capacity/count assertions retain exact6/1 and now print the actual
pointer and both values. Raw native mon bytes are still retained before strict
decode; an invalid record fails without repair or replacement.

## Read-only observations and inputs

Use candidate resident symbols for list attr, acceptance, remembered and both
commit adapters. Ov9 list construction021EC2CC returns lists at UI+3C with90h
category stride and four-byte entries; counts are UI+114F. Guard native ov9
probes explicitly, since the same RAM also holds field/Options overlays.

Battle Bag touch rectangles are read from ov9 tables021EE220 (categories),
021EE23C (six items/page) and021EE1B0 (Use/Cancel). HP category64,40; first list
item64,32; Use100,170. Field Bag helpers' first row y56 is unsuitable here.
Party target uses existing slot0 coordinates. Inputs are bounded and every
transition is screenshotted; the native confirmation sequence needs parent
feedback, not speculative additional input retries.

Read-only ov14 observations: parent02202954 provides controller;02200A30 encodes
the12-byte command;02221674 executes the item;02215A2C consumes by owner;
0221D7A8 proves the enemy's actual Splash turn. Final native mon HP/PP, all Bag
bytes, target gate and other party members are compared. Restrictions require
native empty lists/mask0 plus the observed blue Back button236,170 with unchanged command
destination/slot, inventory and mons. This is **not** a forced stale Potion at
acceptance or either backstop, and cannot certify their denial paths.

After the separate [shipping binding fix](items-binding-fix.md), the test reads
the Bag clone at setup+108 (native size864h). Setup+F8/args+0 is named
TrainerInfo throughout the new trace. Root/setup/Bag pointers are range-checked
before dereference; null/ITCM, misaligned and truncated ranges fail. Every
physical pocket slot is checked before accepting quantities, and all864h bytes
are retained so trailing-field changes remain visible. The old native run's
address0 inventory read is invalid evidence, despite its genuine HP1→21 and
owner0 consumption hooks.

State13 is now `fade_close_state13`, recording the selected item and category.
The parent's successful ALL path returned13 while preserving item17/category0;
this is accepted only with the real commit/target/command/effect/quantity/turn
proof. Restricted normal cancellation requires item0/category4 at fade and a
cleared selection through the parent Bag gate. State13 by itself proves neither
policy denial nor success. The old category screen ignored B; the next native
run uses the observed blue Back touch target without repeated blind inputs.

## Parent command and next feedback

From repository root:

```sh
.venv/bin/python work/research/difficulty-armips/tests/run.py --native --native-phase items --native-timeout 180
```

Each mode has its own supervised process (180 seconds maximum), terminal report,
nonce, trace and failure capture in `tests/native-tests/items_all` and
`items_restricted` under `work/build/difficulty-v2/`. No old state or forced
battle ending. Return `process.log`, `result.json` and the last screenshots for
the first failure before expanding the matrix. If a shipping failure is found,
preserve the exact trace for a separate fix agent; do not fix shipping here.

Initial host validation passed72 tests, including deterministic typed fixtures,
late-write rejection, incorrect item/target/quantity/turn/ownership negatives,
overlay reuse, and evidence binding. The correction adds a regression test with
an invalid real party and deceptively valid-looking trainer info; it proves the
test uses setup+8, preserves diagnostics and performs no write before rejection.
Corrected native run is pending. All20 additions,
no-effect semantics, remembered/stale gates, doubles, contexts and pagination
remain required. Full UI/growth/items rerun follows final source stabilization.
