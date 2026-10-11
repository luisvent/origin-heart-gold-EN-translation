# Lugia appearance freeze — 2026-10-09

**Reproduced in melonDS 1.1. Follow-up: D-2297 is fixed by the user-approved
D-2298 change; see [fix and verification](lugia_freeze_fix_20261009.md).**

The sections below preserve the initial investigation, before that follow-up.

The reported picture is the first Lawrence encounter in Whirl Islands, after his battle and immediately before Lugia appears. This is a different failure from the Rocket HQ texture-frame data abort (D-2043 / D-2083). Enabling that existing fix does not prevent this freeze.

## Normal-control reproduction

- Input: the supplied `Pokemon - HeartGold Version (USA)-patched.sav`, SHA-256 `6dcb4b9acd82a7dc349e3d7432445fb10f2c9d9dd52d51f08c86b9dd5f86f04d`. The input file was checked unchanged after testing.
- Emulator: the existing headless melonDS 1.1 core, commit `b86390e4428bf38ce4c1ce0e9ca446d6d25955e8`, interpreter, software renderer, built-in BIOS, DS direct boot; RTC initially 2026-10-09 12:00.
- ROM: existing `work/build/lugia-freeze/control.nds`, SHA-256 `502c2e33fdec6e77b5b7f70cca30ad291736184d1f0efcbcb4c20b9d38017ea6`. This is the English development build without `overworld-texture-frame-bounds`; it retains the other fixes, including the Bulbasaur reflection fix. It is not the released rc5 ROM.
- Continue starts at map 244, (16,38). Walk north to start the scene. Win the Rocket double battle (903/904), advance the dialogue, then defeat Lawrence (997). This run used the supplied party and ordinary keys/touch input, with a melonDS checkpoint reload during the first battle. No party, event, script or code edits were used in this reproduction.
- Advance Lawrence's final reply, then dismiss Lugia's cry. The picture stops at map 244, (18,27), matching the attached report. A further 726 frames including A/B input leave the screenshot byte-identical.

Observed ARM9 state: CPSR `0x00000097`, PC `0xFFFF0108`, one **prefetch abort**, zero data aborts and zero undefined instructions. The core log is `ARM9: prefetch abort (00001004)`. R3 is `0x1000`. The underlying bad branch/callback and its cause have not been established.

**Do not interpret the harness's `fault_pc` here as the offending instruction.** `Harness.arm9_abort()` computes LR minus eight for data aborts; this event is a prefetch abort. The raw registers, banked registers and melonDS log are retained for investigation.

## Existing-fix comparison

The existing `develop.nds` and `control.nds` files differ in exactly one byte: ROM offset `0x2867C`, mapped to ARM9 `0x0202467C`, `08` versus `2C`. Development SHA-256: `d5442d367ebfa552d4cc4e6a014350fda426e310a7180f2a41151dafc9d1aed7`.

Replayed the checkpoint immediately before dismissing Lugia's cry on each ROM. Because savestates carry ARM9 RAM, the test explicitly synchronized that one RAM branch to the ROM being tested (`0xD208` original / `0xD22C` guard). **Both abort after 226 frames with identical CPU registers and the same prefetch-abort signature.** This is an isolated guard comparison, not a separate fresh development playthrough.

The Lugia event script (a/0/1/2 member 104) is byte-identical in the untouched Chinese ROM and both English builds: SHA-256 `df4d62fcd84657d7d1d54c4d512c757d89e0e8c4065751815adc4f9527c12a49`. The relevant sequence is Lawrence's battle at offset 881, messages 14–16, Lugia's cry/message 6 at 995–1006, then `ScrCmd_459` at 1008. Script identity alone does not establish whether the crash originates in the Chinese hack.

## Local evidence and retry

All game-bearing evidence is ignored under `work/build/lugia-repro-20261009/`:

- `session/control-resume/articuno_end.ml1`: Lawrence defeated, final reply displayed.
- `session/control-resume/after_lawrence_line.ml1`: Lugia's cry displayed, immediately before failure.
- `session/control-resume/lugia_appearance.ml1` and `.png`: original crash.
- `session/control-resume/freeze_confirmed.png`: identical picture after further input/time.
- `session/control-retry/report.json` and `session/develop-guard/report.json`: both isolated replays, raw registers and logs.
- `session/compare.py`: repeat the guard comparison from the pre-crash checkpoint, using `.venv/bin/python work/build/lugia-repro-20261009/session/compare.py` from the repository root.
- `roms.json`: input ROM hashes, branch bytes and script hashes.

At the end of the initial investigation the Chinese runtime comparison was untested:
the diagnostic had been canceled while waiting for an emulator slot. The follow-up
has now run that fresh-boot diagnostic and reproduced the same callback prefetch
abort in the original Chinese ROM. See the linked fix report for the method and
its battle-bypass limitation.

No ROM was built or fix implemented in the initial investigation. The follow-up
implements and verifies a local build; nothing was downloaded, committed or published.
