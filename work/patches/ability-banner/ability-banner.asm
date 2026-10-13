; ability-banner - Keep English ability pop-up names inside their window. D-2500 (pending).

.nds
.thumb
.include "../include/guards.inc"
.open "overlay14.bin", 0x022007E0
.org 0x0222670A
.area 2
 expect16 0x2284
 mov r2, #112 ; 120 pixels less 8 pixels of right padding
.endarea
.org 0x0222670C
.area 2
 expect16 0x3108
 add r1, #16 ; player-side banner begins partly offscreen
.endarea
.close
