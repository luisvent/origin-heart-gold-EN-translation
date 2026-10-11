# Issue 6 — Pokémon Tower Magcargo loss investigation, 2026-10-09

**Proceed to bounded reproduction; do not implement a whiteout repair by default.**
The defect is supported by native control flow and historical paired runtime
evidence. The four-byte whiteout diagnostic below is a useful mechanism control,
but it loses the encounter after defeat and therefore does not preserve the
script's explicit attempted retry. A sensible repair preserving retry has not
yet been justified. D-2300 authorizes scoped repairs after reproduction, while
also allowing an issue to be logged and skipped if a repair does not make sense.

This stage ran static inspection only. No runtime, ROM build, production
script/tool/patch change, source-save edit, download, decision edit or commit.
Private evidence is under `work/build/bugfix-sequential-20261009/issue06/`.

## Actual interaction and control flow

Map **155** is the hack's combined Pokémon Tower interior, despite its vanilla
Sprout Tower constant and broad Lavender map label. It uses scripts
`a/0/1/2` member **17**, events `a/0/3/2` member **150**, messages **53**, and an
empty map header member **278**. Magcargo is native object **8**, sprite **680**,
at **2,51**, hide flag **1155**, script **10**, entry **648**. A practical talk
position is **2,52,UP**, subject to checking movement/collision in reproduction.

| Offset | Native effect |
|---|---|
| 648–669 | Lock, face player, Magcargo cry and message33 |
| 671–688 | Message34 offers catching; hide touch menu, collect choice in0x800C; choice0 calls L2519 |
| 695–699 | Declining restores touch menu, releases and ends |
| 2519–2527 | Restore touch menu, cry219 and wait |
| 2529 | WildBattle219, level40, form0 |
| 2536–2540 | CheckBattleWon0x800C, compare with0 |
| 2546 | Equality jumps to L2519, attempting another battle |
| 2553–2587 | Nonloss: set1155; hide objects8,3,5,9,10,12,13; release and end |
| 3914–3918 | Existing WhiteOut; ReleaseAll; End |

`CallIf` at688 is a real call into the battle block. Its nonloss path uses End,
not Return. Do not assume the caller's instructions695–699 run after a fight.
The decline branch leaves Magcargo available in the currently loaded map.

Native CheckBattleWon handler **0x02048DF0**, store **0x02048E18**, calls
**0x0205172C**, which returns0 for raw results **2 or3** (loss/draw), and1 for
other outcomes. Thus knockout, capture and flee take the hide path; loss/draw
take the attempted retry. Historical guide verification reports this same
outcome distinction. Fresh result controls should record raw result and stored
won value separately from the handler's ordinary return1 (interpreter yield).

The metadata decodes WildBattle's level as **65320 /0xFF28**. Native handler
**0x020434E8** reads a u16 and truncates the resolved value to u8 at
**0x02043524–32**, so the battle level is **40**, not65320. Preserve all original
arguments/bytes. Its explicit operands are species u16, level u16, form u8;
there is no exposed TrainerBattle-style allowed-loss operand. The handler
calls **0x02050418** with implicit scripted argument1. Do not reinterpret form0
as an allowed-loss option.

## Scene setup and shared state

The illusion-grunts coordinate event invokes script **8**, entry466, across
**x1–4,z40**, when **var0x40B7 ==0**. The native event record is
`(8,1,40,4,1,0,0,16567)`; the general event parser omits its condition fields.
Battle **992+993** at2347 is followed by a loss check that already targets
WhiteOut3914. On victory, the scene exposes Silph Scope item object6, clears
item flag2006 at2459, sets **1155 at2493**, clears1156, hides grunts4/7, and sets
**0x40B7=1 at2509**. Magcargo8 remains present in this loaded map even though
its hide flag is set. Any normal map reload then hides it.

Object8's script10 can be talked to repeatedly after the grunts while it remains
loaded: it has **no CheckFlag or progress-var gate**, only the catch choice.
Declining ends without hiding it, so a second direct talk offers the encounter
again. After a successfully completed battle it is explicitly hidden; after
loss its retry loop stalls before any later object interaction is possible.

There is **no existing map-init recovery check**: header278 is exactly
`00000000` and has no events. The native object loader simply applies shared
flag1155 on map entry. A persisted narrow loss marker plus an override showing
only object8 on map155 could preserve completed grunts and other NPCs, but it
would require new logic/marker allocation and defined clearing on knockout,
capture/flee. No available reserved marker or old-save migration semantics was
established here. Do not reuse0x40B7 values without auditing its later story
readers, and do not revive every1155 object. This is implementation uncertainty
for a separately bounded stage, not a ready four-byte script repair.

All reachable literal commands for1155 are:

- Member17: SetFlag2493 (grunts win), SetFlag2553 (Magcargo nonloss).
- Member129: SetFlag1109 (Rock Tunnel rescue).
- Member769: CheckFlag96 (Mr. Fuji's House dialogue), ClearFlag2399 (Cubone scene).

Event member150 shares1155 across **nine** objects: **3,4,5,7,8,9,10,12,13**.
Besides Magcargo and the grunts, these are Colette, Oak's illusion, Mom's
illusion, object10, Archie and Petrel. No other event member uses literal1155.
This is a scan of reachable literal script commands and event records, not a
proof against dynamically supplied flag IDs.

**Clearing1155 on loss is not a scoped retry fix.** It brings all nine objects
back on reload. Since0x40B7 remains1, the illusion-grunts coordinate scene does
not replay. Resetting0x40B7 too would replay defeated grunts and alter shared
story progress; this variable has other writers/readers in members31,49,129,
131,769 and942. Neither change is supported by the Magcargo loss branch.

## Precedents and diagnostic, not approved repair

Six same-member loss branches already use WhiteOut3914: Mom at2145, grunts
at2365, trainer294 at2811, trainer976 at3719, Blue at3771, ghost girl at5088.
Wild precedents: member42 Bronzor350 checks loss and whites out at384;
member130 Dialga2706/Palkia2748 check loss and white out at2784. These establish
that native WhiteOut handles scripted wild defeat, not that Magcargo's retry
should be replaced by whiteout.

Same-member Maxie TrainerBattle526 at6506 uses allowed-loss argument1 and its
loss branch6524→7434 continues the story. Nearby Lavender Gastly trainer184
in member771 at832 also uses allowed-loss1. These show intentional losses can
return safely when their battle setup supports it. They are trainer-specific
precedents, not an interchangeable WildBattle argument. HealParty6251 and
RestoreOverworld6255 are embedded in another cutscene; jumping there would
also execute its surrounding story and is not a valid Magcargo recovery block.

Smallest **private diagnostic**: change only member17's signed relative branch
displacement at **2549 /0x9F5**, preserving size/header/condition:

```text
old bytes: de ff ff ff   (-34; 2553-34 =2519)
new bytes: 51 05 00 00   (+1361; 2553+1361 =3914)
TOML halfwords if ever approved: expect="FFDE FFFF"; new="0551 0000"
```

In-memory static disassembly verifies the only changed instruction is2546 and
all entries and member size are identical. Do this in the emulator's disposable
loaded script RAM, not the ROM, for the next stage. Expect native whiteout and
healing, but **no Magcargo on returning to the map with1155 set**. Record that
as a semantic limitation, not a successful retry repair. An in-place heal/retry
or encounter-specific respawn hook requires further justification; none was
implemented or endorsed here. If no bounded retry-preserving candidate emerges,
log this reproduced defect and move on under D-2300.

## Bounded reproduction handoff

The cited `emu_harness.py guide0813 --case magcargo` is no longer callable.
Commit **2e6fe55** removed `emu_guide0813.py`, `emu_guide0107.py` and
`emu_skitty.py`. Inspect with `git show 2e6fe55^:work/tools/<module>.py`;
adapt only necessary pieces into private issue06 scratch. Historical
`case_magcargo` warped to155,17,12 and injected a jump from script1 to2519;
it bypassed object8, the choice and the grunts. Do not describe it as a natural
object-interaction reproduction. Current `emu_rock_tunnel.py` supplies useful
guarded command hooks, strict stable-party checks and bounded battle controls.

1. Run one emulator at a time, fresh boot and private battery copy per ROM;
   pin noon2026-10-09, resolve paths before harness chdir and preserve source
   `work/build/memcheck/full_bag_6mons.sav` hash. Use untouched CN and latest
   issue05-fixed English listed below; RC7 is an optional old-build control.
2. Prefer a **native grunts-scene setup**: clear1155 and set0x40B7=0 only in
   private fixture, warp to155 near `(2,39)` and walk onto `(2,40)` to invoke
   native script8. Use a strong valid party to win992+993, without changing
   battle result/task/scripts. Record2459/2493/2509, flags1155/1156/2006 and
   var0x40B7. Remain on this map; do not use stairs or warp again.
3. After grunts win, prepare a strict valid weak party via current native
   generator and party editor: six native-generated Lv5 Magikarp records or
   declared validated clones, Splash150/PP40, empty other moves, real HP.
   Reject transient decrypted/checksum-invalid records; do not infer corruption
   from a single live snapshot. Loss uses normal FIGHT and forced switches;
   no HP/result rewrite. Walk to `(2,52,UP)` and talk to object8, advance33/34,
   choose Yes. Assert script10/entry648, CallIf688→2519 and wild219/Lv40.
4. If grunts setup exceeds a finite900 battle iterations or cannot be reached,
   use a declared **controlled post-grunts loaded-object fixture**: enter with
   1155 clear, then set1155 and0x40B7=1 in private RAM, hide grunts4/7 using
   native commands, and talk to native object8. This models its transient
   availability and must be distinguished from winning the actual scene.
   Direct L2519 injection remains a fallback mechanism test only.
5. Hook script dispatch **0x0203F4CE**, checking signature from the historical
   OpTrace; context+0x7C is member base, context+8 cursor. Capture WildBattle589,
   CheckBattleWon220, compare17, GoToIf28, TouchscreenMenuShow747, cry76,
   WhiteOut219/task0x02051B3C and result store0x02048E18. Verify exact loaded
   member bytes before tracing/diagnostic. Guard overlay hooks with code
   signatures, and discard freed contexts outside the member.
6. Bound loss selection to900 iterations, then observe **20×150 frames** with
   occasional A/B/START (historical window). Record black screen, field state,
   map, command counts, final HP,1155/1156/2006,0x40B7 and PC/task samples.
   Expected failure: won0,2546→2519, one WildBattle total, second menu-show
   stalls, no second cry/battle or whiteout, no field restoration. A generic
   timeout or PC address alone is not the failure oracle.
7. Repeat both native failures. Separately repeat English with only loaded
   displacement2549 changed above; expect WhiteOut3914, healed controllable
   respawn field and preserved progress state. Re-enter155 and check object8
   is absent with1155 set. Do not clear1155 to manufacture retry success.
8. On separate fresh setups verify decline, knockout, capture and flee keep
   native semantics; capture should add Magcargo219/Lv40, nonloss should hide
   exactly the existing listed objects. Draw can be a documented untested
   branch unless generated through legitimate battle actions. No cross-ROM
   savestate loads. Host startup abort134 requires the usual same-command
   escalation and is separate from the game freeze.

## Evidence and input integrity

Historical `work/build/harness/guide08_13/report_all_both.json` has paired
Magcargo records: exactly one WildBattle,2546→2519 then TouchscreenMenuShow,
no WhiteOut/field recovery, samples near **0x01FF8030**, plus
`<cn|en>/magcargo_{battle,after}.png`. This agrees with D-1560 and
`softlock_audit.md` item15. The historical recipe does not prove the preceding
grunts/object interaction; the next stage should improve that evidence.

Direct ROM reads show identical **14766-byte** member17 in all three inputs:
SHA-1 `3b381a8adc85353ba9b906bd18521f7efcad95cb`, SHA-256
`a2e86eeef6662253bd5fb1ee4dc68ebe4930d0768eeb34d6459dda7ecdc164a3`.

| Input | SHA-256 |
|---|---|
| `work/rom/origin_v4.0.3_cn.nds` | `4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8` |
| `work/build/rc7/candidate/origin_hg_v4.0.3_en_wip.nds` | `b16f81bec13b07730ee544fbe24aead4229eccf04368f186aa71abe0b48710df` |
| `work/build/bugfix-sequential-20261009/issue05/fix/fixed/origin_hg_v4.0.3_en_wip.nds` | `7f85c44d5416ce87e2b9afb37b535899cef1b048ded0098079abe88c30db218d` |

Private `static.py`, `static-inputs.json` and `static-scene.json` preserve the
candidate assertions, native scene offsets, events and flag scans. Keep the
enabled **zero-pp-struggle** and **rock-tunnel-corner-loss** repairs and all
unrelated dirty files. Critical unresolved behavior choice: safely retain the
explicit in-place retry, or skip implementation; ordinary whiteout silently
making the encounter disappear is not recommended.
