# Bradams fork: difficulty, caps and settings binary audit

2026-10-05. Read-only analysis of locally decoded Speedoption, untouched Chinese v4.0.3, and the supplied NoBigText reference. No gameplay change implemented. This report distinguishes code facts from runtime behavior that still needs a fixture. The companion fork audit contains the Discord message citations. Scratch disassembly and investigation scripts are under ignored `work/build/bradams-audit/difficulty/`.

## Addressing and evidence

Use runtime addresses below, **not** ARM9 file offsets interpreted as RAM. `NintendoDSRom.loadArm9()` reports a main section at `0x02000000`, length `0x1106A0`, and an appended ITCM section loaded at `0x01FF8000`, length `0xEFC`. For example, the cap getter is at runtime `0x01FF8634`, stored at ARM9 offset `0x110CD4`. Overlay 14 loads at `0x022007E0`. Disassembly in `section0.txt`, `section1.txt`, `speed_ov14.txt`, and `script3.txt` uses the correct runtime addresses. Earlier flat whole-ARM9 disassembly in scratch is not a valid runtime address reference for the appended code.

## What hard mode actually does

The implementation changes trainer data **when read**, using two patched ARM9 veneers:

| Address | Behavior |
| --- | --- |
| `02072700` | Move trainer index to r2, destination to r0, select archive `0x37`, branch through literal `01FF8675` |
| `02072710` | Same for archive `0x38` |
| `01FF8674` | Read original record with `02007424`, then conditionally alter loaded record |
| `01FF8620` | Get save pointer (`02001194`), flags block (`0204F858`), test requested flag (`0204F864`) |

The low bit in `01FF8675` selects Thumb mode. Hard mode tests event flag `0x218` (536). Clear means the original read remains unchanged. It does not rewrite the source archive, the player's team, or existing Pokémon in storage.

For trainer headers (archive `0x37`), the helper reads the halfword at destination+`0x0C`, ORs it with `0x030F`, and writes it back. Those exact added AI bits are 0, 1, 2, 3, 8 and 9; existing bits survive. This is not a replacement of the entire AI field with all bits set. “Strongest AI” is the author's shorthand, not a verified ordering of every AI strategy. Per-bit behavioral names and actual decision quality require tracing the hack's AI interpreter; this audit does not import vanilla names as proof of the modified hack's semantics.

For parties (archive `0x38`), the helper reads the corresponding header into its stack buffer, takes the party count from byte3, clamps it to six, and processes 28-byte (`0x1C`) records backwards. At each record it writes `0xFF` to byte0 and changes the halfword level at+6. The downstream constructor at `020727F8–0207281E` computes `31 * byte0 / 255` and passes the result to the Pokémon constructor. Thus 255 initially produces IV31. **However, the advertised six-max-IV result does not survive the full constructor:** unchanged code at `020728E0–02072912` later sets HP IV to10 for the boosted level≤40,20 for41–79, and31 for≥80. Its six-iteration loop repeatedly sets field70 (HP), rather than incrementing the stat field. Those bytes are identical to CN. Final ordinary trainer construction therefore gives five IVs31 and the original tiered HP IV, not six IVs31 below level80. This follows the source behavior documented in `trainer_runtime_review.md`; the fork did not repair it. No EV editing is performed by this helper. There is an additional dependency: the original constructor reads byte0 and level into its personality/RNG seed calculation at `020727B8–020727C8`, before the explicit IV conversion. Changing these fields can therefore also change generated personality-dependent outcomes through the unchanged constructor; the hook does not separately preserve the previous seed. Exact nature/ability/gender outcomes need constructor-specific fixtures rather than assuming that only displayed level and IVs change.

Exact level transform, for L < 100:

```
boost = max(1, ((L + 5) * 205) >> 11)
new_level = min(100, L + boost)
```

The reciprocal arithmetic implements rounding of roughly ten percent, rather than truncating `L * 1.1`. Over the legal 1–99 input domain it equals `L + max(1, floor((L+5)/10))`, capped at100. Examples: 1→2, 6→7, 12→13, 15→17, 25→28, 38→42, 55→61, 80→88, 90→99, 99→100. An existing level of100 **or above** skips level editing; IV editing still occurs. No minimum-level validation is added.

Relevant helper instructions are `FF20 1870` at `01FF86C0` (IV255), `D888` at`01FF86C4` (level read), `411D CD22 5143 C90A` at`01FF86CA` (boost arithmetic), and `D880` at`01FF86DE` (level write). Header AI modification is at`01FF8692–01FF869C`.

### AI follow-up: what the consumer trace establishes

The trainer header's AI field is a32-bit word at+`0x0C`; Bradams modifies only its low halfword and preserves the upper16bits. The original loader at`0207257C` calls the patched header reader, then`02072580–02072592` copies all52bytes into battle setup+`0x28 + trainer_slot*0x34`. Therefore the modified word reaches setup+`0x34 + trainer_slot*0x34`, rather than remaining confined to a temporary read buffer. The other native metadata accessor at`020725F4`, selector8, returns the full32-bit header word using`LDR r4,[sp,#0xC]` at`02072646`.

A bounded follow-up searched the local source assets and traced candidate native header/field consumers through ARM9 and overlay14. It did **not** establish the hack's final AI dispatch from that setup word or isolate the individual behavior of bits0,1,2,3,8,9. In particular, reading an AI mask into battle setup does not prove that all those bits are consumed by the hack's current interpreter, nor that their union is a monotonic difficulty increase. Existing custom battle code differs enough from vanilla that assigning vanilla flag labels without a verified dispatcher would be misleading. The current binary-proven description is **“OR0x030F into each intercepted trainer's AI metadata”**, not “verified strongest AI.” This remains an explicit unresolved reverse-engineering item: identify the final strategy selector, follow each selected branch/script, and test actual move decisions on controlled states. No missing patch is known to supply source symbols for that work.

The reciprocal level formula was exhaustively checked for every legal input1–99: `((L+5)*205)>>11 == floor((L+5)/10)` throughout that domain. The HP-IV constructor override was independently byte-compared between CN and Speedoption and is unchanged, as described above. These two conclusions are stronger than the still-unresolved per-bit AI semantics.

### Scope and limitations

The helper contains no trainer/wild/facility/link/player/partner classification; its scope is callers of the two archive readers. Direct ARM9 callers include `0207257C`, `020725FC` (header) and `02072764` (party). Overlay14 also calls them at `0222C1DE` and `0222C1E6`. A trainer, partner or special battle using those readers gets transformed; one using a different constructor does not. The statement “all opponents get this” is broader than what these hooks prove. Wild encounters are not modified by these particular hooks. Do not assume partners, Frontier rentals, link Pokémon, scripted enemies or generator-created Pokémon are covered or excluded without checking their actual constructors.

The report of a level6 Misty Psyduck cannot be explained as this multiplier turning a normal high-level Pokémon into level6: it only raises legal levels. A missing flag, different constructor, different release, original data or another bug remains possible.

## Level caps: exact progression

Getter `01FF8634` checks flag`0x2C1` (705); when clear it returns100. When enabled it gets profile data through `0202933C`, calls `02029480`, clamps the returned count to16, and indexes 17 bytes at`01FF8660`:

| Total badges | Cap |
| --- | --- |
| 0 | 12 |
| 1 | 20 |
| 2 | 25 |
| 3 | 38 |
| 4 | 55 |
| 5 | 65 |
| 6–11 | 80 |
| 12–13 | 85 |
| 14 | 88 |
| 15 | 93 |
| 16+ | 100 |

Raw bytes: `0C 14 19 26 37 41 50 50 50 50 50 50 55 55 58 5D 64`.

`02029480` explicitly counts set bits in profile bytes+`0x1C` and+`0x1F`. This is a **total badge count**, not a route, trainer-defeat, story milestone or badge-identity lookup. There is no condition for underground executives, Erika, Elite Four or Champion beyond whatever badges the profile already contains. The reported cap38 stall therefore corresponds exactly to a three-badge profile under this release's table; whether that player's story should already have awarded another badge needs the save and exact release. It is not proof of a malfunctioning cap getter.

Caps and hard mode are independent flags. Turning hard mode on does not raise the cap table by10%; for example, the initial player cap12 coexists with a normal level12 trainer raised to13.

### Enforcement: two battle hooks, not a universal cap

1. At overlay14 `02218896`, the previous current-level/100 comparison is replaced by `BL 022560E0` (`3D F0 23 FC`). The stub preserves r0–r3, copies the original level into r7, calls cap getter `01FF8634`, compares r7 against cap and returns those condition flags. The caller's unsigned-below branch at`0221889A` admits EXP growth only while current level < cap. Existing at-cap and above-cap Pokémon receive no growth through this path; they are not downleveled.
2. At `0221F716`, a level getter call is replaced by `BL 022560EC` (`36 F0 E9 FC`). That wrapper calls the original `02218104`; if actual level >= cap it returns100, otherwise actual level. This causes the existing comparison to100 at`0221F71A` to take its already-maxed branch, suppressing this EXP presentation/output path. It does not change the Pokémon's actual level.

**The first hook does not clamp an award that crosses the cap.** For below-cap Pokémon, code`022188A2–022188BA` adds the entire award to cached EXP and writes it to the backing Pokémon, then executes the original stat/level recalculation (`0206D558` at`02218914`). There is no lookup of EXP-at-cap and no subtraction of excess EXP. A sufficiently large award can therefore move a below-cap Pokémon above the cap in one operation. This is a static control-flow finding, not a reproduced emulator test. It is material to any adoption: a cap-1 fixture with a large reward must be tested, including evolution, move learning and the EXP bar.

Neither new helper filters battle category or owner. It also reads the live save badge count on demand instead of freezing a resolved policy at battle start. These facts matter for any proposal to reuse it in a more general challenge system.

### Nonbattle growth remains uncapped by these changes

The following Speedoption ARM9 ranges are byte-identical to untouched CN:

| Range | Established native path |
| --- | --- |
| `0208F51C–0208F79B` | Item eligibility, including Rare Candy |
| `0208FA50–0208FC3F` | Item effects including Rare Candy level increase |
| `0206B274–0206B43F` | Day Care withdrawal, level preview and price neighborhood |
| `0206BFB4–0206C04F` | Day Care accumulation neighborhood |

These identities, together with the exclusively overlay14 cap-hook placement, establish that the patch does not add the corresponding cap guards to those native nonbattle paths. Rare Candy and Day Care remain bypass candidates; native fixtures should confirm the resulting UI, item consumption and final level. Captures, gifts, trades and already-overleveled saves are likewise not downleveled by either helper. There is no strict team-admission rule.

## Settings NPC, storage and placements

The added standard script is global script2072, zero-based entry72 (73rd entry) of archive`a/0/1/2` member3, beginning at byte`0x16B4`. It plays the interaction sound, locks actors, faces the player and sequentially asks about caps, hard mode, then speed. It uses message bank38:

| Message | Purpose |
| --- | --- |
| 116 | Adventure-settings introduction |
| 117 / 118 | Caps currently ON: turn OFF? / currently OFF: turn ON? |
| 119 / 120 | Hard mode currently ON: turn OFF? / currently OFF: turn ON? |
| 122 / 123 | HeartGold speed currently ON: turn OFF? / currently OFF: turn ON? |
| 121 | Completion, with invitation to return |

At each question, menu result1 leaves the setting alone; the affirmative route sets/clears that option's flag immediately. This is sequential immediate mutation, without a final Apply/Cancel transaction. Hard mode and caps have no separate numeric readout or descriptions of AI, IVs or the cap schedule in this dialogue.

Flags are ordinary persisted event flags: hard `0x218`, caps `0x2C1`, speed `0x2C2`. In save block4, using flag base+`0x2E0`, these occupy byte`0x323` bit0 and byte`0x338` bits1/2 respectively. The native block initializer at`0204F848` zeroes`0x474` bytes (block table row at ARM9 offset`0xF310C`), so newly initialized flag storage starts with all three off. A complete reachable CN script scan found no CheckFlag/SetFlag/ClearFlag uses of these three ids. This is evidence for unused script flags, not a blanket proof that every native initializer, save migration or external tool leaves them untouched. Old imported saves should be checked rather than force-reset.

Twenty-five event archives add one NPC, sprite341, movement17, script2072, visibility flag0 (always present), facing0 and no roam radius. Member61 (zone64) places it at(11,6); the remaining24 place it at(1,16). Exact event member→zone mapping:

```
61→64; 66→69; 78→81; 153→158; 160→166; 163→169;
178→185; 196→203; 212→226; 222→236; 232→246; 264→293;
315→358; 350→393; 363→407; 383→428; 389→434; 420→466;
428→475; 435→482; 453→501; 460→508; 463→511; 466→514; 480→528.
```

The zone table identifies zone64 as the Pallet Town player-house upper floor, zone203 as One Island (the vanilla constant misleadingly says Bill’s House), and the rest as Cherrygrove, Ecruteak, Violet, Azalea, Route32, Goldenrod, Olivine, Cianwood, Mahogany, Blackthorn, Vermilion, Celadon, Saffron, Cerulean, Lavender, Route10, Pewter, Fuchsia, Viridian, Cinnabar, Route3, Mt. Silver and Frontier Access Pokémon Center locations. Resolve map identities through the repository's zone table, not vanilla file labels. This inventory makes NPC-placement testing reproducible, including the starting-room report. No new event visibility flag is allocated for the NPC itself.

## Related mentions and adoption implications

The generator predates these difficulty hooks: the Discord's X+Select creation feature is not established as a new difficulty addition, and this trainer archive wrapper does not implement an existing-Pokémon IV editor. The appended nickname/boxed-Pokémon interaction changes should be evaluated separately in the fork's interaction audit. No affection-removal behavior exists in the difficulty/cap helpers above; the Discord request should remain “not established as shipped” unless a different battle patch is identified.

The current repository's `code_patches.json` does not implement this difficulty/cap scheme. Separate worktree research under `/private/tmp/poke-difficulty-research` has a much broader policy and save-memory investigation; its `difficulty_exp_caps.md` specifically documents the same EXP seam and the need to clamp the **accepted award**, plus Rare Candy/Day Care safeguards. That work is distinct from this fork and is not validation of the fork's implementation.

Useful candidates to carry into our design review are the two trainer-reader seams, exact IV conversion, the badge-count cap as an explicitly limited reference, and the two EXP-related hook locations. Do not copy the Bradams cap as a complete implementation: it lacks partial-award clamping and nonbattle enforcement. Do not describe its AI mask as universally optimal or its effects as restricted only to enemy trainers without constructor coverage. Adoption would also need legacy-save defaults, native flag collisions, injected-code memory ownership, real trainer/partner/facility contexts and old-save behavior tested. This audit makes no production changes and does not supersede the user's existing gameplay-fidelity decisions.
