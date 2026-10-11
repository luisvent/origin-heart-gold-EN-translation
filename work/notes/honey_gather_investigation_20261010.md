# Honey Gather investigation — 2026-10-10

Honey Gather is omitted from the hack's post-battle item collector. The reported
Combee receiving no Honey is consistent with the code: ability 118 is skipped
before any random roll or item award. Registered as **D-2324**.

The initial finding was static. The follow-up below implements and tests the
user-authorized repair in an isolated worktree. Whether the original omission
was intentional is unknown.

## Original hack

Read directly from untouched `work/rom/origin_v4.0.3_cn.nds`, overlay 14
(load address `0x022007E0`), collector `0x0222BCC8`:

| Address | Behavior |
|---|---|
| `0x0222BCFE` | Obtain the next party member's battle record. |
| `0x0222BD0A` | Read its ability through `0x02217BF8`. |
| `0x0222BD1A–0x0222BD24` | Skip Eggs (Pokémon data selector `0x4C`). |
| `0x0222BD26` | Compare ability with `0x35` = 53 = Pickup. |
| `0x0222BD28` | If unequal, branch to `0x0222BD9A`, the next-party-member path. |
| `0x0222BD2A–0x0222BD32` | For Pickup only, test the nominal 10% activation gate. |
| `0x0222BD3E–0x0222BD98` | For successful Pickup, select a level-dependent reward and add one directly to the Bag. |

The ability-name bank `a027/0711` independently identifies Pickup as 53 and
Honey Gather as 118 (`0x76`). Thus Honey Gather fails the ability comparison
and never reaches the RNG or award. Level and an empty held-item slot cannot
change that result. This routine has no Honey Gather branch and does not test
the held-item slot. Its level calculation belongs to Pickup's reward table,
not a Honey Gather activation chance.

Two direct calls to the collector occur at `0x0220313C` and `0x022034F4`.
Their surrounding state machines consume the returned item list to report
awards. The inspected battle overlay has no immediate comparison with ability
118. No separate Honey Gather award path was identified. This absence search
is supporting evidence; the explicit Pickup-only branch is the decisive local
control-flow evidence.

## Vanilla comparison

The user's USA HeartGold ROM has a combined Pickup/Honey Gather handler in
overlay 12 at `0x022440A0`. It checks ability 118 at `0x02244190`, requires no
held item, determines the level band, and reads the probability table at
`0x0226CA58`: `5, 10, 15, 20, 25, 30, 35, 40, 45, 50` percent. A successful
roll sets held item 94 (Honey), at `0x022441E6–0x022441F0`.

This verifies the reported standard mechanic from the local retail executable.
The hack uses its own collector, which retains Pickup but lacks that branch.
It does not establish why the original author omitted it.

## Chinese/English parity and evidence

The complete collector range `0x0222BCC8–0x0222BDBF`, both inspected caller
ranges (`0x02203118–0x022031E7`, `0x02203450–0x022035DF`), and the ability getter
are byte-identical between untouched Chinese and the current local English
WIP. This is an original-hack issue, not a translation regression in those
paths. It is not a claim about every historical English release or third-party
fork.

- Chinese ROM SHA-256: `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8`.
- Inspected English WIP SHA-256: `6fa7b4e739391ca9ea9bfcf90d83eec6407c3c04102e52432bb41bc8ae44a7d3`.
- Collector SHA-256, both: `6ca60b1714bf56eb8e171532c6d3e6ee7069b6c440802f30bfcc3cb49cee5f07`.

Private evidence is retained under ignored
`work/build/honey-gather-audit-20261010/`: `evidence.json`, Chinese/English
collector and caller disassemblies, and `us-retail_collector.txt`. ROMs were
parsed with existing ndspy and disassembled with existing Capstone. No tools
or datasets were downloaded for the investigation.


## Authorized repair and risk

The user requested investigation of similar mechanics and a fix in a worktree,
then selected **Honey to the Bag**, retaining the empty-held-item check and
level-scaled chance. D-2325 records this exception to D-1337 in the main
checkout's decision register. This worktree starts at `a657a13`; its older
register does not yet contain D-2324/D-2325. Those existing records must accompany
integration; the worktree deliberately does not copy unrelated uncommitted
register changes or allocate competing IDs.

`work/patches/honey-gather` replaces only the original 248-byte collector
allocation, including its private literal pool. No overlay growth, save-format
change, text change or new hook is needed. Honey Gather rolls once per eligible
party member, skips Eggs and nonempty held-item slots, and adds one item 94 on
success. It reads the original ability at actor+0x16 (as Pickup already did),
the held item at actor+0x20, and level at actor+0x24. Chance is
`5 * (min((level - 1) / 10, 9) + 1)` percent with integer division.

The common award path now checks Bag_AddItem's return value before populating
the message list. The native Pickup path did not check it (D-2326): a rejected item
still incremented the announced reward count. The repair applies the same
success rule to both abilities. Pickup's 10% gate, level reward table, ability
source, allowance for an existing held item, and order of random draws stay
unchanged. Failed Honey awards are not retried or converted into held items.

Risk is bounded but not zero: the collector is shared with Pickup, so a bad
register, output-list or probability change could affect all post-battle item
collection. Original-byte guards reject unsupported binaries; instruction
replays compare Pickup's outputs and RNG calls against the original, and native
replays exercise the actual Bag and battle return paths. Real hardware and
special link/facility outcomes are not covered. Caller outcome eligibility is
unchanged; this does not promise Honey after every kind of battle exit.

## Related-mechanics audit

All addresses below are in the original Chinese overlay 14. This is a targeted
static audit, not a claim that every item-related mechanic has been playtested.

| Mechanic | Evidence and conclusion |
|---|---|
| Post-battle Pickup | Same collector; it works but ignores Bag_AddItem failure at 0x0222BD7C. The shared award check fixes the false report. |
| In-battle Pickup (53) | Ability provider 0x02232804 registers event 0x16 -> 0x02232810. It requires an empty held item, selects another battler's consumed item and queues an item grant. This is distinct from random post-battle rewards. |
| Harvest (139) | Provider 0x02234CF0 registers event 0x16 -> 0x02234CFC. Handler reads the consumed-item field, checks the berry classifier 0x02225F6C and empty held item, then a weather bypass or 50% gate before queuing the restored berry. Its handler is present; Honey's missing branch does not explain a Harvest failure. |
| Ball Fetch (237) | Provider 0x022376C4 registers event 0x16 -> 0x022376D0. It checks the empty held item and the recorded failed-ball flag/ID, then queues an item grant. It does not depend on the post-battle collector. |
| Pickpocket (124), Magician (170), Symbiosis (180) | Separate ability providers/event handlers. They use the battle item transfer system rather than this collector. Their full trigger matrices were not replayed. |
| Recycle (move 278) | Move table entry 0x02252040 -> provider 0x0223F698; event table 0x022506E0. It has a move handler, independent of the post-battle collector. |
| Held-item persistence | 0x0222B910 -> 0x0222BA00 -> 0x0222BA58 separately reconciles battle-result and original held items, including berry and transfer cases. The repair leaves this policy intact and avoids it by granting Honey through Bag_AddItem. An item disappearing after battle needs its own trace through this reconciliation. |

Ability registration is through 0x0223AAA0 / 0x0223AA5C and the pointer table
at 0x0224FF2C, indexed by ability ID. Honey Gather's entry is zero. The
0x02251C90 table is the **move** registration table, not an ability table:
matching the numeric ID alone would misidentify unrelated move handlers.

## Verification

The bounded Thumb runner executes the assembled original or patched collector
with native-helper stubs that deliberately clobber volatile registers and
flags. It is an instruction regression test, not a complete emulator.

- All 100 levels × all 100 Honey chance rolls, including band boundaries.
- Original collector reproduces zero Honey even at level 100.
- Eggs, held items, unrelated abilities, empty party, mixed party and six holders.
- Full Bag and one remaining capacity unit; no phantom output-list entries.
- Pickup matches original for all 100 reward rolls at both ends of all ten level
  bands, including an already-held item, and all failed chance rolls.
- Callee-saved registers, aligned stack and output-list bounds.
- Guard rejection, changed-byte confinement and unchanged overlay size.

Run from this worktree root with the existing local armips configured:

```sh
ARMIPS=/path/to/armips .venv/bin/python work/tools/test_honey_gather.py
.venv/bin/python work/tools/asmpatch.py --armips /path/to/armips check --only honey-gather
.venv/bin/python work/tools/asmpatch.py --armips /path/to/armips listing --check honey-gather
python3 work/tools/fixes.py check
```

Native replay uses `work/tools/emu_honey_gather.py`: first `--prepare-only`
generates valid Pokémon with the game's generator and exports a private save;
then each `--prepared SAVE --cases CASE` replay boots a fresh emulator process.
This avoids unsafe live party replacement and DeSmuME's unsafe in-process
restart. Early live-RAM fixture failures are retained as diagnostic attempts,
not used as evidence of a game or patch bug. Successful runs assert valid
post-battle records and record source-save hash comparisons. Only the collector's RNG
seed is controlled at entry; the native chance, Bag, messages and battle flow
execute normally.


### Native replay results

DeSmuME 0.9.12, isolated saves, level-100 generated Mewtwo fighting with Psychic,
level-31 generated Combee on the bench. Wild fixture: scripted level-5 Rattata;
trainer fixture: trainer 185. A controlled seed at collector entry makes the
first Honey gate succeed; seed 1 makes it fail. This checks real battle return
and Bag behaviour without relying on lucky rolls. The multiple-holder fixture
has two independent rolls; with seed 0 only the first succeeds.

| English patched case | Result |
|---|---|
| Wild win | Honey 1 → 2; returned one reward, item 94 in Combee's output slot. |
| Trainer win | Honey 1 → 2; returned one reward. |
| Already holding Honey | Bag unchanged; no award call. Held item remains 94. |
| Honey stack at 999 | Bag unchanged; native Bag_AddItem rejects the attempted award; returned zero rewards. |
| Failed chance roll | Bag unchanged; no award call. |
| Flee | Bag unchanged; collector never entered. |
| Two Honey Gather holders | Honey 1 → 2; only the first chance roll succeeds. |
| Pickup with an existing held item | Returned item 11 and added it to the Bag; existing held item remains 1. |

Paired Chinese controls use the same private prepared save: original Honey
Gather returns zero and adds nothing, while the fixed collector returns one and
adds Honey. With Pickup and item 11 already at 999, the original returns one
reward despite no Bag change; the fixed collector returns zero. This reproduces
and corrects D-2326 in the native game.

All successful replays return to the field with valid party records. The seed
save is unchanged. The paired Chinese runs additionally hash-check the prepared
save. Evidence lives under ignored `work/build/honey-gather/verified-*`, including
per-case JSON, ROM hashes and screenshots. Earlier `runtime-*` and `debug`
folders are exploratory and are not the final verification set.

Only 216 bytes differ in each test ROM, all inside the declared 248-byte
collector region; ROM and overlay lengths are unchanged. Inputs are the
Chinese/English hashes recorded above. Patched test image SHA-256:

- Chinese: `03ba5c2d8cfe9e73d5891a825fde06be7dd03b16b46fe9bb54fd6877890a050e`.
- English: `2e955ff50f43b79a638e399a7c7a263b2f2034f5b447ac5c46a1cc9df94d9a6f`.

Eight instruction tests pass, plus registry, assembly, listing, Python lint and
format checks. This is an isolated patch applied to existing local test images,
not a newly packaged release or a full rebuilt English translation. No ROM or
save is included in git; no hardware, link battle or battle-facility claim is
made. The other mechanics in the audit table were checked statically only.


### Review follow-up: false reward assertions (P3)

The original native replay checked unchanged Honey quantity for negative cases
without asserting the collector's returned reward count or item list. A false
award announcement could therefore pass that check. The recorded outcomes were
correct; this was a gap in the replay's regression protection.

`emu_honey_gather.assert_rewards` now requires exactly one observed collector
entry and return, a zero reward count, and a zero item ID for every active party
slot for held-item, failed-roll, full-stack and original-Honey controls. It also
checks zero output items for patched Pickup with a full stack. Held-item,
failed-roll and original-Honey controls must make no Bag_AddItem call; full-stack
patched cases must attempt exactly one insertion of the expected item. The
return hook captures only active party slots instead of always reading three.

`test_emu_honey_gather.py` injects false counts, stale item IDs and complete
phantom awards while keeping Bag quantities unchanged. It also rejects missing
or duplicate call hooks, missing/nonzero party output slots and unexpected Bag
calls. The original Pickup full-stack false award remains an explicitly allowed
baseline control; the patched case rejects it.

Run the six replay-validation tests with:

```sh
.venv/bin/python work/tools/test_emu_honey_gather.py
```

All six replay-validation tests pass. Five fresh native replays also pass with
the stronger assertions: English held-item, full Honey stack, failed roll and
full Pickup stack, plus the untouched Chinese Honey omission control. Each
returns count 0 with `[0, 0]` for the two active party slots; held-item,
failed-roll and original-Honey runs make no Bag call. Both full-stack runs make
one rejected insertion and return no rewards. Evidence is in ignored
`work/build/honey-gather/p3-*/result.json` and `p3-summary.json`. All source and
prepared save hashes still match. The game patch itself is unchanged.
