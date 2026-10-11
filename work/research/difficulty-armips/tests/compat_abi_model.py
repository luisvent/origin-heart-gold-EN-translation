"""Bounded interpreter of real freshly assembled compatibility instructions.
Not a DS emulator; source promoted from options/compat_check.py.
"""
from pathlib import Path
import struct,json
from candidate_tools import assembled
from support import SOURCE
stage=assembled()[0]
contract=json.loads((SOURCE/'compatibility.json').read_text())
raw={k:(stage/f'{k}.bin').read_bytes() for k in ('arm9','overlay50','itcm')}
bases={k:int(v['base'],16) for k,v in contract['full_input_guards']['en'].items()}
def block(f,a,b):return struct.unpack('<'+'H'*((b-a)//2),raw[f][a-bases[f]:b-bases[f]])
def run(code,regs,word=0):
 r=[0]*8;r[:len(regs)]=regs;carry=0;written=False
 for ins in code:
  rd=ins&7;rm=(ins>>3)&7;imm=(ins>>6)&31
  if ins&0xf800==0x0000:r[rd]=(r[rm]<<imm)&0xffffffff
  elif ins&0xf800==0x0800:r[rd]=r[rm]>>(imm or 32)
  elif ins&0xf800==0x2000:r[(ins>>8)&7]=ins&255
  elif ins&0xf800==0x8800: assert r[rm]+imm*2==0x10000000;r[rd]=word
  elif ins&0xf800==0x8000: assert r[rm]+imm*2==0x10000000;word=r[rd]&65535;written=True
  elif ins&0xffc0==0x4380:r[rd]&=~r[rm]
  elif ins&0xffc0==0x4300:r[rd]|=r[rm]
  elif ins&0xffc0==0x4000:r[rd]&=r[rm]
  elif ins&0xffc0==0x4240:carry=int(r[rm]==0);r[rd]=(-r[rm])&0xffffffff
  elif ins&0xffc0==0x4140:
   v=r[rd]+r[rm]+carry;carry=int(v>0xffffffff);r[rd]=v&0xffffffff
  elif ins&0xf800==0x1800:
   operand=(ins>>6)&7;v=operand if ins&0x400 else r[operand]
   if ins&0x200:carry=int(r[rm]>=v);r[rd]=(r[rm]-v)&0xffffffff
   else:r[rd]=(r[rm]+v)&0xffffffff
  elif ins==0x4770:break
  else:raise AssertionError(hex(ins))
 return r,word,written
getters=[('arm9',0x20040b4,0x20040b8,0,0),('arm9',0x202b202,0x202b20a,0,0),('overlay50',0x21e4b18,0x21e4b1c,1,1),('overlay50',0x21e4b44,0x21e4b48,0,0),('overlay50',0x21e53b4,0x21e53b8,0,2)]
getters=[(block(f,a,b),start,end) for f,a,b,start,end in getters]
setter=block('arm9',0x202b20c,0x202b220)
speed=block('itcm',0x1ff8ac2,0x1ff8acc)
inline_speed=block('itcm',0x1ff8af6,0x1ff8b00)
rows=block('itcm',0x1ff8a1e,0x1ff8a28)
fast1=block('itcm',0x1ff8766,0x1ff876a)
fast2=block('itcm',0x1ff8c2e,0x1ff8c32)
for w in range(65536):
 for code,start,end in getters:
  regs=[0,0];regs[start]=w;r,_,_=run(code,regs);assert r[end]==((w>>4)&1)
 for t in [0,1,2,3,0xffffffff]:
  _,out,wrote=run(setter,[0x10000000,t],w);assert wrote and out==((w&~16)|((t&1)<<4))
 for m in [0,4]:
  for code in [speed,inline_speed]:
   _,out,wrote=run(code,[0x10000000,m],w);assert wrote and out==((w&~4)|m)
 assert run(rows,[w])[0][1]==((w>>2)&1)
 for code in [fast1,fast2]:assert run(code,[w])[0][1]==(w&4)
payload=json.loads(Path('work/patches/text-speed/payload.json').read_text());data=bytes.fromhex(payload['code']);base=payload['base']
# Exact all-byte candidate census, then bind each to its disassembled code role.
census=[]
for pat in ['0c21','0c23']:
 census += [hex(base+i) for i in range(0,len(data)-1,2) if data[i:i+2]==bytes.fromhex(pat)]
assert set(census)=={'0x1ff8766','0x1ff8a1e','0x1ff8ac4','0x1ff8af8','0x1ff8c2e'}
