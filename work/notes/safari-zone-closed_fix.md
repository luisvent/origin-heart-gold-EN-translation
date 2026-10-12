# Safari Zone closed (option A, user decision 2026-10-12)

2026-10-12. Branch `fix/safari-zone-closed`. First stopped because closing the entrance makes Baoba's Geodude test impossible;
Shishio then chose option A (close everything), implemented in `work/patches/safari-zone-closed/` (D-2407).

## Entrance, as found in the untouched Chinese ROM

- Gate building = zone 173 (script file a/0/1/2 #119, message bank 133, events bank 167). Zone 174 is the outdoor
  Resort Zone (script file 116); it has no Safari entry script.
- Entry scripts in file 119: the three counters (script 1/object 0, script 2/object 2, script 5/object 4) end in
  `SafariZoneAction [0,0]`, `SetDynamicWarp [173,1,5,2,1]`, `Warp [357,0,79,100,0]` (also at offsets 2141-2173,
  2413-2445, 4155-4187; the Link counter variant 2923-2955 / 4761-4793 uses `SafariZoneAction [0,1]`).
  Script 7 (script 7 = the "leave?" trigger) warps out. The interior also has two plain door warps at (5,2) and
  (19,2) to map 357. Only file 119 warps to map 357.

## Why the Geodude test breaks

- Baoba (script 9, `SetVar 16471, 2`) and message 30/33 send the player into the Safari Zone to catch a Geodude.
  Script label L3652 then calls `CheckSafariZoneChallengeCompleted [0, var]` (command 791, handler
  ov3 0x0225B2E8). The handler walks the PARTY (save array 2, count at +4, 0xEC-byte entries from +8) and accepts a
  non-egg Pokémon of species 74 (Geodude; 27 Sandshrew for test 1) whose OT id is the player's and whose met
  location equals that of map 357, the Safari Zone. A Geodude caught anywhere else does not count, and it must be
  in the party when shown. (My first report said "caught-Pokémon store"; that was wrong, it is the party.)
- So with the entrance closed, 0x4057 stays at 2 forever: no second test (Sandshrew + Area Customizer), no
  Safari Owner state. Baoba keeps saying "hurry and catch me a Geodude, go inside the Safari Zone".
- Not affected: the Dragonair/medicine chain (file 211 sets 0x4057=1 only), the Dratini gift (flag 1202, script 11,
  independent of 0x4057), Fuchsia gym/badge (no reference to the Safari variables or flags).

## Facts that contradict the Discord description

The Safari Zone is not an empty shell in this ROM: it has a Safari battle setup (`work/notes/safari-double_fix.md`:
setup 0x20, RUN works), real area tables (pokedex_wild_gates.md: "Safari Zone base areas work"), the counter, the
Area Customizer and Baoba's two tests. Only Object Arrangement never unlocks (D-2296). The brief's "Rattata/Wobbuffet" is
the ordinary-map placeholder table (pokedex_wild_trade_audit.md), not the Safari area tables.

## Options (Shishio decides; nothing implemented)

A. Close it completely (counters + door warps show "closed"). Baoba's Geodude test then cannot be finished (needs a
   text change from Baoba to match, or he keeps asking). Costs the Area Customizer and the Safari-only encounters.
B. Close it except while the Geodude test (0x4057 = 2) or the Sandshrew test (= 5) is open: entry allowed only
   then, message otherwise. Keeps the quest finishable; the Zone is still enterable for those players.
C. Close it and make Baoba's tests unreachable at the source (Baoba stops offering them, 16471 stays 1). Removes the
   quest instead of leaving it dangling; needs a Baoba text decision (no invented content unless approved).
D. Close it and mark the Geodude test passed when it is offered (script change, invents progress).

The closed-message wording (hack tone) is not written yet; it would be decided together with the option.

## Implementation (2026-10-12)

`work/patches/safari-zone-closed/fix.toml`, kind narc, enabled, D-2407 (the notice) and D-2408 (open question about
Baoba's lines, see below):

- 4 `[[script_insert]]` in a/0/1/2 member 119: after FacePlayer of scripts 1, 2, 4, 5 the block
  `NPCMsg 46, WaitButton, CloseMsg, ReleaseAll, End` (11 bytes, relocated by scriptinsert.py). Nothing else in the member
  changes; the old paths after the block are dead code.
- 2 `[[narc_bytes]]` in a/0/3/2 member 167: the warp events (5,2) and (19,2) to map 357 move to (0,0).
- Message: the pipeline (ws.export) only exports the ids of the original bank, so a new id 115 is not possible.
  a027/0133#46 (the Object Arrangement line "Feel free to ask me any questions", not referenced by any script,
  and Object Arrangement never unlocks, D-2296) carries the notice instead: "I am very sorry! The Safari Zone is
  closed for now and is not available yet. We hope to reopen it in a later version. Thank you for your patience."
  (its zh is unchanged and no longer matches; recorded in the string's notes).
- Door tiles: they are in a staff area (static collision: no path from the entrance to (5,4)/(19,4)); the harness
  places the player there and steps on them. Moving the warps costs nothing and keeps the zone shut if a route exists.
- Not touched: variable 0x4057 / 16471 and every flag, Baoba's text, scripts 3, 6, 7, 8, 12 and the Dratini gift.

## Proof (DeSmuME, `work/tools/emu_safari_closed.py`, save full_bag_6mons.sav, clock 2026-10-09 12:00, variable 0x4057 = 2)

| case | Chinese ROM | build without the fix | build with the fix |
|---|---|---|---|
| pay counter (4,6) facing up | pays, Warp, map 357 (79,100) | same | message 46 shown, no Warp, stays on map 173 |
| friend counter (18,6) | hack's own "cannot be used yet" (msg 84), stays | same | closed notice (46), stays |
| Link counter (21,6) | msg 84, stays | same | closed notice (46), stays |
| door (5,2) / (19,2) (player placed at (5,4)/(19,4), walks up) | map 357 | same | stays on map 173 at the door tile |
| Dratini gift NPC (7,13) | message 101 (the offer) | same | message 101, no closed notice |

Also: `work/tools/test_safari_zone_closed.py` (7 tests, no emulator): no counter entry reaches Warp/SafariZoneAction/payment,
the notice comes first, every other entry's commands and the variable/flag writes are unchanged, only the two warps
change. check.py (fast): registry, fixes-md and asm-synth pass; ruff fails on work/tools/fixes.py:1787 and
test_script_insert.py:88 and the tests step on test_honey_gather's setUpClass, all three exist on develop and are not from this change.

Not run: the full build check (check.py --full), the Fuchsia gym by hand (no script it uses is touched: the fix changes
only member 119 and warp events of zone 173, and the unit test pins every other script of member 119).

## Open

- D-2408: Baoba's lines #30/#33 still send the player into the closed zone and the Geodude test cannot be finished.
