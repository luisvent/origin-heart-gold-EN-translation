# forest-of-time-sammy-guard: fix notes (2026-10-12)

**Status: disabled** (`enabled = false`). Reviewed by a separate reviewer (approved with notes); merged into develop on 2026-10-12 as a separate, switched-off patch by the user's decision. The standard build keeps the Chinese behaviour; build it with `build.py --only forest-of-time-sammy-guard`. A tester xdelta (rc7 plus this fix) is available on request. Cause, emulator evidence and what is not verified: work/notes/shared-progress-losses_investigation.md (D-1581 section). Finding D-1581 (open), D-1429.

Reviewer's notes (kept, not fixed): the ranger's talk script (@616/@635 of file 92) checks only 0x40A2 == 17 and flag 2110, not 0x4099, so a player in the middle of the hunt who talks to the ranger gets flag 2105 set and 0x4099 rewritten to 3, which the guard then lets through. That is out of scope for this fix and untested. The "pixel-identical over 84 frames" claim below was only partly reproduced by the reviewer: 2 of 3 sample frames matched, the third differed by 11x20 px of ambient sprite animation.

## Change

work/patches/forest-of-time-sammy-guard/fix.toml, two `[[script_insert]]` in a/0/1/2 member 52 (member SHA-1
d8049a08..., 7666 bytes), each in front of a scene's first command (`ScrCmd_609` at 34 = script 1, the Sammy arrival scene;
at 437 = script 3, the Marauder scene; guard bytes `61 02 60 00`):

```
CheckFlag 2105          20 00 39 08
GoToIf set -> +2        1C 00 01 02 00 00 00      flag set (the Sammy chapter is active): skip the End
End                     02 00
ScrCmd_609 / LockAll ... the old script, unchanged
```

Flag 2105 is the Sammy chapter's own "active" flag. The ranger's scene (file 92 @5364) sets it directly before
`HidePerson 17`, `SetVar 0x4099 = 3` (@5372, the only genuine start) and `ClearFlag 1120`; only the finale (file 52 @2401) clears
it; a scan of every script member finds no other SetFlag/ClearFlag of it, and its only other use is the ranger's own hide flag
in Ilex Forest (event 114 object 17). So in the real chapter both scenes run exactly as before; in the bug hunt (2105 clear)
they end at once with nothing shown or written. Nothing is removed, no content or text is added. Member grows by 26 bytes
(+ up to 3 zero bytes keeping its movement blocks 4-aligned); both header slots land on the inserted CheckFlag.

Not changed on purpose: the maze copy of Ilex Forest (file 106) that bounces you back at 0x4099 = 2 and 4 (harmless: the
way back is the entrance clearing); the hunt's own writes; no new variable, no migration. A save already damaged
(0x4099 = 6 from the early Marauder scene, or 4 where the hunt wanted 3) is not repaired: a 6 is also the legitimate end of
the Sammy chapter, so the two cannot be told apart.

## Verified

* work/tools/test_forest_of_time_sammy_guard.py (5 tests, no emulator): only member 52 changes and grows by 26..29; both entries
  and the inserted CheckFlag 2105 / GoToIf (condition 1, target the old first command) / End decode; the rest of the member
  decodes identically; flag 2105 has exactly one SetFlag (92 @5364, directly followed by HidePerson 17, SetVar 0x4099 3,
  ClearFlag 1120) and one ClearFlag (52 @2401); guards reject a changed member.
* Emulator (DeSmuME), rc7 plus the fix against rc7 and the Chinese ROM, states forced (flag 2105 clear, 1120 set):
  0x4099 = 3 at (16,81): scene gone, stays 3 (it goes to 4 on the Chinese ROM and rc7); 0x4099 = 5 at (15,38): scene gone,
  stays 5 (6 and flag 2110 on the others). Genuine chapter (2105 set, 1120 clear): 0x4099 = 3 arrival scene, 84 screenshots
  pixel-identical to rc7; 0x4099 = 5 Marauder scene with both battles forced to a win, same end state (6, 2105 clear, 2110
  set) in the same number of loop frames.

## Not verified

* A natural play-through (a real hunt to 5, then the Forest, then Bugsy); Bugsy's closing talk on the fixed ROM (it is the
  unchanged script @2879 at 0x4099 = 5, which the fix leaves at 5); the Sammy chapter beyond the two scenes on the fixed ROM;
  melonDS / hardware; text fit (no text change).
* Whether a player in the hunt at 5 can walk the maze in natural play: the maze copy's trigger only bounces at 2 and 4
  (parsed event selection, offline), not walked in the emulator.

## Reviewer: look hardest at

1. That 2105 is set at both scenes in every legitimate path (the ranger scene is the only start: file 92 @5364/5372), including
   an old save made between the ranger scene and the finale.
2. A End before `LockAll` (the guard runs before any lock) and the GoToIf condition code 1 (jump when the flag IS set).
3. The 4-alignment padding of member 52's movement blocks after two inserts (decode test and the emulator scenes cover it).
