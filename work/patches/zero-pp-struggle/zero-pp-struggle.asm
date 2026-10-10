; zero-pp-struggle - Restore exhausted-move Struggle actions. D-2300/D-2302 (D-1576).
.nds
.thumb
.include "../include/guards.inc"
.open "overlay14.bin", 0x022007E0
.org 0x02216538
    expect32_at 0x00, 0x28008BC0
    expect32_at 0x04, 0x2001D101
    expect32_at 0x08, 0x20004770
    expect32_at 0x0C, 0x00004770
.org 0x02217104
    expect32_at 0x00, 0x2207B418
    expect32_at 0x04, 0x0549400A
    expect32_at 0x08, 0x0E092301
    expect32_at 0x0C, 0x18411C1C
    expect32_at 0x10, 0x40944805
    expect32_at 0x14, 0x5C080622
    expect32_at 0x18, 0x42100E12
    expect32_at 0x1C, 0x2300D100
    expect32_at 0x20, 0xBC181C18
    expect32_at 0x24, 0x46C04770
    expect32_at 0x28, 0x000002BA
.org 0x02200960
    expect32_at 0x00, 0x2400B430
    expect32_at 0x04, 0x60446004
    expect32_at 0x08, 0x07124C0D
    expect32_at 0x0C, 0x7C24446C
    expect32_at 0x10, 0x0E120409
    expect32_at 0x14, 0x68056084
    expect32_at 0x18, 0x43A5240F
    expect32_at 0x1C, 0x43252401
    expect32_at 0x20, 0x43A524F0
    expect32_at 0x24, 0x43141C2C
    expect32_at 0x28, 0x0A094A06
    expect32_at 0x2C, 0x430A4022
    expect32_at 0x30, 0x400A4905
    expect32_at 0x34, 0x094907D9
    expect32_at 0x38, 0x60014311
    expect32_at 0x3C, 0x4770BC30
    expect32_at 0x40, 0xFFFFFFF8
    expect32_at 0x44, 0xFF0000FF
    expect32_at 0x48, 0xFBFFFFFF
.org 0x022167A0
    expect32_at 0x00, 0x47707D00
.org 0x02217B10
    expect32_at 0x00, 0x008921AB
    expect32_at 0x04, 0x47705840
.org 0x02216E34
    expect32_at 0x00, 0x5C404901
    expect32_at 0x04, 0x46C04770
    expect32_at 0x08, 0x0000029E
.org 0x02202F74
    expect32_at 0x00, 0x58604944
    expect32_at 0x04, 0x58611D09
    expect32_at 0x08, 0xFAE8F029
    expect32_at 0x0C, 0xD0042800
    expect32_at 0x10, 0x1C204941
    expect32_at 0x14, 0xF82AF7FF
    expect32_at 0x18, 0x2001E079
.org 0x0222C304
    expect32_at 0x00, 0xB08CB5F8
    expect32_at 0x04, 0x1C051C0C
    expect32_at 0x08, 0x92001C1E
    expect32_at 0x0C, 0xD1022CA5
    expect32_at 0x10, 0x2000B00C
    expect32_at 0x14, 0x1C20BDF8
; Native slot helpers guard the move/PP field offsets used by the scan.
.org 0x02216E60
    expect32_at 0x00, 0x434A2212
    expect32_at 0x04, 0x48011881
    expect32_at 0x08, 0x47705A08
    expect32_at 0x0C, 0x0000025A
.org 0x02216F14
    expect32_at 0x00, 0x434A2212
    expect32_at 0x04, 0x20971881
    expect32_at 0x08, 0x5C080080
    expect32_at 0x0C, 0x00004770
.org 0x0222C550
    expect32_at 0x00, 0xB085B5F0
    expect32_at 0x04, 0x1C0C1C05
    expect32_at 0x08, 0xFFEEF7E9
    expect32_at 0x0C, 0xD1052800
    expect32_at 0x10, 0x21041C28
    expect32_at 0x14, 0xFDCEF7EA
    expect32_at 0x18, 0xD0072800
    expect32_at 0x1C, 0xD0022C00
    expect32_at 0x20, 0xF7D41C20
    expect32_at 0x24, 0xB005F9D3
    expect32_at 0x28, 0xBDF02001
    expect32_at 0x2C, 0x21011C28
    expect32_at 0x30, 0xFDC0F7EA
    expect32_at 0x34, 0xD00E2800
    expect32_at 0x38, 0xD0092C00
    expect32_at 0x3C, 0xF7EA1C28
    expect32_at 0x40, 0x1C01F907
    expect32_at 0x44, 0x1C200609
    expect32_at 0x48, 0x22000E09
    expect32_at 0x4C, 0xF9C8F7D4
    expect32_at 0x50, 0x2001B005
    expect32_at 0x54, 0x1C28BDF0
    expect32_at 0x58, 0xF7EA211A
    expect32_at 0x5C, 0x2800FBBD
    expect32_at 0x60, 0xA801D023
    expect32_at 0x64, 0x221A1C29
    expect32_at 0x68, 0xFBC0F7EA
    expect32_at 0x6C, 0x98029901
    expect32_at 0x70, 0x9103AA03
    expect32_at 0x74, 0xCA039004
    expect32_at 0x78, 0xFBD2F7EA
    expect32_at 0x7C, 0x1C281C07
    expect32_at 0x80, 0xFA9EF7EB
    expect32_at 0x84, 0x1C281C06
    expect32_at 0x88, 0xF8E2F7EA
    expect32_at 0x8C, 0x0E000600
    expect32_at 0x90, 0xD0072C00
    expect32_at 0x94, 0x90000632
    expect32_at 0x98, 0x1C391C20
    expect32_at 0x9C, 0x23000E12
    expect32_at 0xA0, 0xF9B6F7D4
    expect32_at 0xA4, 0x2001B005
    expect32_at 0xA8, 0x1C28BDF0
    expect32_at 0xAC, 0xF7EA211B
    expect32_at 0xB0, 0x2800FB93
    expect32_at 0xB4, 0x1C28D019
    expect32_at 0xB8, 0xFCA4F7EA
    expect32_at 0xBC, 0x1C281C07
    expect32_at 0xC0, 0xFA7EF7EB
    expect32_at 0xC4, 0x1C281C06
    expect32_at 0xC8, 0xF8C2F7EA
    expect32_at 0xCC, 0x0E000600
    expect32_at 0xD0, 0xD0072C00
    expect32_at 0xD4, 0x90000632
    expect32_at 0xD8, 0x1C391C20
    expect32_at 0xDC, 0x23000E12
    expect32_at 0xE0, 0xF996F7D4
    expect32_at 0xE4, 0x2001B005
    expect32_at 0xE8, 0x2000BDF0
    expect32_at 0xEC, 0xBDF0B005
.area 0xF0, 0
    push {r4-r7, lr}
    sub sp, 0x14
    mov r5, r0
    mov r4, r1
    bl 0x02216538
    cmp r0, 0
    bne skip
    mov r0, r5
    mov r1, 4
    bl 0x02217104
    cmp r0, 0
    beq flag_one
skip:
    cmp r4, 0
    beq forced
    mov r0, r4
    bl 0x0220091C
    b forced
flag_one:
    mov r0, r5
    mov r1, 1
    bl 0x02217104
    cmp r0, 0
    beq stored_26
    cmp r4, 0
    beq forced
    mov r0, r5
    bl 0x022167A0
    mov r1, r0
    mov r0, r4
    mov r2, 0
    bl 0x02200930
    b forced
stored_26:
    mov r0, r5
    mov r1, 0x1A
    bl 0x02216D28
    cmp r0, 0
    beq stored_27
    add r0, sp, 4
    mov r1, r5
    mov r2, 0x1A
    bl 0x02216D3C
    add r2, sp, 4
    ldmia r2!, {r0,r1}
    bl 0x02216D70
    mov r7, r0
    b construct
stored_27:
    mov r0, r5
    mov r1, 0x1B
    bl 0x02216D28
    cmp r0, 0
    beq pp_scan
    mov r0, r5
    bl 0x02216F54
    mov r7, r0
    b construct
pp_scan:
    ; This guard also runs before command entry. Keep Bag/switch/run available:
    ; only the FIGHT handler may submit the new zero-PP fallback.
    ldr r0, [sp, 0x24]   ; saved caller LR (20-byte push + 20-byte locals)
    ldr r1, =0x02202F81
    cmp r0, r1
    bne ordinary
    ldr r6, =0x25A
    add r6, r5
    mov r7, 4
pp_next:
    ldrh r0, [r6]
    cmp r0, 0
    beq pp_advance
    ldrb r0, [r6, 2]
    cmp r0, 0
    bne ordinary
pp_advance:
    add r6, 0x12
    sub r7, 1
    bne pp_next
    mov r7, 165
construct:
    mov r0, r5
    bl 0x02217B10
    mov r6, r0
    mov r0, r5
    bl 0x022167A0
    str r0, [sp]
    cmp r4, 0
    beq forced
    mov r0, r4
    mov r1, r7
    lsl r2, r6, 24
    lsr r2, r2, 24
    mov r3, 0
    bl 0x02200960
forced:
    mov r0, 1
    b done
ordinary:
    mov r0, 0
done:
    add sp, 0x14
    pop {r4-r7, pc}
.pool
.endarea
.close
