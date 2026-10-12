# Wrong move-tutor moves (investigation, 2026-10-12, agent tutor-wrong-moves)

Issue (queue rank 14): D-1305 Blackthorn tutor promises Play Rough but teaches Flail; D-1338 Rock Tunnel tutor
promises Signal Beam but teaches Pollen Puff; D-1347 Saffron Dojo tutor teaches Charge instead of Volt Switch to a
Pokemon with fewer than four moves. Verdicts: Blackthorn REPRODUCED -> fix `tutor-blackthorn-play-rough`
(branch fix/tutor-blackthorn-play-rough); Saffron Dojo REPRODUCED (three paths) -> fix `tutor-saffron-volt-switch`
(branch fix/tutor-saffron-volt-switch); Rock Tunnel REPRODUCED, JUDGMENT NEEDED (question in the register).

## Decoded scripts (a/0/1/2, untouched Chinese ROM, `romdata.disasm`)

Move ids: 175 抓狂 Flail, 268 充电 Charge, 324 信号光束 Signal Beam, 521 伏特替换 Volt Switch, 583 嬉闹 Play Rough,
676 花粉团 Pollen Puff (bank a027/0739; `work/notes/move_data_audit.md` explains that v3 slots 175/268 were Play Rough
/ Volt Switch and v4 moved them).

| Tutor | member | text bank | move operands in the script | fee |
|---|---|---|---|---|
| Blackthorn | 944 | 0626 #58-#68 | Play Rough half: 175 at MonHasMove @1925, SetMonMove @3461, PokemonSummaryScreen @3551, SetMonMove @3619. Draco Meteor half: 434, correct | free |
| Saffron Dojo | 829 | 0525 #61-#72 | 4-move path 521 (@4369, @4437); <=3 moves: SetMonMove 268 @6368 (GoToIf LE 3 @4321 -> 6363); retry path (4 moves, 'no' to the forget prompt, 'yes' to the retry at 6641): summary 268 @6680, SetMonMove 268 @6748. Counter half: 68, correct | 10000 yen (SubMoneyImmediate) |
| Rock Tunnel | 129 | 0142 #133-#146 | 676 everywhere: MonHasMove @4277, SetMonMove @5194, summary @5292, SetMonMove @5360 | 1 Dusk Ball |

The other tutor findings in the register need no work here: D-0933 (Cherrygrove, text fixed under D-1496), D-0980 and
D-1037 (text slips, resolved), D-1408 (Close Combat fee, a different bug class: no wrong move), D-1138 (messages).
`move_data_audit.md` checked all 71 tutor scripts: no other tutor teaches a v3 id. The Route 25 'Headbutt' row of
`docs_crossref.md` is a doc-generator row for script 216 (it only has MonHasMove 311 Weather Ball), not a
move-id mismatch; not investigated further.

## Author's sheets (local, `Pokémon Origin HeartGold v4.0.3 Cn Items.xlsx`, sheet 3.2道具, read with openpyxl)

* row 585: 嘻闹 (Play Rough) | Blackthorn City | free  -> agrees with the text, so the script is wrong.
* row 554: 伏特替换 (Volt Switch) | Saffron Dojo | 10000 -> agrees with the text and the script's own main path.
* row 599: 花粉团 (Pollen Puff) | Rock Tunnel exit, the Bug Catcher on the left | Dusk Ball -> agrees with the
  SCRIPT (and the v4 move id 676, which has no v3 slot), not with the dialogue, which still says 信号光线.

## Emulator reproduction (DeSmuME via the harness, 2026-10-12; run individually)

Method: the 2026-10-06 `hackbugs --case tutor` recipe (removed 2026-10-09) restored from git (8c16d8d^) into the
scratch folder with a two-line shim for helpers the harness has since moved; the script runs from the label right
after the party selection with 0x800C = 0 (forced state: no walk-up, no prepared story save; the tutor's own
CountMonMoves, SetMonMove, fee, messages and summary run). Pupil: Pikachu-like generator Pokemon Lv 50 with 3 or 4
moves (Thunderbolt, Quick Attack, Thunder Wave, Thunder); money 20000 / 3690 / a Dusk Ball in the bag as needed.
Reproduced under forced state (script entered at the post-selection label), not by natural play.

| ROM | tutor | 3 moves learned | 4 moves learned | fee |
|---|---|---|---|---|
| Chinese | Blackthorn | 175 抓狂 (Flail) | 175 抓狂 | none |
| Chinese | Saffron Dojo | 268 充电 (Charge) | 521 伏特替换 | 10000 both |
| Chinese | Saffron Dojo, retry path (no, no, yes, yes) | - | 268 充电 (summary shows it, then taught) | 10000 |
| Chinese | Rock Tunnel | 676 花粉团 | 676 花粉团 | 1 Dusk Ball both |
| rc7 | Blackthorn | 175 Flail | 175 Flail | none |
| rc7 | Saffron Dojo | 268 Charge | 521 Volt Switch | 10000 both |
| rc7 | Rock Tunnel | 676 Pollen Puff | 676 Pollen Puff | 1 Dusk Ball both |
| rc7 + tutor-blackthorn-play-rough | Blackthorn | 583 Play Rough | 583 Play Rough (summary shows it) | none |
| rc7 + tutor-saffron-volt-switch | Saffron Dojo | 521 Volt Switch | 521 Volt Switch | 10000 both |
| rc7 + tutor-saffron-volt-switch | Saffron Dojo retry path | - | 521 Volt Switch (both summaries) | 10000 |

Screenshots (scratch, not committed): `scratchpad/inv/tutor-wrong-moves/out/{cn,rc7,fixbt,fixsf,fixsfretry,cnretry2}/`;
looked at: `cn/tutor_blackthorn4_summary.png` (summary names 抓狂 at the bottom), `fixbt/tutor_blackthorn4_summary.png`
(Play Rough, Fairy type, PP 10/10 after the forget path), `fixsfretry/summary2.png` (Volt Switch). The
'<=3 moves' question in D-1347 is therefore not an engine quirk: the script itself holds the stale id 268 on the
CountMonMoves <= 3 branch.

## Decisions per tutor

* Blackthorn: script wrong, intended move proved by the text (every line), the author's sheet and the Gym hint.
  Minimal fix, four operands. Done.
* Saffron Dojo: script wrong on three places, intended move proved by the text, the sheet and the script's own
  main path. Minimal fix, three operands. Done.
* Rock Tunnel: the script (676) and the author's v4 sheet agree; only the dialogue is stale. The Chinese text
  tells a whole joke about Signal Beam (#133) and names it in 12 lines. A text fix would have to either rename
  the move in a joke that is about another move (inventing/dropping Chinese content, D-1500) or change the
  English away from the Chinese (AGENTS.md: never silently correct; D-1496 needs the user's approval). Switching the
  script back to Signal Beam (324) would go against the author's own v4 sheet. JUDGMENT NEEDED, question recorded.
  Options: (A) leave and keep the guide's known-issue entry; (B) approve an English-only text change (name Pollen Puff
  in the move-naming lines #134-#146 and decide what to do with the Signal Beam joke in #133);
  (C) revert the script to Signal Beam (undoing the author's v4 change).

## Not verified

* Natural play (walking up to each tutor with a story save): the harness has no such saves here.
* The compatibility lists of the three tutors (species lists in the scripts) were not changed or checked for
  Play Rough / Volt Switch legality.
* Real hardware / melonDS (DeSmuME only).
* The unpatched English develop build (rc7 was the control).
