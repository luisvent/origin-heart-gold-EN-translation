; battle-hit-sound - Battles: a damaging move plays the hit sound again (normal, super effective, not very
; effective). D-2342 (user-approved exception to D-1337).
; Why and what: fix.toml next to this file; overview work/patches/FIXES.md; work/notes/hit-sound_fix.md.
;
; The hack's battle engine (overlay 14) drives the screen with a queue of action commands. Action 28
; (handler table 0x0224AB70, entry 28 = BattleAct_MoveDamage, 0x02204CF0) shows a move's damage: its
; arguments are [target count, type-effectiveness class, move id, ...] and per target a battler id and the
; damage (BattleClient +0x98 / +0x9C, 8 bytes apart). Step 0 builds the target and damage lists, starts the
; blink (0x0222EF1C) and the HP-bar drain (0x022013E0); step 1 waits. The effectiveness class is 1 normal,
; 2 super effective, 3 not very effective (observed: Thunderbolt on Gyarados 2 with 2#74, Tackle on Onix 3
; with 2#75, Tackle on Snorlax 1). Nothing in the handler plays a sound, and no code in the hack plays the
; hit sounds SEQ_SE_DP_KOUKA_H/L/M (1788/1789/1790). The untouched HeartGold plays one of them with every
; hit (battle command 215 -> client handler US overlay12 0x0225B3D4: normal 1790, super 1788, not very 1789).
;
; The fix rewrites step 0's list-building loop (0x02204D0E-0x02204D4F, 66 bytes) more compactly and uses
; the bytes it frees to play the hit sound for the class first: PlaySE(1786 + (class == 1 ? 4 : class)),
; i.e. 1 -> 1790 KOUKA_M, 2 -> 1788 KOUKA_H, 3 -> 1789 KOUKA_L; any other class plays nothing. The loop
; builds the same two lists (target object from 0x02215704 with the battler id's low byte, damage's low
; halfword) for the same count, and leaves the same registers for the unchanged code after it (0x02204D50:
; count at [sp+4], lists at sp+0x18 / sp+0x10, r7 = BattleClient). [sp+8] holds the remaining count
; instead of the index; [sp+0xC] is no longer used (both are scratch slots of this step only).

.nds
.thumb
.include "../include/guards.inc"

.definelabel PlaySE,                     0x02005F5C   ; arm9: PlaySE(u16 seq) (US arm9 0x0200604C)
.definelabel BattleAct_MoveDamage,       0x02204CF0   ; overlay 14, action 28: (client r0, step* r1, args* r2)
.definelabel BattleAct_MoveDamage_Step0, 0x02204D0E   ; step 0: build the lists  <- rewritten
.definelabel BattleAct_MoveDamage_Start, 0x02204D50   ; blink + HP bar, step++   (unchanged)
.definelabel BattleClient_GetMonObject,  0x02215704   ; (r0 = [client+0x28], r1 = battler id) -> object
.definelabel BattleBlink_Start,          0x0222EF1C   ; (objects*, count)
.definelabel BattleHpBar_Start,          0x022013E0   ; (client, objects*, damages*, count)

SEQ_SE_DP_KOUKA_BASE equ 1786                         ; + 2 = KOUKA_H 1788, + 3 = KOUKA_L 1789, + 4 = KOUKA_M 1790

.open "overlay14.bin", 0x022007E0

; Read-only guard: the handler's entry and dispatch, unchanged. r2 (args) is not touched before step 0.
.org BattleAct_MoveDamage
    expect16_at 0x00, 0xB5F8    ; push  {r3-r7, lr}
    expect16_at 0x02, 0xB08A    ; sub   sp, #0x28
    expect16_at 0x04, 0x1C07    ; add   r7, r0, #0              r7 = BattleClient
    expect16_at 0x06, 0x6810    ; ldr   r0, [r2]                args[0] = target count
    expect16_at 0x08, 0x9100    ; str   r1, [sp]                step*
    expect16_at 0x0A, 0x0400    ; lsl   r0, r0, #16
    expect16_at 0x0C, 0x0C00    ; lsr   r0, r0, #16
    expect16_at 0x0E, 0x9001    ; str   r0, [sp, #4]            count (u16)
    expect16_at 0x10, 0x1C08    ; add   r0, r1, #0
    expect16_at 0x12, 0x6800    ; ldr   r0, [r0]                step
    expect16_at 0x14, 0x2800    ; cmp   r0, #0
    expect16_at 0x16, 0xD002    ; beq   BattleAct_MoveDamage_Step0
    expect16_at 0x18, 0x2801    ; cmp   r0, #1
    expect16_at 0x1A, 0xD035    ; beq   0x02204D78              step 1: wait
    expect16_at 0x1C, 0xE03B    ; b     0x02204D86

; Read-only guard: what follows the rewritten part, which relies on [sp+4], sp+0x18, sp+0x10 and r7.
.org BattleAct_MoveDamage_Start
    expect16_at 0x00, 0x9901    ; ldr   r1, [sp, #4]
    expect16_at 0x02, 0xA806    ; add   r0, sp, #0x18           objects
    expect16_at 0x04, 0x0609    ; lsl   r1, r1, #24
    expect16_at 0x06, 0x0E09    ; lsr   r1, r1, #24
    expect16_at 0x08, 0xF02A    ; bl    BattleBlink_Start (1/2)
    expect16_at 0x0A, 0xF8E0    ;                         (2/2)
    expect16_at 0x0C, 0x9B01    ; ldr   r3, [sp, #4]
    expect16_at 0x0E, 0x1C38    ; add   r0, r7, #0
    expect16_at 0x10, 0x061B    ; lsl   r3, r3, #24
    expect16_at 0x12, 0xA906    ; add   r1, sp, #0x18           objects
    expect16_at 0x14, 0xAA04    ; add   r2, sp, #0x10           damages
    expect16_at 0x16, 0x0E1B    ; lsr   r3, r3, #24
    expect16_at 0x18, 0xF7FC    ; bl    BattleHpBar_Start (1/2)
    expect16_at 0x1A, 0xFB3A    ;                         (2/2)

; The edit: step 0's loop, rewritten, with the hit sound in front of it.
.org BattleAct_MoveDamage_Step0
.area BattleAct_MoveDamage_Start - BattleAct_MoveDamage_Step0
    expect16_at 0x00, 0x2000    ; mov   r0, #0
    expect16_at 0x02, 0x9002    ; str   r0, [sp, #8]            i = 0
    expect16_at 0x04, 0x9801    ; ldr   r0, [sp, #4]
    expect16_at 0x06, 0x2800    ; cmp   r0, #0
    expect16_at 0x08, 0xDD1B    ; ble   BattleAct_MoveDamage_Start
    expect16_at 0x0A, 0x9E02    ; ldr   r6, [sp, #8]
    expect16_at 0x0C, 0xAC06    ; add   r4, sp, #0x18
    expect16_at 0x0E, 0xAD04    ; add   r5, sp, #0x10
    expect16_at 0x10, 0x00B0    ; lsl   r0, r6, #2              loop: offset 8 * i
    expect16_at 0x12, 0x9003    ; str   r0, [sp, #0xC]
    expect16_at 0x14, 0x9903    ; ldr   r1, [sp, #0xC]
    expect16_at 0x16, 0x6AB8    ; ldr   r0, [r7, #0x28]
    expect16_at 0x18, 0x1879    ; add   r1, r7, r1
    expect16_at 0x1A, 0x3198    ; add   r1, #0x98
    expect16_at 0x1C, 0x6809    ; ldr   r1, [r1]                battler id
    expect16_at 0x1E, 0x0609    ; lsl   r1, r1, #24
    expect16_at 0x20, 0x0E09    ; lsr   r1, r1, #24
    expect16_at 0x22, 0xF010    ; bl    BattleClient_GetMonObject (1/2)
    expect16_at 0x24, 0xFCE8    ;                                 (2/2)
    expect16_at 0x26, 0xC401    ; stmia r4!, {r0}
    expect16_at 0x28, 0x9803    ; ldr   r0, [sp, #0xC]
    expect16_at 0x2A, 0x1CB6    ; add   r6, r6, #2
    expect16_at 0x2C, 0x1838    ; add   r0, r7, r0
    expect16_at 0x2E, 0x309C    ; add   r0, #0x9C
    expect16_at 0x30, 0x6800    ; ldr   r0, [r0]                damage
    expect16_at 0x32, 0x8028    ; strh  r0, [r5]
    expect16_at 0x34, 0x9802    ; ldr   r0, [sp, #8]
    expect16_at 0x36, 0x1CAD    ; add   r5, r5, #2
    expect16_at 0x38, 0x1C41    ; add   r1, r0, #1
    expect16_at 0x3A, 0x9801    ; ldr   r0, [sp, #4]
    expect16_at 0x3C, 0x9102    ; str   r1, [sp, #8]
    expect16_at 0x3E, 0x4281    ; cmp   r1, r0
    expect16_at 0x40, 0xDBE6    ; blt   loop

    ; The hit sound, by the effectiveness class args[1] (r2 = args, untouched since the entry).
    ldr     r0, [r2, #4]                    ; class: 1 normal, 2 super effective, 3 not very effective
    sub     r1, r0, #1
    cmp     r1, #2
    bhi     @@lists                         ; any other class: no sound
    cmp     r0, #1
    bne     @@play
    mov     r0, #4                          ; normal -> KOUKA_M
@@play:
    mov     r1, #(SEQ_SE_DP_KOUKA_BASE / 8)
    lsl     r1, r1, #3
    add     r0, r0, r1
    add     r0, #(SEQ_SE_DP_KOUKA_BASE - (SEQ_SE_DP_KOUKA_BASE / 8) * 8)
    bl      PlaySE                          ; 1788 / 1789 / 1790

    ; The target and damage lists, as before: object of each battler id, damage, count targets.
@@lists:
    add     r6, r7, #0
    add     r6, #0x98                       ; r6 = &BattleClient+0x98 (battler id), +4 damage; 8 per target
    add     r4, sp, #0x18                   ; objects
    add     r5, sp, #0x10                   ; damages (u16)
    ldr     r0, [sp, #4]
    str     r0, [sp, #8]                    ; remaining = count
@@loop:
    ldr     r0, [sp, #8]
    sub     r0, #1
    bmi     BattleAct_MoveDamage_Start
    str     r0, [sp, #8]
    ldrh    r0, [r6, #4]
    strh    r0, [r5]
    add     r5, #2
    ldrb    r1, [r6]
    add     r6, #8
    ldr     r0, [r7, #0x28]
    bl      BattleClient_GetMonObject
    stmia   r4!, {r0}
    b       @@loop
.endarea
.if org() != BattleAct_MoveDamage_Start
    .error "battle-hit-sound: the rewritten step 0 must end at 0x02204D50"
.endif

.close
