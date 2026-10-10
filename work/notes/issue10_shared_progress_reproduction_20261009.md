# Issue 10 — bounded native-handler reproduction, 2026-10-09

**D-1579 and D-1580 reproduced in both inputs; their two private operand
candidates pass the bounded controls.** D-1581's shared-state collision is
reproduced, but a separated domain and compatibility policy remain unresolved.
D-1578's one-shot defeat transition is demonstrated; a narrative-correct defeat
continuation is not established and no retry/unlock repair is justified here.

This was offline execution of actual ROM Thumb instructions using a private
subclass of `double_target_thumb_model.CPU`, **not a fresh in-game run**. No
emulator startup, escalation request, download, ROM build, production patch,
source-save edit, decision-register change or commit occurred. D-2300 supplies
the scoped authorization; this handoff changes no production behavior.

## Evidence and execution boundary

Run from the repository root:

```sh
.venv/bin/python work/build/bugfix-sequential-20261009/issue10/repro/matrix.py
```

Private evidence under that `repro/` directory: `native_executor.py`,
`matrix.py`, `matrix.json` (every native command's handler, actual return cursor,
comparison byte and persisted byte writes; every scene stub; executed instruction
bytes), `summary.json`, `run.log`, and `unsupported_full_forest_scene.json`.

The final matrix has **104 passing cases per ROM**, zero unsupported cases in
the bounded matrix, and identical CN/EN semantic traces. It executed **401
distinct native instruction addresses** and read **1,030 ARM9 byte addresses**.
The address-plus-byte SHA-256 of all consumed ARM9 bytes is
`fe7573ce9f5584b7e1416804103c4588f85b67ebbfdc2f908325f5814a3e866a`.
Every consumed byte, every bounded code range and all native command-table entries
used by the executor were checked for CN/EN equality; hashes are in the summary.

Inputs were freshly loaded read-only and pinned by full SHA-256:

- CN `work/rom/origin_v4.0.3_cn.nds`:
  `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8`.
- Latest issue06-fixed EN
  `work/build/bugfix-sequential-20261009/issue06/fix/fixed/origin_hg_v4.0.3_en_wip.nds`:
  `1f955bf433e69ba47d688749d70a635da8c5d9c024e838ed7cd8499dd76bbfa2`.

The ten investigation members 23/45/50/52/92/106/149/842/943/962 were checked
against the inventory's SHA-1 and length, and against each other. Member216 was
additionally executed for the legitimate Route25 domain and pinned in the
summary. Event members5/26/60/114/236/261/289/296/298/416 also match across
inputs; the summary gives their sizes and SHA-256 values.

Native predicates and writes are not mirrored in Python. The executor dispatches
through the ROM command table `020F793C`. It runs the actual halfword/word
operand readers, unsigned comparator `02040110`, GoToIf condition table,
cursor writer `0203F514`, var resolver `0203FAB0→0204F92C`,
SetVar41, Compare17, GoTo22/GoToIf28, Set/Clear/CheckFlag30/31/32 and their
native flag wrappers/core. `CheckBattleWon220` executes the actual helper
`0205172C`: raw outcomes2/3 yield0; 0/1/4/5/6/7 yield1.

Fixture boundaries are explicit:

- Save allocation accessor `0204F858` returns a bounded private save block.
  Special environment accessor `0203FA2C` returns fixture attribute pointers.
  The actual resolver subtracts **0x7FD6**, so special var0x800C uses environment
  attribute0x36; raw battle outcome uses separate attribute0x18. Neither stub
  decides a quest predicate.
- Menu choices, raw battle outcomes, player coordinates and puzzle-side output
  `ScrCmd_729` are supplied fixtures. Messages, movement, fades, cry playback,
  actor creation and other listed scene commands are omitted and logged.
- Native HidePerson101, its native hide routine/getters and the underlying flag
  setter execute. Object lookup uses the real event record's hide flag through
  a private object/manager fixture; object destruction is omitted. This is not
  a claim that a rendered object was present on a naturally loaded map.
- Native Warp176 reads and resolves actual operands and emits the native service
  arguments. The field warp service `02052A4C` is omitted; no map is loaded.
- Event eligibility is **parsed event selection**, using the real record's
  var/value fields. The native coordinate trigger selector is not executed.
  Natural ordering/reachability remains the structural evidence in the
  investigation, not a simulated playthrough.

Instruction and script budgets, an allowlist of native code ranges, bounded
private memory and rejection of unsupported instructions/commands prevent an
unknown path from silently passing. No general script/emulator framework was
added to production tools.

## D-1579 — expedition overwrites beasts eligibility

Native `842@2223` writes11. Leader entry `962@117` at state11 or12 executes
the initial challenge. Supplied Yes / nonloss / accept reaches `962@3482`,
which writes **3, not1**, to private save offset0x13E. For state11 this changes
event5's beasts script14 record from eligible to ineligible. Native beast-release
segment `23@6937..6953` separately demonstrates11→12 and the existing hide-flag
clears. Event selection itself remains parsed.

Controls:

| State/action | Original native result | Private candidate result |
|---|---|---|
| 0/1/2/4/6/7/8/9, Yes/nonloss/accept | Challenge, then3 | Entry predicates unchanged |
| 3 | Existing recruitment dialogue2370 | Same |
| 5 | Existing expedition dialogue2359 | Same |
| 10 | Completed dialogue5827, no battle/write | Same |
| 11/12, Yes/nonloss/accept | Battle and overwrite3 | Completed5827, no battle/write |
| 11/12, No | Retain state | Candidate bypasses challenge |
| 11/12, raw loss2/draw3 | Native WhiteOut3435; retain state | Candidate bypasses battle |

Candidate exists only in private script memory: `962@136` condition byte
`01→04` (equality→greater-or-equal). Compare409F,10 remains native and unchanged.
All states0..12 were exercised through the gate in both versions; full
candidate11/12 paths end in existing completed dialogue. No global409F remap,
partner dialogue harmonization, backward save restoration or legendary reset.
Already overwritten state3 cannot safely identify a damaged save.

## D-1580 — Ho-Oh panel clears Silver's marker

Native new-game `149@190` sets565. Full panel entry45@14, with supplied
puzzle-success flag2426, reaches the actual HidePerson1, Clear273, Set546 and
Clear565 handlers. Native dream initialization50@2675 with1902clear,
1980/1981set and40AB=3 then jumps at2690 to3305. With565set, identical native
gates instead reach3499. This independently reproduces the unrelated collision.

The private candidate changes only `45@184` operand `3502→0000`:
ClearFlag565→ClearFlag0. Native flag0 resolution returns null and performs **no
persisted write**. Full solved panel execution retains565, still clears273,
sets546 and emits the original native Warp request315/5/24/0. Unsolved2426clear
ends64 without these changes in either version.

Arrival controls cover565set/clear,1980/1981clear/set,1902set and chapter40AB=2.
All existing gate destinations remain native. Separate real Silver battle
entry50@2436 uses supplied raw outcomes0..7: loss2/draw3 reach WhiteOut2384
and retain565; all native nonloss results reach legitimate Clear565@3224.
The candidate does not change any dream byte or restore old saves whose565 is
already clear; legitimate Silver completion uses the same marker.

## D-1581 — hunt/Forest collision; repair remains unresolved

Native hunt setters92@6516 and10693 produce2→3 with1120set and2105clear.
Parsed event298 then selects Forest script1. Executing its actual entry52@34
with coordinate fixture16/81 reaches native SetVar52@2875 and changes3→4,
despite the hidden-actor/inactive-Sammy fixture. The actual hunt comparison and
jump92@1878/1884 take different paths: before the foreign write they fall
through to1891; afterward they jump4344.

Native hunt setter92@2209 produces5. Parsed event298 selects script3. Its real
entry52@437 reaches Marauder TrainerBattle763@880; native CheckBattleWon and
GoToIf route nonloss to905 and loss/draw to2910 while2105 remains clear.
A separately retained full-scene attempt stops at unsupported
**52@1290 ScrCmd_459** after that first nonloss battle. It does not prove the
entire confrontation completes or the hunt remains finishable afterward.

The other direction is independently demonstrated at write level: real hunt
setter segments6516/10693/10735/2209 overwrite private genuine Sammy values
3/4/5/6 with2/3/4/5. This proves the competing writes; reaching those setter
segments from a late hunt remains structural evidence, not fresh play.

Genuine-Sammy controls execute the native ranger gate40A2==17, activation
segment92@5364..5378 (set2105, write3, clear1120), Forest entry34→4,
native setter52@6140→5, and completion2397..2405 (set2110, clear2105, write6).
These are explicitly segmented transitions; medicine and later battle scenes
were not driven end to end. Route25's native3820→0 and3899/8994→1 setters
retain their legitimate parsed Route25/hunt-entry eligibility.

Maze event416 controls0..6:2 selects the lower return record;4 selects both
lower-return and upper-entry records;0/1/3/5/6 select neither. Selected
member106 scripts execute native Warp operands: the lower return requests
map327,x17,z82,direction0; the upper entry requests462,x49,z13,direction1.
Map switching and coordinate triggers are not native-engine tested here.

Do not remap4099 globally or implement a guessed new variable/migration.
The investigation's allocation audit and compatibility questions remain open.

## D-1578 and next-stage boundary

Native HidePerson943@3623 resolves object4's real hide flag2188 and writes it
before the separately executed battle/result segment5002..5019. Raw2/3 reach
WhiteOut3755 while2188 stays set and1331 stays set; the chief claim is not
reached. Native nonloss outcomes0/1/4/5/6/7 continue5026 through6397, clear1331
and end6407, with2188 still set. Both inputs agree. The scene between consuming
the Star and Deoxys battle is structural linkage, not continuous movement/battle
play. These results establish the transition, **not intended defeat narrative**.
Keep D-1578's warning and exclude retry/unlock shortcuts.

The private executor now safely runs actual Set/Clear/CheckFlag handlers,
wrappers, resolver and core byte operations for bounded legal save fixtures.
It can support a later sequential issue9 offline probe with explicit private
memory maps and assertion boundaries. Current unknown/native out-of-range
addresses or assertions fail closed; issue9's overflow/special-memory regions
would need deliberate fixture mapping and code pinning. No issue9 case was run.

Next: implementation/verification may scope only the two reproduced operand
candidates. Full emulator movement, map load, battle rendering and save/reload
remain unverified while host execution approval is unavailable. D-1581 needs
further design; D-1578 needs stronger narrative evidence.
