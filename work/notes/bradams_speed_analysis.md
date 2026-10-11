# Bradams fork: speed and text timing binary analysis

Audit date: 2026-10-05. This is a read-only analysis, not an imported change or compatibility certification. The supplied Discord export, local `Speedoption.xdelta`, and the already available `NoBigText.xdelta` are the evidence set. No patches were downloaded for this analysis.

## Findings that matter for choosing changes

1. **Speedoption implements a persistent global pacing toggle, not an independent text-speed setting.** Flag 706 (`0x2C2`) enables one conditional extra VBlank wait in the game's main loop. Clearing it preserves the Chinese hack's existing main-loop pacing. The option's name, “HeartGold speed,” is an approximation: its implementation does not restore every part of the retail HeartGold loop.
2. **No separate dialogue-speed fix exists in the inspected final fork.** The Chinese fixed-fast getter, delay mapper, printer constructor, asynchronous printer, native renderer, and Options overlay remain byte-identical in Chinese, NoBigText and Speedoption. Ordinary text can become slower in real time when the new global slowdown is enabled.
3. **There is a concrete reason slow mode need not reproduce retail text timing.** Retail USA HeartGold runs the text-printer queue twice per main-loop iteration; Chinese, NoBigText and Speedoption run it once. Speedoption restores the optional extra wait but does not restore the second printer-queue execution. Under the idealized two-VBlank slow path, a printer that advances once per queue visit gets half as many visits per video frame as the corresponding retail loop. This is a scheduling inference, not a measured end-to-end text benchmark.
4. **The final speed hook does not inspect indoor/outdoor map type, a hardware identifier, emulator status, script identity, ladder state, sound effect, HP bar, or EXP bar.** It inspects a frame counter, a save-data pointer, and one saved flag. Location-dependent perceived speed can result from frame load, but the intermediate chat claim about explicit indoor/outdoor policy cannot be attributed to this hook.
5. **Hardware reliability and text speed are separable concerns.** Demand-loaded messages and allocator changes occur elsewhere in the fork; the global speed option does not repair a text buffer, heap, or message parser. The chat's claim that slow mode is required to make scripts work on hardware is not proved by the code inspected here.

## Artifact identities and address convention

| Artifact | ROM SHA-256 |
| --- | --- |
| Untouched Chinese v4.0.3 | `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8` |
| NoBigText decoded from the already available patch | `5e7de6aac1a8d83276a709b4a3ab1e3a55d6adff10a890d22b339b10c951dd2b` |
| Supplied Speedoption decoded against USA HeartGold | `c95961d1b335e351299750676037a1348dfb3f449162dbf3021751c47c4afe3f` |

All code addresses below are **runtime addresses**, unless explicitly called decompressed ARM9 offsets. This matters: the added code lives in an autoloaded ITCM section. Treating the decompressed ARM9 as one contiguous mapping at `0x02000000` gives wrong call targets for that section.

`ndspy`'s ARM9 autoload parsing gives:

| Section | Chinese / NoBigText initialized size | Speedoption initialized size |
| --- | ---: | ---: |
| `0x02000000` | `0x1106A0` | `0x1106A0` |
| `0x01FF8000` ITCM | `0x620` | `0xEFC` |
| `0x027E0000` DTCM | `0x60`, plus `0x20` BSS | same |

The new speed hook is at decompressed ARM9 offset `0x111560`, which maps to `0x01FF8EC0`, **not** `0x02111560`. The shared flag helper at offset `0x110CC0` maps to `0x01FF8620`.

## Exact speed hook and its effect

The only changed instruction in the relevant main-loop block is the four-byte Thumb BL at `0x02000DD4`. Chinese/NoBigText call the existing queue runner `0x02020040`; Speedoption calls `0x01FF8EC0`. The incoming argument is the queue pointer read from `gSystem + 0x24`, the print queue. The hook first calls the original queue runner, preserving that work.

The hook then behaves as follows, expressed as audit pseudocode:

```c
run_original_print_task_queue(incoming_queue);
if (gSystem.frameCounter != 0) return;
if (SaveData_Get() == NULL) return;
if (!check_saved_event_flag(706)) return;
OS_WaitIrq(TRUE, VBLANK);
gSystem.vblankCounter++;
```

| Runtime address | Verified operation |
| --- | --- |
| `0x01FF8EC2` | Calls original queue runner `0x02020040` |
| `0x01FF8EC6` | Loads `gSystem = 0x021D0094` |
| `0x01FF8EC8–0x01FF8ECC` | Reads `gSystem + 0x30`; skips extra wait when nonzero |
| `0x01FF8ECE–0x01FF8ED4` | Calls `0x02001194` and rejects a null save pointer |
| `0x01FF8ED6–0x01FF8EDE` | Loads `0x2C2`, calls flag helper `0x01FF8620`, skips extra wait if clear |
| `0x01FF8EE0–0x01FF8EE6` | Sets both arguments to 1 and calls `0x020CFC2C`, the same IRQ-wait function used by the original main loop |
| `0x01FF8EE8–0x01FF8EEC` | Increments `gSystem + 0x2C`, the VBlank counter |
| `0x01FF8EEE` | Returns |

The surrounding loop still performs its unconditional VBlank wait at `0x02000DE8`, increments its VBlank counter at `0x02000DEC–0x02000DF0`, and clears its frame counter at `0x02000DF2`. This is a selective **additional** wait; it neither removes the original wait nor changes the DS display refresh rate.

The hook executes only on the original main-update path: the existing check at `0x02000DB8` can branch past it to `0x02000DD8`. Consequently “slow mode always doubles every delay” is too strong. When work has already advanced `frameCounter`, the added wait is skipped. VBlank scheduling and render load constrain the realized ratio.

An idealized fast iteration which reaches the original final wait before VBlank has one wait; its slow counterpart can have two. That explains the common “2x” description. It does **not** establish an exact 2x ratio for every scene, a 3x mode, a fixed 30 FPS cap, or a CPU-clock change. The code performs no DS/DSi CPU-clock write.

### Comparison with the user's USA ROM

The USA ROM independently confirms the retail loop structure; the upstream [main-loop source](https://github.com/pret/pokeheartgold/blob/master/src/main.c) provides useful names for the same operations.

| Operation | USA runtime address | Chinese/NoBigText | Speedoption |
| --- | --- | --- | --- |
| First print-queue run | `0x02000DF0` | `0x02000DD4` | Same work through new hook |
| Extra wait if frame counter is zero | `0x02000DF4–0x02000E06` | Absent | Restored conditionally, additionally gated by save pointer and flag 706 |
| Second print-queue run after 3D update | `0x02000E14–0x02000E16` | Absent | Still absent |
| Final unconditional wait | `0x02000E1E` | `0x02000DE8` | Unchanged |

That missing second printer visit is why “HeartGold speed ON” must not be documented as a complete vanilla timing restoration. It can reproduce part of the pacing while retaining different text scheduling.

## Setting, persistence, defaults and old saves

The shared helper `0x01FF8620` obtains the main save pointer through `0x02001194`, gets save block 4 through `0x0204F858`, and calls the existing flag reader at `0x0204F864` with flag 706. The reader selects `block4 + 0x2E0 + (706 >> 3) = block4 + 0x338`, bit 2. This is ordinary saved event-flag storage, not an ephemeral emulator option or an Options-menu bit.

The existing block-4 initialization entry, at decompressed ARM9 offset `0xF310C`, identifies size function `0x0204F841` and initializer `0x0204F849`. The size is `0x474`; initializer `0x0204F848` calls the clearing routine with value zero for the whole block. **A freshly initialized block therefore starts with flag 706 clear: the Chinese fast path.** The difficulty audit's complete reachable Chinese-script scan found no flag operations for 706. This is strong static evidence for a fresh-game fast default, though a from-reset runtime observation was not performed here.

Changing the NPC option sets/clears the flag in live save data; persistence across restart requires the ordinary game save. It does not write a separate settings file or visibly invoke a dedicated immediate-save operation. Existing saves use their existing value at this bit. No migration marker or per-version conversion appears in the speed hook. An imported, edited or unrelated-build save with that bit already set therefore selects slow mode; do not claim every possible old save defaults fast.

The setting is implemented in `a/0/1/2` script member 3, zero-based entry 72 (the 73rd entry; global script 2072), offset `0x16B4`. The new NPC performs level-cap and hard-mode questions before the speed question. At script offset `0x1888`, it tests flag 706:

- Clear: message-bank 38, message 123 asks whether to turn HeartGold speed ON. An affirmative branch sets flag 706.
- Set: message-bank 38, message 122 asks whether to turn it OFF. An affirmative branch clears flag 706.
- The No choice leaves the flag unchanged. The script finishes with message 121.

The decoded comparison treats menu result 1 as No; other returned values take the affirmative branch. Whether a cancellation value is possible for this particular menu command is a separate UI question, so do not call this a proven cancel-to-Yes bug. See the difficulty analysis for placements and full NPC control flow.

## Separate text speed: negative finding with positive byte evidence

The inspected speed getter at `0x0202B1C0` still immediately returns 2. Its delay mapper at `0x0202B1E4` retains the 8/4/1 table and therefore returns 1 for ordinary callers. The adjacent getter `0x0202B1C4` still reads the historical Options low nibble, repurposed by this hack for music speed. No fork change restores a separate text-speed choice there.

The following ranges are byte-for-byte equal across **all three** compared ROMs:

| Region, end exclusive | SHA-256 |
| --- | --- |
| Native renderer/control handling `0x020022D0–0x02002B10` | `f2b0cd7eaabb2b856fce7b25f651c148971f3dd1d742e4ecd1d11629bcb2d6ea` |
| Printer construction/dispatch `0x020208D4–0x02020A9A` | `f092146a47e326fcf1a3a5f89a5f6a08f9809a5b37d850fc44bd3f63ed42f6e7` |
| Getter/mapper `0x0202B1C0–0x0202B200` | `3832008d21e05bef5b393f6c91c22b7d2a14281a2a8945c493488a42bd009bc2` |
| Entire Options overlay 50 | `852d8fcd01bf09ba54bee1a24609e2a82e71d25b5d6dd84c5d919cc0b3418856` |

This is stronger than “the chat does not mention a fix”: the actual relevant code is unchanged. It does not imply identical wall-clock text speed, because the scheduler surrounding that code changed. Nor does it mean every text consumer uses the ordinary getter; scripts and specialized callers can provide their own speed or wait arguments.

The demand-loading instruction at `0x0200BA9A`, also changed in this fork, concerns message loading. The printer consumes a prepared String; it is not a per-character ROM-bank read. Calling that change a dialogue-speed fix conflates loading and printing. See [the existing heap audit](heap_audit.md) for why demand loading is useful for English text.

A separate local research task already implements NORMAL/FAST/INSTANT text batching under `/private/tmp/poke-text-speed-research/work/patches/text_speed/`. Its [research notes](/private/tmp/poke-text-speed-research/work/notes/text_speed_research.md) identify the same engine functions. That work is a separate feature and must be reviewed on its own merits; it is **not contained in Bradams' supplied patch**, and this audit neither modifies nor certifies it.

## Chat claims reconciled with the binaries

| Claim/report | What the code establishes | Remaining limitation |
| --- | --- | --- |
| “Original hack is faster,” older release retains that pace | Chinese and NoBigText lack the additional wait; Speedoption clear-flag path preserves that structure | Does not date every historical intermediate patch |
| “Insides should be slower; left outdoors unchanged” | Final hook has no map or location branch | Requires the actual intermediate release to establish the historical implementation |
| “HeartGold speed ON is slow; OFF is fast” | Correct: ON sets flag 706; only set-flag path adds the wait | Actual ratio depends on frame workload |
| Very slow dialogue and battles | Global extra wait can slow both; absent second printer visit explains a specific difference from retail | No paired runtime measurements or proof that this explains every report |
| EXP-bar slowdowns | Global scheduler affects wall-clock progress of frame-driven UI | No distinct EXP-bar speed repair identified in this speed hook |
| Erratic enemy HP bars | Hook does not inspect or write HP-bar state | Report cannot be called fixed by speed toggle |
| Missing attack/super-effective audio | Hook leaves the original per-loop sound update call in place | Changed cadence may affect timing; no proven fix or causal diagnosis |
| Ladder visual glitch | Hook does not identify ladders or transitions | No targeted ladder fix demonstrated; historical patch needed |
| Hardware requires slow mode to avoid script breakage | Final toggle changes a saved flag and main-loop wait only | Chat speculation, not a proven safety requirement; no physical hardware test here |
| QR-code splash delays should be shortened | This was a request, and the speed hook has no splash-specific handling | No splash-delay feature should be inferred from a general “speed” label |

Relevant Discord anchors: [author's interior/outdoor statement](https://discord.com/channels/1554815898848731217/1555205598860288140/1555428181400621190), [ladder glitch](https://discord.com/channels/1554815898848731217/1555205598860288140/1555428431296995451), [request for separate text speed and HP-bar report](https://discord.com/channels/1554815898848731217/1555205598860288140/1556342656483729429), [speed-option release](https://discord.com/channels/1554815898848731217/1555205598860288140/1556499740193984596), [ON/OFF observation](https://discord.com/channels/1554815898848731217/1555205598860288140/1556615586279325737), [author's final clarification](https://discord.com/channels/1554815898848731217/1555205598860288140/1556623918607896699). These are evidence of statements and reports, not substitutes for code verification.

## Verification performed and limits

Read-only extraction used installed `ndspy`; disassembly used installed Capstone through `.venv/bin/python`. The shared inventory is `work/build/bradams-audit/inventory.json`; decompressed code images are under `work/build/bradams-audit/images/`.

The reproducible local verifier is:

```sh
.venv/bin/python work/build/bradams-audit/speed/verify.py
```

It hashes the four unchanged text/Options regions and executes the bounded hook's decoded instructions in a small purpose-written interpreter, stubbing its existing engine calls. All eight combinations of zero/nonzero frame counter, null/non-null save pointer, and flag clear/set produce the expected path. Every case preserves one original print-queue invocation; only zero counter + non-null save + set flag performs the extra wait and counter increment. A counter wrap case also passes. Output is `work/build/bradams-audit/speed/verification.json`, and the decoded hook is `speed_hook.disasm` alongside it.

This is a static/code-level branch check, **not** execution on an ARM CPU, a DS emulator, or actual hardware. It does not measure VBlank timing, text latency, sound cadence, transition artifacts, flashcart behavior, or script safety. No claim of universal hardware compatibility or complete vanilla timing restoration follows from it.

## What to obtain next

For **the final supplied speed feature**, the current patch is sufficient to recover the implementation above. For **historical attribution**, obtain AntiPirate, OriginHeartGoldFixed, and the older PokemonOriginHeartGold release linked in the Discord audit. Their exact contents would let us isolate the intermediate automatic slowdown from the final saved toggle and determine whether any prior speed change was removed. The exact author source commit or patch-development scripts would be even better evidence for intent and lineage. Do not stack historical patches onto one another without establishing their required bases.

For the user's desired text-speed improvement, no additional Bradams patch should be assumed necessary: the inspected final patch has no independent text-speed feature to extract. Continue the dedicated text-speed work separately, and treat optional global slowdown as its own feature decision. Under the repository's behavior-fidelity rule, importing this global pacing change is a gameplay/engine choice that still needs the user's explicit scope decision; this audit imports nothing.
