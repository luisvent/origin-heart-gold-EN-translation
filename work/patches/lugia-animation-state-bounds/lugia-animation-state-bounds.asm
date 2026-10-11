; lugia-animation-state-bounds - Lugia cutscene callback bounds. D-2298 (finding D-2297).
; See fix.toml and work/notes/lugia_freeze_fix_20261009.md for evidence and limits.
.nds
.thumb
.include "../include/guards.inc"
.open "overlay1.bin", 0x021E4980

; Read-only guards: dispatcher, both callbacks, and the two-entry table.
.org 0x021F80C0
    expect32_at 0x00, 0x1C05B5F8
    expect32_at 0x04, 0xFA60F666
    expect32_at 0x08, 0x1C281C07
    expect32_at 0x0C, 0xF001683C
    expect32_at 0x10, 0x2801F923
    expect32_at 0x14, 0x2C00D018
    expect32_at 0x18, 0x1C28D016
    expect32_at 0x1C, 0xF9E6F666
    expect32_at 0x20, 0x009E1C03
    expect32_at 0x24, 0x1C284B09
    expect32_at 0x28, 0x1C21599B
    expect32_at 0x2C, 0x47981C3A
    expect32_at 0x30, 0xF6661C28
    expect32_at 0x34, 0x6138F9DB
    expect32_at 0x38, 0x1C211C28
    expect32_at 0x3C, 0xF996F001
    expect32_at 0x40, 0x1C211C28
    expect32_at 0x44, 0xF872F000
    expect32_at 0x48, 0x46C0BDF8
    expect32_at 0x4C, 0x02208F70
.org 0x021F819C
    expect32_at 0x00, 0x6910B510
    expect32_at 0x04, 0x28001C0C
    expect32_at 0x08, 0x1C20D007
    expect32_at 0x0C, 0xF62C2100
    expect32_at 0x10, 0x1C20F9AD
    expect32_at 0x14, 0xF62C2100
    expect32_at 0x18, 0x2101F9D9
    expect32_at 0x1C, 0x03091C20
    expect32_at 0x20, 0xF9B6F62C
    expect32_at 0x24, 0x0000BD10
    expect32_at 0x28, 0x6910B510
    expect32_at 0x2C, 0x28011C0C
    expect32_at 0x30, 0x1C20D007
    expect32_at 0x34, 0xF62C2101
    expect32_at 0x38, 0x1C20F999
    expect32_at 0x3C, 0xF62C2100
    expect32_at 0x40, 0x2101F9C5
    expect32_at 0x44, 0x03091C20
    expect32_at 0x48, 0xF9A2F62C
    expect32_at 0x4C, 0x0000BD10
.org 0x02208F70
    expect32_at 0x00, 0x021F819D
    expect32_at 0x04, 0x021F81C5

.org 0x021F80E0
.area 0x18
    expect32 0x009E1C03
    cmp r0, 1
    bhi 0x021F80F8         ; unsupported state: retain frame/cache, still update position/visibility
    lsl r6, r0, 2
    ldr r3, [pc, 0x24]     ; original literal at 0x021F810C -> callback table 0x02208F70
    ldr r3, [r3, r6]
    mov r0, r5            ; unchanged callback arguments: map object, graphics, private data
    mov r1, r4
    mov r2, r7
    blx r3
    lsr r0, r6, 2         ; callbacks preserve r6 and do not change object animation state
    str r0, [r7, 0x10]    ; same cached state for valid input, no cache write for invalid input
    nop
.endarea
.close
