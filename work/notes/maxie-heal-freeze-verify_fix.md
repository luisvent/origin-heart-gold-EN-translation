# Maxie gauntlet Potion freeze: verification (2026-10-12)

Discord #bugs, atano0506, 2026-10-07: "Game freeze when healing in Maxie battle. Maybe during speed up too?" (second wave
of Maxie's double battle, Potion on Marshtomp froze the game; an earlier save with speed-up froze there too).
**Verdict: already fixed on develop; no new fix needed.** Reproduced on melonDS without the fix, passes with it, with
and without the TEXT SPEED FAST option.

## Is the fix on develop?
Yes: `work/patches/battle-heal-hpbar-switched-out` (enabled, D-2314; developed as 2e448a1 on fix/melonds-retest, landed
with `e277d77` "Prepare RC7"). It is part of v1.0.0-rc7 (2026-10-11). The report (2026-10-07) predates it, so the
reporter was on rc6 or earlier. `work/notes/melonds-retest_fix.md` has the root cause: the Potion's playback finds the
healed Pokemon's battler after the whole turn; Houndoom's Roar has dragged it out, the lookup gives 5, health bar 0
(never set up in doubles) has a NULL sprite, data abort at 0x02210C9E on melonDS/hardware (DeSmuME reads address 0).

## Runs (develop e21ab4b)
Builds: `build.py --no-patch` (with the fix, SHA-1 7ebeaee8...) and `--without battle-heal-hpbar-switched-out`
(3d32dc1d...). Test copies with the Maxie triggers of script file 17 repointed (as in melonds-retest_fix.md): wave 2
with Green, party Marshtomp Lv100 (lead, half HP) / Blissey / Snorlax / Clefairy / Marshtomp Lv60 written into RAM after
Continue, Potions in the bag, Potion on the lead on turn 1. The option TEXT SPEED is set in the Options word (save array
1, bits 2-3: 0 NORMAL, 1 FAST) before the battle and again before the Potion; "speed-up" means that option. Emulator
fast-forward changes no emulated timing; the 0/10/20-frame start offsets vary the timing instead. Natural Roar in every
run (the fixed build's screen after the turn shows the lead replaced by Clefairy).

| Emulator | ROM | NORMAL | FAST |
|---|---|---|---|
| melonDS 1.1 | develop without the fix | abort 3/3 (fault 0x02210C9E) | abort 3/3 |
| melonDS 1.1 | develop with the fix | menu 3/3 | menu 3/3 |
| melonDS 1.1 | Chinese ROM (v4.0.3) | abort 3/3 | abort 3/3 |
| DeSmuME | without / with the fix | menu (no freeze, reads address 0) | menu |

(the DeSmuME 10-frame-offset trials were still running at writing; the 0-frame trials are in the table.)
Setup scripts are session scratch, not committed; the standing regression test is
`emu_harness.py fixes --case battle-heal-hpbar-switched-out` (emu_battle_heal.py).

## Speed-up
No separate cause: FAST changes only how many letters print per frame; the Potion/Roar turn is computed by the battle
engine before playback and the freeze comes from the playback of the healing event. Both settings freeze without the
fix and pass with it.

## For Shishio
- Reply to the reporter: fixed in rc7 (Roar dragging the healed Pokemon out was the trigger); on rc6 avoid Potions in wave 2.
- Real hardware is untested (same as D-2314).
