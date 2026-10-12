#!/usr/bin/env python3
"""PC wallpaper stress by RAM: live storage wallpaper array (24 bytes) set to value ranges, PC > Organize boxes, page through all 24 boxes with the title arrow; abort/black checks (melonDS)."""
import sys,datetime,json,argparse,struct
from pathlib import Path
sys.path.insert(0,'/Users/simonvergauwen/Developer/poke/work/tools')
import emu_harness as E
p=argparse.ArgumentParser();p.add_argument('--rom');p.add_argument('--out');p.add_argument('--emulator',default='melonds')
p.add_argument('--rounds',default='0,24,32,40,255')
a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
sav='/Users/simonvergauwen/Developer/poke/work/build/memcheck/full_bag_6mons.sav'
sig=bytes(range(16))+bytes(range(8));rep=[]
with E.start_at(69,4,9,rom=a.rom,sav=sav,out=out,clock=datetime.datetime(2026,10,9,12),emulator=a.emulator) as h:
    h.step(60)
    ram=h.read(0x02000000,0x400000);cands=[]
    i=-1
    while True:
        i=ram.find(sig,i+1)
        if i<0:break
        cands.append(0x2000000+i)
    W=cands[-1];print('wallpaper array',[hex(c) for c in cands],'using',hex(W),flush=True)
    def setw(vals):
        h.write(W,bytes(v&0xFF for v in vals))
    def check(tag):
        rr=h.hang_report(20);e={'tag':tag,'black':(rr['black_top'],rr['black_bottom']),'abort':rr.get('abort')}
        if h.emulator=='melonds':ex=h.cpu_exceptions();e['exc']=(ex['data_aborts'],ex['prefetch_aborts'],ex['undefined'])
        rep.append(e);(out/'report.json').write_text(json.dumps(rep,default=str,indent=1));print(json.dumps(e,default=str),flush=True)
        return bool(e['abort'])
    # open PC > organize boxes
    if h.emulator=='melonds':
        h.write(0x21e5d5e,struct.pack('<H',0x21FB));h.write(0x21e5d66,struct.pack('<H',0x00C9));h.write(0x21e5d6a,struct.pack('<H',0x3102))
        h.press('A',after=60)
    else: h.run_script(script_id=2010,settle=60)
    for k in range(3):h.press('A',after=250)
    rounds=[int(x) for x in a.rounds.split(',')]
    setw([rounds[0]+i for i in range(24)])
    h.step(300);h.press('DOWN',after=100);h.press('A',after=600);h.screenshot('open')
    for r in rounds:
        vals=[(r+i) if r!=255 else 255-i for i in range(24)]
        setw(vals)
        # return to box 1 by going left, then page right through all 24 boxes
        for b in range(24):
            h.touch(155,27,frames=12,after=120)
            h.screenshot(f'r{r}_b{(b+1)%24}')
            if check(f'round {r} box {(b+1)%24} wp {vals[(b+1)%24]}'):sys.exit(1)
