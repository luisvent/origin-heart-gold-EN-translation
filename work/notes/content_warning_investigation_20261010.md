# Startup content warning — implemented 2026-10-10

Worktree: `/private/tmp/poke-content-warnings`, branch `investigate/content-warnings`,
based on `a657a13`. User approved replacing QQ/Tieba promotion with a first-page
warning, removing the QR display, and retaining five pages, author credits and
attribution notices. The GitHub README warning is approved too.

## Player-visible result

1. Content warning and `Current version: 4.0.3-RC7` (bank 0816 #4).
2. Welcome, original author credit and non-commercial notice (#0). The user
   rejected the original-author permission claim; it has been removed.
3. Explanation of unofficial mechanics (#1, unchanged).
4. Free-game and repost attribution notices, a reference to the website save
   editor, and `Website & Guide: originheartgold.github.io` over two lines (#2).
   The user requested removing the cheat-tool limitation and bugs disclaimer.
   QQ/Tieba promotion is removed; attribution moved from #4.
5. Complete author/special-thanks credits plus `kakapipi/Shishio` and
   `(Translator & Bug fixing)` (#3). Ye Shifu and Guagua share one line to keep
   eight lines. The version moved to the first warning page.

The original five nine-second timers and A-button transitions are unchanged.
The bottom-screen QR background is hidden and its separate caption is not drawn.
No replacement graphic or website QR code was added. Existing assets are still
loaded/freed normally. No new graphic asset was generated.

The README warning appears before “Play it”; the red patch-page warning is above the
patcher; the FAQ uses the same wording:

> This fan game contains strong language, sexual themes and innuendo, violence,
> death, and dark humour. It is intended for mature audiences and is not suitable
> for children.

## Implementation

`work/patches/startup-content-warning/` is a guarded, enabled armips fix for overlay49
(RAM 0x021E4980). No growth or allocation changes, and no new message IDs:

| Address | Change |
| --- | --- |
| 0x021E71B6 | BG4 enable argument 1 → 0, hiding the QR background |
| 0x021E733A | Body-message reader calls index-mapping helper |
| 0x021E7434 | Former QR-caption prologue becomes helper: counter 0 → ID 4, counter 1–4 → IDs 0–3 |
| 0x021E77C2 | Only QR-caption render call replaced with two NOPs |

The helper preserves an eight-byte-aligned stack. The counter stays 0–4, so the
existing final-page checks, timer reset, fade transitions and final start prompt
remain intact. The timer/caption IDs are not accidentally shifted. Original-byte
guards and the patch system’s declared-region checks protect every edit.

Bank `a027/0816` edits are restricted to English/status/origin/notes of IDs 0,2,3,4.
The original Chinese and IDs remain unchanged; #8’s old caption remains stored but
is no longer read. Backup and scene packet are in `work/build/content-warning/`.

Source-worktree decisions **D-2292, D-2293 and D-2294** record the startup approval,
credit/version/website additions, and permission/save-editor wording corrections.
Their integration is complete: `decisions.py add` transferred them to prep-local
**D-2327, D-2328 and D-2329**, respectively, and the imported references were updated.
The unrelated global Bellsprout finding remains **D-2292**; it was not remapped or
overwritten. The primary register was left unchanged. These prep-local allocations
still need coordination before any later merge with the global register.

## Evidence and verification

- Traced the untouched CN ROM’s real message calls: bank 816 is opened by
  overlay49 at 0x021E76B6; body reader 0x021E733A; caption reader 0x021E7450.
- Inspected the bank scene packet and the earlier D-0504 notice-panel verification.
- Final corrected-notices build: SHA-1 `507721e66c937c7c95320164cf4061f92a880e01`.
- Build verification passed: NARC/text round trips, glyphs, graphics, guarded
  assembly edits and text-speed contract. Generated xdelta re-applies to exactly
  the built ROM; SHA-1 `f834502e969d72fc9374e16fb3cc02d55b4f0c70`.
  ROM/patch outputs stay ignored and have not been published.
- 53 assembly tests passed, including each-fix and combined-image hashes.
- Bank QA: **0 errors**, five reviewed warnings. The width warning is source-relative
  (189 px versus the Chinese bank’s 182 px reference) and fits the actual panel.
  Eight-line warnings are confirmed to fit. The missing-number warning is the removed QQ number, as explicitly approved.
- Final-build DeSmuME blank-battery run observes body IDs **4,0,1,2,3**, no ID 8
  caption reads, and the final ID 7 start prompt. Holding A before expiry does not
  leave the warning. All five pages were visually checked for clipping/overlap.
- Normal input proceeds through the information menu and Oak intro to the outfit
  chooser. Full naming/both-player completion and existing-save Continue were not
  separately exercised. No save data or runtime state was injected.
- Patch-page MDX compilation and warning placement checks passed. The local page
  was captured with `agent-browser` and visually checked after switching the
  content warning to Starlight's red `danger` style. The screenshot and embedded
  HTML review are `work/build/content-warning/patch-page-content-warning.png`
  and `work/build/content-warning/patch-page-review.html`. The patcher display
  uses existing local RC5 release metadata, with its null `release_url` omitted
  for manifest validation; this preview does not indicate a new release.

Reproduce the startup capture with the existing emulator environment (no downloads):

```sh
/Users/contributor/Developer/poke/.venv/bin/python work/tools/emu_startup_warning.py \
  --rom work/build/content-warning/notice-final/origin_hg_v4.0.3_en_wip.nds \
  --out work/build/content-warning/screens-notice
```

Screenshots and runtime read log: `work/build/content-warning/screens-notice/`:
`01-warning.png`, `02-welcome-and-credit.png`, `03-mechanics.png`,
`04-free-and-attribution.png`, `05-credits.png`, `06-after-notices.png`,
`07-new-game.png`, `report.json`.

The updated self-contained HTML gallery is `work/build/content-warning/review.html`.
Its seven embedded images match the final capture files byte-for-byte.

`CONTRIBUTING.md` now documents updating bank 0816 #4 before each release: the
version is embedded text, so changing the GitHub tag alone does not update it.

## Integration/release follow-up

Changes are local and uncommitted. The primary checkout was not changed.
Reconcile the decision ID as described above, and regenerate destination-specific
build hashes if integrating with its newer changes. Copy the public warning into
the next GitHub release description and packaged README too; direct release
visitors bypass the website and repository README. Nothing was published here.
