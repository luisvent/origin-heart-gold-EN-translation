# Native Difficulty page implementation handoff

2026-10-10. Sole scoped implementation agent; no subagents, downloads, ROM build,
ROM/save writes, or historical command execution. **Implemented and compiled;
native display/input/save/reset acceptance remains unproved.** Do not mark this
as feature acceptance from the host callback checks or a preparation-only runner.
Installer, integrated native tests, GPT6 Astra review, and fixes remain serial
parent-owned steps. Candy/runtime/provider/progression are outside this module.

## Owned source and integration interface

- `native/settings.h`, `native/settings.c`: portable two-byte codec and transaction.
- `native/options.h`, `native/options.c`: actual native page, lifecycle adapters,
  input, game-font drawing, explicit host ABI seams.
- `native/options.asm`, `native/options_hooks.json`: nine hooks and nine eight-byte
  tail thunks. Full native ABI and expected original bytes are in the JSON.
- `compatibility.asm`, `compatibility.json`: 24 guarded halfword edits, full
  current EN/CN section hashes and enclosing dependency hashes.
- `research/options-source-pins.json`: source/tool/input identities and local
  output hashes; pins this handoff, not a general-purpose future fixture waiver.

No production TEXT SPEED/tools, foundation files, policy/growth, translation
banks, existing research, or decision register were edited. Generated files,
extracted binaries, scratch tests, ELF/map/listings and staged copies are confined
to ignored `work/build/difficulty-v2/options/`.

The installer links `settings.c` and `options.c` with the other modules. They
have no unresolved helper/runtime symbols and need no external C provider.
`policy.h` supplies only logical flag constants. Do not compile the host-test
macro in the resident payload. All public APIs are in the two headers.

`dg_settings_decode(word)` returns SHARE_OFF=1, CAP_ON=2, ITEMS_ALL=4 from
stored bits15,3,5. `dg_settings_merge(word,flags)` preserves every other bit;
invalid flags leave the word unchanged. Transaction setters/apply return explicit
errors before any truncation or store. `DG_SettingsTxn` is private, zero-created,
not persisted: owner, exact Options identity, nonzero epoch, original mask,
wide draft_flags, active. Begin refuses replacing an active transaction. Apply
rejects stale ownership/epoch/object or changed live difficulty bits, merges
into the current word, and performs exactly one aligned halfword store only for
a net change. A no-op performs no store, including when unrelated fields changed.
Apply consumes a successful transaction; error leaves it active for cancellation.
Cancellation clears every field. No read or write at Options+2 is performed.

## User flow and native route

**Hold L while opening Options from the field menu** for DIFFICULTY. Ordinary
entry retains all seven Options rows, including TEXT SPEED. The displayed rows
are ITEMS (`Berries/flutes` / `All`), SHARE (`ON` / `OFF`), CAP (`OFF` / `ON`).
Default flags0 is Berries/flutes, Share ON, Cap OFF. This restricted item default
is the approved optional feature behavior, not the original hack item rule.

Up/Down wrap through three settings, CANCEL, APPLY; Left/Right toggle a setting
or move between footer controls; A toggles a setting or activates its footer.
Touch a displayed value or either footer. B always cancels. Empty rows and touch
regions have no actions. Font colour marks the selected value; a dash marks the
focused row. All labels are project-authored text encoded through the existing
font/character mapping; no sprites, labels-as-graphics, icons, or assets generated.

Integration update (2026-10-10): CAP help now says **Gym-based cap. Never decreases. / Candy and Day Care unchanged.** under D-2312. Both exceptions are explicit under D-2304; Candy was deferred because stable field-menu ownership through its delayed effect is not established. This menu does not acquire, compute or cache cap levels. Only this project-authored help string changed in options.c. The original local-check results below belong to the pre-edit source; integration freshly recompiles and reruns the shipping host checks, with current source binding in options-source-pins.json and the integration receipt. Native UI acceptance remains pending.

Actual hook chain:

1. ARM9 `0203E544` wraps only the field launch's Options getter. It returns the
   original pointer exactly and samples native held keys at `gSystem+44` (L512).
   `0203E556` binds the exact Args pointer before the original field dispatcher.
   The shared Options getter is unchanged. Other Options callers cannot request
   custom mode via this route. A new launch supersedes any unconsumed ticket.
2. Only the Options overlay descriptor at `020F6F78` has its init callback changed.
   `dg_menu_init` consumes the one-shot ticket, calls native `021E4980`, then
   compares manager Args and actual Options pointer before starting the private
   transaction. A second simultaneous custom owner is refused. One extra native
   String(40) allocation on heap38 supplies all labels. Failure falls back to
   ordinary Options before suppressing any rows. Original native init allocation
   failure behavior is unchanged; this code does not make that native path safe.
3. Custom row load at `021E4D7C` creates zero choice strings/counts. The original
   teardown loop therefore frees none; no phantom pointers are inserted. Normal
   mode calls the existing TEXT SPEED loader at `01FF8A0C`.
4. Custom initial drawing at `021E4D88` replaces the **entire** normal `021E5210`
   pass, including every `021E53EC` preview. It fills/copies the existing five
   windows; synchronous speedFF printing leaves no borrowed String outstanding.
   Native windows/resource construction and teardown remain intact. Sprite setup
   still constructs all nine native sprites for matching destruction, then hides
   all nine in custom mode. Existing native position updates do not reveal them.
5. Custom input at `021E4C00` replaces `021E578C` entirely. It uses native new keys
   (`gSystem+48`) and touch-down (`+64`, coordinates `+60/+62`), with no fabricated
   callback outcome path. State+10 low bits signal Apply1/Cancel2 to the original
   fade/resource teardown state machine. Field input-mode bookkeeping matches
   native key/touch choice. No sound/background/frame preview setter is called.
   The footer animation-wait adapter at `021E4C20` returns0 for custom mode, so
   hidden footer sprite animations cannot block leaving the page.
6. Descriptor exit pointer `020F6F80` routes **before all six native setters,
   Cancel preview restoration, and TEXT SPEED commit**. The custom callback reads
   the saved heap ID before free, validates and applies/cancels once, frees its
   String, invalidates ownership, frees manager data, destroys heap38. No naked
   middle-of-function call or reconstructed native stack is used. Normal mode
   calls original exit entry `021E4A68` unchanged. A repeated exit with manager
   data already null returns1 without another free. A replaced/missing custom
   allocation refuses the write/free and exposes STALE through
   `dg_menu_last_apply_result()`; this is a lifecycle violation for tests to catch,
   not an advertised recovery path. The custom String may leak on that invalid
   lifetime path because freeing unknown/reused storage is unsafe.

Custom Apply conflict detected during input remains on the page with an error
and allows Cancel; final exit validates again. Final-exit failure writes nothing
and is observable in `dg_menu_last_apply_result`. There is no auto-save.

Window geometry (existing native templates, no allocation enlargement): title
state+34 is96x24 at(8,0); main+44 is240x144 at(8,24); help+54 is216x32 at(16,152)
on the other BG/screen; CANCEL+74 is64x24 at(112,168), APPLY+64 at(176,168).
Rows draw at local y8/40/72; controls hint at108. Touch setting bands are
screen y24..55,56..87,88..119; labels at x8..71 only focus, values at x72..183
and184..247 choose. Footer touch is y168..191, x112..175 Cancel/x176..239 Apply.
Native screen placement/visibility/font palette still requires runtime inspection.

## Compatibility edits and storage caveats

All edits are declared in `compatibility.json` and assembled by armips.
Startup title extraction, public title getter/setter, initial/local Apply title
snapshot construction, native title row read, final Apply extraction, and Cancel
restoration are narrowed to bit4. Local snapshots currently derive from the
narrowed getter, but narrowing their own writers/readers makes their ownership
explicit too. The normal title preview call itself is unchanged.

Current TEXT SPEED payload is **not recompiled or relocated**. Precisely five
`MOV #12` masks become `MOV #4`: five changed bytes inside five declared
two-byte instruction spans (ten-byte allowed span):

| Address | Purpose |
|---|---|
| `01FF8766` | print_task inlined fast check |
| `01FF8A1E` | load_rows normal/fast selection |
| `01FF8AC4` | standalone commit_speed clear mask |
| `01FF8AF8` | exit_free inlined commit_speed clear mask |
| `01FF8C2E` | pass_end inlined fast check |

Fresh exact halfword census of the entire pinned payload finds exactly these
five candidate mask instructions, each matched to its disassembled role and the
current C fast/load_rows/commit source. Payload symbols, code length, 52-byte
frame state, ITCM end `01FF8FC0`, and every other byte remain unchanged. Phone,
frame-printer and catch-up source/code remain otherwise byte-identical. The
production `text_speed_patch.verify()` intentionally rejects this companion
payload: installer must verify exact declared delta, not call it unchanged or
weaken its production pins. It must also preserve existing overlay92/ARM9 hooks.

The native Options allocator/init/copy still operates on exactly two bytes; all
native normal fields own disjoint bits after narrowing. No profile offsets,
save-entry sizes, checksums, mirror logic, or replay copy sizes change. Valid
legacy words with zero repurposed bits yield flags0. There is no version/checksum
tag in this compact encoding. Reserved old text encodings2/3 now mean bit2
NORMAL/FAST plus CAP; high title bit now means ITEMS_ALL. Arbitrary edited or
corrupt legacy words cannot be distinguished from chosen difficulty. Downgrading
can reinterpret those bits as old invalid title/text encodings. Do not promise
arbitrary old-word semantic preservation, corruption detection, or lossless
mixed-version use. Native save CRC/mirror policy remains authoritative.

## Installer contract and measured ABI

Run commands from repo root. For armips, use absolute source/output paths and
`-root ABSOLUTE_FRESH_STAGE`; that option resolves its staged file names without
changing the command's repo-root invocation. Stage unchanged copies of both ASM
files and exact input `arm9.bin`, `overlay50.bin`, `itcm.bin`. FIRST verify all EN
whole-file size/hash guards plus source/tool pins. CN hashes/ranges are provenance
and independent comparison guards, **not alternative accepted installation bytes**.
Hash checks outside patch sites are mandatory. Then stage `c-symbols.inc` with
`.definelabel dg_menu_..., ODD_ELF_THUMB_ADDRESS` for the nine functions. Supply
`-definelabel DG_OPTIONS_STUB_BASE BASE` as an armips command argument: an include
`.definelabel` is too late for `.open` parsing in armips0.11.0.

Use a four-byte-aligned stub base AFTER the complete linked C initialized and
BSS span, and any preceding item stubs. Allocate exactly72 bytes in
`options-stubs.bin`. `DG_OptionsStubsStart/End` are actual emitted extent labels;
nine `DG_Stub_dg_menu_*` labels are eight-byte `ldr r3; bx r3; .word odd_C_target`
thunks. They preserve SP/LR and all arguments (these hooks use at most r0/r1),
and clobber only caller-saved r3. BL hooks target even stub labels; callback
pointers target stub+1. Verify branch reach and all emitted symbols on the FINAL
combined link. Do not hardcode the provisional addresses below in the installer.

Compile flags actually used: `clang --target=arm-none-eabi -mcpu=arm946e-s -mthumb
-Os -ffreestanding -fno-builtin -fno-unwind-tables -fno-asynchronous-unwind-tables
-fstack-usage -Wall -Wextra -Werror`. Link with the local Rust `ld.lld`, explicit
sections, `--no-undefined`. Do not compile/recreate the production TEXT SPEED
payload. Local compiler/linker/armips paths and hashes are in the pin metadata.

Measured isolated link at provisional `023DC000`:

- text2764 bytes, rodata427, alignment1 byte, BSS72 bytes;
- initialized end `023DCC77`, BSS `[023DCC78,023DCCC0)`;
- options stubs `[023DCCC0,023DCD08)`; full span3336 bytes;
- no undefined symbols, relocations or runtime helpers; only text/rodata/BSS
  allocatable sections; code symbols retain Thumb bit;
- compiler stack usage: largest single function `text`136 bytes, drawing96,
  init56; input→finish→draw→text adds312 bytes, **excluding native callee stacks**.
  Eight-argument native call ABI is intentional: unused registers/stack words are
  ignored by shorter native callees; all used values are 32-bit AAPCS slots.

This is NOT a final whole-feature reservation decision. Combine other modules,
measure their true total, and enforce the integration handoff's reviewed arena
reservation below `023E0000`. Interior C BSS BEFORE the stubs must be materialized
as zero initialized bytes, or placed in a separate autoload section; do not put
stubs on NOLOAD storage or treat interior BSS as the autoload's trailing count.
Cold boot and native reset must clear pending/page/epoch BSS. No separate runtime
marker, reset hook or persistent pointer is introduced here.

## Actual checks and remaining proof

Fresh checks live only under `work/build/difficulty-v2/options/`:

- Real host and ARM946E-S Thumb compilation with warnings-as-errors; actual ARM
  ELF linked with no undefined symbols. `options.elf`, map, `.su` and staged
  assembled output are current and source-bound by the pin receipt.
- `host_check.c` linked against shipping settings/options C (native ABI mocks
  under `DG_OPTIONS_HOST_TEST`): all65536 words x8flags, unrelated-field
  preservation, aligned halfword at protected-page boundary, invalid wide flags,
  owner/epoch/options mismatch, active reentry, changed-live mask, and no-op on
  read-only live page. Also all8 input-driven draft/Apply patterns, touch choices,
  B/Cancel, away-and-back, hidden rows inert, conflict, allocation fallback,
  normal-route delegation, and cleanup exactly once. These are callback/logic
  tests with native primitives mocked, **not synthetic native UI acceptance**.
- `assemble_check.py`: actual armips over fresh extracted staged English sections,
  nine branch/pointer hook targets, exact72-byte thunks, exact24 compatibility
  halfwords, unchanged file extents/every other byte; all33 independently
  corrupted hook/edit sites reject without any staged writes.
- `compat_check.py`: bounded instruction interpreter of ACTUAL assembled title
  and text mask sequences across all65536words (five title readers, title setter
  inputs0/1/2/3/FFFFFFFF, both speed setter copies, load_rows and both fast checks).
  Full EN/CN guards and18 dependency ranges each match; mutations outside short
  patch guards fail full-file identity. This is instruction arithmetic evidence,
  not ARM hardware/runtime/emulator execution of the new page.

The installer must freshly check current input/source guards and exact combined
logical deltas. The test agent must exercise actual held-L launch, visible page,
D-pad/touch selection, Apply/Cancel/B/reopen, all seven normal settings/previews,
absence of custom audio/background preview calls, native resource teardown,
transaction owner/reset transitions, tight English heaps, and integrated gameplay.
Native saving, mirrors/CRC, reload, cold boot/new game, soft reset, and actual
initialized/BSS/autoload ranges remain unproved. Parent requested GPT6 Astra
review/fixes remain later sequential steps. No claim of native UI, save, gameplay,
Candy, or full candidate acceptance is made by this implementation handoff.
