# Ruins of Alph Kabuto chamber approach — 2026-10-10

The reported IMG_1504.png shows the player west of the Kabuto chamber approach, approximately map 113 (433,268). The green patch immediately east is solid terrain, not traversable tall grass. No fix is needed: enter from the east by walking around the southern ruin.

Read-only comparison of the untouched CN ROM and `work/build/origin_hg_v4.0.3_en_wip.nds` found identical collision around the approach. Tile (434,268) is blocked in both, as is the north–south band at x434 around this ruin. Exterior event member110 and matrix member0 are also byte-identical. The door warp at (436,266) leads to map312, the Kabuto chamber.

Verified in the English ROM with a disposable copy of the harness seed save, a normal scripted warp to (433,268), then actual walking through these waypoints:

`(432,268) → (432,278) → (438,278) → (439,274) → (441,272) → (441,269) → (438,269) → (436,267) → UP`

Every waypoint returned successful arrival. The last step entered map312 at (6,17). The initial southbound route along x433 hit the NPC at (433,276); stepping west first avoids them. A direct save teleport also used the wrong outdoor height, so that attempt is not evidence of blocked access.

Evidence: `work/build/alph-door-report-20261010/route.py` and `route/*.png`. The reporter's save/build was not supplied; the runtime check used the local English build. CN parity is from static map data, not a second runtime walkthrough. No ROM, production script, translation, or user save was changed.

Player directions: go south around the large ruin below the character, turn east below it, then head north along its eastern side and west into the doorway approach. If Silver is absent inside, the story requires talking to the Research Center assistant, then asking both Gold and Crystal about Molly (guide/08-cherrygrove-to-azalea.md).
