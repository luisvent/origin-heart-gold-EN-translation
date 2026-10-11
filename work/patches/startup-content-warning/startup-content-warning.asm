; startup-content-warning - First-page warning and no QQ display. D-2327, D-2328, D-2329
.nds
.thumb
.include "../include/guards.inc"
.open "overlay49.bin", 0x021E4980

; Keep the lower-screen background loaded for normal cleanup, but hidden.
; BG4 is the QR background; BG5 is the separate caption window.
.org 0x021E71B6
.area 2
    expect16 0x2101
    mov r1, #0
.endarea

; Page counter remains 0..4, so timing and final-page detection are unchanged.
.org 0x021E733A
.area 4
    expect16_at 0, 0xF624
    expect16_at 2, 0xFBE7
    bl NoticeMessage
.endarea

; Reuse the now-unreachable QR caption renderer prologue, without overlay growth.
.org 0x021E7434
.area 0x18
    expect16_at 0x00, 0xB510
    expect16_at 0x02, 0xB084
    expect16_at 0x04, 0x1C04
    expect16_at 0x06, 0x302C
    expect16_at 0x08, 0x2100
    expect16_at 0x0A, 0xF636
    expect16_at 0x0C, 0xFEB3
    expect16_at 0x0E, 0x1C20
    expect16_at 0x10, 0x302C
    expect16_at 0x12, 0xF636
    expect16_at 0x14, 0xFD0D
    expect16_at 0x16, 0x68A0
NoticeMessage:
    push {r3, lr}
    cmp r1, #0
    bne @@original
    mov r1, #4
    b @@read
@@original:
    sub r1, #1
@@read:
    bl 0x0200BB0C
    pop {r3, pc}
    .fill 0x021E744C - ., 0
.endarea

; Do not read/draw the QQ caption, including on the first warning page.
.org 0x021E77C2
.area 4
    expect16_at 0, 0xF7FF
    expect16_at 2, 0xFE37
    nop
    nop
.endarea
.close
