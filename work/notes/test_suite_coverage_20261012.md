# Test coverage reassessment — 2026-10-12

## Merge

`hardware/harness-memchecks` merged into `develop` as `d202d3e`, with parents
`5b7a101` and `dfe8ba2`. All 64 source-branch non-merge commits had patch-equivalent
commits in develop (`git cherry` reported only minus entries). An `ours` merge
records that ancestry while retaining the newer develop tree; the merge changes
no tracked file content. A normal merge would conflict with newer RC7 content
and resurrect removed RC5 tooling. Existing README edits and the deletion of
the work/.venv symlink were preserved. Nothing was pushed or downloaded.

## Fresh verification

The installed save-editor dependencies rebuilt the stale shared-core assets.
These are application assets, not a ROM build. Logs are local in /tmp.

| Check | Result | Interpretation |
| --- | --- | --- |
| Registry / generated FIXES.md | Pass: 50 registered fixes, 47 enabled, 26 assembly sources linted | Declaration consistency, not runtime correctness |
| Portable Python harness, with images | 354 passed; five native tests explicitly excluded | Harness/codec/reporting contracts; no game execution |
| Memory-checker unit tests | 58 passed | Synthetic memory, decoder and verdict tests; no game execution |
| Save-editor check | Typecheck and lint passed; 491 tests passed, one optional local-ROM test skipped | Editor and shared-core tests combined |
| Semantic mutations | 8/8 compiled mutations caught by their intended assertions | Demonstrates sensitivity to eight chosen save-corruption bugs |
| Website Node tests | 86 passed, 18 skipped | Built-page integration checks were not enabled |
| Python documentation tests | 46 passed | Parser and documentation-generation contracts |
| Python website tests | 44 passed | Reference extraction and formatting contracts |
| Fast aggregate gate | Failed | Ruff F841 at work/tools/site/export_data.py:569; HoneyGatherTests.setUpClass needs armips even though fast tests deliberately hide it |
| Fast aggregate tool tests | 1,049 executed, one setup error, 93 skips | Gate stops here, so its docs/site suites were run separately above |
| Synthetic assembly | Skipped: pinned armips unavailable on PATH | No new assembly evidence |
| Full build / reproducibility / emulator / hardware checks | Not run | No fresh claim about ROM output, gameplay or hardware acceptance |

The first editor server test failed because the sandbox prohibited binding
127.0.0.1. The complete editor check passed when rerun with localhost access.
The optional skipped editor case checks local English-ROM parity.
Counts overlap: the portable harness is a subset of the general tool suite;
the editor suite includes shared-core tests. Do not sum them into a unique total.

## What each layer is useful for

| Layer | Bugs it catches | Why retain it / practical cadence |
| --- | --- | --- |
| Registry, lint, typecheck and architecture checks | Invalid patch regions/dependencies, undeclared writes, API mismatches, duplicated production save codecs | Cheap prerequisites on relevant changes; they cannot prove gameplay |
| Synthetic assembly | Invalid instructions, area overflow and writes outside declared regions without private ROM inputs | Keep in patch CI; zero-filled inputs and disabled guards cannot prove the original bytes match |
| Python unit tests | Broken binary tools, wrapping/tag rules, harness sequencing, evidence classification and failure handling | Keep in the fast gate; especially useful to prevent an incomplete run becoming a false pass |
| Save-core invariants, transactions, sequences, mirrors and worker tests | CRC/checksum errors, aliasing, partial failed edits, unsafe bounds, mirror policy, differences between worker and direct execution | Keep; invalid saves can silently corrupt progress. Worker tests exercise a separate execution boundary |
| Editor integration tests | Import/export containers, field conversions, UI-facing operations and serving the shared module graph | Keep alongside core tests: correct codecs do not guarantee correct editor wiring |
| Independent read-only decoders/native oracles | Writer and reader agreeing on the same incorrect encoding | Keep small independent oracles. Reusing the production codec for every assertion would weaken the evidence |
| Save-core mutations | Tests passing despite bypassed validation, boundary errors, reversed mirror order or aliasing | Keep the eight bounded mutants in save-related CI; 8/8 is not a universal mutation score |
| Full ROM assembly, US references, listings and golden hashes | Wrong original-byte assumptions, wrong reference addresses, unreviewed machine-code changes and unintended build changes | Keep for patch integration/releases; snapshots and hashes need review rather than automatic blessing |
| Reproducible builds | Output depending on paths, locale, timezone, hash seed or compiler changes | Keep for releases and build-tool changes; identical output can still be wrong |
| Emulator fix/control pairs | A fix not changing its intended behavior, or a scenario passing without the fix | Keep: a negative control establishes that the test detects the regression |
| CN/EN behavior scenarios | Translation/build changes altering the hack's behavior | Keep for behavior fidelity; parity alone can preserve an original hack bug |
| Memory checks | Allocation failures, heap corruption, null writes, stale selected Pokémon/move state and missing scenario checkpoints | Keep for runtime safety. Screenshots cannot show these; host verdict tests alone do not execute them |
| Runtime text-fit and approved graphics crops | Wrong window assumptions, clipping, bad tile/palette/layout output | Keep for changed text/graphics; static wrapping cannot reproduce every native window and variable substitution |
| melonDS freeze reproducers | Hardware-like ARM9 protection faults that permissive DeSmuME runs may miss | Keep alongside hooked DeSmuME tests; they answer different questions |
| Hardware acceptance | Flashcart/loader anti-piracy, device-specific timing and actual audio/input behavior | Still needed for hardware claims; emulator anti-piracy hooks do not exercise a real loader |
| Website parser/data and built-page tests | Wrong acquisition/rate data, broken links/anchors, lost information during rendering | Keep both: correct JSON does not prove correct compiled pages. CI enables GUIDE_TEST_DIST=1 after building |

## Measured scope and gaps

The unified fix runner maps **38 of 47 enabled fixes (80.9%)** to scenarios via
emu_fixes.COVERAGE. This is registry coverage, not statement/branch coverage,
freshly passed gameplay coverage, or proof that every branch within a fix is tested.
It has 27 in-process scenario recipes plus four external recipes. General
behavior scenarios have five TOML files; the freeze layer has three reproducers.

The nine enabled fixes outside the unified mapping are:

- honey-gather and startup-content-warning: dedicated native runners.
- zero-pp-struggle: dedicated paired runner; ordinary Bag/switch/run sequences,
  natural story cleanup and all doubles configurations remain incomplete.
- rock-tunnel-corner-loss: dedicated loss/whiteout/retry runner; complete victory
  evidence remains limited.
- magcargo-loss-whiteout: a private runtime runner; alternate outcomes have
  structural checks without separate runtime runs.
- double-battle-targeting: dedicated CN/EN matrix and assembled host tests.
- lugia-animation-state-bounds: dedicated runner requiring a private supplied save.
- gfx-battle-result-labels and gfx-jp-buttons: missing link/facility/wireless or
  otherwise unreached native screens.

All nine have explanations in emu_fixes.UNCOVERED. A dedicated runner's existence
or historical pass does not make it part of the default gate or prove its result
matches today's sources and ROM.

The memory checker declares **18 scenarios**, all with expected checkpoints.
Five configure party order, two summary selection, two move order, and two
explicit rendering expectations. Those different assertions are complementary:
reaching a screen does not prove the selected Pokémon, stored moves or copied
description are correct. Coverage is concentrated on menus, full inventory/
party cases and a few battles, not an entire story playthrough.

Pending graphics/baseline approvals do not fail the emulator layer. A successful
exit therefore needs its pending count reviewed before claiming visual acceptance.
The default gate also omits the separate difficulty-candidate research suite and
the focused check_translation.py lint/typecheck gate. Candidate host success must
remain separate from required native-case completion.

There is no measured repository-wide line/branch coverage percentage in this
assessment. Test totals and registry mappings cannot supply one. Coverage is
strongest around save integrity and harness verdicts; weakest around full story
sequences, link/wireless/facility screens and real-device behavior.

## Keep, simplify and prioritize

Keep all distinct layers above, but do not run every expensive layer for every
text edit. Fast checks belong on ordinary changes; relevant paired runtime cases
belong on gameplay fixes; full/repro/runtime/hardware checks belong on release
acceptance as appropriate to the changed feature.

Avoid redundantly running the standalone save-core suite after the editor check
already ran those same tests. The portable harness repeats part of the tool gate
deliberately: it proves a minimal-dependency CI configuration and fails on unexpected
skips. Running both portable configurations in CI likewise verifies optional
dependency isolation; locally the with-images mode suffices for functional coverage.
Preserve independent oracles while removing duplicated production implementations.
No specific test is shown to be safe to delete merely because another layer covers
the same feature.

Priorities:

1. Restore a reliable fast gate: address the unused acquisition_notes assignment
   and classify Honey Gather's armips requirement explicitly rather than allowing
   an unhandled setup error. These pre-existing issues were reported, not edited.
2. Bring dedicated regression runners into the aggregate release report with
   current source/ROM bindings and explicit missing-fixture results.
3. Require built-page tests for website acceptance and account for every native
   skip and pending visual approval when reporting release readiness.
4. Add end-to-end save/reload and complete story-outcome cases where current
   evidence only executes handlers or controlled scene fixtures.
5. Record real-device/loader acceptance separately from emulator evidence.

Documentation also needs refreshing: CONTRIBUTING.md says four native exclusions
where the portable runner now excludes five, and describes an older emulator-only
fix step/timing rather than the current four-part layer.
