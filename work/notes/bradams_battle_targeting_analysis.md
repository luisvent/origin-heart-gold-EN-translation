# Bradams fork: battle selection and missing-target navigation

2026-10-05. Static audit of decoded Speedoption against untouched CN and NoBigText. The five hook neighborhoods below are identical in CN and NoBigText; Speedoption changes them. No production code/data changed. Supporting disassembly and executable host-model checks are in ignored `work/build/bradams-audit/difficulty/battle/`. Host-model tests are not emulator, touchscreen or real-hardware tests.

## Inventory

All overlay addresses refer to overlay14, runtime base`022007E0`. Injected routines reside in the ARM9 autoloaded ITCM section at`01FF8000`, not at the flat file-offset-derived address.

| Hook | Original bytes/behavior | Speedoption bytes/behavior |
| --- | --- | --- |
| `02211E3E` | `09 06 09 0E`: narrow r1 to a byte | `E6 F5 D1 FF`: BL`01FF8DE4`, narrow plus cache/restore menu cursor by actor-object pointer |
| `02212596` | `00 F0 2B FA`: BL`022129F0` generic target repair | `E6 F5 73 FC`: BL`01FF8E80`, prefer a valid opponent when previous target isn't1/3 |
| `02212786` | Set up availability buffer and call native mask builder; scan0,1,2,3 | `E6 F5 65 FB` followed by early return at`0221278A`: delegate to`01FF8E54`, scan1,3,2,0 |
| `02212812` | `C8 5C 01 28`: check direct target availability==1 | `E6 F5 CF FA`: BL`01FF8DB4`, add opposite-column fallback for vertical navigation |
| `02212A1A` / `02212A20` | signed `<0` and `>=4` invalidate target | unsigned `>4` invalidates, exact4 is preserved |

These are separate fixes, affecting remembered command-menu position, target initialization, directional target navigation, and the cancel sentinel. They should not be collapsed into “double battles fixed” without describing which failure each addresses.

## Target eligibility is inherited

Native`022126CC` fills four bytes, one per target slot. With r2=1, it first calls`022196AC(slot)` and sets availability0 if the slot fails that native check. Otherwise it selects the row indexed by request byte3 from table`0224D060` and copies the per-slot value. The fork's new helpers call this existing builder with r2=1. They do not mark every opponent targetable, bypass move-specific eligibility, resurrect fainted battlers or alter battle ownership.

The original first-target helper`02212784` returns the first slot whose eligibility is exactly1 in index order0,1,2,3; if none, it returns4. The replacement`01FF8E54` performs the same exact-1 test in order **1,3,2,0**, read from bytes`01 03 02 00` at`01FF8E50`. Thus eligible opponent positions1/3 take precedence; the remaining slots are fallbacks only when both preferred positions are unavailable. Slot4 remains “no target/cancel”, not a fifth battler. This is preference among eligible slots; it does not force an opposing slot for a move that cannot target one.

`01FF8E80`, called while entering target selection, reads remembered target from`02255B90+0x14`. If it is1 or3, the old native repair routine validates it. Otherwise it immediately selects the first eligible target using the new ordering and stores it. Consequently a remembered ally or cancel position does not remain the initial target when entering this path; a remembered valid opposing target can survive. The old repair routine still checks the native target-mode predicate`02212758` and eligibility; the fork does not replace those policy decisions wholesale.

## Why a missing slot blocked directional selection

The native navigation grid at`0224CD44` is unchanged in all three ROMs:

```
row 0:  slot3   slot1
row 1:  slot0   slot2
row 2:  cancel4 cancel4
```

`022127A4` finds the current slot's grid coordinates, adds horizontal/vertical deltas, bounds-checks a two-column/three-row grid and examines the destination. An out-of-bounds move returns the previous slot. Cancel4 is accepted before eligibility lookup. An unavailable slot causes another step in the **same direction**.

That original behavior cannot reach a valid diagonal target through an absent direct neighbor: it skips the entire row without looking at the other column. For example, slot2 pressing Up when only slot3 is eligible first encounters unavailable slot1, then exits the grid and returns slot2. Slot0 pressing Up when only slot1 is eligible similarly stays on slot0.

The injected`01FF8DB4` first preserves the old direct-slot test. If the slot is unavailable and horizontal delta r7 is nonzero, it returns “invalid” exactly as before. With horizontal delta zero, it probes the **other column in the same destination row** (`r4==0 ? column1 : column0`). If that alternate slot is eligible==1, it changes r3 to that slot and returns equality flags; the caller accepts it. Otherwise it returns unequal flags, and the original loop continues. r4 is saved/restored, so the fallback does not corrupt the navigation coordinate held by the caller. r3 is intentionally the selected target result. Cancel rows never reach this helper because the caller accepts4 first.

Concrete before/after:

| State/action | CN / NoBigText | Speedoption |
| --- | --- | --- |
| At slot2, Up, only slot3 eligible | Remain slot2 | Select slot3 |
| At slot0, Up, only slot1 eligible | Remain slot0 | Select slot1 |
| At cancel4, Up, only slot0 eligible | Remain cancel4 | Select slot0 |
| Direct neighbor eligible | Select it | Same |
| Horizontal move into absent target | Continue same horizontal search | Same |
| No eligible battler anywhere | Native bounds/cancel behavior | Same bounds/cancel behavior |

This addresses a real missing-slot topology, not a battle-damage or trainer-AI issue.

## Cancel sentinel correction

Native repair at`022129F0` previously treated r4<0 or r4>=4 as invalid and selected a new target. Speedoption changes the ordinary branch to unsigned r4>4 → repair, r4==4 → keep, then checks eligibility only for0–3. This preserves the cancel sentinel without indexing the four-byte availability array at index4. Negative bit patterns remain invalid under the unsigned comparison. The earlier special target-mode branch already handled exact4 separately, and remains intact.

This correction does not mean cancel is retained at every entry point: the new entry wrapper above intentionally replaces a non-opponent remembered target, including4, when entering target selection. The distinction is initial selection versus subsequent repair/navigation.

## Command cursor cache: exact mechanics and unproven edges

The cache is for global`02255B90+0x10`, distinct from target slot at+0x14. The key is the word at`[global+4]+0x1F4`, an actor-object pointer, not a saved trainer ID. Evidence: native setup`02211774` stores incoming r0 there at`02211780`, then passes it to`022167A0`, which dereferences object byte+0x14; other native callers dereference further actor fields through this same word.

The injected helper uses:

- `01FF8D8C`: last-seen actor pointer;
- `01FF8D90`: replacement counter;
- `01FF8D94–01FF8DB3`: four `(pointer, cursor)` pairs, eight bytes each.

On a key change it writes the new last-seen pointer, scans the four entries, and restores the matching cursor to global+0x10; an unknown pointer restores0. It does not save incoming cursor under the previous pointer on that branch. On subsequent calls with the same key it updates that key's cached cursor, creating an entry using `(counter++ & 3)` if absent. This is round-robin insertion, not least-recently-used eviction.

A subtle control-flow limitation deserves runtime coverage: on key change the helper updates the **global cursor**, but returns the old incoming narrowed r1. The caller immediately dispatches directional input based on that old r1 at`02211E42`, and its branches may write a new cursor to the same global. Later`02211EF2` rereads the global and compares it with r1, allowing redraw of a restored value. With no directional input, this can display the restored cursor correctly; with directional input on the very first actor-change call, a branch based on the previous actor's cursor can overwrite it. This is a concrete ordering risk, not a demonstrated gameplay failure.

Likewise, the cache helper has no battle-end clear, pointer-generation tag or stale-pointer rejection. Fresh ARM9 autoload initializes this storage, but a reused actor allocation address in a later battle can match a previous cursor entry. Whether cross-battle retention is intentional and whether actor addresses are reused need native fixtures. Four entries fit a four-battler scenario but do not establish safe behavior for every allocation lifecycle. Do not describe this as proven persistent per-Pokémon cursor storage.

## Verification performed and remaining coverage

`static_tests.py` transcribes the observed grid traversal and injected fallback. It exhaustively checks16 binary availability masks ×5 current positions ×4 cardinal directions = **320 cases**. Speedoption differs in21 cases; every new result is either the original current position, cancel4, or an eligible slot. All cases terminate. It also checks all16 masks for the new first-target ordering, verifying that an eligible1/3 always wins before2/0. Explicit assertions cover both missing-opponent-column examples above. The tests deliberately include starting positions that have become invalid, as happens during changed battle state. They do not exercise nonbinary table values, diagonal/zero input deltas or native callbacks; actual cardinal navigation is the modeled scope.

These checks support the intended single/double-slot navigation semantics but do not prove UI integration. Required native cases include one opponent remaining in each column; both controlled actors; targetable ally moves; spread/self moves; Cancel then re-enter; touch versus D-pad; fainting/replacement between commands; first-frame held input when switching actor; new battles reusing actor pointers; and switching different battle types. Existing Discord confirmations are separate player evidence, not substitutes for those controlled cases.

The missing-slot fallback, first-target preference and sentinel bounds changes are small, intelligible candidates for review. The four-entry command cache deserves independent native validation before copying. These are original-hack behavior changes and require the project's existing gameplay-fidelity policy to be addressed explicitly before adoption; this report implements none of them.
