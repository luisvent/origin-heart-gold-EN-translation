; battle-faint-cry - Battles: a Pokemon that faints plays its cry (the low faint cry) and the faint sound again,
; on both sides, as in HeartGold. D-2341 (user-approved exception to D-1337).
; Why and what: fix.toml next to this file; overview work/patches/FIXES.md; work/notes/faint-cry_fix.md.
;
; The hack's battle engine (overlay 14) shows a faint with client command 21, whose handler calls Faint_Run
; (0x0222CB7C) once per frame until it returns 1. Faint_Run is a small state machine (state byte FaintState+1,
; FaintState = 0x02255EDC): 0 prepare (Faint_Prepare), 1 wait while a cry is playing (Cry_IsPlaying), start the
; health box task (Faint_HealthboxOut) and go to 2 if the sprite is raised (attribute 0x29) else 3, 2 lower it,
; 3 set up the partial draw, 4 slide the sprite down 8 px a frame and hide it, 5 wait for the health box, done.
; It never starts a cry or a sound, so state 1 waits for nothing. HeartGold's faint task in overlay 12 has the
; same states and, before the slide, plays the cry in faint mode and waits for it, then the faint sound:
;   state 4 (US overlay12 0x022601FA): pan = +117 for a front sprite (the foe), -117 for a back sprite;
;     PlayCryWithChatter(chatter, mode 5, species, form, pan, 127, ..., heap 5, delay 0)
;     (US overlay12 0x0226022A; US arm9 0x0207204C)
;   state 5: wait while a cry plays (US overlay12 0x02260244)
;   state 6: PlaySEWithPan(SEQ_SE_DP_POKE_DEAD3 = 1795, pan) (US overlay12 0x0226026E)
;
; The fix rewrites Faint_Run in place (same entry, same 352 bytes, same states and calls) more compactly and
; uses the bytes it frees for the two sounds:
;   * state 0, when Faint_Prepare reports ready: Cry_Play(mode 5, species, pan, 127, heap 5, delay 0, form),
;     the hack's own cry routine (arm9 0x02006898, the one its send-out cries use), with the species and form
;     the sprite shows (the same MonView fields state 3 already reads);
;   * state 1, once the cry has ended: PlaySEWithPan(1795, pan) (arm9 0x02005F3C).
; Pan = (facing - 1) * 117 with the facing value Faint_Run already computes for state 3 (0 back, 2 front).
; Compacting, without a behaviour change: the facing is computed without the [sp+8] round trip and the byte
; mask, states 0, 3 and 4 share one 'set state' tail, state 3 reads species, form and gender from the MonView
; directly (the three getters are one-instruction loads: +0, +5, +0x239), and state 4 moves the sprite down
; with Sprite_AddAttr(1, 8) (arm9 0x02008BC8: attribute 1 is the halfword +0x26 that Sprite_GetAttr /
; Sprite_SetAttr read and write). Everything else is the original code in the original order.
; Not as in HeartGold: Chatot plays its normal cry, not a Chatter recording (the hack's send-out cries do the
; same); command 21's handler and its table entry are not touched.

.nds
.thumb
.include "../include/guards.inc"

; overlay 14 (the hack's battle engine)
.definelabel Faint_Run,               0x0222CB7C   ; (client r0, battler r1) -> 1 when the faint is shown  <- rewritten
.definelabel Faint_Run_End,           0x0222CCDC   ; the next function (unchanged)
.definelabel Battle_GetSpriteSlot,    0x02228778   ; ([client+0x28], battler) -> sprite slot
.definelabel Battler_FacingKind,      0x0222850C   ; (battler) -> 0: back sprite (player's side), else front
.definelabel BattleSprite_Get,        0x02227F28   ; (slot) -> the Pokemon sprite
.definelabel Battle_GetMonView,       0x022151B0   ; ([client+0x28], battler) -> MonView:
                                                   ;   +0 species, +5 form, +0x239 gender
.definelabel Faint_Prepare,           0x0222DBB0   ; (client, slot, 0, 1) -> nonzero when ready (also command 20)
.definelabel Faint_HealthboxOut,      0x0222DF40   ; ([client+0x28], slot, 0): health box task;
                                                   ;   FaintState+0 = 1 until it is done
.definelabel FaintState,              0x02255EDC   ; +0 health box busy, +1 Faint_Run's state
; arm9
.definelabel PlaySEWithPan,           0x02005F3C   ; (u16 seq, pan) (US arm9 0x0200602C)
.definelabel Cry_IsPlaying,           0x02006258   ; () -> nonzero while a cry plays
.definelabel Cry_Play,                0x02006898   ; (mode, species, pan, volume, [sp] heap, [sp+4] delay, [sp+8] form)
.definelabel Sprite_Delete,           0x0200871C   ; (sprite)
.definelabel Sprite_SetAttr,          0x02008740   ; (sprite, attribute, value)
.definelabel Sprite_GetAttr,          0x02008A14   ; (sprite, attribute) -> value
.definelabel Sprite_AddAttr,          0x02008BC8   ; (sprite, attribute, delta)
.definelabel Sprite_SetPartialDraw,   0x02009028   ; (sprite, 0, 0, [sp] height)
.definelabel Mon_GetSpriteYOffset,    0x0206FCBC   ; (species, gender, facing, form, [sp] 0) -> y offset

CRY_MODE_FAINT          equ 5        ; HeartGold's faint cry mode
HEAP_ID_BATTLE          equ 5
CRY_VOLUME              equ 127
FAINT_PAN               equ 117      ; 0x75: + for a front sprite (foe), - for a back sprite
SEQ_SE_DP_POKE_DEAD3    equ 1795     ; HeartGold's faint sound
ATTR_Y                  equ 1        ; sprite y (halfword +0x26)
ATTR_HEIGHT             equ 0x12     ; visible height while sliding down
ATTR_RAISE              equ 0x29     ; elevation of a raised sprite
MONVIEW_GENDER          equ 0x239

.open "overlay14.bin", 0x022007E0

; The edit: Faint_Run, rewritten in its own 352 bytes. The guards check every original halfword.
.org Faint_Run
.area Faint_Run_End - Faint_Run, 0x00
    expect16_at 0x000, 0xB5F0    ; push {r4, r5, r6, r7, lr}
    expect16_at 0x002, 0xB083    ; sub sp, #0xc
    expect16_at 0x004, 0x1C05    ; adds r5, r0, #0
    expect16_at 0x006, 0x6AA8    ; ldr r0, [r5, #0x28]
    expect16_at 0x008, 0x1C0F    ; adds r7, r1, #0
    expect16_at 0x00A, 0xF7FB    ; bl Battle_GetSpriteSlot (1/2)
    expect16_at 0x00C, 0xFDF7    ;   (2/2)
    expect16_at 0x00E, 0x1C06    ; adds r6, r0, #0
    expect16_at 0x010, 0x1C38    ; adds r0, r7, #0
    expect16_at 0x012, 0xF7FB    ; bl Battler_FacingKind (1/2)
    expect16_at 0x014, 0xFCBD    ;   (2/2)
    expect16_at 0x016, 0x9002    ; str r0, [sp, #8]
    expect16_at 0x018, 0x1C30    ; adds r0, r6, #0
    expect16_at 0x01A, 0xF7FB    ; bl BattleSprite_Get (1/2)
    expect16_at 0x01C, 0xF9C7    ;   (2/2)
    expect16_at 0x01E, 0x1C04    ; adds r4, r0, #0
    expect16_at 0x020, 0x6AA8    ; ldr r0, [r5, #0x28]
    expect16_at 0x022, 0x1C39    ; adds r1, r7, #0
    expect16_at 0x024, 0xF7E8    ; bl Battle_GetMonView (1/2)
    expect16_at 0x026, 0xFB06    ;   (2/2)
    expect16_at 0x028, 0x1C07    ; adds r7, r0, #0
    expect16_at 0x02A, 0x9802    ; ldr r0, [sp, #8]
    expect16_at 0x02C, 0x2800    ; cmp r0, #0
    expect16_at 0x02E, 0xD101    ; bne #0x222cbb0
    expect16_at 0x030, 0x2000    ; movs r0, #0
    expect16_at 0x032, 0xE000    ; b #0x222cbb2
    expect16_at 0x034, 0x2002    ; movs r0, #2
    expect16_at 0x036, 0x0600    ; lsls r0, r0, #0x18
    expect16_at 0x038, 0x0E00    ; lsrs r0, r0, #0x18
    expect16_at 0x03A, 0x9001    ; str r0, [sp, #4]
    expect16_at 0x03C, 0x4847    ; ldr r0, [pc, #0x11c]
    expect16_at 0x03E, 0x7841    ; ldrb r1, [r0, #1]
    expect16_at 0x040, 0x2905    ; cmp r1, #5
    expect16_at 0x042, 0xD900    ; bls #0x222cbc2
    expect16_at 0x044, 0xE087    ; b #0x222ccd2
    expect16_at 0x046, 0x1849    ; adds r1, r1, r1
    expect16_at 0x048, 0x4479    ; add r1, pc
    expect16_at 0x04A, 0x88C9    ; ldrh r1, [r1, #6]
    expect16_at 0x04C, 0x0409    ; lsls r1, r1, #0x10
    expect16_at 0x04E, 0x1409    ; asrs r1, r1, #0x10
    expect16_at 0x050, 0x448F    ; add pc, r1
    expect16_at 0x052, 0x000A    ; data
    expect16_at 0x054, 0x0022    ; data
    expect16_at 0x056, 0x004E    ; data
    expect16_at 0x058, 0x0072    ; data
    expect16_at 0x05A, 0x00B2    ; data
    expect16_at 0x05C, 0x00F2    ; data
    expect16_at 0x05E, 0x1C28    ; adds r0, r5, #0
    expect16_at 0x060, 0x1C31    ; adds r1, r6, #0
    expect16_at 0x062, 0x2200    ; movs r2, #0
    expect16_at 0x064, 0x2301    ; movs r3, #1
    expect16_at 0x066, 0xF000    ; bl Faint_Prepare (1/2)
    expect16_at 0x068, 0xFFE5    ;   (2/2)
    expect16_at 0x06A, 0x2800    ; cmp r0, #0
    expect16_at 0x06C, 0xD073    ; beq #0x222ccd2
    expect16_at 0x06E, 0x483B    ; ldr r0, [pc, #0xec]
    expect16_at 0x070, 0x2101    ; movs r1, #1
    expect16_at 0x072, 0x7041    ; strb r1, [r0, #1]
    expect16_at 0x074, 0xE06F    ; b #0x222ccd2
    expect16_at 0x076, 0xF5D9    ; bl Cry_IsPlaying (1/2)
    expect16_at 0x078, 0xFB31    ;   (2/2)
    expect16_at 0x07A, 0x2800    ; cmp r0, #0
    expect16_at 0x07C, 0xD16B    ; bne #0x222ccd2
    expect16_at 0x07E, 0x1C20    ; adds r0, r4, #0
    expect16_at 0x080, 0x2129    ; movs r1, #0x29
    expect16_at 0x082, 0xF5DB    ; bl Sprite_GetAttr (1/2)
    expect16_at 0x084, 0xFF09    ;   (2/2)
    expect16_at 0x086, 0x2800    ; cmp r0, #0
    expect16_at 0x088, 0xDD02    ; ble #0x222cc0c
    expect16_at 0x08A, 0x2102    ; movs r1, #2
    expect16_at 0x08C, 0x4833    ; ldr r0, [pc, #0xcc]
    expect16_at 0x08E, 0xE001    ; b #0x222cc10
    expect16_at 0x090, 0x4832    ; ldr r0, [pc, #0xc8]
    expect16_at 0x092, 0x2103    ; movs r1, #3
    expect16_at 0x094, 0x7041    ; strb r1, [r0, #1]
    expect16_at 0x096, 0x6AA8    ; ldr r0, [r5, #0x28]
    expect16_at 0x098, 0x1C31    ; adds r1, r6, #0
    expect16_at 0x09A, 0x2200    ; movs r2, #0
    expect16_at 0x09C, 0xF001    ; bl Faint_HealthboxOut (1/2)
    expect16_at 0x09E, 0xF992    ;   (2/2)
    expect16_at 0x0A0, 0xE059    ; b #0x222ccd2
    expect16_at 0x0A2, 0x1C20    ; adds r0, r4, #0
    expect16_at 0x0A4, 0x2129    ; movs r1, #0x29
    expect16_at 0x0A6, 0xF5DB    ; bl Sprite_GetAttr (1/2)
    expect16_at 0x0A8, 0xFEF7    ;   (2/2)
    expect16_at 0x0AA, 0x1C05    ; adds r5, r0, #0
    expect16_at 0x0AC, 0x3D08    ; subs r5, #8
    expect16_at 0x0AE, 0xD500    ; bpl #0x222cc2e
    expect16_at 0x0B0, 0x2500    ; movs r5, #0
    expect16_at 0x0B2, 0x1C20    ; adds r0, r4, #0
    expect16_at 0x0B4, 0x2129    ; movs r1, #0x29
    expect16_at 0x0B6, 0x1C2A    ; adds r2, r5, #0
    expect16_at 0x0B8, 0xF5DB    ; bl Sprite_SetAttr (1/2)
    expect16_at 0x0BA, 0xFD84    ;   (2/2)
    expect16_at 0x0BC, 0x2D00    ; cmp r5, #0
    expect16_at 0x0BE, 0xD14A    ; bne #0x222ccd2
    expect16_at 0x0C0, 0x4826    ; ldr r0, [pc, #0x98]
    expect16_at 0x0C2, 0x2103    ; movs r1, #3
    expect16_at 0x0C4, 0x7041    ; strb r1, [r0, #1]
    expect16_at 0x0C6, 0x1C38    ; adds r0, r7, #0
    expect16_at 0x0C8, 0xF7EA    ; bl MonView_GetSpecies (1/2)
    expect16_at 0x0CA, 0xFFD0    ;   (2/2)
    expect16_at 0x0CC, 0x1C05    ; adds r5, r0, #0
    expect16_at 0x0CE, 0x1C38    ; adds r0, r7, #0
    expect16_at 0x0D0, 0xF7EA    ; bl MonView_GetForm (1/2)
    expect16_at 0x0D2, 0xFFC8    ;   (2/2)
    expect16_at 0x0D4, 0x1C06    ; adds r6, r0, #0
    expect16_at 0x0D6, 0x1C38    ; adds r0, r7, #0
    expect16_at 0x0D8, 0xF7EB    ; bl MonView_GetGender (1/2)
    expect16_at 0x0DA, 0xFAC8    ;   (2/2)
    expect16_at 0x0DC, 0x0600    ; lsls r0, r0, #0x18
    expect16_at 0x0DE, 0x0E01    ; lsrs r1, r0, #0x18
    expect16_at 0x0E0, 0x2000    ; movs r0, #0
    expect16_at 0x0E2, 0x9000    ; str r0, [sp]
    expect16_at 0x0E4, 0x9A01    ; ldr r2, [sp, #4]
    expect16_at 0x0E6, 0x1C28    ; adds r0, r5, #0
    expect16_at 0x0E8, 0x1C33    ; adds r3, r6, #0
    expect16_at 0x0EA, 0xF643    ; bl Mon_GetSpriteYOffset (1/2)
    expect16_at 0x0EC, 0xF829    ;   (2/2)
    expect16_at 0x0EE, 0x2350    ; movs r3, #0x50
    expect16_at 0x0F0, 0x1A18    ; subs r0, r3, r0
    expect16_at 0x0F2, 0x2100    ; movs r1, #0
    expect16_at 0x0F4, 0x9000    ; str r0, [sp]
    expect16_at 0x0F6, 0x1C20    ; adds r0, r4, #0
    expect16_at 0x0F8, 0x1C0A    ; adds r2, r1, #0
    expect16_at 0x0FA, 0xF5DC    ; bl Sprite_SetPartialDraw (1/2)
    expect16_at 0x0FC, 0xF9D7    ;   (2/2)
    expect16_at 0x0FE, 0x4817    ; ldr r0, [pc, #0x5c]
    expect16_at 0x100, 0x2104    ; movs r1, #4
    expect16_at 0x102, 0x7041    ; strb r1, [r0, #1]
    expect16_at 0x104, 0xE027    ; b #0x222ccd2
    expect16_at 0x106, 0x1C20    ; adds r0, r4, #0
    expect16_at 0x108, 0x2101    ; movs r1, #1
    expect16_at 0x10A, 0xF5DB    ; bl Sprite_GetAttr (1/2)
    expect16_at 0x10C, 0xFEC5    ;   (2/2)
    expect16_at 0x10E, 0x1C02    ; adds r2, r0, #0
    expect16_at 0x110, 0x1C20    ; adds r0, r4, #0
    expect16_at 0x112, 0x2101    ; movs r1, #1
    expect16_at 0x114, 0x3208    ; adds r2, #8
    expect16_at 0x116, 0xF5DB    ; bl Sprite_SetAttr (1/2)
    expect16_at 0x118, 0xFD55    ;   (2/2)
    expect16_at 0x11A, 0x1C20    ; adds r0, r4, #0
    expect16_at 0x11C, 0x2112    ; movs r1, #0x12
    expect16_at 0x11E, 0xF5DB    ; bl Sprite_GetAttr (1/2)
    expect16_at 0x120, 0xFEBB    ;   (2/2)
    expect16_at 0x122, 0x1C05    ; adds r5, r0, #0
    expect16_at 0x124, 0x3D08    ; subs r5, #8
    expect16_at 0x126, 0xD500    ; bpl #0x222cca6
    expect16_at 0x128, 0x2500    ; movs r5, #0
    expect16_at 0x12A, 0x1C20    ; adds r0, r4, #0
    expect16_at 0x12C, 0x2112    ; movs r1, #0x12
    expect16_at 0x12E, 0x1C2A    ; adds r2, r5, #0
    expect16_at 0x130, 0xF5DB    ; bl Sprite_SetAttr (1/2)
    expect16_at 0x132, 0xFD48    ;   (2/2)
    expect16_at 0x134, 0x2D00    ; cmp r5, #0
    expect16_at 0x136, 0xD10E    ; bne #0x222ccd2
    expect16_at 0x138, 0x1C20    ; adds r0, r4, #0
    expect16_at 0x13A, 0xF5DB    ; bl Sprite_Delete (1/2)
    expect16_at 0x13C, 0xFD31    ;   (2/2)
    expect16_at 0x13E, 0x4807    ; ldr r0, [pc, #0x1c]
    expect16_at 0x140, 0x2105    ; movs r1, #5
    expect16_at 0x142, 0x7041    ; strb r1, [r0, #1]
    expect16_at 0x144, 0xE007    ; b #0x222ccd2
    expect16_at 0x146, 0x7801    ; ldrb r1, [r0]
    expect16_at 0x148, 0x2900    ; cmp r1, #0
    expect16_at 0x14A, 0xD104    ; bne #0x222ccd2
    expect16_at 0x14C, 0x2100    ; movs r1, #0
    expect16_at 0x14E, 0x7041    ; strb r1, [r0, #1]
    expect16_at 0x150, 0xB003    ; add sp, #0xc
    expect16_at 0x152, 0x2001    ; movs r0, #1
    expect16_at 0x154, 0xBDF0    ; pop {r4, r5, r6, r7, pc}
    expect16_at 0x156, 0x2000    ; movs r0, #0
    expect16_at 0x158, 0xB003    ; add sp, #0xc
    expect16_at 0x15A, 0xBDF0    ; pop {r4, r5, r6, r7, pc}
    expect16_at 0x15C, 0x5EDC    ; data
    expect16_at 0x15E, 0x0225    ; data

    push    {r4-r7, lr}
    sub     sp, #0xC
    add     r5, r0, #0                      ; client
    ldr     r0, [r5, #0x28]
    add     r7, r1, #0                      ; battler (r1 is passed on unchanged)
    bl      Battle_GetSpriteSlot
    add     r6, r0, #0                      ; slot
    add     r0, r7, #0
    bl      Battler_FacingKind
    cmp     r0, #0
    beq     @@facing
    mov     r0, #2
@@facing:
    str     r0, [sp, #4]                    ; facing: 0 back (player's side), 2 front (foe)
    add     r0, r6, #0
    bl      BattleSprite_Get
    add     r4, r0, #0                      ; sprite
    ldr     r0, [r5, #0x28]
    add     r1, r7, #0
    bl      Battle_GetMonView
    add     r7, r0, #0                      ; MonView
    ldr     r0, =FaintState
    ldrb    r1, [r0, #1]                    ; state
    cmp     r1, #5
    bls     @@dispatch
    b       @@exit
@@dispatch:
    add     r1, r1, r1
    add     r1, pc
    ldrh    r1, [r1, #6]
    lsl     r1, r1, #16
    asr     r1, r1, #16
    add     pc, r1
@@table:
    .halfword @@state0 - @@table - 2
    .halfword @@state1 - @@table - 2
    .halfword @@state2 - @@table - 2
    .halfword @@state3 - @@table - 2
    .halfword @@state4 - @@table - 2
    .halfword @@state5 - @@table - 2

@@state0:                                   ; prepare; when ready: the faint cry (new), state 1
    add     r0, r5, #0
    add     r1, r6, #0
    mov     r2, #0
    mov     r3, #1
    bl      Faint_Prepare
    cmp     r0, #0
    beq     @@exit
    ldr     r2, [sp, #4]
    sub     r2, #1
    mov     r0, #FAINT_PAN
    mul     r2, r0                          ; pan: -117 back, +117 front
    ldrb    r0, [r7, #5]
    str     r0, [sp, #8]                    ; form
    mov     r0, #0
    str     r0, [sp, #4]                    ; delay 0
    ldrh    r1, [r7]                        ; species
    mov     r3, #CRY_VOLUME
    mov     r0, #HEAP_ID_BATTLE
    str     r0, [sp]                        ; heap
    mov     r0, #CRY_MODE_FAINT
    bl      Cry_Play
    mov     r1, #1
    b       @@set_state

@@state1:                                   ; wait for the cry; the faint sound (new); health box; state 2 or 3
    bl      Cry_IsPlaying
    cmp     r0, #0
    bne     @@exit
    ldr     r1, [sp, #4]
    sub     r1, #1
    mov     r0, #FAINT_PAN
    mul     r1, r0                          ; pan
    ldr     r0, =SEQ_SE_DP_POKE_DEAD3
    bl      PlaySEWithPan
    add     r0, r4, #0
    mov     r1, #ATTR_RAISE
    bl      Sprite_GetAttr
    mov     r1, #3
    cmp     r0, #0
    ble     @@state1_set
    mov     r1, #2                          ; raised: lower it first
@@state1_set:
    ldr     r0, =FaintState
    strb    r1, [r0, #1]
    ldr     r0, [r5, #0x28]
    add     r1, r6, #0
    mov     r2, #0
    bl      Faint_HealthboxOut
    b       @@exit

@@set_state:                                ; r1 = the next state
    ldr     r0, =FaintState
    strb    r1, [r0, #1]
@@exit:
    mov     r0, #0
    add     sp, #0xC
    pop     {r4-r7, pc}

@@state2:                                   ; lower a raised sprite 8 px a frame; then state 3 at once
    add     r0, r4, #0
    mov     r1, #ATTR_RAISE
    bl      Sprite_GetAttr
    add     r5, r0, #0
    sub     r5, #8
    bpl     @@state2_set
    mov     r5, #0
@@state2_set:
    add     r0, r4, #0
    mov     r1, #ATTR_RAISE
    add     r2, r5, #0
    bl      Sprite_SetAttr
    cmp     r5, #0
    bne     @@exit
    ldr     r0, =FaintState
    mov     r1, #3
    strb    r1, [r0, #1]

@@state3:                                   ; draw only the part above the ground line; state 4
    mov     r0, #0
    str     r0, [sp]
    mov     r1, #(MONVIEW_GENDER >> 2)
    lsl     r1, r1, #2
    add     r1, #(MONVIEW_GENDER & 3)
    ldrb    r1, [r7, r1]                    ; gender
    ldrb    r3, [r7, #5]                    ; form
    ldr     r2, [sp, #4]                    ; facing
    ldrh    r0, [r7]                        ; species
    bl      Mon_GetSpriteYOffset
    mov     r3, #0x50
    sub     r0, r3, r0
    mov     r1, #0
    str     r0, [sp]
    add     r0, r4, #0
    add     r2, r1, #0
    bl      Sprite_SetPartialDraw
    mov     r1, #4
    b       @@set_state

@@state4:                                   ; slide down 8 px a frame until hidden; state 5
    add     r0, r4, #0
    mov     r1, #ATTR_Y
    mov     r2, #8
    bl      Sprite_AddAttr
    add     r0, r4, #0
    mov     r1, #ATTR_HEIGHT
    bl      Sprite_GetAttr
    add     r5, r0, #0
    sub     r5, #8
    bpl     @@state4_set
    mov     r5, #0
@@state4_set:
    add     r0, r4, #0
    mov     r1, #ATTR_HEIGHT
    add     r2, r5, #0
    bl      Sprite_SetAttr
    cmp     r5, #0
    bne     @@exit
    add     r0, r4, #0
    bl      Sprite_Delete
    mov     r1, #5
    b       @@set_state

@@state5:                                   ; wait for the health box; reset the state, done
    ldrb    r1, [r0]                        ; r0 = FaintState (from the dispatch)
    cmp     r1, #0
    bne     @@exit
    mov     r1, #0
    strb    r1, [r0, #1]
    add     sp, #0xC
    mov     r0, #1
    pop     {r4-r7, pc}

.pool
.endarea

.close
