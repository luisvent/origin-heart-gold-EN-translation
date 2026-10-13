# Remaining Spanish graphics: source check, 2026-10-13

The user subsequently supplied Spanish retail HeartGold (game code IPKS), SHA-256 `9e0f7a1a4a18d9015936678722ce081d08b6a5d882fd648e89b624307f8f9e19`. It provides the small NACIONAL switch region (`a/0/6/8`, screen 0 / graphic 1, x40..215 y120..135), tutorial artwork (`a/2/1/9` members 42/44/46), and Spanish GET replacements (`a/2/2/4` members 13/17). The latter differ from USA only in tiles 56..63 and 76..83 respectively; the donor changes those same letter tiles. Compatible palettes/maps/cells/animations were checked, and preparation enforces those dependencies. Raw retail assets remain ignored and local.

The earlier PLAYER/SCORE identification of member 50 was incorrect: it contains TÚ. Retail comparison instead revealed unchanged English labels in other tutorial sheets. All confirmed gaps in this reviewed selection are now addressed; strict preparation passes with an empty fallback list. This is not an exhaustive language audit or an emulator test.

The following table records the earlier bounded search, before the user supplied the retail ROM.

| Source checked | Evidence | Result |
|---|---|---|
| User's USA ROM and local graphics inputs | Existing pinned USA ROM, hg-engine vendor files, and Spanish rc42 extraction | Spanish donor already supplies the large NACIONAL header, type/status icons, buttons and other selected labels. The small switch label and PLAYER/SCORE are unchanged. No separately named Spanish retail HGSS dump found in the checked ROM/Downloads locations. |
| [hg-engine](https://github.com/BluRosie/hg-engine/tree/c056eb74d8486ec1b046ed4628ca23821c79dadd) | Complete GitHub tree at `c056eb74d8486ec1b046ed4628ca23821c79dadd`; README describes an English HeartGold engine | No Spanish/localization graphics paths identified. Existing noncommercial/credit terms apply; no new assets copied. |
| [pret/pokeheartgold](https://github.com/pret/pokeheartgold/tree/53dded53802b237d39fabfd8ee396fe9cdc8aa3e) | Complete GitHub tree at `53dded53802b237d39fabfd8ee396fe9cdc8aa3e`; README lists USA HG/SS build targets | No Spanish/localization paths identified. Tool subdirectory licences are not treated as blanket licences for game artwork. No assets copied. |
| Public repository search | Searches for Spanish HGSS graphics, NACIONAL and Pokéathlon assets | Results included GBA/GB projects styled after HGSS and visual mods, but no verified compatible, suitably sourced Spanish label set. No packs or ROMs downloaded. |

The retail source supersedes the earlier missing-source limitation. Both English header variants now use USA NATIONAL, and both Spanish variants use donor NACIONAL. No new lettering was invented. Any future missing or incompatible required source remains a build error; newly accepted fallbacks must be explicit and hash-checked.
