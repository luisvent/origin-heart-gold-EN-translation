> Update 2026-10-09: the later `double-target-option2` worktree implemented the approved Option 2
> and recorded 22/22 CN/EN emulator checks on 2026-10-07. It is now ported as the enabled armips fix
> `work/patches/double-battle-targeting/`. See `work/notes/double_target_armips_port.md`.
> The approval/status and legacy build plans below describe the earlier investigation.

# Double-battle target cursor: bug, options and build plans

Status 2026-10-06: researched and prototyped, **not approved**. The bug is in the original hack's code (v4.0.3), so
fixing it is an exception to D-1337 ("hack gameplay bugs are reported, never fixed") and needs the user's explicit
decision. Nothing here is enabled in the build.

This file records everything needed to build **option 2** (recommended first step) and **option 4** (full
vanilla behaviour), and why options 1 and 3, the Bradams patch and "no fix" were not chosen.

All addresses are runtime addresses in **overlay 14** of the Chinese v4.0.3 ROM (base `0x022007E0`; file offset =
address − `0x022007E0`). Our English build's overlay 14 is identical in all code named here (it differs only in data
at `0x0224C88B`–`0x0224CA66`).

## 1. The bug

Player report: "anyone getting a bug where 2v2 battles make u only attack ur teammate? Try touch controls as a
temporary fix."

Reproduced in the emulator on the untouched Chinese ROM and on our English build (identical results).

**Trigger:** a foe position stays **empty** in a double battle. That happens when the trainer has no Pokémon left to
send in, in wild doubles and in multi battles. A foe that faints and is replaced never triggers it.

| Foe that is gone | Who is trapped | What the player sees |
|---|---|---|
| Top-right (slot 1) | Your lead | Cursor opens on your partner; Up/Down/Left/Right all stay there; Down to CANCEL snaps back. A attacks the partner, B is the only way out. Repeats every turn. |
| Top-left (slot 3) | Your second Pokémon | Same trap, stuck on your lead. |

**Milder variant, no faint needed.** After your partner uses a self-target move (Splash), your lead's cursor opens
on the partner. Pressing A at once hits the partner; Up gets out.

**Workaround for players:** tap the foe on the touch screen. Down to CANCEL does not help: the D-pad cannot reach
CANCEL in this hack.

Not affected:
- your partner fainting with no replacement
- your lead fainting, replaced or not
- turn 1 of every battle (the remembered target is cleared at battle end)

### Slots and grid

| Slot | Position on the target screen |
|---|---|
| 0 | your lead, bottom-left (BL) |
| 1 | foe, top-right (TR) |
| 2 | your partner, bottom-right (BR) |
| 3 | foe, top-left (TL) |
| 4 | CANCEL |

Grid table `0x0224CD44` (byte-identical to vanilla `0x0226E210`):

```
row 0:  3  1
row 1:  0  2
row 2:  4  4
```

### Code (Chinese v4.0.3, overlay 14)

| What | Address | Notes |
|---|---|---|
| Shared cursor memory | `0x02255B90` | Generic menu framework struct: +0 u8 show-cursor flag, +1..+3 padding (unused), +4 pointer, +8.. u32 per screen. +0x10 = command menu, **+0x14 = target screen** (`0x02255BA4`). |
| Target-mode table | `0x0224D060` | Byte-identical to vanilla `0x0226E64C`. Mode = request byte 3. Single-target modes: 8 = lead's normal move `[0,1,1,1]`, 9 = partner's `[1,1,0,1]`, 6 = partner's self-target `[0,0,1,0]`, 10 = user-or-ally. Spread modes: 1, 2, 3, 5, 7. |
| Spread predicate | `0x02212758` | Returns 1 for spread modes. |
| Eligibility builder | `0x022126CC` | Fills 4 bytes (1 = eligible). r2=1 also requires the battler to be present (`0x022196AC`); r2=0 checks the mode only. |
| First eligible | `0x02212784` | Order 0,1,2,3; returns 4 if none. |
| Navigation | `0x022127A4` | Straight-line search; skips ineligible cells; CANCEL always accepted; leaving the grid keeps the old slot; never tries the other column. |
| Key handler | `0x02212828` | 0xFC bytes; pointer stored at `0x0224CE94`. |
| Draw | `0x02212924` | 0xCC bytes. |
| Repair | `0x022129F0` | 0x48 bytes. Keeps +0x14 if valid, else first eligible. Its signed `>=4` test treats CANCEL as invalid. |
| State handler | `0x02212558` | Entry, accept (A and touch), confirm. |
| Touch write | `0x022140DA` | In the shared input dispatcher `0x0221400C`, which serves four screens: don't touch it. |
| Battle-end clear | arm9 `0x020DC3B8` | Clears +0x14 to 0. |

Callers:

| Routine | Called from |
|---|---|
| Repair `0x022129F0` | entry `0x02212596`; rejected A/touch `0x022125D0`; **every frame** `0x0221283A`; draw `0x02212936` |
| First eligible `0x02212784` | spread value sent to the engine `0x0221262E`; spread Up `0x02212866`; spread A `0x022128FC`; spread draw `0x02212958`; repair spread branch `0x02212A06`; repair single-target fallback `0x02212A2C` |
| Navigation `0x022127A4` | `0x02212880`, `0x02212896`, `0x022128AE`, `0x022128C4` (the four directions in the key handler) |
| Eligibility `0x022126CC` | `0x0221233E` and `0x0221244A` (button setup, r2=0); accept check `0x022125BE` (r2=1); `0x02212752` (group helper); `0x0221278A` (first eligible); `0x022127C0` (navigation); `0x02212A16` (repair) |

Key handler writes to +0x14:
- the four directions: `0x02212886`, `0x0221289C`, `0x022128B4`, `0x022128CA`
- spread Up stores the first eligible slot: `0x0221286C`
- spread Down stores 4: `0x0221285A`

### Repair routine (`0x022129F0`), for reference

```
push {r3,r4,r5,lr}; r4 = [0x02255B90+0x14]; r5 = obj
bl 0x02212758 (spread?) ; if spread:
    if r4 == 4 -> keep
    r0 = bl 0x02212784 (@0x02212A06) ; store +0x14 ; return
single target:
    bl 0x022126CC(obj, sp, 1)        (@0x02212A16, r2 set at 0x02212A14)
    0x02212A1A: cmp r4,#0 ; blt invalid ; cmp r4,#4 ; bge invalid      <- CANCEL counted invalid
    if eligible[r4] != 0 -> keep (0x02212A34)
invalid (0x02212A2A): r0 = bl 0x02212784 (@0x02212A2C) ; store +0x14
```

### Why the three causes combine

1. **One shared memory slot for both battlers.** A self or ally pick by one carries over to the other.
2. **Fallback order 0,1,2,3.** Your own Pokémon come before the left foe, so after a faint the cursor lands on a
   teammate.
3. **Straight-line navigation, plus CANCEL rejected every frame.** No key leads off the teammate.

### Where the code came from

- v3 (and vanilla) have HeartGold's own cursor module: per-battler memory, foe-first order 3,1,0,2, no per-frame
  repair.
- v4 replaced HeartGold's battle overlay with a different engine. Less than 2% of overlay 14 matches vanilla. It
  rebuilt the bottom-screen menus partly from HeartGold source (identical grid and mode tables, some functions
  recompiled line for line) on a generic menu framework with one remembered cursor per screen.
- Vanilla's cursor module was not carried over. The shared target, the 0,1,2,3 scan and the straight-line search look
  like simple generic code, not a design choice. Intent can't be proven from the binary.
- Side findings that contradict repo notes (not yet corrected):
  - `work/notes/credits_and_sources.md` says v4 is "built on hg-engine". The battle code is not hg-engine's.
  - `hardcoded_text.md` says v4 keeps the Japanese code layout. v4 has 120 overlays against the Japanese ROM's 128.
  - `hardcoded_text.md` also says our ov14 is byte-identical to the Chinese one. 334 bytes of data differ; the code
    named here is identical.

## 2. The options compared

Vanilla behaviour comes from static reading of the USA ROM (overlay 12); vanilla was not run in the emulator.

| Situation | Vanilla HG | 1: prototype | 2: prototype + vanilla order | 3: near-vanilla | 4: full vanilla | Bradams |
|---|---|---|---|---|---|---|
| Turn 1 start | TL | TR | **TL** | TL | TL | TR |
| Later turns | per battler, own last target | shared foe | shared foe | shared foe | **per battler** | shared foe |
| After partner's Splash | lead unaffected | foe | foe | foe | lead's own memory | foe |
| Empty foe slot | navigable, A does nothing | skipped, diagonal jump | skipped, diagonal jump | navigable, A does nothing | navigable, A does nothing (4a) or skipped (4b) | skipped, diagonal at every step |
| Down from a foe | TL→CANCEL, TR→own below | as vanilla | as vanilla | as vanilla | as vanilla | detours via own Pokémon |
| Up from CANCEL | column you came from | right column | right column | right column | **column you came from** | own Pokémon |
| Ally targeted on purpose | remembered | not remembered | not remembered | not remembered | remembered (modes 8/9) | not remembered |
| Spread value sent to engine | first alive 0..3 | **TR first (changed)** | unchanged | unchanged | unchanged | TR first (changed) |
| Size | — | 160/164 B in place | **164/164 B in place** | < prototype | rewrite of 0x2B8 B block | needs ITCM growth |

## 3. Why options 1 and 3, the Bradams patch and "no fix" were not chosen

- **1. Prototype as is.**
  - It starts on the right foe where vanilla starts on the left.
  - It changes the representative target the state handler sends to the battle engine for spread moves
    (`0x0221262E`) and the value the repair stores for spread modes. Earthquake played out normally, but field-wide
    moves (mode 3) and the partner's spread moves (mode 7) were never tested, and the engine's use of that value was
    never read.
  - Option 2 fixes both at the same size, so 1 is strictly worse.
- **3. Near-vanilla (navigable empty cells, no memory).**
  - It takes vanilla's weak point (the cursor can rest on an empty slot where A silently does nothing; touching an
    empty slot moves the cursor onto it) without vanilla's strength (per-battler memory).
  - It is a middle ground with less polish than 2 and less fidelity than 4.
  - Its only advantage, being the smallest change to the hack's own logic, matters less than UX.
- **Bradams patch (Speedoption fork).**
  - It does fix the trap; verified in the emulator.
  - No licence or reuse permission. Authorship of individual hunks is unclear (the author says it's largely
    AI-assisted, on other translators' bases).
  - Its code lives in fast memory (ITCM) the system still treats as free, which our patch tool can't create.
  - Its every-step diagonal fallback changes moves that work today: Down from a foe goes to your own Pokémon instead
    of CANCEL, and Up from CANCEL lands on your own Pokémon.
  - It bundles an unrelated command-menu cursor cache with a stale-pointer risk.
  - Its diagnosis is worth crediting; its bytes are not reused (none were).
- **Porting vanilla's code verbatim.** Not possible:
  - vanilla's cursor module doesn't exist in v4
  - its memory hangs off vanilla battler structs the new engine doesn't have
  - its memory reset on send-out lives in the vanilla battle core
- **No fix (D-1337 default).** Players get trapped and attack their own Pokémon in common late-battle situations. If
  this is chosen: log a hack finding, add the touch-screen workaround to `guide/known-issues.md` and the release
  notes.

## 4. Build plan: option 2 (prototype + vanilla order + native spread order)

**Behaviour:**
- **Start:** opens on a living foe, left first (vanilla order 3,1,0,2). A remembered foe (1/3) is kept; a remembered
  ally, self or CANCEL is never used as the start.
- **D-pad:** straight-line search as in the hack. If a vertical search leaves the grid without a hit, it is repeated
  once from the same row in the other column. That changes only the 11 of 320 mask/slot/direction cases where the
  hack's cursor stayed put.
- **CANCEL** is reachable and stays selected.
- **Spread moves and their engine value** are unchanged (native order 0,1,2,3).

### Patches

Same mechanism as the prototype: `work/translate/hardcoded/code_patches.json`, same-size in-place edits, each with
`expect` = the untouched Chinese bytes, so the build refuses them if the code ever changes. Use ids
`dbltarget2-*` and `"enabled": false` until approved.

| id | Address (file offset) | Change |
|---|---|---|
| `dbltarget2-code` | `0x02212784`–`0x02212827` (`0x11FA4`, 164 bytes) | New code below: `first_eligible` (native order) at `0x02212784`, `first_eligible_foe` at `0x02212788`, `entry_repair` at `0x022127AA`, `nav` at `0x022127BC`. **164 of 164 bytes, no padding.** |
| `dbltarget2-navcall1..4` | `0x02212880`, `0x02212896`, `0x022128AE`, `0x022128C4` | BL → `nav` `0x022127BC` |
| `dbltarget2-entry` | `0x02212596` (`0x11DB6`) | BL → `entry_repair` `0x022127AA` (instead of repair `0x022129F0`) |
| `dbltarget2-fallback` | `0x02212A2C` (`0x1224C`) | BL → `first_eligible_foe` `0x02212788`. Repair's single-target fallback only. **New compared with the prototype.** |
| `dbltarget2-cancel` | `0x02212A1A` (`0x1223A`), 4 halfwords | `cmp r4,#4; beq 0x02212A34 (keep); bhi 0x02212A2A (invalid); nop`. Unsigned, so negative values stay invalid; 0–3 are checked as before. |

All other callers of `0x02212784` stay on the native-order entry: `0x0221262E`, `0x02212866`, `0x022128FC`,
`0x02212958` and `0x02212A06`.

### Source

Thumb (armv5te), assembled with Apple clang:

```
clang -target armv5te-none-eabi -mthumb -c opt2.s -o opt2.o
```

The `__bl_mask_*` and `__b_repair` placeholders are filled by the patch generator:

| Placeholder | Becomes |
|---|---|
| `__bl_mask_1`, `__bl_mask_2` | BL to `0x022126CC` |
| `__b_repair` | B to `0x022129F0` (the tail call) |

This layout was assembled and fits exactly (0xA4 bytes). It has **not yet been run** in the host model or the
emulator.

```asm
.syntax unified
.thumb
.text

first_eligible:            @ 0x02212784: native order 0,1,2,3 (spread callers + repair spread branch)
    movs r1, #0xE4
    b 0f
first_eligible_foe:        @ order 3,1,0,2 (vanilla): repair single-target fallback (BL at 0x02212A2C)
    movs r1, #0x87
0:  push {r2-r4, lr}       @ r2's slot = 4-byte eligibility buffer
    adds r4, r1, #0
    mov r1, sp
    movs r2, #1
__bl_mask_1: .short 0, 0
1:  movs r0, #3
    ands r0, r4
    mov r1, sp
    ldrb r1, [r1, r0]
    cmp r1, #1
    beq 2f
    lsrs r4, r4, #2        @ next 2-bit slot; order list ends when no bits are left
    bne 1b
    movs r0, #4
2:  pop {r2-r4, pc}

@ entry into target selection: keep a remembered opposing target (1/3), otherwise invalidate it so the
@ native repair picks the first eligible target (foe first). Tail-calls the native repair; r0 = obj.
entry_repair:
    ldr r1, =0x02255B90
    ldr r2, [r1, #0x14]
    cmp r2, #1
    beq 1f
    cmp r2, #3
    beq 1f
    movs r2, #5
    str r2, [r1, #0x14]
1:
__b_repair: .short 0

@ navigation: r0 = current slot, r1 = dx, r2 = dy -> new slot. Grid 2 cols x 3 rows at 0x0224CD44.
@ Native straight-line search (skip ineligible slots, cancel always accepted, leaving the grid keeps the
@ current slot). New: when a vertical search leaves the grid without a hit, it is repeated once from the
@ same row in the other column, so a move that used to do nothing reaches the diagonal target.
nav:
    push {r3-r7, lr}       @ r3's stack slot is the 4-byte eligibility buffer
    adds r6, r0, #0
    adds r7, r1, #0
    adds r5, r2, #0
    ldr r0, =0x02255B90
    ldr r0, [r0, #4]
    movs r1, #0xfb
    lsls r1, r1, #2
    ldr r0, [r0, r1]
    mov r1, sp
    movs r2, #1
__bl_mask_2: .short 0, 0
    ldr r3, =0x0224CD44
    movs r4, #5            @ grid index of the current slot (last match, as native; none -> 0)
1:  ldrb r0, [r3, r4]
    cmp r0, r6
    beq 2f
    subs r4, #1
    bne 1b
2:  adds r2, r4, #0        @ r2 = start index (bit 3 set once the other column was tried)
3:  movs r0, #1
    ands r0, r4
    adds r0, r0, r7        @ new column
    cmp r0, #1
    bhi 8f
    lsrs r1, r4, #1
    adds r1, r1, r5        @ new row
    cmp r1, #2
    bhi 8f
    lsls r4, r1, #1
    adds r4, r4, r0
    ldrb r0, [r3, r4]
    cmp r0, #4             @ cancel is always accepted
    beq 9f
    mov r1, sp
    ldrb r1, [r1, r0]
    cmp r1, #1
    beq 9f
    b 3b
8:  cmp r7, #0             @ left the grid: horizontal -> stay (native)
    bne 7f
    cmp r2, #8             @ vertical, other column already tried -> stay
    bhs 7f
    movs r4, #1
    eors r4, r2            @ restart from the start row, other column
    movs r2, #8
    b 3b
7:  adds r0, r6, #0
9:  pop {r3-r7, pc}

.align 2
.ltorg
```

Order encoding: 2 bits per slot, lowest first.
- `0xE4` = 0,1,2,3
- `0x87` = 3,1,0,2

The loop ends when no bits are left. That works because slot 0 is never the last entry in either order.

### How it flows

- **Entry:** `entry_repair` writes 5 (invalid) unless +0x14 holds a foe (1 or 3), then tail-calls the native repair.
- **Single-target moves:** the repair, with the cancel patch, sees 5 as invalid and calls `first_eligible_foe` via
  `0x02212A2C`. Turn 1 (+0x14 = 0 after the battle-end clear) therefore opens on TL.
- **Spread moves:** the repair's spread branch still calls the native `first_eligible` (`0x02212A06`), so spread
  behaviour and the engine value are unchanged.

### Build and test steps

1. **Code.**
   - Put the source in a generator next to the prototype's (`asm.py` pattern).
   - Fill the placeholders: BL/B encoders as in the prototype, filler `mov r8,r8` / `0x46C0`.
   - Emit `code_patches.json` entries with `expect` taken from the untouched Chinese overlay 14.
   - Add the five rows above to `code_patches.json`, disabled.
2. **Host model.** A Thumb interpreter running the real bytes:
   - `first_eligible`: equal to the original for all 16 masks (it must stay byte-for-byte equivalent in behaviour)
   - `first_eligible_foe`: order 3,1,0,2 for all 16 masks
   - `nav`: 320 cases, exactly the 11 former stuck cases differ from native
   - repair: 256 cases, CANCEL kept
   - entry wrapper: 224 cases
3. **Test ROM.** Apply only these patches to copies of the Chinese ROM and today's English WIP through
   `hardcoded.apply` (the build's stage 3c), written to a scratch directory. Never write to `work/build/` or
   `work/rom/`.
4. **Emulator matrix (CN and EN).**
   - Trainer 6 double (`TrainerBattle 6 6 0 0`), right foe KO'd and left foe KO'd, both battlers, keys only on
     turn 2.
   - Both foes alive, turn 1: expect TL for the lead.
   - Partner Splash, then lead.
   - Earthquake, plus at least one **field-wide (mode 3)** move and one partner spread move (mode 7).
   - CANCEL via Down, then A, B and re-entry; touch then keys.
   - Single battle unaffected.
   - Wild double, and multi battle `MultiBattle 385 6 8`.
   - Then run the harness suite subset `open,arceus,vqueue` on both test ROMs.
5. **Gate.** Every party edit in tests must wait for a valid checksum (see §6).

## 5. Build plan: option 4 (full vanilla behaviour)

**Goal:** vanilla HeartGold's target-select UX on the hack's engine.

- **Start:** each battler opens on **its own** last confirmed target if that slot is still alive and eligible.
  Otherwise the first alive eligible slot in the order TL, TR, BL, BR. Spread moves open on the box.
- **Memory:** per battler, written only on a confirmed choice (A or touch, not CANCEL or B). Ally picks are remembered
  too.
- **D-pad:** straight line. Cells the move can't target are skipped. Empty foe cells are navigable (4a, vanilla), and
  A or touch on them does nothing.
- **CANCEL row:** keeps the column you came from; Up returns to that column.
- **Spread:** box/CANCEL toggle and the native engine value, unchanged.

### Where the memory goes

The padding bytes `0x02255B91`–`0x02255B93` of the shared struct. All accesses to +0 are byte-sized, no literal points
at +1..+3, and nothing memsets the struct.

| Byte | Meaning |
|---|---|
| `0x02255B91` | lead's memory: slot + 1 for **mode 8**, 0 = none |
| `0x02255B92` | partner's memory: slot + 1 for **mode 9**, 0 = none |
| `0x02255B93` | CANCEL-row column (0 = left, 1 = right) |

Mode 8 is always the lead's single-target move and mode 9 always the partner's. Keying by mode therefore gives
per-battler memory without knowing which battler is acting. Other modes (self, user-or-ally, spread) are not
remembered; vanilla keys on mode too, so a mode change already resets its memory.

**To verify first:** that these bytes are zero at the start of every battle. They're BSS, probably zeroed when
overlay 14 loads; check in the emulator across two consecutive battles. If they aren't, clear them where +0x14 is
cleared (arm9 `0x020DC3B8`) or on battle entry.

Vanilla also clears a battler's memory when a new Pokémon is sent into that position. That reset lives in the vanilla
battle core, which v4 doesn't have, and isn't ported. The alive/eligible check on restore covers the cases that matter
(a remembered foe that fainted falls back to the default).

### What changes

The whole block `0x02212784`–`0x02212A3B` (0x2B8 bytes) is rewritten by hand, keeping every **external entry
address** fixed:

| Keep at | Routine | Called from outside the block |
|---|---|---|
| `0x02212784` | first eligible (native order) | `0x0221262E` |
| `0x02212828` | key handler | pointer in data at `0x0224CE94` |
| `0x02212924` | draw | `0x0221259C`, `0x022125D6` |
| `0x022129F0` | repair | `0x02212596` (redirected to the new entry routine), `0x022125D0` |

Inside the block:

1. **First eligible:** two entries, native and foe order (3,1,0,2), as in option 2.
2. **Navigation (4a):**
   - Build the mask with r2=0 (mode only, so empty foe cells are navigable) and walk straight.
   - In the CANCEL row, Left/Right do nothing and Up uses the column stored at `0x02255B93`.
   - Moving down into CANCEL stores the column you came from.
   - With 4b (option 2's navigation: alive check plus the other-column retry), the cursor never rests on an empty
     slot. The difference between 4a and 4b is the r2 value plus the retry code.
3. **Repair (per-frame validity):**
   - Use the mask with **r2=0** in the single-target branch (the old `movs r2,#1` at `0x02212A14`). Otherwise the
     per-frame repair would snap a cursor resting on an empty foe cell back to a teammate.
   - Keep CANCEL (4).
   - Fall back with foe order. The spread branch stays native.
4. **Entry** (redirect the BL at `0x02212596` to a new routine):
   - Read the mode (request byte 3, as the predicate `0x02212758` does).
   - Mode 8: memory byte `0x02255B91`. Mode 9: `0x02255B92`.
   - If the memory byte is non-zero and that slot is eligible with r2=1 (alive), store slot → +0x14.
   - Otherwise store 5, so the repair picks foe-first.
   - Other modes: option 2's rule (keep a remembered foe 1/3, otherwise foe-first).
   - Then call the repair and return.
5. **Save on confirm:**
   - The BL at `0x02212636` (outside the block; `bl 0x02212A3C` after a successful accept) is the single point
     reached by both A and touch for a real target. CANCEL branches away earlier at `0x022125E2`.
   - Redirect it to a new routine inside the block. If the mode is 8 or 9, write `r6 + 1` (r6 = chosen slot) to the
     matching byte, then tail-call `0x02212A3C`. Preserve r0/r6 as the caller expects.
6. **A on an empty slot needs no new code.** The A result goes back through `0x0221400C` into the state handler's
   accept check (`0x022125BA`–`0x022125DA`, mask with r2=1). It already rejects an empty slot, re-runs the repair and
   redraws, which is vanilla's "A does nothing".
7. **Key handler space:** the handler repeats one ldr/str sequence for each of the four directions. Rewrite it as a
   table or loop over (dx, dy) to free about 0x38 bytes for the memory routines. The spread-mode branches
   (`0x0221285A` Down → 4, `0x02212866` Up → first eligible, `0x022128FC` A → first eligible) must keep their
   behaviour.

### Space estimate (from the vanilla research)

| Part | Bytes |
|---|---|
| First eligible, two entries | ~0x22 |
| Navigation with CANCEL column | ~0x4E–0x60 |
| Entry with restore | ~0x2C |
| Save hook | ~0x1C |
| Literal pools | ~0x10 |

That exceeds the 0xA4 of the old first-eligible and navigation routines by 0x14–0x24, which is why the key handler
(0xFC), draw (0xCC) and repair (0x48) are re-laid out in the same block. The total block is 0x2B8 bytes. Assemble the
full block first and confirm it fits before writing tests.

### Risks specific to option 4

- 21 call sites and the key handler pointer depend on routines in the block; every entry address must stay put or be
  retargeted.
- Making empty foe cells navigable changes what the repair and draw see every frame. Test that drawing a cursor on an
  empty foe panel looks right (vanilla draws it there).
- Memory persistence across battles (see the verification above).
- Touch on an empty slot: the dispatcher writes +0x14 before the accept check, so the cursor moves onto the empty
  slot. Cosmetic, and vanilla-like.
- It is the largest and least-tested change. Build it after option 2 is in place, with option 2's test matrix plus:
  - each battler's memory across 3+ turns
  - an ally targeted on purpose
  - a remembered foe fainting
  - CANCEL-row column from both columns
  - two consecutive battles

## 6. Infrastructure and evidence

- **Option 1 prototype (disabled):** worktree `.claude/worktrees/agent-ab6e9db852b5ad6b7`, branch
  `worktree-agent-ab6e9db852b5ad6b7`, 7 `dbltarget-*` entries in `work/translate/hardcoded/code_patches.json`, all
  `"enabled": false`, uncommitted. `test_hardcoded.py` passes.
- **Generators and tests:** scripts from this session live in the session scratchpad, which is temporary. Copy what's
  needed before it's cleaned up.
  - `fix/asm.py`: the prototype generator
  - `fix/hostmodel.py`: Thumb interpreter tests
  - `fix/make_rom.py`: applies only the targeting patches through `hardcoded.apply`
  - `fix/matrix.py`: emulator matrix
  - `replacement/drv.py`, `scenarios.py`, `wild.py`: replacement, wild and multi scenarios with gated edits
  - `doc/opt2.s`: the option 2 source above
- **Emulator harness gotchas** (`work/tools/emu_harness.py`):
  - Pin the clock.
  - After touch input, the first key press only switches to key mode.
  - Splash opens a self-target screen that needs a confirm.
  - Detect the cursor by counting pure-red pixels (r>200, g<40, b<40) per bottom-screen quadrant.
- **Harness bug (not fixed yet):** `edit_party_mon` races the game's in-place decrypt/encrypt of party data in the
  field. A raw edit can turn a party Pokémon into a Bad Egg (checksum-fail flag), which the battle skips. Gate every
  edit: step frame by frame until the slot decodes with a valid checksum and the Bad Egg flag (flags & 4) clear, then
  edit and re-check. Proposed harness fix:
  - gate in `edit_party_mon`
  - `encode_pokemon` raises on a checksum mismatch
  - same gate in `party()`, `swap_party` and `generate_pokemon`
- **Credit:** the Bradams/Speedoption fork diagnosed and patched the same bug independently. If a fix ships, credit
  the diagnosis in the release notes; no Bradams code is used.

## 7. Decisions still open

1. Fix at all, as a D-1337 exception, and which option: 2 now, 4 later, or 4 directly.
2. If no fix: hack finding, plus the touch workaround in `guide/known-issues.md` and the release notes.
3. Apply the harness party-edit gate.
4. Correct `work/notes/bradams_battle_targeting_analysis.md` (touch does write the remembered target) and the repo
   notes listed under "Where the code came from".
