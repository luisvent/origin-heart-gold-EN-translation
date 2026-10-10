# Issue 6 — Pokémon Tower Magcargo loss repair, 2026-10-09

**Enabled and verified locally.** D-2300 explicitly authorizes this scoped
original-hack repair for D-1560; **D-2306** records the critical recovery and
visibility choice. Native CN/English failures and the loaded-RAM diagnostic are
in the preceding investigation/reproduction notes. This stage finishes the
four-byte repair with host checks, paired private builds and one native fixed-ROM
loss/whiteout/control run. No download, commit, publication or source-save edit.

## Critical choice: whiteout ends the current visit

Use the existing native WhiteOut/ReleaseAll/End block at3914. Preserve shared
flag1155 and progress variable0x40B7. The preceding grunts scene sets1155 at2493
and0x40B7=1 at2509 **before the Magcargo catch choice**. Its object remains
available only in the already loaded map. Decline695–699 does not clear1155;
ordinary departure and reload already hide Magcargo and every other1155 object.
Thus whiteout follows the existing reload visibility rule. It replaces the
broken attempted in-place retry; it does not create persistent retry availability.
Do not clear1155, replay the grunts, allocate retry flags or introduce recovery
hooks. This supersedes the investigation note's recommendation to retain retry
or skip, using the clarified native decline/reload evidence recorded in the
reproduction note and explicit fix-stage direction.

The native CheckBattleWon handler at0x02048DF0 calls0x0205172C at0x02048E14,
then stores its result at0x02048E18. Direct disassembly and execution of the actual
16-byte helper show raw2 and3 return0; every other raw value returns1. The
handler's ordinary return1 is its interpreter return, not the won value.
Only loss/draw therefore reach the changed branch. Knockout, capture and flee
retain the native nonloss hide continuation at2553.

## Exact production change and host verification

`work/patches/magcargo-loss-whiteout/fix.toml`, enabled, uses the existing guarded
NARC patch stage. In `a/0/1/2` member17, offset2549 /0x9F5:

```text
de ff ff ff (-34; relative to2553, target2519)
51 05 00 00 (+1361; relative to2553, target3914)
```

The entire original14766-byte member SHA-1
`3b381a8adc85353ba9b906bd18521f7efcad95cb` and expected four bytes are both
checked before any write. There is no engine, event, header, save, graphic or
text edit. The original WildBattle operands219,65320,0 (effective level40),
CheckBattleWon, equality condition, decline, native hide list8/3/5/9/10/12/13,
flag writes and every other reachable command remain unchanged.

`work/tools/test_magcargo_loss_whiteout.py` verifies full reachable disassembly:
identical entries and instruction addresses, with only instruction2546's target
changed. It executes the actual native outcome helper for0–255 and unsigned
boundary values, checks the call/store signature, and checks all branch outcomes
0–7. It verifies the existing WhiteOut/ReleaseAll/End block, untouched one-visit
state and nonloss hide path. Whole-member source changes at six locations are
rejected before mutation; the four-byte guard is also tested independently with
a deliberately matching changed-member hash. Combined focused/NARC suite:
**13 tests pass**. Ruff and `fixes.py check` pass; `FIXES.md` regenerated.

## Paired private builds and exact differences

Both full current-tree builds use existing local armips0.11.0, banks and graphics,
`--no-regen-graphics --no-patch`. Both pass full build verification: NARC/text
round trips and export equality, glyphs, graphics, hardcoded code and text speed.
Outputs are only under ignored
`work/build/bugfix-sequential-20261009/issue06/fix/{without,fixed}/`.

| Artifact | SHA-256 |
|---|---|
| Current tree without this fix; identical to issue05-fixed ROM | `7f85c44d5416ce87e2b9afb37b535899cef1b048ded0098079abe88c30db218d` |
| Fixed current tree | `1f955bf433e69ba47d688749d70a635da8c5d9c024e838ed7cd8499dd76bbfa2` |
| Fixed member17 | `2676b6f6158a48667da278c68562556e308a4f3696bd37d2cacd442387be05e4` |
| Preserved Rock Tunnel member129 | `5a23834df647e325b1c18c3f4de116a854c4bee2da637e3ed59b0c9c47f2960e` |
| Preserved decompressed overlay14 | `ff77fa8057543c2ecc09dca097cdbf4825875d19afb870cfb771c7903d49f898` |
| Preserved root English ROM | `6fa7b4e739391ca9ea9bfcf90d83eec6407c3c04102e52432bb41bc8ae44a7d3` |
| Preserved RC7 ROM | `b16f81bec13b07730ee544fbe24aead4229eccf04368f186aa71abe0b48710df` |
| Preserved original battery | `b3aca10747cd0f1adc3d5852a50dddaaa36ed8680f5ba04012cfe3110faad90f` |

Private `pair_check.py` / `pair-summary.json` independently prove equal ROM size,
exactly four raw ROM bytes changed at136155049–136155052, only fileID132 changed,
only member17 changed within its NARC, and exactly offsets2549–2552 changed in
that member. ARM9/ARM7 and overlay tables are identical. Entire overlay14 and
member129 equal the prior verified build, preserving zero-PP Struggle and
Rock Tunnel repairs. Root/RC7/source battery hashes match the preceding stage.
`expected.toml` is left for the coordinator's final combined refresh.

## Built-ROM native loss and control

Private `fix/runtime.py` minimally adapts the successful reproduction runner:
`--fixed` validates the built displacement and expects native whiteout, while
disallowing the diagnostic RAM patch. It also guards result-store/helper code
and checks prebattle party extension sanity. The first native startup aborted134
inside the sandbox. The **exact same command** was rerun escalated and passed;
the host startup abort is unrelated to the game defect. One emulator ran.

Fresh boot/private battery, clock noon2026-10-09. The explicitly controlled
post-grunts loaded-object fixture enters155 with1155 clear, then models native
completion writes1155=true,0x40B7=1,1156=false,2006=false and native HidePerson4/7.
Object8 stays loaded until the real talk. This is not a completed natural grunts
adventure. Native generator output becomes the sole active Lv5 Magikarp, HP17,
Splash150/PP40, empty other move slots. Both prebattle and healed records are
closed flags0, checksum-valid, Lv5, with unchanged sane stats17/6/10/13/5/7.
No HP, battle result, task, battle argument or loaded-script write is used.
Strict snapshots reject transient records; none is repaired or interpreted.

`runtime-loss/result.json` passes with `diagnostic=false`, `fixed=true`,
`patch=null`. Complete loaded member bytes match the fixed ROM before tracing.
Native object8/script10 at648, messages33/34 and choice0 lead CallIf688→2519
and exactly one WildBattle219/Lv40. Ordinary FIGHT produces loss in16 iterations.
At frame6538 raw2/won0 is stored; at6539 GoToIf2546→3914, WhiteOut and native
task0x02051B3C execute. ReleaseAll3916 and End3918 follow at7953/7954.
At9672 field is restored at501 `(8,13)` and the valid Magikarp is healed17/17.
After closing native Nurse dialogue with B, DOWN moves to `(8,14)`.
The restored field screenshot was visually inspected.

Returning through native Warp to155 retains1155=true,1156=false,2006=false,
0x40B7=1 and has no native object8. Every observed progress snapshot retains
these values. No flag clearing manufactures a retry. `runtime-verified-summary.json`
independently asserts native interaction, loss/whiteout, strict party health and
extension validity, movement and preserved state. Post-End script-cursor values
are excluded: the original script context is freed after End, even if a reused
cursor happens to fall within member bounds. They are not field/script evidence.

Evidence hashes:

- `runtime-loss/result.json`: `f10f94f3f7af7fc24d74eea60400025dd9a81c2f130962ef716853cb8488dc10`.
- Exact runner used: `277643e62576634f562839796a3eb2a67ea6bb199ea97ac927eb506b6545b1d8`.

The accepted preceding CN/EN one-mon baseline failures remain the paired native
negative control; this stage's without build is hash-identical to that English
input. No redundant baseline runtime or broad optional journeys were added.

## Commands and limits

All commands run from repository root:

```sh
.venv/bin/python -m unittest work/tools/test_narcpatch.py work/tools/test_magcargo_loss_whiteout.py
.venv/bin/ruff check work/tools/test_magcargo_loss_whiteout.py
python3 work/tools/fixes.py check
python3 work/tools/fixes.py docs --out work/patches/FIXES.md
.venv/bin/python work/tools/build.py --armips /Users/contributor/Developer/armips/build/armips --work-dir work/build/bugfix-sequential-20261009/issue06/fix/without --without magcargo-loss-whiteout --no-regen-graphics --no-patch
.venv/bin/python work/tools/build.py --armips /Users/contributor/Developer/armips/build/armips --work-dir work/build/bugfix-sequential-20261009/issue06/fix/fixed --no-regen-graphics --no-patch > work/build/bugfix-sequential-20261009/issue06/fix/fixed-build.log 2>&1
.venv/bin/python work/build/bugfix-sequential-20261009/issue06/fix/pair_check.py
.venv/bin/python -u work/build/bugfix-sequential-20261009/issue06/fix/runtime.py --rom work/build/bugfix-sequential-20261009/issue06/fix/fixed/origin_hg_v4.0.3_en_wip.nds --out work/build/bugfix-sequential-20261009/issue06/fix/runtime-loss --controlled --single --fixed
```

Limits are explicit: one DeSmuME native backend, a controlled valid fixture,
not a full story playthrough or hardware/melonDS run. Decline/reload behavior,
knockout/capture/flee continuation and draw recovery are structurally/engine
verified; these outcomes were not separately run in this stage. No new text,
reward, capture persistence or optional victory runtime claim. Root/RC7 ROMs,
source battery and unrelated dirty work are preserved. D-2306 was added only
through `decisions.py`; no other decision was edited or resolved.
