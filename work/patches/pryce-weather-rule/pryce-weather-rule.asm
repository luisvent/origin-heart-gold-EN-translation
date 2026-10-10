; pryce-weather-rule - Pryce's Glacier Badge rule checks the party's Abilities, not 28 species. D-2320
; (user-approved exception to D-1337).
; Why and what: fix.toml next to this file; overview work/patches/FIXES.md; work/notes/pryce-weather-rule_fix.md.
;
; Pryce (Mahogany Gym, event-script file 928, message bank 613) tells the player: no Pokemon whose Ability
; changes the weather, Double Battle (msg 0, msg 14: 能够靠特性改变天气的精灵). His check (L269-L794) refuses
; the party when it holds any of 28 species (PlayerHasSpecies), whatever their Ability: a Charizard (Blaze,
; Solar Power, Tough Claws here) or a Probopass (Sturdy, Magnet Pull, Power Spot) is refused, which no
; Ability of theirs explains.
;
; The script engine has no command that reads a party Pokemon's Ability. MonGetContestValue (command 542,
; used by no script of the hack) reads GetMonData(party mon, 0x13 + type); without the '+ 0x13' it reads
; any GetMonData field. Part 1 removes that add (one instruction). Part 2 replaces the 28 species checks
; with a loop over the party: an egg is skipped (field 76), and a Pokemon whose current Ability (field 10,
; the hack's u16 at block B +0x1A) changes the weather sends the script to the refusal (L1083, msg 14).
; Everything else (the party-count check before it, the battle after it) is unchanged.

.nds
.include "../include/guards.inc"

; ------------------------------------------------------------------------------------------------ part 1: arm9
.thumb
.definelabel ScriptCmdTable,                0x020F793C   ; u32 handler (Thumb) per script command, 843 entries
.definelabel ScrCmd_MonGetContestValue,     0x0204CCC0   ; command 542 (slot, type, ret var)
.definelabel MonGetContestValue_Field,      0x0204CD0E   ; add r4, #0x13: field = 0x13 + type  <- the edit
.definelabel ScriptReadHalfword,            0x0203F534
.definelabel ScriptGetVar,                  0x0203FAE8   ; the value of a var, or the literal
.definelabel ScriptGetVarPointer,           0x0203FAB0
.definelabel SaveArray_Party_Get,           0x0207365C
.definelabel Party_GetMonByIndex,           0x0207339C
.definelabel GetMonData,                    0x0206D848   ; (mon, field, buf)
.definelabel BoxMonData_JumpTable,          0x0206D9FE   ; s16 case offsets (from 0x0206DA00) per field
.definelabel BoxMonData_Ability,            0x0206DC32   ; field 10: ldrh r4, [block B, #0x1A]
.definelabel BoxMonData_IsEgg,              0x0206DD00   ; field 76: the egg bit (bit 30 of block B +0x10)

.open "arm9.bin", 0x02000000

; Read-only: command 542 is this routine.
expect32_abs ScriptCmdTable + 4 * 542, ScrCmd_MonGetContestValue + 1

; Read-only: the routine (slot, type, ret: *ret = GetMonData(Party_GetMonByIndex(party, slot), 0x13 + type)).
.org ScrCmd_MonGetContestValue
    expect16_at 0x00, 0xB5F8    ; push  {r3-r7, lr}
    expect16_at 0x02, 0x1C05    ; add   r5, r0, #0              r5 = script context
    expect16_at 0x04, 0xF7F2    ; bl    ScriptReadHalfword      (1/2)
    expect16_at 0x06, 0xFC36    ;                               (2/2)
    expect16_at 0x08, 0x1C01    ; add   r1, r0, #0
    expect16_at 0x0A, 0x1C28    ; add   r0, r5, #0
    expect16_at 0x0C, 0x3080    ; add   r0, #0x80
    expect16_at 0x0E, 0x6800    ; ldr   r0, [r0]
    expect16_at 0x10, 0xF7F2    ; bl    ScriptGetVar            (1/2)
    expect16_at 0x12, 0xFF0A    ;                               (2/2)
    expect16_at 0x14, 0x1C07    ; add   r7, r0, #0              r7 = party slot
    expect16_at 0x16, 0x1C28    ; add   r0, r5, #0
    expect16_at 0x18, 0xF7F2    ; bl    ScriptReadHalfword      (1/2)
    expect16_at 0x1A, 0xFC2C    ;                               (2/2)
    expect16_at 0x1C, 0x1C01    ; add   r1, r0, #0
    expect16_at 0x1E, 0x1C28    ; add   r0, r5, #0
    expect16_at 0x20, 0x3080    ; add   r0, #0x80
    expect16_at 0x22, 0x6800    ; ldr   r0, [r0]
    expect16_at 0x24, 0xF7F2    ; bl    ScriptGetVar            (1/2)
    expect16_at 0x26, 0xFF00    ;                               (2/2)
    expect16_at 0x28, 0x1C04    ; add   r4, r0, #0              r4 = type (u16)
    expect16_at 0x2A, 0x1C28    ; add   r0, r5, #0
    expect16_at 0x2C, 0xF7F2    ; bl    ScriptReadHalfword      (1/2)
    expect16_at 0x2E, 0xFC22    ;                               (2/2)
    expect16_at 0x30, 0x1C01    ; add   r1, r0, #0
    expect16_at 0x32, 0x1C28    ; add   r0, r5, #0
    expect16_at 0x34, 0x3080    ; add   r0, #0x80
    expect16_at 0x36, 0x6800    ; ldr   r0, [r0]
    expect16_at 0x38, 0xF7F2    ; bl    ScriptGetVarPointer     (1/2)
    expect16_at 0x3A, 0xFEDA    ;                               (2/2)
    expect16_at 0x3C, 0x3580    ; add   r5, #0x80
    expect16_at 0x3E, 0x1C06    ; add   r6, r0, #0              r6 = ret var
    expect16_at 0x40, 0x6828    ; ldr   r0, [r5]
    expect16_at 0x42, 0x68C0    ; ldr   r0, [r0, #0xC]          save data
    expect16_at 0x44, 0xF026    ; bl    SaveArray_Party_Get     (1/2)
    expect16_at 0x46, 0xFCAA    ;                               (2/2)
    expect16_at 0x48, 0x1C39    ; add   r1, r7, #0
    expect16_at 0x4A, 0xF026    ; bl    Party_GetMonByIndex     (1/2)
    expect16_at 0x4C, 0xFB47    ;                               (2/2)
    expect16_at 0x50, 0x1C21    ; add   r1, r4, #0              field
    expect16_at 0x52, 0x2200    ; mov   r2, #0
    expect16_at 0x54, 0xF020    ; bl    GetMonData              (1/2)
    expect16_at 0x56, 0xFD98    ;                               (2/2)
    expect16_at 0x58, 0x8030    ; strh  r0, [r6]
    expect16_at 0x5A, 0x2000    ; mov   r0, #0
    expect16_at 0x5C, 0xBDF8    ; pop   {r3-r7, pc}

; Read-only: GetMonData field 10 is the Ability (u16, block B +0x1A), field 76 the egg bit.
.org BoxMonData_JumpTable + 2 * 10
    expect16 BoxMonData_Ability - 0x0206DA00
.org BoxMonData_JumpTable + 2 * 76
    expect16 BoxMonData_IsEgg - 0x0206DA00
.org BoxMonData_Ability
    expect16_at 0x00, 0x8B6C    ; ldrh  r4, [r5, #0x1A]         r5 = block B
.org BoxMonData_IsEgg
    expect16_at 0x0A, 0x6928    ; ldr   r0, [r5, #0x10]
    expect16_at 0x0C, 0x0040    ; lsl   r0, r0, #1
    expect16_at 0x0E, 0x0FC4    ; lsr   r4, r0, #31             bit 30

; The edit: the field is the script's value itself (MonGetContestValue becomes 'get GetMonData field').
.org MonGetContestValue_Field
.area 2
    expect16 0x3413             ; add   r4, #0x13
    nop                         ; (mov r8, r8)
.endarea

.close

; --------------------------------------------------------------------------------- part 2: event script 928
; Opened at 0: addresses are offsets in the script file, the L-numbers of work/tools/docs/scriptdump.py 928.
; Script commands: u16 command, then its arguments (work/tools/docs/script_cmds.json); vars 0x8000+.

CMD_COMPARE_VAR_VALUE   equ 17      ; CompareVarToValue var, u16 value
CMD_COMPARE_VAR_VAR     equ 18      ; CompareVarToVar var, var
CMD_GOTO                equ 22      ; GoTo s32 (from the end of the command)
CMD_GOTO_IF             equ 28      ; GoToIf u8 condition, s32
CMD_ADD_VAR             equ 39      ; AddVar var, value
CMD_SET_VAR             equ 41      ; SetVar var, value
CMD_NPC_MSG             equ 45      ; NPCMsg u8 message
CMD_TRAINER_BATTLE      equ 213
CMD_PLAYER_HAS_SPECIES  equ 389     ; PlayerHasSpecies ret var, species
CMD_MON_GET_DATA        equ 542     ; MonGetContestValue slot, field, ret var (part 1: field = GetMonData field)
COND_LT                 equ 0
COND_EQ                 equ 1
COND_NE                 equ 5

VAR_SLOT                equ 0x8004  ; loop counter (a scratch var; Pryce's script does not use it)
VAR_COUNT               equ 0x8005  ; party count: GetPartyCount 0x8005 at L252, just before the check
VAR_RESULT              equ 0x800C

MON_FIELD_ABILITY       equ 10
MON_FIELD_IS_EGG        equ 76

; Abilities that change the weather (bank 712 descriptions; work/notes/pryce-weather-rule_fix.md).
ABILITY_DRIZZLE         equ 2       ; 降雨: rain
ABILITY_SAND_STREAM     equ 45      ; 扬沙: sandstorm
ABILITY_DROUGHT         equ 70      ; 日照: sun
ABILITY_SNOW_WARNING    equ 117     ; 降雪: hail
ABILITY_PRIMORDIAL_SEA  equ 189     ; 始源之海: heavy rain
ABILITY_DESOLATE_LAND   equ 190     ; 终结之地: harsh sun
ABILITY_DELTA_STREAM    equ 191     ; 德尔塔气流: strong winds
ABILITY_SAND_SPIT       equ 245     ; 吐沙: sandstorm when hit
ABILITY_ORICHALCUM_PULSE equ 288    ; 绯红脉动: sun on entry
ABILITY_TERAFORM_ZERO   equ 309     ; 归零化境: erases weather and terrain
ABILITY_WILDFIRE        equ 313     ; 霹雳火: harsh sun (the hack's own)

.definelabel Pryce_PartyCount,  0x0FC   ; L252: GetPartyCount 0x8005; one Pokemon -> L1072
.definelabel Pryce_RuleCheck,   0x10D   ; L269: the 28 species checks                   <- the edit
.definelabel Pryce_Battle,      0x321   ; L801: TrainerBattle 32, 32 (Double Battle)
.definelabel Pryce_Refused,     0x43B   ; L1083: NPCMsg 14 (the rule; sort out your party)

.macro species_check_was, n, species        ; old check n: PlayerHasSpecies; != 0 -> Pryce_Refused
    expect16_at 19 * (n) + 0, CMD_PLAYER_HAS_SPECIES
    expect16_at 19 * (n) + 2, VAR_RESULT
    expect16_at 19 * (n) + 4, species
    expect16_at 19 * (n) + 6, CMD_COMPARE_VAR_VALUE
    expect16_at 19 * (n) + 12, CMD_GOTO_IF
    expect32_at 19 * (n) + 15, Pryce_Refused - (Pryce_RuleCheck + 19 * (n) + 19)
.endmacro

.macro SetVar, var, value
    .halfword CMD_SET_VAR, var, value
.endmacro
.macro AddVar, var, value
    .halfword CMD_ADD_VAR, var, value
.endmacro
.macro CompareVarToValue, var, value
    .halfword CMD_COMPARE_VAR_VALUE, var, value
.endmacro
.macro CompareVarToVar, var1, var2
    .halfword CMD_COMPARE_VAR_VAR, var1, var2
.endmacro
.macro MonGetData, slot, field, ret
    .halfword CMD_MON_GET_DATA, slot, field, ret
.endmacro
.macro GoToIf, cond, target
    .halfword CMD_GOTO_IF
    .byte cond
    .word (target) - (org() + 4)
.endmacro
.macro GoTo, target
    .halfword CMD_GOTO
    .word (target) - (org() + 4)
.endmacro
.macro RefuseIfAbility, ability
    CompareVarToValue VAR_RESULT, ability
    GoToIf COND_EQ, Pryce_Refused
.endmacro

.open "script928.bin", 0x00000000

; Read-only: the refusal and the battle the check leads to.
.org Pryce_Refused
    expect16_at 0, CMD_NPC_MSG
    expect16_at 2, 14 | (50 << 8)   ; message 14 (u8), then WaitButton (command 50)
.org Pryce_Battle
    expect16_at 0, CMD_TRAINER_BATTLE
    expect16_at 2, 32               ; Pryce (trainer 32)
    expect16_at 4, 32               ; twice: Double Battle

.org Pryce_RuleCheck
.area Pryce_Battle - Pryce_RuleCheck
    species_check_was 0, 6          ; Charizard
    species_check_was 1, 37         ; Vulpix
    species_check_was 2, 38         ; Ninetales
    species_check_was 3, 87         ; Dewgong
    species_check_was 4, 144        ; Articuno
    species_check_was 5, 186        ; Politoed
    species_check_was 6, 218        ; Slugma
    species_check_was 7, 219        ; Magcargo
    species_check_was 8, 230        ; Kingdra
    species_check_was 9, 244        ; Entei
    species_check_was 10, 248       ; Tyranitar
    species_check_was 11, 279       ; Pelipper
    species_check_was 12, 321       ; Wailord
    species_check_was 13, 324       ; Torkoal
    species_check_was 14, 369       ; Relicanth
    species_check_was 15, 382       ; Kyogre
    species_check_was 16, 383       ; Groudon
    species_check_was 17, 384       ; Rayquaza
    species_check_was 18, 449       ; Hippopotas
    species_check_was 19, 450       ; Hippowdon
    species_check_was 20, 459       ; Snover
    species_check_was 21, 460       ; Abomasnow
    species_check_was 22, 476       ; Probopass
    species_check_was 23, 478       ; Froslass
    species_check_was 24, 526       ; Gigalith
    species_check_was 25, 698       ; Amaura
    species_check_was 26, 699       ; Aurorus
    species_check_was 27, 873       ; Frosmoth
    ; the 28 checks fill the area exactly
    .if Pryce_RuleCheck + 19 * 28 != Pryce_Battle
        .error "the old species checks do not end at Pryce_Battle"
    .endif

    SetVar VAR_SLOT, 0
Pryce_NextMon:
    MonGetData VAR_SLOT, MON_FIELD_IS_EGG, VAR_RESULT
    CompareVarToValue VAR_RESULT, 1
    GoToIf COND_EQ, Pryce_NextSlot                      ; an egg changes no weather
    MonGetData VAR_SLOT, MON_FIELD_ABILITY, VAR_RESULT
    RefuseIfAbility ABILITY_DRIZZLE
    RefuseIfAbility ABILITY_SAND_STREAM
    RefuseIfAbility ABILITY_DROUGHT
    RefuseIfAbility ABILITY_SNOW_WARNING
    RefuseIfAbility ABILITY_PRIMORDIAL_SEA
    RefuseIfAbility ABILITY_DESOLATE_LAND
    RefuseIfAbility ABILITY_DELTA_STREAM
    RefuseIfAbility ABILITY_SAND_SPIT
    RefuseIfAbility ABILITY_ORICHALCUM_PULSE
    RefuseIfAbility ABILITY_TERAFORM_ZERO
    RefuseIfAbility ABILITY_WILDFIRE
Pryce_NextSlot:
    AddVar VAR_SLOT, 1
    CompareVarToVar VAR_SLOT, VAR_COUNT
    GoToIf COND_LT, Pryce_NextMon                   ; slots 0 .. count - 1
    GoTo Pryce_Battle
    .fill Pryce_Battle - org(), 0               ; the rest of the old checks: never reached
.endarea

.close
