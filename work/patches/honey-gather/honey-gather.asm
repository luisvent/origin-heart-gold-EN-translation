; honey-gather - Restore direct-to-Bag Honey Gather. D-2324/D-2325/D-2326.
.nds
.thumb
.include "../include/guards.inc"
.open "overlay14.bin", 0x022007E0
.org 0x022167B4
    expect32_at 0x00, 0x47706900
.org 0x02217BF8
    expect32_at 0x00, 0x47708AC0
.org 0x02218104
    expect32_at 0x00, 0x78003024
    expect32_at 0x04, 0x00004770
.org 0x0221679C
    expect32_at 0x00, 0x47708C00
.org 0x02216154
    expect32_at 0x00, 0x21061C28
    expect32_at 0x04, 0xF6572200
    expect32_at 0x08, 0x8420FB75
.org 0x0222BCC8
    expect32_at 0x00, 0xB085B5F0
    expect32_at 0x04, 0x91019000
    expect32_at 0x08, 0x90042000
    expect32_at 0x0C, 0x1C174837
    expect32_at 0x10, 0x69016800
    expect32_at 0x14, 0x00809801
    expect32_at 0x18, 0x68401808
    expect32_at 0x1C, 0x98049003
    expect32_at 0x20, 0x98039002
    expect32_at 0x24, 0xFB54F647
    expect32_at 0x28, 0xDD5C2800
    expect32_at 0x2C, 0x98009A02
    expect32_at 0x30, 0x99010612
    expect32_at 0x34, 0xF0040E12
    expect32_at 0x38, 0x1C06FE0F
    expect32_at 0x3C, 0xFF70F7EB
    expect32_at 0x40, 0xF7EB1C30
    expect32_at 0x44, 0x1C04FF75
    expect32_at 0x48, 0x80382000
    expect32_at 0x4C, 0xF7EA1C30
    expect32_at 0x50, 0x214CFD4D
    expect32_at 0x54, 0xF6412200
    expect32_at 0x58, 0x2800FD93
    expect32_at 0x5C, 0x2C35D139
    expect32_at 0x60, 0x200AD137
    expect32_at 0x64, 0xFBC8F7FA
    expect32_at 0x68, 0xD0322800
    expect32_at 0x6C, 0x24002064
    expect32_at 0x70, 0xFB98F7FA
    expect32_at 0x74, 0x1C301C05
    expect32_at 0x78, 0xF9E0F7EC
    expect32_at 0x7C, 0x210A1E40
    expect32_at 0x80, 0xEA66F6C5
    expect32_at 0x84, 0x0E030600
    expect32_at 0x88, 0xD3002B0A
    expect32_at 0x8C, 0x48182309
    expect32_at 0x90, 0x21004A18
    expect32_at 0x94, 0x781818C3
    expect32_at 0x98, 0x18208816
    expect32_at 0x9C, 0x0E040600
    expect32_at 0xA0, 0xDD1142AC
    expect32_at 0xA4, 0x22014811
    expect32_at 0xA8, 0x23056800
    expect32_at 0xAC, 0x20426901
    expect32_at 0xB0, 0x58080080
    expect32_at 0xB4, 0xF64A1C31
    expect32_at 0xB8, 0x803EFE43
    expect32_at 0xBC, 0x1C409804
    expect32_at 0xC0, 0x0E000600
    expect32_at 0xC4, 0xE0049004
    expect32_at 0xC8, 0x1C921C49
    expect32_at 0xCC, 0x2916330A
    expect32_at 0xD0, 0x9802D3E1
    expect32_at 0xD4, 0x1C401CBF
    expect32_at 0xD8, 0x98039002
    expect32_at 0xDC, 0xFAF8F647
    expect32_at 0xE0, 0x42819902
    expect32_at 0xE4, 0x9804DBA2
    expect32_at 0xE8, 0xBDF0B005
    expect32_at 0xEC, 0x02255BAC
    expect32_at 0xF0, 0x0224E3D8
    expect32_at 0xF4, 0x0224E3AC
.area 0xF8, 0
    push {r4-r7, lr}
    sub sp, 0x14
    str r0, [sp, 0]
    str r1, [sp, 4]
    mov r6, r2
    mov r5, 0
    mov r7, 0
    ldr r0, =0x02255BAC
    ldr r0, [r0]
    ldr r0, [r0, 0x10]
    lsl r1, r1, 2
    add r0, r0, r1
    ldr r0, [r0, 4]
    str r0, [sp, 8]
    b check_slot
next_slot:
    add r5, 1
    add r6, 2
check_slot:
    ldr r0, [sp, 8]
    bl 0x02073398
    cmp r5, r0
    bge done
    ldr r0, [sp, 0]
    ldr r1, [sp, 4]
    mov r2, r5
    bl 0x02230920
    mov r4, r0
    mov r0, 0
    strh r0, [r6]
    ldr r0, [r4, 0x10]
    mov r1, 0x4C
    mov r2, 0
    bl 0x0206D848
    cmp r0, 0
    bne next_slot
    ldrh r0, [r4, 0x16]
    cmp r0, 53
    beq pickup
    cmp r0, 118
    bne next_slot
    ldrh r0, [r4, 0x20]
    cmp r0, 0
    bne next_slot
    bl level_band
    add r0, 1
    lsl r1, r0, 2
    add r0, r0, r1
    bl 0x022264C0
    cmp r0, 0
    beq next_slot
    mov r4, 94
    b award
pickup:
    mov r0, 10
    bl 0x022264C0
    cmp r0, 0
    beq next_slot
    mov r0, 100
    bl 0x0222646C
    str r0, [sp, 12]
    bl level_band
    ldr r1, =0x0224E3D8
    add r1, r1, r0
    ldr r2, =0x0224E3AC
    mov r3, 22
    ldr r0, [sp, 12]
select_item:
    ldrb r4, [r1]
    cmp r0, r4
    blo selected
    sub r0, r0, r4
    add r1, 10
    add r2, 2
    sub r3, 1
    bne select_item
    b next_slot
selected:
    ldrh r4, [r2]
award:
    ldr r0, =0x02255BAC
    ldr r0, [r0]
    ldr r1, [r0, 0x10]
    mov r0, 0x42
    lsl r0, r0, 2
    ldr r0, [r1, r0]
    mov r1, r4
    mov r2, 1
    mov r3, 5
    bl 0x02076A08
    cmp r0, 0
    beq next_slot
    strh r4, [r6]
    add r7, 1
    b next_slot
done:
    mov r0, r7
    add sp, 0x14
    pop {r4-r7, pc}
level_band:
    push {r3, lr}
    mov r0, 0x24
    ldrb r0, [r4, r0]
    sub r0, 1
    mov r1, 10
    blx 0x020F1218
    cmp r0, 9
    bls band_done
    mov r0, 9
band_done:
    pop {r3, pc}
.pool
.endarea
.close
