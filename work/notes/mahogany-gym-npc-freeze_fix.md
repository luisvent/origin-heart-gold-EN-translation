# Discord #bugs "After beating mahagony gym Bug" (2026-10-12): not reproduced, no fix

Reporter's save (DeSmuME-format .dsv, really a raw 512 KB battery save, SHA-256 7beef7a6...eca): map 247 (Team Rocket HQ B1F) at (13,4), lead follower Charizard, badges 0-13 set, badge 14 (Mahogany/Glacier, the final gym of this hack's order, Pryce needs the League Champion) NOT set, var 16555 = 7 (HQ camera ambush not yet fought). So the save is in Rocket HQ before the camera ambush; it is not at the gym.

## What was tried (fresh develop build e98854f, rc7 build, Chinese ROM; melonDS 1.1 and DeSmuME)
- melonDS, walk east from (13,4): Chinese ROM aborts at (16/17,4), fault 0x02024696 (the known Rocket HQ texture-frame NULL, D-2043). develop and rc7 reach (23,4), the ambush battle starts and is won (var 16555 -> 8), no abort.
- Talking to the "guy" at (23,3) (obj 5, sprite 287, a Persian statue, script 6, "Its eyes are glowing red") before and after the ambush: works on develop and rc7 (melonDS). Talking to every other scripted HQ B1F object (objs 14, 15, 25, 37, all four sides): no abort, develop, melonDS.
- Mahogany gym (map 140), DeSmuME with badge 14 set: Haze tutor girl (flow to party select, "can't learn Haze"), Pryce menu and the Singles battle: all work. Pryce "photo" path (CameronPhoto) and the melonDS gym run were not completed (menu selection by key did not reach it; machine was contended).

## Conclusion
The only freeze this save produces is the already fixed Rocket HQ texture-frame NULL (fix overworld-texture-frame-bounds, in rc7). The reporter is probably on rc5/rc6 or an emulator build that still hits it; ask which version. The "gym" wording does not match the save. No code or data change made.

## Questions for Shishio
1. Which release did the reporter patch with? Can they send the screenshot (which NPC)?
2. If they are on rc7+: the remaining untested candidates are Pryce's photo option (CameronPhoto) and the Haze teach path (PokemonSummaryScreen/GetMoveSelection) on melonDS with badge 14 set.
