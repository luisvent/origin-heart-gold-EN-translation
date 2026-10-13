# Spanish graphics selection

`selection.json` selects assets from the user-supplied Spanish rc42 patch (based on EN rc4). It is a compiler input policy, not an assertion that the Spanish ROM is release-ready. `locale_graphics.py` materializes the selection without saving a ROM or editing translation catalogues.

## Result

- 168 recognized graphics members differ between ES rc42 and EN rc4.
- 157 donor members are selected across 24 archives, plus the 480-byte battle status-icon range in overlay 14.
- 11 donor members are excluded: four title assets (preserve D-0767's bilingual logo), two unrelated overworld sprite/animation additions, and five Pokéathlon NSCR containers whose entries and dimensions are unchanged.
- Repacking the Pokédex adds changes to its dependent maps: the prepared stage contains 183 replacement members across 25 archives, and one bounded code range.
- All other members remain byte-for-byte intact. No entire donor archive or overlay is transplanted.

The policy pins the five ROM inputs, every selected donor/baseline/current member, and the complete current destination archives. These archive guards cover palettes, tile maps, cells, animations, and costume dependencies; any future change requires a new comparison rather than an automatic overwrite.

## Preserving fixes after EN rc4

The current destination is the graphics output of this checkout's enabled graphics fixes, reconstructed in memory from the Chinese and USA ROMs. This deliberately does not build a ROM, apply unrelated code fixes, or modify the normal build command.

- **Pokédex header:** three-way merge existing indexed pixels from EN rc4, ES rc42, and current EN. Conflicting edits fail. The current column-edge correction survives; the Spanish NACIONAL lettering is reused for both header variants (screens 7/8), as requested by the user on 2026-10-13 because the National Dex is available from the beginning. This changes the header artwork, not gameplay flags.
- **English headers:** both runtime variants use the existing USA NATIONAL lettering. Spanish uses NACIONAL for both. The small ES switch row now comes from Spanish retail, with matching palettes and existing tile limits.
- **Spanish retail labels:** source Pokéathlon tutorial members 42/44/46 in `a/2/1/9` and the GET replacements 13/17 in `a/2/2/4`. Palette/map/cell/animation dependencies are compared with retail before accepting these tiles. The remaining archive members stay intact.
- **Pokédex buttons:** retile existing Spanish button images into the allocation pool already audited by `gfx.make_dex_labels`. Preserve the current search screens 9/10/69/70 and direct-copy background tiles 98/101. Member 71 keeps its current disabled-button state and palettes; only label rows 22–29 are sourced from donor member 6. Both costume copies receive the same result. No new lettering is drawn.
- **Chain Logger:** accept donor members 25/26 together; its highest referenced tile is 46, within the current loader's 48-tile limit. The broken rc4 allocation is not restored.
- **Title:** preserve the project's bilingual logo and its current subtitle. The donor title changes are outside this selection.

Existing runtime-loader hash guards and tile limits in `work/graphics/layout_checks.json` pass for the prepared state. Additional summary/trainer-card map edits preserve dimensions and stay within the previous screen's tile ceiling; those checks do not claim a new runtime allocation audit.

## Reproduce

Run every command from the worktree root. Supply the existing local ROMs; do not download them. If needed, reconstruct EN rc4 with `xdelta3 -d -s <USA.nds> <EN-rc4.xdelta> work/build/gfx-es-selection/en-rc4.nds`.

```sh
python3 work/tools/locale_graphics.py prepare \
  --cn-rom '/path/to/origin_v4.0.3_cn.nds' \
  --us-rom '/path/to/Pokemon - HeartGold Version (USA).nds' \
  --baseline-rom work/build/gfx-es-selection/en-rc4.nds \
  --source-rom work/extract/gfx-es-rc42/origin_v4.0.3_es_rc42.nds \
  --spanish-rom '/path/to/Spanish-HeartGold.nds' \
  --out work/build/gfx-es-selection/prepared-es
```

Use a fresh output directory. Input hash mismatches, changed destination dependencies, conflicting header edits, tile exhaustion, or altered loader code stop preparation. Generation is isolated in a temporary directory; failed preparations do not leave a partial output. The output contains `manifest.json` and only the selected asset files. It records input/recipe hashes and keeps `runtime_verified: false`.

Install the locked graphics environment with the pinned uv 0.12.23:

```sh
uv sync --project work --locked --no-default-groups --group graphics
```

This installs Pillow 12.3.0 and ndspy 4.2.0. Use `work/.venv/bin/python` for the commands above and below. Add `--python python3` to `uv sync` to use an already installed compatible Python 3.14 interpreter. Preparation itself still does not require Pillow; contact sheets and image checks do.

```sh
python3 -m unittest discover -s work/tools -p 'test_locale_graphics.py'
python3 -m unittest discover -s work/tools -p 'test_gfx.py'
```

## Compiler handoff

After the existing ordinary graphics stage, call:

```python
locale_graphics.apply_prepared(get_file, set_file, gfx.CodeView(rom), prepared_directory)
```

`get_file`/`set_file` are the same NARC access callbacks as `gfx.apply_patches`. The hook validates all destination archives, individual assets, code ranges and existing loader bounds before mutation. It writes only selected NARC members and the specified 480 code bytes. Subsequent compiler stages must not overwrite these resources; final ROM verification should check all `after_sha256` values. The existing English graphics report must be reconciled with the ES overrides instead of expecting the superseded EN member hashes.

The current archive guards intentionally require the selected enabled graphics configuration. A build omitting or changing one of those graphics fixes needs a separately validated selection. The manifest is local generated data, not a distributable asset bundle.

## Verification and remaining scope

Seventeen focused ROM-free tests cover three-way conflicts, changed dependencies, tampered assets, size changes, code-range bounds, traversal rejection and unrelated-data preservation. The existing 17 graphics tests pass. Real-input preparation validates all selected hashes, layout rules and readback. Independent local verification checks that unselected members remain unchanged, costume copies match, and repeat preparation produces identical assets.

Latest local evidence is under `work/build/gfx-es-selection/`: `retail-final/` (strict prepared stage), `locale-headers.png`, `retail-verification.json`, `retail-review.png`, `retail-labels.png` and `pokeathlon-retail.png`. Older preparation directories predate the retail source and English header change and must not be consumed. Verification checks both header variants per locale, exact Spanish switch pixels and palettes, identical costume copies, preserved search screens/direct-copy tiles, retail replacements and unchanged unselected members. These are static checks, not emulator evidence.

In-game EN/ES integration remains necessary. Text, fonts and hardcoded non-graphic strings are separate inputs. No ROM was saved or built by this graphics preparation.

## Explicit fallback policy

Default `--fallback-policy allow-listed` permits only recorded, hash-checked gaps. The current reviewed list is empty after sourcing the Spanish retail artwork, so strict preparation also passes. Both large EN headers say NATIONAL; both large ES headers say NACIONAL. Each output carries the exact fallback list, policy and `known_fallbacks_remaining` flag.

The earlier PLAYER/SCORE identification of `a/2/1/9#50` was incorrect; that sheet contains TÚ. The retail comparison located actual untranslated labels in other tutorial sheets and the GET artwork. This correction removes the inaccurate fallback entry rather than treating it as a newly translated label.

`--fallback-policy error` refuses preparation while any listed gap remains. The compiler can also pass `fallback_policy="error"` to `apply_prepared` to enforce that policy when consuming an otherwise prepared stage.

Neither mode substitutes English when a required Spanish asset is missing, corrupt, changed, incompatible or has an unknown dependency: those failures always stop the operation before mutation. A fallback region/member changing also fails its hash check. This is an explicit list of known gaps, not automatic language detection or a claim that all other donor graphics are Spanish.

See [SOURCES.md](SOURCES.md) for the bounded local/public source search and the Spanish retail source verification. Adding a sourced replacement means reviewing it, updating hashes/dependencies, removing its fallback entry, and regenerating the prepared stage; a build never fetches assets from the network.

Prepared manifests use schema 2; old schema-1 stages must be regenerated so strict mode cannot bypass an absent fallback inventory.
