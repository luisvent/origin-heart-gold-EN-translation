# Issue 7 — Department Store doubles eligibility investigation, 2026-10-09

**Proceed to bounded native-interaction reproduction.** A narrow repair is
available: use the hack's native `PartyCheckForDouble` command before the
unfinished scene moves its actors, and show an existing neutral refusal message
when it returns zero. The native condition is **at least two living, non-Egg
Pokémon**, not merely two party records. D-2300 authorizes this scoped exception
after fresh reproduction; no fix was implemented in this stage.

This stage performed static inspection only. No emulator run, ROM build,
production tool/patch/script/text change, source-save edit, decision edit,
download or commit occurred. Private evidence and repeatable `static.py` are
under `work/build/bugfix-sequential-20261009/issue07/`.

## Actual map and scene

Map **196**, `MAP_GOLDENROD_DEPARTMENT_STORE_6F`, uses script archive `a/0/1/2`
member **901**, event member **189**, message bank **589**, header member
**676**. The hack combines store floors in this map; the relevant scene is in
the northern section around z6, not the lower store areas around z39/z71.

Native object **13** is the blind man, sprite330, at **2,6**, script **11**,
entry **542**, hide flag **2146**. Object14 is his Poochyena, at3,6, also
flag2146. The shoppers are objects **18** at4,6 and **19** at4,5, flag **2147**,
scripts13/14. Talking to a shopper does not start this battle. A practical
blind-man talk position is **2,7,UP**; **1,6,RIGHT** uses an explicitly handled
alternate player-x branch. Check collision/movement during reproduction.

There is no badge, story variable, trainer flag or party gate in script11.
Visibility requires2146 clear. Its initial unfinished-scene check requires2147
clear. Header676 runs scripts32/type3 and7/type2; script32 updates store-floor
var0x4113 from coordinates, while script7 is a short sign/message path. Neither
is a party gate.

| Offset | Native effect |
|---|---|
|542–555|PlaySE, lock, face player, message78, wait, close|
|557–561|Check2147; when set, jump2206 to release/end|
|568–773|Move shoppers, player, blind man and Poochyena; messages50–59|
|780–799|Message60 offers speaking up; collect choice0x800C; Yes0 jumps2210|
|806–913|Decline: departure scene; set2146, hide13/14, release/end|
|2210–2269|Yes: player movement/name/follower setup; x1 branch2914, otherwise2930|
|2930–3085|Argument with shoppers, including gender-specific69/70|
|3087|TrainerBattle **777,778,0,0**|
|3095–3105|CheckBattleWon; zero branches to native WhiteOut3789|
|3112–3271|Victory aftermath, shoppers depart, old man thanks player|
|3271–3283|Item69 / White Flute, quantity1, reward CallStd2033|
|3289–3303|Set2147, hide18/19, release/end|
|3789–3793|WhiteOut, ReleaseAll, End|

Do not reuse the **decline** route as an eligibility refusal: it permanently
hides the blind man/Poochyena through2146 and loses this scene's reward. A
refusal must leave2146/2147, trainers, actors and bag unchanged. Native loss
already whites out and does not mark the scene complete; preserve that path.
Victory sets2147 and preserves the old man, whose next talk displays78 then
exits through2206. Normal completed-scene dialogue should bypass any new guard.

Both trainer records have four Pokémon, levels62–65; record777's species are
112/164/369/398, record778's are113/162/370/389. Their individual trainer-header
`double` bits are **false**. Supplying both trainer IDs creates this double
battle. Do not condition this scoped guard on `TrainerIsDoubleBattle(777)`:
that would incorrectly bypass it.

## Existing native eligibility and refusal

Opcode **222**, `PartyCheckForDouble <destination>`, dispatches to ARM9
**0x02048E9C**. It obtains the player's party, calls **0x02053570**, and writes
the returned boolean at **0x02048EC0**. The predicate returns1 when
**0x0205349C** counts at least2. That counter iterates the declared party count
and calls **0x02053354** for each record. The latter accepts only current HP
field **0xA3 >0** and Egg field **0x4C ==0**. No artificial level/species/status
restriction is needed. Poisoned/paralyzed/etc. living non-Egg Pokémon qualify.

The native command therefore rejects one healthy Pokémon; one healthy plus
fainted records; one healthy plus Eggs; and any other party with fewer than two
living non-Egg Pokémon. Two healthy records qualify even if additional Eggs or
fainted records are present. Party-count-only guards and `PartyCountNotEgg`
would be insufficient. `CountAliveMons 0x800C,6` is equivalent for this ordinary
six-slot party but unnecessary because the native boolean already exists.

Reachable literal opcode222 uses in the original hack are standard trainer
member **949@3066** and **949@3353**. Both compare the result with0 and branch
to **3643**, which obtains trainer parameters, shows a refusal trainer message,
waits, closes, releases and ends. This confirms both guard semantics and safe
field refusal. Trainers777/778 have **no** rows in `a/0/5/7`, so calling their
own `TrainerMessage` refusal is not supported.

Reuse existing neutral field text through **MsgBoxExtern** (opcode440), which
resolves argument1 as bank and argument2 as message ID and uses the ordinary
field renderer. Recommended existing message is **a027/0100#10**, the hack's
own Double Battle refusal asking the player to return with enough Pokémon.
Member **78@453–463** checks party count and targets its refusal at819, then
wait/close/touch-menu-show/release/end. Its weaker count check is only a
message/cleanup precedent; use opcode222 for eligibility here. Message
**a027/0084#42** is a shorter neutral alternative, used by member55@2696→2866.
Both messages were decrypted directly from CN, RC7 and latest fixed English;
they already exist in all three ROMs and have no speaker-name prefix or buffer.
No new wording, text-bank edit or graphics work is needed.

## Recommended scoped insertion and critical choice

The clean site is **568**, after the existing2147 check and **before the first
actor movement**. Replace only that instruction's entry with a branch to an
appended guard block (preserve layout of the original member), then:

1. `PartyCheckForDouble 0x800C`; compare with0.
2. On failure: `MsgBoxExtern 100,10`, wait, close, release, end. The touch menu
   has not been hidden yet; do not enter the choice or decline machinery.
3. On success: execute the displaced original `ApplyMovement19` with its
   original movement target, then resume **576**. Preserve all later original
   commands, movements, relative targets, entry points and data.

This check must be unconditional for this scene's pair777/778, while respecting
the preceding completed2147 branch. A later implementation should verify that
the relocated ApplyMovement displacement still resolves to the original
movement data; copying raw displacement bytes to a new address is unsafe.

**Critical behavior choice:** an insufficient party is refused before the
argument begins, so it cannot select the native permanent-departure decline
until the party becomes eligible. This is a small interaction change within
the broken scene. It avoids trapping actors in the middle of their cutscene or
making the reward missable on refusal. Normal eligible Yes/No choices, battle
setup, victory, whiteout, retry and reward paths remain native. A guard only at
3087 would need a correctly justified actor/follower reset; merely ReleaseAll
there leaves displaced actors and is not the recommended bounded repair.
Do not globally alter double battles or convert777+778 to single battles.

## Bounded reproduction and fix-stage handoff

The old `emu_harness.py guide0813 --case white_flute` is no longer callable:
commit2e6fe55 removed `emu_guide0813.py`, `emu_guide0107.py`, `emu_skitty.py`.
Inspect historical code using `git show 2e6fe55^:work/tools/emu_guide0813.py`.
The historical test warped to196,4,8 and injected script11 directly at3087. It
proves the battle mechanism only, not the native blind-man conversation. Use
current harness/party validation helpers and adapt only necessary pieces into
private issue07 scratch. `work/.venv/bin/python` currently has a symlink loop;
the repo-root `.venv/bin/python` works for static inspection and prior runtime.

1. Fresh boot one emulator at a time, private battery copy per ROM, pinned
   noon2026-10-09. Resolve absolute paths before harness chdir. Preserve source
   save `work/build/memcheck/full_bag_6mons.sav` and its hash. No source-save
   writes or cross-ROM savestate loads.
2. For a declared **controlled native-object setup**, clear2146/2147 in private
   fixture RAM/save, warp to196 near2,7, faceUP, and talk to object13. This is
   a native interaction with controlled visibility, not a natural playthrough.
   Trace script11 from542 through the Yes choice at799→2210, then battle3087.
3. Begin with a strict valid one-Pokémon party. Prefer native generation and
   native empty-slot records (the historical helper used ZeroMonData-like
   `empty_mon()`), not a count1 party with stale live monsters in slots1–5.
   Validate declared count, encrypted checksums, species, moves and real HP on
   stable snapshots; reject transient decrypted data. Do not inject an invalid
   second ally to manufacture the bug.
4. At the battle menu record trainers777/778, both opponent teams, both player
   battlers/party-index selections and screenshots. Select FIGHT/first move by
   ordinary input. Bound the failing observation to at least the historical
   **2400 frames**. Record lack of turn/menu progress, blank bottom screen,
   script/battle task/PC samples and input probes. A PC address alone or generic
   timeout is not the failure oracle. Repeat on CN and latest fixed English.
5. Run controls with **two healthy non-Egg Pokémon** and with six, confirming
   normal doubles and a completed turn. Also test **one healthy + one fainted**
   and **one healthy + one Egg**. A healthy pair in later slots with earlier
   Egg/fainted records is a useful eligibility/selection control. Never count
   Egg HP as usable. The two-healthy minimum control is mandatory; the historical
   six-mon control did not establish the boundary.
6. For fix verification, insufficient-party cases must execute222→false, show
   existing100#10, return to a movable field/menu and invoke **zero battles**.
   Verify unchanged2146/2147, money/item69 and actor positions. Talk again with
   the same party to prove refusal is safe/repeatable. Add/heal a second valid
   Pokémon, then talk again and proceed through the original native scene.
7. Eligible controls must retain both trainer IDs and original four-Pokémon
   teams. Win normally to verify item69 x1,2147 set,18/19 hidden and13/14
   retained. A second talk must bypass the guard via2147 and not duplicate the
   reward. Lose using normal battle actions with two weak valid Pokémon:
   verify3095 won0→3789 native whiteout, field recovery/healing, no reward or
   completion flags, and a safe re-entry/retry. Decline with an eligible party
   must retain the original2146/hide13+14 behavior and no reward.
8. Hook dispatch **0x0203F4CE** with historical signatures
   `0203F4BE:206e814204d3`, `0203F4CE:e26d89005158`; ctx+0x7C is member base,
   ctx+8 is script cursor. Verify exact member bytes before tracing. Record
  222 handler/result store0x02048EC0, battle213, won220, flags and WhiteOut219.
   Follow only live contexts for member901; freed-context cursors can be junk.
   Native refusal MsgBoxExtern440 is overlay1 **0x021EE05C**; guard hooks by
   loaded overlay/code signature. Do not confuse handler return0/1 (interpreter
   yield) with the stored eligibility boolean.

If full native conversation reproduction cannot be reached within a finite
budget, direct3087 injection is a labelled fallback mechanism test. It cannot
verify a guard at568, movement cleanup or retry/reward semantics. Reproduction
must report that limitation rather than claim full-path verification.

## Input integrity and historical evidence

All three inputs contain identical **4376-byte** member901, SHA-256
`81807b0739586c8287f9842442a31eaf61843885e0f7a0a7a1ab9f476b778d63`.
Opcode222's handler bytes are identical too. Input SHA-256 values:

| Input | SHA-256 |
|---|---|
|Untouched CN `work/rom/origin_v4.0.3_cn.nds`|`4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8`|
|Pinned RC7 `work/build/rc7/candidate/origin_hg_v4.0.3_en_wip.nds`|`b16f81bec13b07730ee544fbe24aead4229eccf04368f186aa71abe0b48710df`|
|Combined issue06-fixed English `work/build/bugfix-sequential-20261009/issue06/fix/fixed/origin_hg_v4.0.3_en_wip.nds`|`1f955bf433e69ba47d688749d70a635da8c5d9c024e838ed7cd8499dd76bbfa2`|

Historical `work/build/harness/guide08_13/report_all_both.json` records both
one-party battles starting with both teams and failing to complete a turn;
both six-party controls return to the command menu. CN sampled PC0x01FF8030;
English sampled0x01FF8038. D-1559's prose uses the CN address for the shared
symptom. Screenshots are `guide08_13/<cn|en>/white_flute_{one|full}_{battle|turn}.png`.
Fresh boundary/whole-scene tests remain for the next stages; none are claimed
here. Preserve earlier **zero-pp-struggle**, **rock-tunnel-corner-loss** and
**magcargo-loss-whiteout** repairs and all unrelated dirty workspace files.
