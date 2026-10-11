# Remaining bugs and integration priority — 2026-10-09

Triage snapshot of `develop` at `a657a13`, the local RC7 candidate, current working-tree changes,
and the separate fix branches. This is a proposed work order, not authorization to change the
original hack's behavior. Highest priority goes to progression loss and crashes, then incorrect
mechanics and lost content, then presentation. A tested fix can be integrated before a higher-ranked
issue whose cause still needs investigation.

Register status is not implementation status: many `resolved` questions mean “documented, leave
unchanged.” Conversely, some `open` findings are harmless Chinese typos, unused content, or disproved
suspicions. The 164 open hack-finding records are not a count of unfixed gameplay bugs.

Follow-up user direction: **D-2300** authorizes sequential investigation/reproduction/fixes for
items 3, 5, 6, 7, 9 and 10. Item 4 is **deprioritized, with no fix requested**: the user reports no
bug reports and no natural reproduction. The ranking below is the earlier proposal; implementation
progress and the revised scope are tracked in [the execution ledger](sequential_bugfix_run_20261009.md).

## Ranked work queue

“No fix found” means none was located in the current registry, branch changes, or inspected research
notes; it does not mean a repair is impossible. The long tail of quest findings is grouped below;
the [known-issues guide](../../site/src/content/docs/guide/known-issues.md) retains the individual entries.

| Rank | Priority | Bug and impact | Existing fix / integration status |
|---:|---|---|---|
| 1 | High | **S.S. Anne party softlock**: Honey before the old man, or Blue first, permanently traps the player aboard (D-1549). | No fix found. Safe order is documented. |
| 2 | High | **Maxie gauntlet healing freeze**: Potion/berry playback after Roar looks up a departed Pokémon's HP bar and crashes in melonDS; can also animate the wrong bar in singles. | **Implemented, unmerged:** `fix/melonds-retest`, `battle-heal-hpbar-switched-out`. Paired original/control/fixed emulator evidence. |
| 3 | High | **No Struggle at zero PP**: a Trainer battle can become impossible to finish; the must-lose Route 12 battle also traps Ghost-only teams (D-1576). | **Implemented and enabled locally, uncommitted:** `zero-pp-struggle` (D-2302). CN/RC7 reproduction, paired current builds, assembly and runtime controls passed; see [fix report](issue03_struggle_fix_20261009.md). |
| 4 | High | **Goldenrod entry crash**: townsfolk and Rocket groups visible together exceed the sprite resource table (D-1547). | No fix found. Reproduced with the flag combination; the natural story order producing it remains uncertain. |
| 5 | High | **Rock Tunnel corner-kid loss freezes** (D-1395/D-1548). | **Implemented and enabled locally, uncommitted:** `rock-tunnel-corner-loss` (D-2305). Paired built loss/retry and structural checks pass; [victory-runtime limitation recorded](issue05_rock_tunnel_fix_20261009.md). |
| 6 | High | **Pokémon Tower Magcargo loss freezes** (D-1560). | **Implemented and enabled locally, uncommitted:** `magcargo-loss-whiteout` (D-2306). Paired build and native loss recovery pass; preserves existing one-visit visibility. [Fix report](issue06_magcargo_fix_20261009.md). |
| 7 | High | **Department Store 6F Double Battle with one Pokémon freezes** (D-1559). | No production fix. Fresh CN scene reached, but action test was invalid and corrected rerun never launched due pending approval. [Run limitation](issue07_department_doubles_reproduction_20261009.md). Bring at least two usable Pokémon. |
| 8 | Medium | **Double-battle D-pad targeting trap** when an enemy slot stays empty. | **Implemented, enabled locally and included in planned RC7 contents; uncommitted, packaging/release deferred.** `double-battle-targeting` includes the reviewed horizontal fallback; 26/26 fresh CN/EN cases, 130 target screens and 28 focused tests pass. See [validation](double_target_horizontal_validation.md). The prior Lugia-only RC7 artifact does not contain it. |
| 9 | Medium | **Out-of-range story flags write into Pokédex save data** at Route 1 and Mt. Mortar (D-1333/D-1550). | **Partly fixed locally, uncommitted:** `mortar-invalid-flag-noop` (D-2310), verified by paired builds and actual native-handler execution. Route 1 remains deferred for marker reservation / old-save compatibility (D-2311). [Fix and limits](issue09_story_flags_fix_20261009.md). No proven general save corruption. |
| 10 | Medium | **Permanent quest/legendary losses through shared progress:** Deoxys loss blocks Lucky Meowth God; expedition leader can suppress the beasts; early Ho-Oh panel skips Silver; bug hunt interferes with Forest of Time (D-1578–D-1581). | **Two fixes enabled locally, uncommitted:** `expedition-completed-progress` and `hooh-panel-silver-marker` (D-2308). Paired builds/native-handler tests pass; no fresh in-game scenes. Deoxys intent and bug-hunt migration remain unresolved (D-2309). [Report](issue10_shared_progress_fix_20261009.md). |
| 11 | Medium | **Cute Charm announces infatuation without applying it.** | **Implemented, unmerged:** `fix/cute-charm-infatuation`. DeSmuME and melonDS evidence; preserves the hack's chance and eligibility rules. |
| 12 | Medium | **Unsupported/broken evolution methods**, including Pancham and Petilil's self-evolution (D-1481/D-1485). | No fixes found. Boldore/Gurdurr and learning evolution moves are already fixed separately. Some affected species are unavailable. |
| 13 | Medium | **Pidgeot loan replaces the player's Pokémon**, including losing its held item (D-1392/D-1552). | No fix found. |
| 14 | Medium | **Wrong tutor moves:** Blackthorn Play Rough → Flail, Rock Tunnel Signal Beam → Pollen Puff, Lightning Whip lesson → Charge (D-1305/D-1338/D-1347). | No fixes found. |
| 15 | Medium | **Wrong charges/rewards:** fortune-teller price check/deduction mismatch, S.S. Anne TM sale, Game Corner coin quantity, other lost or mismatched rewards. | No fixes found. D-1545 and guide entries identify individual cases. |
| 16 | Medium | **In-battle party status is stale**, both after cures and newly acquired conditions; affects swap and item-target screens. | **Implemented, unmerged:** `fix/heal-bell-status`, `battle-party-status-sync`. Reviewed four party-screen paths; DeSmuME and melonDS evidence. |
| 17 | Medium | **Unavailable encounter systems:** swarms, National-Dex encounter variants, Safari Object Arrangement, special fishing replacement fields (D-2293–D-2296). | No gameplay fixes found. Guide/Pokédex sources corrected in current work. Static findings; disabled systems may be intentional. |
| 18 | Medium | **Partner move-in scenes unreachable** and other shared-flag quest failures (D-1391 and guide). | No fixes found. The quest-flag save-editor prototype only exposes two unrelated gates; it is not a repair for these bugs. |
| 19 | Low | **Multi-hit KO HP bar jumps/disappears before finishing its drain.** Damage itself is correct. | **Implemented, unmerged:** `fix/multihit-ko-hpbar`, `faint-waits-for-hp-bar`. DeSmuME and melonDS evidence. |
| 20 | Low | **Battle messages choose the wrong side/prefix**, including Destiny Knot, immunity, protection and several other move/condition lines. | **Implemented, unmerged:** `fix/destiny-knot-side`, `battle-message-variant` (two rounds). Some sites have static evidence only. **Lock-On/Mind Reader and “all fired up” remain outside this fix.** Future Sight's older report must be checked separately, not assumed covered. |
| 21 | Low | **Missing damage hit sounds.** | **Implemented, unmerged:** `fix/hit-sound`, `battle-hit-sound`. Single/double/multi-hit checks; some paths such as substitute and OHKO remain uncovered. Does not supply missing animation sounds for later-generation moves. |
| 22 | Low | **Missing faint cries/sound.** | **Implemented, unmerged:** `fix/faint-cry`, `battle-faint-cry`. DeSmuME and melonDS evidence; normal Chatot cry, not recorded Chatter. |
| 23 | Low | **Easy Chat ABC mode is still a Japanese kana grid** (D-1588). | No fix found; translated GROUP mode remains usable. |
| 24 | Low | **Weekday-sibling ribbon script aborts with the message open** (D-1331/D-1558). | No fix found. Ribbon is given; walking, X and saving work. It is not a freeze. |
| 25 | Low / fidelity | **Pokédex ends at internal No. 709; unavailable forms/items; Unown always A; Unown Report does not progress; fixed species lists disagree with Gym rules.** | No general fixes found. Some are original design limitations rather than confirmed unintended defects. |
| — | Deliberately held | **Pryce bans 28 species rather than inspecting their weather Abilities.** | **Implemented, unmerged and explicitly disabled by the user:** `fix/pryce-weather-rule`, `enabled = false`. Preserve that decision; not a routine pending merge. |

## Investigation queue

| Order | Report | Current evidence / next discriminator | Fix status |
|---:|---|---|---|
| 1 | Saffron move-relearner black screen, D-1589 / new evidence D-2299 | Reproduced in the locally supplied Bradams NoBigText ROM; Speedoption and RC7 pass the same six-visit stress sequence. Untouched Chinese passes the simple control. See [fresh comparison](saffron_bradams_repro_20261009.md). Do not attribute the same fault to current English releases without a failing current-build trace. | Existing `msgload` is already in RC4+; causal NoBigText control recorded in the comparison note. No new production patch. |
| 2 | PC wallpaper load crash reported in the fork's Discord export | Reporter supplied an out-of-range archive-index explanation; relevant PC code/resources unchanged in inspected Bradams builds. Needs our own reproduction using the affected save/build. | Reporter workaround is not a validated production repair. |
| 3 | Move-learning freeze / Silph elevator / quick battle-Bag exit | Separate branch names exist for the first two, but contain no changes beyond their common ancestor and have clean worktrees. Quick-Bag exit did not reproduce in the prior 1,620-trial two-emulator comparison. | **No implementation found**; a branch name alone is not a fix. |
| 4 | Triple Axel successive-kick damage, D-1596 | Missing kicks correctly stop the sequence; damage growth still needs measurement. | No fix found. |
| 5 | League teleport Abra/sprite mismatch, D-2281 | User screenshot differs from text; untouched Chinese rendering comparison still needed. | No fix found. |
| 6 | Other uncertain quest gates (D-1590–D-1595), hardware/fork-specific reports and Minimize border flicker | Keep separate from reproduced defects. Exact save, ROM and platform matter. | No fixes found. |

## Unmerged implementation inventory

These seven branch tips are not ancestors of `develop`, and their patch directories are absent from
the root registry. Validation below is existing branch evidence, not tests rerun by this triage.

| Suggested integration order | Branch | Tip inspected | Evidence |
|---:|---|---|---|
| 1 | `fix/melonds-retest` | `2e448a1` | `work/notes/melonds-retest_fix.md`; confirmed healing/Roar crash, paired controls. |
| 2 | `fix/cute-charm-infatuation` | `bb824cd` | `work/notes/cute-charm-infatuation_fix.md`; both sides, gender/ability/contact controls. |
| 3 | `fix/heal-bell-status` | `8095ad1` | `work/notes/heal-bell-status_fix.md`; status gain/cure, doubles/multi, end-of-battle parity. |
| 4 | `fix/multihit-ko-hpbar` | `460c6b0` | `work/notes/multihit-ko-hpbar_fix.md`; both sides, ordinary and critical KO timing controls. |
| 5 | `fix/destiny-knot-side` | `b948974` | `work/notes/destiny-knot-side_fix.md`; ten battle scenarios and static caller audit. |
| 6 | `fix/hit-sound` | `7e49173` | `work/notes/hit-sound_fix.md`; sound requests and damage-action arguments verified. |
| 7 | `fix/faint-cry` | `4996483` | `work/notes/faint-cry_fix.md`; both sides, Explosion, trainer and double battles. |

Separately: targeting is an uncommitted current-tree integration included in planned RC7 contents;
packaging/release are deferred. Pryce (`2ff7cce`) is parked/disabled.
The Saffron investigation (`76295b3`) contains research and a test harness only; the branch named
`codex/saffron-relearner-fix` has no fix beyond its ancestor. Catch-nickname's clean branch likewise has
no implementation; it is a feature request rather than a confirmed regression.

Before integrating existing branches, reconcile their decision references: some use D-2276/D-2281
for branch-local authorizations, but those numbers identify different records in the current register.
Do not blindly merge their whole decision files, generated hashes or historical changelogs. Combined
assembly guards and relevant runtime checks still need to pass after integration.

## Already fixed / stale documents

- RC6: overworld texture-frame crashes (Rocket HQ/Five/Seven Island), Bulbasaur reflections, Safari
  random-double crash, evolution moves, Nature Power/Attract references, type-name messages,
  Boldore/Gurdurr trade-only evolution, Poliwag nickname wording, repeated Red/cop line and listed UI fixes.
- Planned RC7: Lugia entrance callback bounds and reviewed Double Battle targeting, including horizontal
  fallback. The prior Lugia-only candidate hashes/checks are preserved separately in `rc7_validation.md`;
  its build report does not include targeting. Packaging/release of the combined contents are deferred.
- Double-battle targeting: the root `2v2BATTLE_CONTROL.md` is superseded by `double_target_armips_port.md`
  and `double_target_horizontal_validation.md`.
- The public guide still includes some fixed RC6 defects; do not use its headings as a live bug count.
- `softlock_audit.md` contains historical conclusions superseded by later emulator findings, including
  the S.S. Anne dead end and the already-fixed Rocket HQ crash.

The original triage was read-only. Follow-up builds and scoped repairs are recorded in the execution ledger above. No commits, merges, downloads or publication were performed for this run.
