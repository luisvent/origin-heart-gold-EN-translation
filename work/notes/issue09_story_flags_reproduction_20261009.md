# Issue 9 — story flag reproduction stage, 2026-10-09

**Fresh runtime writes unverified; stage closed without a production fix.**
The sandboxed DeSmuME worker aborted at host startup before boot or native
flag execution. The exact rerun requested outside the sandbox remained pending
and its tool call was canceled after165.4 seconds. No fresh SetFlag/CheckFlag,
control, native-save or reload result was produced. The coordinator explicitly
closed the stage without further emulator or approval requests. This host
failure is not game evidence and does not establish that the issue is absent.

Private preparation is in
`work/build/bugfix-sequential-20261009/issue09/repro/`: the unexecuted runtime
harness and `summary.json` recording unchanged inputs and the first Chinese
worker's returncode−6 (SIGABRT, equivalent to shell exit134). The parent command
then exited1 because its complete-matrix assertion failed. DeSmuME printed its
version and rasterizer initialization; no worker `result.json`, array snapshot,
save state or battery export exists. A closure process-inventory command was
denied by the sandbox (`operation not permitted: ps`); it was not escalated.
The coordinator's earlier inventory had not shown a launched rerun.

Both attempted commands were identical, run from the repository root:

```text
.venv/bin/python work/build/bugfix-sequential-20261009/issue09/repro/reproduce.py
```

The second request used `require_escalated`, with a prefix scoped to that exact
Python executable and private reproducer path. Its recorded tool outcome was
`aborted by user after 165.4s`. No automatic approval rejection or rejection
reason was returned. Do not treat the private harness as a passing test: its
native instrumentation, dynamic allocation checks and save/reload driver have
not run and may still require correction.

## Evidence retained and limits

The completed investigation remains
`work/notes/issue09_story_flags_investigation_20261009.md`; ignored static
artifacts are `issue09/static-inputs.json`, `static-evidence.json`,
`native-callers.json` and extracted native bytes. Both current ROMs have
identical member168 commands CheckFlag7286@235 and SetFlag7286@1954,
and member962 SetFlag4461@1819. The flag handlers are identical. Native
GetFlagAddr calls a conditional assertion for an excessive ordinary flag
index, then can continue constructing the address; actual SetFlag STRB is
0x0204F8B2. The investigation's arithmetic maps7286 to Pokédex+0x172/bit6
(legacy seen entry1335), and4461 to Pokédex+0x11/bit5 (Weezing caught).
These are static/historical findings, not freshly executed writes in this stage.

D-1333/D-1550 retain their historical observations. This stage adds no evidence
of visible Pokédex damage, general save corruption, story reachability or
persistence. It also adds no runtime evidence for old/new Route1 marker
compatibility. Static evidence still requires preserving the legacy completion
marker: moving7286 directly to a new valid bit would omit the old save's marker.
Any compatibility mapping remains a separate design/verification task.
Mt. Mortar's safety-only SetFlag0 proposal and the warnings against assigning365
or clearing legitimate Weezing data remain investigation recommendations only.

## Input integrity

Closure SHA-256 checks match both the initial and final sandbox snapshots:

| Input | SHA-256 |
|---|---|
| Untouched Chinese ROM | `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8` |
| Latest issue06-fixed English ROM | `1f955bf433e69ba47d688749d70a635da8c5d9c024e838ed7cd8499dd76bbfa2` |
| Source `work/build/memcheck/full_bag_6mons.sav` | `b3aca10747cd0f1adc3d5852a50dddaaa36ed8680f5ba04012cfe3110faad90f` |
| Private, unexecuted harness | `4a37d1a91d1e1dcdec5f3759a58e9ca233f36cf2f21b75e6cdad7ae2046db6a7` |

No production patch/tool/text edit, ROM build, source-save edit, decision change,
download, commit or publishing occurred. Under the sequential reproduction gate,
issue9 proceeds no further in this run.
