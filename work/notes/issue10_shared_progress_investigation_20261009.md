# Issue 10 — shared progress investigation, 2026-10-09

Proceed to bounded offline native-script reproduction of **D-1579 and D-1580**.
D-1581 is a real state collision but needs a separate domain and a documented
compatibility policy before implementation. **Exclude D-1578 from a simple
retry/unlock repair**: the source intentionally consumes a one-shot encounter;
this investigation does not establish a narrative-correct loss continuation.

Investigation only. No emulator execution, ROM build, production script/tool/
patch/text edit, source-save edit, download, commit or decision-register change.
Earlier fixes and unrelated dirty work are preserved. D-2300 is the scoped
authorization; the reproduction gate remains in force. Host emulator execution
approval was unavailable in the preceding stages; no new request was made.

Private evidence: `work/build/bugfix-sequential-20261009/issue10/` contains
untouched-member dumps/bytes, `inventory.json`, the CN ARM9 and
`native-state-handlers.txt`. This is static evidence, **not fresh reproduction**.

## Inputs and state domains

CN SHA-256: `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8`.
Latest issue06-fixed EN SHA-256:
`1f955bf433e69ba47d688749d70a635da8c5d9c024e838ed7cd8499dd76bbfa2`.
Members 23,45,50,52,92,106,149,842,943,962 match byte-for-byte across those ROMs.
Their sizes/SHA-1 values are in the private inventory.

Native persisted vars are halfwords `0x4000..0x416F`, at
`vars + 2*(id-0x4000)` (ARM9 resolver `0x0204F92C`). Consequently `0x4099`
is offset `0x132`, and `0x409F` is offset `0x13E`. Special vars `0x8000+`
are environment fields, not persisted quest domains. Persisted flags 1..3231
are at `vars+0x2E0+(flag>>3)`; native flag 0 is a no-op.

The inventory includes all decoded script operand uses, all object hide flags
and full coordinate records for the relevant IDs. It is not a proof that a
newly chosen variable is unused by native engine code, computed operands or
script-header tables. Do not allocate a new marker from that scan alone.

## D-1578 — Deoxys and Lucky Meowth God: disputed repair scope

Map290 uses script943/event261. Red Star object4 at213,68 starts script11,
entry676, and uses hide flag2188. Lance's one-time home visit clears2188 at
842@2205. The scene requires Red/Blue Orbs (534/535); 943@3623 HidePerson4
sets2188 **before** the battle. Deoxys object26 is shown with flag1366 toggled
around ShowPerson, then WildBattle386 at5002 runs. CheckBattleWon5009,
Compare5013, GoToIf5019 sends loss/draw to3755 WhiteOut/ReleaseAll/End.
All nonloss results continue at5026, including capture, knockout and fleeing.

The chief's claim runs5026..6407. At6397 it clears1331; One Island restaurant
map205/script894/event198 objects16/17/18 use1331. The earlier story uses
1331 in members212/249/739; the restaurant completion sets it again at
894@4753/@5011. No other post-game reachable clear was identified.

This is an asymmetric missable, rather than one unrelated quest overwriting
another quest's counter. The chief holds the player responsible for the Red
Star's disappearance even after fleeing/knocking out Deoxys, so loss also
having a follow-on scene is plausible. It is not proven intended. Clearing
2188 on loss would give another legendary attempt; clearing1331 before
whiteout would skip the chief's entire claim; redirecting loss past WhiteOut
would change native defeat recovery. None is a faithful minimal repair.
Retain the historical finding/warning. Do not implement any of these shortcuts.
Recovering an already consumed Star without the claim would require a distinct
pending-scene design and deliberate narrative choice outside this handoff.

Sources: D-1578; guide06 post-game Deoxys entry and known-issues “Losing to
Deoxys”; historical CN+EN traces in `guide-review-20261006/ch06/deoxys_*`.

## D-1579 — expedition leader overwrites beasts eligibility

`0x409F` has sequential reused domains: early Kanto setup (member189 writes1),
bug-hunt count (92 increments2101/2290/2479/2574, reward5743 resets1),
expedition3→5→6→7 in962, B1F8→9→10 in98, Lance's home visit11
(842@2223), and beasts released12 (23@6953). All literal uses and event
records are inventoried. Do not remap this ID globally.

Natural ordering is explicit in guide11: the expedition opens the final-chapter
altar path, then final Hall of Fame/Lance's home visit advances the same counter
to11. Member98@3526 sets10 and @3536 clears461, making the completed
expedition leader visible again. HidePerson during962 script11 does set461;
the older D-1406 “never set” claim is obsolete.

Leader map250 object4 starts962 script2/entry117. At128 it compares state10;
134 branches on equality to5827 (completed-partner dialogue). It tests5/3 next,
and every other state offers the initial “strong Trainer” challenge. Yes at188
reaches TrainerBattle897@2706; loss goes3435 WhiteOut, No ends without writing.
Victory plus accepting the invitation reaches3482 SetVar409F,3. State11 is
therefore erased. Burned Tower map7 event5 coord2 (12,18,7×3) selects script14
only at state11. Script23@6937 clears1855 and beast hide flags2318..2320,
then writes12. Lance's visit is one-time, so the eligibility does not return.

**Minimal candidate:** keep Compare409F,10 and change the branch condition at
962@134 from equality1 to greater-or-equal4. The byte at136 changes01→04;
the registry's halfword patch can pin offset136 `3601→3604` (next displacement
byte is36). State10/11/12 all use existing completed-partner dialogue5827;
no battle/reset occurs. Existing3/5 choices, loss handling, recruitment and
beast release remain native. Other expedition partners' equality10 checks at
241/324 (and961@56) are separate; no reset at those talk entries was established.
Do not broaden this repair merely to harmonize their dialogue.

Old saves already reset to3 cannot be safely distinguished from actual
unfinished expedition progress using409F alone. This forward guard must not
silently restore11 or re-release already caught beasts. Explicitly report that
it prevents future resets and does not repair existing damaged progress.

Sources: D-1579/D-1406; guide10/11/12 scoped warning; historical
`guide-review-20261006/known-issues/F/leader_{cn_no,cn_yes,en_yes}`.

## D-1580 — unrelated Ho-Oh puzzle clears Silver's battle marker

New-game149@190 sets565. Its only decoded clears are puzzle45@182 and
Silver victory50@3224. All seven decoded readers are in dream member50
(2556/2686/2745/2944/3486/3684/3827); dream event296 objects14/15 also
have hide flag565. No puzzle object, puzzle reader, or other event uses565.

Map318's Ho-Oh panel script45/entry14 launches AlphPuzzle3 with no story
check. Successful solve reaches134..182: HidePerson1, clear273, set546,
clear565. The puzzle's own state is not565. Dream map325 header311's
initialization path reaches50@2675; with1902 clear, Check565@2686 and
GoToIf2690 jump3305 when565 is clear, repositioning Silver/Croconaw after
their battle. With565 set and1980/1981 set, it instead reaches3499 to gather
the three companions. Native MultiBattle602/280/601@2436 is Silver's help
battle; its success reaches3224 and only then legitimately clears565. The
steps check2556 also treats cleared565 as Silver finished.

Natural choice evidence: the independent Ho-Oh panel is available before the
Molly/Silver dream story; nothing in its scene or puzzle semantics requests
skipping that story battle. This is a strong unrelated-marker collision.

**Minimal candidate:**45@182 ClearFlag565→ClearFlag0, changing only operand
at184 `0235→0000`. Native ClearFlag0 performs no write. Keep clear273,
set546, floor movement/warp, panel flags and every dream byte unchanged.
No new saved marker is needed. Restore565 on every load would replay completed
Silver battles and is unsuitable.

An old save where the panel already cleared565 is ambiguous once the dream
chapter has begun: legitimate Silver victory uses the same bit. Preserve it;
do not introduce guessed migration. Prevent future interference. Historical
arrival comparison does not prove the full dream chapter was driven.

Sources: D-1580; guide08 dream story and known-issues early-panel entry;
`guide-review-20261006/pass2-A/hooh_arrive_{early,normal}_cn`.

## D-1581 — bug hunt drives Forest of Time's later scenes

`0x4099` has three domains: Route25 member216 writes0@3820,1@3899/@8994
(event26 coord1 on0); Ilex bug-hunt entry event114 coord0 on1, Honey handover
92@6516 writes2, first-rock outcomes10693/10735 write3/4, the remaining
outcomes2209/2398/4564/4682/9396/9796 write5, reward5713 resets2;
Sammy ranger scene92@5372 writes3,52@2875 writes4 (medicine),6140 writes5
(upper-forest confrontation),2405 writes6 (finished). Member92's 20 comparisons
of4099 all belong to the hunt; its5372 is the one Sammy setter.

Ranger script16/entry616 requires40A2==17 at635 to start the genuine Sammy
scene. It sets2105@5364 and clears actors' hide1120@5378. Forest map327
event298 coord0 (16,81,3×2) selects52 script1 on4099==3, and coord1 (15,38)
selects script3 on==5, with no story/actor guard. Scene1 writes4@2875 even
when the actors are hidden. Scene3 runs Marauder battles and eventually writes6.
There is no conditional gate on the Ilex map117 warp to327. This gives a
natural mid-hunt detour; it does not require a fabricated contradictory flag set.

Maze map462/event416 uses4099==2 or4 at49,13 to run106 script1 and warp
back to327 entrance17,82; ==4 at49,50 runs106 script3. Values3/5 from the
hunt bypass the last-exit restriction as well as invoking the wrong scenes.
The arrival3→4 demonstrably mutates the hunt's own state. Historical tests did
not prove completing the hunt after that interference.

**Candidate design requiring further investigation:** separate the Forest of
Time progress into a reserved persisted variable, leaving Route25 and every
bug-hunt4099 reader/writer intact. Remap the Sammy setter92@5372, all three
52 writers, both event298 coordinate vars and three event416 coordinate vars.
Preserve the harmless pre-Sammy maze restriction: simply moving the ==2 record
to a zero-initialized new variable removes the original restriction. A deliberate
initialization/legacy prequest check is needed. Do not remap all92 operands,
the entire4099 ID, or adjacent bug counters; those are outside this finding.

The literal inventory lists possible unused persisted IDs (e.g.4160), **not a
reserved choice**. Audit native indexed users and script headers before choosing.
Alternative disjoint values in4099 also need controls proving a late unfinished
hunt cannot overwrite real Sammy progress; they are not a complete separation.

For compatibility, flag2105 distinguishes a genuine active Sammy lead: it is
set by the ranger and cleared52@2401 when finished;2110 is set52@2397 at
completion. These are migration evidence, not a final migration design. Check
all readers/writers before using them. Legacy3/4/5 without2105 normally belongs
to the hunt; with2105 may belong to Sammy. Already corrupted saves may have
false2110 or lost hunt state, which cannot safely be reconstructed. Keep normal
prequest, genuine active, genuine completed and ambiguous saves distinct.

Sources: D-1581/D-1429; guide09 hunt/Sammy entries, guide13 maze, known-issues;
historical `pass2-A/fot_{v3,v5}_{cn,en}` and `ch13/maze_*`.

## Bounded offline reproduction handoff

Existing `work/tools/double_target_thumb_model.py` supplies a Capstone Thumb
CPU, already used to execute the native battle-result helper in the Magcargo
tests. `.venv/bin/python` imports its dependencies offline. A private subclass
can map pinned ARM9 plus real script bytes and execute native state handlers.
Add only necessary missing instructions (notably STRH/BICS; fail on unsupported
instructions). Do not rewrite script comparisons/jumps/SetVar as Python logic.

Native command table0x020F793C: CompareVarToValue17→02040208,
GoTo22→02040368, GoToIf28→02040440, SetVar41→02040650,
Set/Clear/CheckFlag30/31/32→020404A8/C0/D8. Execute actual halfword/word operand
readers0203F534/54C, unsigned comparator02040110, branch lookup table and native
cursor writer0203F514. Execute var resolver0203FAB0→0204F92C and flag
wrappers→0204F864/890/8B8/E4. Stub only save-array allocation accessor0204F858
to a private block and special-var environment lookup0203FA2C for8000+ fixtures.
The latter supplies choices/outcomes; it must not decide quest comparisons.
Pin every handler and table against CN and current fixed EN.

| Case | Real native script segments / supplied fixture | Required trace |
|---|---|---|
| Expedition positive |842@2223;962 entry117, menuYes and battlewon=1, accept|11→3 at3482; state11 event5 eligibility lost|
| Expedition controls |states1/3/5/6/7/8/9/10/11/12; menuNo, battleloss|10→5827;11/12 wrongly initial challenge; No/loss retain11; early recruitment behavior recorded|
| Puzzle positive |149@190;45@174..182;50@2675 onward,1902clear/1980+1981set/40AB3|565set→clear;2690→3305 rather than3499; legitimate Silver-clear3224 remains distinct|
| Puzzle controls |565set/clear; puzzle notsolved2426clear; Silver win/loss|arrival branching, puzzle own273/546 changes; native Silver successclears565/loss retains|
| Hunt interference |92@6516 then10693;52 entry34 through2875|2→3→4, flags1120set/2105clear; hunt comparison branches change after foreign write|
| Hunt late branch |92@2209 or2398;52 entry437; battle outcomes supplied|5 triggers Marauder script despite missing Sammy activation; record mutation/battles reached without claiming rendered scene|
| Genuine Sammy controls |92@5372/@5378;52@2875/@6140/@2405|3→4→5→6 with2105/1120/2110 lifecycle; same sequences in both inputs|
| Maze |real event416 records and106 scripts1/3, values0..6|matching records and actual native Warp operands;2/4 return327,3/5 pass through|

The offline event-row matcher may establish the record's var/value eligibility,
but unless the actual coordinate-selector native function is also executed,
label that layer **parsed event selection**, not native engine trigger execution.
Likewise stubbed messages, movement, battle results and object presence prove
state/control flow, not rendered behavior, player reachability or emulated play.
Record every stub, entry point, actual native byte write and return cursor.
Use native CheckBattleWon helper0205172C for supplied raw outcomes (2/3 are
loss/draw; others nonloss), not a guessed win predicate.

Priority: reproduce expedition and puzzle first, then prove the hunt write/read
collision independently of any proposed fix. Only after that design D-1581's
allocation and compatibility; stop/log it if a sensible bounded repair is still
unproved. Emulator UI, natural movement and save/reload remain a separately
reported verification limit while host approval is unavailable. D-1578 stays
excluded unless stronger intended-loss evidence is found.
