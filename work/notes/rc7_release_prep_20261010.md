# RC7 release preparation — 2026-10-10

> Source integration update: Honey Gather, startup notices and opt-in difficulty source
> were added after the builds below. Those artifacts and hashes do not validate this
> checkout's current source. See [the bounded source integration report](rc7_source_integration_20261010.md).

## Current validation run — 2026-10-10

The current baseline contains **47 enabled fixes** (45 revised fixes plus Honey
Gather and the approved startup notices). Earlier fingerprints below are historical.
The baseline ROM SHA-1 is `7ebeaee81a0232b70d5b2a434a2d52fb22a97ea2`;
its USA-source xdelta SHA-1 is `e7dc27dc200c98c7ddf8326362ae2b2458a83a17`.

The latest strict production gate passed with **1049 tool tests, 43 documentation
tests and 35 site-tool tests**, with no skips, pinned tools, verified assembly/listings
and USA claims, expected artifact hashes, and byte-identical rebuild/patch reproduction.
Save-core separately passed 202 tests, typechecking, lint and mutation checks.
The site tests and production build passed (4636 pages).
Private logs are under the primary root's `work/build/rc7-completion-20261010/`.

Difficulty's input pins were revised only after an exact byte/dependency review;
see [the compatibility review](rc7_difficulty_compatibility_20261010.md).
Its installed candidate SHA-256 is
`c0f8a54f36dbfd9a32500009fc5ed44222c42ff9a884c03142fb43d1aba0b251`.
The independent fresh-compilation verifier passed exact-write/preservation checks
and all 53 negative corruption/overlap/bounds rejections. All 188 difficulty
host/static tests passed. The 94-job native suite remains running; **16 required
native requirements still have no implemented driver**. Host tests and installer
verification do not establish those requirements. The candidate is not release-ready.

Five combined gameplay scenario groups and all three melonDS freeze cases passed.
The broad production-fix native run is still running. Its Heal Bell case initially
failed because an invalid historical seed record was reused by the fixture. The
fixture now buffers three validated native-generated records before replacing any
bench slots; invalid or changing generated output remains rejected. Four regressions
and the fresh fixed/control Heal Bell pair passed. The ROM was not changed by this
fixture correction. All 18 Honey Gather pairs and all 14 individual Struggle checks
passed; Rock Tunnel loss/win/control passed. Startup captures were visually inspected,
including an enlarged credits/footer detail: no clipping or overlap.

The supplemental targeting invocation mistakenly expected the untouched Chinese
ROM to implement the new targeting behavior. These failures are invalid positive
control expectations, not evidence of a regression in the combined ROM. The historical
Option 2 control separately passed its intended `--expect-option2` oracle. Initial
Honey invocations had missing fixture CLI arguments; the corrected prepared-fixture
run supersedes them and passed all 19 steps (preparation plus 18 checks). Preserve
both original logs and corrected evidence; do not describe the original batch as passing.

No RC7 release has been published. Local playtest patches are not release artifacts.

## Current scope revision — D-2321

The user excluded `mortar-invalid-flag-noop`, `expedition-completed-progress` and
`hooh-panel-silver-marker` after reviewing their audit provenance and uncertain story intent.
They remain in the registry with `enabled = false`. RC7 now adds **11 fixes to RC6,
45 enabled fixes total**, preserving the Chinese bytes in event-script members 45 and 962.
No player report is recorded for the Mt. Mortar write; the expedition and Silver changes
are withheld because their non-crashing consequences may reflect intended behavior.

The 48-fix artifacts and runtime evidence below are historical, not the current release candidate.
Revised artifacts are under `work/build/rc7-scope-revised/` and the strict-check output
`work/build/rc7-scope-revised-checked/`. No published release artifacts were replaced.
The original 48-fix files under `work/build/rc7-final/` must not be used as the current candidate.

Independent comparison of the revised ROM with the previous candidate confirms exactly five
restored bytes: member45 offsets184/185 and member962 offsets136/1821/1822. Both complete
members now match the untouched Chinese ROM byte-for-byte. Every other logical ROM part,
including both translation archives and all battle/animation code, is identical to the previous candidate.
Proof: `work/build/rc7-scope-revised/scope-proof.json`.

| Current fingerprint | SHA-1 |
|---|---|
| Text | `922a51f5639fda62fce76bc678793c050fac7a46` |
| Nontext | `da788dec0e577e0e04ca592e7dc974c5d3fbd79c` |
| ROM | `a45fe3ec141ef6ad8f0bf00b1fb7114e19993c27` |
| Xdelta | `ca7206a64f8a3844323e498c482a50f733ce7756` |

The normal builder and artifact verification passed. `check.py --full --strict-release`
passed all 11 stages: 1029 tool tests, 43 docs tests and 35 site tests, plus registry,
assembly, listings, USA claims, expected hashes and reproducibility. The second build
produced identical ROM/xdelta bytes and a matching normalized report.
Log: `work/build/rc7-scope-revised-check.log`.
No new emulator run is claimed for this scope removal; previous runtime evidence applies to
the unchanged code and retained fixes, with its original limitations.

## Historical 48-fix preparation (superseded scope)


Local preparation only; no publication, download or modification of existing release artifacts.
Branch `release/rc7-prep`, isolated checkout
`work/build/rc7-release-prep-checkout`, based on RC6/develop `a657a13`.
The user's instruction was “skip hit sound and faint cry. build all others including pryce together
in a rc7-release prep branch and run the checks.” D-2313 records this authorization.

## Integrated scope

RC6 contains 34 enabled fixes. This preparation contains **48 enabled fixes**, adding these 14:

| Patch | Source |
|---|---|
| `lugia-animation-state-bounds` | reviewed local source |
| `double-battle-targeting` | reviewed local source |
| `zero-pp-struggle` | reviewed local source |
| `rock-tunnel-corner-loss` | reviewed local source |
| `magcargo-loss-whiteout` | reviewed local source |
| `expedition-completed-progress` | reviewed local source |
| `hooh-panel-silver-marker` | reviewed local source |
| `mortar-invalid-flag-noop` | reviewed local source |
| `battle-heal-hpbar-switched-out` | `fix/melonds-retest`, D-2314 |
| `cute-charm-infatuation` | `fix/cute-charm-infatuation`, D-2315 |
| `battle-party-status-sync` | `fix/heal-bell-status`, D-2317 |
| `faint-waits-for-hp-bar` | `fix/multihit-ko-hpbar`, D-2318 |
| `battle-message-variant` | `fix/destiny-knot-side`, D-2319 |
| `pryce-weather-rule` | `fix/pryce-weather-rule`, enabled under D-2320 |

`battle-hit-sound` and `battle-faint-cry` are absent from the registry and assembly inventory.
Pryce's earlier keep-disabled choice is superseded by the current explicit instruction.
The Saffron crash reproduced in the earlier investigation belongs to **Bradam's NoBigText patch**;
this preparation adds no Saffron fix.

Selected tools, native regressions, evidence notes and shared-codec egg fixture support accompany the fixes.
Unrelated dirty site/docs exports and difficulty research/code are excluded. The decision register retains
existing globally assigned records, including unrelated difficulty decisions, to avoid reassigning IDs.
Branch-local D-2276/D-2281 collisions were reconciled using `decisions.py`, never hand-editing JSONL.
During preparation a concurrent user-approved difficulty D-2312 appeared in root. The coordinator then
explicitly authorized root `decisions.py add` reservations D-2313–D-2320; prep copied that register.
These reservations are the sole intentional root tracked-file exception. All other tracked dirty-file
hashes captured at start are unchanged. No private saves, extracted data or ROMs are staged.

## Independent byte review

Private proofs are under root `work/build/rc7-integration/`:
`assembly-proof.json` and `final-artifact-proof.json`.

- The preceding 18-source local assembly matches every reviewed golden; all six added branch isolated
  assemblies match their branch golden fingerprints.
- Combined assembly is exactly the independent composition of those six region writes onto the preceding
  18-source image: **24 sources, 94 code/data regions, four strings**, without undeclared writes or overlaps.
- Pryce's `script928` namespace maps to event NARC `a/0/1/2` member 928. The four local NARC patches touch
  members 17, 45, 129 and 962. These are different members; no graphics patch touches that NARC.
- A fresh source control built with all 14 additions excluded exactly reproduces RC6 expected ROM SHA-1
  `ca55846b7748ed251680f9b65e84acd59f387b54`, text hash and nontext hash.
- Compared with that control, final logical ROM changes are restricted to ARM9, overlays 1/14 and event
  NARC members **17, 45, 129, 928, 962**, all within the 14 declared claims. Translation text is unchanged.
- Both excluded audio regions retain original Chinese bytes in the final ROM: overlay14 offsets
  17710–17776 SHA-256 `2a562529e45ce72f1d65c4198f2bed1c881b0c081c146b374609ec50536f8818`, and
  181148–181500 SHA-256 `7bc510dc3087a1c1146bc9626d2bc2f0fd1dcd6dc0cab9c74aa2107c607f3167`.

`expected.toml`, `sizes.toml`, listings and combined test fingerprints were updated after this review;
no blanket golden replacement was used.

## Checks and reproducibility

All commands run from the isolated repo root; root `.venv`, ROM/extract/ref inputs and existing dependency
folders are reused through ignored links. The save-core generated output is built privately in this checkout.
No install/download command runs. The directory-link spelling `/work/translate/ref` is explicitly ignored.

```sh
npm --prefix work/save-core run build
MELONDS_SHIM=/Users/contributor/Developer/poke/work/build/melonds/libmelonds_shim.dylib \
TEXT_SPEED_TEST_ROM=/Users/contributor/Developer/poke/work/build/rc7-release-prep-checkout/work/build/rc7-no-text-speed/origin_hg_v4.0.3_en_wip.nds \
.venv/bin/python work/tools/check.py --full --strict-release \
  --armips /Users/contributor/Developer/armips/build/armips --work-dir work/build/rc7-final
```

Final gate: **all 11 stages PASS in 97.8 seconds; 1020 tools + 43 docs + 35 site = 1098 tests, zero skips**. Logs: `work/build/rc7-final.log` and its build/repro directories. Earlier reviewed full build, strict release gate and
strict gate with complete fixtures passed. Earlier full runs reported 33 skips: seven needed the local
melonDS shim path and 26 needed the optional no-text-speed binary fixture. Both were supplied and a
subsequent strict run executed **all 1019 tool tests with zero skips**, plus 43 docs and 35 site tests.
The final gate reruns after the harness integration repairs and added HP fixture regression.
Save-core fixture tests: **84 pass**, including egg-bit preservation across 32 shuffles; typecheck/lint pass.
Artifact checker separately passed against the identical final ROM.

Strict release validation recompiles the native payload with pinned clang21, checks registry/listings/USA
claims, builds against USA HeartGold CRC32 C180A0E9 and repeats under varied locale/timezone/hash seed,
filenames and working directory. ROM and xdelta are byte-identical; build reports are identical after normalizing the three base/ROM/patch path fields.

## Combined runtime evidence

The paired runner command was:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python work/tools/emu_harness.py fixes \
  --case battle-heal-hpbar-switched-out,cute-charm-infatuation,battle-party-status-sync,faint-waits-for-hp-bar,battle-message-variant,pryce-weather-rule \
  --rom work/build/rc7-strict-complete/origin_hg_v4.0.3_en_wip.nds \
  --rom-report work/build/rc7-strict-complete/build_report.json \
  --controls work/build/rc7-runtime/controls --build-controls \
  --out work/build/rc7-runtime/battle-and-pryce-current-tools --jobs 2
```

The fixture rerun used `--case battle-party-status-sync,faint-waits-for-hp-bar` without rebuilding controls,
and wrote `healbell-multihit-final`. Other invocations are retained in the corresponding reports/logs:
`emu_lugia.py --expect fixed`, Lugia `check_states.py`, 13 separate `emu_double_target.py` cases,
`emu_struggle.py`, `emu_rock_tunnel.py`, and reviewed private Magcargo `runtime.py --controlled --single --fixed`.

All cases below use the 48-fix combined ROM. Evidence stays ignored under this checkout's
`work/build/rc7-runtime/`; logs are `work/build/rc7-*.log`.

| Regression | Verdict and retained evidence |
|---|---|
| Lugia fresh boot | PASS, `lugia-fixed/report.json`; private supplied save, zero CPU faults, intended field/story state, immutable inputs; battle skips are explicitly diagnostic |
| Lugia state/recovery matrix | PASS, `lugia-states/report.json`; valid 0/1 parity, unsigned invalid values and recovery; isolated checkpoint dispatcher test |
| Double targeting | **13/13 fresh combined-ROM cases, 65 target screens PASS**, `targeting/summary.json`; remembered foes, eligibility, directions/allies, CANCEL, spread/single/empty cases |
| Zero-PP Struggle | **7/7 PASS**, `struggle/result.json`; four-zero, one-zero, positive PP, last PP, trainer victory, double and enemy cases; native move165, damage/recoil and field return |
| Rock Tunnel corner loss | PASS, `rock-tunnel-loss/result.json`; genuine object17/script18/trainer606 loss, healed valid party, native whiteout, movement and retry; victory not rerun |
| Magcargo loss | PASS, `magcargo-loss/result.json`; controlled post-grunts valid one-Magikarp fixture, native defeat/whiteout and map reload; encounter remains one-visit |
| Expedition/Ho-Oh/Mortar | actual native predicate/handler matrices execute in full tests with local CN ROM; these are bounded offline native tests |

Targeting's older standalone evidence was 26 CN/EN cases and 130 screens; that count is **not** claimed for
this combined run. Magcargo private runtime source SHA-256 is
`277643e62576634f562839796a3eb2a67ea6bb199ea97ac927eb506b6545b1d8`.

All six newly merged battle/Pryce fixes have discriminating paired **fixed/original** verdicts:

| Fix/scenario | Combined ROM | One-fix-disabled control |
|---|---|---|
| heal HP / `battle-heal` | fixed | original |
| Cute Charm / `cutecharm` | fixed | original |
| Heal Bell / `healbell` | fixed | original |
| multi-hit KO / `multihit-ko` | fixed | original |
| message variant / `battle-variant` | fixed | original |
| Pryce / `pryce` | fixed | original |

Six controls were freshly built with exactly the selected fix excluded (47 enabled, identical translated
text, verified source/build provenance). Message variant also ran the untouched Chinese reference and ten
cases; Pryce ran nine Ability/egg/slot6 cases. Verdicts are classifier outcomes, not merely subprocess exits.
Definitive merged evidence `definitive-paired-report.json` cites its two source reports: four passing cases
in `battle-and-pryce-current-tools/fixes_report.json` and the repaired Heal Bell/multi-hit rerun
`healbell-multihit-final/fixes_report.json`. It does not claim a single subsequent six-case run.

Launch/fixture troubleshooting is retained separately. The initial run lacked SDL dummy configuration and
all children exited -6 before observations; a correctly escalated headless retry launched successfully.
That retry exposed branch-era imports/APIs removed by current tooling (`emu_guide0107`, `emu_open`,
`emu_sweeps`, `emu_verify`, `_prng_stream`). Maintained current helpers/shared TypeScript codec now replace
these. Maxie's HP fixture has an added 32-shuffle preservation regression. Static scan finds no obsolete
imports or calls reachable in these six scenarios.
Heal Bell also queried a top-level status instead of `party.status`, then encountered invalid historical
seed bench records. Three native-generated valid bench records now supply the four-mon active fixture;
strict checksum validation is retained. Full diagnostic tracebacks are in `rc7-healbell-diagnostic*.log`.
The unpinned multi-hit control initially judged fixed as well; seed-dependent battle timing can hide this
bug (a critical message is a known example, but that first run did not trace the cause). The fixture now
pins both native RNGs to seed1 and records battle messages. Both sides reproduce original draining/reset
behavior in the control and finish draining before faint in the combined ROM. Future child logs retain
complete stdout/stderr and exit status rather than only the truncated error summary.

## Artifacts and limits

Prepared artifacts are private under `work/build/rc7-final/` and `work/build/rc7-final-repro/`;
previous `work/release/v1.0.0-rc7/` remains the older Lugia-only candidate and is untouched.
Only xdelta patches may be distributed; no ROM is committed or published.

| Fingerprint | Value |
|---|---|
| Text SHA-1 | `922a51f5639fda62fce76bc678793c050fac7a46` |
| Nontext SHA-1 | `cccf1635ceb250222b7d8e45c6312041a9605752` |
| ROM SHA-1 | `43de6cf39faa5d30ae986eab85fb288fa8399388` |
| ROM SHA-256, 278780608 bytes | `df7104cb45823273f987bbda73dbdce1fece8de8ba84c70a38c59362b0aacbd3` |
| Xdelta SHA-1 | `148335e34a535c201d0630729a588cc2b7a3c061` |
| Xdelta SHA-256, 43561477 bytes | `8835eb4cc79f2e58bfc758dee7aab5cfde07abd01dcaabf8ca9b13ce6bd4ffaf` |

No complete game walkthrough, hardware run, Rock Tunnel victory rerun, full expedition/Mt. Mortar scenes
or native save/reload of those story repairs is claimed. Known deferred Route1 marker, shared hunt-state
migration and Deoxys-loss narrative issues remain deferred. Cute Charm's separate per-turn naming finding
D-2316 remains open. These limitations do not suppress any release checks.
