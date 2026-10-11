# Difficulty v2: storage, native Options and resident installation handoff

2026-10-09. Bounded research handoff; no implementation or ROM build performed by this researcher. Work from the repository root. Keep the recovered `foundation.asm`, `hooks.asm`, `fix.toml`, `check.py` and `README.md` unchanged. Implement a complete, explicitly opt-in candidate under this research directory and write generated artifacts only under ignored `work/build/difficulty-v2/<scope>/`. Do not modify production tools or unrelated dirty files for this candidate.

## Decision and implementation interfaces

Use the existing **two-byte Options object**, narrowing two existing fields, rather than assigning save-entry-1 padding. Bits 15, 3 and 5 supply exactly the three approved settings. This avoids the historical standalone-Options overread and does not require changing save allocation sizes, entry offsets, checksums or copy lengths.

| Public policy flag | Stored Options bit | Choice when clear | Choice when set |
|---|---|---|---|
| `SHARE_OFF = 1` | 15 (`0x8000`) | Share ON | Share OFF |
| `CAP_ON = 2` | 3 (`0x0008`) | Cap OFF | Cap ON |
| `ITEMS_ALL = 4` | 5 (`0x0020`) | Berries/flutes | All |

`DIFFICULTY_MASK = 0x8028`. Default flags **0** means Berries/flutes, Share ON, Cap OFF. This is the declared default of the optional feature, **not unchanged Chinese-hack item behavior**: All expands availability, while the restricted mode intentionally limits it. There are exactly two item choices, not separate Berry and flute choices.

Recommended source/API boundaries (names can be coordinated, semantics must remain):

```c
/* settings.h / settings.c: portable, same code used by host and ARM tests. */
u32 dg_settings_decode(u16 word);
u16 dg_settings_merge(u16 word, u32 flags); /* precondition flags <= 7 */
/* decode = ((word >> 15)&1) | (((word >> 3)&1)<<1)
 *        | (((word >> 5)&1)<<2)
 * merge = (word & ~0x8028) | ((flags&1)<<15)
 *       | ((flags&2)<<2) | ((flags&4)<<3) */

struct DG_SettingsTxn {
    uintptr_t owner; /* lifetime identity, never serialized */
    u32 epoch;
    u16 original_word;
    u8 original_flags, draft_flags, active;
};
/* Runtime boundary, exactly one aligned Options halfword, never Options+2. */
int dg_options_begin(const u16 *options, uintptr_t owner, u32 epoch,
                     struct DG_SettingsTxn *txn);
int dg_options_apply(u16 *options, uintptr_t owner, u32 epoch,
                     struct DG_SettingsTxn *txn);
void dg_options_cancel(struct DG_SettingsTxn *txn);
```

Reject invalid flags before narrowing, stale owner/epoch, inactive transactions and changed live difficulty bits. A net no-op preserves the current word exactly. A changed Apply merges into the **current** Options word, preserving every unrelated bit even if normal Options changed since opening. Do not replace the whole saved word from `original_word`. Compare the owned mask for staleness; unrelated current bits need not make Apply fail. Store one aligned halfword only after validation. The owner identity/epoch check supplements a valid caller lifetime; it cannot make an arbitrary pointer safe.

The shared shipping arithmetic remains `native/policy.{h,c}`:

- `dg_clamp_exp(current, requested, ceiling, enabled)`;
- `dg_exp_eligible(native_eligible, participated, share_enabled)`;
- `dg_item_battle_mask(item_id, original_mask, all_mask, player_trainer_bag, items_all)`.

Use these helpers from actual wrappers, so FFI tests exercise shipping arithmetic. Growth integration supplies the approved `DG_GrowthSnapshot { u32 flags, cap_level, allowed; uintptr_t root; u32 epoch; }` and `const DG_GrowthSnapshot *dg_growth_snapshot(void)`. Refresh snapshots at proven native owner/context boundaries; clear validity on initialization/reset and owner changes. Do not keep a borrowed Options pointer across teardown. The growth agent's **late, pre-message EXP clamp** is required; an early clamp before later multipliers is insufficient. Special battle/context exclusions remain in runtime wrappers.

## Fresh native inspection and exact compatibility edits

Inspected read-only:

- Chinese input `work/rom/origin_v4.0.3_cn.nds`, SHA-256 `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8`.
- Current available English fixture `work/build/double-target-armips/final/origin_hg_v4.0.3_en_wip.nds`, SHA-256 `a5a418b277bf07390e7282413923ec34f1c364f4a96c88936d65a73a80d51f40`.
- Current `work/patches/text-speed/{native.c,text-speed.asm,fix.toml,payload.json}` and `work/tools/text_speed_patch.py`.

These are inspection identities, not permission to accept every future build with matching nearby instructions. The installer must bind its actual input independently.

Both ROMs have ARM9 main `[02000000,021106A0)`, ITCM at `01FF8000`, and DTCM initialized at `027E0000` (size `0x60`, BSS `0x20`). The English ITCM is `0xFC0` bytes because TEXT SPEED is installed; the old Chinese-only `0x620` assertion must not be copied into the new installer.

### Title field must become one bit

The title row has two selectable values, but native code currently extracts two bits. Fresh disassembly confirms **startup also reads this field directly before calling audio setup**; patching the public getter alone is wrong.

All values below are little-endian **16-bit instruction words**, not byte strings:

| Address | Expected word | New word | Meaning |
|---|---:|---:|---|
| ARM9 `020040B4` | `0680` | `06C0` | Direct startup title extraction: LSL r0,27 |
| ARM9 `020040B6` | `0F80` | `0FC0` | LSR r0,31; pass only bit4 to `0200589C` |
| ARM9 `0202B202` | `0680` | `06C0` | Title getter: LSL r0,27 |
| ARM9 `0202B204` | `0F80` | `0FC0` | LSR r0,31 |
| ARM9 `0202B210` | `0789` | `07C9` | Title setter: LSL r1,31, retain only input bit0 |
| ARM9 `0202B214` | `2230` | `2210` | Clear only saved bit4, preserve bit5 |
| ARM9 `0202B216` | `0E89` | `0EC9` | LSR r1,27, position input at bit4 |

Guard the full enclosing function/dependency ranges in addition to these instructions. In particular inspect `0200403C..020040CC` and `0202B200..0202B220` against the actual input. The startup call at `020040B8` remains unchanged.

Native overlay50 also extracts the local title snapshot at `021E4B18/1A` (r1; words `0689/0F89`) and Cancel audio restoration at `021E4B44/46` (r0; `0680/0F80`). Narrow these to `06C9/0FC9` and `06C0/0FC0` respectively if the modified menu snapshot can contain difficulty bits. Prefer doing so explicitly in compatibility.asm: both are known title consumers, and the guards exist. The existing row preview at `021E5496` calls `0200589C` with a row index; keep the normal title preview, suppress it completely on the Difficulty page.

### TEXT SPEED bit3 is occupied until deliberately freed

Current `native.c` has precisely these semantic dependencies:

1. `fast()`: `((*opts >> 2) & 3) == 1` -> `((*opts >> 2) & 1) == 1`.
2. `load_rows()`: the same two-bit equality populates row6 at state+`0x27E`; narrow to bit2.
3. `commit_speed()`: `*opts = (*opts & ~12) | (m << 2)` -> clear only `~4`.

Two acceptable **isolated** implementation strategies:

- Preferred small-delta option if disassembly permits: guarded `compatibility.asm` edits to the exact emitted mask/shift instructions in the existing pinned ITCM payload. Enumerate **all inlined fast() instances**, including the printer/catch-up consumers, rather than finding one `MOV #12` and assuming completeness. Preserve every symbol address, payload length and unrelated byte. Bind the current source/payload hashes and disassembled instruction contracts. Exact ITCM edit addresses were **not derived in this handoff**; the implementation agent must derive them from `payload.json`/listing and independently validate them.
- Otherwise compile a companion copy with these three explicit source edits, using the existing reproducible clang/link workflow. Relocate all dependent symbol references deliberately. Do not overwrite production `native.c`, payload pins or default registry tools merely to generate this optional candidate.

`text_speed_patch.verify()` deliberately rejects modified payload bytes. Do not claim it passes. The installer needs a compatibility verifier that accepts **only** the declared delta, retains the frame-printer/phone behavior, and verifies NORMAL/FAST for every difficulty combination. Existing source defines unknown text encodings 2/3 as NORMAL; repurposing bit3 changes that old invalid/unreleased interpretation. Document that limitation rather than silently claiming arbitrary old words retain their semantics.

Relevant existing armips source sites:

- ARM9 `0202B176`: current new-game `MOV r0,#4; ORR r1,r0` (words `2004,4301`) sets FAST.
- `0202B1C6/C8`: current music getter masks bits0..1 (`0780,0F80`).
- `0202B1D2/DA`: current music setter masks are `2203/2103`; retain them.
- `020D1A28`: current ITCM arena start is `01FF8FC0`; preserve unless a reviewed replacement actually changes the block extent.
- Overlay50 hooks: `021E4B5A` -> text-speed `exit_free`; `021E4D7C` -> `load_rows`; `021E4DA2` -> `setup_sprites`; `021E5264` -> `load_label`; `021E5284` -> `draw_label`; `021E5366` -> `load_choice`.

### Preservation and initialization findings

These statements are fresh native instruction observations, not completed runtime acceptance:

- `0202B148` allocates **2 bytes**. `0202B168` clears **2 bytes** before initializing normal settings. Zero difficulty bits therefore initialize the approved default, with current TEXT SPEED still setting bit2 FAST. No new persistent record initializer is needed.
- `0202B15C` copies **2 bytes** via `020D3810`; standalone/battle/replay Options copies naturally carry the new bits without enlarging allocations.
- Scene setter `0202B228` only owns bit7; battle style `0202B244` only bit6; background `0202B264` owns bits8..9 (mask literal `FFFFFCFF`); frame `0202B280` owns bits10..14 (mask literal `FFFF83FF`). These preserve `0x8028`. Current music setter owns bits0..1. The narrowed title and text setters must do likewise.
- Replay at `02030668..02030678` performs frame-only halfword RMW; it preserves the other bits, including bit15. The later frame extraction drops bit15.
- The existing saved Options halfword already belongs to initialized, serialized, checksummed save entry1. This design never accesses entry1+2, moves profile+4, or changes the native save entry sizes.

The supplemental halfword shift-pattern census over ARM9 sections/all overlays produced 116 candidates, with the recognized title consumers above. This is **discovery evidence only**, not a proof that arbitrary computed consumers cannot exist. Review actual Options-bearing consumers and byte/word masks, especially bit15-sensitive whole-word comparisons, before acceptance. The existing getter contracts and masked writers give a considerably smaller proof surface than assigning a new trailing object. Do not recycle the historical 48/72 ledger as proof of these new bit semantics.

## Native Options implementation approach

Use the current seven-row engine, with a native Difficulty page selected by **holding L while opening Options** (coordinator permits a documented shortcut; SELECT is an alternative). Prefer this bounded entry mode to live L/R switching in the first implementation. Normal entry remains normal Options including TEXT SPEED. L must merely choose a page; it must not trigger a diagnostic write. Show the shortcut in user-facing candidate instructions and identify the displayed page clearly.

The actual field launch at `0203E530` allocates 12-byte Args on heap11, obtains SaveData through `0203D9E4`, calls Options getter at `0203E544`, stores the Options pointer at Args+4, stores a field interior at Args+8, and dispatches through `0203E520`. The original getter is `02029348`, tailcalling native SaveArray_Get(1) at `02027740`. Keep the shared getter unchanged. A new wrapper at this field call can sample held L and bind the upcoming menu owner, then return exactly the original Options pointer. It must not inherit the historical synthetic transaction dispatcher.

For general runtime readiness, current TEXT SPEED obtains the published runtime SaveData using `02001195` (Thumb), then `02029349`. Its source documents that publication happens after construction/load. The earlier internal global `021D11B4` alone is insufficient readiness: history found it published before layout initialization and left stale on some failure frees. Snapshot roots should use the ready runtime source plus concrete battle/field lifetime checks.

Current overlay50 ABI locators:

| Object / callback | Contract |
|---|---|
| Manager data getter `020071AC` | `void *get_data(void *manager)` |
| Manager data free `020071B0` | Free once after all custom transaction reads/cleanup |
| Menu state+`0x24` | Borrowed live Options pointer |
| State+`0x18` | Native local snapshot assembled from getters; not a separate allocated Options object |
| State+`0x10` low two bits | Exit result: 1 Apply, 2 Cancel path |
| Row value | `u16` at state+`0x86 + 0x54*row` |
| Row6 value | TEXT SPEED at `0x27E` |
| Footer value | `0x2D2`; native footer 0 QUIT, 1 CONFIRM |
| Work allocation | Current TEXT SPEED grows original `0x324` to `0x378` |
| Original row loader `021E5334` | `void load_rows(void *state)` |
| Exit callback `021E4A68` | Native Apply setters start after exit decision; common cleanup at `021E4B58` |

Existing TEXT SPEED source wrappers give ready C ABI references:

```c
void load_rows(void *state);
void *load_choice(void *message_data, unsigned id);
void load_label(void *message_data, unsigned id, void *string);
void draw_label(void *window, unsigned font, void *string,
                unsigned x, unsigned y, unsigned speed,
                unsigned color, void *callback);
void setup_sprites(void *state);
void exit_free(void *manager);
```

Native engine calls already used by these wrappers: string creation `02026865`, string character copy `02026EB9`, message load `0200BB0D`/`0200BB41`, text printer `02020835`, and row/sprite setup `021E5ACD`. Encode project-authored labels using the existing character map/font, as `labels.h` does; do not generate graphic assets.

Implement the page with a private transaction keyed to the current manager/Options owner. Display Items, Share, Cap and clear Apply/Cancel controls; unused normal rows must be hidden/inert, not repurposed as controls that still invoke old audio/background previews. The current seven-row touch geometry and row tables are a starting point, not proof the new screen works. Adjust choice counts, focus/wrap bounds, touch mapping and labels coherently.

Critical exit rule: **intercept before the original six setters and before text-speed commit**, not only at the existing free call. Difficulty Apply validates and merges only `0x8028`; Difficulty Cancel/B/QUIT merges nothing. Both then perform the original resource cleanup exactly once. Normal mode retains the seven existing behaviors and modified narrow TEXT SPEED setter. Avoid calling a naked middle-of-function address from C without reconstructing its expected registers/stack; use a reviewed armips stub or replace the callback with an explicit normal/custom adapter.

Normal preview calls are intentional; they must not leak into custom mode. The old host-dispatched challenge page did leak title/audio preview via `021E5496` and Cancel `021E4B48`, even while preserving saved words. The real implementation must test preview globals/calls as well as stored bits.

Allocation failure should leave normal Options available or return safely without modifying settings. A resident singleton transaction is acceptable only with explicit manager identity, non-reentrancy and teardown invalidation; otherwise append separately allocated state with native allocator/free pairing. Do not insert fields into the current work struct without relocating every affected native offset.

**Not proved here:** final page layout, custom event/input routing, callback ABI/trampolines, row suppression, touch operation, cleanup, user-visible Apply/Cancel or save/reload. These are implementation and test work; old screenshots/allrows results do not establish them.

## Resident autoload and opt-in installer contract

The new feature does **not** need the historical bootstrap marker, startup BL or field-getter diagnostic wrapper. The native loader can initialize code/data and zero BSS. Keep historical files as provenance; install only hooks required by the completed feature.

Use one declared main-RAM reservation below the original ARM7 boundary, e.g. `[023DC000,023E0000)` = **0x4000 / 16 KiB**, or `[023DA000,023E0000)` = **0x6000 / 24 KiB** if measured output needs it. Pick one actual size from the linked artifact and enforce it; never grow silently. Patch arena-high literal `020D1970`, expected `023E0000`, to the reservation start. Existing original BSS `[021106A0,021E4980)` and overlays must remain at their original locations. Never extend the main section into BSS.

Recommended new source boundaries: `native/settings.{h,c}`, `native/options.{h,c}`, `native/runtime.{h,c}`, companion `compatibility.asm`, `native/link.ld`, and a single research-only `build.py`/`install.py` with an explicit JSON contract. The native policy, item and growth modules are separate inputs, not reconstructed historical command output.

Build/install stages:

1. Read and hash a completed current English ROM and all source/compiler/linker/armips inputs. Verify the existing TEXT SPEED input contract, every hook/dependency guard, section layout and overlay bounds. Build in a fresh isolated output directory; reject overwriting inputs or a mismatched prior candidate.
2. Compile freestanding ARM946E-S C with a real ARM ELF linker (local clang + Rust `ld.lld`). Link code/rodata/data/BSS with explicit ranges, stack-usage output and no unresolved relocations/runtime helpers. Generate all public symbol labels from the ELF; preserve ARM/Thumb state bits. Reject unexpected allocatable sections or out-of-region symbols. The executable calls are interworking-aware.
3. Support Mendel's armips item stubs: link C first, compute `ITEM_STUB_BASE = align_up(max(C initialized end, C BSS end), required_alignment)`, provide external C labels, assemble stubs, and import their actual emitted symbols for hooks. Reject overlap with C/BSS and reserve the full stub/literal-pool span. Verify all six item-hook declarations from its `hooks.json`; no unlisted file writes.
4. **Interior BSS pitfall:** if stubs follow C BSS, that BSS cannot simply be represented as the autoload section's trailing BSS count. Materialize the intervening C BSS as zero bytes in the initialized image, include following stubs, and reserve only the final tail as native BSS. Alternatively use separately declared non-overlapping autoload sections. Confirm every C BSS symbol is zero at cold boot and reset. Never overlay stubs on NOLOAD addresses.
5. Stage bounded binary files and patch hooks/compatibility through guarded armips `.open`/`.org`/`.area` operations. No raw undeclared Python instruction patches. Keep source/recovered `.create` test artifacts out of the production-style patch staging contract.
6. Append the declared ARM9 autoload section with `ndspy.code.MainCodeFile.Section(initialized_bytes, base, tail_bss)`, then serialize ARM9 with ndspy. This is explicit installer infrastructure, not a hidden generator side effect. Guard and allow the code-settings autoload bookkeeping words `[codeSettingsOffs, codeSettingsOffs+12)` as required by the actual reconstruction; preserve main size/BSS endpoints and all original autoload sections except the explicitly permitted TEXT SPEED delta.
7. Reopen the output and independently verify exact logical differences: declared main hooks/arena/autoload bookkeeping, declared overlay hooks, one new resident section, narrow ITCM compatibility edits only, all other files/data unchanged. ARM7 binary/overlay table, original ROMs and saves remain untouched. ROM container offsets/header checksums may change when repacking; compare logical payloads rather than promising only a few physical ROM bytes changed.
8. Emit a receipt with input/output hashes, source/tool versions, symbols, all section extents, zero ranges, exact allowed byte deltas, guards, and verification results. Use an atomic final output rename only after validation succeeds. Reject double-install or recognize only an exact already-installed receipt.

The reservation owns executable/data storage independently of transient heaps. It costs arena capacity; verify original initial-low literal (`020D1A1C`, historically `02264920`), current maximum overlay end including BSS, every autoload section and native arena users. Exclude the **whole ARM7 startup/backup span `[023E0000,023F9EF0)`**, not just the loaded ARM7 file. Historical prototypes at/above `023E0000` collided with ARM7 and must not be revived.

Native startup/autoload performs copying, BSS clearing and cache maintenance; the new candidate must freshly demonstrate normal startup and native soft reset follow that path with its actual section sizes. Mutable cache/transaction state must initialize solely from declared zeros/initial values, not a historical marker. Add an explicit invalidation hook only if actual reset/owner lifetime requires it. Heap/arena reserve checks need the English build, especially tight Bag/Summary scenarios; old Chinese capacity numbers are not transferable.

## Persistence and acceptance work

Ordinary native saving handles the unchanged Options entry and native mirror/CRC machinery. Apply changes RAM; only an actual user save persists it. Do not auto-save, auto-upgrade adjacent words or treat emulator state files as battery-save compatibility evidence.

The compact mapping has **no version tag or per-record checksum**. All eight difficulty patterns are valid. Valid old native settings have zero in the repurposed high title/text bits and unused bit15, yielding default0; an arbitrary edited/corrupt old word may look like selected difficulty. Native save CRC/mirror selection remains authoritative. Invalid old title/text encodings cannot be distinguished from new flags without a separate migration marker; do not claim corruption detection or perfect downgrade compatibility. Downgrading can interpret the reused title/text bits as old encodings. Document supported upgrade/downgrade behavior explicitly.

Minimum test handoff:

- Exhaustive **all 65,536 Options words × 8 flags** merge/decode checks: exact preservation outside `0x8028`, canonical flag round-trip and unrelated normal-field extraction. Test setter compositions, initialization/copy/replay and invalid flags before narrowing. Use shipping C and actual assembled compatibility instructions, not only a second Python formula.
- For both legal title values and NORMAL/FAST, all eight flags must preserve audio/title behavior and printer choice. Include the startup direct consumer and normal Options Cancel previews.
- Native user input only for feature acceptance: shortcut launch, visible three settings, each value by D-pad/touch, Apply, B/QUIT/Cancel, away-and-back no-op, reopen, normal Options edits preserving difficulty and difficulty edits preserving all seven normal settings. No host mutation of flags, draft state or callback outcomes in acceptance runs.
- Real native Save with changed mirror counter/valid CRC/serialized Options evidence; fresh-process reload; cold boot/new game; soft reset before Apply, after Apply without saving, and after saving. Preserve original saves; test copied valid legacy and native-corrupt-mirror recovery fixtures. Corrupt-record expectations must match the no-tag format limitation above.
- Actual gameplay hooks consume the selected flags via shared policy; cap at the final pre-message award; all six item hooks and special-context bypasses installed. Menu acceptance alone is not gameplay acceptance.
- Resident bounds, C/stub/BSS layout, ABI/stack, original ARM7 span and tight English heap scenarios observed across menu/battle/overlay/reset transitions. Guard corruption tests fail without publishing a modified candidate. Make test outputs fresh and source-bound; no stale passed result after a failed rerun.

## Historical evidence read, not executed

Index: sibling `poke-difficulty-research/work/research/difficulty-recovery/record-inventory.json`. Exact session paths are in `source_records`; the following are **one-based source record lines**, not commands to run:

| Record | Lines | Useful evidence / limit |
|---|---|---|
| `/root/resident_owner` | 1297, 1334 | Old D640 codec and later halfword/alignment correction; do not adopt this encoding |
| `/root/resident_owner` | 1631, 1702 | Design bridge; global owner equality alone does not prove readiness |
| `/root/resident_owner` | 2785, 2818, 2853 | Linked wrapper/layout/install source; use as loader/ABI evidence only |
| `/root/resident_owner` | 2635 | allrows covered six **existing** settings, not difficulty or today's TEXT SPEED row |
| `/root/resident_owner` | 3047 | Inactive diagnostic chord path, not a user-selectable feature |
| `/root/resolve_storage` | 424, 840 | Host-dispatched page and identified preview leakage; not native UI implementation |
| `/root/resolve_storage` | 1971, 3542 | Entry allocation vs standalone Options distinction; native menu/getter/setter contracts |
| `/root/resident_owner` | 8005, 8304 | Later ownership/callback reports; still incomplete trailing-padding assignment |
| `/root/high_effort_safety_review` | 5945, 6057 | Narrow reader reviews; historical 48 accepted /24 remaining, not current acceptance |
| `root` | 14871 | Last historical 48/24 checkpoint before loss |

Only inert text was extracted to ignored `work/build/difficulty-v2/integration/`; no historical command, recovered script, ROM or emulator test was executed. Fresh disassembly/census evidence is in `cn-native.txt`, `en-native.txt`, `inline-extract-census.json` there. No historical file restoration is needed to implement the selected Options-word design. Remaining work is the explicit companion compatibility, private native page, actual runtime hooks and guarded installation/testing above.
