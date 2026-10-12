# RC7 bounded source integration — 2026-10-10

Source integration is complete in `release/rc7-prep` at
`$HOME/Developer/poke/work/build/rc7-release-prep-checkout`.
This is **not a new built or release-ready candidate**. No ROM build, emulator,
commit, publication or download was performed. The earlier RC7 build evidence
predates these additions. All shell commands were launched from the main root
`$HOME/Developer/poke`; Git operations used `git -C`.

## Exact inputs and retained work

The three source checkouts are based on
`a657a13941fadd14ab373dbfcbb5cf347af9d9a3`; dirty-file hashes, rather than HEAD
alone, identify the integrated source. Prep HEAD remains
`e652abd68d26b5075bd02d1ecb69103b6953cb00`.

| Source | Integrated scope |
|---|---|
| Main root, `develop` | Entire `work/research/difficulty-armips`: 133 source files; no caches, `.DS_Store`, ROMs or generated artifacts |
| `/private/tmp/poke-honey-gather`, `fix/honey-gather` | Honey patch ASM/manifest/listing, four tools/tests, investigation note, two changelog bullets and softlock-audit section |
| `/private/tmp/poke-content-warnings`, `investigate/content-warnings` | Startup patch ASM/manifest/listing, screenshot runner, investigation note, README/CONTRIBUTING/FAQ/patch-page changes, bank 0816 approved edits, isolated assembly test |

[The source manifest](rc7_source_integration_manifest_20261010.json) lists every
copied/merged source path with SHA-256, target path/hash and prior target hash
where applicable (156 source entries, 155 unique targets). Decision transfer and
integration-authored report/status edits are described separately here. Internal
command logs, the initial inventories, touched-bank backup and transfer commands
are retained under main-root `work/build/rc7-source-integration/`.

No unrelated main-site, guide, generated-doc, registry, tool or bank changes were
copied. Initial source inventories were checked after integration: all inventoried
files in main and both source worktrees remain unchanged. Existing prep work was
retained, including its dirty expected hashes, D-2321 decision and disabled
manifests. Shared documents were merged; they were not replaced by source versions.
Every pre-existing FIXES.md section matches its pre-integration bytes; only the
two requested sections/table rows were added through the target generator.

All 133 difficulty files match the main source byte-for-byte. Historical five:

| File | SHA-256 |
|---|---|
| `foundation.asm` | `f16ebbf3c3f8072631c6e711ee97bc5532e38861ec9745f87cfa8e49d2f28b59` |
| `hooks.asm` | `b1b96e794d4f865c8877bec56f6585116b7320acfffcc8fc91eed44012ec3af0` |
| `fix.toml` | `9b9097ddfb60ccf661f2a7e01baa46530584b1446b98af581aac04763da10ca2` |
| `check.py` | `b35f016cc5afc1814ab00d7e554189bb8d08e78ab93b80167f86e17570fe8ee5` |
| `README.md` | `54c121c5ba8311e118899088a8f167c91b948d7306f0d7927a0d610fdde5b2f9` |

Latest Honey checker and test are exact copies:

- `work/tools/emu_honey_gather.py`: `8e49856cd07c4ba2200a6c272acf935a97bf81709781c85c1b3a75f125911906`.
- `work/tools/test_emu_honey_gather.py`: `689f365647b6ab90fa97ca45595f9f7839e25afbaa8f13ca5653b130b5d917d3`.

`assert_rewards` checks Bag quantities, collector counts/output slots and expected
Bag calls. Negative tests reject phantom counts, stale slots, missing/duplicate
hooks and unexpected insertion attempts even with unchanged Bag quantities.
Original Pickup's false full-Bag announcement is accepted only as baseline evidence.

## Decisions and approved text

Only `decisions.py add` changed the register; no JSONL was hand-edited or copied.
The pre-existing target records remain unchanged. Global D-2322–D-2326 were
reconstructed with their existing IDs and substantive fields: the two difficulty
revival records and three Honey records. Honey's manifest/header now cite its
transferred decisions instead of claiming register integration is pending.

Content-source D-2292–D-2294 collide with unrelated existing global/prep encounter
findings. They were added as **prep-local D-2327–D-2329**, respectively. References
in the imported bank notes, patch manifest/ASM and note were remapped. The old
encounter decisions remain untouched. D-2329 records the later removal of the
permission claim, amending the initial request preserved in D-2327.

Main's register is unchanged and ends at D-2326 in the captured inventory.
D-2327–D-2329 are not globally reserved by this task: the coordinator must preserve
this mapping or reconcile later global allocations before merging registers.
The tool command/ID transcript is `decisions-transfer.json` in the scratch folder.
D-2326's unspecified confidence remains null; its source, finding, refs, rationale,
open status and related IDs are retained.

Bank `a027/0816` changes only `en`/`notes` for IDs **0, 2, 3, 4**; all Chinese,
other IDs and other fields remain unchanged. These are the approved startup
changes, not a new translation batch: warning/version first, original author and
translator credits, free/non-commercial/repost notices and website/save-editor
reference, with QQ/Tieba promotion, QR display, permission claim and disclaimer
removed as approved. No batch completion was added to PROGRESS.md.

## Checks performed on prep source

Commands below use the main root, with:

```sh
prep=work/build/rc7-release-prep-checkout
logs=work/build/rc7-source-integration
```

| Check | Result | Log in `$logs` |
|---|---|---|
| Honey host instruction replay and reward-oracle regressions | **14 passed**, 9.249 seconds | `honey-tests.log` |
| Startup isolated source golden and full source-inventory test | **2 passed** | `startup-tests.log` |
| Scoped difficulty host/source/oracle subset | **74 run: 66 passed, 8 errors**, 11.367 seconds; no assertion failures/skips | `difficulty-host.log` |
| Registry validation/overlap check | **50 registered, 47 enabled**, no registry overlap errors | `registry.log` |
| Combined assembly dry-run against local CN input | **26 ASM fixes, 99 code/data regions, 4 strings**, armips v0.11.0; no ROM serialized | `assembly-check.log` |
| Both new disassembly snapshots | **2 passed** | `listings.log` |
| Bank 0816 QA | **9 strings, 0 errors, 5 warnings** | `qa.log` |
| Decision register validation | One pre-existing D-1298 missing-bank reference; identical error before/after | `decisions-baseline.log`, `decisions.log` |
| Source preservation / import provenance / diff whitespace | Hash and target-origin checks passed; `git diff --check` clean | `preservation.json`, `module-origins.txt` |

Test commands:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$prep/work/tools" \
ARMIPS=$HOME/Developer/armips/build/armips \
.venv/bin/python -m unittest -v test_emu_honey_gather test_honey_gather

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$prep/work/tools" \
ARMIPS=$HOME/Developer/armips/build/armips \
.venv/bin/python -m unittest -v \
  test_asmpatch.RealFixes.test_startup_content_warning_source_golden \
  test_asmpatch.RealFixes.test_every_armips_fix_has_a_source

PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="$prep/work/research/difficulty-armips/tests:$prep/work/tools" \
.venv/bin/python -m unittest -v test_host test_policy test_source \
  test_native_composites test_native_items_doubles test_native_free_trace \
  test_native_items_remembered test_native_items_control test_native_items_gates \
  test_native_items_field test_native_progression test_native_multiko \
  test_native_caprise test_native_edges

python3 "$prep/work/tools/fixes.py" check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python "$prep/work/tools/asmpatch.py" \
  --armips $HOME/Developer/armips/build/armips check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python "$prep/work/tools/asmpatch.py" \
  --armips $HOME/Developer/armips/build/armips \
  listing --check honey-gather startup-content-warning
python3 "$prep/work/tools/qa.py" check "$prep/work/translate/banks/a027/0816.json"
python3 "$prep/work/tools/decisions.py" \
  --register "$prep/work/translate/decisions/decisions.jsonl" \
  --ws "$prep/work/translate/banks" validate
git -C "$prep" diff --check
```

The four actual C drivers (growth, items, runtime/caps, settings/options) passed
ASan/UBSan. All nine composite tests passed on this target copy. This is a scoped
new host result, **not 171 current-host passes or full-suite acceptance**.

All eight difficulty errors require the absent target-local
`work/build/difficulty-v2/integration-impl/receipt.json`: three free-trace tests,
and one each for typed gates, field records, progression fixtures, trainer6
multi-KO fixtures and other-curve/level100 fixtures. No old candidate/receipt was
linked in to manufacture a passing result. Existing prep links to parent `.venv`,
ROM and extract inputs were sufficient for the independent checks. No new
symlinks were needed. All inspected project module origins and `support.ROOT`
resolve inside prep; the parent Python executable supplies dependencies only.

QA warnings are expected approved content differences: three eight-versus-seven
line counts, the removed QQ number, and one 189px line versus the old 182px Chinese
maximum. No overflow error is reported. These are not grounds to undo the approved
warning. Native screenshots still need rerunning against the eventual combined ROM.

An initial startup test attempt stopped at registry loading because the newly
populated Honey decision list named D-2326 but the ASM comment did not. The comment
was corrected; the subsequent two tests and combined dry-run passed. The first
changelog patch did not apply to prep's existing additions; its two bullets were
then merged explicitly without replacing the existing changelog.

## Preserved exclusions and deferred golden updates

The 45 existing enabled fixes remain enabled; Honey and startup add two. Under
D-2321, `mortar-invalid-flag-noop`, `expedition-completed-progress` and
`hooh-panel-silver-marker` remain disabled and byte-identical to their initial prep
files. `battle-hit-sound` and `battle-faint-cry` remain absent from the registry.
Difficulty remains outside it; its historical foundation manifest is not enabled
or moved into `work/patches`.

`work/patches/expected.toml` was **not changed by this integration**, and the content
worktree's version was not copied. Its captured/final SHA-256 is
`2a4ec6d9557cb1a00306f7615e7b3c4ba6f863af2069fded0f3ed72716375bd7`.
It describes the earlier 45-fix build, not this new source. No combined hash was
blessed. The content branch's isolated startup golden was carried over and verified,
but its obsolete 16-source combined golden/count was not copied over prep's
24-source baseline. That old combined test is now explicitly named
`test_preintegration_fixes_together_match_golden`; its original hashes/counts remain.
The inventory test includes both additions. The eventual combined byte review must
extend the combined golden inventory and recompute expected text/nontext/ROM/patch
hashes, then run the strict release/reproducibility checks.

## Current difficulty status supersedes older prose

`IMPLEMENTATION.md` and older handoffs were copied intact for source fidelity.
Their **0/69**, stationary-cursor rerun and historical fixture statements are not
an up-to-date acceptance summary. The current parent handoff is authoritative for
status: **Aristotle stopped; R3 strict doubles work is done; R1/R2 are partial**.
Nine composite host tests had passed; this integration also reran those nine
successfully. The earlier **39-pass/3-fail targeted run was not rerun as that suite
after its fixes**. The full suite was not run. New selected results above do not
close that gap, and the historical 171-host total is not claimed for latest edits.
No native acceptance or final review is established by this integration.

Six further coverage/review blockers remain open (see the copied coverage map and
required-native manifest):

1. Source-bound combined no-banking evidence across cap-rise and multi-KO paths.
2. Current gap closure, plateau and entry-freezing evidence for skipped decreases.
3. Native egg/fainted/remote recipients, deferred crossing and simultaneous-KO gaps.
4. Real Erika win/loss/retry/ceremony script paths.
5. Other constructors, replay/link/facility, load-identity and arena obligations.
6. Stable final-source reruns of historical UI/items/growth evidence and final review.

Host oracle support, prepared fixtures and R3 completion do not by themselves close
these native/combined obligations. Rare Candy and Day Care remain deliberate
exceptions under D-2304/D-2307.

## What eventual difficulty inclusion actually requires

The standard `work/tools/build.py` loads the production fix registry, exports text,
applies graphics/NARC/ASM fixes and creates artifacts. It does **not** discover or
invoke the research difficulty installer. Copying this tree to prep therefore
cannot put difficulty in the resulting ROM.

The opt-in path is `work/research/difficulty-armips/build.py --enable-difficulty
--input <completed-English-ROM>`, using `install.py` to compile/link the resident
payload, add an autoload section, reserve the arena, apply all hooks and compatibility
edits, verify logical preservation, and produce a source/tool/input-bound receipt.
It is not safe to install only the historical three-hook `fix.toml`.

The pinned-input statement has two distinct meanings: it remains an actual guard
in the copied installer, but its historical fixture is **not approval or compatibility
proof for the current combined RC7 source**. `install.py` currently requires full
input SHA-256 `a5a418b277bf07390e7282413923ec34f1c364f4a96c88936d65a73a80d51f40`,
whole overlay9/14 pins, and ARM9/ITCM/overlay50 guards in `compatibility.json`, plus
hook/dependency/source/tool pins. It rejects the new combined input. Do not bypass
or mechanically replace those hashes.

Necessary subsequent work, outside this bounded task:

- Build the completed 47-fix English baseline, independently inspect all differences
  from the old difficulty input, and review every affected pin/guard/dependency.
- Reconcile difficulty with existing TEXT SPEED explicitly. The static comparison
  of 46 difficulty hook/edit spans against enabled registry footprints finds **17
  intersections, all in TEXT SPEED's overlay50 Options region**, and none with the
  Honey/startup patches. ITCM appended payload and resident memory require separate
  byte/layout review; registry growth sentinels cannot prove their compatibility.
  See scratch `conflicts.json`. These intended layered edits are not permission to
  insert difficulty as an ordinary non-overlapping registry patch.
- Review the full input guard changes and source/tool contracts; create a target-local
  candidate/receipt using the deliberate opt-in installer only after that review.
  Validate arena/autoload bounds, exact logical writes and preservation of all 47
  production fixes, disabled story bytes and excluded sound/cry bytes.
- Complete the missing host fixtures, post-fix targeted/full suites, source-bound
  native evidence and final review. Recheck normal TEXT SPEED and difficulty Options,
  save/load/reset, battle/item/growth behavior and startup/Honey on the combined ROM.
- Make the production release process explicitly account for the difficulty
  post-processing and its verification if shipping it is approved. Regenerate the
  final USA-based xdelta and expected hashes **after** difficulty installation;
  the standard builder's earlier patch does not include it. Preserve strict
  validation rather than disabling verifiers to accommodate the changed bytes.

No installer pins, production build paths, difficulty source or acceptance gates
were weakened or refactored during this integration.

## Astra source-review P3 closure

Corrected the content-warning investigation note's collision explanation: global
Bellsprout remains D-2292; source startup D-2292–D-2294 were transferred to prep-local
D-2327–D-2329. Updated only that note's target hash in the source manifest; its
source hash is unchanged. All 156 manifest entries' source and target hashes were
rechecked successfully, and `git diff --check` passed. No additional tests or
research were performed.
