# RC7 source/tag handoff — 2026-10-11

Requested publication: commit source/documentation, tag `v1.0.0-rc7`, and push to `origin/main`. This is a release-candidate source tag; the complete native difficulty acceptance gate is still incomplete. No GitHub Release or binary asset upload is part of this operation.

Integrated the retained `release/rc7-prep` branch with `origin/main` at `77b73d5`, preserving the published website and save-editor gender repair. Pending guide and research documentation was included. Older workspace copies of twelve already-published website/acquisition files were retained locally rather than replacing newer main versions. The private local ROM-ideas catalogue, third-party promotional assets, virtual-environment path change, ROMs, saves, patches, extracted data and build artifacts remain outside this commit.

The multiplayer-scope decision is D-2330 in the merged register. The primary workspace had independently used D-2327 for that decision; the release register already uses D-2327 for the startup warning. D-2330 was added through decisions.py, and current validation references were updated. No user decision changed.

Checks on the merged source:

- 1,056 tool tests passed, 33 runtime/environment-dependent tests skipped.
- 46 documentation tests passed.
- 216 difficulty host/static tests passed. This does not establish native acceptance.
- Production website build passed: 4,653 pages.
- All 104 website tests passed against built pages, zero skips.
- Save-editor typecheck, lint and test/mutation checks passed: 491 tests passed, one skipped; all configured mutation checks passed.
- Git whitespace and game-artifact staging checks passed.

Local rc7 xdelta independently decoded to SHA-256 `81ec4501ef92c01872e97fc61d1e763c84cb1e7fcb92164ed1aa1623e1b9ec39`; it remains ignored. Release candidate includes opt-in difficulty, installed separately from the 47-fix baseline as documented. Full and short player-facing changelogs are in CHANGELOG.md and work/notes/rc7_changelog_short.md.
