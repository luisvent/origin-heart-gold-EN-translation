# Bradams fork: code audit and adoption assessment

2026-10-05. This is the implementation-level companion to the [923-message Discord audit](bradams_fork_audit.md). It supersedes that earlier report's uncertainty about whether the **locally available final patch** contains identifiable code changes. Historical attribution, author intent and actual hardware compatibility still need separate evidence.

## Main findings

Speedoption contains a real global pacing toggle, optional trainer difficulty changes, badge-based EXP restrictions, a double-battle targeting repair, a catch-nickname workflow, memory/task changes and six bypass stubs associated with the antipiracy claim. It does **not** contain an independent text-speed control. Some advertised fixes change intentional Chinese gameplay: twenty medicines gain battle availability, and Bounce regains charge-related flags. Additional unadvertised changes remove HM replacement restrictions and guard a photo script.

The patch is not suitable for wholesale import. Some changes are already in our translation, some carry correctness risks, and some contradict our current fidelity policy. The reports distinguish binary facts, control-flow deductions, chat reports and tests still needed. Nothing was imported into production, no modified game was built for release, and no ROM/patch was committed or published.

## Reports by feature

| Feature | Exact implementation and principal caveat | Detailed report |
|---|---|---|
| Global speed toggle | Saved flag706 gates an extra VBlank wait in the main loop; fresh flag is clear/fast. No map/hardware branch. Slow mode still lacks retail's second printer-queue run. | [Speed](bradams_speed_analysis.md) |
| Dialogue speed | Renderer, printer, speed getter/mapper and Options overlay unchanged from Chinese. Global pacing indirectly changes wall-clock printing. | [Speed](bradams_speed_analysis.md#separate-text-speed-negative-finding-with-positive-byte-evidence) |
| Hard mode | Flag536 transforms trainer records on load: rounded ~10% level increase, IV source byte255, AI mask OR `0x030F`. Native postprocessing leaves five IVs31 and HP IV10/20/31 by boosted level; shared readers can affect partners. | [Difficulty](bradams_difficulty_analysis.md) |
| Level caps | Flag705 selects a 17-entry table by total badges. Blocks subsequent battle EXP at/above cap; does not clamp an award crossing the cap. Rare Candy/Day Care paths unchanged. | [Difficulty](bradams_difficulty_analysis.md#level-caps-exact-progression) |
| Settings NPC | 25 event placements; independent, persistent cap/hard/speed switches. Changes apply one question at a time. | [Difficulty](bradams_difficulty_analysis.md) |
| Double-battle targeting | Five overlay14 hook sites: opponent-first default, missing-slot vertical navigation, cancel handling and actor-pointer cursor cache. Cache has ordering/lifetime concerns. | [Targeting](bradams_battle_targeting_analysis.md) |
| Captured Pokémon nicknames | Battle yes/no prompt, PID lookup after capture, 10-character naming UI; boxed captures temporarily borrow last party slot. PID collisions/zero sentinel and raw copy restoration need tests. | [Nicknames](bradams_nickname_analysis.md) |
| Healing items | Exactly20 item records gain battle-pocket bits; no healing calculation changes. Many restrictions are explicitly documented by original author. | [Items and moves](bradams_items_moves_analysis.md) |
| “Two-turn moves” | Only Bounce's live move record changes; four added flags match Fly. Restores charge handling against author's one-turn design. | [Items and moves](bradams_items_moves_analysis.md#two-turn-moves-the-actual-live-data-difference-is-bounce) |
| HM replacement | HM predicate replaced by constant false, bypassing callers' HM-forgetting restrictions. Unconditional convenience change. | [Items and moves](bradams_items_moves_analysis.md#additional-change-remove-hm-classification-for-replacement-guards) |
| Bulbasaur reflection | One branch changes `<=428` exclusion to `<428`, including the first follower sprite. | [Hardware](bradams_hardware_analysis.md#reflection-boundary-precise-one-byte-change) |
| Task capacity | Main queue160→255, +3,040 bytes. Other queues unchanged. | [Hardware](bradams_hardware_analysis.md#task-capacity-increase) |
| Allocation retries | Two new wrappers retry64 times synchronously; no frame wait/cleanup and still return null on exhaustion. | [Hardware](bradams_hardware_analysis.md#allocation-retry-hooks-and-their-limitations) |
| Memory allocation | Root heap3 +32KiB; summary +84KiB; bag +56KiB. Does not establish safe reuse of unused stack space. | [Hardware](bradams_hardware_analysis.md#memory-sizes-and-text-loading) |
| Message loading | Force on-demand banks, already present in our translation. Memory fix, not text-speed repair. | [Hardware](bradams_hardware_analysis.md#memory-sizes-and-text-loading) |
| Antipiracy-associated bypass | Six ARM routines in overlay114 replaced by constant returns 0/1. Does not prove every crash was antipiracy or that all loaders now work. | [Hardware](bradams_hardware_analysis.md) |
| Chain Logger labels | Screen map retiled within unchanged48-tile loader allocation; NoBigText references tiles up to74, Speedoption up to47. Our WIP also respects47. | [Lineage](bradams_lineage_analysis.md#chain-logger--link-capture-graphics-a-real-allocation-repair) |
| Enlarged-text layout |27 lines restore emphasis with safe page boundaries; includes the known Gyarados text-overrun fix. Renderer remains unchanged. | [Lineage](bradams_lineage_analysis.md#text-layout-and-the-gyarados-crash-inherited-fix-is-present) |
| Photo script guard / inherited changes | Separate script and resource lineage analysis distinguishes a new guard from translation-base edits. | [Lineage](bradams_lineage_analysis.md) |
| PC wallpaper workaround | Storage overlay16 and wallpaper archive unchanged from Chinese in Speedoption; discussed repair is absent. | [Hardware](bradams_hardware_analysis.md) |
| Gyarados event | Event script unchanged; known English text-overrun trigger corrected by one-line enlarged text. Inclusion confirmed, authorship and all other crash causes unresolved. | [Lineage](bradams_lineage_analysis.md) |

## Inputs and reproducible comparison

Both locally available xdelta patches decoded successfully against the project's USA HeartGold source (CRC32 `C180A0E9`). This establishes that this source works for these exact patch files; it does not prove that no other source would decode. These are complete alternative patches, not an update chain. No additional patch was downloaded during this audit.

| Input | Role | SHA-256 |
|---|---|---|
| `Speedoption.xdelta` | User-supplied latest beta | `dea9758315c1345e13c1199268cda33517148ab98d3d27526c570b41bf3e8c4e` |
| Decoded Speedoption ROM | Main audit target | `c95961d1b335e351299750676037a1348dfb3f449162dbf3021751c47c4afe3f` |
| Decoded NoBigText ROM | Earlier locally available modified reference, **not a clean base** | `5e7de6aac1a8d83276a709b4a3ab1e3a55d6adff10a890d22b339b10c951dd2b` |
| Untouched Chinese v4.0.3 ROM | Behavioral baseline | `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8` |
| Existing English WIP ROM | Translation snapshot for inherited/change comparison | `592352e0489fa879e4917b4aabce33b28e3215a6a2592d9c8899f16562ccca51` |

The English WIP is an existing built artifact, not proof of the exact current source tree's output. The source registers are consulted separately where necessary. NoBigText's name describes a text presentation choice, not a guarantee it lacks gameplay changes. Exact source commits for the fork's successive bases are unknown.

Methods: decode with installed xdelta3; parse ROM files and NARCs with ndspy; decompress every ARM9 overlay; byte-compare every file/member; decode changed text and scripts; disassemble Thumb/ARM and follow callers/callees; interpret changed data through actual consumers; check settings persistence and native postprocessing; independently model bounded control-flow cases. Scratch data and scripts are under ignored `work/build/bradams-audit/`, with `inventory.json`, `images/*/index.json` and feature subdirectories. These contain game data and must remain untracked.

ARM9 is multi-section: main runtime `02000000`, size `1106A0`; appended Speedoption ITCM runtime `01FF8000`, size `EFC`, stored at ARM9 offset `1106A0`. Do not interpret flat ARM9 offset+`02000000` as the runtime address of appended helpers. For example, the cap getter is `01FF8634`, not `02110CD4`. Overlay14 base is `022007E0`.

### Code-difference inventory

The counts below count differing byte positions and any appended bytes after decompression; they are **not** instruction counts or amounts of new executable code.

| Region | Chinese → Speedoption | NoBigText → Speedoption |
|---|---:|---:|
| ARM9 |2,649|2,448|
| Overlay1 |1|1|
| Overlay14 |13,659|13,325|
| Overlay17 |4|4|
| Overlay44 |1|0|
| Overlay49 |2|0|
| Overlay58 |84|0|
| Overlay114 |48|48|

ARM7 is unchanged. Other decompressed overlays match the Chinese baseline. Overlay14 grows from337,216 to350,500 bytes, but most growth serializes previously zero-initialized BSS (`02252D20–022560DF`); the two cap stubs begin at`022560E0` and`022560EC`. Counting all13KiB as new battle logic would be misleading. ARM9 also contains writable globals, backup buffers and superseded helpers, not just active code.

## What this means for our goals

**Text speed should remain a separate implementation.** There is no dedicated feature to extract from this patch. The fork supplies a global pacing choice that affects field/battle/UI timing together. Our existing text-speed research is independent. If we adopt a pace toggle, test it with each text-speed mode rather than assuming the two are interchangeable or that the slow option recreates retail timing.

**Difficulty can inform our design, but the implementation needs stricter semantics.** Its level boost formula, independent switches and table are recoverable. Its caps only check the level before an award, and its trainer reader has broader scope than strictly enemy trainers. The “maximum IVs” claim fails below level80: unchanged native code overwrites HP IV with10 at levels≤40 or20 at41–79 (31 at80+). The AI bitmask is not synonymous with universally optimal AI. A future implementation should state which battle types are affected, how partners behave, what cap overshoot/alternate EXP sources do, and how difficulty interacts with caps. Those are design and runtime-validation requirements, not changes made here.

**Treat hardware compatibility as a separate possible goal.** Nothing examined establishes that the original developers deliberately removed hardware support. The chat demonstrates some success on New2DS XL/TWiLight and persistent failures on DS/R4; that is platform-specific evidence, not author intent. The reflection and targeting bugs also appear in emulator reports, so their value is not confined to hardware. AP bypasses, heap sizing and task capacity should each be evaluated separately. On-demand text loading is already ours. Tight retry loops and increased allocations are not a substitute for proving memory ownership, free capacity and failure handling on the target loader.

**Do not silently adopt the medicine/Bounce changes as bug fixes.** The author's documentation supports the original restrictions and one-turn Bounce. HM forgetting is another independent convenience choice. These should be explicit optional gameplay decisions if wanted. Current D-1002/D-1337 fidelity remains unchanged by this research task; no implementation decision was recorded on the user's behalf.

**Catch nicknames and targeting are useful candidates with reviewable caveats.** Target navigation models support the missing-slot repair, but cache behavior needs actual battle tests. Nicknames have a substantial custom state machine and boxed-record swap; a safer implementation may use the actual capture destination rather than a PID search. Neither should be copied merely because an opening post calls it fixed.

## Features mentioned in chat without a demonstrated shipped repair

The [chat report's issue inventory](bradams_fork_audit.md#defects-and-requests-without-a-confirmed-shipped-fix) retains message-level evidence for every reported issue. Code inspection does not turn these into confirmed fixes: R4 freezes; later TWiLight crashes; Saffron relearner black screen; post-capture bag failure; building-transition model glitches; erratic enemy HP bars; missing attack audio; Misty's level anomaly; awkward dialogue/quiz answers; removal of affection survival effects; widescreen; Mega completion; expanded evolution information; a repaired/full v3 translation. Some may be indirectly affected by global timing or memory changes, but that is not a targeted verified repair. The intro-credit shortening request was declined. The PC wallpaper change is positively absent from the compared relevant resources.

## Verification achieved and limits

The strongest evidence is the supplied patch's actual instructions, data and unchanged regions, with runtime-address mapping and downstream consumers. Bounded model checks exercise320 targeting navigation cases and16 eligibility masks; the speed-hook interpreter covers8 branch combinations plus counter overflow. These are useful logic checks, not native ARM execution. Archive comparisons confirm all20 item edits and the single live move edit. Detailed reports give byte ranges, hashes and scratch reproduction paths.

A private DeSmuME nickname probe aborted during native startup before reaching gameplay. Consequently this audit has **no successful fresh emulator or physical-hardware validation** of the new features. It cannot establish crash-free play, exact frame-rate ratios, end-to-end naming safety or universal loader support. Original Discord testers' results remain attributed to them. Full AI semantic recovery, all expanded move-flag meanings, obfuscated AP predicate internals and release-by-release ancestry remain bounded uncertainties rather than invented conclusions.

## Additional patches needed

No further download is necessary to identify the final Speedoption mechanisms documented here. To establish which release introduced, lost or restored each change—and inspect the intermediate automatic slowdown—obtain the following complete patches, each for independent decoding against its correct clean base:

1. [AntiPirate.xdelta](https://www.mediafire.com/file/e0lt9juq5tlx7p6/AntiPirate.xdelta/file): highest priority, immediate predecessor retained in the opening post.
2. [PokemonOriginHeartgoldFixed.xdelta](https://www.mediafire.com/file/cy99d5h0q6nr2m9/PokemonOriginHeartgoldFixed.xdelta/file): pre-AP state and claimed targeting restoration.
3. [MoreSpace.xdelta](https://www.mediafire.com/file/xlm0sxc1ak51mfw/MoreSpace.xdelta/file): isolate memory changes and the stack-space explanation.
4. [PokemonOriginHeartgoldBulbaFix.xdelta](https://www.mediafire.com/file/cnilmtdyb4ikrmv/PokemonOriginHeartgoldBulbaFix.xdelta/file): initial reflection/task/targeting release.
5. [PokemonOriginHeartGold.xdelta](https://www.mediafire.com/file/pffgf5kz6xown5u/PokemonOriginHeartGold.xdelta/file): older faster difficulty build.

These URLs are from the export; live availability was not verified. They are research inputs, not five patches to stack or install. Exact Shishio/kakapipi base artifacts or author source/patch scripts would further distinguish inherited work and clarify intent. The unrelated v3 patch is unnecessary for this v4 audit. Repository rules prohibit unsolicited downloads; none of these historical artifacts was fetched.
