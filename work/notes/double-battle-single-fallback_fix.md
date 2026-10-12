# double-battle-single-fallback (2026-10-12)

Fix `work/patches/double-battle-single-fallback/`, decision D-2357 (the id may collide with other branches: the merge step renumbers),
related D-1559 (the Department Store finding). Authority: user 2026-10-12, "Lets replace [the Department Store check] and build a
downgrade to single battle like the Spanish patch." This replaces the per-battle `department-store-double-one-mon` guard (that branch is
untouched). Nothing was copied from the Spanish ROM: the code below is derived from the Chinese arm9.

## Code (untouched Chinese ROM, arm9)
`0x02050768` is the trainer battle setup (r1 trainer 1, r2 trainer 2, r3 partner, stack: flag, flag, heap, ...). Callers: ScrCmd_TrainerBattle
(213, 0x02048B64; r3 = the follower partner id from the save when the player has one), MultiBattle (562, 0x02048BF8; r3 = its first argument),
and the handler of script command 223 (0x02048EC8, battles trainer id 1). It picks the type r4 and calls `BattleSetup_New(11, r4)` (0x020507A8):

| trainer 2 | partner (r3) | type |
|---|---|---|
| 0 | any | 1 (0x801 when the script's flag byte is set: loss allowed) |
| = trainer 1 | any | 3 double, one trainer twice |
| other | 0 | 0x13 double, two trainers |
| other | set | 0x4B multi battle, the partner is the ally |

The setup stores trainer 1 at +0x1C, partner +0x20, trainer 2 +0x24. Nothing reads the party. The player's party count is `Party_GetCount(SaveArray_Party_Get(save))`
(0x02073398 / 0x0207365C; the same calls the native PartyCheckForDouble uses, 0x02048EB8). With a count below 2 the overlay 14 init reads the empty
second player slot as a pointer (DeSmuME: broken ally, blank screen at FIGHT; melonDS: data abort at 0x022167B4).

## Fix
At 0x020507A4 `movs r0,#0xB; adds r1,r4,#0; bl BattleSetup_New` becomes `bl hook; nop; nop`. The 40-byte hook (+4 nop) sits in the handler of command 223
(0x02048EC8, 44 bytes). That command is used by no script of a/0/1/2 (all 850 TrainerBattle, 91 MultiBattle and 9 TrainerMessage sites plus every opcode
were scanned: opcode 223 occurs nowhere) and only its command-table slot (0x020F7CB8) points at it. The hook: if `(type & 0x42) == 2` (double, no partner bit: types 3 and 0x13) and the party
count is below 2, then r4 = 1 and r6 (trainer 2) = 0; then `BattleSetup_New(11, r4)`; return. r5 holds the return address (it is free until BattleSetup_New returns).
Not changed: singles (1, 0x801), multi battles with a partner (0x4B), every other BattleSetup_New caller (wild encounters, link, facilities, Pal Park: other overlays
and other types; they do not go through 0x02050768).

Criterion = party COUNT, not "able to fight": one healthy Pokemon next to a fainted one or an Egg behaves exactly as in the Chinese hack (the engine
sends the fainted/Egg slot out as the ally; observed to play). If the user prefers "fewer than two able to fight", the hook would call
0x02053570's counter (0x0205349C) instead of Party_GetCount, same size; that would also turn the fainted/Egg case into a single battle.

## The second trainer (multi-trainer decision)
The downgraded battle is a single battle against trainer 1 (the first id). Trainer 2 is not fought and no reward is taken for them: money and the
Pokemon come from trainer 1 only. Progress is not affected, because the scripts do not rely on the engine for the defeated flags: the standard trainer
script (file 949, double branches at L4101/L4348) and the one-off scenes call `SetTrainerFlag` for both trainers themselves after `CheckBattleWon`
(Department Store 6F: file 901 L3087, the win goes straight to the shoppers' "Ow! ..." lines and the White Flute; the loss goes to WhiteOut). So
the second trainer is skipped silently and counted defeated, the first one's team must be beaten. This changes no flag logic. Where a script
battles the SAME id twice (Yellow's Singles option 951 951, Chuck 34 34) the single battle is that trainer's usual team.
Not examined individually: the other ~130 sites for scripts that read trainer 2 after the battle.

## Verification
Emulator driver and logs: session scratchpad `fix/double-battle-single-fallback/` (`dbs.py`, `logs/`, `out/` screenshots). ROMs: Chinese, rc7, and
the fix applied alone to each (`mkfix2.py`). DeSmuME records the BattleSetup_New type through an exec hook; melonDS has no hooks, so the type there is
judged from the screen. "Dept" = natural talk path in Department Store 6F from the investigator's in-game save fixture; "forced" = `LockAll; TrainerBattle a b; End` run
by the harness (DeSmuME only: run_script needs on_exec). Party edits are RAM edits after load.

### Department Store 6F, natural path (777 778)
| party | Chinese / rc7 | fixed (Chinese+fix, rc7+fix) |
|---|---|---|
| 1 Pokemon | DeSmuME: type 0x13, broken ally, never ends; melonDS: data abort 0x022167B4 on both | DeSmuME and melonDS: type 1, single battle vs Rhydon, plays to the end; loss: white-out to the Pokemon Center (map 501) |
| 1 Pokemon, Lv100 (win) | - | single battle won on both emulators, both fixed ROMs: back in map 196, flag 2147 set (the script ran to the end: shoppers' lines, White Flute) |
| 2 healthy | double 0x13, plays, loss/white-out | identical (0x13), both emulators |
| 1 healthy + 1 fainted | 0x13, plays (DeSmuME; Chinese) | identical (0x13), both emulators |
| 1 + Egg (party count 2) | 0x13, plays | identical (0x13), both emulators |
| 2 Pokemon, lead Lv100 (double win/loss) | - | still a double (0x13); plays; the weak second Pokemon lost in most runs (white-out), one rc7+fix DeSmuME run won (2147 set) |

### Forced scripts (DeSmuME), party of one unless noted
| script | Chinese | fixed |
|---|---|---|
| TrainerBattle 951 951 (Yellow Singles) | type 3, freeze | type 1, single battle, menu works |
| 34 34 (Chuck) | type 3, freeze | type 1 |
| 786 787 (two trainers) | 0x13, freeze | type 1 vs 786 (Bronzong Lv90 seen), trainer 787 not fought |
| 786 787 / 951 951 with two Pokemon | 0x13 / 3 | unchanged |
| 823 0 (single) | 1 | 1 |
| MultiBattle partner 64, 507 508, one Pokemon | 0x4B, double with the partner | 0x4B, still a double with the partner |

Each fixed row was run on Chinese+fix and rc7+fix. The win/loss ends of the forced scripts were not followed: the harness script has no WhiteOut/result handling, so after a loss the
loop hit its iteration cap; only the start (type, battle screen, command menu) is the evidence there.

### Not verified
Hardware; melonDS for the forced scripts (no run_script there); the other ~130 sites individually (no natural-path run, so no check of what each script does after the battle);
the Battle Frontier / link / tag facilities (they never reach 0x02050768; not run); wild doubles (Safari: separate fix; the random wild double and the follower double use
ov2 types 0x4A through BattleSetup_New, not this function; the random one needs two Pokemon able to fight already); the Lv100 double runs are not a clean win/loss comparison.
Offline: `python3 -m unittest work/tools/test_double_battle_single_fallback.py` runs the real setup function from the assembled arm9 on a Thumb
interpreter with the natives stubbed: types for party counts 0, 1, 2, 3, 6 with single, same-trainer double, two-trainer double, partner
multi battle, loss-allowed single; the control on the original arm9 shows the type never depended on the party; trainer 2 stored in the setup is 0 only on the downgrade.
Static: `fixes.py check`, `asmpatch.py synthetic/check/listing`, test_fixes/test_asmpatch/test_asmlisting pass. test_asmpatch's source list and count were extended by this fix.
expected.toml (full build hash) was NOT updated: no full build was possible in this worktree (the merge step disables the fix).
