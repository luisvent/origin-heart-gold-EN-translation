# In-battle party screen: stale status after Heal Bell / Aromatherapy

2026-10-09. Fix: `work/patches/battle-party-status-sync/` (overlay 14, five regions), D-2317 (user-approved
exception to D-1337).

## Report

Discord: "After using Heal Bell (cures your whole team of status conditions) the status conditions are still
displayed on the Pokémon in the swap screen, but when swapping them in they are cured, so it's just a visual
bug."

## Reproduction (DeSmuME, before the fix)

Save `full_bag_6mons.sav`, map 28 (1326, 80); lead Chansey Lv60 from the hack's generator with Heal Bell (or
Aromatherapy) only; bench slots 1-3 set to PSN (0x08), PAR (0x40), BRN (0x10) in RAM; `TrainerBattle 960`
(Camper, Nuzleaf/Luvdisc Lv17; Fake Out takes the first turn); Heal Bell on turn 2; then the POKéMON button.

| ROM | Cure messages | Party screen (slots 0-5) |
|---|---|---|
| untouched Chinese v4.0.3 | 1#336, 1#380, 1#360 | 0, PSN, PAR, BRN, 0, 0 |
| build without the fix | 1#336, 1#380, 1#360 | 0, PSN, PAR, BRN, 0, 0 |
| build with the fix | 1#336, 1#380, 1#360 | all 0 |

The status shown is the one the party screen's copy of each Pokémon holds, read at the arm9 status-icon
routine `0x0208A200` (`GetMonStatusIconId`); screenshots agree. A Pokémon switched in after the cure has no
status, and after the battle the field party is cured: only the screen was wrong.

The same screen never showed a status gained in battle either: lead with a Flame Orb (burned at the end of
turn 1) shows no BRN on the Chinese ROM and the control, BRN with the fix. Refresh on a poisoned lead: PSN
stays on the control, gone with the fix.

## Cause

Overlay 14 is the hack's battle engine (a different engine from vanilla HGSS, with per-member battle records
and two copies of each party). Each party member has a battle record (bpp, 0x414 bytes): its status table
is at bpp+0x40.. (8-byte entries, PAR at +0x40, BRN at +0x58, PSN at +0x60 as seen in RAM), and bpp+0x10
points to the battle's copy of the party Pokémon.

- Heal Bell/Aromatherapy (the hack prints one cure message per Pokémon) cure each member through
  `BPP_CurePokeSick` (0x02216CC0), which clears the record's table only. So do every other cure and the
  status setter (`0x02216DD8` calls the cure first, then sets the new condition): the copies are never
  updated during the battle.
- At the end of the battle `BPP_ReflectToPP` (0x02218B28) writes HP, experience, status, moves, form and item
  from the record to the copy; its status block (0x02218B52) converts the record's condition
  (`BPP_GetPokeSick`, 0x02216C64: 0 none, 1 PAR, 2 SLP, 3 FRZ, 4 BRN, 5 PSN) to party status bits (0, 0x40, 2,
  0x20, 0x10, 0x08; fainted -> 0) and calls `SetMonData(copy, 0xA0, ...)`.
- The in-battle party screens are built in four loops that add `BPP_GetSrcData(member)` (the copy) to a new
  party: 0x022027DC (POKéMON button), 0x02202B78 (Bag item target), 0x0220405C (forced switch after a faint, and after U-turn),
  0x02203DBC ('Will you switch your Pokémon?' when the foe's Pokémon faints in a trainer battle). Hooks
  confirmed all four (the fourth and U-turn in the review).

So these screens show every status as it was when the battle started.

## Fix

- ReflectToPP's status block is replaced by `bl BPP_SyncSickToPP; b <rest of ReflectToPP>`, and the new
  routine `BPP_SyncSickToPP(bpp)` (0x02218B5A, in the same 80 bytes) does what the block did (same table,
  same fainted case, same SetMonData) and returns the copy. ReflectToPP's result is unchanged.
- The four loops call `BPP_SyncSickToPP` instead of `BPP_GetSrcData` (one `bl` each), so each copy gets the
  record's current status right before the screen is built.

Nothing else is written to the copy; the records, the cure logic, catching (0x0222B99E) and the
single-Pokémon copy at 0x0222F5B2 are untouched.

## Evidence after the fix

- `emu_harness.py fixes --case battle-party-status-sync` (scenario `healbell`, DeSmuME): fixed ROM `fixed`
  (cures 336/380/360, screen all 0), control `original` (screen 0, 0x8, 0x40, 0x10).
- Aromatherapy, Refresh, Flame Orb: as above (fixed shows the current status, control the old one).
- Double battle (`TrainerBattle 960 960`, Chansey + Blissey, bench PSN/PAR/BRN, partner PSN): control shows
  PSN/PAR/BRN, fixed none.
- melonDS 1.1 (`trainer_2mons.sav`, Route 1 trainer, Chansey with Heal Bell, bench PSN/PAR): control shows
  PSN/PAR, fixed none; no data/prefetch aborts or undefined instructions on either.
- End of battle unchanged: win with a Flame Orb lead (lead BRN, bench statuses kept) and after Heal Bell
  (bench cured): identical field statuses on the fixed and the control build.
- `emu_harness.py fixes --case battle,ivev`: pass.

Not tested: real hardware.

## Review (2026-10-09)

- Behaviour unchanged apart from the screen. A trainer battle with a Toxic Orb lead and a Rest user,
  switched out and back three times through the party screen (sleep and toxic on records whose copies the
  screen now syncs): the whole battle message log (every battle_string read, 59 reads over 11 turns:
  poison damage, 'is fast asleep' twice, 'woke up', Rest again) is identical on the fixed and the control
  build. The sleep turns live in the record (`BPP_Create` 0x022160F8 draws a fresh sleep duration from the
  party status only when the battle starts; it is called only by the battle setup 0x02215080), so the copy's
  SLP value (2, the hack's own end-of-battle value) is never read back during the battle.
- Fleeing a wild battle and catching: `ReflectToPP` runs at the end of every battle for each member
  (0x022308E0, also on fleeing) and for a caught Pokémon (0x02215C1E); the field party after fleeing
  (Flame Orb burn kept) and the caught Pokémon's status (Spore: SLP 2, Thunder Wave: PAR 0x40) are the same
  on both builds. The only foe-side call of `BPP_SyncSickToPP` is the catch's `ReflectToPP`, as before.
- Other readers of the copy's status in overlay 14: only `BPP_Create` (battle start) and the doubles
  target-selection buttons (0x02212B34, through `BPP_GetViewSrcData`; it colours a button for a statused
  Pokémon). Those buttons are drawn for the foes and the partner, whose copies the fix never touches.
- Multi battle (`MultiBattle 385 416 613`, partner Blue): Heal Bell cures the bench; control PSN/PAR/BRN,
  fixed none; the party screen lists the player's six only; the battle logs are identical.
- Vanilla HeartGold (USA, new game, Route 29, DeSmuME): a Flame Orb burn shows BRN on the in-battle party
  screen at once, and Heal Bell's cure of a benched PAR Pokémon shows at once. Vanilla's overlay 12 writes
  the party Pokémon itself: Heal Bell sets each party member's status (`SetMonData(mon, 0xA0)` at
  0x022593AE, skipping Soundproof), and the battle copies the battler to its party Pokémon (HP, status,
  moves, item, form: 0x022591F4, link command 39) after each change. The fix makes the hack's screens agree.
