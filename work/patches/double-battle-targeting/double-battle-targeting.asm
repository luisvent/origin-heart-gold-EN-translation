; double-battle-targeting - Escape the double-battle D-pad targeting trap. D-1337 exception.
; Option 2 approved in the isolated worktree on 2026-10-06; see fix.toml and
; work/notes/double_target_option2_plan.md. Original code, no Bradams patch bytes reused.
; Preserve native spread order; single targets prefer living foes, left first.
; Vertical navigation retries the other column only after the native search fails.
; Horizontal navigation tries the other Pokemon row only after an ineligible adjacent slot.
; This additional behavior was approved on 2026-10-09; historical Option 2 bytes are the port baseline.

.nds
.thumb
.include "../include/guards.inc"
.definelabel Target_Mask, 0x022126CC
.definelabel Target_Repair, 0x022129F0
.definelabel Target_Keep, 0x02212A34
.definelabel Target_Invalid, 0x02212A2A

.open "overlay14.bin", 0x022007E0

.org 0x02212784
.area 0xA4
    expect16_at 0x00, 0xB508
    expect16_at 0x02, 0xA900
    expect16_at 0x04, 0x2201
    expect16_at 0x06, 0xF7FF
    expect16_at 0x08, 0xFF9F
    expect16_at 0x0A, 0x2000
    expect16_at 0x0C, 0xAA00
    expect16_at 0x0E, 0x7811
    expect16_at 0x10, 0x2901
    expect16_at 0x12, 0xD004
    expect16_at 0x14, 0x1C40
    expect16_at 0x16, 0x1C52
    expect16_at 0x18, 0x2804
    expect16_at 0x1A, 0xDBF8
    expect16_at 0x1C, 0x2004
    expect16_at 0x1E, 0xBD08
    expect16_at 0x20, 0xB5F8
    expect16_at 0x22, 0xB082
    expect16_at 0x24, 0x1C06
    expect16_at 0x26, 0x481D
    expect16_at 0x28, 0x1C0F
    expect16_at 0x2A, 0x6841
    expect16_at 0x2C, 0x20FB
    expect16_at 0x2E, 0x0080
    expect16_at 0x30, 0x5808
    expect16_at 0x32, 0x9200
    expect16_at 0x34, 0x2400
    expect16_at 0x36, 0xA901
    expect16_at 0x38, 0x2201
    expect16_at 0x3A, 0x1C25
    expect16_at 0x3C, 0xF7FF
    expect16_at 0x3E, 0xFF84
    expect16_at 0x40, 0x1C20
    expect16_at 0x42, 0xE00D
    expect16_at 0x44, 0x4A16
    expect16_at 0x46, 0x0043
    expect16_at 0x48, 0x2100
    expect16_at 0x4A, 0x18D3
    expect16_at 0x4C, 0xE005
    expect16_at 0x4E, 0x5CCA
    expect16_at 0x50, 0x4296
    expect16_at 0x52, 0xD101
    expect16_at 0x54, 0x1C0C
    expect16_at 0x56, 0x1C05
    expect16_at 0x58, 0x1C49
    expect16_at 0x5A, 0x2902
    expect16_at 0x5C, 0xDBF7
    expect16_at 0x5E, 0x1C40
    expect16_at 0x60, 0x2803
    expect16_at 0x62, 0xDBEF
    expect16_at 0x64, 0x4A0E
    expect16_at 0x66, 0xA901
    expect16_at 0x68, 0x9800
    expect16_at 0x6A, 0x19E4
    expect16_at 0x6C, 0x182D
    expect16_at 0x6E, 0x2C00
    expect16_at 0x70, 0xDB05
    expect16_at 0x72, 0x2C02
    expect16_at 0x74, 0xDA03
    expect16_at 0x76, 0x2D00
    expect16_at 0x78, 0xDB01
    expect16_at 0x7A, 0x2D03
    expect16_at 0x7C, 0xDB02
    expect16_at 0x7E, 0xB002
    expect16_at 0x80, 0x1C30
    expect16_at 0x82, 0xBDF8
    expect16_at 0x84, 0x0068
    expect16_at 0x86, 0x1810
    expect16_at 0x88, 0x5C23
    expect16_at 0x8A, 0x2B04
    expect16_at 0x8C, 0xD002
    expect16_at 0x8E, 0x5CC8
    expect16_at 0x90, 0x2801
    expect16_at 0x92, 0xD1E9
    expect16_at 0x94, 0x1C18
    expect16_at 0x96, 0xB002
    expect16_at 0x98, 0xBDF8
    expect16_at 0x9A, 0x46C0
    expect16_at 0x9C, 0x5B90
    expect16_at 0x9E, 0x0225
    expect16_at 0xA0, 0xCD44
    expect16_at 0xA2, 0x0224
first_eligible:            ; 0x02212784: native order 0,1,2,3 (spread callers + repair spread branch)
    mov r1, #0xE4
    b scan_first0
first_eligible_foe:        ; order 3,1,0,2 (vanilla): repair single-target fallback (BL at 0x02212A2C)
    mov r1, #0x87
scan_first0:  push {r2-r4, lr}       ; r2's slot = 4-byte eligibility buffer
    add r4, r1, #0
    mov r1, sp
    mov r2, #1
    bl Target_Mask
scan_first1:  mov r0, #3
    and r0, r4
    mov r1, sp
    ldrb r1, [r1, r0]
    cmp r1, #1
    beq scan_first2
    lsr r4, r4, #2        ; next 2-bit slot; order list ends when no bits are left
    bne scan_first1
    mov r0, #4
scan_first2:  pop {r2-r4, pc}

; entry into target selection: keep a remembered opposing target (1/3), otherwise invalidate it so the
; native repair picks the first eligible target (foe first). Tail-calls the native repair; r0 = obj.
entry_repair:
    ldr r1, =0x02255B90
    ldr r2, [r1, #0x14]
    lsr r2, r2, #1        ; odd slots: 1/3 are foes; other odd values fail native unsigned repair
    bcs @@entry1          ; no stored target is modified by this test
    mov r2, #5
    str r2, [r1, #0x14]
@@entry1:
    b Target_Repair

; navigation: r0 = current slot, r1 = dx, r2 = dy -> new slot. Grid 2 cols x 3 rows at 0x0224CD44.
; Native straight-line search (skip ineligible slots, cancel always accepted, leaving the grid keeps the
; current slot). Vertical failure retries from the same row in the other column. An ineligible horizontal
; neighbor retries from the other Pokemon row in the same direction. CANCEL and outward edges stay native.
nav:
    push {r3-r7, lr}       ; r3's stack slot is the 4-byte eligibility buffer
    add r6, r0, #0
    add r7, r1, #0
    lsl r5, r2, #1        ; row stride (dy * 2); signed wrap is checked by unsigned grid bounds
    ldr r0, =0x02255B90
    ldr r0, [r0, #4]
    mov r1, #0xfb
    lsl r1, r1, #2
    ldr r0, [r0, r1]
    mov r1, sp
    mov r2, #1
    bl Target_Mask
    ldr r3, =0x0224CD44
    mov r4, #5            ; grid index of the current slot (last match, as native; none -> 0)
@@nav1:  ldrb r0, [r3, r4]
    cmp r0, r6
    beq @@nav2
    sub r4, #1
    bne @@nav1
@@nav2:  add r2, r4, #0        ; r2 = start index (bit 3 set once the other column was tried)
@@nav3:  mov r0, #1
    and r0, r4
    add r0, r0, r7        ; new column
    cmp r0, #1
    bhi @@nav8
    add r4, r4, r7
    add r4, r4, r5        ; new grid index after dx and the row stride
    cmp r4, #5
    bhi @@nav8
    ldrb r0, [r3, r4]
    cmp r0, #4             ; cancel is always accepted
    beq @@nav9
    mov r1, sp
    ldrb r1, [r1, r0]
    cmp r1, #1
    beq @@nav9
    cmp r7, #0
    beq @@nav3            ; vertical: continue the original straight-line search
    mov r0, #2           ; horizontal: retry from the other Pokemon row
    b @@retry
@@nav8:  cmp r7, #0             ; left the grid: outward horizontal -> stay (native)
    bne @@nav7
    mov r0, #1           ; vertical: retry from the other column
@@retry: cmp r2, #8             ; only one retry, for either direction
    bhs @@nav7
    eor r2, r0
    add r4, r2, #0        ; restart before applying the same direction
    mov r2, #8
    b @@nav3
@@nav7:  add r0, r6, #0
@@nav9:  pop {r3-r7, pc}

.align 4
.pool
.endarea

; Redirect navigation to the vertical column retry and horizontal Pokemon-row retry.
.org 0x02212880
.area 4
    expect16_at 0x00, 0xF7FF
    expect16_at 0x02, 0xFF90
    bl nav
.endarea

; Redirect navigation to the vertical column retry and horizontal Pokemon-row retry.
.org 0x02212896
.area 4
    expect16_at 0x00, 0xF7FF
    expect16_at 0x02, 0xFF85
    bl nav
.endarea

; Redirect navigation to the vertical column retry and horizontal Pokemon-row retry.
.org 0x022128AE
.area 4
    expect16_at 0x00, 0xF7FF
    expect16_at 0x02, 0xFF79
    bl nav
.endarea

; Redirect navigation to the vertical column retry and horizontal Pokemon-row retry.
.org 0x022128C4
.area 4
    expect16_at 0x00, 0xF7FF
    expect16_at 0x02, 0xFF6E
    bl nav
.endarea

; Target-screen entry keeps a remembered foe (1/3), otherwise resets to a living foe, left first.
.org 0x02212596
.area 4
    expect16_at 0x00, 0xF000
    expect16_at 0x02, 0xFA2B
    bl entry_repair
.endarea

; Single-target repair uses foe-first order; every spread caller retains native order 0,1,2,3.
.org 0x02212A2C
.area 4
    expect16_at 0x00, 0xF7FF
    expect16_at 0x02, 0xFEAA
    bl first_eligible_foe
.endarea

; Keep CANCEL (4) during per-frame single-target repair; unsigned comparison rejects invalid values.
.org 0x02212A1A
.area 8
    expect16_at 0x00, 0x2C00
    expect16_at 0x02, 0xDB05
    expect16_at 0x04, 0x2C04
    expect16_at 0x06, 0xDA03
    cmp r4, #4
    beq Target_Keep
    bhi Target_Invalid
    nop
.endarea

.close
