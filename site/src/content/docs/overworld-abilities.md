---
title: Overworld abilities
description: Which abilities do something outside battle in Origin HeartGold v4.0.3 (encounter rates, levels, natures, genders, held items, egg hatching, Pickup and more), read from the game's own code.
---

Some abilities matter before a battle starts: they change which wild Pokémon you meet, how often you meet them, how fast Eggs hatch and what you find afterwards. This page lists every one found in the game's code, with the numbers the **Origin HeartGold v4.0.3** hack really uses. Several differ from the original HeartGold, so older guides will be wrong.

## How the rules work

- **Lead means the first Pokémon in your party.** Only that slot counts, even if it has fainted. If the first slot holds an Egg, no lead ability works at all. Hidden Abilities count like any other.
- **Whole-party abilities** are the exception: Flame Body, Magma Armor and Pickup look at everyone in your party.
- Lead abilities also apply to scripted wild battles, not only to grass, caves and water.
- Percentages are the game's own rolls. They are chances per encounter, not guarantees.

## Which wild Pokémon you meet

| Ability | Needs | Effect |
|---|---|---|
| [Synchronize](../abilities/synchronize/) | Lead | The wild Pokémon **always** has the lead's Nature. In the original game this was only 50%. |
| [Cute Charm](../abilities/cute-charm/) | Lead | 2 in 3 chance the wild Pokémon is the opposite gender of the lead. Species that are always one gender or genderless are not affected. |
| [Static](../abilities/static/) | Lead | 1 in 3 chance the encounter is picked only from the **Electric**-type Pokémon of that area, if there are any. |
| [Magnet Pull](../abilities/magnet-pull/) | Lead | The same, for **Steel** types. |
| [Flash Fire](../abilities/flash-fire/) | Lead | The same, for **Fire** types. New in this hack. |
| [Storm Drain](../abilities/storm-drain/) | Lead | The same, for **Water** types. New in this hack. |
| [Harvest](../abilities/harvest/) | Lead | The same, for **Grass** types. New in this hack. |
| [Lightning Rod](../abilities/lightning-rod/) | Lead | Forces an Electric type, but only when the game is choosing which of the visible overworld Pokémon to spawn. |
| [Compound Eyes](../abilities/compound-eyes/) | Lead | Wild Pokémon hold items more often: no item 20% (instead of 45%), common item 60% (50%), rare item 20% (5%). |

In testing, a Static lead in grass with Electric Pokémon among the slots (about 1 in 10 normally) gave an Electric encounter roughly 4 times in 10.

### Wild levels

| Ability | Needs | Effect |
|---|---|---|
| [Hustle](../abilities/hustle/), [Pressure](../abilities/pressure/), [Vital Spirit](../abilities/vital-spirit/) | Lead | 1 in 2 chance the wild Pokémon is at the **highest level its slot allows**. In grass there is also a 1 in 2 chance of choosing the highest-level slot of the same species. |
| [Intimidate](../abilities/intimidate/), [Keen Eye](../abilities/keen-eye/) | Lead | 1 in 2 chance a wild encounter is cancelled when the wild Pokémon would be **5 or more levels below** your lead. Needs a lead above Lv. 5. |

## How often you meet them

| Ability | Needs | Effect |
|---|---|---|
| [Illuminate](../abilities/illuminate/), [No Guard](../abilities/no-guard/), [Arena Trap](../abilities/arena-trap/) | Lead | Encounter rate **doubled**. |
| [Stench](../abilities/stench/), [White Smoke](../abilities/white-smoke/), [Quick Feet](../abilities/quick-feet/) | Lead | Encounter rate **halved**. |
| [Snow Cloak](../abilities/snow-cloak/) | Lead | Encounter rate halved in snow. The only places with snow are the Mt. Silver summit and one snowfield, and neither has wild Pokémon, so this does nothing in practice. |

## Eggs and items

| Ability | Needs | Effect |
|---|---|---|
| [Flame Body](../abilities/flame-body/), [Magma Armor](../abilities/magma-armor/) | Anyone in the party | Each Egg step check removes **8** hatch cycles instead of 1: Eggs hatch about eight times faster. Several of these Pokémon do not stack. In the original game the effect was only 2×. |
| [Pickup](../abilities/pickup/) | Anyone in the party | After a battle, 10% chance per Pokémon to find an item, sent straight to the Bag. See the [Pickup chart](../mechanics/#pickup). Eggs do nothing. |
| [Honey Gather](../abilities/honey-gather/) | — | **Does nothing** in the original hack: it never gives Honey. A repair exists but is not part of the standard patch. |

## Fishing and Rock Smash

| Ability | Needs | Effect |
|---|---|---|
| [Sticky Hold](../abilities/sticky-hold/), [Suction Cups](../abilities/suction-cups/) | Lead | The bite chance when fishing is **doubled** (read from the game's code; not tested in game). |
| [Suction Cups](../abilities/suction-cups/), [Magnet Pull](../abilities/magnet-pull/), [Keen Eye](../abilities/keen-eye/) | Lead | +5 percentage points to the chance that smashing a rock turns up an item (only on the maps where rocks can hold items). |
| [Serene Grace](../abilities/serene-grace/), [Super Luck](../abilities/super-luck/) | Lead | Rock Smash items shift towards the rarer ones. |

## Abilities with no overworld effect found

Run Away and Sand Veil do nothing outside battle in this hack. This is the result of searching the game's code for every place an ability is read, not a proof, so a rare exception could be missing.

## Known problem: surfing with a Harvest lead

In testing on the original Chinese hack, surfing with a **Harvest** lead sometimes started a battle against a broken Pokémon: a wrong species at Lv. 1, or one with no name. This happened in about a third of surf encounters in the test setup. The game scans 12 slots while a water table only fills 5, so leftover data can be picked. Nothing froze in the short tests. Until this is fixed, avoid Harvest as the lead on water. In the same test Static, Magnet Pull and Flash Fire did nothing odd. Storm Drain produced no broken Pokémon, but by the same slot logic it probably makes the rare water Pokémon of that spot much more common (not tested on an all-water spot).

<small>Everything above except the notes marked "not tested" was confirmed in the emulator against the untouched Chinese hack. This page was last checked against v4.0.3.</small>
