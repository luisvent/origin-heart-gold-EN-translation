; cute-charm-infatuation - Battle: Cute Charm infatuates the attacker again ('fell in love!' no longer prints
; without effect). D-2315 (user-approved exception to D-1337).
; Why and what: fix.toml next to this file; overview work/patches/FIXES.md; work/notes/cute-charm-infatuation_fix.md.
;
; Overlay 14 is the hack's battle engine. A condition ("sick") is stored per battle record in 8-byte entries
; at bpp+0x38+n*8; infatuation is condition 7 (bpp+0x70). Each entry carries a continuation word whose low
; 3 bits are its kind (0 none, 1 turns, 2 permanent, 3 linked to a Pokemon, ...); kind 0 is no condition.
;
; Cute Charm (ability 56) has one handler, CuteCharm_OnHit (0x02232A70, event 0xBB, after a hit): the holder
; is the target, the attacker is read from event var 0xA, both must have a gender and differ; then it builds
; the continuation and hands it, with condition 7, to TouchAddSick (0x0223ACDC: contact, Shield Dust, the
; chance 0x32 = 50 %, then the add-condition action with message 1#444 'fell in love'). It builds the
; continuation with SickCont_MakePokeSick (0x02225520), the constructor for the five status conditions
; 0..5 (sleep gets its turn count there): any other condition falls to its default case, kind 0. So the
; action prints 'fell in love!' and stores an empty entry: the attacker is never infatuated, no per-turn
; line, and the next contact prints the line again.
;
; Attract and Destiny Knot use SickCont_MakeLinked (0x022251D0, r1 = r2 = the Pokemon to be in love with:
; kind 3, Pokemon id in bits 3..8; 0x022255FA, 0x0220AF06). The fix calls it the same way with the holder's
; id (r5): two instructions, 'movs r1, #7' -> 'adds r1, r5, #0' and the bl target. Everything around them,
; and the 50 % chance, stay as they are. The guards below check the whole handler.

.nds
.thumb
.include "../include/guards.inc"

.definelabel CuteCharm_OnHit,          0x02232A70   ; ability 56 handler (r1 = holder's Pokemon id)
.definelabel CuteCharm_MakeCont,       0x02232ACE   ; movs r1, #7; adds r2, r5, #0; bl ...MakePokeSick <- edit
.definelabel SickCont_MakePokeSick,    0x02225520   ; (out, condition 0..5, Pokemon id); other conditions: kind 0
.definelabel SickCont_MakeLinked,      0x022251D0   ; (out, Pokemon id, Pokemon id): kind 3, linked to that Pokemon
.definelabel TouchAddSick,             0x0223ACDC   ; (holder, condition, cont lo, cont hi, [sp] chance %)
.definelabel EventVar_Get,             0x0220FCC0
.definelabel Battle_GetPoke,           0x022151BC   ; Pokemon id -> battle record
.definelabel Bpp_GetSex,               0x022181E8   ; [bpp+0x239]: 0 male, 1 female, 2 none
.definelabel Battle_SkipCheck,         0x0222383C   ; not identified; nonzero: no effect

.open "overlay14.bin", 0x022007E0

; Read-only guards: the handler around the edit (nothing is written here).
.org CuteCharm_OnHit
    expect16_at 0x00, 0xB5F0    ; push  {r4-r7, lr}
    expect16_at 0x02, 0xB085    ; sub   sp, #0x14
    expect16_at 0x04, 0x200B    ; mov   r0, #0xB                 target (defender)
    expect16_at 0x06, 0x1C0D    ; add   r5, r1, #0               r5 = holder
    expect16_at 0x08, 0xF7DD    ; bl    EventVar_Get  (1/2)
    expect16_at 0x0A, 0xF922    ;                     (2/2)
    expect16_at 0x0C, 0x4285    ; cmp   r5, r0
    expect16_at 0x0E, 0xD136    ; bne   return
    expect16_at 0x10, 0x2037    ; mov   r0, #0x37
    expect16_at 0x12, 0xF7DD    ; bl    EventVar_Get  (1/2)
    expect16_at 0x14, 0xF91D    ;                     (2/2)
    expect16_at 0x16, 0x2800    ; cmp   r0, #0
    expect16_at 0x18, 0xD131    ; bne   return
    expect16_at 0x1A, 0xF7F0    ; bl    Battle_SkipCheck (1/2)
    expect16_at 0x1C, 0xFED7    ;                     (2/2)
    expect16_at 0x1E, 0x2800    ; cmp   r0, #0
    expect16_at 0x20, 0xD12D    ; bne   return
    expect16_at 0x22, 0x200A    ; mov   r0, #0xA                 attacker
    expect16_at 0x24, 0xF7DD    ; bl    EventVar_Get  (1/2)
    expect16_at 0x26, 0xF914    ;                     (2/2)
    expect16_at 0x28, 0x0600    ; lsl   r0, r0, #0x18
    expect16_at 0x2A, 0x0E04    ; lsr   r4, r0, #0x18            r4 = attacker
    expect16_at 0x2C, 0x1C28    ; add   r0, r5, #0
    expect16_at 0x2E, 0xF7E2    ; bl    Battle_GetPoke (1/2)
    expect16_at 0x30, 0xFB8D    ;                     (2/2)
    expect16_at 0x32, 0x1C06    ; add   r6, r0, #0
    expect16_at 0x34, 0x1C20    ; add   r0, r4, #0
    expect16_at 0x36, 0xF7E2    ; bl    Battle_GetPoke (1/2)
    expect16_at 0x38, 0xFB89    ;                     (2/2)
    expect16_at 0x3A, 0x1C07    ; add   r7, r0, #0
    expect16_at 0x3C, 0x1C30    ; add   r0, r6, #0
    expect16_at 0x3E, 0xF7E5    ; bl    Bpp_GetSex    (1/2)
    expect16_at 0x40, 0xFB9B    ;                     (2/2)
    expect16_at 0x42, 0x0600    ; lsl   r0, r0, #0x18
    expect16_at 0x44, 0x0E04    ; lsr   r4, r0, #0x18            r4 = holder's gender
    expect16_at 0x46, 0x1C38    ; add   r0, r7, #0
    expect16_at 0x48, 0xF7E5    ; bl    Bpp_GetSex    (1/2)
    expect16_at 0x4A, 0xFB96    ;                     (2/2)
    expect16_at 0x4C, 0x0600    ; lsl   r0, r0, #0x18
    expect16_at 0x4E, 0x0E00    ; lsr   r0, r0, #0x18            r0 = attacker's gender
    expect16_at 0x50, 0x2C02    ; cmp   r4, #2
    expect16_at 0x52, 0xD014    ; beq   return                   holder genderless
    expect16_at 0x54, 0x2802    ; cmp   r0, #2
    expect16_at 0x56, 0xD012    ; beq   return                   attacker genderless
    expect16_at 0x58, 0x4284    ; cmp   r4, r0
    expect16_at 0x5A, 0xD010    ; beq   return                   same gender
    expect16_at 0x5C, 0xA801    ; add   r0, sp, #4               out = the continuation
    ; 0x5E..0x65: the edit below
    expect16_at 0x66, 0x9802    ; ldr   r0, [sp, #8]
    expect16_at 0x68, 0x9901    ; ldr   r1, [sp, #4]
    expect16_at 0x6A, 0x9004    ; str   r0, [sp, #0x10]
    expect16_at 0x6C, 0x2032    ; mov   r0, #0x32                chance 50 % (kept)
    expect16_at 0x6E, 0x9103    ; str   r1, [sp, #0xC]
    expect16_at 0x70, 0xAC03    ; add   r4, sp, #0xC
    expect16_at 0x72, 0x9000    ; str   r0, [sp]
    expect16_at 0x74, 0x1C28    ; add   r0, r5, #0               holder
    expect16_at 0x76, 0x2107    ; mov   r1, #7                   condition 7: infatuation
    expect16_at 0x78, 0xCC0C    ; ldmia r4!, {r2, r3}            the continuation
    expect16_at 0x7A, 0xF008    ; bl    TouchAddSick  (1/2)
    expect16_at 0x7C, 0xF8F7    ;                     (2/2)
    expect16_at 0x7E, 0xB005    ; add   sp, #0x14                return
    expect16_at 0x80, 0xBDF0    ; pop   {r4-r7, pc}

; The edit: the continuation is 'linked to the Cute Charm holder' (kind 3, holder's id), as for Attract.
.org CuteCharm_MakeCont
.area 8
    expect16_at 0, 0x2107       ; movs  r1, #7                   condition 7 for the status constructor
    expect16_at 2, 0x1C2A       ; adds  r2, r5, #0
    expect16_at 4, 0xF7F2       ; bl    SickCont_MakePokeSick (1/2)
    expect16_at 6, 0xFD25       ;                             (2/2)
    add     r1, r5, #0          ; r1 = holder's id
    add     r2, r5, #0          ; r2 = holder's id (unchanged)
    bl      SickCont_MakeLinked
.endarea

.close
