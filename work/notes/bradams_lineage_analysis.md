# Bradams fork: remaining resource changes and lineage audit

Audit date: 2026-10-05. Read-only comparison of the same four ROMs identified in `work/build/bradams-audit/inventory.json`: untouched Chinese, local NoBigText, supplied Speedoption, and the inspected local English WIP. “Shared” below means byte equality, not proof of who authored or first published a change. The NoBigText filename alone does not establish that it contains only a text-size change.

## Additional verified change: Pallet Town photo eligibility guard

`a/0/1/2` member **733**, used by map 49 / Pallet Town / message bank 439, is identical in Chinese, NoBigText and the inspected WIP (2,202 bytes). Speedoption grows it to 2,244 bytes and changes the photographer's affirmative interaction path.

At offset `0x88`, the original script tests whether the photo album is full. Speedoption replaces that instruction sequence's entry with a jump to the newly appended block at `0x89A`:

1. `CountAliveMons 0x800C, 6`.
2. If result is zero, jump to existing cleanup at `0x353` (close message, release actors, end).
3. Otherwise perform the original album-full check, branching to the existing full-album response at `0x367` when full.
4. Otherwise resume the original photographic sequence at `0x99`.

The command's name is corroborated by its actual handler, not assumed. Opcode 357 dispatches to `0x0204CE60`. That handler iterates the party, skips the index named by its second argument, excludes Pokémon for which field `0x4C` (Egg) is nonzero, and only counts entries for which field `0xA3` (current HP) is nonzero. Argument 6 skips no ordinary slot in a six-slot party. Thus the new guard rejects an **empty party, all-Egg party, or party without a living non-Egg Pokémon** before attempting this photo.

The code establishes the preventive check; a crash reproduction establishing its original symptom and a runtime regression test were not performed. It is a new guard relative to all three baselines, not a difficulty, text-speed or Gyarados-script change. Do not generalize this one map edit to all photographers.

## Route 3 / Misty / Gyarados: what script member 175 does and does not prove

Member **175** is Route 3 (map 11), containing the Misty/Gyarados scene and other interactions. Speedoption, Chinese and the inspected WIP have **exactly identical bytes**, SHA-256 prefix `f1a772e3e09b`, size 4,694. NoBigText differs, size 4,696, SHA-256 prefix `c694387d8e8c`.

The NoBigText difference is a script-layout change, not a modified Gyarados event:

- Chinese/Speedoption entry offsets begin `0x166, 0x7E, 0xB8, 0xF2, 0x12C`.
- NoBigText begins `0x7E, 0x93, 0xCD, 0x107, 0x141`.
- These are the same entry-index behaviors: a signpost and four Deoxys-form interactions, physically reordered so the signpost comes first.
- Relative branch displacements are updated to preserve their original targets.
- All bytes from `0x17B` through the end of the original member are identical. NoBigText adds two zero padding bytes at the end.
- A graph traversal pairing entry points and branch targets compared **1,114 reachable instruction pairs**, normalizing branch displacements, and found **zero semantic instruction differences**. Scratch evidence: `work/build/bradams-audit/lineage/script175-normalization.json`.

This disproves treating the member175 byte difference as evidence of a new Gyarados script fix. It **does not disprove an indirect Gyarados crash fix**: the scene's message bank 319 and the message-loading/heap code differ between builds. The existing [heap audit](heap_audit.md) documents a reproduced 200%-height English-message overflow in this scene and NoBigText's removal of size tags. Judge that text/layout fix from the actual affected messages and rendering evidence, not from script archive differences. A general heap/antipiracy fix could also affect the scene without changing member175.

## Text layout and the Gyarados crash: inherited fix is present

Decrypted comparison of NoBigText and Speedoption finds35 changed field strings: eight new settings messages (`0038#116–123`) and27 existing lines with size-tag/layout differences. The only changed battle string is the new nickname question (`battle bank2#487`). This is a narrow content change relative to NoBigText, despite large encrypted-archive byte differences.

The27 field entries are `0048#5,6,20; 0053#1,39; 0058#27; 0081#25; 0090#141; 0319#26; 0321#27; 0377#136; 0441#41; 0457#123; 0462#165; 0476#14,19,69,74; 0546#12,48; 0547#7; 0597#36; 0599#45,56; 0616#37; 0617#20; 0733#13`. Speedoption restores the200%-height emphasis tags removed by NoBigText while keeping each enlarged line on its own page, including a two-page split for `0616#37`. Twenty-six of these27 strings are exactly equal to the inspected English WIP; the remaining Pryce string differs in wording but uses the same split-page approach.

This is material positive evidence for the **known English text-layout Gyarados crash fix**: `0319#26` is a single enlarged line with the size reset before any subsequent page. The existing [heap audit](heap_audit.md#second-crash-class-double-size-text-with-a-line-break-misty-scene-rc3--fixed-d-1389) records actual earlier emulator evidence that a newline inside a200%-height span overruns the32-pixel-high message buffer and corrupts heap metadata, and that the one-line layout avoids that trigger. Speedoption has that corrected layout, not the unsafe original English wrapping. It does not introduce clipping into the renderer; the renderer is unchanged, so future unsafe text can still trigger the underlying defect.

Thus distinguish three statements: the Route3 event script is unchanged; the known scene's English text is corrected; and no fresh Speedoption runtime test proves every Gyarados-associated crash is gone. Shared text establishes inclusion, not first authorship. This is a **text-layout/memory-safety fix**, distinct from per-character text speed.

Compared with the inspected WIP rather than NoBigText, Speedoption differs in949 field strings across135 banks and11 battle strings across3 banks. Those differences include translation evolution, not949 new fixes. Do not replace our current text archives with the fork's snapshot.

## Code changes already shared with the English baseline

All three overlays below are byte-identical in **NoBigText, Speedoption and the inspected WIP**. They differ from Chinese, but cannot be presented as newly discovered Speedoption fixes:

| Code | Meaning verified against repository patch records |
| --- | --- |
| Overlay 44, offset `0x2E6C`, runtime `0x02228DAC` | Naming-screen kind-7 maximum length changes 5 → 7 |
| Overlay 49, offsets `0x4E` / `0x66`, runtime `0x021E49CE` / `0x021E49E6` | Intro player/rival naming maximum changes 5 → 7 |
| Overlay 58, original 2,016 bytes → 2,072 bytes | English outfit-selector labels; strings relocated and pointers adjusted. This is the outfit chooser, not a speed or compatibility module |

These match the intent and locations in `work/translate/hardcoded/code_patches.json`, `work/translate/hardcoded/strings.json`, and [the hardcoded-text audit](hardcoded_text.md).

The same byte-equality check attributes these ARM9 differences to the shared localized baseline (decompressed offsets): `0x42862`, `0x42892`, `0x4291E`, `0x490DA–0x490DC`, `0x83C25`, `0x90944`, and the Western naming-keyboard data groups `0x100C90–0x100CA9`, `0x100CC8–0x100D35`, `0x100DFC–0x100E16`, `0x100E34–0x100E86`, `0x100EA4–0x100EBE`. Other new code families are covered by the difficulty, targeting, hardware and speed reports.

Some new-relative-to-NoBigText changes are **also present in the inspected WIP**, including demand loading at `0x0200BA9A` and `0x0208799A` / `0x02087A0C`. Their function matters, but equality does not prove independent invention or which project supplied them to the other. Preserve attribution uncertainty.

## Chain Logger / link-capture graphics: a real allocation repair

Speedoption changes `data/linkcapture.narc` members **25** (screen map) and **26** (character tiles). Overlay 28 is unchanged in all compared ROMs. Its loader at `0x0225FE30` still loads `0x600` bytes, **48 4bpp tiles**. The resource files therefore must use only tile indices 0–47, regardless of how many tiles the file stores.

| Artifact | Character tiles stored | Highest screen-map tile index | Fits unchanged 48-tile loader? |
| --- | ---: | ---: | --- |
| Chinese | 96 | 46 | Yes |
| NoBigText | 96 | 74 | **No** |
| Speedoption | 48 | 47 | Yes |
| Inspected WIP | 96 | 47 | Yes |

Speedoption shrinks character member26 from 3,136 to 1,584 bytes and repacks the English screen map within the loaded tile range. Visual inspection of decoded assets shows DETAILS, X:INFO and Y:EXIT. It does not add a Chain Logger gameplay feature or change its encounter logic.

The mechanism matches the allocation problem independently documented and reproduced in [the graphics-layout audit](graphics_layout_audit.md): the old translated map addressed tiles that never reached VRAM. **The fix's scope is the labels' tile allocation.** Static allocation and decoded-image checks support that mechanism; this audit did not run the fork's UI in an emulator. The Speedoption and current WIP assets are not byte-identical, so describe them as different implementations satisfying the same tile bound, not proven copies.

A scratch comparison image is `work/build/bradams-audit/lineage/linkcapture-comparison.png`. It uses grayscale palette-index visualization to inspect lettering; it is not an in-game screenshot.

## Remaining archive inventory: shared assets versus fork-specific changes

A fresh per-member comparison classifies every changed non-text archive member relative to Chinese. Full member lists and equality results are in `work/build/bradams-audit/lineage/resources.json`.

| Archive/group | Members changed from Chinese | Speedoption relation to NoBigText / inspected WIP |
| --- | ---: | --- |
| `a/0/0/8` | 23 | All identical to both |
| `a/0/1/5` | 1 | Identical to both |
| `a/0/1/6` fonts | 4 | All identical to both |
| `a/0/3/1` | 1 | Identical to both |
| `a/0/3/9` | 3 | All identical to both |
| `a/0/4/9` and two costume copies | 3 each | All identical to both |
| `a/0/6/8` and two costume copies | 27 each | All identical to NoBigText; 20 of those 27 identical to WIP |
| `a/1/0/4`, `a/1/1/3`, `a/1/5/2`, `a/1/7/8`, `a/2/1/5`, `a/2/3/2`, `a/2/4/0` | 1 each | Identical to both |
| `a/1/4/3` | 6 | All identical to both |
| `a/2/1/9` | 16 | All identical to both |
| `a/2/6/4` | 3 | All identical to both |
| `battle/battle_graphics.narc` | 10 | All identical to both |
| `data/namein.narc` and costume `a031.narc` copies | 1 each | All identical to both |
| `a/0/1/2` scripts | 2 | New settings/global scripts and Pallet photo guard; Route3 member175 itself matches Chinese |
| `a/0/1/7` item records | 20 | New relative to both; covered by item-effect audit |
| `a/0/3/2` events | 25 | Settings NPC additions; covered by difficulty/NPC audit |
| `data/linkcapture.narc` | 2 | New tile-allocation repair described above |
| `extra/new_move_data.narc` | 1 | Bounce record340; covered by move/turn-state audit |

The `a/0/6/8` difference from the WIP includes later Pokédex graphic changes. Speedoption retains NoBigText's version of those assets; it is not the newest version of every local graphics fix. This comparison cannot certify a graphic's correctness simply because it is shared.

For the two NoBigText→Speedoption NARCs `a/0/4/3` and `a/0/6/5`, archive sizes differ by two bytes, but **no member payload differs**. This is archive-container packing/padding, not evidence of difficulty or gameplay changes. An earlier inference from whole-archive differences alone would be incorrect.

Text archives are intentionally handled separately by the root audit's full decrypted-message comparisons (`root/text-nobigtext-speed.txt`, `root/text-ours-speed.txt`). Their broad size and translation changes are not additional engine-fix counts. The final fork includes much shared English localization and does not represent an independent rewrite of every asset that differs from the Chinese ROM.

## What remains unknown

Binary equality establishes shared content, not the exact authoring chain, base release, or permission history. The missing historical patches/source revisions prevent assigning every change to its first release. No unchanged script should be used to dismiss a reported indirect crash fix, and no changed archive header should be counted as a gameplay fix without examining members. The new Pallet guard and Chain Logger allocation repair are concrete mechanisms; broad “all crashes fixed,” “Gyarados fixed everywhere,” or “all hardware supported” claims still exceed the evidence.
