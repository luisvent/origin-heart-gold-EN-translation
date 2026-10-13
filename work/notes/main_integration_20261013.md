# Locale, Spanish graphics and ability-banner integration — 2026-10-13

Integrated the uncommitted work from `codex/translation-locales`, `codex/gfx-es` and `fix/ability-banner` onto main. Their committed tips were already ancestors of main. Source worktrees are preserved.

The locale infrastructure, English catalogue review, full trainer-name display support, Spanish graphics selection/preparation tooling and pinned graphics dependencies are included. Private locale catalogues, reference ROMs and generated graphics remain local and are not published. The separately reviewed ability-banner repair remains disabled; its finding is D-2500. Native single-battle evidence covers both sides; doubles placement remains unverified.

Decision IDs were reconciled through the register tool, preserving existing main records. `main_integration_decision_ids_20261013.json` maps source-worktree IDs to main. Main's repurposed Safari Zone closed notice in a027/0133#46 takes precedence over the older translation review. Other overlapping banks retain the current main changes. Existing bank indentation is preserved. Chinese/Japanese source text, string IDs and bank source metadata are unchanged.

Validation:

- English QA: 76,862 strings, 821 banks, 0 errors. Existing warnings remain, including the unchanged worst-case placeholder-width warning in a027/0419#51.
- 1,287 tool tests pass with the local pinned armips assembler; 26 optional tests skipped. All three ability-banner binary/width tests pass.
- 46 documentation tests pass. Locale gate, Spanish graphics tests, graphics dependency pins, register validation, assembly registry/docs, synthetic assembly, Ruff and git whitespace checks pass.
- The aggregate fast gate reaches a pre-existing site-test import failure: `work/tools/site/sync_guide.py` requires the absent `work/tools/site/quest_ledger.json`. Site tooling is unchanged by this integration.

No release ROM was built, no release hashes were refreshed and no game data was committed or published. This is a source integration, not a new release certification. Test logs and integration backups are in ignored `work/build/main-integration/`.
