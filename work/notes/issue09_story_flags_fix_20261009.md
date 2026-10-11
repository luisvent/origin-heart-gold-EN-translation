# Issue 9 — bounded story-flag repair, 2026-10-09

**Mt. Mortar's invalid write is prevented; Route 1 remains deferred.** D-2300
authorizes the scoped original-hack repair. D-2310 records the no-op choice;
D-2311 records the bounded Route1 audit and excluded migration. No emulator,
escalation, download, commit or publication occurred.

## Enabled change

`work/patches/mortar-invalid-flag-noop/fix.toml` replaces only the operand of
member962 SetFlag4461 at1819 in `a/0/1/2`: offsets1821/1822 `6D11→0000`.
The whole original 6788-byte member SHA-1 is pinned to
`33cb77c9032d91186fa1680ae2b28919b4f58be5`; the operand has an independent guard.
Native SetFlag0 returns without a persisted byte read/write or assertion.

Set675, Clear670, SetVar409F=7, ReleaseAll/End, all command offsets and the
existing issue10 completed-expedition condition at136 remain intact. Flag461
would add NPC persistence;365 changes unrelated legendary respawn state.
Neither is assigned. Existing Weezing caught/seen data is preserved: an old
caught bit cannot be distinguished from a legitimate capture. No save migration
or old-data restoration is performed.

## Route 1 bounded audit and deferral

Candidate3190/0xC76 has no literal Set/Clear/CheckFlag or event hide use, but is
not a proved author typo or reserved flag. The private `fix/route_audit.py` reads
the pinned CN ROM and executes actual native helpers with bounded inputs:

- All 1024 local trainer IDs: 4096 native set/check/clear/check calls, flags1360–2383;
  every store stays in array4 and none reaches the candidate byte.
- Native daily reset:24 byte stores at flags0xAA0–0xB5F; candidate bit remains set.
- 231 native hidden-item conversions: script IDs0x1F40–0x2026 yield flags800–1030.
- Overlay103's shared 10-entry native table at021FE46C resolves to2730–2739.
  Script151's computed contest flags627–636 and script948's653–662/2730–2739
  bounds are also inspected in the actual disassembly.

The 104 direct Thumb BL callers inventory still exposes unproved inputs:
overlay2@0225141A consumes caller-derived r7; overlay92@021F130E/021F1318 reads
table-record+4; the reward helper consumes0x8006; dynamic object creation and
tail/function-pointer consumers are not completely bounded. These checks reduce
candidate collisions but do not justify a global reservation.

A two-site remap7286→3190 would make a legacy-only completed save repeat the
gift. Exact-ID legacy-or-new reads or lazy migration could preserve that marker,
but need a defensible allocation and verified native hook. The legacy dex bit
can also be legitimate species1335 seen data and must never be cleared. No
Route1 operand, engine hook, alias, migration, bag reward or global bounds guard
is changed. The existing Route1 out-of-range write therefore remains open.

## Tests and paired builds

`work/tools/test_story_flags.py` adds six tests using local ROM instructions and
actual NARC registry entries: exact operand/unchanged structure; atomic whole
member and independent operand guards; composition in both orders with issue10;
native SetFlag0 no-read/no-write plus original assertion rejection; and native
675/670/409F tail controls with whole-array comparisons. Existing NARC and
shared-progress suites plus these tests pass: **24 tests**. Ruff check/format and
registry validation pass. No production executor changes or game dumps are added.

Both current-tree builds use local armips0.11.0 and
`--no-regen-graphics --no-patch`; both pass complete builder verification.

| Artifact | SHA-256 |
|---|---|
| Without this repair; identical to issue10 fixed | `50a5b4a91a401f85392068cc15731406c46c15c5ea703c013c1e93e90f3bee5c` |
| Fixed | `af0641ced20e830b9f27a4d0771e1478308cfc4dcdd537030d4e50d06e6299bd` |
| Fixed member962 | `72f1a0e63d154b2ec730002f135bb8a7e6befd87ecbd4a5620a7b0aa1872ca74` |

Private `fix/pair_check.py` proves equal ROM size278780608, only fileID132 and
member962 changed, and exactly raw offsets137579825/137579826 differ. ARM9,
ARM7 and both overlay tables are identical. The complete overlay14 and earlier
script members17/129/45, plus issue10's962@136 condition, retain all five earlier
sequential repairs. Root ROM, RC7, source battery and `expected.toml` are intact;
the coordinator owns the final expected-hash refresh. `FIXES.md` is regenerated.

## Actual built native matrix and limits

Private `fix/matrix.py` executes **20 passing cases per actual built ROM**.
The actual member bytes supply the changed operand; no handpatched scene is
substituted. Four `(caught,seen)` combinations validate SetFlag0 and the native
expedition tail. Every fixed command preserves the entire mapped dex region,
all unrelated save bytes and legitimate preexisting bits. Native tail commands
return1819/1823/1827/1833 and finish675=true,670=false,409F=7. The unchanged
native commands/writes around1819 match the baseline exactly. All eight complete
Route1/valid-control cases have identical traces across builds. Synthetic0,
3190 and3231 controls dispatch the actual built native command table.

235 instruction addresses and576 ARM9 bytes execute/read per variant, with
identical code and consumed-address-byte SHA-256
`9d9bcb7fc713a1bce4d105bb9aa2e1c177daaa58f2b71d467a0226f5d9d92173`.
The mapped region rejects reads/writes immediately beyond0230372B.

This is **offline native-handler verification, not full-game validation**.
Private RAM uses historically observed array allocation metadata; the save
accessor is a fixture. Original badflag tests execute the real assertion call,
but replace the assertion implementation with a logged returning fixture that
models historically observed behavior. They do not prove the current full
game's assertion branch returns. Actor setup, coordinate triggering, rendering,
ReleaseAll services, natural story reachability, map reload, native save/reload
and hardware behavior are untested. The production Scene test logs ReleaseAll
as a boundary and reads actual End; it does not simulate those services.

Preservation snapshots retain all unrelated dirty work. The coordinator changed
`bug_priorities_20261009.md` during this stage and confirmed ownership; an
unrelated `.DS_Store` metadata change is preserved. Neither is restored.

## Local reproduction

Run from repository root; all build/evidence artifacts remain ignored under
`work/build/bugfix-sequential-20261009/issue09/fix/`:

```sh
.venv/bin/python -m unittest work/tools/test_narcpatch.py work/tools/test_story_flags.py work/tools/test_shared_progress.py
.venv/bin/ruff check work/tools/test_story_flags.py
.venv/bin/ruff format --check work/tools/test_story_flags.py
python3 work/tools/fixes.py check
.venv/bin/python work/tools/build.py --armips /Users/contributor/Developer/armips/build/armips --work-dir work/build/bugfix-sequential-20261009/issue09/fix/without --without mortar-invalid-flag-noop --no-regen-graphics --no-patch
.venv/bin/python work/tools/build.py --armips /Users/contributor/Developer/armips/build/armips --work-dir work/build/bugfix-sequential-20261009/issue09/fix/fixed --no-regen-graphics --no-patch
.venv/bin/python work/build/bugfix-sequential-20261009/issue09/fix/pair_check.py
.venv/bin/python work/build/bugfix-sequential-20261009/issue09/fix/matrix.py
.venv/bin/python work/build/bugfix-sequential-20261009/issue09/fix/route_audit.py
```

`matrix.json` retains all instructions, boundaries and byte writes; `summary.json`
retains code/input pins. `route-audit.json`, `pair-summary.json`, build logs and
preservation snapshots capture the bounded audit, exact changes and limits.
