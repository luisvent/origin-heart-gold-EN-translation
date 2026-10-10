; battle-heal-hpbar-switched-out - Battle: a healing item used on a Pokemon that is forced out later in the
; same turn (Roar, ...) no longer freezes the game (Maxie gauntlet, Lavender Town). D-2314 (user-approved
; exception to D-1337). Why and what: fix.toml next to this file; overview work/patches/FIXES.md;
; work/notes/melonds-retest_fix.md.
;
; The hack's battle engine (overlay 14) computes a whole turn first and then plays it back on the client.
; A Potion from the battle Bag queues the client command handled by BattleHeal_Cmd (0x022053D0): state 0
; calls BattleHeal_StartBar (0x0222E024, r1 = the healed Pokemon's id byte, r2 = HP, r3 = the command's done
; flag), state 1 waits for that flag. BattleHeal_StartBar looks up the battler that shows the Pokemon
; (0x02228740: battler 0-3, or 5 when the Pokemon is not on the field), turns it into a health-bar index
; (0x022156C4) and starts a task (0x0222DFE8) that animates that health bar and sets the done flag.
; The lookup reads the party order after the whole turn. When the same turn forces the healed Pokemon out
; (Houndoom's Roar in the gauntlet's second wave), it is no longer on the field: the lookup returns 5, the
; index table gives health bar 0, which a double battle never sets up, and the task's gauge drawing reads
; the bar's NULL sprite (ldr r0, [r0] at 0x02210C9E). melonDS 1.1 (and the hardware's protection unit)
; raise a data abort there and the game freezes on 'used the Potion!'; DeSmuME reads address 0 and goes on.
; In a single battle the same index points at the opponent's bar instead.
;
; The fix: when the lookup returns 5, BattleHeal_StartBar writes that nonzero value to the done flag and
; returns without a health-bar task (the Pokemon's bar is not on screen; it is drawn from its current HP when
; it comes back). To make room in place, the routine is re-laid: the caller passes the id in r0 (it was
; loaded into r1 and r0 was unused), and G + 0x2AC + index * 0x3C is computed as G + (index + 11) * 0x3C
; + 0x18. Every other step, its order, the task, its priority and the literal pool are unchanged.

.nds
.thumb
.include "../include/guards.inc"

.definelabel BattleHeal_Cmd,        0x022053D0   ; client command handler: state 0 start, state 1 wait
.definelabel BattleHeal_CmdLoadR0,  0x022053E8   ; ldr r0, [r3, #0x28] (r0 unused by the callee)  <- edit 1
.definelabel BattleHeal_StartBar,   0x0222E024   ; r1 = Pokemon id, r2 = HP, r3 = done flag      <- edit 2
.definelabel Battle_BattlerOfMon,   0x02228740   ; id -> battler 0-3, 5 = not on the field
.definelabel Battle_HealthbarIndex, 0x022156C4   ; battler -> health-bar index (table 0x0224D134)
.definelabel Healthbar_SetHpChange, 0x02210A64
.definelabel CreateSysTask,         0x0200DE74
.definelabel HealthbarHeal_Task,    0x0222DFE9   ; the bar animation task (Thumb)
.definelabel Battle_Global,         0x02255C74   ; -> G; health bars at G + 0x2AC, 0x3C bytes each

.open "overlay14.bin", 0x022007E0

; Edit 1: the handler passes the id byte in r0 as well (r1 holds id << 24 here).
.org BattleHeal_Cmd
    expect16_at 0x00, 0xB538    ; push  {r3-r5, lr}
    expect16_at 0x02, 0x1C0C    ; add   r4, r1, #0
    expect16_at 0x04, 0x1C03    ; add   r3, r0, #0
    expect16_at 0x06, 0x6820    ; ldr   r0, [r4]                state
    expect16_at 0x08, 0x2800    ; cmp   r0, #0
    expect16_at 0x0A, 0xD002    ; beq   state 0
    expect16_at 0x0C, 0x2801    ; cmp   r0, #1
    expect16_at 0x0E, 0xD00E    ; beq   state 1
    expect16_at 0x10, 0xE014    ; b     return 0
    expect16_at 0x12, 0x6811    ; ldr   r1, [r2]                Pokemon id (command argument 0)
    expect16_at 0x14, 0x255D    ; mov   r5, #0x5D
    expect16_at 0x16, 0x0609    ; lsl   r1, r1, #0x18
    expect16_at 0x1A, 0x012D    ; lsl   r5, r5, #4              done flag at +0x5D0
    expect16_at 0x1C, 0x6852    ; ldr   r2, [r2, #4]            HP (command argument 1)
    expect16_at 0x1E, 0x0E09    ; lsr   r1, r1, #0x18
    expect16_at 0x20, 0x195B    ; add   r3, r3, r5
    expect16_at 0x22, 0xF028    ; bl    BattleHeal_StartBar     (1/2)
    expect16_at 0x24, 0xFE17    ;                               (2/2)
.org BattleHeal_CmdLoadR0
.area 2
    expect16 0x6A98             ; ldr   r0, [r3, #0x28]
    lsr     r0, r1, #0x18
.endarea

; Edit 2: BattleHeal_StartBar, push through literal pool (0x4C bytes), re-laid with the not-on-field exit.
.org BattleHeal_StartBar
    expect32_at 0x00, 0x1C08B570    ; push {r4-r6, lr}; add r0, r1, #0
    expect32_at 0x04, 0x1C1D1C16    ; add r6, r2, #0; add r5, r3, #0
    expect32_at 0x08, 0xFB88F7FA    ; bl Battle_BattlerOfMon
    expect32_at 0x0C, 0xFB48F7E7    ; bl Battle_HealthbarIndex
    expect32_at 0x10, 0x680A490C    ; ldr r1, =Battle_Global; ldr r2, [r1]
    expect32_at 0x14, 0x008921AB    ; mov r1, #0xAB; lsl r1, r1, #2
    expect32_at 0x18, 0x213C1852    ; add r2, r2, r1; mov r1, #0x3C
    expect32_at 0x1C, 0x18544341    ; mul r1, r0; add r4, r2, r1
    expect32_at 0x20, 0x1C311C20    ; add r0, r4, #0; add r1, r6, #0
    expect32_at 0x24, 0xFD0CF7E2    ; bl Healthbar_SetHpChange
    expect32_at 0x28, 0x22FA1C20    ; add r0, r4, #0; mov r2, #0xFA
    expect32_at 0x2C, 0x210063A5    ; str r5, [r4, #0x38]; mov r1, #0
    expect32_at 0x30, 0x30237029    ; strb r1, [r5]; add r0, #0x23
    expect32_at 0x34, 0x48047001    ; strb r1, [r0]; ldr r0, =HealthbarHeal_Task
    expect32_at 0x38, 0x00921C21    ; add r1, r4, #0; lsl r2, r2, #2
    expect32_at 0x3C, 0xFF08F5DF    ; bl CreateSysTask
    expect32_at 0x40, 0x46C0BD70    ; pop {r4-r6, pc}; nop
    expect32_at 0x44, Battle_Global
    expect32_at 0x48, HealthbarHeal_Task
.area 0x4C
    push    {r4-r6, lr}
    add     r6, r2, #0              ; HP
    add     r5, r3, #0              ; done flag
    bl      Battle_BattlerOfMon     ; r0 = Pokemon id (edit 1)
    cmp     r0, #5
    beq     @@not_on_field
    bl      Battle_HealthbarIndex
    add     r0, #11
    mov     r1, #0x3C
    mul     r0, r1
    ldr     r1, [@@global]
    ldr     r1, [r1]
    add     r4, r1, r0
    add     r4, #0x18               ; r4 = G + 0x2AC + index * 0x3C
    add     r0, r4, #0
    add     r1, r6, #0
    bl      Healthbar_SetHpChange
    str     r5, [r4, #0x38]         ; the task sets this flag when it ends
    mov     r1, #0
    strb    r1, [r5]
    mov     r0, #0x23
    strb    r1, [r4, r0]            ; task state 0
    ldr     r0, [@@task]
    add     r1, r4, #0
    mov     r2, #0xFA
    lsl     r2, r2, #2              ; priority 1000
    bl      CreateSysTask
    pop     {r4-r6, pc}
@@not_on_field:
    strb    r0, [r5]                ; done (5): the handler moves on, no bar to animate
    pop     {r4-r6, pc}
.align 4
@@global:
    .word   Battle_Global
@@task:
    .word   HealthbarHeal_Task
.endarea

.close
