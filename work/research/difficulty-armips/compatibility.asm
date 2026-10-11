; Current EN-only compatibility delta. Verify compatibility.json whole-file/source guards first.
.nds
.thumb
.macro dg_compat16, value
 .if readu16(outputname(),org()-headersize()) != value
  .error "difficulty compatibility guard failed at " + tohex(org(),8)
 .endif
.endmacro
.open "arm9.bin", 0x02000000
; startup title LSL r0,27
.org 0x20040b4
.area 2
 dg_compat16 0x0680
 .halfword 0x06C0
.endarea
; startup title LSR r0,31
.org 0x20040b6
.area 2
 dg_compat16 0x0F80
 .halfword 0x0FC0
.endarea
; title getter LSL r0,27
.org 0x202b202
.area 2
 dg_compat16 0x0680
 .halfword 0x06C0
.endarea
; title getter LSR r0,31
.org 0x202b204
.area 2
 dg_compat16 0x0F80
 .halfword 0x0FC0
.endarea
; title setter input bit0
.org 0x202b210
.area 2
 dg_compat16 0x0789
 .halfword 0x07C9
.endarea
; title setter clear bit4 only
.org 0x202b214
.area 2
 dg_compat16 0x2230
 .halfword 0x2210
.endarea
; title setter position bit4
.org 0x202b216
.area 2
 dg_compat16 0x0E89
 .halfword 0x0EC9
.endarea
.close
.open "overlay50.bin", 0x021E4980
; initial local title snapshot input bit0
.org 0x21e49f6
.area 2
 dg_compat16 0x0780
 .halfword 0x07C0
.endarea
; initial local title snapshot clear bit4 only
.org 0x21e49fa
.area 2
 dg_compat16 0x2130
 .halfword 0x2110
.endarea
; initial local title snapshot position bit4
.org 0x21e49fc
.area 2
 dg_compat16 0x0E80
 .halfword 0x0EC0
.endarea
; Apply local title snapshot clear bit4 only
.org 0x21e4ab8
.area 2
 dg_compat16 0x2230
 .halfword 0x2210
.endarea
; Apply local title snapshot input bit0
.org 0x21e4ac2
.area 2
 dg_compat16 0x0792
 .halfword 0x07D2
.endarea
; Apply local title snapshot position bit4
.org 0x21e4ac4
.area 2
 dg_compat16 0x0E92
 .halfword 0x0ED2
.endarea
; load native title row from local snapshot
.org 0x21e53b4
.area 2
 dg_compat16 0x0680
 .halfword 0x06C0
.endarea
; load native title row from local snapshot
.org 0x21e53b6
.area 2
 dg_compat16 0x0F82
 .halfword 0x0FC2
.endarea
; native Apply title extraction
.org 0x21e4b18
.area 2
 dg_compat16 0x0689
 .halfword 0x06C9
.endarea
; native Apply title extraction
.org 0x21e4b1a
.area 2
 dg_compat16 0x0F89
 .halfword 0x0FC9
.endarea
; native Cancel title extraction
.org 0x21e4b44
.area 2
 dg_compat16 0x0680
 .halfword 0x06C0
.endarea
; native Cancel title extraction
.org 0x21e4b46
.area 2
 dg_compat16 0x0F80
 .halfword 0x0FC0
.endarea
.close
.open "itcm.bin", 0x01FF8000
; print_task inlined fast mask
.org 0x1ff8766
.area 2
 dg_compat16 0x210C
 .halfword 0x2104
.endarea
; load_rows speed mask
.org 0x1ff8a1e
.area 2
 dg_compat16 0x210C
 .halfword 0x2104
.endarea
; commit_speed clear mask
.org 0x1ff8ac4
.area 2
 dg_compat16 0x230C
 .halfword 0x2304
.endarea
; exit_free inlined commit clear mask
.org 0x1ff8af8
.area 2
 dg_compat16 0x230C
 .halfword 0x2304
.endarea
; pass_end inlined fast mask
.org 0x1ff8c2e
.area 2
 dg_compat16 0x210C
 .halfword 0x2104
.endarea
.close
