; Standalone armips 0.11.0 stubs. Invoke from repo root with -root STAGE.
; Supply ITEM_STUB_BASE and all six dg_bag_* odd ELF function symbols using
; -definelabel. No C-to-stub callbacks, fixed payload addresses or Python opcodes.
; Optional -definelabel DG_ITEMS_PATCH_HOOKS 1 patches staged overlay9/14.bin.
; Installer MUST validate full current input/dependency hashes before that mode.
.nds
.if (ITEM_STUB_BASE & 3) != 0 || ITEM_STUB_BASE < 0x02000000 || ITEM_STUB_BASE + 0x150 > 0x023E0000
 .error "item stub alignment/main RAM bounds"
.endif
.if (dg_bag_item_attr & dg_bag_remembered & dg_bag_accept & dg_bag_commit_item & dg_bag_commit_target & dg_bag_effect_attr & 1) == 0
 .error "item C symbols must retain ELF Thumb bit"
.endif
.create "item_stubs.bin", ITEM_STUB_BASE
.area 0x150, 0
DG_ItemStubsStart:
.thumb
.align 4
DG_ItemList:
 bx pc
 nop
.arm
 push {r4,lr}
 mov r3,r4
 mov r4,sp
 bic sp,sp,#7
 ldr r12,=dg_bag_item_attr
 blx r12
 mov sp,r4
 pop {r4,lr}
 bx lr
.pool
.thumb
.align 4
DG_ItemRemembered:
 bx pc
 nop
.arm
 push {r4,lr}
 mov r12,r4
 mov r4,sp
 bic sp,sp,#7
 sub sp,sp,#8
 str r12,[sp] ; fifth AAPCS argument: original UI r4
 ldr r12,=dg_bag_remembered
 blx r12
 mov sp,r4
 pop {r4,lr}
 bx lr
.pool
.thumb
.align 4
DG_ItemAccept:
 bx pc
 nop
.arm
 push {r4,lr}
 mov r4,sp
 bic sp,sp,#7
 ldr r12,=dg_bag_accept
 blx r12
 mov sp,r4
 pop {r4,lr}
 bx lr
.pool
.thumb
.align 4
DG_ItemCommitBag:
 bx pc
 nop
.arm
 push {r0-r12,lr}
 mov r4,sp
 bic sp,sp,#7
 mov r0,r1
 ldr r12,=dg_bag_commit_item
 blx r12
 str r0,[r4,#28] ; displaced output r7
 mov sp,r4
 pop {r0-r12,lr}
 ; State3/5 have no preceding call in this invocation. Their native LR is
 ; saved at entry-SP+0x2C by 02202954 push{r4-r7,lr}; sub sp,0x1C.
 ; Hook BL's LR is only a continuation, not the pre-hook native LR.
 ldr lr,[sp,#0x2C]
 cmp r7,#0
 ldr pc,=0x02202ADD ; ARMv5 LDR-to-PC interworks, preserves all registers/NZCV
.pool
.thumb
.align 4
DG_ItemCommitTarget:
 bx pc
 nop
.arm
 push {r0-r12,lr}
 mov r4,sp
 bic sp,sp,#7
 ldr r0,[r4,#16] ; original controller r4
 mov r1,r2
 ldr r12,=dg_bag_commit_target
 blx r12
 str r0,[r4,#4] ; displaced output r1
 mov sp,r4
 pop {r0-r12,lr}
 ldr lr,[sp,#0x2C]
 cmp r1,#6
 ldr pc,=0x02202BF5
.pool
.thumb
.align 4
DG_ItemEffectAttr:
 bx pc
 nop
.arm
 push {r4,lr}
 mov r4,sp
 ; Original 022217C8 frame: actor at old-SP+8, target at old-SP+20h.
 ; Saved r4/LR add8. Forward original r0-r2; fifth arg goes on aligned SP.
 ldr r3,[r4,#0x10]
 ldr r12,[r4,#0x28]
 bic sp,sp,#7
 sub sp,sp,#8
 str r12,[sp]
 ldr r12,=dg_bag_effect_attr
 blx r12
 mov sp,r4
 pop {r4,lr}
 bx lr
.pool
DG_ItemStubsCodeEnd:
.endarea
DG_ItemStubsEnd:
.close

.macro dg_item_guard, expected
 .if readu32(outputname(),org()-headersize()) != expected
  .error "item hook guard failed at " + tohex(org(),8)
 .endif
.endmacro
.ifdef DG_ITEMS_PATCH_HOOKS
.if DG_ITEMS_PATCH_HOOKS != 1
 .error "DG_ITEMS_PATCH_HOOKS must be 1 or omitted"
.endif
.thumb
.open "overlay9.bin", 0x021E4DA0
.org 0x021EC308
.area 4
 dg_item_guard 0xF882F68A
 bl DG_ItemList
.endarea
.org 0x021EC266
.area 4
 dg_item_guard 0xFC5BF68A
 bl DG_ItemRemembered
.endarea
.org 0x021EB264
.area 4
 dg_item_guard 0xF818F000
 bl DG_ItemAccept
.endarea
.org 0x021EB6B8
.area 4
 dg_item_guard 0xFDEEF7FF
 bl DG_ItemAccept
.endarea
.close
.open "overlay14.bin", 0x022007E0
; Narrow lookup adapter: final attr38 callback only; global getter unchanged.
; Full effect-loop frame/order/table dependencies are installer-pinned.
.org 0x022218C0
.area 4
 dg_item_guard 0xFDA6F654
 bl DG_ItemEffectAttr
.endarea
; Stack-frame dependency of BOTH instruction replacements. Installer also
; verifies dispatch-to-state3/5 paths have no intervening BL (see handoff).
.org 0x02202954
 dg_item_guard 0xB087B5F0
.org 0x02202AD8
.area 4
 dg_item_guard 0x2F008B0F
 bl DG_ItemCommitBag
.endarea
.org 0x02202BF0
.area 4
 dg_item_guard 0x29067B51
 bl DG_ItemCommitTarget
.endarea
.close
.endif
