# Cleanup audit — 2026-10-10

Initial directory survey: approximately 53 GB under `work`, including 51 GB
under `work/build`. The largest concentration was 17 GB of difficulty-installer
staging and publication backups. A release-validation emulator run was active
under `work/build/rc7-release-prep-checkout`; its checkout and outputs were retained.

Removed 59 redundant installer ROM copies (15.32 GiB) on the first cleanup pass.
Only `run-*/candidate.pending.nds` with a completed receipt and transaction ROM
copies under `publication-*` were eligible. Minimum age: one hour. Receipts,
compilation logs, assembled sections, published candidates, source ROMs, saves,
release patches, snapshots, worktrees and failed-build evidence were preserved.
Cleanup holds the publication lock and refuses a pending recovery journal.

Root causes and changes:

- Publication deliberately retained old full ROMs even after commit or recovery.
  It now deletes redundant transaction ROMs best-effort after either succeeds.
  Cleanup failure cannot change the commit result; journaled recovery copies
  remain available until recovery succeeds.
- The installer CLI retained its full staged ROM after successful publication.
  It now deletes that redundant copy while preserving receipts and build evidence.
- The cached test assembly helper used an unmanaged `mkdtemp`. It now owns a
  `TemporaryDirectory` through an exit stack, retained for the test process and
  released at normal exit. Forced termination can still leave temporary files.
- `work/.venv` was a self-referencing symlink. It now points to `../.venv`.

Maintenance: `python3 work/tools/cleanup_installer.py` previews eligible historical
copies; add `--apply` to remove them. It does not recursively purge build folders.

Validation: all 13 `test_installer.PublicationTests` passed without ROM construction
or emulator execution, including interrupted publication/recovery, rollback,
backup removal, and cleanup failure after commit. Existing receipts retain their
original source hashes; these source edits do not revalidate prior native evidence.

Remaining large folders include active release-validation outputs, sequential
bugfix reproductions, and retained research evidence. Their age or ignored status
alone does not establish that they are disposable. No tracked or untracked source
work was removed, and no worktree was removed.
