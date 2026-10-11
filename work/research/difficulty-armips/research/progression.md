# Gym progression and next-gym caps

Research handoff, 2026-10-09; confirmed policy update, 2026-10-10 (D-2312). Companion input: [gym_schedule.json](gym_schedule.json).

The user confirmed **“Keep gym-only; never decrease” (D-2312)**. Select the earliest unfinished gym in researched guide order and return the running maximum of actual gym maxima through that row. No story caps are inserted. Existing Pokémon keep their levels and EXP and remain usable, including when already above the cap. Growth at or above the cap stops; excess newly awarded battle EXP is not banked or redistributed. Rare Candy and Day Care remain native exceptions under D-2304/D-2307.

## Ordered schedule

The order follows the local quest guide and website's `trainer_guide.json`, cross-checked against original Chinese-ROM battle and badge scripts. It is a guide-order selection policy, **not proof that every preceding gym is an engine-enforced prerequisite**. Select the first incomplete row; when it completes, skip later rows already completed. The effective cap is a prefix maximum, distinct from each gym's unchanged actual maximum. The last column assumes the preceding rows are complete.

| Order | Next gym | Trainer record(s) | Actual gym maximum | Effective cap before challenge | Native badge ID | Effective cap after completion |
|---:|---|---|---:|---:|---:|---:|
| 1 | Brock — Pewter | 253 | 12 | 12 | 0 | 20 |
| 2 | Misty — Cerulean | 254 | 20 | 20 | 1 | 25 |
| 3 | Lt. Surge — Vermilion | 255 | 25 | 25 | 2 | 38 |
| 4 | Erika — Celadon | 256 | 38 | 38 | 3, delayed | 55 |
| 5 | Koga — Fuchsia | 257 | 55 | 55 | 5 | 65 |
| 6 | Blaine — Cinnabar | 259 | 65 | 65 | 6 | 80 |
| 7 | Sabrina — Saffron | 258 | 80 | 80 | 4 | 100 |
| 8 | Giovanni — Viridian | 662 | 100 | 100 | 7 | 100 |
| 9 | Falkner — Violet | 20 | 80 | 100 | 8 | 100 |
| 10 | Bugsy — Azalea | 21 | 80 | 100 | 9 | 100 |
| 11 | Whitney — Goldenrod | 714, or 30 with Norman 266 | 88 | 100 | 10 | 100 |
| 12 | Morty — Ecruteak | 31 | 80 | 100 | 11 | 100 |
| 13 | Jasmine — Olivine | 33 | 80 | 100 | 13 | 100 |
| 14 | Chuck — Cianwood | 34 | 80 | 100 | 12 | 100 |
| 15 | Pryce — Mahogany | 32 | 85 | 100 | 14 | 100 |
| 16 | Clair — Blackthorn | 35 | 85 | 100 | 15, delayed | 100 |
| — | All gym challenges complete | — | — | 100 | Not a badge-count test | 100 |

The actual gym maxima remain `12,20,25,38,55,65,80,100,80,80,88,80,80,80,85,85` in `gym_facts[].maximum`. The effective sequence in `proposal.caps` is `12,20,25,38,55,65,80,100,100,100,100,100,100,100,100,100`, followed by the ordinary level-100 ceiling. The JSON's retained `proposal` key now describes the accepted policy.

This replaces the former coordinator interpretation with decreases after Giovanni and Whitney. On the guide route, reaching Giovanni's row permits level100 and every Johto row retains100; new teammates can also grow to100. No later story or gym cap restores a lower restriction.

**Skipped gyms:** later completions do not bypass an earlier unfinished gym and do not raise its cap. If Koga is still unfinished after later gyms, the effective cap stays55. Completing Koga can jump directly over later completed rows. Morty still holds the earliest-unfinished row when skipped, but its prefix maximum is already100. This is a stateless resolver, not a saved highest-cap value: adding completion predicates never lowers its output. Save rollback or clearing a completion predicate can lower the selected stage; transient scripted flag/badge handoffs are evaluated at stable scene boundaries.

### Order and branch details

- **Blaine precedes Sabrina's badge challenge.** The early Saffron willpower scene can occur without the Volcano Badge, but Sabrina's Tower continuation needs it; the Marsh Badge fight follows Saffron's liberation. Native badge IDs therefore are not chronological order.
- **Koga can be delayed.** The guide documents starting the Saffron takeover without the Soul Badge; Koga is absent during the occupation and returns after liberation. An earliest-unfinished resolver still selects Koga's 55 if that gym is skipped. It does not infer which accessible gym the player intends to fight next.
- **Whitney has two initial routes.** The friendly recording choice leads to singles against record 714. The other route uses partner Gold 343 against Whitney 30 and Norman 266 (`883:1303`). Both Whitney records peak at 88; Norman peaks at 87. Neither route changes the cap. Records reused for rematches do not create additional stages.
- **Jasmine precedes Chuck in this hack.** The Mineral Badge starts the Lighthouse Rocket/Amphy arc. Curing Amphy removes Chuck's door blocker; the cave battle against Chuck 718 then returns him to the gym. The guide order is Jasmine, then Chuck, not the familiar vanilla badge ordering. See guide chapters 10 (Olivine Gym and Amphy) and 11 (Cianwood Gym closed, then Storm Badge).
- **Morty may be postponed or temporarily unavailable.** His challenge is blocked during certain League investigation windows. Guide chapter 10 recommends earning the badge before investigation round 4. The selected resolver retains his unfinished row rather than advancing from later story counters.
- Falkner follows the Sprout Tower memorial; the required Route 46 hostage scene precedes that ceremony. Bugsy returns after the Ilex Forest story. Pryce's gym opens after Mahogany Rocket HQ. Clair's challenge precedes the Dragon's Den trial. These are story gates, not additional cap stages.
- These sources establish the above dependencies and branches, not an exhaustive proof of all feasible gym permutations. Keep guide order explicit in both the UI description and implementation contract.

## Completion predicates and resolver contract

The resolver accepts two read-only callbacks scoped to the current, valid save owner:

```c
bool badge(unsigned native_badge_id);  // IDs 0..15
bool flag(unsigned native_flag_id);
// Result: running maximum through first incomplete gym; 100 after all rows.
```

Normal rows use `badge(id)`. The two delayed-award rows instead use:

```text
Erika complete = badge(3)  OR flag(1220)  // flag 0x04C4
Clair complete = badge(15) OR flag(209)   // flag 0x00D1
```

**Native binding implemented in `native/caps.c` (2026-10-10)** using the subsequently verified readers in [candy.md](candy.md): profile `0202933D(save)`, badge `02029429(profile,id)`, VarsFlags `0204F859(save)`, flag `0204F865(vars,id)`. `runtime.c` requires the published current save `02001195()` to equal battle setup+`1C0` and captures at native battle entry. Runtime progression fixtures remain pending; these addresses are actual hack bindings, not vanilla inferences.

### Erika: advance after the gym, before the Rainbow Badge

All script references below are member IDs and decimal byte offsets in `a/0/1/2`.

| Route / milestone | Original-ROM evidence |
|---|---|
| Normal challenge | `784:130` battles trainer 256; the win path sets flag 1220 at `784:1380` |
| Disguise challenge | `783:7652` battles trainer 256; the win path sets flag 1220 at `783:8172` |
| Object-side check | Event member 352, object 7 is the sole mapped object using flag 1220; `784:1424` hides it after the victory scene |
| Later Rocket finale | `853:2599` is a Multi Battle with partner 272 against Ariana 443 (maximum 55) and record 453 (maximum 50) |
| Badge ceremony | `853:3182` clears flag 1220; `853:3330` awards badge 3 |

The combined predicate covers the pre-badge gym victory and the later permanent badge. Thus the cap advances **38 → 55 after Erika**, allowing growth during the Gloom investigation and Rocket arc. Waiting for the Rainbow Badge would retain 38 through Ariana's level-55 encounter.

**Do not use flag 1173.** The disguise route executes `783:7563 HidePerson 11`, whose Celadon event object uses 1173, before battling Erika. A scan of explicit `SetFlag` commands alone misses this premature state change. Flags 1179 and 1089 also change elsewhere in the story and are not standalone victory markers.

There is a short scripted interval between clearing 1220 and awarding badge 3. No battle occurs in that interval. Resolve or refresh growth snapshots at stable scene boundaries; do not treat every intermediate flag write as a persistent player progression state. Static checks support the predicate, but full new-game/legacy-save and both-route runtime tests remain integration obligations (`predicate_verified_for_all_saves` stays false).

### Clair: final gym victory is earlier than the final badge

`939:14122` battles trainer 35. On victory the scene sets flag **209** at `939:14164` and story variable **0x40A2 = 4** at `939:14168`. No other explicit set/clear of 209 was found in the decoded script scan, and it has no mapped event object. Use the victory flag with the badge fallback, not the changing story counter alone.

The Dragon's Den gatekeeper comes next (`111:894`, trainer 936), then Tianyuan (`112:167`, trainer 937, maximum **90**) and the shrine quiz. The Rising Badge is awarded only at `112:4728`; the story counter subsequently becomes 6 at `112:4849`.

If the previous gyms are complete, **Clair's gym victory completes the last gym row immediately after her victory scene**, before Tianyuan. All gym challenges can be complete with only fifteen badges. The effective cap is100 both before and after that victory; her actual gym maximum remains85. There is no additional level-90 cap. A numerical cap100 assertion cannot prove Clair completion: native acceptance must trace flag209, defeat/retry and the later badge fallback.

### Excluded Viridian badge scene

Blue's record 261 peaks at 93, but its `741:151` battle and `741:176 GiveBadge 15` belong to unused entry 1 with no Gym event binding in the reviewed reachability model. Do not use it as the first Viridian gym or as a Rising Badge milestone. The actual first Viridian challenge is Giovanni 662 at `741:2311`, followed by **Earth Badge 7** at `741:2863`. Blue 261 is used elsewhere, including the League and rehabilitation; excluding this script does not mean the trainer record is globally unused.

## Large gaps and intervening story events

These are consequences of the selected gym-only schedule. The ten `story_facts` groups in the JSON identify relevant numeric trainer maxima and available script bindings; they are not an exhaustive boss inventory. Their `after_guide_rank` is guide-route placement, not a machine-enforced prerequisite. None is a resolver stage.

| Interval | Active cap on the guide route | Important intervening events and consequence |
|---|---:|---|
| Surge → Erika | 38 | A 13-level increase; the route to Celadon and Erika's normal/disguise branch sit before the next gym milestone. |
| Erika → Koga | 55 | A 17-level increase. Gloom investigation, auction leads, Game Corner/Rocket base, Ariana 55 and the delayed Rainbow Badge ceremony; then Fuchsia's forest/ninja-bell trial before Koga. |
| Koga → Blaine | 65 | A 10-level increase. Cinnabar's hidden Gym/riddle access leads to Blaine; Saffron's trial has an early setup branch but is not an earlier Marsh Badge award. |
| Blaine → Sabrina | 80 | A 15-level increase. Sabrina's Tower continuation and the Saffron takeover/liberation separate these badge fights. |
| Sabrina → Giovanni | 100 | A 20-level increase. The Sevii/Two Island Granny Mae trial is needed to open Viridian. Recorded trial opponents peak at 73, 76, 75 and 74; consecutive trial battles have no intervening heal. The cap already permits 100 throughout this stretch. |
| Giovanni → Falkner | 100 | Victory Road qualifiers and the Indigo tournament (Goh80, Steven83, Karen85), first Elite Four (88–90), Blue93 and first Hall of Fame precede the Cerulean Cave Giovanni100 duel/rematch. Mt. Silver rehabilitation includes Brock/Misty82, Blue93, Sabrina90 and Yellow82. Oak's Elm errand, early Johto story, Route46 and the Sprout Tower ceremony follow before Falkner. All new growth retains the level100 ceiling. |
| Falkner → Bugsy → Whitney | 100 | Ruins of Alph/Molly, Union Cave and Ilex's bug-catching story precede Bugsy. Goldenrod's recording choice branches Whitney into singles or a Gold/Norman partner challenge; the latter adds the Ruby/Sapphire rescue chain. Actual gym maxima80/80/88 do not lower the effective cap. |
| Whitney → Morty → Jasmine | 100 | Ecruteak's Burned Tower/Marauder chapter and Route39's Gold scene intervene. The former88→80 drop is removed; native party restrictions still apply. |
| Jasmine → Chuck | 100 | Lighthouse opponents reach90, followed by medicine for Amphy. Chuck's required cave encounter peaks at89 and his subsequent Storm Badge team at80. Neither creates a lower cap. |
| Chuck → Pryce | 100 | Lake of Rage, Boot Camp Ruins and Mahogany Rocket HQ include Charon88, Cyrus/Ariana90, Lawrence88 and Petrel87. These remain story facts, not cap stages. |
| Pryce → Clair | 100 | Ice Path and Crystal's Suicune-trap story lead to Blackthorn. Both actual gym maxima are85; the effective cap stays100. |
| Clair → Rising Badge and later story | 100 | Dragon's Den gatekeeper, Tianyuan90 and the quiz occur after the last gym fight but before its badge. Subsequent conference, League investigations and final Rocket/League story retain the ordinary level100 ceiling. |

Cerulean Cave's first Giovanni duel advances only after a loss, but the later double-battle rematch requires a win. Native gym party/type restrictions may require raising new team members; on the guide route these can now grow to100 throughout Johto. No story stage has been added. Large gaps remain documented context under the settled gym-only decision, not pending policy questions.

## Evidence, identity and validation limits

- Authority: untouched `work/rom/origin_v4.0.3_cn.nds`, SHA-256 `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8`. Fresh reads checked `a/0/5/6` trainer maxima and the referenced `a/0/1/2` instructions. The JSON records relevant member hashes and numeric bindings without party dumps or dialogue.
- Local site evidence: `site/src/data/trainers.json` and `site/src/data/trainer_guide.json`; guide order is also explicit in `work/tools/docs/trainer_guide.py`. All included maxima matched the website data during this pass. Source identities for these files and guide chapters are recorded in the JSON. The attempted live trainer-page check was unavailable through the web tool; no live parity claim is made.
- **Source hashes are documentary evidence, not build gates.** Unrelated website or guide edits must not automatically fail ROM integration. Required factual checks should derive maxima and verify relevant instructions from the actual input ROM. Rechecking a changed relevant source is different from requiring an unchanged whole-site hash.
- The ordinary CN party constructor loads the stored level halfword at ARM9 **0x02072816** from record offset 6 and passes it to creation at **0x0207281E → 0x0206D0C0**. Fresh static inspection found no dynamic scaling of that input. The recorded constructor region is **0x02072730**, length **0x228**, with its hash in the JSON. This does not prove every later battle mode leaves levels unchanged.
- Giovanni's native level-100 construction is historical evidence already established: recovery inventory `work/research/difficulty-recovery/record-inventory.json` in checkout `poke-difficulty-research`, record **`/root/earth_badge_verification`**, lines **112, 155, 339**. It includes the music-only `CallStd 2031` trace and the limits of the synthetic combat witness. Historical commands were not executed. No new emulator test is claimed here.
- Morty's record retains its original low-level members; its maximum is 80. No team, script, original save or ROM was modified. The original research pass created documentation/data only, with read-only extraction artifacts under ignored `work/build/difficulty-v2/progression/`.

Native callback bindings and current-save ownership checks are implemented. Native acceptance still needs both Erika branches including defeat/retry; Clair before/after Tianyuan; legacy saves; skipped gyms; and snapshot refresh across the ceremony's transient flag changes. The table and predicates are implemented and host-tested, not a claim of completed runtime acceptance.
