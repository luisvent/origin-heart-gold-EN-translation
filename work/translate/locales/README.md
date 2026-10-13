# Locale catalogues

Chinese message text in `work/extract/v4/<narc>/<bank>.json` is the stable source. A string is identified by `narc/bank#id`; its `source_sha256` fingerprints the decoded source text from that extract, including source bytes hidden behind song-lyric redaction in the English workspace. `work/translate/banks/` remains the English catalogue. The English adapter reads it without rewriting it.

Each locale has a tracked `locale.json` plus editable glossary and voice configuration. Glossaries map source terms to nonempty target strings; voice files map speaker names to nonempty voice guidance strings. Other JSON shapes are invalid. Glossaries and voice files start empty: add only locale-specific reviewed entries. Locale bank records and decision logs are local data and are ignored by Git. Their text field is always `text`, never `en`.

Statuses are explicit: `todo` has no target text; `imported` is third-party reference material that still needs human review; `draft` is locally authored but unreviewed; `reviewed` is approved for the locale. Locale readiness requires every required source to have a current reviewed target, no duplicate refs or stale source hashes, configured glossary and voice resources, plus verified locale build resources. Empty glossary/voice files keep readiness false.

From the repository root:

```sh
.venv/bin/python work/tools/check_translation.py --locales-only
python3 work/tools/localization.py init-locales
python3 work/tools/localization.py init-target fr
python3 work/tools/localization.py import-es
python3 work/tools/localization.py stats es
python3 work/tools/localization.py readiness es
python3 work/tools/localization.py context a027/0000#5 --locale es --out work/build/context/a027-0000-5.json
python3 work/tools/localization_build.py matrix
python3 work/tools/localization_build.py prepare es
```

`localization_build.py matrix` reports coverage, review blockers, and separate build-resource
states. For non-English locales, graphics, hardcoded strings, font support, and a grammar
audit must each be integrated and carry file/hash evidence in that locale's `locale.json`.
A populated glossary or voice file does not establish asset readiness. These resources are
currently unverified for French, Italian, German, and Spanish.

`localization_build.py prepare <locale>` requires a complete catalogue of current, reviewed
targets and runs locale-neutral control-tag QA. It does not evaluate target encoding, glyph
availability, name buffers, or pixel fit; those checks remain explicit compile blockers.
Missing, stale, imported, or draft
text stops staging; nonlinguistic and configured passthrough rows are copied exactly from
Chinese. It writes an EN-shaped temporary workspace plus manifest under
`work/build/locales/<locale>/<fingerprint>/`. The EN-shaped form exists only at this compiler
compatibility boundary; locale records remain in `text` fields and never enter the English
catalogue. Fingerprints identify text staging inputs: source and target catalogues, the source bank inventory,
locale config/resources, enumerated build tools, patch files, charmaps, available fonts, and graphics.
They are not complete ROM compiler dependency keys. Stages include a hash inventory and repeated
preparation rejects changed, unmanifested, or symlinked cached files.

Preparation is for review and is not a ROM build. Every non-English manifest remains
`compile_ready: false` while locale compiler integration is absent, and matrix reports that
as a blocker. The matrix marks English as using the legacy default build path but does not
claim its output is verified; existing build QA and release gates still apply. The existing
English build command and its default workspace remain unchanged.

The Spanish importer accepts only unique, equal-count, same-index structural candidates whose control signatures agree and whose Chinese bank fingerprint matches the extracted Chinese ROM. Default Chinese loading verifies the full bank inventory against that ROM and rejects missing or edited banks, empty source inventories, and unsupported raw-only banks explicitly. Spanish raw banks are decoded and compared exactly with the JSON rows; default imports also verify bank provenance against the reconstructed reference ROM and manifest. Such rows are still `imported` with low-confidence alignment. Expanded-bank additions, collisions, missing refs and stale fingerprints are written to the ignored quarantine file. No bank order is treated as script order. Context packages are bounded physical neighbours and label English as a reference. They carry the settled source-fidelity and adult-tone policies (D-0627/D-2081), preserving ambiguity and the source strength of insults, sex, violence, and dark or political jokes.

`schema.json` documents locale records. Context packages add a compact `scene.py show` excerpt when available, relevant locale voice/decision resources, and a mandatory `needs_context` blocker. A line with no script path remains explicitly unresolved; retrieve the bank packet with `python3 work/tools/scene.py packet <narc>/<bank>` and inspect a line with `python3 work/tools/scene.py show <ref>`. Custom glossary, voice, decision, and target-bank paths in `locale.json` must stay within that locale directory; readers and initializers resolve those configured paths. Custom resources remain ignored by default to prevent accidental publication of game text. Known song-lyric sources and target candidates are withheld from context, preserving the original hash and D-0368 substitution instruction. Bounded decision lists report omitted counts. Context output refuses shared build-input symlinks. Build integration must not silently substitute English or source text for an unready locale.
