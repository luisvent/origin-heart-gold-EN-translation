"""Restricted instruction model of fresh assembled stubs, NOT ARM CPU execution.
Promoted from items/impl/check_stubs.py; no historical binaries are executed.
"""
import struct,json
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_ARM
from capstone.arm import ARM_OP_IMM
from candidate_tools import assembled
from support import SOURCE
_,_,_,_,_,_,_,report=assembled()
stage=assembled()[0]
base=next(s['start'] for s in report['stub_spans'] if s['file']=='item_stubs.bin')
code=(stage/'item_stubs.bin').read_bytes()
syms=report['elf_labels']
hooks=json.loads((SOURCE/'native/items_hooks.json').read_text())
funcs=['dg_bag_item_attr','dg_bag_remembered','dg_bag_accept','dg_bag_commit_item','dg_bag_commit_target','dg_bag_effect_attr']
thumb=Cs(CS_ARCH_ARM,CS_MODE_THUMB);thumb.detail=True
arm=Cs(CS_ARCH_ARM,CS_MODE_ARM);arm.detail=True
# Restricted instruction model over REAL armips output, not a hardware emulator.
# Every C boundary is mocked and poisons all volatile registers/flags. Shipping
# C itself is exercised independently by host_check, not reimplemented here.
alias={'sb':9,'sl':10,'fp':11,'ip':12,'sp':13,'lr':14,'pc':15}
def rn(ins,r):
 n=ins.reg_name(r)
 return alias[n] if n in alias else int(n[1:])
def model(hook,align,result,initial_flags):
 regs=[0x02020000+i*0x100 for i in range(16)];regs[13]=0x023a1000+align;regs[14]=0x02123457
 initial=regs[:];sp=regs[13];mem={sp+0x2c:regs[14],sp+8:0x02031000,sp+0x20:0x02032000};flags=initial_flags;t=True
 pc=int(hook['address'],16);ret=pc+4;isbag=hook['target']=='DG_ItemCommitBag';istarget=hook['target']=='DG_ItemCommitTarget'
 calls=0;minsp=sp
 args=initial[:4]
 if hook['target']=='DG_ItemList':args[3]=initial[4];function=funcs[0]
 elif hook['target']=='DG_ItemRemembered':function=funcs[1]
 elif hook['target']=='DG_ItemAccept':args=args[:1];function=funcs[2]
 elif hook['target']=='DG_ItemEffectAttr':args=initial[:3]+[0x02031000];function=funcs[5]
 elif isbag:args=[initial[1]];function=funcs[3]
 else:args=[initial[4],initial[2]];function=funcs[4]
 def read(p):
  if base<=p<base+len(code):return struct.unpack_from('<I',code,p-base)[0]
  assert p in mem,hex(p)
  return mem[p]
 for step in range(120):
  if pc==ret:break
  if pc==int(hook['address'],16):
   o=int(hook['offset'],16);raw=(stage/hook['file']).read_bytes()[o:o+4]
  else:assert base<=pc<base+len(code),hex(pc);raw=code[pc-base:pc-base+4]
  ins=next((thumb if t else arm).disasm(raw,pc));op=ins.operands;m=ins.mnemonic
  nextpc=pc+ins.size
  def value(x):
   if x.type==ARM_OP_IMM:return x.imm & 0xffffffff
   r=rn(ins,x.reg);return pc+(4 if t else 8) if r==15 else regs[r]
  if m in ('push','pop'):
   rr=[rn(ins,x.reg) for x in op];start=regs[13]-4*len(rr) if m=='push' else regs[13]
   for i,r in enumerate(rr):
    if m=='push':mem[start+4*i]=regs[r]
    else:regs[r]=read(start+4*i)
   regs[13]=start if m=='push' else start+4*len(rr)
  elif m=='mov':regs[rn(ins,op[0].reg)]=value(op[1])
  elif m in ('bic','sub'):
   a,b=value(op[1]),value(op[2]);regs[rn(ins,op[0].reg)]=(a&~b if m=='bic' else a-b)&0xffffffff
  elif m in ('ldr','str'):
   r=rn(ins,op[0].reg);b=rn(ins,op[1].mem.base);a=(pc+8 if b==15 else regs[b])+op[1].mem.disp
   if m=='str':mem[a]=regs[r]
   else:
    v=read(a)
    if r==15:t=bool(v&1);nextpc=v&~1
    else:regs[r]=v
  elif m=='bl':regs[14]=nextpc|1;nextpc=value(op[0])
  elif m=='blx':
   assert value(op[0])==syms[function]
   assert regs[13]%8==0 and regs[:len(args)]==args,(function,regs[:4],args)
   if function==funcs[1]:assert read(regs[13])==initial[4]
   if function==funcs[5]:assert read(regs[13])==0x02032000
   calls+=1
   for r in (0,1,2,3,12,14):regs[r]=0xbad00000+r
   regs[0]=result;flags=0xf0000000
  elif m=='bx':v=value(op[0]);t=bool(v&1);nextpc=v&~1
  elif m=='cmp':
   a,b=value(op[0]),value(op[1]);d=(a-b)&0xffffffff
   flags=(d&0x80000000)|(int(d==0)<<30)|(int(a>=b)<<29)|((((a^b)&(a^d))>>3)&0x10000000)
  elif m=='nop':pass
  else:raise AssertionError((hex(pc),m,ins.op_str))
  pc=nextpc;minsp=min(minsp,regs[13])
 else:raise AssertionError('loop')
 assert calls==1 and t and regs[13]==sp
 if isbag or istarget:
  output=7 if isbag else 1
  for r in range(15):assert regs[r]==(result if r==output else initial[r]),(hook['target'],r,hex(regs[r]),hex(initial[r]))
  b=0 if isbag else 6;d=(result-b)&0xffffffff
  expected=(d&0x80000000)|(int(d==0)<<30)|(int(result>=b)<<29)|((((result^b)&(result^d))>>3)&0x10000000)
  assert flags==expected
 else:
  assert regs[0]==result
  for r in range(4,12):assert regs[r]==initial[r]
  assert regs[14]==ret|1
 return sp-minsp
maxstack={};cases=0
for h in hooks:
 for align in (0,4):
  for result in (0,1,5,6,17,790,0x80000000,0xffffffff):
   for flags in range(16):
    depth=model(h,align,result,flags<<28);maxstack[h['target']]=max(maxstack.get(h['target'],0),depth);cases+=1
