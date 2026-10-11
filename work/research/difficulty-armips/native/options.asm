; Copy unchanged into a fresh staging directory with c-symbols.inc and binaries.
; Enforce options_hooks.json + compatibility.json hashes BEFORE this assembly.
; C labels in c-symbols.inc retain ELF Thumb bit. No guessed C addresses.
; Invoke from repo root: armips ABSOLUTE_ASM -root ABSOLUTE_STAGE
; Supply -definelabel DG_OPTIONS_STUB_BASE ALIGNED_BASE for .open parsing.
.nds
.thumb
.include "c-symbols.inc"
.macro dg_hook32, value
 .if readu32(outputname(),org()-headersize()) != value
  .error "difficulty Options guard failed at " + tohex(org(),8)
 .endif
.endmacro
.open "options-stubs.bin", DG_OPTIONS_STUB_BASE
.if filesize(outputname()) != 72
 .error "Options stub file must have exactly 72 bytes"
.endif
.if (DG_OPTIONS_STUB_BASE & 3) != 0 || DG_OPTIONS_STUB_BASE < 0x02000000 || DG_OPTIONS_STUB_BASE + 72 > 0x023E0000
 .error "Options stub alignment/main RAM bounds"
.endif
.org DG_OPTIONS_STUB_BASE
.area 72
DG_OptionsStubsStart:
.align 4
DG_Stub_dg_menu_field_getter:
 .if (dg_menu_field_getter & 1) == 0
  .error "C target must retain ELF Thumb bit"
 .endif
 ldr r3, =dg_menu_field_getter
 bx r3
.pool
.align 4
DG_Stub_dg_menu_launch:
 .if (dg_menu_launch & 1) == 0
  .error "C target must retain ELF Thumb bit"
 .endif
 ldr r3, =dg_menu_launch
 bx r3
.pool
.align 4
DG_Stub_dg_menu_init:
 .if (dg_menu_init & 1) == 0
  .error "C target must retain ELF Thumb bit"
 .endif
 ldr r3, =dg_menu_init
 bx r3
.pool
.align 4
DG_Stub_dg_menu_exit:
 .if (dg_menu_exit & 1) == 0
  .error "C target must retain ELF Thumb bit"
 .endif
 ldr r3, =dg_menu_exit
 bx r3
.pool
.align 4
DG_Stub_dg_menu_load_rows:
 .if (dg_menu_load_rows & 1) == 0
  .error "C target must retain ELF Thumb bit"
 .endif
 ldr r3, =dg_menu_load_rows
 bx r3
.pool
.align 4
DG_Stub_dg_menu_draw:
 .if (dg_menu_draw & 1) == 0
  .error "C target must retain ELF Thumb bit"
 .endif
 ldr r3, =dg_menu_draw
 bx r3
.pool
.align 4
DG_Stub_dg_menu_cursor_plane:
 .if (dg_menu_cursor_plane & 1) == 0
  .error "C target must retain ELF Thumb bit"
 .endif
 ldr r3, =dg_menu_cursor_plane
 bx r3
.pool
.align 4
DG_Stub_dg_menu_input:
 .if (dg_menu_input & 1) == 0
  .error "C target must retain ELF Thumb bit"
 .endif
 ldr r3, =dg_menu_input
 bx r3
.pool
.align 4
DG_Stub_dg_menu_exit_animation:
 .if (dg_menu_exit_animation & 1) == 0
  .error "C target must retain ELF Thumb bit"
 .endif
 ldr r3, =dg_menu_exit_animation
 bx r3
.pool
DG_OptionsStubsEnd:
.endarea
.close
.open "arm9.bin", 0x02000000
; r0=SaveData; returns original Options pointer
.org 0x203e544
.area 4
 dg_hook32 0xFF00F7EA
 bl DG_Stub_dg_menu_field_getter
.endarea
; r0=FieldSystem,r1=Args; native dispatcher
.org 0x203e556
.area 4
 dg_hook32 0xFFE3F7FF
 bl DG_Stub_dg_menu_launch
.endarea
; r0=manager,r1=step; returns native completion
.org 0x20f6f78
.area 4
 dg_hook32 0x021E4981
 .word DG_Stub_dg_menu_init + 1
.endarea
; r0=manager,r1=step; custom skips ALL native setters and preview restores
.org 0x20f6f80
.area 4
 dg_hook32 0x021E4A69
 .word DG_Stub_dg_menu_exit + 1
.endarea
.close
.open "overlay50.bin", 0x021E4980
; r0=state; normal tail calls existing TEXT SPEED loader
.org 0x21e4d7c
.area 4
 dg_hook32 0xFE46F613
 bl DG_Stub_dg_menu_load_rows
.endarea
; r0=state; custom replaces entire normal draw/preview pass
.org 0x21e4d88
.area 4
 dg_hook32 0xFA42F000
 bl DG_Stub_dg_menu_draw
.endarea
; r0=BG index,r1=enabled; hide native BG0 outline/sprites only for custom
.org 0x21e4db4
.area 4
 dg_hook32 0xFB50F637
 bl DG_Stub_dg_menu_cursor_plane
.endarea
; r0=state; replace native input dispatch only in custom
.org 0x21e4c00
.area 4
 dg_hook32 0xFDC4F000
 bl DG_Stub_dg_menu_input
.endarea
; r0=state; no hidden footer animation wait in custom
.org 0x21e4c20
.area 4
 dg_hook32 0xFFAAF000
 bl DG_Stub_dg_menu_exit_animation
.endarea
.close
