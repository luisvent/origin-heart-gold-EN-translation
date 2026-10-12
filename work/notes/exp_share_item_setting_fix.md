# Exp. Share item and the SHARE setting (rc8 #bugs report, konando)

Status: NOT fixed. Documented design of the English patch; judgment call for Shishio. No reproduction run in the emulator (the behaviour is stated in the sources below, so I stopped at static evidence).

## Report
Setting SHARE to OFF (Options page 2/2, DIFFICULTY) also stops a held Exp. Share (item 216) from giving EXP to the holder.

## Evidence
- The setting is an English-patch extra, not part of the Chinese hack (site/src/content/docs/difficulty.md). The Chinese ROM has no such setting.
- Chinese ROM (D-1002 reference): the per-recipient EXP routine at overlay 14 0x022289B4 never reads the held item. A non-participant gets EXP only through the always-true getter at 0x022157C0 (half amount, deferred marker +0xC, which prints the "via the Exp. Share" message, battle_string 0002#?). Item 216 is therefore redundant in the Chinese hack: a holder and any other bench member get the same half share. There is no "item vs setting" behaviour in the original to preserve.
- English build: SHARE OFF makes dg_growth_share_enabled() (work/research/difficulty-armips/native/growth.c) return 0, so the 0x022289EA getter result is 0 for every non-participant. The function takes no recipient, so the held item cannot influence it.
- This is deliberate: D-2301 ("Exp. Share OFF disables EXP and EV gains for benched Pokemon"), research/growth.md ("Held Exp. Share is not an override of the global OFF predicate here"), and the guide (difficulty.md: "Holding an Exp. Share doesn't get round SHARE OFF").

## Possible fix (not made)
In the per-recipient routine the recipient's Pokemon struct is already available (r4 -> 0x022167B4 -> held item via 0x0206D848(mon, 6, 0), the same read used for Lucky Egg 0xE7 at 0x02228A1C). A fix would replace the getter call at 0x022289EA with a helper that returns `share_on || held_item == 216` for that recipient (still half EXP and EVs, still subject to the CAP clamp), plus a guide sentence and a test (bench holder vs bench non-holder, SHARE OFF, singles and doubles, wild and trainer). It changes a documented decision, so it needs approval.

## Questions for Shishio
1. Should a held Exp. Share keep working with SHARE OFF (vanilla item semantics; the reporter's expectation), or stay as documented (SHARE OFF is absolute)?
2. If it should work: half EXP and full EV for the holder, as vanilla HeartGold, or the same as the setting-ON bench share (half EXP, EVs as now)?
