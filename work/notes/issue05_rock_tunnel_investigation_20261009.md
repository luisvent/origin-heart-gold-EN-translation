# Issue 5 — Rock Tunnel corner-child loss investigation, 2026-10-09

**Proceed to reproduction.** The native loss branch is demonstrably aimed at the
wrong child's dialogue. The smallest sensible candidate is to send that branch
to the same file's existing whiteout block. This stage made no production edit,
ROM build, runtime run, source-save change, download or commit. D-2300 authorizes
the eventual scoped fix, superseding D-1337 for this issue after reproduction.

## Native behavior and candidate

Zone **342** is Rock Tunnel, with scripts `a/0/1/2` member **129**, events member
**313**, messages bank **142**. Object **17** is at **43,98**, has no hide flag,
and invokes script **18**, entry **1624**. Stand at **43,99**, facing UP, and talk.
The script checks flag **1966**: if clear, it starts the challenge at L2872;
if already set, it gives the post-win conversation and ends without a battle.

| Offset | Native command / effect |
|---|---|
| 2872 | Introductory message 75; wait and close |
| 2879 | `TrainerBattle 606,0,0,0` |
| 2887 | `CheckBattleWon 0x800C` |
| 2891 | Compare result with zero |
| 2897 | If equal (loss), jump to **L3782** |
| 2904–2917 | Win: message 76, set **1966**, release, end |
| 2734–2738 | Existing **WhiteOut; ReleaseAll; End** block |

The trainer arguments are two u16 trainer IDs followed by two u8 options.
The native handler at **0x02048B64** reads them in that order and calls the battle
task at **0x02050768**. Here the second trainer is zero: a single trainer battle.
Historical runtime establishes that third argument **0** does not restore the
field after a defeat; scripts must explicitly white out. Third argument **1**
permits returning to the field after defeat. It is a diagnostic control, not the
recommended repair. `CheckBattleWon` is opcode 220, handler **0x02048DF0**;
`WhiteOut` is opcode 219, handler **0x02048DE4**, calling **0x02051B3C**.

L3782 belongs to the **Pikachu-disguised child**, normally reached from script 12
and its question menu. It opens message 46 and another menu; agreeing twice can
set **1554** without a battle, while refusal starts trainer **194**. Both trainer
194 loss routes already jump to L2734. The archaeologist child's trainer **523**
and rock child's trainer **208** also use L2734. In total, seven existing battle
loss branches in member 129 use this block. This is strong same-scene evidence
for ordinary whiteout on the corner child's defeat; the incorrect cross-child
dialogue is not a meaningful loss route.

Recommended candidate, **only after reproduction**: replace the signed u32
relative displacement at member offset **2900 / 0xB54**:

```text
expect raw bytes: 6e 03 00 00   (+878: 2904 + 878 = 3782)
new raw bytes:    56 ff ff ff   (-170: 2904 - 170 = 2734)
TOML halfwords:  expect = "036E 0000"; new = "FF56 FFFF"
```

This preserves the condition, trainer, loss option, battle itself, win message,
win flag, and all file/header offsets. A scratch in-memory disassembly check
confirms **only instruction 2897 changes**, with unchanged member size and header
entries. The existing `kind = "narc"` / `[[narc_bytes]]` pipeline can guard the
whole source member SHA-1 and these four bytes; no engine patch is needed.

## Progress readers and side effects

All reachable literal CheckFlag/SetFlag/ClearFlag commands for **1966, 1554,
1884, 1885, 1868** occur only in file 129. None is an object-hide flag in the
event archive. Flag 1966 is checked at **1302** (all-four-found reward gate),
**1632** (corner child retry/post-win state), and **2812** (archaeologist's
follow-up offer). Its only writer is the win at **2911**. Flag 1554 is the
Pikachu child's completion; writers **3847,4433,5173** are its own routes.

Script 8, object 13, checks all four completion flags **1554/1966/1884/1885**
before giving reward item **407**, then sets reward flag **1868**. A repaired
loss must leave these flags unchanged and permit a later retry. Whiteout uses
native healing, respawn and monetary behavior already used by this scene;
verify those instead of replacing them with a custom heal or forced victory.
This reader scan covers reachable literal script commands and event flags, not
an exhaustive proof against dynamically supplied flag IDs elsewhere.

## Existing observations and limits

D-1395 was an initial untested static interpretation; **D-1548 corrects it**.
The 2026-10-06 private reports show the real object interaction freezes after a
Splash-only party loses, on both CN and the then-current English build:
field never returns, map stays 342, no post-battle message, flag 1966 stays clear.
Recorded PCs are CN **0x022A2974** and EN **0x022A220C**. The reports' `pc_in_heap`
test accepts the broad range 0x02200000–0x02400000, which also contains overlays;
that test alone is **not proof of executing heap memory**. Fresh reproduction
should capture the stopped screen, script/task PCs and lack of field restoration.

Historical injected controls, same trainer and save: `606,0,1,0` returned to
Rock Tunnel; `606,0,0,0` followed by `WhiteOut` returned to Pokémon Center map
501. These were **injected diagnostic scripts**, not a repaired native branch.
The historical reports contain no interpreter opcode trace proving execution
of L3782; static control flow identifies the intended next branch.

Evidence: `work/build/harness/guide01_07/report_corner_kid.json` (CN),
`report_electrode_corner_kid_blue_saffron_en.json` (EN), and the six
`<cn|en>/corner_{real,canlose,whiteout}_after_loss.png` screenshots.
The EN report also contains an unrelated Blue case error; its corner controls
all completed. `work/notes/emu_harness.md` section 7 records the old recipes.

## Concrete reproduction handoff

The historical command `emu_harness.py guide0107 --case corner_kid` is **no longer
callable**: cleanup commit **2e6fe55** removed `emu_guide0107.py` and its helpers.
Read the old recipe with `git show 2e6fe55^:work/tools/emu_guide0107.py`; adapt only
needed functions into the next agent's ignored issue05 scratch runner, without
restoring obsolete production modules.

1. Run **one emulator at a time**, from repo root, using current `.venv`, native
   DeSmuME and `emu_harness.start_at`. Resolve output/ROM/save paths before the
   harness changes process directories. Preserve the source battery save hash.
2. Fresh boot with a private copy of `full_bag_6mons.sav`, pinned noon
   2026-10-09. Clear 1966 and 1554 only in the private fixture, recording all
   four found flags and 1868. Set every existing party member's moves to Splash
   150 with PP 40 through the strict party editor; keep legitimate HP/count.
3. Warp to **342,43,99,UP**, wait 60 frames, press A, advance message 75 and
   confirm native trainer 606 starts. **Do not replace its script or battle**
   for the failure run. Lose through real move selection and forced switches.
4. Capture battle result, `CheckBattleWon` output, conditional target, message
   opens, WhiteOut calls, map/field state, final party HP, flags, screen, task/
   interpreter PCs and a bounded post-battle trace. Use fixed finite waits, not
   merely a generic battle helper timeout as the failure oracle.
5. Repeat on untouched CN and pinned RC7. As a diagnostic, alter **only the
   loaded private script displacement at 2900** to target L2734, then repeat
   native interaction/defeat. This tests the proposed loss branch without a
   production build. A third-argument-1 injected control is optional context.
6. Candidate pass: native WhiteOut invoked, healed controllable field at the
   save's respawn location (historical fixture: map 501), **all quest completion
   flags unchanged**. Return to the child and confirm he can challenge again.
   Win control: normal trainer victory, message 76, 1966 set, other found flags
   unchanged; subsequent talk skips battle. Already-found and reward gate
   controls belong in implementation verification if reproduction passes.

Warping/clearing flags and changing moves is a **controlled fixture**. The
corner child's script is directly attached to a visible native object with no
hide flag, so this tests a real interaction; it does not claim a complete
unmodified story playthrough to Rock Tunnel. Do not load cross-ROM savestates.
If native startup exits 134 inside the sandbox, escalate the same command as
required; distinguish that host failure from the game defect.

## Input hashes and preservation

| Input | SHA-256 |
|---|---|
| Untouched CN ROM | `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8` |
| `work/build/rc7/candidate/origin_hg_v4.0.3_en_wip.nds` | `b16f81bec13b07730ee544fbe24aead4229eccf04368f186aa71abe0b48710df` |
| Issue03 Struggle-fixed ROM | `93514313cba83acbb3f6b870fddfc9b111d62ad20b763a0670e4dd67ab074668` |
| Preserved root English ROM | `6fa7b4e739391ca9ea9bfcf90d83eec6407c3c04102e52432bb41bc8ae44a7d3` |
| Source battery save | `b3aca10747cd0f1adc3d5852a50dddaaa36ed8680f5ba04012cfe3110faad90f` |
| Historical CN report | `a5e9233c45657096cd6cfbffe99e047674edfc2360c1ab397d4a377fa3d82141` |
| Historical EN report | `392d840fbc7d62a2768726f2f081eca8a2a63e9128caac6276cba84f5798a1b7` |

All four ROMs have byte-identical **6030-byte** member 129:
SHA-1 **c73334fd0e00250cad1b66fc2b929931374bdca4**, SHA-256
**819737679c800fdd6f4831d4d251abe79d78a98486fde3328b13009c872c2692**.
The existing ROM-data cache was checked against the direct CN member and matches.
Exact input/report hashes and static candidate checks are preserved privately in
`work/build/bugfix-sequential-20261009/issue05/{static-inputs,static-check}.json`.

Critical choice for the coordinator: **ordinary native whiteout on loss**, with
the existing win/retry/reward semantics preserved. Avoid changing allowed-loss
behavior, marking a loss as a win, completing either child on loss, healing in
place, or touching the prior zero-PP-Struggle repair. No new decision was added
at this investigation stage; runtime reproduction remains the gate.
