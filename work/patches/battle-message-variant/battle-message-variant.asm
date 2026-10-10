; battle-message-variant - battle lines that one Pokemon's effect prints about another Pokemon pick their
; own / wild / foe's / trainer's form from the Pokemon they name (Destiny Knot: "The wild Chansey fell in love
; because of the Destiny Knot!"). D-2319 (user-approved exception to D-1337).
; Why and what: fix.toml next to this file; overview work/patches/FIXES.md; work/notes/destiny-knot-side_fix.md.
;
; Bank 1 of battle_string has four forms of each line: plain (the player's Pokemon), 'The wild ...', 'The
; foe's ...' and '<trainer>'s ...'. The server sends the line with a variant battler (stream op 3); the client
; picks the form from that battler's side (0x02225E40) and fills the template's parameters. The form belongs to
; the Pokemon the prefix stands before, so the variant battler has to be that Pokemon.
;
; 1. Condition applier (0x0221E53C; reached from ApplyCondition 0x0221F87C and its queued path 0x0221E05C).
;    Its struct holds the source (the Pokemon whose move, Ability or item causes it, [0]) and the target (the
;    one that gets the condition, [4]); a message record the caller built (+0x30 of its struct) is sent with
;    0x0222934C(record, variant). The variant is the source's when there is one, else the target's; its own
;    default message names the target and passes the target. Every caller with a record of its own whose source
;    and target differ names the target (static audit, work/notes/destiny-knot-side_fix.md), e.g. Destiny Knot
;    (0x0220AECC: source = the holder, target = the attacker, 1#448 "{target} fell in love because of the
;    {item}"), Mean Look / Block 1#1180, Curse 1#1442, Poison Point 1#638, Gastro Acid 1#762, Smack Down 1#1530,
;    Octolock 1#1958. Fix: test the target first (the source only when there is no target). 10 bytes.
; 2. Change applier (0x0221F968, ApplyHPChange with a message record at +0x20, source [0], target [1]): the
;    record is sent with the source's battler. Callers whose source differs from the record's first argument
;    name the target there (1#524 "{0}'s HP was restored", four handlers); two name the source (1#944, 1#2138).
;    Fix: the variant is the record's first argument (low byte of its first parameter, record + 4). 6 bytes.
; 3. Same function, Heal Block: 1#1200 "{0} can't heal because of Heal Block" is emitted with the source's
;    battler and the target as {0}. Fix: the target's battler. 2 bytes.
;
; Not changed: the message ids, the arguments, the default messages, which Pokemon gets the condition and its
; source, and every line whose variant already is the Pokemon it names (unchanged by construction: the new
; choice equals the old one whenever source and target, or source and first argument, are the same).

.nds
.thumb
.include "../include/guards.inc"

.definelabel CondApply_Message,         0x0221E53C   ; (src mon, tgt mon, cond, ...; default flag, record)
.definelabel CondApply_PickVariant,     0x0221E548   ; r1 = variant battler: src, else tgt   <- edit 1
.definelabel CondApply_VariantOfR5,     0x0221E55A   ; r0 = tgt; bl BattleMon_GetBattler; r1 = result
.definelabel CondApply_Ref,             0x0221E55C   ; bl BattleMon_GetBattler (r0 = a battle Pokemon)
.definelabel CondApply_VariantDone,     0x0221E564
.definelabel HPChange_SendRecord,       0x0221FA1C   ; 0x0222934C(record + 0x20, [struct]) <- edit 2
.definelabel HPChange_HealBlocked,      0x0221FA4A   ; 0x02229E1C([struct], 1200, [struct+1]) <- edit 3
.definelabel BattleMon_GetBattler,      0x022167A0   ; ldrb r0, [r0, #0x14]
.definelabel BattleMsg_SendRecord,      0x0222934C   ; (record, variant battler)
.definelabel BattleMsg_Emit1,           0x02229E1C   ; (variant battler, id, param)

.open "overlay14.bin", 0x022007E0

; Read-only guards: the applier's variant choice and both record sends (nothing is written here).
.org CondApply_Message
    expect16_at 0x00, 0xB40F    ; push  {r0, r1, r2, r3}
    expect16_at 0x02, 0xB530    ; push  {r4, r5, lr}
    expect16_at 0x04, 0xB089    ; sub   sp, #0x24
    expect16_at 0x06, 0x1C0D    ; adds  r5, r1, #0              r5 = target
    expect16_at 0x08, 0x1C14    ; adds  r4, r2, #0              r4 = condition
    expect16_at 0x0A, 0x2100    ; movs  r1, #0
    expect16_at 0x0C, 0x2800    ; cmp   r0, #0                  r0 = source  <- edit 1 (0x0C-0x15)
    expect16_at 0x0E, 0xD004    ; beq   0x0221E556
    expect16_at 0x10, 0xF7F8    ; bl    BattleMon_GetBattler    (1/2)
    expect16_at 0x12, 0xF928    ;                               (2/2)
    expect16_at 0x14, 0x0600    ; lsls  r0, r0, #0x18
    expect16_at 0x16, 0x0E01    ; lsrs  r1, r0, #0x18           variant = source
    expect16_at 0x18, 0xE006    ; b     CondApply_VariantDone
    expect16_at 0x1A, 0x2D00    ; cmp   r5, #0                  0x0221E556
    expect16_at 0x1C, 0xD004    ; beq   CondApply_VariantDone
    expect16_at 0x1E, 0x1C28    ; adds  r0, r5, #0              CondApply_VariantOfR5
    expect16_at 0x20, 0xF7F8    ; bl    BattleMon_GetBattler    (1/2)  CondApply_Ref
    expect16_at 0x22, 0xF920    ;                               (2/2)
    expect16_at 0x24, 0x0600    ; lsls  r0, r0, #0x18
    expect16_at 0x26, 0x0E01    ; lsrs  r1, r0, #0x18           variant = target
    expect16_at 0x28, 0x9811    ; ldr   r0, [sp, #0x44]         CondApply_VariantDone: default-message flag
    expect16_at 0x2A, 0x2800    ; cmp   r0, #0
    expect16_at 0x2C, 0xD032    ; beq   0x0221E5D0
    expect16_at 0x2E, 0x2D00    ; cmp   r5, #0
    expect16_at 0x30, 0xD030    ; beq   0x0221E5D0
    expect16_at 0x52, 0x1C28    ; adds  r0, r5, #0              default message: {0} = target
    expect16_at 0x54, 0xF7F8    ; bl    BattleMon_GetBattler    (1/2)
    expect16_at 0x56, 0xF906    ;                               (2/2)
    expect16_at 0x78, 0x1C28    ; adds  r0, r5, #0              ... and variant = target
    expect16_at 0x7A, 0xF7F8    ; bl    BattleMon_GetBattler    (1/2)
    expect16_at 0x7C, 0xF8F3    ;                               (2/2)
    expect16_at 0x7E, 0x1C01    ; adds  r1, r0, #0
    expect16_at 0x80, 0x0609    ; lsls  r1, r1, #0x18
    expect16_at 0x82, 0xA800    ; add   r0, sp, #0
    expect16_at 0x84, 0x0E09    ; lsrs  r1, r1, #0x18
    expect16_at 0x86, 0xF00A    ; bl    BattleMsg_SendRecord    (1/2)
    expect16_at 0x88, 0xFEC3    ;                               (2/2)
    expect16_at 0x94, 0x9812    ; ldr   r0, [sp, #0x48]         0x0221E5D0: the caller's record
    expect16_at 0x96, 0x2800    ; cmp   r0, #0
    expect16_at 0x98, 0xD001    ; beq   0x0221E5DA
    expect16_at 0x9A, 0xF00A    ; bl    BattleMsg_SendRecord    (1/2)  r1 = the variant chosen above
    expect16_at 0x9C, 0xFEB9    ;                               (2/2)

; Edit 1: the target's battler first, the source's only when there is no target. The old target branch
; (0x0221E55A-0x0221E563) does the target; the source reuses its call at 0x0221E55C (r0 = source).
; 0x0221E552-0x0221E559 (lsrs, b, cmp r5, beq) are no longer reached.
.org CondApply_PickVariant
.area 10
    expect16_at 0, 0x2800       ; cmp   r0, #0                  a source?
    expect16_at 2, 0xD004       ; beq   0x0221E556
    expect16_at 4, 0xF7F8       ; bl    BattleMon_GetBattler    (1/2)
    expect16_at 6, 0xF928       ;                               (2/2)
    expect16_at 8, 0x0600       ; lsls  r0, r0, #0x18
    cmp     r5, #0
    bne     CondApply_VariantOfR5       ; a target: its battler
    cmp     r0, #0
    beq     CondApply_VariantDone       ; neither: battler 0, as before
    b       CondApply_Ref               ; only a source: its battler (r0 = source)
.endarea

; Read-only guards: the change applier's message paths.
.org 0x0221FA10
    expect16_at 0x00, 0x1C20    ; adds  r0, r4, #0
    expect16_at 0x02, 0x3023    ; adds  r0, #0x23
    expect16_at 0x04, 0x7800    ; ldrb  r0, [r0]                record type (+0x23)
    expect16_at 0x06, 0x0640    ; lsls  r0, r0, #0x19
    expect16_at 0x08, 0x0E40    ; lsrs  r0, r0, #0x19
    expect16_at 0x0A, 0xD005    ; beq   0x0221FA28              no record
    expect16_at 0x12, 0xF009    ; bl    BattleMsg_SendRecord    (1/2)  <- edit 2 is 0x0221FA1C-0x0221FA21
    expect16_at 0x14, 0xFC93    ;                               (2/2)
    expect16_at 0x16, 0xE016    ; b     0x0221FA56
    expect16_at 0x36, 0x2D02    ; cmp   r5, #2                  0x0221FA46: heal blocked
    expect16_at 0x38, 0xD105    ; bne   0x0221FA56
    expect16_at 0x3C, 0x214B    ; movs  r1, #0x4B               (0x0221FA4A: edit 3)
    expect16_at 0x3E, 0x7862    ; ldrb  r2, [r4, #1]            {0} = target
    expect16_at 0x40, 0x0109    ; lsls  r1, r1, #4              1200
    expect16_at 0x42, 0xF00A    ; bl    BattleMsg_Emit1         (1/2)
    expect16_at 0x44, 0xF9E3    ;                               (2/2)

; Edit 2: the record goes out with its first parameter's battler (record + 0x20, parameters from +4).
.org HPChange_SendRecord
.area 6
    expect16_at 0, 0x7821       ; ldrb  r1, [r4]                variant = source
    expect16_at 2, 0x1C20       ; adds  r0, r4, #0
    expect16_at 4, 0x3020       ; adds  r0, #0x20               r0 = record
    add     r0, r4, #0
    add     r0, #0x20           ; r0 = record
    ldrb    r1, [r0, #4]        ; variant = the first parameter (a battler)
.endarea

; Edit 3: Heal Block's line takes the target's battler, the Pokemon it names.
.org HPChange_HealBlocked
.area 2
    expect16_at 0, 0x7820       ; ldrb  r0, [r4]                variant = source
    ldrb    r0, [r4, #1]        ; variant = target
.endarea

; 4. Move lines that the move code sends itself (stream op 3 through 0x02229E1C / 0x02224C50, or the condition
;    check's 'already ...' helper 0x02229944) with the attacker's or the move user's battler while {0} (or {1})
;    is another Pokemon. Each edit makes the variant the Pokemon the prefix stands before; one halfword each:
;    1#296 'It had no effect at all on {0}' (OHKO on a higher level), 1#288 'It doesn't seem to affect {0}' (five
;    sites), 1#706 Protect, 1#1220 drain moves, the condition check's messages (1#340 'is already poisoned' and
;    the other 'already ...' / 'doesn't affect' lines of 0x02229944: struct + 4 is the target, + 0 the source),
;    1#1468 Gravity, 1#1000 Ingrain against Roar / Whirlwind, 1#1554 Pledge ('{0} is waiting for {1}': prefix
;    on {1}). Not changed: their ids, parameters and when they appear.

.definelabel Gravity_Variant, 0x0220E4DA
.definelabel NoEffectAtAll_Variant, 0x0221A7B8
.definelabel DoesntAffect1_Variant, 0x0221AE92
.definelabel DoesntAffect2_Variant, 0x0221AEB6
.definelabel DoesntAffect3_Variant, 0x0221AF34
.definelabel DoesntAffect4_Variant, 0x0221B228
.definelabel Protect_Variant, 0x0221B384
.definelabel DoesntAffect5_Variant, 0x0221B8F6
.definelabel Drain_Variant, 0x0221C1FC
.definelabel CondBlocked_Variant, 0x0221E0E8
.definelabel Ingrain_Variant, 0x02220B78
.definelabel Pledge_Variant, 0x02222DE2

; 1#1468 Gravity: variant = {0} (r2, the grounded Pokemon), not Gravity's user ([sp])
.org Gravity_Variant
.area 2
    expect16_at -0x02, 0x782A    ; 0220E4D8 ldrb r2, [r5]
    expect16_at 0x00, 0x9800    ; 0220E4DA ldr r0, [sp]   <- the edit
    expect16_at 0x02, 0x4904    ; 0220E4DC ldr r1, [pc, #0x10]
    expect16_at 0x04, 0xF01B    ; 0220E4DE bl #0x2229e1c
    expect16_at 0x06, 0xFC9D    ; 0220E4E0 (2/2)
    add     r0, r2, #0
.endarea

; 1#296 OHKO 'had no effect at all on {0}': variant = the target (r4), not the attacker (r6)
.org NoEffectAtAll_Variant
.area 2
    expect16_at -0x06, 0x482B    ; 0221A7B2 ldr r0, [pc, #0xac]
    expect16_at -0x04, 0x6800    ; 0221A7B4 ldr r0, [r0]
    expect16_at -0x02, 0x6A07    ; 0221A7B6 ldr r7, [r0, #0x20]
    expect16_at 0x00, 0x1C30    ; 0221A7B8 adds r0, r6, #0   <- the edit
    expect16_at 0x02, 0xF7FB    ; 0221A7BA bl #0x22167a0
    expect16_at 0x04, 0xFFF1    ; 0221A7BC (2/2)
    expect16_at 0x06, 0x9005    ; 0221A7BE str r0, [sp, #0x14]
    expect16_at 0x08, 0x1C20    ; 0221A7C0 adds r0, r4, #0
    expect16_at 0x0A, 0xF7FB    ; 0221A7C2 bl #0x22167a0
    expect16_at 0x0C, 0xFFED    ; 0221A7C4 (2/2)
    expect16_at 0x0E, 0x9000    ; 0221A7C6 str r0, [sp]
    expect16_at 0x10, 0x4826    ; 0221A7C8 ldr r0, [pc, #0x98]
    expect16_at 0x12, 0x224A    ; 0221A7CA movs r2, #0x4a
    expect16_at 0x14, 0x9001    ; 0221A7CC str r0, [sp, #4]
    expect16_at 0x16, 0x9B05    ; 0221A7CE ldr r3, [sp, #0x14]
    expect16_at 0x18, 0x1C38    ; 0221A7D0 adds r0, r7, #0
    expect16_at 0x1A, 0x2103    ; 0221A7D2 movs r1, #3
    expect16_at 0x1C, 0x0092    ; 0221A7D4 lsls r2, r2, #2
    expect16_at 0x1E, 0xF00A    ; 0221A7D6 bl #0x2224c50
    expect16_at 0x20, 0xFA3B    ; 0221A7D8 (2/2)
    add     r0, r4, #0
.endarea

; 1#288: variant = {0} (r4, the target's battler) instead of the attacker's
.org DoesntAffect1_Variant
.area 2
    expect16_at -0x0C, 0x4812    ; 0221AE86 ldr r0, [pc, #0x48]
    expect16_at -0x0A, 0x6800    ; 0221AE88 ldr r0, [r0]
    expect16_at -0x08, 0x6A05    ; 0221AE8A ldr r5, [r0, #0x20]
    expect16_at -0x06, 0x1C30    ; 0221AE8C adds r0, r6, #0
    expect16_at -0x04, 0xF7FB    ; 0221AE8E bl #0x22167a0
    expect16_at -0x02, 0xFC87    ; 0221AE90 (2/2)
    expect16_at 0x00, 0x1C03    ; 0221AE92 adds r3, r0, #0   <- the edit
    expect16_at 0x02, 0x2212    ; 0221AE94 movs r2, #0x12
    expect16_at 0x04, 0x480F    ; 0221AE96 ldr r0, [pc, #0x3c]
    expect16_at 0x06, 0x9400    ; 0221AE98 str r4, [sp]
    expect16_at 0x08, 0x9001    ; 0221AE9A str r0, [sp, #4]
    expect16_at 0x0A, 0x1C28    ; 0221AE9C adds r0, r5, #0
    expect16_at 0x0C, 0x2103    ; 0221AE9E movs r1, #3
    expect16_at 0x0E, 0x0112    ; 0221AEA0 lsls r2, r2, #4
    expect16_at 0x10, 0xF009    ; 0221AEA2 bl #0x2224c50
    expect16_at 0x12, 0xFED5    ; 0221AEA4 (2/2)
    add     r3, r4, #0
.endarea

; 1#288 (type immunity): variant = {0} (r4) instead of the attacker's
.org DoesntAffect2_Variant
.area 2
    expect16_at -0x0C, 0x4809    ; 0221AEAA ldr r0, [pc, #0x24]
    expect16_at -0x0A, 0x6800    ; 0221AEAC ldr r0, [r0]
    expect16_at -0x08, 0x6A05    ; 0221AEAE ldr r5, [r0, #0x20]
    expect16_at -0x06, 0x1C30    ; 0221AEB0 adds r0, r6, #0
    expect16_at -0x04, 0xF7FB    ; 0221AEB2 bl #0x22167a0
    expect16_at -0x02, 0xFC75    ; 0221AEB4 (2/2)
    expect16_at 0x00, 0x1C03    ; 0221AEB6 adds r3, r0, #0   <- the edit
    expect16_at 0x02, 0x2212    ; 0221AEB8 movs r2, #0x12
    expect16_at 0x04, 0x4806    ; 0221AEBA ldr r0, [pc, #0x18]
    expect16_at 0x06, 0x9400    ; 0221AEBC str r4, [sp]
    expect16_at 0x08, 0x9001    ; 0221AEBE str r0, [sp, #4]
    expect16_at 0x0A, 0x1C28    ; 0221AEC0 adds r0, r5, #0
    expect16_at 0x0C, 0x2103    ; 0221AEC2 movs r1, #3
    expect16_at 0x0E, 0x0112    ; 0221AEC4 lsls r2, r2, #4
    expect16_at 0x10, 0xF009    ; 0221AEC6 bl #0x2224c50
    expect16_at 0x12, 0xFEC3    ; 0221AEC8 (2/2)
    add     r3, r4, #0
.endarea

; 1#288 in the loop over a move's targets: variant = the target (r4; {0} = r7 = its battler)
.org DoesntAffect3_Variant
.area 2
    expect16_at -0x12, 0x1C20    ; 0221AF22 adds r0, r4, #0
    expect16_at -0x10, 0xF7FB    ; 0221AF24 bl #0x22167a0
    expect16_at -0x0E, 0xFC3C    ; 0221AF26 (2/2)
    expect16_at -0x0C, 0x0600    ; 0221AF28 lsls r0, r0, #0x18
    expect16_at -0x0A, 0x0E07    ; 0221AF2A lsrs r7, r0, #0x18
    expect16_at -0x08, 0x480D    ; 0221AF2C ldr r0, [pc, #0x34]
    expect16_at -0x06, 0x6800    ; 0221AF2E ldr r0, [r0]
    expect16_at -0x04, 0x6A00    ; 0221AF30 ldr r0, [r0, #0x20]
    expect16_at -0x02, 0x9003    ; 0221AF32 str r0, [sp, #0xc]
    expect16_at 0x00, 0x1C30    ; 0221AF34 adds r0, r6, #0   <- the edit
    expect16_at 0x02, 0xF7FB    ; 0221AF36 bl #0x22167a0
    expect16_at 0x04, 0xFC33    ; 0221AF38 (2/2)
    expect16_at 0x06, 0x1C03    ; 0221AF3A adds r3, r0, #0
    expect16_at 0x08, 0x2212    ; 0221AF3C movs r2, #0x12
    expect16_at 0x0A, 0x480A    ; 0221AF3E ldr r0, [pc, #0x28]
    expect16_at 0x0C, 0x9700    ; 0221AF40 str r7, [sp]
    expect16_at 0x0E, 0x9001    ; 0221AF42 str r0, [sp, #4]
    expect16_at 0x10, 0x9803    ; 0221AF44 ldr r0, [sp, #0xc]
    expect16_at 0x12, 0x2103    ; 0221AF46 movs r1, #3
    expect16_at 0x14, 0x0112    ; 0221AF48 lsls r2, r2, #4
    expect16_at 0x16, 0xF009    ; 0221AF4A bl #0x2224c50
    expect16_at 0x18, 0xFE81    ; 0221AF4C (2/2)
    add     r0, r4, #0
.endarea

; 1#288 from the immunity dispatcher: variant = {0} (r2, the target's battler)
.org DoesntAffect4_Variant
.area 2
    expect16_at -0x0E, 0xF7FB    ; 0221B21A bl #0x22167a0
    expect16_at -0x0C, 0xFAC1    ; 0221B21C (2/2)
    expect16_at -0x0A, 0x1C05    ; 0221B21E adds r5, r0, #0
    expect16_at -0x08, 0x1C20    ; 0221B220 adds r0, r4, #0
    expect16_at -0x06, 0xF7FB    ; 0221B222 bl #0x22167a0
    expect16_at -0x04, 0xFABD    ; 0221B224 (2/2)
    expect16_at -0x02, 0x1C02    ; 0221B226 adds r2, r0, #0
    expect16_at 0x00, 0x0628    ; 0221B228 lsls r0, r5, #0x18   <- the edit
    expect16_at 0x02, 0x2112    ; 0221B22A movs r1, #0x12
    expect16_at 0x04, 0x0E00    ; 0221B22C lsrs r0, r0, #0x18
    expect16_at 0x06, 0x0109    ; 0221B22E lsls r1, r1, #4
    expect16_at 0x08, 0xF00E    ; 0221B230 bl #0x2229e1c
    expect16_at 0x0A, 0xFDF4    ; 0221B232 (2/2)
    lsl     r0, r2, #0x18
.endarea

; 1#706 Protect: variant = {0} (r2, the protected Pokemon), not the attacker (r6)
.org Protect_Variant
.area 2
    expect16_at -0x10, 0x1C28    ; 0221B374 adds r0, r5, #0
    expect16_at -0x0E, 0xF7FB    ; 0221B376 bl #0x22167a0
    expect16_at -0x0C, 0xFA13    ; 0221B378 (2/2)
    expect16_at -0x0A, 0x1C06    ; 0221B37A adds r6, r0, #0
    expect16_at -0x08, 0x1C20    ; 0221B37C adds r0, r4, #0
    expect16_at -0x06, 0xF7FB    ; 0221B37E bl #0x22167a0
    expect16_at -0x04, 0xFA0F    ; 0221B380 (2/2)
    expect16_at -0x02, 0x1C02    ; 0221B382 adds r2, r0, #0
    expect16_at 0x00, 0x0630    ; 0221B384 lsls r0, r6, #0x18   <- the edit
    expect16_at 0x02, 0x4905    ; 0221B386 ldr r1, [pc, #0x14]
    expect16_at 0x04, 0x0E00    ; 0221B388 lsrs r0, r0, #0x18
    expect16_at 0x06, 0xF00E    ; 0221B38A bl #0x2229e1c
    expect16_at 0x08, 0xFD47    ; 0221B38C (2/2)
    lsl     r0, r2, #0x18
.endarea

; 1#288 when the target is not the struct's source: variant = {0} (r2), not the source
.org DoesntAffect5_Variant
.area 2
    expect16_at -0x0A, 0x1C20    ; 0221B8EC adds r0, r4, #0
    expect16_at -0x08, 0xF7FA    ; 0221B8EE bl #0x22167a0
    expect16_at -0x06, 0xFF57    ; 0221B8F0 (2/2)
    expect16_at -0x04, 0x1C02    ; 0221B8F2 adds r2, r0, #0
    expect16_at -0x02, 0x2112    ; 0221B8F4 movs r1, #0x12
    expect16_at 0x00, 0x7828    ; 0221B8F6 ldrb r0, [r5]   <- the edit
    expect16_at 0x02, 0x0109    ; 0221B8F8 lsls r1, r1, #4
    expect16_at 0x04, 0xF00E    ; 0221B8FA bl #0x2229e1c
    expect16_at 0x06, 0xFA8F    ; 0221B8FC (2/2)
    add     r0, r2, #0
.endarea

; 1#1220 drain: variant = {0} (r2, the drained Pokemon), not the drainer (r4)
.org Drain_Variant
.area 2
    expect16_at -0x10, 0x1C20    ; 0221C1EC adds r0, r4, #0
    expect16_at -0x0E, 0xF7FA    ; 0221C1EE bl #0x22167a0
    expect16_at -0x0C, 0xFAD7    ; 0221C1F0 (2/2)
    expect16_at -0x0A, 0x1C04    ; 0221C1F2 adds r4, r0, #0
    expect16_at -0x08, 0x1C30    ; 0221C1F4 adds r0, r6, #0
    expect16_at -0x06, 0xF7FA    ; 0221C1F6 bl #0x22167a0
    expect16_at -0x04, 0xFAD3    ; 0221C1F8 (2/2)
    expect16_at -0x02, 0x1C02    ; 0221C1FA adds r2, r0, #0
    expect16_at 0x00, 0x0620    ; 0221C1FC lsls r0, r4, #0x18   <- the edit
    expect16_at 0x02, 0x4902    ; 0221C1FE ldr r1, [pc, #8]
    expect16_at 0x04, 0x0E00    ; 0221C200 lsrs r0, r0, #0x18
    expect16_at 0x06, 0xF00D    ; 0221C202 bl #0x2229e1c
    expect16_at 0x08, 0xFE0B    ; 0221C204 (2/2)
    lsl     r0, r2, #0x18
.endarea

; condition check's messages via 0x02229944 (1#340 ...): variant = the target (struct + 4), not the source
.org CondBlocked_Variant
.area 2
    expect16_at 0x00, 0x6828    ; 0221E0E8 ldr r0, [r5]   <- the edit
    expect16_at 0x02, 0xF7F8    ; 0221E0EA bl #0x22167a0
    expect16_at 0x04, 0xFB59    ; 0221E0EC (2/2)
    expect16_at 0x06, 0x6969    ; 0221E0EE ldr r1, [r5, #0x14]
    expect16_at 0x08, 0x0600    ; 0221E0F0 lsls r0, r0, #0x18
    expect16_at 0x0A, 0x9100    ; 0221E0F2 str r1, [sp]
    expect16_at 0x0C, 0x6869    ; 0221E0F4 ldr r1, [r5, #4]
    expect16_at 0x0E, 0x68AB    ; 0221E0F6 ldr r3, [r5, #8]
    expect16_at 0x10, 0x0E00    ; 0221E0F8 lsrs r0, r0, #0x18
    expect16_at 0x12, 0x1C22    ; 0221E0FA adds r2, r4, #0
    expect16_at 0x14, 0xF000    ; 0221E0FC bl #0x221e420
    expect16_at 0x16, 0xF990    ; 0221E0FE (2/2)
    ldr     r0, [r5, #4]
.endarea

; 1#1000 Ingrain vs Roar: variant = {0} (r2, the rooted Pokemon), not the Roar user (r6)
.org Ingrain_Variant
.area 2
    expect16_at -0x10, 0x1C30    ; 02220B68 adds r0, r6, #0
    expect16_at -0x0E, 0xF7F5    ; 02220B6A bl #0x22167a0
    expect16_at -0x0C, 0xFE19    ; 02220B6C (2/2)
    expect16_at -0x0A, 0x1C06    ; 02220B6E adds r6, r0, #0
    expect16_at -0x08, 0x1C20    ; 02220B70 adds r0, r4, #0
    expect16_at -0x06, 0xF7F5    ; 02220B72 bl #0x22167a0
    expect16_at -0x04, 0xFE15    ; 02220B74 (2/2)
    expect16_at -0x02, 0x1C02    ; 02220B76 adds r2, r0, #0
    expect16_at 0x00, 0x0630    ; 02220B78 lsls r0, r6, #0x18   <- the edit
    expect16_at 0x02, 0x21FA    ; 02220B7A movs r1, #0xfa
    expect16_at 0x04, 0x0E00    ; 02220B7C lsrs r0, r0, #0x18
    expect16_at 0x06, 0x0089    ; 02220B7E lsls r1, r1, #2
    expect16_at 0x08, 0xF009    ; 02220B80 bl #0x2229e1c
    expect16_at 0x0A, 0xF94C    ; 02220B82 (2/2)
    lsl     r0, r2, #0x18
.endarea

; 1#1554 Pledge '{0} is waiting for {1}': variant = {1} (r7), the Pokemon the prefix stands before
.org Pledge_Variant
.area 2
    expect16_at -0x12, 0x9400    ; 02222DD0 str r4, [sp]
    expect16_at -0x10, 0x4808    ; 02222DD2 ldr r0, [pc, #0x20]
    expect16_at -0x0E, 0x9701    ; 02222DD4 str r7, [sp, #4]
    expect16_at -0x0C, 0x9002    ; 02222DD6 str r0, [sp, #8]
    expect16_at -0x0A, 0x4805    ; 02222DD8 ldr r0, [pc, #0x14]
    expect16_at -0x08, 0x4A07    ; 02222DDA ldr r2, [pc, #0x1c]
    expect16_at -0x06, 0x6800    ; 02222DDC ldr r0, [r0]
    expect16_at -0x04, 0x2103    ; 02222DDE movs r1, #3
    expect16_at -0x02, 0x6A00    ; 02222DE0 ldr r0, [r0, #0x20]
    expect16_at 0x00, 0x1C23    ; 02222DE2 adds r3, r4, #0   <- the edit
    expect16_at 0x02, 0xF001    ; 02222DE4 bl #0x2224c50
    expect16_at 0x04, 0xFF34    ; 02222DE6 (2/2)
    add     r3, r7, #0
.endarea

.close
