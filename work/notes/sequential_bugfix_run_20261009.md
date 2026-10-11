# Sequential bug-fix run — 2026-10-09

User authorization: **D-2300**. GPT-6.1 Sol agents work strictly one at a time, with a separate
agent for investigation, reproduction, and implementation/verification. Reproduction is a gate:
if a defect cannot be reproduced or a sensible scoped repair cannot be justified, record it and
move on. No downloading, publishing, committing game data, or unrelated gameplay changes.

| User item | Scope | Investigation | Reproduction | Fix / verification |
|---|---|---|---|---|
| 3 | Zero-PP Struggle (D-1576) | Complete | Reproduced CN + RC7 | Enabled locally; paired builds, assembled tests and runtime controls passed (D-2302) |
| 5 | Rock Tunnel corner-kid loss freeze (D-1548) | Complete | Reproduced CN + EN; branch-only whiteout control passes | Enabled locally; paired built loss/retry and structural tests pass. Victory runtime evidence limited (D-2305) |
| 6 | Pokémon Tower Magcargo loss freeze (D-1560) | Complete; shared flag already hides scene on ordinary departure | Reproduced CN + EN; single-mon whiteout diagnostic passes | Enabled locally; four-byte native whiteout, paired builds/core runtime and structural outcome tests pass (D-2306) |
| 7 | Department Store doubles with one Pokémon (D-1559) | Complete; native living non-Egg guard and existing refusal text found | Native CN scene reached; action test invalid; corrected run never launched (pending approval canceled) | Skipped under reproduction gate; remains open |
| 9 | Out-of-range story flags / Pokédex writes (D-1333/D-1550) | Complete; intended IDs unproved, old-save compatibility required | Offline native flag writes reproduced: 19 cases per CN/EN; full emulator unavailable | Mt. Mortar safety repair enabled; exact 2-byte paired build diff and 20 native cases/build pass (D-2310). Route1 deferred after bounded candidate audit; reservation/compatibility remain unproved (D-2311) |
| 10 | Deoxys/Lucky Meowth God, expedition/beasts, Ho-Oh panel/Silver, bug hunt/Forest of Time (D-1578–D-1581) | Complete; two narrow candidates, bug-hunt state split unresolved, Deoxys intent disputed | Offline native-handler matrix: 104 cases per ROM; two candidates pass; hunt collision proven | Two guarded fixes enabled; paired builds differ at3 bytes; 104 native cases/build pass. No full-game run; other two deferred/excluded (D-2308/D-2309) |

Item 4 (Goldenrod) is excluded from fixes in this run. The forced NPC visibility combination is
historically reproducible, but a natural story path was not established. The user reports no
incoming bug reports and does not consider it actionable. Preserve the historical technical
finding without presenting it as a confirmed normal-play crash.

## Decisions made during execution

- Item 10 is scoped to the four concrete shared-progress problems listed in the previous answer
  and triage: D-1578 through D-1581. It does not authorize changing every quest, intended missable,
  one-shot legendary encounter, or relationship route.
- Reproduction may use private save fixtures and controlled RAM/script setup, but every report
  must distinguish naturally reachable scene behavior from forced-state setup and instrumentation.
- User approval D-2300 covers fixing the specified reproduced original-hack bugs. It is not a
  reason to ask again for the same scope or to silently broaden it.
- Existing unrelated dirty/untracked files belong to other ongoing work and must be preserved.
- D-2302: zero-PP fallback runs only when FIGHT is selected; existing forced actions retain
  precedence, empty slots do not provide PP, and the native Struggle executor handles the turn.
  Bag/switch/run remain available. Broader move restrictions were not redesigned.
- D-2305: Rock Tunnel's corner-child defeat now uses the same native whiteout block as seven
  neighboring loss routes; loss remains incomplete and retryable. Victory/reward logic is unchanged.
  Paired built-ROM loss/retry is fully verified; victory assertions passed in an earlier run but
  that run failed in optional harness followup before saving full JSON, and a rerun refused a
  transient party fixture. This is recorded as limited victory evidence, not a clean runtime pass.

- D-2306: Magcargo loss/draw now uses the existing native whiteout block. Preserve
  shared1155/0x40B7 and native one-visit visibility: the preceding grunts already
  set1155, so ordinary departure after decline also hides the encounter. No
  persistent retry marker or shared-state reset. Fixed-ROM native loss/healing/
  control passes; knockout/capture/flee/draw semantics are structurally verified.

- D-2308: the completed expedition leader recognizes409F>=10, preserving11/12
  without battle/reset; the Ho-Oh panel uses native ClearFlag0 instead of565.
  No old-save restoration. Exact three-byte paired build diff and offline actual
  native-handler matrix pass; complete in-game scenes/map-load/save-reload remain
  untested while emulator execution approval is unavailable.
- D-2309: D-1581 needs a verified separate state allocation and old-save
  compatibility policy before repair; D-1578 needs stronger defeat-narrative
  evidence before any continuation design. No guessed migration or retries.
- D-2310: Mt. Mortar SetFlag4461 becomes native SetFlag0. Preserve675/670/409F,
  the earlier expedition gate repair and existing Pokédex data. Do not guess461
  for NPC persistence or365 for legendary respawns. Paired builds and bounded
  native tests pass; full scenes, map reload and native save/reload are untested.
- D-2311: Route1 remains unchanged. Candidate3190 has no literal/event use and
  survives bounded trainer/daily/hidden/table audits, but unresolved computed
  consumers prevent a safe reservation. A plain remap loses old completion;
  no new gift, alias/migration, legacy-dex clearing or global guard is introduced.

## Handoffs

- `issue03_investigate` → `work/notes/issue03_struggle_investigation_20261009.md`.
- `issue03_reproduce` → `work/notes/issue03_struggle_reproduction_20261009.md`.
- `issue03_fix` → `work/notes/issue03_struggle_fix_20261009.md`.
- `issue05_investigate` → `work/notes/issue05_rock_tunnel_investigation_20261009.md`.
- `issue05_reproduce` → `work/notes/issue05_rock_tunnel_reproduction_20261009.md`.
- `issue05_fix` → `work/notes/issue05_rock_tunnel_fix_20261009.md`.
- `issue06_investigate` → `work/notes/issue06_magcargo_investigation_20261009.md`.
- `issue06_reproduce` → `work/notes/issue06_magcargo_reproduction_20261009.md`.
- `issue06_fix` → `work/notes/issue06_magcargo_fix_20261009.md`.
- `issue07_investigate` → `work/notes/issue07_department_doubles_investigation_20261009.md`.

- `issue07_reproduce` → `work/notes/issue07_department_doubles_reproduction_20261009.md`.
- `issue09_investigate` → `work/notes/issue09_story_flags_investigation_20261009.md`.

- `issue09_reproduce` → `work/notes/issue09_story_flags_reproduction_20261009.md`.
- `issue10_investigate` → `work/notes/issue10_shared_progress_investigation_20261009.md`.
- `issue10_reproduce` → `work/notes/issue10_shared_progress_reproduction_20261009.md`.

- `issue10_fix` → `work/notes/issue10_shared_progress_fix_20261009.md`.

- `issue09_reproduce_offline` → `work/notes/issue09_story_flags_offline_reproduction_20261009.md`.
- `issue09_fix` → `work/notes/issue09_story_flags_fix_20261009.md`.

## Final integration — 2026-10-10

Catalog/snapshot omissions repaired without changing game bytes; see
`work/notes/sequential_bugfix_integration_20261010.md`. All six new fixes are
truthfully inventoried with separate runtime/native-handler evidence and
remaining full-game gaps. Armips inventory: 18 sources, 66 regions, 4 strings;
registry: 42 enabled fixes; unified scenarios: 32 covered, 10 listed gaps.
Focused 106 tests pass. Final full check has 1080 tests OK (26 skipped), all 18
snapshots and build fingerprints pass. Its only failure is 36 preexisting ruff
findings in untracked `work/research/difficulty-armips`, left untouched.
ROM SHA-1 remains `4167ea2c4999edb5359d945977bc7433cad2a91e`; xdelta SHA-1 remains
`afe14e3519b7535d0bd95b50b9d767cbf9b0cd5c`. The private final rerun outputs are
byte-identical to the coordinator build; root/RC7 ROMs and expected.toml are
unchanged. No emulator execution or expected refresh was performed here.
