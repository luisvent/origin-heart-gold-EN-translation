# Issue 9 — bounded offline native reproduction, 2026-10-09

**Both out-of-range writes are reproduced by actual ROM Thumb instructions in
untouched CN and the latest combined English build.** The matrix passes 19
cases per ROM with identical complete command, instruction and memory traces.
SetFlag7286 writes only Pokédex+0x172/bit6; SetFlag4461 writes only
Pokédex+0x11/bit5, the Weezing caught bit. Native SetFlag0 performs no persisted
write. This establishes the bounded byte-write mechanism and supports the
Mt. Mortar safety-only no-op choice. Route 1 marker reservation and old-save
compatibility remain separate implementation decisions.

This is **offline native-handler execution with private RAM fixtures**, not a
fresh DeSmuME/full-game run. The prior emulator attempt remains unexecuted as
recorded in `issue09_story_flags_reproduction_20261009.md`. This stage adds no
natural scene reachability, rendered Pokédex fault, general corruption,
save/reload, field recovery or current full-game assertion-behavior evidence.
No emulator, host approval request, download, build, production patch/tool,
source-save edit, decision-register change, commit or publication occurred.

## Exact inputs and code pins

| Input | SHA-256 |
|---|---|
| `work/rom/origin_v4.0.3_cn.nds` | `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8` |
| `work/build/bugfix-sequential-20261009/issue10/fix/fixed/origin_hg_v4.0.3_en_wip.nds` | `50a5b4a91a401f85392068cc15731406c46c15c5ea703c013c1e93e90f3bee5c` |

Both ROMs are read-only local inputs, pinned by their whole-file hashes. Member
168 is byte-identical: length2470, SHA-1
`2b32089d594baff7844c629378bf545770d47f16`, SHA-256
`2a7a40b92564f636a5bb2c6746a95789cfc3a8d99120d3ab9b53e824bbd9f554`.

Member962 is length6788 in both. CN SHA-1 is
`33cb77c9032d91186fa1680ae2b28919b4f58be5`; current EN SHA-1 is
`710a737be7e3cabdc99c29232e27ca36b989b8bf`, SHA-256
`61d3570360f6a938c2c3f96525da197d47c749b1745b89b33787e9477ddf57cb`.
The complete member comparison proves only offset136 differs, `01→04`, the
separate issue10 completed-expedition condition repair. Its bad flag command
at1819 and all tested tail bytes remain identical.

| Actual script site | Command bytes, both ROMs | Handler from actual table020F793C |
|---|---|---|
| 168@235 | `2000761c`, CheckFlag7286 | `020404D8` |
| 168@1954 | `1e00761c`, SetFlag7286 | `020404A8` |
| 962@1819 | `1e006d11`, SetFlag4461 | `020404A8` |

All consumed ARM9 bytes and every private allowed code range are checked for
CN/EN equality. The matrix executed235 distinct native instruction addresses
and consumed576 distinct ARM9 byte addresses. The SHA-256 of sorted
`little-endian-address || byte` records is
`9d9bcb7fc713a1bce4d105bb9aa2e1c177daaa58f2b71d467a0226f5d9d92173`.
Complete instruction bytes and range pins are retained in `summary.json`.
Principal equal range SHA-256 pins:

| ARM9 range, end exclusive | SHA-256 |
|---|---|
| 020404A8–020404F4, flag command handlers | `eedfb3fefebd77468ba620ca4afcfcebe904de0377344d00a1b5ef6425195e38` |
| 0203FAB0–0203FB88, var/field wrappers | `10b610502da15e303054579629fa62447b5d3541865bfb36f264b60c3c3a5ad5` |
| 0204F840–0204F948, flag block/core/resolver | `4220eed6fb746eafc61364dec15f366fdd0b4e6fe9692b844deca13dc213e854` |
| 020F79B4–020F79C0, command entries30–32 | `f726d24ee06c895b536e301cd683c2b3f51b9652455a444bc12ab1a384a75ce6` |
| 02025B2C–02025B44, assertion routine, **pinned but not executed** | `53f592cfd6c44372b466f211cc7b65feb102f4507b97e87fc06d93ced42357b7` |

## Private fixture and explicit assertion boundary

The sole executor extension is the ignored private `Issue9CPU` subclass of
`work/tools/native_script_state.py`. It maps a bounded adjacent save region,
supplies the saved-array accessor and the returning assertion boundary, and
records native instructions and writes. Production tools are unchanged.

Save-pointer fixture is02302000; general-data base is save+0x10=02302010.
Array metadata comes from the historically observed allocation in
`work/notes/emu_harness.md`, `work/tools/emu_dex.py`, and the ignored historical
`guide01_07/report_promo_flag.json` / `report_electrode_mortar_flag.json`.
Their hashes are in the summary. These are source metadata for the fixture,
**not newly resolved current runtime array-table rows**.

| Array | General-data offset | Logical size | Fixture pointer |
|---|---|---|---|
| 4, vars/flags | 0xEAC | 0x474 | 02302EBC |
| 5, local field | 0x1324 | 0x84 | 02303334 |
| 6, Pokédex | 0x13A8 | 0x374 | 023033B8 |

The actual native size getter0204F840 executes and returns0x474. Array4 has
four padding bytes before array5; the historical report's0x478 allocation span
is not the logical flag-block size. Pokédex magic is fixture0xBEEFCAFE.
Only RAM02302EBC–0230372B is added; unrecognized memory still fails closed.
Read/write probes at0230372C both reject in both ROMs. All surrounding private
save bytes contain deterministic sentinels, and full mapped-region differences
are checked, preserving unrelated bits and neighboring arrays.

The native wrappers call0204F858; the external save accessor returns02302EBC.
Its allocator and SaveArray_Get are not executed. Actual GetFlagAddr executes
the range comparison and native BL02025B2C for each excessive ordinary flag.
At that boundary, an explicitly logged **returning assertion fixture** returns
to0204F906, preserves callee-saved registers and poisons volatile registers and
flags. This models the historical observed returning release behavior. The
assertion implementation is not executed, and the fixture does **not** prove
the current full game's assertion/environment branch takes that return path.
Its current bytes are nevertheless pinned and equal across inputs.

No Python bit calculation selects a native flag address, predicate, branch or
write. The ROM instructions execute operand reading, address construction,
mask creation, LDRB/OR/STRB, CheckFlag and the Route1 GoToIf. Expected-byte
assertions compare those native results against independent explicit fixtures.

## Exact executed traces and controls

The SetFlag7286 trace reaches native GetFlagAddr with byte index0x38E:
0204F8FE compares it with0x194; native0204F900 falls through to
BL02025B2C@0204F902. After the logged assertion return, native0204F906–90C
constructs0230352A, vars+0x66E, general-save+0x151A, dex+0x172.
LDRB@0204F8AC readsA5; native OR@0204F8B0 producesE5;
**STRB@0204F8B2 writesE5**. Exactly this one byte changes: bit6 is set and
every other bit/byte stays intact. This is the seen bitmap's entry1335 under
the historical dex metadata, not proof of a visible list/card fault.

Actual CheckFlag168@235 subsequently executes LDRB@0204F874 at the same
address, returns true into the context comparison byte, and actual
GoToIf168@239 returns cursor246. With legacy bit6 clear it returns cursor1214.
Four private `(legacy7286, bounded3190)` combinations prove the current native
check consults the old dex marker independently of a proposed new marker:

| Legacy / bounded marker | Native comparison | Actual GoToIf cursor | Save writes |
|---|---:|---:|---:|
| 0 / 0 | 0 | 1214 | 0 |
| 1 / 0 | 1 | 246 | 0 |
| 0 / 1 | 0 | 1214 | 0 |
| 1 / 1 | 1 | 246 | 0 |

For actual962@1819 SetFlag4461, native index is0x22D. The same native
assertion-call/address-construction path produces023033C9, vars+0x50D,
general-save+0x13B9, dex+0x11. LDRB reads85 and native STRB@0204F8B2
writesA5, setting only bit5. All four supplied `(Weezing caught, seen)`
combinations0/0,0/1,1/0,1/1 pass. The caught-clear cases have exactly one
changed byte; caught-set cases still execute the actual same-value STRB with
zero byte differences. The independent seen byte dex+0xD9 and every other
byte remain unchanged. Native field CheckFlag4461 returns1 afterward without
a write. Weezing can therefore become caught while unseen in this fixture.

The actual962 tail commands1815/1819/1823/1827 execute sequentially through
their native handlers and recorded return cursors1819/1823/1827/1833. Native
Set675, Clear670 and SetVar409F,7 retain their original effects, independently
checked by native flag readers and the resulting variable bytes. The fixture
starts409F=6; it finishes675=true,670=false,409F=7 with the additional
original4461 dex write. ReleaseAll1833/End1835, previous actor setup,
coordinate triggering and scene completion are not executed.

Operand-only diagnostic scripts supply3190,3231 and0 to the actual ROM command
table; these are explicitly synthetic controls rather than original scene
operands. Set/Check/Clear3190 writes only vars+0x46E, `85→C5→85`.
Set/Check/Clear3231 reaches the last valid byte vars+0x473,
`35→B5→35`. Both native reads return1, all stores stay in array4, unrelated
bits and the entire dex remain unchanged, and neither calls the assertion.
The actual maximum is3231; the3190 control does not reserve that marker.

Native Set/Clear/Check0 follows GetFlagAddr's null return. Set/Clear execute
no persisted LDRB/STRB, Check returns0, all save bytes remain identical and no
assertion is reached. This proves the handler-level safety of replacing only
Mt. Mortar's operand4461 with0. It is not an actual patched-ROM test; a later
fix stage must pin the exact member operand and built bytes while preserving
the other native tail commands.

## Handoff and preservation

The bounded reproduction gate is met for both original byte writes. A narrow
Mt. Mortar4461→0 repair avoids new dex writes without inventing a replacement
story flag. Do not assign365 or clear old Weezing data. NPC persistence with
461 is a different behavior change and is not justified by this stage.

Route1 remains deferred for implementation:3190 is only a tested bounded
candidate. A reservation audit and a deliberate old-save completion policy
must precede a fix. The native four-case reads prove that merely moving the
operand would lose a legacy-only completion marker. No alias, migration,
global bounds guard, production design rewrite or save-restoration policy was
implemented or tested here.

Before/after SHA-256 snapshots cover273 preexisting dirty/untracked files,
patch files, executor tools, expected hashes and the source battery. Every
hash is unchanged, including all five existing sequential repairs. Source
`work/build/memcheck/full_bag_6mons.sav` remains
`b3aca10747cd0f1adc3d5852a50dddaaa36ed8680f5ba04012cfe3110faad90f`.
The input ROMs remain pinned and unchanged. The only new files are ignored
private evidence and this handoff note; the coordinator owns ledger updates.

Reproduce from the repository root:

```sh
.venv/bin/python work/build/bugfix-sequential-20261009/issue09/repro-offline/reproduce.py
```

Private evidence directory:
`work/build/bugfix-sequential-20261009/issue09/repro-offline/`.
`matrix.json` contains every case's command/cursor, assertion boundary, native
instruction/branch, write and whole-region difference. `summary.json` contains
inputs, instruction bytes, range/consumed-byte pins, metadata sources and memory
rejections; `run.log` records PASS. Artifact SHA-256 values for this handoff:

| Artifact | SHA-256 |
|---|---|
| `reproduce.py` | `46878c4f05a249ab82447aa96dcfe8001644d1e017c2a4e7b571ec636d5625b9` |
| `matrix.json` | `95ac8a3ba8de8e46f05709076bce32457faf612f268d40fb2a8ff321b6b08c0c` |
| `summary.json` | `398a7b61251e7cfa6626978700aefa396b4b7ce38b9bf145285b705dc1fb9bb8` |
| `run.log` | `cd67a180efdad0130e3616ac64d76af2545a7870ce76874596171487961e6a4b` |
| `protected-before.json` and `protected-after.json` | `96f6174b53cf533c706bf8d692a771bab0abcbc9d87e41f83fb0f6c1aa0b0c91` |
