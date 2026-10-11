# Functional growth/progression coverage for final review

This map applies D-2312: first unfinished gym in guide order, using the running
maximum `12,20,25,38,55,65,80,100`, then100 throughout Johto. Evidence is accepted
only for the exact current candidate, receipt, inputs and test sources. Historical
passes below are context, never current acceptance. Check `report.json` for the
current gate; host checks are not native evidence.

| Functional obligation | Driver / evidence | Current scope and remaining work |
|---|---|---|
| Final-recipient clamp; two actual fighters; no redistribution; Share ON/OFF EXP+EV; zero and partial7 messages | `native_battle.py --scope matrix` | Six historical battles passed; fresh current-source matrix required. Partial fixture uses species19 candidate growth table, valid level11 stats and EXP=T12−7. Native eligibility boolean/deferred, raw bytes, application/message, cache/backing, EV and lifecycle remain mandatory. |
| Nonzero Kanto prefix | `native_progression.py --case prefix` | Prepared native checkpoint: badge0 gives20; level20 fighter forfeits its native request, level8 fighter and bench still grow. |
| Functional Erika predicate | `--case erika-prewin` and `--case erika-win` | Prepared native checkpoints: same badge0..2 prefix;1173 alone leaves38;1220 advances55 without badge3. All16 native badge callbacks,1220/209 flag callbacks, pointer ownership and captured cap are required. These are pre-entry inputs, not script wins. |
| Earlier gap despite later badges | `--case skipped-koga` | Prepared native checkpoint: maskFFDF (badge5 absent) yields55 despite every later badge, with actual clamp. `native_edges.py --case gap` now prepares same-party55→100 closure; first native run pending. |
| Growth beyond obsolete80/88 ceilings | `--case plateau-81` and `--case plateau-89` | Prepared native checkpoints: real native awards to level81/89 Rattata at cap100. Full candidate growth table supplies threshold100; no downlevel and no award rejection. Constant100 is never completion/selected-row proof. |
| Entry frozen, next entry refreshes cap | `native_caprise.py` | Prepared two-battle checkpoint:12 then20, native reader callbacks and complete generations. Only badge0 changes in field; no mid-battle flag edit or victory-script claim. |
| No EXP banking after cap rise | `native_caprise.py` / `growth.caprise_no_banking` | Prepared one-boot/two-KO checkpoint with exact raw party and inventory continuity, native PP progression, positive discarded request at12 and only new requests accepted at20. Native EV request/backing checked per recipient per KO. |
| Multiple opponents in one battle with changed actual participation | `native_multiko.py` | Historical trainer6 singles two-KO Cap OFF/ON pair passed with totals [44,86,44] versus [0,86,44]. Four-battle Share/Cap matrix passed167 hosts and both native cases before these source edits; fresh final-source rerun required. Native lists must change13:{1,2} →14:{2}; fighter3 remains benched. Observes actual reward-pass grouping rather than assuming per-KO awards. Simultaneous KOs and other aggregate/exclusion permutations remain missing. |
| Over-cap/100 and another growth curve | `native_edges.py --case overlevel/curve` | Prepared Caps OFF/ON controls: lead20 plus fighter100 at cap12; species1 level11 EXP=T12−7 from its distinct ROM curve. Native run pending. Native egg/fainted/remote exclusions remain missing. |
| Actual Erika victory/loss/retry/ceremony scripts | `progression.erika_routes`, unimplemented | Still required story integration evidence; native predicate fixture passes cannot satisfy this case. |
| Deferred awards | `native_multiko.py` / `growth.deferred` | Historical four-battle native pass: positive bench and zero-cap former fighter, original boolean/deferred preserved. Partial deferred crossing remains unproven. |
| Broader constructors/ownership, replay/link/facility exclusions | Existing manifest missing cases | Remain incomplete until actual constructors/actions produce native traces. |

Astra's obsolete obligations are explicitly reclassified in `required_native.json`
under `optional_research`: `progression.clair` and
`progression.selected_late_rows`. After the first seven Kanto completions, every
remaining Giovanni/Johto badge/Clair209 combination resolves100. Shipping exposes
no selected-row state. Real Clair/Tianyuan story execution is optional research;
raw gym maxima, guide order and209 predicates remain independently checked
research facts. No pass was awarded for these reclassifications. The functional
`progression.skipped_decreases` aggregate gate remains incomplete until earlier
gap closure, plateau growth and frozen/new-cap behavior are all established.

First parent checkpoint (six separately supervised cold boots; no old states):

```sh
.venv/bin/python work/research/difficulty-armips/tests/run.py --native --native-phase battle --battle-scope progression --native-timeout 240
```

Expected roughly8–12 minutes, hard limit24 minutes for six children plus host
validation. Each child performs one native wild battle with pre-entry HP1 enemy,
real Splash, native party switch, and real Dragon Rage/KO. No post-entry HP,
participation, eligibility, flag or outcome writes. Reports and screenshots live
under `work/build/difficulty-v2/tests/native-tests/progression/<case>/`.
Stop on the first failed child to return useful diagnostics without spending the
remaining budget. Final matrix/UI/items evidence must be rerun after sources
stabilize; freshness and failed-report vetoes are unchanged.


## Cap-rise checkpoint after six progression fixtures

The parent reported all six progression fixture cases passed with156 host tests
on candidate73b188b9… and the then-current receipt/sources. Adding this checkpoint
makes those reports historical until rerun; it does not preserve stale passes.

```sh
.venv/bin/python work/research/difficulty-armips/tests/run.py --native --native-phase battle --battle-scope caprise --native-timeout 360
```

One cold boot, two complete wild battles, estimated2–4 minutes plus host checks;
child deadline360 seconds. Output: `native-tests/caprise/result.json`, raw closed
field continuity records and native events in `caprise-trace.json`, all action
screenshots and before/after opponent fixture records. Player fixture and Options
are installed once. Only profile badge0 is edited between battles, with exact
before/after checks of full party allocation, Bag, profile, VarsFlags, Options
and frame; no emulator steps occur during this edit. Both native battles retain
strict original eligibility/deferred/raw, message/application/cache/backing,
EV and action/lifecycle assertions. The parent must execute the native command.

Closing skipped Koga55→100 with later badges remains next, along with actual
multi-opponent participation changes. No existing aggregate gate is promoted
by this narrower two-battle case.


## First multiple-KO checkpoint

Parent reported the carried-party cap12→20 case passed with159 host tests:
awards `[0,234,118]` then `[175,217,118]`, including the native level-dependent
fighter2 request217. Those reports become historical after these source edits.

```sh
.venv/bin/python work/research/difficulty-armips/tests/run.py --native --native-phase battle --battle-scope multiko --native-timeout 600
```

One cold boot, four Share/Cap trainer6 singles controls, two native KOs each;
estimated5–8 minutes plus host checks, hard child deadline600 seconds. Player
inputs are reset only between control battles. Both native-created
enemy records are strictly validated and preserved before installing identical
typed level5 Rattata HP1/Splash inputs at the pre-entry trainer launch seam.
STYLE=SET is selected through normal Options. Real Splash1/switch1→2/Dragon
Rage2/Dragon Rage2 inputs must leave recorded participant lists `{1,2}` then`{2}`.
No within-battle resets, participation writes or outcome overrides exist.

Trace022289B4 records each native per-opponent recipient calculation.
022288E8/02228910/0222896E record the actual temporary, combined and postprocessed
native reward arrays, including native last-record marker semantics.
0221F5E8 defines observed award-pass groups; groups consume traced opponent
aggregates exactly once, whether awards occur per KO or after several KOs.
Native boolean/deferred/raw, EV requests, message/application/cache/backing and
full lifetime checks remain strict. Pair comparison rejects changed native
requests, recipient redistribution and EV loss. No simultaneous-KO claim is made.

Output: `native-tests/multiko/`, including the first failed input checkpoint if
replacement UI or native reward grouping needs an evidence-led fixture adjustment.

Deferred coverage: `growth.deferred` now uses the multi-KO matrix, requiring a
positive deferred bench award and the former fighter's zero-cap deferred award
with exact native boolean/raw/deferred preservation and application semantics.
This is not partial deferred crossing coverage. The broad no-banking gate stays
incomplete: cap-rise continuity and this matrix need current combined evidence.

Multi-KO EV provenance: raw yield bytes remain native, including bench yield1.
Observe original eligibility at caller0221F682, return and apply/skip branch;
bind accepted calls at0222AC50/LR0221F6AB to recipient/raw/group/opponent.
Battle-mon EV storage (+248 total, +24A six values) must change only for
eligible recipients, including capped participants. Party backing EV flush
is checked after battle, not assumed at each award group.

## Bounded growth edges checkpoint and Astra follow-up

```sh
.venv/bin/python work/research/difficulty-armips/tests/run.py --native --native-phase battle --battle-scope edges --native-timeout 600
```

Three fresh boots, two battles each; stop on first failed job. Reports are under
`native-tests/edges/{gap,overlevel,curve}`. No emulator savestate is loaded.
Gap input is FFDF→FFFF (only Koga bit5), preserving all later badges and raw
party/inventory between entries. This proves native saved-predicate readers and
next-entry growth, never an actual victory script. Overlevel/curve controls reset
only their pre-entry fixtures between the two Cap settings. Species1 uses the
candidate personal/growth tables, valid level11 stats and EXP=T12−7; all native
threshold, message/application, cache/backing, level and EV assertions stay strict.

For final Astra review, still distinguish these missing functional obligations:
- `growth.no_banking`: needs a source-bound combined gate over caprise plus multiko;
  neither subcase alone closes the broad obligation.
- `progression.skipped_decreases`: needs combined current gap closure, plateau
  and entry-freezing evidence. Its gate remains incomplete during first feedback.
- `growth.native_exclusions`: egg/fainted/remote recipients are not covered by
  this narrow level100 pair. Partial deferred cap crossing and simultaneous KOs
  also remain unproven.
- `progression.erika_routes`: actual win/loss/retry/ceremony scripts remain missing.
- Other constructor, replay/link/facility, load-identity and arena gates remain
  explicit missing cases. Prepared fixtures cannot stand in for those contexts.
- All historical UI/items/growth results require a final stable-source rerun;
  obsolete selected-row/Clair requirements stay optional research under D-2312.

Latest edge feedback: gap55→100 passed on the171-host source set, with native
lead evolution19→20 and strict same-party continuity. Its artifacts are preserved;
subsequent test changes make it historical until final rerun. The overlevel job
completed native KO/rewards/teardown but timed out during a second evolution/
move-learning scene. Only the pre-entry level100 recipient now uses already-
evolved species20 with valid candidate stats/EXP; no outcome writes or longer
waits were added. `--edge-cases overlevel curve` targets the pending four battles.
