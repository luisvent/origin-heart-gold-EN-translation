# Issue 5 — Rock Tunnel corner-child defeat repair, 2026-10-09

Scoped D-1548 repair under user authorization **D-2300**; technical choice
**D-2305**. Native CN and English reproduction and the branch-only diagnostic
are recorded in the investigation/reproduction notes. No downloads, commits,
publishing, source battery edits, or root/RC7 ROM replacement.

## Critical choice and exact change

Choose **ordinary native whiteout**, matching seven other defeat branches in
this map script. Do not change the allowed-loss battle argument, heal in place,
force victory or complete either child on defeat.

Enabled `work/patches/rock-tunnel-corner-loss/fix.toml` uses the existing
`kind = "narc"` stage. It guards the entire 6030-byte source member SHA-1
`c73334fd0e00250cad1b66fc2b929931374bdca4`, then changes only offset2900
(0xB54) in `a/0/1/2` member129: raw `6e030000` → `56ffffff`.
The equality branch at2897 targets existing WhiteOut2734, ReleaseAll2736,
End2738 rather than another child's dialogue3782. Trainer606 arguments
`606,0,0,0`, CheckBattleWon, message76, flag1966, retry and reward logic stay
byte-identical. There is no engine, text, save, asset or header-entry edit.

## Paired builds and preservation

Full current-tree builds used local armips0.11.0, existing banks and graphics,
`--no-regen-graphics --no-patch`. Both build verifications passed (text/NARC
round trips, export equality, graphics, glyphs, hardcoded code and text speed).
Outputs are isolated under ignored
`work/build/bugfix-sequential-20261009/issue05/fix/{without,fixed}/`.

| Artifact | SHA-256 |
|---|---|
| Unfixed current tree (`--without rock-tunnel-corner-loss`) | `93514313cba83acbb3f6b870fddfc9b111d62ad20b763a0670e4dd67ab074668` |
| Fixed current tree | `7f85c44d5416ce87e2b9afb37b535899cef1b048ded0098079abe88c30db218d` |
| Fixed member129 | `5a23834df647e325b1c18c3f4de116a854c4bee2da637e3ed59b0c9c47f2960e` |
| Preserved root English ROM | `6fa7b4e739391ca9ea9bfcf90d83eec6407c3c04102e52432bb41bc8ae44a7d3` |
| Preserved RC7 ROM | `b16f81bec13b07730ee544fbe24aead4229eccf04368f186aa71abe0b48710df` |
| Original source battery | `b3aca10747cd0f1adc3d5852a50dddaaa36ed8680f5ba04012cfe3110faad90f` |

Independent `fix/pair-summary.json` proves only ROM file ID132 changes, only
member129 changes inside it, only bytes2900–2903 differ, and member length stays
6030. The entire decompressed overlay14 is identical between builds, and the
previous issue03 Struggle guard is identical to its verified build. The unfixed
ROM is exactly the earlier issue03-fixed ROM by hash.

## Host verification

`work/tools/test_rock_tunnel_corner_loss.py` passes three tests against the local
Chinese ROM: only the branch changes in the full reachable disassembly with
unchanged entries and instruction set; changed source bytes at five locations
are rejected before any write; and the four-byte guard rejects independently
when a deliberately changed fixture's whole-member hash is made to match.
Tests also verify native trainer arguments, WhiteOut/ReleaseAll/End, unchanged
victory flag1966, unchanged reward region and exactly one additional loss branch
to2734. The combined NARC-stage and focused suite passes12 tests. Ruff passes.
`fixes.py check` passes; `FIXES.md` regenerated through the registry tool.

## Runtime method and verification

`work/tools/emu_rock_tunnel.py` is a focused durable runner adapted from the
successful reproduction recipe. One freshly booted DeSmuME at a time, private
battery copy, clock noon2026-10-09. All five completion/reward flags are explicit:
1966 and1868 false, other children's1554/1884/1885 true. TM407 is removed from
only the private battery bag fixture for reward quantity comparisons.

Loss uses six private RAM copies of a strictly valid native-generated Lv5
Magikarp (HP17, Splash150/PP40), ordinary FIGHT selection and forced switches.
Win uses a native-generated Lv100 Mewtwo with Psychic94/PP40. These are controlled
fixtures, not a full unmodified story journey. Native real object17/script18
starts trainer606; no substituted script, branch RAM edit, battle result/HP write
or allowed-loss change is used. Reward controls use native object13/script8.

Strict snapshots read the whole party at one paused boundary, decode each record
with `diagnostic=False`, and verify raw bytes remain stable. This rejects nonzero
native open/decrypted flags as well as bad checksums. Rejected transient records
are reported as unavailable and never repaired, saved or treated as HP evidence.
A bounded300-frame search obtains a fully closed snapshot for healing assertions.

The first native startup aborted134 inside the sandbox. The same command was
rerun with required escalation. The first gameplay runner attempt failed the
command-menu recognizer after reaching the native battle handler; its prebattle
button sequence accidentally used B instead of the reproduction recipe's A.
That attempt is a harness failure, not a passing game result. The sequence was
corrected and later runs keep explicit failure screenshots/events.

### Built native loss and paired control

Fixed `runtime-loss2/result.json` passes: real script18/native606 defeat produces
raw result2/won0 at frame9686; GoToIf2897 targets2734 at9687; native WhiteOut
handler and task both execute. Field returns to map501 `(8,13)`. At frame12331
all six records are closed (flags0), checksum-valid and healed17/17 with PP40.
Ordinary DOWN moves to `(8,14)`. All flags retain `1966=false,1554=true,
1884=true,1885=true,1868=false`. Money is3650, unchanged in this seed; no monetary
behavior was overridden. A new real object17 interaction starts trainer606 at
frame12925, on the actual built fixed script. The retry's second defeat is not
run. The restored Pokémon Center screenshot was visually inspected.

Paired `runtime-without/result.json` passes the expected-failure oracle: raw
result2/won0 at9752, GoToIf2897→3782 at9753, no WhiteOut, unchanged five flags,
strictly closed six-member HP0 snapshot, black non-field state still in
map342 `(43,99)` after the fixed2640-frame observation window. The console emits
`ARM9: Undefined instruction: 0x27110010 PC=0x022A225C`; a broad RAM PC range is
not the failure oracle. Source battery hash matches after both runs.

The first fixed report also retained a meaningless negative cursor after native
whiteout freed the original script context. That value is excluded from all
claims. The final runner retains script cursors only while pointing into this
member; it never treats freed context bytes as script evidence. The final
frame12330 party sample is unavailable due checksum mismatch; the neighboring
strict closed snapshot at12331 supplies the healing evidence. No transient
record was repaired or interpreted.

### Victory assertions and explicit verification limit

The first native victory run completed the actual trainer606 battle at frame12513,
passed native won1, field-return, message76, SetFlag1966, unchanged other-flags,
no-WhiteOut and already-won real-talk/no-new-battle assertions. The runner then
attempted an optional reward warp while a message window remained open and
stopped with `A press did not reach the field talk handler`. That run wrote
`runtime-win/after.png` and the same-ROM private `after.dst`, but its final JSON
was written only at the end, so **there is no complete durable victory JSON**.
The earlier completed assertions and saved artifacts are limited evidence, not
an independently rechecked passing victory report. No reward grant or duplicate
runtime behavior is claimed.

The final runner removes every optional reward followup and retains the original
bag. Its fresh core-only rerun stopped **before scene interaction**: no strictly
closed/checksum-valid whole-party snapshot appeared within the bounded300 frames
after native generator/swap setup. It refused the fixture, repaired no record,
and did not use transient data as evidence. This is a fixture-validation refusal,
not proof of a game corruption or a scene regression. Per coordinator direction,
no more runtime recovery or fixture debugging was performed.

Victory/reward behavior is additionally proved unchanged structurally: the only
changed command is the won==0 branch target. The win continuation at2904–2917,
post-win flag1966 reader/dialogue, and entire script8 reward region remain
byte-identical. Native checks1554/1966/1884/1885, duplicate guard1868, rewarditem407
and SetFlag1868 are unchanged. The preliminary missing-corner reward gate passed
in the first win attempt, but no complete reward runtime report is claimed.

### Evidence identities and commands

- `runtime-loss2/result.json`: SHA-256 `90e88932a7c04ca66c7cd28f1f63c81364e8c93c4728f3250bfee80496826bb2`.
- `runtime-without/result.json`: SHA-256 `2f3c517f86a06b9c3f5b11a31cf11537b343ce4139708d734e215b6cf13966e3`.
- `work/build/bugfix-sequential-20261009/issue05/fix/runtime-win/after.png`: SHA-256 `c2a1e79aca86a3f56ad0c79899bbc3f6df5129d86279a740a75ac3758e96939d` (incomplete-run artifact).
- `work/build/bugfix-sequential-20261009/issue05/fix/runtime-win/after.dst`: SHA-256 `365a8c7b26a1cad894f8b6d30f8ad233cdab07d4baba73b1040f1cb5f93e2659` (incomplete-run artifact).
- Final durable runner: SHA-256 `eaef34de69a174b4426af7f784e0aeacd167eeb7cfdee781af065d824aba7ffc`.

`fix/runtime-verified-summary.json` independently checks the two complete passing
reports and strict closed healed/defeated snapshots, and explicitly records
victory limits. Exact commands run from repo root (native emulator escalated):

```sh
.venv/bin/python work/tools/build.py --armips /Users/contributor/Developer/armips/build/armips --work-dir work/build/bugfix-sequential-20261009/issue05/fix/without --without rock-tunnel-corner-loss --no-regen-graphics --no-patch
.venv/bin/python work/tools/build.py --armips /Users/contributor/Developer/armips/build/armips --work-dir work/build/bugfix-sequential-20261009/issue05/fix/fixed --no-regen-graphics --no-patch
.venv/bin/python -m unittest work/tools/test_narcpatch.py work/tools/test_rock_tunnel_corner_loss.py
.venv/bin/python -u work/tools/emu_rock_tunnel.py --rom work/build/bugfix-sequential-20261009/issue05/fix/fixed/origin_hg_v4.0.3_en_wip.nds --out work/build/bugfix-sequential-20261009/issue05/fix/runtime-loss2
.venv/bin/python -u work/tools/emu_rock_tunnel.py --rom work/build/bugfix-sequential-20261009/issue05/fix/without/origin_hg_v4.0.3_en_wip.nds --out work/build/bugfix-sequential-20261009/issue05/fix/runtime-without --without
.venv/bin/python -u work/tools/emu_rock_tunnel.py --rom work/build/bugfix-sequential-20261009/issue05/fix/fixed/origin_hg_v4.0.3_en_wip.nds --out work/build/bugfix-sequential-20261009/issue05/fix/runtime-win --win
.venv/bin/python -u work/tools/emu_rock_tunnel.py --rom work/build/bugfix-sequential-20261009/issue05/fix/fixed/origin_hg_v4.0.3_en_wip.nds --out work/build/bugfix-sequential-20261009/issue05/fix/runtime-win-core --win
```

Final runner changes after complete loss/control reports remove optional reward
fixtures/followups and discard out-of-member freed-context cursors. Loss party
validation, native interaction, battle loop and loss/retry assertions are intact.
Native fixture generation uses random individual values; the paired weak records
are not identical, but both have legitimate HP17, Splash/PP40 and count6.

Limits: controlled fixtures, not a full unmodified story playthrough; one native
DeSmuME backend, no hardware/melonDS run; money3650 in this seed; no complete
durable victory JSON, and reward grant/duplicate are structurally preserved,
not verified through a complete runtime claim. Root ROM, RC7 and original battery
remain byte-identical. `expected.toml` is left for the coordinator's final combined
sequential build refresh; both isolated builds passed full build verification.
No unrelated dirty work changed, no downloads/commits/publication.

Production additions: `rock-tunnel-corner-loss/fix.toml`, `emu_rock_tunnel.py`,
`test_rock_tunnel_corner_loss.py`, and this note. `FIXES.md` regenerated; technical
D-2305 appended through the decision CLI. Core four-byte loss repair is verified;
coordinator requested stopping runtime after the documented fixture refusal.
