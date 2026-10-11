# Issue 6 — Magcargo loss reproduction, 2026-10-09

**Reproduced in untouched Chinese and the issue05-fixed English ROM with a
valid one-Pokémon fixture.** Native object8 interaction and the catch choice
reach the Magcargo battle; loss returns to the broken in-place retry and
freezes. A four-byte loaded-RAM whiteout diagnostic restores control and
heals the party, but Magcargo is absent on returning to Pokémon Tower.
This is reproduction only under D-2300: no production fix, ROM build,
source-save edit, download, decision edit or commit.

Private evidence: `work/build/bugfix-sequential-20261009/issue06/repro/`.
`commands.txt` retains the exact runtime commands; `summary.json` records
result-file and harness hashes. Each sandbox run aborted134 at DeSmuME host
startup and the exact command was rerun with `require_escalated`. That host
abort is separate from the reproduced game freeze. One emulator ran at a time.

## Fixture and limits

Fresh boot/private battery per run, source
`work/build/memcheck/full_bag_6mons.sav`, clock noon2026-10-09. The first Chinese
attempt naturally entered script8 by walking from `(2,39)` onto the grunts'
coordinate trigger. It reached TrainerBattle992+993@2347, but the battle UI
driver did not finish within900 iterations. `cn-native/result.json` preserves
that incomplete prerequisite attempt; it is not a completed native story run.

The accepted runs use the explicitly controlled post-grunts loaded-object
fixture: enter map155 at `(2,52,UP)` with1155 clear, then set1155 and0x40B7=1,
clear1156/2006 in private RAM, and run native HidePerson4/7. These are the
grunts scene's completion writes. Object8 stays loaded. No reload follows
before talking to Magcargo. This proves the real encounter/loss path from
that state, not the entire preceding adventure.

The hack's native generator creates a strictly validated Lv5 Magikarp. Its
closed record is copied to slot0 and the private active party count becomes1;
Splash150/PP40 and empty remaining move slots are prepared with the existing
strict editor. HP starts17. No HP, battle-result or task rewrite; ordinary
FIGHT selection produces defeat. The accepted before/after records retain
Lv5, plausible unchanged stats, checksum validity and closed flags0. Every
post-loss record in the three accepted runs also passes extension sanity.

Earlier six-clone runs are excluded from accepted proof. The Chinese run's
post-loss slot1 had an impossible Lv195/stat extension despite a valid boxed
checksum. Nothing was repaired, and the one-mon runs replace that evidence.
The first whiteout diagnostic recovered/healed but its movement assertion ran
while the Nurse dialogue was open. The fresh repeat closes that native dialogue
with B before assessing movement; only that complete repeat is accepted.

## Native failure

Guarded dispatch hook0x0203F4CE reads context+0x7C/member base and context+8/cursor.
The complete loaded14766-byte member17 must match the ROM before tracing.
The talk hook is guarded by the overlay signature. Result hook0x02048E18
separately records the raw battle result and stored won value; WhiteOut/task
hooks distinguish actual recovery from a generic timeout or PC sample.

| Accepted run | Loss iterations | Raw / won | Post-loss evidence |
|---|---:|---|---|
| `cn-single/result.json` | 13 | 2 /0 | Black screens, HP0, no field recovery |
| `en-single/result.json` | 17 | 2 /0 | Same native failure |

Both traces record native script10 at648, messages33/34, choice0,
CallIf688→2519, WildBattle219 with original operands `[219,65320,0]`.
The battle screenshots verify Magcargo Lv40. After loss:
CheckBattleWon2536 stores0; compare2540 reads0; GoToIf2546→2519; the second
TouchscreenMenuShow2519 stalls with cursor2521. Exactly one WildBattle and one
battle-block cry execute. No second cry, second battle or WhiteOut occurs.

Twenty150-frame observations with occasional A/B/START all retain fieldFalse,
map155 at2,52 and valid fainted Magikarp. The final PC0x01FF8030 is supporting
evidence only. Flags1155=True,1156=False,2006=False and0x40B7=1 remain unchanged.

## Bounded whiteout diagnostic and encounter visibility

`en-single-whiteout-closed/result.json` passes. At native entry648, the only
loaded member changes are offsets2549–2552: `de ff ff ff`→`51 05 00 00`.
Loss still records raw2/won0; branch2546 now reaches native WhiteOut3914 and
task0x02051B3C. Magikarp heals to17/17. After closing the Nurse dialogue,
native movement changes `(501,8,13)`→`(501,8,14)`.

Returning by native Warp to155 leaves1155 set and0x40B7=1. The active native
object scan has no object8; `return-no-magcargo.png` shows its empty tile.
All nine1155 objects are absent on reload. No flag was cleared to manufacture
retry success.

**Visibility nuance for the separate fix stage:** the native grunts already
set1155 before the catching choice. Decline695–699 neither clears1155 nor
adds a respawn hook. Therefore declining and normally leaving/re-entering the
map also hides Magcargo, by the same loader rule. Whiteout disappearance ends
the current visit and follows existing reload visibility; it is not evidence
of a newly added flag mutation. It nevertheless replaces the explicit attempted
in-place retry, so the behavior choice belongs to the fix stage. No persistent
retry marker, shared-flag clear or engine recovery patch was introduced here.
Decline/reload visibility is statically established, not a separate runtime
outcome test. Knockout/capture/flee/draw were outside this bounded stage.

## Input integrity

| Input | SHA-256 |
|---|---|
| Untouched Chinese ROM | `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8` |
| Issue05-fixed English ROM | `7f85c44d5416ce87e2b9afb37b535899cef1b048ded0098079abe88c30db218d` |
| Source battery, unchanged | `b3aca10747cd0f1adc3d5852a50dddaaa36ed8680f5ba04012cfe3110faad90f` |
| Native member17, both ROMs | `a2e86eeef6662253bd5fb1ee4dc68ebe4930d0768eeb34d6459dda7ecdc164a3` |
| Diagnostic loaded member17 | `2676b6f6158a48667da278c68562556e308a4f3696bd37d2cacd442387be05e4` |

The final private harness SHA-256 is
`b8e2ea0c827452418a82f3298514eebd72732ad6f4deb1486e00b72ef563fbfc`.
The enabled zero-PP/rock-tunnel repairs and all unrelated dirty files were preserved.
