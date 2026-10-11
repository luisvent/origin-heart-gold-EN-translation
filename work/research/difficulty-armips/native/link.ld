OUTPUT_FORMAT(elf32-littlearm)
OUTPUT_ARCH(arm)
ENTRY(dg_battle_begin)
SECTIONS {
 . = 0x023DC000;
 __resident_start = .;
 .text : { *(.text .text.*) }
 .rodata : { *(.rodata .rodata.*) }
 .data : { *(.data .data.*) }
 __initialized_end = .;
 . = ALIGN(4);
 __bss_start = .;
 .bss (NOLOAD) : { *(.bss .bss.*) *(COMMON) }
 . = ALIGN(4);
 __bss_end = .;
 __c_end = .;
 /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment) }
 ASSERT(__c_end <= 0x023E0000, "difficulty C exceeds 16KiB reservation")
}
