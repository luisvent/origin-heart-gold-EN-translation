# Native Options pages — 2026-10-11

The user requested that both Options pages use the actual native menu presentation after comparing RC6 with the font-based two-page footer.

Implemented in the retained RC7 prep checkout, not the older root research sources:
`work/build/rc7-release-prep-checkout/work/research/difficulty-armips/native/options.c`.

- Preserve original native Confirm/Quit label windows and button sprites7/8 on both pages.
- Use native red BG0 row outline and button focus through original routine021E5944.
- Difficulty uses the same20-pixel row pitch as normal Options. Existing three settings and saved codec remain unchanged.
- Restore native frame arrows5/6 only on page1. L/R and existing footer arrows still switch pages.
- Native cursor setup waits until sprite initialization finishes. The first prototype violated this order and faulted; that attempt is not accepted evidence.
- Original ordinary drafts and the difficulty transaction remain separate until shared Confirm/Cancel. Temporary cursor state/choice changes are restored before native input/exit.

The source override history is retained in integration_contract.json; focused host touch coordinates/cursor expectations were updated in tests/drivers/options_check.c.

Final candidate SHA-256: `4896050aaa689c65a034b3bb1dc98b49d69d143393eec6941262b3a27b7ea0b1`.

Validation: guarded build/install/reopen passed; focused ASan/UBSan Options driver passed (including524288 codec combinations, draft/commit/cancel, cursor, touch, cleanup and fallback checks). Fresh native captures cover both pages, all five difficulty focus states, page return and Cancel. A short native check passed page-switch draft retention, no early commit, cancelling both drafts, confirming both drafts, and unrelated-bit preservation. Copies of the save are used; no source ROM/save is modified.

Evidence: `work/build/rc7-rerun-20261011/native-options-prototype/` (screens-v2, apply-cancel/report.json, source backup and native-options.patch).

The preceding101/102 native-job report applies to the earlier menu payload, not this UI revision. This is focused UI validation; no new full gameplay matrix or release packaging is claimed. Native runtime suite cursor/touch assumptions need updating before a later comprehensive rerun; this task intentionally did not expand that suite.
