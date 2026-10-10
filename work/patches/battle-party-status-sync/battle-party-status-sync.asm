; battle-party-status-sync - In-battle party screen: status conditions cured or inflicted during the battle
; (Heal Bell, Aromatherapy, Refresh, Natural Cure, Flame Orb, ...) are shown as they are now. D-2317
; (user-approved exception to D-1337).
; Why and what: fix.toml next to this file; overview work/patches/FIXES.md; work/notes/heal-bell-status_fix.md.
;
; The hack's battle engine (overlay 14) keeps a battle Pokemon record (bpp) per party member, with its own
; status table (8-byte entries at bpp+0x40.., one per condition) and a pointer to the battle's copy of the
; party Pokemon at bpp+0x10 (BPP_GetSrcData, 0x022167B4). Battles change the record only: the copy gets the
; record's status at the end of the battle, from BPP_ReflectToPP (0x02218B28), which converts the record's
; condition (BPP_GetPokeSick, 0x02216C64: 0 none, 1 PAR, 2 SLP, 3 FRZ, 4 BRN, 5 PSN) to party status bits
; and calls SetMonData(copy, 0xA0 status, ...). The in-battle party screens are built from the copies: four
; loops (0x022027DC POKEMON button, 0x02202B78 Bag target, 0x0220405C forced switch, 0x02203DBC foe-fainted
; switch list) add BPP_GetSrcData(member) for each member to a new party. So these screens show each
; Pokemon's status from the start of the battle: a Pokemon cured on the bench by Heal Bell still shows
; PSN/PAR/BRN, one burned by a Flame Orb shows none.
;
; The fix: ReflectToPP's status block (0x02218B52-0x02218BA1) becomes a call to a new routine in the same
; bytes, BPP_SyncSickToPP(bpp): the same conversion and SetMonData, returning the copy. ReflectToPP's
; behaviour is unchanged. The four party-screen loops call BPP_SyncSickToPP instead of BPP_GetSrcData, so
; every member's copy carries its current status when the screen is built. Nothing else is written to the
; copy (HP, PP, item, form stay as they are), and the record is not touched.

.nds
.thumb
.include "../include/guards.inc"

.definelabel SetMonData,                0x0206DF70   ; arm9: SetMonData(mon, field, &value); 0xA0 = status
.definelabel Party_AddMon,              0x0207327C   ; arm9: Party_AddMon(party, mon)
.definelabel BtlParty_GetMember,        0x022151A0   ; (party, index) -> bpp
.definelabel BPP_GetSrcData,            0x022167B4   ; bpp -> [bpp+0x10], the battle's party Pokemon
.definelabel BPP_GetPokeSick,           0x02216C64   ; bpp -> 0 none, 1 PAR, 2 SLP, 3 FRZ, 4 BRN, 5 PSN
.definelabel BPP_ReflectToPP,           0x02218B28   ; bpp, flag: HP, exp, status, moves, form, item -> copy
.definelabel ReflectToPP_Status,        0x02218B52   ; its status block                    <- edit 1
.definelabel ReflectToPP_Moves,         0x02218BA2   ; the rest of ReflectToPP (moves, form, item)
.definelabel PartyList_Pokemon_Src,     0x022027E6   ; POKEMON button party screen: bl BPP_GetSrcData <- edit 2
.definelabel PartyList_2_Src,           0x02202B82   ; Bag: 'use on which Pokemon'          <- edits 3-5
.definelabel PartyList_3_Src,           0x02203DC6   ; 'Will you switch?' after the foe faints
.definelabel PartyList_4_Src,           0x02204066   ; forced switch after a faint

.open "overlay14.bin", 0x022007E0

; Read-only guards: the routines BPP_SyncSickToPP relies on.
.org BPP_GetSrcData
    expect16_at 0x00, 0x6900    ; ldr   r0, [r0, #0x10]
    expect16_at 0x02, 0x4770    ; bx    lr

.org BPP_GetPokeSick
    expect16_at 0x00, 0x303C    ; adds  r0, #0x3c
    expect16_at 0x02, 0x2201    ; movs  r2, #1
    expect16_at 0x04, 0x3008    ; adds  r0, #8
    expect16_at 0x06, 0x6801    ; ldr   r1, [r0]                 entry i: [bpp + 0x3C + 8*i]
    expect16_at 0x08, 0x0749    ; lsls  r1, r1, #0x1d
    expect16_at 0x0A, 0x0F49    ; lsrs  r1, r1, #0x1d
    expect16_at 0x0C, 0xD001    ; beq   next
    expect16_at 0x0E, 0x1C10    ; adds  r0, r2, #0               return i (1..5)
    expect16_at 0x10, 0x4770    ; bx    lr
    expect16_at 0x12, 0x1C52    ; adds  r2, r2, #1
    expect16_at 0x14, 0x3008    ; adds  r0, #8
    expect16_at 0x16, 0x2A06    ; cmp   r2, #6
    expect16_at 0x18, 0xDBF5    ; blt   loop
    expect16_at 0x1A, 0x2000    ; movs  r0, #0                   none
    expect16_at 0x1C, 0x4770    ; bx    lr

.org BPP_ReflectToPP
    expect16_at 0x00, 0xB538    ; push  {r3, r4, r5, lr}
    expect16_at 0x02, 0x1C04    ; add   r4, r0, #0               r4 = bpp
    expect16_at 0x04, 0x2092    ; mov   r0, #0x92
    expect16_at 0x06, 0x1C0D    ; add   r5, r1, #0               r5 = flag
    expect16_at 0x08, 0x0080    ; lsl   r0, r0, #2
    expect16_at 0x0A, 0x6921    ; ldr   r1, [r4, #0x10]
    expect16_at 0x0C, 0x1820    ; add   r0, r4, r0
    expect16_at 0x0E, 0xF7FF    ; bl    0x02218A44 (1/2)
    expect16_at 0x10, 0xFF85    ;                  (2/2)
    expect16_at 0x12, 0x1C22    ; add   r2, r4, #0
    expect16_at 0x14, 0x6920    ; ldr   r0, [r4, #0x10]
    expect16_at 0x16, 0x21A3    ; mov   r1, #0xa3                current HP
    expect16_at 0x18, 0x321E    ; add   r2, #0x1e
    expect16_at 0x1A, 0xF655    ; bl    SetMonData (1/2)
    expect16_at 0x1C, 0xFA15    ;                  (2/2)
    expect16_at 0x1E, 0x1C22    ; add   r2, r4, #0
    expect16_at 0x20, 0x6920    ; ldr   r0, [r4, #0x10]
    expect16_at 0x22, 0x2108    ; mov   r1, #8                   experience
    expect16_at 0x24, 0x3218    ; add   r2, #0x18
    expect16_at 0x26, 0xF655    ; bl    SetMonData (1/2)
    expect16_at 0x28, 0xFA0F    ;                  (2/2)         then the status block (edit 1)
.org ReflectToPP_Moves
    expect16_at 0x00, 0x1C20    ; add   r0, r4, #0
    expect16_at 0x02, 0xF7FF    ; bl    0x022189F4 (1/2)         moves and PP
    expect16_at 0x04, 0xFF26    ;                  (2/2)
    expect16_at 0x06, 0x1C20    ; add   r0, r4, #0
    expect16_at 0x08, 0xF7FD    ; bl    0x022169D4 (1/2)
    expect16_at 0x0A, 0xFF13    ;                  (2/2)
    expect16_at 0x0C, 0x2800    ; cmp   r0, #0
    expect16_at 0x0E, 0xD101    ; bne   0x02218BB6
    expect16_at 0x10, 0x2D00    ; cmp   r5, #0                   flag
    expect16_at 0x12, 0xD001    ; beq   0x02218BBA
    expect16_at 0x14, 0x7921    ; ldrb  r1, [r4, #4]             form
    expect16_at 0x16, 0xE000    ; b     0x02218BBC
    expect16_at 0x18, 0x7961    ; ldrb  r1, [r4, #5]
    expect16_at 0x1A, 0x6920    ; ldr   r0, [r4, #0x10]
    expect16_at 0x1C, 0xF659    ; bl    0x02072250 (1/2)
    expect16_at 0x1E, 0xFB47    ;                  (2/2)
    expect16_at 0x20, 0x6920    ; ldr   r0, [r4, #0x10]
    expect16_at 0x22, 0x3420    ; add   r4, #0x20
    expect16_at 0x24, 0x2106    ; mov   r1, #6                   held item
    expect16_at 0x26, 0x1C22    ; add   r2, r4, #0
    expect16_at 0x28, 0xF655    ; bl    SetMonData (1/2)
    expect16_at 0x2A, 0xF9D1    ;                  (2/2)
    expect16_at 0x2C, 0xBD38    ; pop   {r3, r4, r5, pc}         (the block's [sp] is not read again)

; Edit 1: ReflectToPP's status block -> a call to BPP_SyncSickToPP, which takes its place.
.org ReflectToPP_Status
.area ReflectToPP_Moves - ReflectToPP_Status
    expect16_at 0x00, 0x1C20    ; adds  r0, r4, #0
    expect16_at 0x02, 0xF7FE    ; bl    BPP_GetPokeSick (1/2)
    expect16_at 0x04, 0xF886    ;                       (2/2)
    expect16_at 0x06, 0x9000    ; str   r0, [sp]
    expect16_at 0x08, 0x8BE1    ; ldrh  r1, [r4, #0x1e]          current HP
    expect16_at 0x0A, 0x2900    ; cmp   r1, #0
    expect16_at 0x0C, 0xD019    ; beq   -> status 0
    expect16_at 0x0E, 0x2805    ; cmp   r0, #5
    expect16_at 0x10, 0xD819    ; bhi   -> status = condition
    expect16_at 0x12, 0x1800    ; adds  r0, r0, r0               switch (condition)
    expect16_at 0x14, 0x4478    ; add   r0, pc
    expect16_at 0x16, 0x88C0    ; ldrh  r0, [r0, #6]
    expect16_at 0x18, 0x0400    ; lsls  r0, r0, #0x10
    expect16_at 0x1A, 0x1400    ; asrs  r0, r0, #0x10
    expect16_at 0x1C, 0x4487    ; add   pc, r0
    expect16_at 0x1E, 0x0026    ; .hword: 0 none -> condition (0)
    expect16_at 0x20, 0x001C    ; .hword: 1 PAR  -> 0x40
    expect16_at 0x22, 0x0026    ; .hword: 2 SLP  -> condition (2)
    expect16_at 0x24, 0x0016    ; .hword: 3 FRZ  -> 0x20
    expect16_at 0x26, 0x0010    ; .hword: 4 BRN  -> 0x10
    expect16_at 0x28, 0x000A    ; .hword: 5 PSN  -> 0x08
    expect16_at 0x2A, 0x2008    ; movs  r0, #8
    expect16_at 0x2C, 0x9000    ; str   r0, [sp]
    expect16_at 0x2E, 0xE00A    ; b     store
    expect16_at 0x30, 0x2010    ; movs  r0, #0x10
    expect16_at 0x32, 0x9000    ; str   r0, [sp]
    expect16_at 0x34, 0xE007    ; b     store
    expect16_at 0x36, 0x2020    ; movs  r0, #0x20
    expect16_at 0x38, 0x9000    ; str   r0, [sp]
    expect16_at 0x3A, 0xE004    ; b     store
    expect16_at 0x3C, 0x2040    ; movs  r0, #0x40
    expect16_at 0x3E, 0x9000    ; str   r0, [sp]
    expect16_at 0x40, 0xE001    ; b     store
    expect16_at 0x42, 0x2000    ; movs  r0, #0                   fainted: no status
    expect16_at 0x44, 0x9000    ; str   r0, [sp]
    expect16_at 0x46, 0x6920    ; ldr   r0, [r4, #0x10]          store: the copy
    expect16_at 0x48, 0x21A0    ; movs  r1, #0xa0
    expect16_at 0x4A, 0xAA00    ; add   r2, sp, #0
    expect16_at 0x4C, 0xF655    ; bl    SetMonData (1/2)
    expect16_at 0x4E, 0xF9E7    ;                  (2/2)
    add     r0, r4, #0
    bl      BPP_SyncSickToPP
    b       ReflectToPP_Moves

; BPP_SyncSickToPP(r0 = bpp) -> r0 = the battle's party Pokemon (what BPP_GetSrcData returns), whose status
; is now the record's: the conversion ReflectToPP did inline (fainted -> 0; else SickToStatus). Keeps r4-r7.
BPP_SyncSickToPP:
    push    {r3, r4, r5, lr}
    add     r4, r0, #0
    bl      BPP_GetPokeSick         ; r0 = 0..5
    ldrh    r1, [r4, #0x1E]         ; current HP
    cmp     r1, #0
    beq     @@store                 ; fainted: status 0 (r1 = 0)
    add     r1, r15, #(SickToStatus - ((. + 4) & ~3))   ; adr r1, SickToStatus
    ldrb    r1, [r1, r0]
@@store:
    str     r1, [sp]                ; the pushed r3's slot
    ldr     r0, [r4, #0x10]         ; the battle's party Pokemon
    mov     r1, #0xA0               ; status
    add     r2, sp, #0
    bl      SetMonData
    ldr     r0, [r4, #0x10]
    pop     {r3, r4, r5, pc}
.align 4
SickToStatus:                       ; condition -> party status bits, as ReflectToPP's switch
    .byte   0x00                    ; 0 none
    .byte   0x40                    ; 1 PAR
    .byte   0x02                    ; 2 SLP (ReflectToPP stores the condition number, 2)
    .byte   0x20                    ; 3 FRZ
    .byte   0x10                    ; 4 BRN
    .byte   0x08                    ; 5 PSN
.align 2
    .fill   ReflectToPP_Moves - ., 0   ; the rest of the old block: no longer reached
.endarea

; Edits 2-5: the in-battle party screen loops take each member's party Pokemon through BPP_SyncSickToPP.
; Each loop: r0 = BtlParty_GetMember(party, i); bl <here>; add r1, r0, #0; ldr r0, [list]; bl Party_AddMon.
.macro party_list_src, addr, bl_hi, bl_lo, get_hi, get_lo, after
.org addr
    expect16_at -0x04, get_hi       ; bl    BtlParty_GetMember (1/2)
    expect16_at -0x02, get_lo       ;                          (2/2)
    expect16_at 0x04, 0x1C01        ; add   r1, r0, #0
    expect16_at 0x06, after         ; ldr   r0, [rN]          the new party
.area 4
    expect16_at 0x00, bl_hi         ; bl    BPP_GetSrcData (1/2)
    expect16_at 0x02, bl_lo         ;                      (2/2)
    bl      BPP_SyncSickToPP
.endarea
.endmacro

    party_list_src PartyList_Pokemon_Src, 0xF013, 0xFFE5, 0xF012, 0xFCDD, 0x6820
    party_list_src PartyList_2_Src,       0xF013, 0xFE17, 0xF012, 0xFB0F, 0x6830
    party_list_src PartyList_3_Src,       0xF012, 0xFCF5, 0xF011, 0xF9ED, 0x6838
    party_list_src PartyList_4_Src,       0xF012, 0xFBA5, 0xF011, 0xF89D, 0x6830

.close
