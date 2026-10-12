"""Limited interpreter for actual adapter instructions. NOT native ARM proof."""
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB
from capstone.arm import ARM_OP_IMM
from candidate_tools import assembled


def check_adapters():
    stage,_,_,_,_,_,_,report=assembled()
    span=next(s for s in report['stub_spans'] if s['file']=='runtime-stubs.bin')
    code=(stage/span['file']).read_bytes();base=span['start']
    arm=Cs(CS_ARCH_ARM,CS_MODE_ARM);arm.detail=True
    thumb=Cs(CS_ARCH_ARM,CS_MODE_THUMB);thumb.detail=True
    aliases={'sb':9,'sl':10,'fp':11,'ip':12,'sp':13,'lr':14,'pc':15}
    pairs=[('dg_begin','dg_battle_begin'),('dg_free','dg_battle_root_free'),
           ('dg_share','dg_growth_share_enabled'),('dg_eligible','dg_growth_eligible')]
    cases=0
    for stub,target in pairs:
        for align in (0,4):
            for output in (0,1,7,0x80000000,0xFFFFFFFF):
                regs=[0x02010000+i*0x100 for i in range(16)];regs[13]=0x027E3600+align;regs[14]=0x02210001
                initial=regs[:];mem={};pc=report['asm_symbols'][stub];t=True;calls=0
                def read(address):
                    if base<=address<=base+len(code)-4:return struct.unpack_from('<I',code,address-base)[0]
                    return mem[address]
                for _ in range(40):
                    if pc==(initial[14]&~1):break
                    assert base<=pc<base+len(code)
                    ins=next((thumb if t else arm).disasm(code[pc-base:pc-base+4],pc));ops=ins.operands
                    def rn(reg):
                        name=ins.reg_name(reg);return aliases[name] if name in aliases else int(name[1:])
                    def value(op):
                        if op.type==ARM_OP_IMM:return op.imm
                        r=rn(op.reg);return pc+(4 if t else 8) if r==15 else regs[r]
                    nextpc=pc+ins.size;m=ins.mnemonic
                    if m in ('push','pop'):
                        rr=[rn(op.reg) for op in ops];start=regs[13]-4*len(rr) if m=='push' else regs[13]
                        for i,r in enumerate(rr):
                            if m=='push':mem[start+4*i]=regs[r]
                            else:regs[r]=read(start+4*i)
                        regs[13]=start if m=='push' else start+4*len(rr)
                    elif m=='mov':regs[rn(ops[0].reg)]=value(ops[1])
                    elif m=='bic':regs[rn(ops[0].reg)]=value(ops[1])&~value(ops[2])
                    elif m=='ldr':
                        assert rn(ops[1].mem.base)==15
                        regs[rn(ops[0].reg)]=read(pc+8+ops[1].mem.disp)
                    elif m=='bx':v=value(ops[0]);t=bool(v&1);nextpc=v&~1
                    elif m=='blx':
                        assert value(ops[0])==report['elf_labels'][target]
                        # DG_Share passes the caller's r4 (the recipient BattleMon) as C argument 0.
                        want=[initial[4]]+initial[1:4] if stub=='dg_share' else initial[:4]
                        assert regs[13]%8==0 and regs[:4]==want
                        calls+=1
                        for r in (0,1,2,3,12,14):regs[r]=0xBAD00000+r
                        regs[0]=output
                    elif m=='nop':pass
                    else:raise AssertionError((m,ins.op_str))
                    pc=nextpc
                else:raise AssertionError('adapter did not return')
                assert calls==1 and t and regs[0]==output and regs[13]==initial[13] and regs[14]==initial[14]
                assert regs[4:12]==initial[4:12]
                cases+=1
    return cases
