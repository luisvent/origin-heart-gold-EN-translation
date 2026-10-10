# Issue 5 — Rock Tunnel corner-child loss reproduction, 2026-10-09

**Reproduced on untouched Chinese and pinned English. Proceed to the separate
implementation stage.** A diagnostic changing only the loaded private script's
four-byte loss displacement restores native whiteout and permits retry. No
production patch, ROM build, source-save edit, download, or commit was made in
this stage. D-2300 supplies the scoped authorization for the later fix.

## Scope and fixture

Private runner and artifacts: `work/build/bugfix-sequential-20261009/issue05/repro/`.
Only one emulator ran at a time. Each run freshly booted its own private battery
copy of `work/build/memcheck/full_bag_6mons.sav`, pinned to noon 2026-10-09. The
English input was the issue03 Struggle-fixed private ROM, **not RC7**; its script
member 129 is byte-identical to CN and RC7 (investigation-stage static checks).

The fixture clears 1966 and 1554 only in the private copy, then uses the game's
native debug generator to produce a valid Lv5 Magikarp with real stats and HP.
The runner copies that strictly validated native record into the six private RAM
party slots, preserving count/capacity 6, then edits moves through the strict
editor to Splash 150 / PP40 and empty remaining slots. Thus these are six copies
of one native record, not six independently caught Pokémon. All six records
passed checksum validation before battle; each began with HP17. Defeat used
ordinary FIGHT/move selection and forced switches: no HP, result, battle task,
trainer, allowed-loss argument, or progress flag was altered to force the loss.

Warp setup puts the player at map342 `(43,99)`, facing UP. A real A interaction
reaches the visible corner-child object, script18, entry1624, message75, and native
TrainerBattle606 with arguments `606,0,0,0`. No substitute script was used for the
native failures or the branch diagnostic. This proves a real object interaction
under a controlled fixture, not a complete unmodified story playthrough.

**Source-save correction:** the first attempt to edit the existing live party
failed with `Pokémon checksum mismatch`. An initial interim explanation called
the seed record invalid; direct source-file inspection subsequently disproved
that. `SaveFile(...).party()` reports all six battery records valid. Live slot1
can be sampled during native mutation at a frame boundary, with implausible
decoded species/HP and checksum failure. Nothing was repaired or saved. The weak
fixture avoids editing that transient record. Likewise, post-whiteout samples
with checksum failure are excluded from healing claims; frame10578 in the
diagnostic is a fully valid six-record snapshot with every HP17. The diagnostic
also contains valid neighboring samples. A sampled invalid live record is not
evidence that the source save or the game permanently corrupted a Pokémon.

## Native failure evidence

| Observation | CN native | English native |
|---|---|---|
| Actual talk/script | script18, entry1624 | script18, entry1624 |
| Battle | trainer606, second trainer0 | trainer606, second trainer0 |
| Native CheckBattleWon | handler at script2887; next compare takes equality | raw battle result2; stored won output0 |
| Loss branch | GoToIf2897 →3782, frame9354 | GoToIf2897 →3782, frame9753 |
| Final interpreter cursor | member3784 | member3784 |
| WhiteOut handler/task | never called | never called |
| Completion/reward flags | all unchanged, false | all unchanged, false |
| Party after loss | all six HP0 | all six HP0 |
| Field restoration | absent through final frame11997 | absent through final frame12396 |
| Final map/player | 342,43,99 | 342,43,99 |
| Final ARM9 sample | `0x022A2968` | `0x022A2268` |

The finite postbattle observation is **40 iterations of B +60 frames** (the
press also advances its key frames), totaling2640 emulated frames after the
battle-exit sample. Both screens remain black; screenshots `cn-native/after.png`
and `en-native/after.png` were captured, and English was visually inspected.
No postbattle NPC message opened on either native run. The primary script
context reaches the wrong branch before field overlay restoration.

The CN console explicitly emitted:

```text
ARM9: Undefined instruction: 0x1C141316 PC=0x022A295C
```

The English file `en-native.log` explicitly records:

```text
ARM9: Undefined instruction: 0x27110010 PC=0x022A225C
```

These observations, real defeat, the branch trace, black screens, and absent
restoration establish the failure. A PC merely lying in the broad
`0x02200000–0x02400000` range is **not** used as a crash oracle. No independent
heap/overlay ownership claim is made for those final addresses.

Instrumentation logs actual command-handler entry, context+8 interpreter PC,
selected return points, and the native result store at `0x02048E18`. That store
receives won0 and raw result2 in English; the handler's ordinary function return
is1, which is an interpreter yield value, **not victory**. CN ran before the
extra native-result-store hook was added: its equality branch and six HP0 prove
the same defeat path, but its report does not directly capture raw result2.
The old CN runner also logged calls at the talk-handler address while battle
overlays occupied it; only the verified prebattle actual script18 interaction
is used. The final runner guards that talk hook with the field code signature.

The report stores ARM9 PC/register samples, script contexts/cursors, and
FieldSystem pointers where available. It does not decode every TaskManager
record. The explicit WhiteOut task entry is instrumented separately.

## Branch-only diagnostic

English diagnostic uses the same pinned ROM, weak fixture and real interaction.
At initial script startup it asserts old bytes, then writes only the loaded
member129 displacement:

```text
offset2900: 6e030000 →56ffffff
RAM member base0x022A7A44; write address0x022A8598
```

The loaded member is disposable RAM; ROM bytes remain unchanged. No trainer
option or injected postbattle script was used.

The native loss result remains2/won0. Frame9717 records GoToIf2897→2734,
WhiteOut at2734, and entry to native whiteout task `0x02051B3C`. The field returns
to map501, the fixture's Pokémon Center. The original script executes
ReleaseAll2736 and End2738 at frames10581/10582. At frame10578 all six records
are valid and fully healed HP17. Final location is `(501,8,13)`; ordinary DOWN
movement changes it to `(501,8,14)`, establishing player control. Money stays3650
in this fixture; native monetary behavior was not overridden or redesigned.

Flags **1966,1554,1884,1885,1868** are false both before and after. The diagnostic
then uses a normal warp back to `(342,43,99,UP)`. A second real talk again enters
script18, message75, and TrainerBattle606 at frame12955: loss leaves retry
available. That new load contains the original ROM branch; the runner does not
alter the retry script or run a second defeat. Victory, already-found and reward
gate controls are left to the separate implementation agent as requested.

The proposed production repair is therefore the existing guarded member-byte
edit from the investigation: `expect="036E 0000"; new="FF56 FFFF"` at2900,
targeting the file's existing native WhiteOut block. Preserve win message76,
flag1966, all four-child/reward logic, trainer606 and battle arguments.

## Exact commands and runtime limits

All commands were run from the repository root. Native DeSmuME first exited134
during startup inside the sandbox, before gameplay. The same command was rerun
with `sandbox_permissions=require_escalated`; this host startup abort is separate
from the reproduced game failure. Later emulator commands used that required
escalation directly. The first successful CN run also followed a failed strict
live-party-edit attempt; that exception occurred before the actual scene.

```sh
.venv/bin/python -u work/build/bugfix-sequential-20261009/issue05/repro/reproduce.py --rom work/rom/origin_v4.0.3_cn.nds --out work/build/bugfix-sequential-20261009/issue05/repro/cn-native
.venv/bin/python -u work/build/bugfix-sequential-20261009/issue05/repro/reproduce.py --rom work/build/bugfix-sequential-20261009/issue03/fix/fixed/origin_hg_v4.0.3_en_wip.nds --out work/build/bugfix-sequential-20261009/issue05/repro/en-native > work/build/bugfix-sequential-20261009/issue05/repro/en-native.log 2>&1
.venv/bin/python -u work/build/bugfix-sequential-20261009/issue05/repro/reproduce.py --rom work/build/bugfix-sequential-20261009/issue03/fix/fixed/origin_hg_v4.0.3_en_wip.nds --out work/build/bugfix-sequential-20261009/issue05/repro/en-diagnostic --diagnostic > work/build/bugfix-sequential-20261009/issue05/repro/en-diagnostic.log 2>&1
.venv/bin/python -c 'import sys; sys.path.insert(0,"work/tools"); import emu_harness as E; s=E.SaveFile("work/build/memcheck/full_bag_6mons.sav"); print([(i,m["checksum_ok"],m["species"],m["flags"]) for i,m in enumerate(s.party())])'
```

The battle loop is bounded to900 iterations, with messages, menus and forced
switches handled normally; native runs reached the postbattle script far before
that bound. The failure oracle uses the subsequent fixed observation window,
not a generic timeout. Savestates are private artifacts from each own ROM and
were never loaded across ROMs.

## Hashes and preservation

| Input/artifact | SHA-256 |
|---|---|
| Untouched CN ROM | `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8` |
| Pinned issue03-fixed English ROM | `93514313cba83acbb3f6b870fddfc9b111d62ad20b763a0670e4dd67ab074668` |
| Preserved root English ROM | `6fa7b4e739391ca9ea9bfcf90d83eec6407c3c04102e52432bb41bc8ae44a7d3` |
| Preserved source battery | `b3aca10747cd0f1adc3d5852a50dddaaa36ed8680f5ba04012cfe3110faad90f` |
| CN native result | `0a8ce928a29c6c4fc4b6b94624292aad13ab79c2f9ab5d585b5da740b3cb757f` |
| English native result | `428d77b18d13d739d24218b67b448cc1f7a4dabf3d30fc899528f9a067d389a6` |
| English diagnostic result | `52a801f0e8956499029d9c57d7410687f27a4019fa58b2345167e43221ddbe75` |
| Final private runner | `b154bd972064c12dd7b3b3f02cc116bbd0bf842cf83ccd93b2941bcb247e4c3f` |

Exact log hashes and paths are in private `repro/final-hashes.json`. Native
member129 SHA-1 is `c73334fd0e00250cad1b66fc2b929931374bdca4` (6030 bytes).
All input hashes still match investigation values. No unrelated tracked or
untracked work was edited. No decision register change was needed in reproduction.

## Suggested implementation gates

1. Guard whole source member129 and the four expected bytes; confirm only
   instruction2897's target changes, size/header/entries stay identical, and
   unrelated NARC members and earlier Struggle overlay patch remain intact.
2. On production fixed-ROM bytes, repeat real object interaction and ordinary
   loss: won0, branch2734, native WhiteOut, field restored/healed/control,
   unchanged completion/reward flags and retry. Preserve an unfixed control.
3. Win trainer606 normally: message76, set1966 only, no WhiteOut. Talk again:
   existing post-win dialogue, no new battle, flags unchanged.
4. Preserve three other children's completion flags through loss and victory;
   verify the reward remains gated on all four, and flag1868 prevents a duplicate.
   Use private documented fixtures; do not change unrelated quest behavior.
5. Avoid trusting transient decoded RAM Pokémon data. Use a fully valid closed
   snapshot for party assertions or prepare weak moves in the private battery
   fixture before boot. Keep original batteries and ROMs byte-identical.
