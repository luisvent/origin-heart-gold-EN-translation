; faint-waits-for-hp-bar - Battle: a Pokémon knocked out by a multi-hit move faints after its HP bar has
; drained, not halfway through it. D-2318 (user-approved exception to D-1337).
; Why and what: fix.toml next to this file; overview work/patches/FIXES.md; work/notes/multihit-ko-hpbar_fix.md.
;
; The hack's battle client (overlay 14) plays each turn as a list of commands. Command 8 (a hit: blink and
; HP bar) starts the HP-bar task 0x02201328 through 0x022013E0 and waits only for the blink; the bar keeps
; draining afterwards. HpBarTask_Start clears the byte HpBarDone (0x02252D3E) and the task sets it to 1 when
; every bar it drives is at its new value (command 12 waits for that byte). Command 21 (the faint: cry, HP box
; redrawn and slid off, sprite drops; Faint_Run 0x0222CB7C) does not look at it. After a one-hit KO a message
; ('The wild ... fainted!', 54 frames) comes between the two commands and the bar has time to finish; after
; the KO hit of a multi-hit move the faint comes straight after the hit, so it starts while the bar is still
; draining: the HP box is redrawn from the bar's HP before the hit (it looks full again) and slides away.
;
; The fix:
; 1. Command 21 waits while HpBarDone is 0: its handler returns 'not done' until every running HP bar has
;    finished, then runs Faint_Run as before. The new handler sits 2 bytes earlier, in the alignment padding
;    before the old one (0x02205122), so the table entry for command 21 moves with it.
; 2. HpBarDone starts at 1 ('no bar running'): it is in overlay 14's .bss, which is 0 when a battle starts, and
;    a faint before the first HP bar of the battle would otherwise wait for ever. BattleMisc_Reset (0x02200B64,
;    called once when the battle client is set up) zeroes the halfwords 0x02252D30..0x02252D3B; it now zeroes
;    the same bytes with three word stores and sets HpBarDone to 1 with the 4 bytes this frees.
; HpBarDone is written only by HpBarTask_Start (0), the HP-bar task's end (1) and the level-up effect
; 0x022115C0/0x02211604 (0, then 1), and read by command 12 and the level-up step at 0x0222F88C; each of
; those starts its own task before it reads the byte, so the start value changes nothing for them.

.nds
.thumb
.include "../include/guards.inc"

.definelabel BattleMisc_Reset,        0x02200B64   ; battle client set-up (0x02224E9C): zero 0x02252D30..3B
.definelabel BattleMisc_Pool,         0x02200B78   ; .word 0x02252D30
.definelabel HpBarTask_Start,         0x022013E0   ; strb 0 -> HpBarDone, start task 0x02201328
.definelabel HpBarTask_Done,          0x022013C2   ; the task's end: strb 1 -> HpBarDone
.definelabel ClientCmd_Table,         0x0224ABC0   ; 0x5E command handlers (Thumb pointers)
.definelabel ClientCmd21_Slot,        0x0224AC14   ; ClientCmd_Table[21]
.definelabel ClientCmdX_End,          0x02205120   ; end of the handler before command 21's (0x02205114)
.definelabel ClientCmd21_New,         0x02205122   ; the new handler (alignment padding + the old handler)
.definelabel ClientCmd21_Old,         0x02205124
.definelabel Faint_Run,               0x0222CB7C   ; (client, battler) -> 1 when the faint is finished
.definelabel HpBarMisc,               0x02252D3C   ; u8 [3]: two counters, HpBarDone at +2

.open "overlay14.bin", 0x022007E0

; ---------------------------------------------------------------------------------------------- 1. command 21
; Read-only guard: the task end and start that write HpBarDone (the meaning the new handler relies on).
.org HpBarTask_Done
    expect16_at 0x00, 0x4806    ; ldr   r0, =HpBarMisc
    expect16_at 0x02, 0x2101    ; mov   r1, #1
    expect16_at 0x04, 0x7081    ; strb  r1, [r0, #2]            HpBarDone = 1: every bar finished
    expect32_abs 0x022013DC, HpBarMisc
.org HpBarTask_Start + 0x3E
    expect16_at 0x00, 0x4804    ; ldr   r0, =HpBarMisc
    expect16_at 0x02, 0x2200    ; mov   r2, #0
    expect16_at 0x04, 0x7082    ; strb  r2, [r0, #2]            HpBarDone = 0: a bar starts draining
    expect32_abs 0x02201430, HpBarMisc

; The handler before command 21's ends with its pop; the next halfword is alignment padding.
.org ClientCmdX_End
    expect16_at 0x00, 0xBD08    ; pop   {r3, pc}

; Command 21's handler: the old one ran Faint_Run(client, args[0] & 0xFF) and turned its result into 1 / 0.
; args[0] is the battler, read as one byte (argument type 1 of command 21: 0x0224D234 [21] = 1 -> 0x0222433C),
; so the mask did nothing; Faint_Run returns 1 or 0 itself and the interpreter (0x02204692) only tests
; for non-zero, so its result is returned as it is.
.org ClientCmd21_New
.area 0x1A
    expect16_at 0x00, 0x0000    ; padding
    expect16_at 0x02, 0xB508    ; push  {r3, lr}                old handler
    expect16_at 0x04, 0x6811    ; ldr   r1, [r2]
    expect16_at 0x06, 0x0609    ; lsl   r1, r1, #24
    expect16_at 0x08, 0x0E09    ; lsr   r1, r1, #24
    expect16_at 0x0A, 0xF027    ; bl    Faint_Run  (1/2)
    expect16_at 0x0C, 0xFD26    ;                  (2/2)
    expect16_at 0x0E, 0x2800    ; cmp   r0, #0
    expect16_at 0x10, 0xD001    ; beq   0x02205138
    expect16_at 0x12, 0x2001    ; mov   r0, #1
    expect16_at 0x14, 0xBD08    ; pop   {r3, pc}
    expect16_at 0x16, 0x2000    ; mov   r0, #0
    expect16_at 0x18, 0xBD08    ; pop   {r3, pc}
    push    {r3, lr}
    ldr     r3, [@@misc]
    ldrb    r3, [r3, #2]        ; HpBarDone
    cmp     r3, #0
    beq     @@wait              ; an HP bar is still draining: not done, ask again next frame
    ldr     r1, [r2]            ; battler
    bl      Faint_Run
    pop     {r3, pc}
@@wait:
    mov     r0, #0
    pop     {r3, pc}
@@misc:
    .word   HpBarMisc
.endarea

.org ClientCmd21_Slot
.area 4
    expect32 ClientCmd21_Old + 1
    .word   ClientCmd21_New + 1
.endarea

; ---------------------------------------------------------------------------------------------- 2. start value
.org BattleMisc_Reset
    expect16_at 0x00, 0x4804    ; ldr   r0, =0x02252D30          (kept)
    expect32_abs BattleMisc_Pool, 0x02252D30
.org BattleMisc_Reset + 2
.area 0x12
    expect16_at 0x00, 0x2100    ; mov   r1, #0
    expect16_at 0x02, 0x8001    ; strh  r1, [r0]
    expect16_at 0x04, 0x8041    ; strh  r1, [r0, #2]
    expect16_at 0x06, 0x8081    ; strh  r1, [r0, #4]
    expect16_at 0x08, 0x80C1    ; strh  r1, [r0, #6]
    expect16_at 0x0A, 0x8101    ; strh  r1, [r0, #8]
    expect16_at 0x0C, 0x8141    ; strh  r1, [r0, #0xA]
    expect16_at 0x0E, 0x4770    ; bx    lr
    expect16_at 0x10, 0x46C0    ; nop   (padding before the literal)
    mov     r1, #0
    str     r1, [r0]            ; 0x02252D30..33  (word-aligned: the same 12 bytes as the six halfwords)
    str     r1, [r0, #4]        ; 0x02252D34..37
    str     r1, [r0, #8]        ; 0x02252D38..3B
    mov     r1, #1
    strb    r1, [r0, #0xE]      ; HpBarDone (0x02252D3E) = 1: no HP bar running yet
    bx      lr
    nop
    nop
.endarea

.close
