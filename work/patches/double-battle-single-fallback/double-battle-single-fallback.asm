; double-battle-single-fallback - a scripted Double Battle with fewer than two Pokemon in the party becomes a
; Single Battle (no frozen battle). D-2357 (user decision 2026-10-12); answers the hack finding D-1559
; (Department Store 6F and the other scripted doubles).
; Why and what: fix.toml next to this file; overview work/patches/FIXES.md;
; work/notes/double-battle-single-fallback_fix.md.
;
; Every scripted trainer battle (TrainerBattle 213, MultiBattle 562) reaches the battle setup at 0x02050768
; (r1 trainer 1, r2 trainer 2, r3 partner). It chooses the battle type r4 and builds the setup with
; BattleSetup_New(11, r4) at 0x020507A8:
;     trainer 2 = 0                         -> 1      single
;     trainer 2 = trainer 1                 -> 3      double, the same trainer twice
;     trainer 2 other, no partner (r3 = 0)  -> 0x13   double, two trainers
;     trainer 2 other, partner              -> 0x4B   multi battle (the partner is the ally)
; Nothing looks at the party. With fewer than two Pokemon the second player slot is empty and the battle
; init (overlay 14) reads a party index as a pointer: DeSmuME shows a broken ally and a blank screen,
; melonDS aborts at 0x022167B4.
;
; The fix: just before BattleSetup_New, when the type is 3 or 0x13 (bit 1 set, partner bit 0x40 clear) and the
; party holds fewer than two Pokemon (party count, not the number able to fight: one healthy Pokemon next to a
; fainted one or an Egg behaves exactly as before), r4 = 1 and trainer 2 (r6) = 0: a single battle against
; trainer 1. The multi battle (0x4B), the single battle (1, 0x801) and every other BattleSetup_New caller
; (wild encounters, link, facilities) are untouched.
;
; Where the 40 bytes live: the hack's script command 223 handler (0x02048EC8, 44 bytes) battles trainer 1
; singly. No script of the hack uses command 223 (every TrainerBattle-family command of a/0/1/2 was scanned),
; and nothing but its command table slot points at it. It is overwritten with the hook; the table slot stays
; (a script that used it would crash, none does). The hook is entered by bl from 0x020507A4 and runs with the
; setup function's frame (no push): r4 type, r6 trainer 2, r5 free (the function sets it after BattleSetup_New),
; [sp,#0xC] the field system.

.nds
.thumb
.include "../include/guards.inc"

.definelabel ScriptCmdTable,         0x020F793C   ; u32 handler (Thumb) per script command
.definelabel SaveArray_Party_Get,    0x0207365C   ; (save data) -> party
.definelabel Party_GetCount,         0x02073398   ; (party) -> count
.definelabel BattleSetup_New,        0x02050C34   ; (heap 11, battle type) -> setup
.definelabel BattleSetup_Trainer,    0x02050768   ; (task, trainer 1, trainer 2, partner, ...)
.definelabel ScrCmd_223,             0x02048EC8   ; dead command: overwritten by the hook
.definelabel Setup_NewCall,          0x020507A4   ; movs r0,#0xB ; adds r1,r4,#0 ; bl BattleSetup_New  <- the edit

.open "arm9.bin", 0x02000000

; Read-only: command 223 is the routine, and the setup function is where this fix expects.
expect32_abs ScriptCmdTable + 4 * 223, ScrCmd_223 + 1
.org BattleSetup_Trainer
    expect16_at 0x00, 0xB5F8    ; push  {r3-r7, lr}
    expect16_at 0x02, 0xB084    ; sub   sp, #0x10
    expect16_at 0x04, 0x9001    ; str   r0, [sp, #4]
    expect16_at 0x06, 0x1C0F    ; add   r7, r1, #0              r7 = trainer 1
    expect16_at 0x08, 0x1C16    ; add   r6, r2, #0              r6 = trainer 2
    expect16_at 0x0A, 0x9302    ; str   r3, [sp, #8]            partner
    expect16_at 0x0C, 0xF7FF    ; bl    0x0204FAD4              (1/2)  the field system
    expect16_at 0x0E, 0xF9AE    ;                               (2/2)
    expect16_at 0x10, 0x9003    ; str   r0, [sp, #0xC]

; The hook (the old command 223 handler, 44 bytes; 40 used, the rest is padding).
.org ScrCmd_223
.area 44
    expect16_at 0x00, 0xB510    ; push  {r4, lr}                old: battle trainer 1 (command 223)
    expect16_at 0x02, 0xB084    ; sub   sp, #0x10
    expect16_at 0x2A, 0xBD10    ; pop   {r4, pc}
    mov     r5, lr              ; return address (r5 is free until BattleSetup_New returns)
    mov     r0, #0x42
    and     r0, r4              ; bit 1 (double) and bit 6 (partner)
    cmp     r0, #2
    bne     @@go                ; not a plain double (1, 0x801, 0x4B): unchanged
    ldr     r0, [sp, #0xC]      ; field system
    ldr     r0, [r0, #0xC]      ; save data
    bl      SaveArray_Party_Get
    bl      Party_GetCount
    cmp     r0, #2
    bge     @@go                ; two Pokemon or more: unchanged
    mov     r4, #1              ; single battle ...
    mov     r6, #0              ; ... against trainer 1 only
@@go:
    mov     r0, #0xB
    add     r1, r4, #0
    bl      BattleSetup_New
    bx      r5
    nop
    nop
.endarea

; The edit: BattleSetup_New(11, r4) becomes the hook (the hook does the same call). The old bl is a nop.
.org Setup_NewCall
.area 8
    expect16_at 0x00, 0x200B    ; movs  r0, #0xB
    expect16_at 0x02, 0x1C21    ; adds  r1, r4, #0
    expect16_at 0x04, 0xF000    ; bl    BattleSetup_New         (1/2)
    expect16_at 0x06, 0xFA44    ;                               (2/2)
    bl      ScrCmd_223
    nop
    nop
.endarea

.close
