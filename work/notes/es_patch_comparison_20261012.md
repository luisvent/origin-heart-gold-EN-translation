# Comparison with the Spanish patch (ES rc42), 2026-10-12

A third-party Spanish-language patch of the same hack, `Origin_HeartGold_v4.0.3_ES_v1.0.0-rc42.xdelta` (with its own
changelog), was compared with our English rc7. This note records what the comparison found, what we can adopt, what
we should not, and what is open. It contains no ROM bytes or text from the Spanish patch; the analysis files
(disassembly listings, extracted banks, rendered graphics) were kept in the session scratchpad and are not committed.

Method: the xdelta was applied to the user's US ROM (CRC32 `C180A0E9`) in a scratch directory; our rc7 xdelta was applied the
same way; both ROMs were compared with the untouched Chinese hack (`work/rom/origin_v4.0.3_cn.nds`) at file, NARC-member,
overlay and ARM9 level, then analysed by three read-only agents (code, scripts/data, text/graphics). "Verified" below means
byte comparison, decoding or disassembly; "inferred" means from addresses, constants or call shape (nothing was run in an
emulator on the Spanish ROM).

## 1. Provenance and rules

- The Spanish patch is **derived from the Speedoption/Bradams fork** that we analysed on 2026-10-05
  (`bradams_*` notes): 24 of its 25 settings-NPC event files, all 20 move-flag edits, the script 733 size change, the
  hard-mode flag 0x218, the level-cap flag 0x2C1 and the trainer-data veneers at 0x02072700/10 are the same. The code is
  re-encoded, not byte-copied. It adds a large new module of its own (about 118 KB).
- Its code is compiled Thumb C with an `ADAI` magic. We found no telltale of hg-engine or decomp code, but had neither
  locally, so that is absence of evidence only.
- **We cannot copy its bytes.** We do not know its licence; no source repository was consulted (nothing downloaded).
  Everything below that we adopt is re-derived from the Chinese ROM in our own patch format (AGENTS.md: sourced, credited).
  The route for the large features is to ask the author (see section 7).
- Its title screen uses a POKÉMON wordmark that looks like official logo lettering and drops the 起源心金 logo; no source
  or credit was found. We keep our bilingual title (D-0767) and must not copy theirs (AGENTS.md: never copy official logo art).

## 2. What the ES ROM changes (vs the Chinese hack)

| Layer | Finding | Evidence |
|---|---|---|
| ARM9 | ~40 small hook sites + ITCM autoload grown from 0x620 to 0x6B0C bytes (+25,836) + a third autoload block of 58,328 bytes at 0x02264920 | verified |
| Heap | main-arena start moved 0x02264920 → 0x02272D00 and the ITCM arena emptied: the main heap is 58 KB smaller | verified; hardware risk (cannot judge statically) |
| Overlay 10 | 32-byte stub → 108,000 bytes at 0x021E4DA0. First 73,824 bytes are identical to Chinese overlay 11 (the trainer-AI overlay); the other 34,176 bytes (~115 functions) are the new Advanced AI | verified |
| Scripts/data | 514 of 1024 trainers get a role byte (trainer header byte +2, NARC a/0/5/5); a settings NPC on 24 Pokémon Centre maps (+ script 2072, bank 38 #116–130); 14 battle sub-scripts in a/0/1/0 (inserted command 0x37 6) = sounds; Pikachu and Butterfree base stats changed (undocumented) | verified |
| Text | bank 718 (trainer text) grows from 1717 to 3440 strings (1,723 AI reaction lines); bank 38 +15; speaker-name colour tags on ~11,900 lines; battle_string has the same counts/tags as ours | verified |
| Not changed | the Chinese AI flags and AI scripts; the event gifts have **no** script or data edits (their IV/nature/ball work is native code + a 3,024-byte table) | verified |

### Advanced AI wiring (verified)
- The AI entry at overlay 14 0x02203736 is redirected to an ITCM dispatcher (0x01FF8C44). If the gate is true it jumps into
  overlay 10; otherwise to the original AI. A failure inside the new AI falls back to the original (matches their changelog).
- Gate (ITCM 0x01FF8BDC): flag 0x2C2 set, a trainer battle, and (flag 0x2C3 clear or this trainer's role bit 0 set).
- State: 0x179C bytes, cache of three, magic `ADAI`. A per-turn hook (overlay 14 0x02203C06) allocates 0xA84 bytes for the reaction engine.
- Settings are **ordinary event flags** in the save flag block, no new save field: 0x218 hard mode, 0x2C1 level cap,
  0x2C2 AI on, 0x2C3 AI "important only", 0x2C4 normal speed (clear = double speed). 0x2C2 was Speedoption's speed flag, so
  their saves are not interchangeable with Speedoption saves.
- Reactions/VS intro/shake/dodge/ball display (inferred) sit in a ~25 KB block (0x0226D10A–0x02272B64), thunks at
  0x0226AC54–0x0226AF50 and data edits in overlay 14 (0x0224ABC8–0x0224AC2C, 0x0224C88B), plus overlay 107/1 hooks and
  graphics in a/0/0/8. All of it depends on the AI module.

### Feature descriptions (from their changelog, plain language)
- **Hard mode:** rival levels about +15% (the NPC text lists level caps 12→80 normal, 14→92 hard), IVs max, EVs scale with
  badges, important trainers without items get a role-fitting item, affection gives no battle bonus, 10% less EXP, only
  participants/Exp. Share holders gain EXP, in-battle healing the original blocked stays blocked.
- **Advanced AI (Off / Important only / All):** knows your team, plans ~2 turns ahead, best attack, priority finishers, avoids
  immune targets and useless status moves, smart switching, lead choice against your lead, doubles coordination, occasional move prediction.
- **Reactions:** personality-grouped one-liners (calm, panicky, cheerful, honourable, thug, Team Rocket villain) for
  situations (last Pokémon, ace out/down, crit, you healing, win/loss closers, praising your best Pokémon); a sound when the
  trainer predicts your move; VS intro with portrait for important trainers; screen shake/flash on crits, super-effective KOs and last-Pokémon faint;
  dodge side-step; replayed send-out animation; touchscreen Poké Ball display (works against any trainer).
- **Event Pokémon:** IV31 all, tuned natures, egg/strong move, hidden ability when best, Gloria Ball; eggs keep it.
- **Other QoL:** double-speed default with toggle; player name in dialogue where the hack left it blank; speaker names in colour (player red).

## 3. Overlap with our fixes (same bug, different patch)

Same bug fixed by both: Magcargo and Rock Tunnel corner-loss (identical script edits), Pryce weather rule (ES: one native command),
evolution moves (same hook site 0x74BD4, ES trampolines into its blob), double-battle last target (same functions), Safari
no-wild-double (equivalent), zero-PP Struggle, Honey Gather, Cute Charm, Attract "(error)", Lilligant/Petilil (see section 4).
Ours are small, documented, `expect`-guarded patches with tests; theirs is ~190 KB of unreviewed code reached by trampolines.
**Do not stack the two on one ROM**: Honey Gather would double, and evolution-moves/targeting write the same bytes.

Hit sound and faint cry (our branches `fix/hit-sound` 7e49173 and `fix/faint-cry` 4996483, D-2281, excluded from rc7):

| | Ours | ES |
|---|---|---|
| Hit sound | in overlay 14 command 8 (BattleAct_MoveDamage) plays HeartGold's 1790/1788/1789 by effectiveness; centred; OHKO and Substitute silent | ITCM routine (~250 B) + 14 battle sub-scripts in a/0/1/0 (cmd 0x37 6); also covers Substitute (inferred), sandstorm, confusion |
| Faint | Faint_Run rewritten to play the cry (mode 5) + sound 1795, panned by side | cry and sound (changelog), implementation not decoded |
| Level-up jingle | not in our branches | ES restores it |
Next step for us: add the Substitute, sandstorm, confusion and level-up sounds to our branches by studying the sub-scripts (needs an emulator study first); keep our code approach.

## 4. Fixes we lack and can adopt (script/NARC level, re-derived from the Chinese ROM)

User, 2026-10-12: D-1337 no longer blocks fixes ("the Chinese rom contains too many bugs.. lets create a fix in a worktree").

| Fix | State |
|---|---|
| Weekday-sibling ribbon freeze (D-1331/D-1558): seven scripts run undefined command 2009 after the fanfare → same-size Noop | **done and reviewed (approved with notes)**, `fix/sibling-ribbon-freeze` 99bc4e6; emulator-proven on the Chinese ROM; Noop chosen over WaitFanfare (author intent unprovable); jingle not checked by ear |
| Petilil + Black Belt (D-1485): the special case built species 548 instead of Hisuian Lilligant (549 + form 1) | **done and reviewed (approved with notes)**, `fix/petilil-hisuian-lilligant` f4db3dc; emulator-proven (549, form 1, Hustle); ids 1109/1348/1371 share the off-by-one but are unreachable; regenerate species.json and work/docs/pokemon_1026-1440.md at merge |
| Romance mail (Cynthia branches check Snow Mail but take Heart/Bubble Mail; one fall-through shows Misty's line) | **done and reviewed (approved with notes)**, `fix/romance-mail-mismatch` 3f3af6a; static proof only; hardening only (Snow/Bubble Mail unobtainable); Misty love-letter branch left open (D-2332) |
| Blank player names: script fills buffer 0 where the text reads buffer 1 (member 111, Clair), Pallet photographer (733), Route 2 Brock line (171, found by scan) | **done and reviewed (approved with notes)**, `fix/blank-player-name` 47a3db1 + eba5ac9 (the reviewer caught a missed ApplyMovement operand in 171; corrected). About 48 further entries (~65 lines) stay open as D-2336 because each needs an inserted command |
| Lost battle vs Giovanni at the hot-spring map jumps to a heal text instead of white-out | **candidate**, needs an emulator repro first |
| Pallet photographer with no healthy party (CountAliveMons guard) | candidate; same guard exists in the Bradams fork; not in scope of the four |
| Route 3 scene: extra prefix (flag 1303 → ShowPerson) so actors appear after skipping a talk | candidate, inferred; check against the Route 3 findings |

Not to adopt: Pikachu/Butterfree base-stat changes (undocumented, conflicts with D-1002); the trainer role bytes (only feed their AI).

## 5. Text, graphics, UI

- Same 817 banks and ids as the Chinese plus the additions in section 2. No new battle messages. Their Attract/Rocks/Spikes/Hisui fixes are code changes, not text.
- **Speaker colour tags:** `{VAR:FF00:n}` around the speaker label on ~11,900 lines (FF00:2 generic/player red; 5 Green or Red; 6 Blue). We have 1,469 such tags, same as the Chinese. Cheap, text-only, worth considering (needs a width re-check and the user's decision on appearance).
- Player-name tags: the text banks do not explain their "name where blank" fix (it is in scripts: section 4). Check item: our 448#163 and 466#199 lack `{VAR:0103:0}` that the Chinese has (probably the deliberate gender-neutral choice, D-1224; confirm).
- Their 3#124 (Twineedle) drops the species name; ours keeps it. We have nothing to fix there.
- Our `{CLEAR}` count is ~3,400 lower than the Chinese (17,752 vs 25,140; ES 20,317). Line-wrap difference, cause not examined.
- TM descriptions "describing another move": could not isolate by similarity; spot checks of ours were fine. Unverified claim.
- **Graphics:** type/category icons and Pokédex labels are comparable in quality; title screen see section 1. a/0/5/8 has two more members than ours; the font NARC differs entirely (their Latin font).
- **Settings UI:** theirs is a talkative NPC in every Pokémon Centre with long explanations (good model for explaining hard mode); ours is an Options page 2/2 (ITEMS/SHARE/CAP) plus a site page. Both are valid; the NPC explains itself in game, the options page is faster to use.
- Translation process (inferred): consistent Latin-American Spanish, official Spanish names, character names kept in English, tone not noticeably softer in sampled lines.

## 6. Dangers if we ever combine or port

- Byte conflicts with our text-speed patch (main-loop hook 0x02000DE0, ITCM arena word 0x020D1A28, ITCM range from 0x620; ES fills ITCM to 0x01FFEB0C and uses the top ~700 B as RAM variables) and with evolution-moves, double-battle-targeting and honey-gather.
- Fixed addresses: the module depends on ~94 overlay-14 and ~108 ARM9 functions, ~85 overlay-14 and ~33 ARM9 patch sites, and keys roles by trainer index, and overlay 10 embeds a full copy of the Chinese overlay 11. **A hack v4.1.0 with any code shift breaks it.**
- Flag reuse (0x2C2) breaks Speedoption saves. Their flags were not checked against our flag use.
- Real-DS risk: 58 KB smaller main heap, ITCM completely used. We cannot judge this statically and our own hardware status is untested.

## 7. Decisions needed from the user

1. **Advanced AI / hard mode:** rebuild (high effort; ~34 KB new AI code needing ~200 fixed addresses; multi-week), or ask the Spanish author for a shared, language-neutral engine with per-language text (their reaction lines are language-specific; 1,723 lines to translate)? Not decided.
2. **Cheap features first** (all re-implemented by us): extra sounds in our branches, touchscreen Poké Ball display, dodge/shake, a "hard trainers" setting on our Options page 2/2, speaker colours.
3. **Matrix release:** this contradicts the settled "English only" rule (AGENTS.md); it needs that rule reopened. Recommendation (not a decision): one xdelta per language with every optional feature built in and off by default (switches in game, like both difficulty menus), plus at most a "base" variant for purists/hardware. The matrix is then language × {base, full}, not a combinatorial set of patches. Keep code patches separate from text so that only text needs redoing for 4.1.0.
4. **Do not wait for 4.1.0:** hooks are re-verified per version either way (our patches are `expect`-guarded and fail loudly on a shifted address; the Spanish module would break silently in places).
5. Misty love-letter branch (D-2332), the Giovanni hot-spring loss, speaker colours, `chmod a-w` on `work/rom/*` (see below).

## 8. Process incident (2026-10-12, 10:57)

The untouched Chinese ROM in `work/rom` was overwritten with a 1,117,496-byte bare ARM9 image by a scratch script of one of the parallel agents
(two agents named different causes: a scratch `dis.py` shadowing Python's `dis`, and an old emulator recipe). It was restored from a hash-verified copy
(sha256 `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8`, 536,870,912 bytes); the snapshot hard links were repaired by the in-place copy.
Prevention: run agent Python with `-I`, never name scratch files after standard modules, and consider making the ROMs read-only.
