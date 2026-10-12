# route3-misty-actors: fix notes (2026-10-12)

Cause and evidence: work/notes/giovanni-hotspring-and-route3_investigation.md, section 2. Decisions D-2346 (finding,
resolved), D-2347 (fix). Cosmetic: the scene finishes either way; without the fix it is played with an empty field.

## Change

work/patches/route3-misty-actors/fix.toml, one `[[script_insert]]` in a/0/1/2 member 175 (member SHA-1 551b5d1d...)
in front of script 17's first command (PlaySE 1500 at 1171, guard bytes `49 00 DC 05`):

```
CheckFlag 1303          20 00 17 05
GoToIf < +16            1C 00 00 10 00 00 00      flag NOT set: skip the reveal (the normal case)
ClearFlag 1303          1F 00 17 05
ShowPerson 28           64 00 1C 00               the Gyarados
ShowPerson 9            64 00 09 00               Misty
ShowPerson 8            64 00 08 00               Misty's second object
PlaySE 1500 ...         the old script, unchanged
```

Objects 8, 9, 28 have hide flag 1303 (event data of zone 11); the script's own movements, cries, messages and
HidePerson then act on visible objects. With the flag clear nothing changes (byte-identical decode apart from the
inserted block). Script 17's header slot now points at the inserted CheckFlag. The scene sets 1303 again at its end
(L3486 / L4139), as before. The member grows by 27 bytes (+1 zero byte for the movement-block alignment).

Tool change: the same `scriptinsert.check_block` extension as fix/giovanni-hotspring-loss (a jump inside the inserted
block); the two files are identical in both branches so the merge is clean.

## Verified

* Unit tests (work/tools/test_route3_misty_actors.py, no emulator): only member 175 changes; entry and prefix decode as
  above; the rest of the script decodes identically; objects 8, 9, 28 have flag 1303 in the events; guards reject a
  changed member.
* Emulator (DeSmuME), forced state flag 1303 set + var 0x4086 = 0 (the state between the Viridian Blue scene and the
  forest scene), warp to 1147,121 and walk RIGHT onto the trigger, party of one Splash Magikarp (the Gyarados battle
  allows a loss): Chinese ROM and rc7 show an empty field; rc7 + this fix shows Misty and the Gyarados (screenshots
  montage compared by eye: m-r3-fix-set.png against m-r3-cn-set2.png); with flag 1303 clear (control) the fixed build
  plays the scene as the unfixed one does, ending with var 0x4086 = 1 and flag 1303 set.

## Not verified

* A full play-through that skips Misty in Viridian Forest; the reachability is argued from the scripts and from the
  map grid (the shortest path through the forest is the same 159 steps with Misty's tiles blocked).
* melonDS / hardware; text fit is not involved (no text changes).
* Where the actors stand after the reveal is the objects' initial position (as with the flag clear); not compared
  pixel by pixel with a flag-clear map load.

## Reviewer: look hardest at

1. The `check_block` rule (same code as the Giovanni branch).
2. That ClearFlag 1303 has no other effect: the readers of flag 1303 in script data are only the object hide flags of
   Route 3 objects 8, 9, 28 (other numeric hits of 1303 in a scan of all members are jump or movement operands).
3. Condition code 0 of the GoToIf (jump when the flag is not set), as scriptdump documents for CheckFlag + GoToIf.
