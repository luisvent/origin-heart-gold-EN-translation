# Native Difficulty cursor fix — 2026-10-10

Parent screenshots `work/build/difficulty-v2/tests/native-tests/ui/focus-{0,1,2,3,4}.png`
show the native red row outline remaining on ITEMS as custom focus moves.
The outline is BG0, separate from the nine native sprites.

Move the existing eight-byte sprite thunk to overlay50's final initialization
BG enable call at `021E4DB4` (original bytes `37f650fb`, Thumb BgToggle
`0201C459`, arguments BG0/enable1). Original sprite setup at `021E4DA2`
(`13f6c7fe`, existing TEXT SPEED setup `01FF8B35`) now remains unpatched.
Difficulty hides all nine allocated sprites and disables BG0 at this final seam,
before initialization returns and fade-in begins. Native footer navigation
already uses this same BG toggle to hide the row outline (`021E594E` path).
No tile/font assets are changed. Custom focus remains its row dash and selected
footer text; custom input never calls native row-scroll/re-enable routines.

The Options overlay/heap is singleton. Only its live custom transaction with
manager/state ownership suppresses BG0; ordinary entry and allocation fallback
forward both original arguments. Original setup and teardown still own all nine
sprite allocations. Other backgrounds, preview behavior, saved settings, cap
schedule, policy, production TEXT SPEED sources/payload and compatibility edits
are unchanged. Hook count nine and stub extent 72 bytes remain unchanged.
Full EN input guards bind the native BG routines and surrounding init sequence;
CN provenance guards remain intact. Explicit source overrides retain prior pins.

Host driver checks original setup once, all nine hides only for custom, final
BG0 state, all five focus positions without re-enabling BG0, normal entry and
allocation fallback. These are ABI mocks, not native visual acceptance.
Build with the integration handoff's pinned double-target input, then run
`.venv/bin/python work/research/difficulty-armips/tests/run.py` from repo root.
Fresh source-bound build receipt and test report are authoritative for results.
No emulator is launched in this fix pass. Parent must verify fresh screenshots,
ordinary Options and native input on the new candidate before accepting the UI.

This cursor patch did not change caps. The subsequent D-2312 policy pass now
implements the nondecreasing gym schedule and updates CAP help; parent native
acceptance must use the rebuilt combined candidate, not the cursor-only hash
`ea4477edf2a494f9bc8de70d879c12e3324106acb209db6d8f7966baadc2c5d3`.
