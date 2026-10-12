# Issue 3 — zero-PP Struggle fix, 2026-10-09

Implemented and verified the scoped D-1576 repair under **D-2300**. Technical choice
**D-2302** records its scope. Untouched CN and RC7 reproduction is documented in
`issue03_struggle_reproduction_20261009.md`. No downloads, commits, publishing,
Newt party changes, story changes or root/candidate ROM replacement occurred.

## Repair and critical behavior choices

`work/patches/zero-pp-struggle/` is an enabled, guarded armips registry fix. It
rewrites only overlay 14's original 240-byte command guard at
`0x0222C550..0x0222C63F` (file offset `0x2BD70`). No overlay growth, allocation,
asset, script, save or move-table edit is involved.

The original guard handles fainted/skip state, forced-action flag 1, stored move
tag 26, and stored move tag 27, in that precedence. It never checks aggregate PP.
The repair preserves those checks and uses shared constructor/return tails to
make room for the new scan. The tag-26 two-word argument copy now loads those same
words directly from its local buffer; the external helper sees identical values.

The new scan runs **only when saved caller LR is `0x02202F81`**, the initial
FIGHT-state handler call at `0x02202F7C`. This distinction matters: the same guard
also runs before the command menu and for AI/forced commands. Forcing Struggle
from those calls would remove the player's opportunity to choose Bag, switch or
run. Other callers retain their original result. Runtime confirms the exhausted
Pokémon still reaches the command menu before FIGHT; host tests cover those other
callers. Actual Bag/Leppa/switch/run UI journeys were not exercised in this stage.

After native forced-action checks, scan all four native move slots. A slot with
move ID 0 is empty and cannot provide an available move, even if its PP byte is
nonzero. Any known move with PP returns ordinary selection. Otherwise, construct
move **165** with the existing native move-action constructor `0x02200960`, native
actor number and native target field. The existing engine resolves Struggle's
target and executes damage/recoil. The zero-known-move host case also produces
Struggle; it is not a claim of a naturally encountered empty moveset.

Neither usability validator `0x0222C304` nor execution validator `0x0221D7A8` is
patched. An individual exhausted move remains rejected when a different known
move has PP. There is no expansion to Disable, Taunt, Encore, Choice restrictions,
or other move-lock rules. Existing forced actions still take precedence.
Read-only assembly guards pin the enclosing FIGHT call, original guard, native
actor/move/PP helpers, action constructor, and native Struggle acceptance site.

## Paired builds and identities

Both full current-tree builds used local armips v0.11.0, existing translated
banks and existing generated graphics, with `--no-regen-graphics --no-patch`.
Build verification passed in both: NARC round-trip/export comparison, glyphs,
graphics, hardcoded assembly regions and text-speed metadata. Reports and logs
are preserved under ignored `work/build/bugfix-sequential-20261009/issue03/fix/`.
Existing unrelated dirty source/patch work is present in **both** builds.

| Artifact | SHA-256 |
|---|---|
| `fix/without/origin_hg_v4.0.3_en_wip.nds` | `81017f681a3687108528f88e57adbd0f705036f1ce4004ea0f7af13fc8e4a98a` |
| `fix/fixed/origin_hg_v4.0.3_en_wip.nds` | `93514313cba83acbb3f6b870fddfc9b111d62ad20b763a0670e4dd67ab074668` |
| Final assembled 240-byte guard | `4a5379d57c1e260a8d31cac1113f43a0a199fef78371ea7b4e6a9d4972dda050` |
| Preserved root English ROM | `6fa7b4e739391ca9ea9bfcf90d83eec6407c3c04102e52432bb41bc8ae44a7d3` |
| Source battery save | `b3aca10747cd0f1adc3d5852a50dddaaa36ed8680f5ba04012cfe3110faad90f` |

Independent pair comparison: **only ROM file ID 14 differs**. The decompressed
overlay stays 337,216 bytes; 193 changed bytes are inside
`overlay14+0x2BD8A..0x2BE5F`, entirely within the declared guard region.
`fix/pair-summary.json` records these assertions. Final comment/decision and
read-only-guard additions were made after building; assembly/listing and machine
code tests confirm identical final payload bytes. Final builds were not copied
over any root or RC7 artifact.

## Runtime verification

`work/tools/emu_struggle.py` uses fresh boots, one DeSmuME 0.9.12 ARM64 instance
at a time, a private copy of the original save, noon 2026-10-09, map 109, and
native debug-generated level-20 Gastly records. Those field records are strictly
validated before battle. Only private move/PP/party-count fields are edited.
Trainer battles are injected through the game's native script command. Trainer
185 retains `TrainerBattle 185,0,1,0`; trainer 5 uses `5,0,0,0`; doubles uses
`6,6,0,0` with two party Pokémon. Native battle actor/action/HP traces are used;
no open/transient encrypted party record is decoded or repaired.

The enemy-exhaustion control additionally sets enemy **native battle** PP to zero
at the initial command guard; it is explicitly a RAM fixture, not natural play.
Its existing AI path submits Struggle in both paired builds. This fix changes no
AI selection behavior.

| Case | Without fix | Fixed |
|---|---|---|
| Four known moves, all zero PP | No action; HP and PP unchanged after rejected choice | FIGHT submits 165; foe HP 32→19; Gastly recoil 42→39; command menu returns |
| One known zero-PP move + three empty slots | Same rejection | Same successful native Struggle turn |
| Mixed PP: Lick 0, Shadow Ball 1 | Lick rejected; Shadow Ball submits 247 and PP reaches 0 | Same rejection and normal Shadow Ball turn, PP 1→0 |
| Last PP transition (Growl 1) | Not run for this transition | Growl 45 consumes last PP normally; following FIGHT submits 165; foe HP 32→18, recoil 42→38; next menu returns |
| Trainer 5 single battle | Not rerun in this stage | Struggle KOs foe (19→0), recoil 42→37; win completes and returns to field |
| Doubles, exhausted lead and Growl partner | Not run in paired baseline | Lead 165, partner 45; living foe KO (17→0), lead recoil 42→38; next command menu returns |
| Enemy native PP zero | Enemy submits 165, damages player and takes recoil | Same enemy action/damage/recoil; next menu returns |

These are native executor numbers, not a proposed change to Struggle's recoil
formula. Duplicate HP changes in traces are the executor/UI actor copies being
updated separately. Battle actors are distinct from UI actors.

The first runtime runner recorded a meaningless final UI-actor snapshot after
trainer 5 returned to field: the battle UI had been freed. That raw snapshot is
**excluded from all assertions and conclusions**; its victory evidence is the
valid in-battle action/HP trace and return to field. The final runner now records
`final: null` for field outcomes. Original raw evidence is preserved.

`fix/runtime-verified-summary.json` independently asserts the completed seven
fixed cases, paired exhaustion/positive/enemy controls, fixed mixed-PP rejection,
damage/recoil, last-PP transition and unchanged source save. Exact runtime result
hashes:

| Evidence | SHA-256 |
|---|---|
| `runtime-fixed/result.json` | `346d2dc3d575e7ff8b403ab4e6ab6df7c4a9ec59a2a15946f12506b98b43dfe1` |
| `runtime-without/result.json` | `3e693ab0d08b75e70dec0a6d54f3b49d574f06e40bf8430c3beeb8c95cfa430c` |
| `runtime-positive-fixed/result.json` | `2ec394280763ddc49c0ebc9e93c0e2eb598d7adef3e8308f93aceb428be581b8` |

Screenshots include the native “Gastly used Struggle!” message, damage/recoil,
next command menus, and zero-PP rejection in the positive control. Same-ROM
private savestates are preserved; no cross-ROM state was loaded.

## Host tests and commands

`work/tools/test_zero_pp_struggle.py` executes the **assembled guard** and native
action constructor in the existing Thumb interpreter, with adversarial external
actor-helper stubs that clobber caller-saved registers. Four tests pass:

- All 256 move-presence/PP masks, including empty slots with stale nonzero PP.
- Three non-FIGHT callers keep native ordinary selection with all PP zero.
- **64** native-vs-patched forced precedence combinations: dead/alive, flags 1/4,
  stored tags 26/27 including both, and present/null action records. Saved
  registers and stack are preserved. An interim update mistakenly counted this
  as 128; the correct count is 64.
- Changed original guard bytes fail assembly guards.

Registry check, final disassembly snapshot check and ruff checks also pass.
Representative exact commands (all from repository root):

```sh
.venv/bin/python work/tools/build.py --armips $HOME/Developer/armips/build/armips --work-dir work/build/bugfix-sequential-20261009/issue03/fix/without --without zero-pp-struggle --no-regen-graphics --no-patch
.venv/bin/python work/tools/build.py --armips $HOME/Developer/armips/build/armips --work-dir work/build/bugfix-sequential-20261009/issue03/fix/fixed --no-regen-graphics --no-patch
.venv/bin/python work/tools/emu_struggle.py --rom work/build/bugfix-sequential-20261009/issue03/fix/fixed/origin_hg_v4.0.3_en_wip.nds --out work/build/bugfix-sequential-20261009/issue03/fix/runtime-fixed
.venv/bin/python work/tools/emu_struggle.py --rom work/build/bugfix-sequential-20261009/issue03/fix/without/origin_hg_v4.0.3_en_wip.nds --out work/build/bugfix-sequential-20261009/issue03/fix/runtime-without --without --cases four-zero,one-zero,positive,enemy
.venv/bin/python work/tools/emu_struggle.py --rom work/build/bugfix-sequential-20261009/issue03/fix/fixed/origin_hg_v4.0.3_en_wip.nds --out work/build/bugfix-sequential-20261009/issue03/fix/runtime-positive-fixed --cases positive
ARMIPS=$HOME/Developer/armips/build/armips .venv/bin/python work/tools/test_zero_pp_struggle.py
.venv/bin/python work/tools/asmpatch.py --armips $HOME/Developer/armips/build/armips listing --check zero-pp-struggle
```

A preliminary emulator command aborted at native startup with exit 134 inside
the sandbox; subsequent emulator commands used required `require_escalated` and
completed normally. That host restriction is not a game failure.

## Limits and handoff

Verified: core exhausted-player selection, empty slots, ordinary PP rejection,
positive selection, natural last-PP consumption within the fixture, actual damage
and recoil, next turns, one completed win, one doubles configuration and existing
enemy Struggle behavior. Not verified: a natural Route 12/Newt story route or
must-lose story cleanup, Bag/Leppa UI restoration, switch/run UI sequences,
all doubles target configurations, other restrictions, melonDS or hardware.
No claims of those wider controls are made.

Production files added: `zero-pp-struggle/fix.toml`, `.asm`, `.listing`,
`work/tools/emu_struggle.py`, `work/tools/test_zero_pp_struggle.py`, and this note.
`work/patches/FIXES.md` was regenerated; decision D-2302 was appended with the
decision CLI. Other dirty/untracked work was preserved.
