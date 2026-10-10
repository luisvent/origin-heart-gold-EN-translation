# Issue 9 — out-of-range story flags investigation, 2026-10-09

**Proceed to bounded reproduction of the native writes.** Both original bad
operands and the native handlers are unchanged in the latest issue06 fixed
English ROM. A scoped safety repair makes sense, but the earlier proposed
`0x116D -> 0x016D` is unsafe. Route 1 also needs explicit old-save behavior:
simply moving its marker gives existing players the one-time gift again.

Investigation only: no emulator execution, ROM build, production patch/tool/text
edit, source-save edit, download, commit or decision-register change. Evidence
scripts and ignored extracted bytes are under
`work/build/bugfix-sequential-20261009/issue09/`. D-2300 authorizes repairs only
after reproduction. D-1333/D-1550 are historical observations; they do not prove
general save corruption or authorize guessed story semantics.

## Exact inputs and native mechanism

| Input | SHA-256 |
|---|---|
| Untouched CN | `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8` |
| issue06/fix/fixed English | `1f955bf433e69ba47d688749d70a635da8c5d9c024e838ed7cd8499dd76bbfa2` |

Both inputs have these identical `a/0/1/2` members:

| Member | Size | SHA-1 | Native sites |
|---|---:|---|---|
|168|2470|`2b32089d594baff7844c629378bf545770d47f16`|235 CheckFlag7286 (`2000761c`);1954 SetFlag7286 (`1e00761c`)|
|962|6788|`33cb77c9032d91186fa1680ae2b28919b4f58be5`|1819 SetFlag4461 (`1e006d11`)|

Command-table base is ARM9 `0x020F793C`. Opcode30 dispatches to
`0x020404A8`,31 to`0x020404C0`,32 to`0x020404D8`. They read a literal
halfword with `0x0203F534` and call field set/clear/check wrappers
`0x0203FB4C/60/38`. These fetch saved vars/flags through`0x0204F858`.

`GetFlagAddr` at`0x0204F8E4` treats0 as null and ordinary IDs below0x4000
as `vars +0x2E0 + (id>>3)`. At`0x0204F8FE` it compares the byte index
with0x194. An excessive index calls assertion`0x02025B2C` at`0x0204F902`,
then execution can continue to address construction at`0x0204F906–90E`.
The assertion is a real conditional diagnostic routine, not an unconditional
abort. Valid persisted IDs are1–3231 (`0x001–0xC9F`);0 is a native no-op.
The block-size function`0x0204F840` returns0x474; flags occupy0x194 bytes
after0x2E0, with8 bytes of transient flags at IDs0x4000–0x403F in separate RAM.

Native CheckFlag is`0x0204F864` (byte load`0x0204F874`). Native SetFlag is
`0x0204F890`: read at`0x0204F8AC`, OR at`0x0204F8B0`, actual STRB at
**`0x0204F8B2`**. D-1550 recorded a callback PC`0x0204F8B6`; that is not
the exact writer instruction in the current verified binaries. For an execute
hook useB2; for a memory callback record its observed PC convention as well.
ClearFlag is`0x0204F8B8` (STRB`0x0204F8DE`).

Historical RAM save layout: vars array4 starts0xEAC; Pokédex array6 starts
0x13A8, size0x374, magic0xBEEFCAFE. Offsets are relative to save+0x10.

| ID | Vars-relative byte/bit | Save byte/bit | Pokédex meaning |
|---|---|---|---|
|7286/0x1C76|0x66E/6|0x151A/6|+0x172: seen entry1335 (`seen +0xCC`, species−1 indexing)|
|4461/0x116D|0x50D/5|0x13B9/5|+0x11: caught entry110/Weezing (`caught +4`)|

Read actual allocation rows in each runtime; do not assume pointer addresses.
Historical list/card read hooks did not read the entry1335 word; Weezing stayed
blank in the list when caught but unseen. This is bounded observed impact.
No current investigation proves a visible dex fault or broad corruption.

## Story identity and scoped choices

Route 1 map9 uses scripts168, header413, message312, event6. Object0 at
1041,334 has no hide flag and starts script4 (entry227). Talk from1041,335,UP.
235 checks7286;239 branches to1214 when clear. First conversation runs
messages2–7 and the native Berry Juice reward;1954 sets7286, releases and ends.
Second conversation follows246/message1. Three directional scene branches
converge at1954. Keep their reward, movement, bag-full handling and text.

No other literal flag command or event hide flag uses7286. No evidence establishes
the intended corrected number.3190/0xC76 is in bounds and has no literal
Set/Clear/CheckFlag or event hide use, but is a **candidate reservation**, not
a proven original author intent or fully proven globally free native flag.
3190 and7286 both use bit6, which can simplify an exact-ID address alias.
All decoded literal flag uses and object flags are in`static-evidence.json`.

The scan also records indirect flag commands33–35: member145 reward helper
uses0x8006;151 contest helpers use calculated flags;948 uses653–662 and
2730+trainer index. Native trainer flags use base0x550 plus trainer ID
(`0x0203FC50/68/80`); daily reset zeros24 bytes from flag0xAA0
(`0x0203FBAC`), i.e.0xAA0–0xB5F. Hidden-item flag conversion is scriptID−0x1C20
(`0x0203FC98`, literal0x1C20 at`0x0203FCA4`); item script IDs start0x1F40,
so these use flags0x320+index; native hidden-item indices max230. Native system helper
`0x02065BD8` uses0x9B0+index<38. These do not establish use of3190, but
indirect/tail-call/table consumers must be considered before declaring it free.
`native-callers.json` inventories possible direct Thumb BL callers in ARM9
and every overlay; it is not a complete allocation proof (data false positives,
tail calls and table-derived operands remain).

Mt. Mortar map250 uses scripts962, header317, message119, event236.
Coordinate record11 at54,26 (1×1) triggers script11 while var0x409F==6;
entry1340 starts the native expedition departure scene. Header317 runs
script1/type3, which repositions actors from existing expedition state.
The closing sequence hides objects4,5,21,22,8,9,10,11;1815 sets675;
1819 sets4461;1823 clears670;1827 sets0x409F=7;release/end.

There is no other decoded literal flag reader/writer or event flag4461.
**Do not replace it with365/0x16D:** member822 Hall of Fame checks365 at
266/526/688 and, if clear, calls801 to clear775. This belongs to the existing
legendary-caught respawn family documented inD-1335. Setting365 changes an
unrelated legendary respawn condition.

There is stronger evidence for a *decimal* typo4461→461/0x1CD: the six
departing expedition objects4/5/8/9/10/11 all have native hide flag461;
objects21/22 have675.461 has two decoded clear sites (98@3536 at expedition
state10 and246@287), and no literal set. Correcting to461 would persist the
six NPC departures on map reload. That is a behavior change requiring an
explicitly justified scope choice and native re-entry controls; the digits
alone are not the proof. **Recommended safety-only choice:** change only the
1819 operand4461→0 (`member offset1821/0x71D:116D→0000`). Native SetFlag0
returns without a write, retaining all scene offsets and native progression.
This does not repair expedition NPC persistence or guess intended story state.

## Old-save compatibility and build support

Never clear the old Weezing caught bit as a migration: it cannot be distinguished
from a legitimate capture. Leave old Pokédex data intact and prevent new writes.
Mt. Mortar safety-only no-op requires no new save field or migration.

Route 1 needs completion preservation. Two operand replacements7286→3190
(member168 at237/0xED and1956/0x7A4) work for a new save, but a completed old
save has only the legacy Pokédex bit. Giving it the gift again is a material
change; do not silently accept it. Preserve completed and uncompleted saves,
new repeat-talk behavior, and save/reload persistence.

A practical scoped design to evaluate is an exact-ID native alias for7286 to
a reserved valid bit: checks read `valid_marker OR legacy_bit`, writes set only
the valid marker. A narrow migration can copy legacy bit6 into the valid marker
before returning the valid byte address. Do not clear or write the legacy dex
byte. If implementing inside GetFlagAddr, ensure original callers keep the same
bit index (3190 satisfies this), preserve registers/flags/return conventions,
and do not modify any other ID. There is no original ClearFlag7286 caller.
Avoid a global bounds guard: it alone makes the promo repeat because the marker
can never become true. Avoid enlarging save blocks or assigning365.

The registry/build already supports exact same-size halfword script changes:
kind`narc`, `[[narc_bytes]]`, `narc='a/0/1/2'`, member, offset, expect/new and
whole-member SHA-1. `narcpatch.apply/verify` pin all other bytes and size.
That supports the Mt. Mortar no-op and a plain two-site Route remap. It does
not support appending a script migration block without tool changes. A native
compatibility alias would use existing kind`code`/armips metadata, scoped ARM9
regions and verified free code space, as prior fixes do. No extension is
recommended before reproducing the actual writes and reserving a safe marker.

## Bounded reproduction handoff

1. Run CN then latest fixed English in isolated private battery copies, one
   emulator at a time; preserve/hash source save. Do not share cross-ROM states.
   Current repo-root`.venv/bin/python` works; historical`work/.venv` loops.
2. Resolve save table at`save+0x2E01C`,42 rows of16 bytes. Array addresses are
   `save+0x10+row.offset`; row i holds the size of array i+1. Record vars/dex
   offsets, sizes, magic and exact affected bytes. Hook script dispatch
   `0x0203F4CE` (ctx r4, opcode r1; member base ctx+0x7C,cursor ctx+8),
   opcode30/32 handlers, GetFlagAddr, assertion, CheckFlag LDRB and SetFlag STRB.
3. Promo: use a private save whose legacy bit6 is clear, or explicitly describe
   diagnostic RAM clearing of that bit. Warp9,1041,335,UP and talk to native
   object0. Bound dialogue driving (e.g.1200 frames); record native235/1954,
   messages2–7, bag item/quantity delta and the exact dex write. Talk again:
   message1 only, no reward/write. Save through native UI, fresh boot same ROM,
   and talk again to prove marker persistence. Do not use harness.set_flag7286:
   current helper correctly rejects out-of-range writes.
4. Mortar: preferred controlled native coordinate setup is var0x409F=6 with
   actors loaded/repositioned by header1, step onto54,26 and trace1340→1819.
   This is a controlled story-state fixture, not a full natural playthrough.
   If full actor setup is impractical, start member962 script11 at native1815
   through a private injected GoTo. Label this as a native-tail diagnostic;
   it must execute the actual member bytes1815–1835. Historical generic
   SetFlag4461 injection proved the handler, not the expedition reachability.
5. Begin with Weezing caught and seen clear; compare their two dex bits before/
   after. Expect caught=true,seen=false and exactly bit5 ORed at+0x11.
   Keep controls with legitimate Weezing caught+seen and with caught=false,
   seen=true. A normal valid SetFlag (e.g.3190 if privately controlled) must
   write within array4; SetFlag0 must write nothing. Record native ending
  675=true,670=false,0x409F=7 and field/menu recovery.
6. An offline assembled-native-function test can supplement emulator evidence:
   load the pinned CN ARM9 flag functions, intercept only assertion, provide
   representative adjacent save blocks, execute set/check for both IDs plus
   valid0xC9F, invalid0xCA0 and0, and record address+byte differences. A Python
   reimplementation of the arithmetic alone is not an independent native proof.
7. Fix-stage Route controls must cover (legacy,new)=(0,0),(1,0),(0,1),(1,1),
   other bits in both bytes, bag-full path, first/second/native-save-reload talk,
   and absence of *new* writes to either dex target. Other flags, entire dex
   data and existing prior fixes remain unchanged. No-op Mt. Mortar must retain
   exact native outcome state above. If461 is chosen instead, explicitly test
   reload hiding and state10/other clear sites, and record that extra behavior.

Historical helpers are inspectable with
`git show 2e6fe55^:work/tools/emu_guide0107.py` (case_promo_flag,
case_mortar_flag); the old recipe is removed from the current harness.
Do not revive unrelated suites or use their historical result as this run's gate.
