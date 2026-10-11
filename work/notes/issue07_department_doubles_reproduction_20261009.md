# Issue 7 — Department Store doubles reproduction, 2026-10-09

**Freeze unverified; close this reproduction gate and move on.** Fresh native
Chinese interaction confirms that the blind-man scene starts trainers777/778
with one strictly valid living Pokémon. The bounded battle-action attempt did
not submit a move because its Splash target confirmation was omitted. It
therefore does **not** reproduce D-1559's freeze and does not justify proceeding
to production implementation in this run. No English or two-healthy control
was run.

Private evidence is in
`work/build/bugfix-sequential-20261009/issue07/repro/cn-one/`: `result.json`,
`before-talk.png`, `battle-menu.png`, `fight.png`, `move-selected.png`,
`after-2400.png`, and same-ROM `battle-menu.dst`. The native scene was entered
by talking to object13 from map196,2,7,UP, with private flags2146/2147 clear.
This is a controlled native-object fixture, not a natural story playthrough.
No scene cursor/battle instruction was injected or modified.

## What the completed diagnostic establishes

- The hack's native generator created species150 at level100. Strict closed
  snapshots rejected open/checksum-invalid records. The usable record had
  flags0, checksum valid, no Egg, status0, HP322/322 and native party stats
  `[322,185,205,265,313,205]`. After generator closure, unused slots1–5 were
  explicitly reset to the native ZeroMonData encrypted-empty representation.
  Party count was1; all five empty records were checked byte-for-byte. Splash
  with40PP was the only diagnostic moveset change; encrypted party stats were
  preserved. The pre-talk and battle snapshots both passed the strict gate.
- A separate injected **native PartyCheckForDouble222** command returned0 at
  the result store0x02048EC0. This tested the native helper, not a scene guard.
- Verified unchanged loaded member901 tracing records native object script11,
  entry542, first movement568, Yes799→2210, then battle3087 with arguments
  `[777,778]`. Both four-Pokémon opponent parties were found in RAM:
  `[112,164,369,398]` and `[113,162,370,389]`.
- The double battle reached a command menu. Its top screen also showed an
  unexpected second player health panel despite the declared count1 and empty
  trailing party records. Instrumentation observed player actor1 at322HP and
  opponent actors13/19 at214/394HP; it did not establish the second player's
  party index or a valid second actor. Do not treat the panel as a supplied
  invalid ally fixture.
- FIGHT and the first move opened the target screen (`move-selected.png`).
  The harness then pressed B while waiting2400 frames, which canceled target
  selection. At frame11630 the command menu was available, bottom screen was
  not black, PC0x020BB6A4 and scene cursor3095. No action was logged. Later A/B
  probes changed screens. The final assertion expecting freeze/black bottom
  failed. This is an **input-harness error**, not a freeze result or evidence
  that the original issue is absent.

## Attempts, blocking condition and integrity

Commands were run from the repository root:

```text
.venv/bin/python work/build/bugfix-sequential-20261009/issue07/repro/reproduce.py --rom work/rom/origin_v4.0.3_cn.nds --out work/build/bugfix-sequential-20261009/issue07/repro/cn-one --count 1
```

Sandbox native startup exited134. The exact command was rerun with
`require_escalated`. Its first fixture attempt stopped at the unused-slot
validation gate; no battle claim comes from that attempt. A bounded rerun
after explicit post-generator empty-slot reset produced the native evidence
above, then failed the action assertion. This second run overwrote the first
`cn-one/result.json`; the preparation failure remains recorded here.

A private harness correction added ordinary A target confirmation and the
second player's FIGHT command. The following rerun request was **pending tool
approval and then canceled by the coordinator after411.4 seconds**; it never launched
an emulator and created no `cn-one-final/` output directory:

```text
.venv/bin/python work/build/bugfix-sequential-20261009/issue07/repro/reproduce.py --rom work/rom/origin_v4.0.3_cn.nds --out work/build/bugfix-sequential-20261009/issue07/repro/cn-one-final --count 1
```

There was no automatic approval rejection or stated rejection reason. The
stage was then explicitly closed without more emulator runs or approval
requests. The current private harness contains that **unexecuted correction**;
its SHA-256 is `443934c070f40e71852821b4232ecf6136c91cb816c08ff62aec7df6aa8f9386`.

| Input | SHA-256 |
|---|---|
|Untouched CN ROM|`4807ab2c130581cb9d4f6110fc64b41ca4807b8d28e7622ebd3c9740baed95c8`|
|Unchanged member901|`81807b0739586c8287f9842442a31eaf61843885e0f7a0a7a1ab9f476b778d63`|
|Source `work/build/memcheck/full_bag_6mons.sav`|`b3aca10747cd0f1adc3d5852a50dddaaa36ed8680f5ba04012cfe3110faad90f`|

The source save's hash was unchanged in runtime cleanup and checked again at
closure. No production ROM build, patch/tool/text modification, source-save
edit, decision change, download, commit or publish occurred. Eligibility for
one healthy plus fainted/Egg records remains supported by the investigation's
native disassembly, not new runtime evidence. Historical direct3087 freeze
evidence remains separate and does not make this fresh reproduction pass.
