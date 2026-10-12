; petilil-hisuian-lilligant - Petilil holding a Black Belt, levelling up by day, evolves into Hisuian Lilligant. D-2334.
; Why and what: fix.toml next to this file; overview work/patches/FIXES.md; work/notes/petilil-hisuian-lilligant_fix.md.
; The hack finding this answers: D-1485.
;
; The evolution scene's setup (0x02074048; r5 = the target species the evolution record names) decodes the hack's
; form-species ids (1025 and up, 'Hisuian Lilligant' 1361) into a base species and sets the form byte with
; SetMonData(mon, FORM, &1). Petilil's Black Belt record names 1361; the decoder returns 548 (Petilil)
; for it: 'movs r5, #0x89 ; lsls r5, r5, #2' = 548, one too low. Lilligant is 549 (Petilil's own Sun Stone record
; names 549), so the Pokemon 'evolved' into a form-1 Petilil and only a Sun Stone made it Hisuian Lilligant.
;
; 548 -> 549 needs one more instruction than the two the hack used, so the five halfwords are rebuilt without
; changing the length or the call: r1 (the FORM field number 0x70, which the call needs anyway) is also the
; base of the species, 0x70 * 4 + 0x65 = 549. Nothing else changes: the call (bl 0x0206DF70 at 0x02074152),
; its arguments (r0 = mon, r1 = 0x70, r2 = &form) and the branch that follows are the hack's.

.nds
.thumb
.include "../include/guards.inc"

.definelabel EvolutionSetup_Hisuian_Lilligant, 0x02074148   ; the case for the id 1361

.open "arm9.bin", 0x02000000

.org EvolutionSetup_Hisuian_Lilligant
.area 10
    expect16_at 0x00, 0x2589        ; movs  r5, #0x89
    expect16_at 0x02, 0x1C38        ; adds  r0, r7, #0
    expect16_at 0x04, 0x2170        ; movs  r1, #0x70
    expect16_at 0x06, 0xAA09        ; add   r2, sp, #0x24
    expect16_at 0x08, 0x00AD        ; lsls  r5, r5, #2
    ; 0x0A: bl 0x0206DF70 (SetMonData) and the 'b' after it stay
    add     r0, r7, #0              ; r0 = mon
    mov     r1, #0x70               ; r1 = FORM field
    add     r2, sp, #0x24           ; r2 = &form (1, set at 0x020740AE)
    lsl     r5, r1, #2              ; 0x70 * 4 = 448
    add     r5, #0x65               ; 448 + 101 = 549: Lilligant (the hack had 548: Petilil)
.endarea

.close
