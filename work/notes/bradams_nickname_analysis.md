# Bradams fork: captured-Pokémon nickname implementation

2026-10-05. Static ARM9/overlay/script analysis of Speedoption against NoBigText. This is a new catch-nickname workflow, not simply increasing the name limit or enabling the English keyboard. The fork still contains older alternative helpers and scripts; distinguishing live hooks from those leftovers is essential. No production changes were made.

## Active path, from catch to naming screen

1. The battle catch flow calls a new setup helper from overlay14 `0x0222D742` → ITCM `0x01FF8C78`. It calls `0x022167A0` with the existing r7 context to obtain the captured species, stores it at `0x01FF8C74`, sets `0x01FF8C6C=1` (pending prompt), clears `0x01FF8C70` (prompt phase), and sets the original state's word to `0x11` so the prior battle animation/state machine can proceed.
2. Two exits in the battle presentation/update routine redirect to `0x01FF8CA4`: overlay14 `0x02204672` and `0x0220469C`. The first follows comparison of the returned command with `0x5E`; the other is the routine's completion path. This helper deliberately uses the caller's saved r3–r7/pc stack frame on return. It is an inline-exit hook, **not an ordinary standalone subroutine despite the BL encoding**. It can hold the parent state at 4 until the prompt finishes.
3. If no prompt is pending, the helper returns success immediately. If pending, its phase0 prepares a battle message buffer at the existing battle context `+0x500`, selects message **487 (`0x1E7`)**, inserts the saved species through `0x02225DEC`, and displays it. The message in `battle/string/battle_string.narc` bank2 is `Give a nickname to{NEWLINE}{VAR:0101:0,0}?`. Calls to `0x022258A8`/`0x022258EC` start/wait for text; this is an ordinary battle message, not an independent speed control.
4. Phase1 waits until text completes, then calls the existing two-choice UI `0x02213040` with values19/20. Phase2 polls `0x022131A4`; `0xFF` means still waiting. Answer0 stores **1** at `0x01FF8A64`; all other completed answers store **0**. It clears pending/phase state and lets the battle finish. The yes/no constants match the battle UI bank's existing choices.
5. Before the original postbattle updater runs, hooks ARM9 `0x0204FCAE` and `0x020500D2` call `0x01FF8970`. It examines the battle result at context `+0x14`; only result **4** stores the personality value (PID) of index0 of the opponent party at context `+8`. Getter `0x0206D848` is invoked with field0. All other results store PID0. It then still calls the original routine `0x020509BC`.
6. Hooks ARM9 `0x0204FCB4` and `0x020500D8` redirect the normal following task call from `0x020543E8` to `0x01FF8B2C`. The latter reads the saved PID and yes/no result and **clears both immediately**. If PID is0, answer is0, or the player party is empty, it calls the original `0x020543E8` and exits. Otherwise it identifies the captured Pokémon and launches a new naming task.

The two pairs of ARM9 hooks cover two existing postbattle control paths; both perform the same capture bookkeeping and naming dispatch. They do not replace all gift, egg, Name Rater or starter naming mechanisms.

## Locating the caught Pokémon

The implementation assumes a Pokémon added to the party is the **last** party member. It reads player party via `0x0207365C`, gets count via `0x02073398`, and gets `count-1` via `0x0207339C`. It compares only its field0/PID with the captured PID. A match proceeds directly to naming that slot.

If the last party member does not match, it requests save array **41 (`0x29`)** via `0x02027740` and scans raw box records:

- 18 boxes, each beginning `0x1000` bytes after the previous box;
- 30 slots per box, `0x88` (136) bytes per record;
- compares the first 32-bit word of each record against the captured PID;
- accepts the **first** match, with no second identity/checksum/OT/species comparison.

A missing match calls the original postbattle task and does not open the keyboard. It does not search every party slot and does not search beyond those 18×30 box positions.

## How full-party / PC naming works

The standard field naming UI operates on a party member, so the fork temporarily borrows the last party slot:

1. Save the selected box-record address at `0x01FF8844` and the borrowed party-slot address at `0x01FF8848`.
2. Back up **236 bytes** (`0x3B` words) of that party member to ITCM `0x01FF8758`.
3. Copy **136 bytes** (`0x22` words) from the selected box record over the beginning of the borrowed party member. Its remaining100-byte party-only extension is left as it was until restoration; the helper does not construct a fresh coherent party extension for the boxed Pokémon.
4. Store task phase0 and `count-1` at `0x01FF8B20`/`0x01FF8B24` and register task `0x01FF8BFC` through `0x0204F9B8`.
5. Task phase0 resolves that party slot, reads species field5 and current nickname field`0x75`, and calls the existing `CallTask_NamingScreen` at `0x0203EDEC`. Arguments include kind1 (Pokémon), **maximum10 characters**, the selected party index, the current nickname and an output-status pointer at `0x01FF8B28`. The existing field task/state flag at nested context `+0x18 → +0x10 → +0xC` is set to1; the new task advances to phase1 and returns incomplete.
6. When the nested naming task returns, phase1 calls cleanup `0x01FF8928`, then returns complete.
7. Cleanup, if a box pointer is pending, first clears that pointer, copies136 bytes from the borrowed party member back to the box record, then restores the entire236-byte original party backup. With no pending box pointer it is a no-op. The saved party pointer is not cleared, but the cleared box pointer gates its use.

The standard naming task itself writes the chosen nickname through `0x0206DF70`, field`0x76`, at `0x0203EDD0`. Its result-status path at `0x0203ED24` only applies the new name when status is zero; nonzero/cancel statuses skip that write. The fork ignores the returned status but still restores the borrowed party member. Thus copying the boxed bytes back after cancellation is not itself proof of an unwanted rename: the underlying naming task governs whether the nickname changed.

The 10-character argument is explicit in this new wrapper, independent of the existing patched script nickname call at `0x0204291E`. English keyboard and other name-length changes already existed in the translation; they should not be counted as this catch workflow's invention.

## Active globals

| Runtime storage | Purpose |
|---|---|
| `0x01FF8758` … `0x01FF8843` | 236-byte party backup |
| `0x01FF8844` | Box record to receive nickname, or0 |
| `0x01FF8848` | Borrowed party member address |
| `0x01FF896C` | Captured PID, or0 |
| `0x01FF8A64` | Yes/no result, 1=yes |
| `0x01FF8B20`, `0x01FF8B24` | Naming task phase and party index |
| `0x01FF8B28` | Existing naming task's output-status halfword |
| `0x01FF8C6C`, `0x01FF8C70`, `0x01FF8C74` | Pending prompt, prompt phase, captured species |

These are a single shared workspace, not per-capture allocations. The normal serial battle→field flow may make that sufficient, but nested/reentrant use is not defended by this code.

## Older helpers and repurposed script commands

The fork changes three entries of the event-command table beginning `0x020F793C`:

| Opcode | Pointer location | Before | After |
|---:|---:|---:|---:|
| 1 (`Dummy`) | `0x020F7940` | `0x0203FFD1` | `0x01FF8929` (cleanup) |
| 228 (`0xE4`) | `0x020F7CCC` | `0x020431E5` | `0x01FF89A1` (prepare lookup/swap) |
| 229 (`0xE5`) | `0x020F7CD0` | `0x020431F1` | `0x01FF8AF9` (consume answer) |

These are **repurposed existing opcodes**, not new table entries. Original opcode1 simply returned0; original228/229 consumed one halfword and returned1. New228 consumes a variable identifier, obtains its pointer, consumes captured PID, returns variable value0 for no match,1 for last-party match,2 for a box match, and performs the same temporary swap for the latter. New229 writes the yes/no global to its variable and clears that global. New1 runs the box-copy-back/party-restore helper.

Field script file3 adds entries73/74 (zero-based) at byte offsets6152/6215, corresponding to standard scripts2073/2074. They read answer with opcode229 into variable`0x800C`, skip naming if zero, otherwise compute last party index into`0x8004`, fade out, use standard `NicknameInput`, fade in; the boxed version executes opcode1 before releasing control. The older helpers `0x01FF86E8` and `0x01FF884C` contain references to standard IDs`0x819`/`0x81A` (2073/2074). They are **not** the targets of the live postbattle hooks.

A scan of aligned direct Thumb BL targets and literal function pointers across ARM9 and all overlays finds no inbound reference to `0x01FF86E8`, `0x01FF884C` or the older prompt helper `0x01FF8A68`. The active replacement instead uses `0x01FF8970`, `0x01FF8B2C`, `0x01FF8BFC`, `0x01FF8C78`, `0x01FF8CA4`. A control-flow parse of accessible ordinary event-script entries finds opcode229 in the two new file3 scripts, opcode1 at the boxed cleanup, and no opcode228 use. This establishes strong evidence of leftover alternatives, not a mathematical proof against every computed reference or malformed/unparsed script. Do not describe the old helpers' restrictions or script-based screen transitions as the normal final beta path.

## Specific correctness risks exposed by the implementation

- **PID0 is treated as absent.** The code explicitly declines naming when captured PID is0. Whether this can be produced by the hack's catch-generation path has not been reproduced, but the sentinel collision is a definite code property.
- **PID collisions choose the wrong candidate.** It checks only the final party member and then accepts the first boxed PID match. It does not use OT ID, species, checksum, current destination box/slot or the actual newly inserted object's address to disambiguate cloned/colliding PIDs. A duplicate last-party PID wins even if the new catch actually went to a box; an earlier boxed duplicate wins over a later new record. This is a concrete conditional failure mechanism, not an observed user save-corruption report.
- **Temporary mixed party data.** Only the boxed portion is swapped; its100-byte party extension belongs to the original slot occupant during the naming UI. The standard name getters/setter examined here concern box fields, but any other code reading that borrowed party slot while active needs testing.
- **One global backup and raw pointers.** An interrupted or nested flow can lose the restore context; there is no stack of pending swaps or identity recheck before copy-back. The normal completion path does restore all236 bytes and copies only the intended136 boxed bytes back.
- **No allocation-failure checks in this new flow.** It uses the existing naming task's allocations, and does not add new guards around them. Hardware/memory stabilization elsewhere is independent.
- **All script users inherit changed opcode1.** It was a no-op; now it performs pending cleanup. In ordinary use with no pending box pointer it remains harmless, but importers must consider script-level compatibility rather than treating it as a private new operation.

## Runtime attempt and remaining tests

An isolated probe was prepared under `work/build/bradams-audit/hardware/nickname/`, using the existing `Harness` with private emulator configuration and read-only import of `route1_path_2mons.sav`. It intended to exercise the live script handlers for PID0, a matching last party member, a boxed match and complete restoration. DeSmuME aborted during startup with exit134 immediately after rasterizer initialization; it did not reach a game state or execute the probes. There are **no successful runtime nickname test results from this audit**, and no user save was overwritten. The log and probe remain in ignored audit scratch.

Required practical cases are: catch with room, catch with a full party, sayNo, cancel keyboard, unchanged nickname, successful new name, repeated catches, different boxes including the18th, full boxes/no successful catch, PID collision, and checking the borrowed original party member byte-for-byte after completion. Run these on unchanged fork and any isolated implementation before adopting it. A narrower implementation using an explicit capture destination and a dedicated temporary Pokémon buffer would need less identity/party-swapping inference, but that is a future design option, not a change made here.
