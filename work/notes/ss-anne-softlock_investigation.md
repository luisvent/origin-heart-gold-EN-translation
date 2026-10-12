# S.S. Anne party softlock: investigation (2026-10-12, agent ss-anne-softlock)

Verdict: **REPRODUCED** (natural play path, real boarding and real NPC walk-ups; only positioning uses the harness warp).
Fix: `ss-anne-softlock` (`work/notes/ss-anne-softlock_fix.md`). Register: D-1549 (resolved earlier, same finding), D-2348.
The "superseded by later emulator findings" wording in the notes refers to D-1549's own settled answer (2026-10-06), which
replaced the earlier guess that the Captain starts the party; nothing in the notes says the trap is not real.

## Method

The one-off recipe `emu_vqueue.py ssanne_story` was removed from develop (2e6fe55); restored from git 2e6fe55^ into a scratch
copy of the tools (`<scratch>`, `oldrepo2` with extra variants), run individually (py-desmume, one case per run):

    EMU_HARNESS_DATA=$PWD/work .venv/bin/python $S/oldrepo/work/tools/emu_harness.py vqueue --case ssanne_story \
        --lang cn|en [--rom-cn|--rom-en ROM] --out DIR

State before boarding: the Vermilion arrival flags/vars (as file 774 @1227-@1267 sets them), every S.S. Anne flag and var
at its new-game value, $3,000, no HM01/Salt/Honey, a Lv 100 lead so battles are won. Real boarding (zone 387 sailor,
file 155 script 1, ScrCmd_723), arrival scene, Captain's speech (156 coord script 5), then NPCs reached by walking up and
pressing A. A write watch on the byte of flag 1440 runs throughout. Forced state: the arrival flags/vars and the Honey in
the Bag (kitchen source not walked); everything else is play-path.

## Result on the untouched Chinese ROM (sha256 4807ab2c...95c8) and rc7 (same member bytes) and a built control

| order after the Captain's speech | outcome |
|---|---|
| old boy battle, then girl with Honey | **party starts** (announcement 255#18, Water Stone, var 0x40A4 = 3, Archie's hall speech) |
| Honey to the girl first (then Captain / old boy / grandfather / Blue in any order) | **stuck**: 1423 set, 1424 later set by the old boy, nothing re-checks; no announcement, hall trigger silent, gangway sailor (object 1, 24,17) never moves |
| Blue first (then old boy, girl, grandfather, Captain) | **stuck** (his party branch sets 1423 before battling) |
| Captain first | Captain: 253#62 'the party's already started', no HM01, sets nothing; harmless on its own |

Same on CN, rc7 (run3) and the English control build (run8). Hall guests (14 objects, hide flag 1440) are visible from boarding.
Evidence: `$S/run2` (CN), `run3` (rc7), `run8` (EN control build with font-glyphs only); screenshots in `<run>/verifyqueue/<en|cn>/`
(`honey_first_exit.png`: player at the gangway, sailor in the way, hall guests on screen; `honey_first_hall.png`).
Not natural: none of the traps needs forced flags; leaving the ship before the party is impossible (sailor object 1 hides
only when the hijack scene starts, 156 @2937).

## Cause (scripts)

Flag 1440 = hide flag of the 14 party guests and the hall shop (events bank 278, objects 11, 12, 24, 29, 30, 35-40, 42-44).
The scripts are written for a voyage that starts with 1440 SET: Captain 157 script 5 (@124 CheckFlag 1440, GoToIf [0] =
'party already started'), old boy 156 L4604, Blue 156 L4502, Archie 156 script 17, the guests; the party start clears it
(157 @550, 161 @1901). Every script file: the only SetFlag 1440 is the hijack (156 @6350); no init (member 842), no
Vermilion arrival and not the harbor sailor (155 sets 554/555, clears 235/556) sets it. So the voyage always runs in the
'party already started' state; the party is announced only inside the Honey hand-over (161 @1524, needs 1424) or the Captain's
speech (157 @514). Honey first / Blue first leaves 1423 set and 1424 clear and nothing re-checks. In the intended state the Captain
sets 1424 and gives HM01, the Honey sets 1423, and whichever comes second announces the party.
Corroboration: the new captain (157 script 6) has a has-HM01 branch; flags 1439 (Blue/old boy hall copies, cleared at the speech) is
likewise never set (cosmetic: Blue and the old boy are in the hall from boarding).

## Not verified

The hijack/Team Rocket scenes after the party with the fix; a save already stuck cannot be rescued by this fix (it acts at
boarding); hardware. Whether the author wants the first-voyage HM01 (the guide says Cut isn't needed): flagged as a judgment.
