; All runtime instruction/literal writes are declared here, never Python opcodes.
; Generated c-symbols.inc contains final, odd ELF Thumb function addresses.
.nds
.include "c-symbols.inc"
.if (DG_RUNTIME_STUB_BASE & 3) != 0 || DG_RUNTIME_STUB_BASE < 0x023DC000 || DG_RUNTIME_STUB_BASE + 176 > 0x023E0000
 .error "runtime stub bounds"
.endif
.open "runtime-stubs.bin", DG_RUNTIME_STUB_BASE
.area 176, 0
DG_RuntimeStubsStart:
; Preserve all four C arguments. Interwork without a scratch register, then
; align the original word-aligned game stack for AAPCS C. No stacked arguments.
.macro adapter, name, target
 .thumb
 .align 4
 name:
 .if (target & 1) == 0
  .error "runtime C target is not Thumb"
 .endif
 bx pc
 nop
 .arm
 push {r4,lr}
 mov r4,sp
 bic sp,sp,#7
 ldr r12,=target
 blx r12
 mov sp,r4
 pop {r4,lr}
 bx lr
 .pool
.endmacro
; DG_Share is called from the per-recipient routine at BL 0x022289EA, where r4
; holds the recipient BattleMon. The original getter ignored its arguments, so
; the stub passes r4 as the C argument (the first ARM word, before r4 is saved).
.macro adapter_r4, name, target
 .thumb
 .align 4
 name:
 .if (target & 1) == 0
  .error "runtime C target is not Thumb"
 .endif
 bx pc
 nop
 .arm
 mov r0,r4
 push {r4,lr}
 mov r4,sp
 bic sp,sp,#7
 ldr r12,=target
 blx r12
 mov sp,r4
 pop {r4,lr}
 bx lr
 .pool
.endmacro
adapter DG_Begin, dg_battle_begin
adapter DG_Free, dg_battle_root_free
adapter_r4 DG_Share, dg_growth_share_enabled
adapter DG_Eligible, dg_growth_eligible
DG_RuntimeStubsCodeEnd:
.endarea
DG_RuntimeStubsEnd:
.close
.macro guard32, value
 .if readu32(outputname(),org()-headersize()) != value
  .error "runtime guard failed at " + tohex(org(),8)
 .endif
.endmacro
.thumb
.open "overlay14.bin", 0x022007E0
.org 0x02214CA2
.area 4
 guard32 0xF837F001
 bl DG_Begin
.endarea
.org 0x02214DA6
.area 4
 guard32 0xFAC9F606
 bl DG_Free
.endarea
.org 0x022289EA
.area 4
 guard32 0xFEE9F7EC
 bl DG_Share
.endarea
.org 0x0221F778
.area 4
 guard32 0xFFB8F7FF
 bl DG_Eligible
.endarea
.org 0x0221F83E
.area 4
 guard32 0xFF55F7FF
 bl DG_Eligible
.endarea
.close
.open "arm9.bin", 0x02000000
.org 0x020D1970
.area 4
 guard32 0x023E0000
 .word 0x023DC000
.endarea
.close
