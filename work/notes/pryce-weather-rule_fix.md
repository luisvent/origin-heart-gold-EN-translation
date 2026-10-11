# Pryce's weather rule: the check reads Abilities (fix `pryce-weather-rule`, D-2320)

**Historical branch status (2026-10-09): written and tested on branch `fix/pryce-weather-rule`, then disabled.** User-approved
exception to D-1337 (hack bugs are reported, not fixed), on a Discord report. The same day the user decided: "I am
not sure we want this change for Pryce to be honest. Keep it but disable." So `fix.toml` has `enabled = false`: the
default build keeps the hack's species check (its ROM equals the build without the fix, SHA-1
`85d0c887076b35949e2ed1b7f4cf0c5f75bcea77`; script 928 and arm9 0x0204CD0E as in the Chinese ROM), and
`emu_harness.py fixes --case all` leaves the `pryce` scenario out. To include the fix: `build.py --only <every
enabled fix>,pryce-weather-rule`; `emu_harness.py fixes --case pryce-weather-rule --rom <that ROM>` then judges it
(passed 2026-10-09 after disabling, same ROM SHA-1 `225f1bcf…` as before).

Current prep status (2026-10-10): D-2313/D-2320 explicitly enable this fix for RC7, overriding the parked choice above. `fix.toml` is enabled and the default fix scenario inventory includes Pryce. Historical artifacts below remain branch-specific.

## The report

> "The 7th Gym Leader of Johto [Pryce] tells me to use a team with no weather-changing Abilities. I have no
> Pokémon like that but he doesn't let me fight." A second player: "It doesn't look at the abilities but directly
> excludes 28 species."

Documented before the fix in `guide/known-issues.md`, "Pryce's weather rule".

## What the game tells the player

Bank 613 (Pryce's room, zone 140, event-script file 928):

- msg 0 (the challenge, before the Glacier Badge): 你不准使用能够靠特性改变天气的精灵，在这个条件下跟我来一场双打对战
  ("you may not use Pokémon that can change the weather by their Ability; under that condition, a Double Battle").
- msg 14 (the refusal): 咱们的规则是你不能使用靠特性改变天气的精灵 ... 你现在的随身精灵不符合条件.

The rule is about Abilities. Nothing in it names species.

## Cause

Script 1 of file 928 (`work/tools/docs/scriptdump.py 928`): after Yes, L252 `GetPartyCount 0x8005` (one Pokémon:
L1072, msg 36), then L269-L794 are 28 checks `PlayerHasSpecies 0x800C, <species>; CompareVarToValue 0x800C, 0;
GoToIf != -> L1083` (msg 14, end), then L801 `TrainerBattle 32, 32` (a Double Battle against one team).

Species and their Abilities in this hack (personal data `a/0/0/2`, abilities u16 at 0x16/0x18, hidden at 0x1A):

| # | Species | Abilities (1 / 2 / hidden) | a weather Ability? |
|---|---|---|---|
| 6 | Charizard | Solar Power / Blaze / Tough Claws | **no** (only the Mega Y form, Drought) |
| 37, 38 | Vulpix, Ninetales | Flash Fire / Flash Fire / Drought | hidden only |
| 87 | Dewgong | Thick Fat / Hydration / Snow Warning | hidden only |
| 144 | Articuno | Snow Warning / Snow Cloak / Slush Rush | first |
| 186 | Politoed | Damp / Drizzle / Azure Skin | second |
| 218, 219 | Slugma, Magcargo | Magma Armor / Weak Armor / Drought | hidden only |
| 230 | Kingdra | Swift Swim / Sniper / Drizzle | hidden only |
| 244 | Entei | Flash Fire / Inner Focus / Wildfire | hidden only |
| 248 | Tyranitar | Sand Stream / Sand Stream / Intimidate | not the hidden one |
| 279 | Pelipper | Keen Eye / Drizzle / Rain Dish | second |
| 321 | Wailord | Water Veil / Sheer Force / Drizzle | hidden only |
| 324 | Torkoal | White Smoke / Drought / Shell Armor | second |
| 369 | Relicanth | Sturdy / Rock Head / Sand Stream | hidden only |
| 382 | Kyogre | Drizzle / Storm Drain / Primordial Sea | not the second |
| 383 | Groudon | Drought / Tough Claws / Desolate Land | not the second |
| 384 | Rayquaza | Air Lock / Aerilate / Delta Stream | hidden only |
| 449, 450 | Hippopotas, Hippowdon | Sand Stream / Sand Force / Strong Jaw | first |
| 459, 460 | Snover, Abomasnow | Snow Warning / Snow Warning / Soundproof | not the hidden one |
| 476 | Probopass | Sturdy / Magnet Pull / Power Spot | **no** |
| 478 | Froslass | Levitate / Snow Cloak / Snow Warning | hidden only |
| 526 | Gigalith | Sturdy / Sand Stream / Sand Force | second |
| 698, 699 | Amaura, Aurorus | Refrigerate / Solid Rock / Snow Warning | hidden only |
| 873 | Frosmoth | Shield Dust / Snow Warning / Ice Scales | second |

So the hack bans by species: Charizard and Probopass can never change the weather and are always refused, and most
listed species are refused with an Ability that changes no weather. Species with a weather Ability that are not
listed pass: Vanilluxe (584, Snow Warning hidden), Silicobra and Sandaconda (843, 844, and Sandaconda's form 1:
Sand Spit), Koraidon (1007, Orichalcum Pulse), Terapagos's Stellar form (Teraform Zero). Eggs are skipped:
`PlayerHasSpecies` (arm9 0x0204D3D4) ignores eggs.

## Which Abilities change the weather

From the hack's Ability descriptions (bank 712; names bank 711), the Abilities that set, replace or remove the
weather when they act:

| id | Ability | zh | effect (bank 712) |
|---|---|---|---|
| 2 | Drizzle | 降雨 | rain on entry |
| 45 | Sand Stream | 扬沙 | sandstorm on entry |
| 70 | Drought | 日照 | sun on entry |
| 117 | Snow Warning | 降雪 | hail on entry |
| 189 | Primordial Sea | 始源之海 | weather that blocks Fire moves |
| 190 | Desolate Land | 终结之地 | weather that blocks Water moves |
| 191 | Delta Stream | 德尔塔气流 | winds that remove Flying weaknesses |
| 245 | Sand Spit | 吐沙 | sandstorm when hit |
| 288 | Orichalcum Pulse | 绯红脉动 | sun on entry |
| 309 | Teraform Zero | 归零化境 | erases weather and terrain (Stellar Terapagos) |
| 313 | Wildfire | 霹雳火 | harsh sun (the hack's own Ability) |

Not counted, because they leave the weather as it is: Cloud Nine (13) and Air Lock (76) cancel the weather's
effects; Forecast, Flower Gift, Ice Face, Protosynthesis and the speed/evasion/heal Abilities react to weather; Mega
Sol (321) uses moves "as if" in harsh sun. Teraform Zero is the one judgement call: it removes the weather rather
than setting one; it is counted because removing Pryce's hail changes the weather. (A party Terapagos normally
holds Tera Shift, so this only matters for a Stellar-form Terapagos in the party.)

## The fix

No script command reads a party Pokémon's Ability (`work/tools/docs/script_cmds.json`: 843 commands, none). Two
edits, both armips (`work/patches/pryce-weather-rule/`):

1. **arm9 0x0204CD0E** `add r4, #0x13` -> `nop`. Script command 542 `MonGetContestValue slot, type, ret`
   (`0x0204CCC0`) returns `GetMonData(Party_GetMonByIndex(party, slot), 0x13 + type)`. No script of the hack uses
   the command (every reachable command of every script file in `a/0/1/2` was checked), so without the add it
   becomes "get GetMonData field N" without changing anything else. Fields used: 10 = the Ability (the hack's u16
   at block B +0x1A, `ldrh r4, [r5, #0x1A]` at 0x0206DC32; the Ability the summary shows, harness note of
   2026-10-06), 76 = the egg bit (0x0206DD00).
2. **script 928 L269-L800** (532 bytes, the 28 checks): `SetVar 0x8004, 0`; per slot `MonGetContestValue
   0x8004, 76, 0x800C`, an egg -> next slot; `MonGetContestValue 0x8004, 10, 0x800C`, then 11 x
   `CompareVarToValue 0x800C, <Ability>; GoToIf == -> L1083`; `AddVar 0x8004, 1; CompareVarToVar 0x8004, 0x8005;
   GoToIf < -> loop`; `GoTo L801`. 0x8005 still holds the party count from L252. The unused rest (329 bytes) is
   zero-filled and never reached. The new code is 201 bytes, so the file keeps its size and every other offset.

The script file is patched like code: the patch toolchain now accepts a `[[code]]` file `scriptNNN` (member NNN of
`a/0/1/2`), staged as `scriptNNN.bin` and opened at 0 (`work/notes/toolchain.md`, "Conventions"). The asm guards
each of the 28 old checks (command, species, jump target), the refusal (L1083 NPCMsg 14) and the battle (L801),
the command table entry, the whole routine and the two GetMonData cases; fix.toml pins the old block's SHA-1.
`text_speed_patch.registry_code_patches` skips script-file regions (they are not code text speed pins).

Not changed: the rule text, the one-Pokémon check, the battle, the post-Badge rematches (L1124, L1167: "no
restrictions"). Mega Evolution and Primal Reversion are not foreseen: a Charizard holding Charizardite Y passes
(its Ability is Blaze or Solar Power until it Mega Evolves in battle), as does a Kyogre with Storm Drain holding
the Blue Orb; see the open question below.

## Evidence

Builds (2026-10-09, `work/build/fixed`, `work/build/control`): full build ROM SHA-1
`225f1bcf77eb61d5dd8f52ffd9a3a868639a47a0`; `--without pryce-weather-rule` `85d0c887076b35949e2ed1b7f4cf0c5f75bcea77`.
They differ only in arm9 (2 bytes at 0x4CD0E) and `a/0/1/2` member 928.

**DeSmuME** (`emu_harness.py fixes --case pryce-weather-rule`, scenario `pryce`; PASS: fixed ROM `fixed`, control
`original`). Party: the save's slots 0-1 (Charmeleon, Butterfree) plus the test Pokémon in slot 2:

| case | full build | `--without` build | Chinese ROM |
|---|---|---|---|
| Charizard, Blaze | battle | refused | refused |
| Probopass, Sturdy | battle | refused | refused |
| Politoed, Damp | battle | refused | refused |
| Politoed, Drizzle | refused | refused | refused |
| Ninetales, Drought | refused | refused | refused |
| Tyranitar, Sand Stream | refused | refused | refused |
| Abomasnow, Snow Warning | refused | refused | refused |
| Egg (Politoed, Drizzle) | battle | battle | battle |
| Vanilluxe, Snow Warning, in slot 6 (slots 2-4 Charmeleon) | refused | battle | battle |

**melonDS 1.1** (no execution hooks, so a hand probe kept out of the repo: the battery save gets Pryce's object
(script 1, sprite 358 at 7,4, copied from a saved NPC record), the player below him and the follower behind; A
through the rule and Yes; "battle" = the field overlay left): full build Charizard Blaze battle, Probopass Sturdy
battle, Politoed Drizzle refused, Abomasnow Snow Warning refused; `--without` build Charizard Blaze refused,
Politoed Drizzle refused; Chinese ROM Charizard Blaze refused. No ARM9 abort in any run.

`check.py --full` passes (expected.toml updated: the non-text hash moves with this fix; the text hash recorded on
develop was already stale before this branch).

## Other Gym rules that ban by species (not changed)

Each says a type or a stat and checks a fixed species list (`guide/known-issues.md`):

- Morty, "weak to Ghost" (file 918, L1140-L13661, 660 species): refuses Exeggutor and Rotom, lets Stunfisk, Yungoos
  and Gumshoos in.
- Jasmine, base Defense 130 or more (file 909, L839-L14918, 742 species): refuses Aegislash, lets Stunfisk, Yungoos
  and Gumshoos in.
- Chuck, Fighting only (file 874, L1213-L14950, 724 species): refuses Staraptor (Fighting/Flying here), lets 618,
  628, 734, 735 in.
- Clair, Dragon only (file 939, L853-L14096, 698 species): lets many non-Dragons in (Seadra, Magmar, Porygon, ...).

A type rule could use the existing command 497 `GetMonTypes` (unused by the hack's scripts) without a code change;
a base-stat rule has no command and no GetMonData field.

## Open questions for the user

- Mega Evolution / Primal Reversion: should a party Pokémon that only gets a weather Ability in battle (Charizard
  with Charizardite Y, Kyogre/Groudon with their Orb and a non-weather Ability, Rayquaza) be refused too? The fix
  checks the Ability the Pokémon has, as the rule text says it literally.
- Teraform Zero is counted as weather-changing (it erases the weather). Keep?
- The guide's "Pryce's weather rule" known issue describes the hack; it should say the English patch fixes it once
  merged.
