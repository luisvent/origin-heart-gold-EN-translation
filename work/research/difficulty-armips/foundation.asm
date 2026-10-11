; Research only: recovered resident bootstrap and getter wrapper, armips v0.11.0.
; BRIDGE_DISPATCH must be supplied by a reviewed native payload linker.
; This creates an isolated binary; it does not install an ARM9 autoload section.
.nds
.create "foundation.bin", 0x023DF000
.arm
.area 0x100, 0
Resident_Bootstrap:
    stmdb sp!, {r0-r3,r12,lr}
    mrs r0, cpsr
    stmdb sp!, {r0,r1}
    ldr r0, [pc, #(Resident_StatePointer - . - 8)]
    mov r1, #0
    str r1, [r0, #4]
    str r1, [r0, #8]
    ldr r1, [pc, #(Resident_Magic - . - 8)]
    str r1, [r0]
    ldmia sp!, {r0,r1}
    msr cpsr_f, r0
    ldmia sp!, {r0-r3,r12,lr}
    b 0x020F1B64
Resident_StatePointer:
    .word 0x023DF100
Resident_Magic:
    .word 0x44524631
.endarea
; Historical layout: state at +0x100; code starts at +0x200.
.area 0x100, 0
.endarea
.thumb
Bridge_Prefix:
    mov r1, #1
    ldr r3, [pc, #4]
    bx r3
    nop
Bridge_WrapperPointer:
    .word Bridge_Wrapper
    .align 16, 0
.arm
Bridge_Wrapper:
    ; No stack write before SYS mode, alignment and the 512-byte budget checks.
    mrs r1, cpsr
    and r3, r1, #31
    cmp r3, #31
    bne Bridge_Bypass
    tst sp, #3
    bne Bridge_Bypass
    ldr r3, =0x027E0284
    cmp sp, r3
    blo Bridge_Bypass
    ldr r3, =0x027E377C
    cmp sp, r3
    bhi Bridge_Bypass
    msr cpsr_f, r1
    mov r1, #1
    stmdb sp!, {r0-r12,lr}
    mrs r1, cpsr
    mov r2, sp
    bic sp, sp, #7
    stmdb sp!, {r1,r2}
    mov r0, r2
    ldr r3, =BRIDGE_DISPATCH
    blx r3
    ldmia sp!, {r1,r2}
    mov sp, r2
    msr cpsr_f, r1
    ldmia sp!, {r0-r12,lr}
    ldr r3, =0x02027741
    bx r3
Bridge_Bypass:
    msr cpsr_f, r1
    mov r1, #1
    ldr r3, =0x02027741
    bx r3
    .pool
    .align 16, 0
Foundation_End:
.if Foundation_End > 0x023DFE00
    .error "resident foundation reaches the report reservation"
.endif
.close
