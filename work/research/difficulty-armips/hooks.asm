; difficulty-armips - Research: recovered difficulty resident hook migration. D-1575
; Research only: historical hook sites, not approved for the current ROM.
.nds
.include "../include/guards.inc"
.open "arm9.bin", 0x02000000
.arm
.org 0x02000908
.area 4
    expect32 0xEB03C495
    bl 0x023DF000
.endarea
.org 0x020D1970
.area 4
    expect32 0x023E0000
    .word 0x023DF000
.endarea
.thumb
.org 0x0203E544
.area 4
    expect32 0xFF00F7EA
    bl 0x023DF200
.endarea
.close
