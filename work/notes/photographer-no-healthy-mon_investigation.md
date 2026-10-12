# Pallet Town photographer without a healthy Pokémon: investigation (2026-10-12)

**Verdict: REPRODUCED on melonDS (hardware-like), on the untouched Chinese ROM and on rc7. DeSmuME does not show it.**
Natural state: no Pokémon at all (new game before the starter) is the state a player is in when meeting Cameron;
fainted-only and Egg-only parties are forced states (RAM edit after Continue).

## Question
Does the Pallet Town photographer (a/0/1/2 member 733, map 49, script 7) misbehave when no Pokémon in the party can
fight (HP > 0 and not an Egg)? A third-party patch (Speedoption; the Spanish one derived from it) inserts
`CountAliveMons 0x800C,6` and jumps to the decline reply there (work/notes/bradams_lineage_analysis.md). An earlier test
(work/notes/pallet_photo_repro_20261008.md) played the whole scene with an empty party on DeSmuME and saw no problem
(the iOS/Manic crash report was not reproduced).

## Method
- Save: `protographer.sav` (the memcheck fixture: Pallet Town, facing the photographer, party = one Lv 9 Charmander;
  SHA-256 e3452382a76e5304b3c44f6e35faff4193717df2895263f44650ebce171eadb9, copied from the harness worktree).
- Harness: `work/tools/emu_harness.py` API (`start_at(None, sav=..., emulator='melonds'|'desmume', clock=2026-10-09 12:00)`),
  one emulator at a time. The variant is applied in RAM after Continue: `empty` = party count 0 and slot 0 zeroed,
  `faint` = `edit_party_mon(0, currentHp=0)`, `egg` = `edit_party_mon(0, egg=True)`, `healthy` = untouched.
  Then A is pressed 30 times (150 frames each: talk, Yes (the default), the photo scene), a screenshot after each, a
  walk try at the end, `arm9_abort()` and `hang_report(120)` on melonDS. The player stands in front of Cameron, so this is
  the real talk path (no script injection).
- ROMs: untouched Chinese (sha256 4807ab2c...95c8, 536,870,912 bytes, checked), rc7 (b16f81be...10df).
- Driver and logs (scratch, not committed): `<scratch>`, results in `<scratch>` (before the fix) and `<scratch>` (with the fix).

## Results before the fix
| ROM | emulator | healthy lead | no Pokémon | lead fainted | lead an Egg |
|---|---|---|---|---|---|
| Chinese | melonDS | photo taken, control back, no abort | data abort, black screens | data abort | data abort |
| rc7 | melonDS | the same | data abort | data abort | data abort |
| Chinese | DeSmuME | photo taken | scene plays, player free afterwards | scene plays, player free | scene plays, the player could not walk afterwards (not examined) |
| rc7 | DeSmuME | photo taken | scene plays, player free | scene plays, player free | the position read garbage afterwards and the emulator logged an Undefined instruction (not examined) |

All six melonDS failures are identical: first data abort at frame 4836 (the 4th A press, as the photo scene starts),
faulting instruction 0x0206D84C `ldrh r0,[r5,#4]`, abort LR 0x0206D854, r5 = 0: this is the start of GetMonData
(0x0206D848) called with a NULL Pokémon pointer, CPSR 0x60000097, abort mode, both screens black. The photo scene
(CameronPhoto, script command 615) asks for the party lead and reads it without a check; with no healthy Pokémon
the lookup returns NULL. DeSmuME has no memory protection and reads address 0 as 0, so it carries on; that is why the
2026-10-08 empty-party test passed there.

Side observation, not part of this fix: a save whose only party member is fainted or an Egg does not even finish
Continue (DeSmuME: Undefined instruction at 0x02000000; melonDS: the field overlay never loads), probably the follower
setup, so those states had to be created in RAM after the field was up. They are not reachable in play (a party
without a Pokémon that can fight is a white-out).

## Fix verification (photographer-no-healthy-mon)
Fix ROMs: rc7 + fix and Chinese + fix (`mkfix2.py`: narcpatch.apply of the fix onto the ROM).
| ROM + fix | emulator | healthy | no Pokémon | fainted | Egg |
|---|---|---|---|---|---|
| rc7 | melonDS | photo taken, control back (player moved to 1032,367 as before) | "Aren't you a shy one?", scene ends, no abort, not hung | the same | the same |
| Chinese | melonDS | photo taken | the same | the same | the same |
| rc7, Chinese | DeSmuME | photo taken | refusal reply | - | - |
The refusal leaves the player free and Cameron can be talked to again (screenshots).

## Not verified
- A full new-game run on melonDS (the empty party there is created in RAM in front of Cameron, not by playing the intro).
- Hardware itself (melonDS 1.1 is evidence, not proof) and the Manic/iOS build.
- The reply: message 5 "Aren't you a shy one?" is the one given for No. It is not about Pokémon; a dedicated
  line would be new text (D-1500), so the decline reply is reused, as the third-party patch does.
- Viewing the stored photo in the PC; the album-full and no-album replies (unchanged paths).
