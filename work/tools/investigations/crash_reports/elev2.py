#!/usr/bin/env python3
"""Silph Co. elevator (map 445, natural entry script, no run_script): per (flag 1208, flag 1366, start floor) boot into the elevator, choose each destination by touch, ride, report arrival map and responsiveness."""
import sys,datetime,json,argparse,time
from pathlib import Path
sys.path.insert(0,'/Users/simonvergauwen/Developer/poke/work/tools')
import emu_harness as E
p=argparse.ArgumentParser();p.add_argument('--rom');p.add_argument('--out');p.add_argument('--starts',default='0,1,2,3,4,5,6');p.add_argument('--dests',default='0,1,2,3,4,5,6')
p.add_argument('--f1208',type=int,default=0);p.add_argument('--f1366',type=int,default=1);p.add_argument('--emulator',default='desmume')
a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
sav='/Users/simonvergauwen/Developer/poke/work/build/memcheck/full_bag_6mons.sav'
POS=[(64,19),(190,19),(64,66),(190,66),(64,114),(190,114),(190,162)]
rep=[]
for s in [int(x) for x in a.starts.split(',')]:
    def edit(sf):
        sf.set_flag(1208,bool(a.f1208));sf.set_flag(1366,bool(a.f1366));sf.set_var(16579,s)
    with E.start_at(445,4,4,rom=a.rom,sav=sav,out=out,clock=datetime.datetime(2026,10,9,12),emulator=a.emulator,edit=edit) as h:
        h.step(200);base=out/f'base_{s}.dst'
        if h.emulator!='melonds':h.save_state(base)
        h.screenshot(f'menu_{a.f1208}_{s}')
        for d in [int(x) for x in a.dests.split(',')]:
            if d!=int(a.dests.split(',')[0]):
                if h.emulator=='melonds':break
                h.load_state(base);h.step(30)
            e={'f1208':a.f1208,'f1366':a.f1366,'start':s,'dest':d}
            t0=time.time()
            try:
                h.touch(*POS[d],frames=10,after=60)
                locs=[]
                for i in range(40):
                    h.step(60)
                    if i%4==3:h.press('A',after=20)
                    if i%5==4:
                        try:locs.append(h.location()['map'])
                        except Exception:pass
                e['maps']=locs;e['loc']=h.location();e['var16579']=h.get_var(16579)
                h.screenshot(f'e{a.f1208}_{s}_{d}_end')
                e['in_field']=h.in_field()
                a0=h.emu.screenshot().convert('RGB').tobytes()
                if e['in_field']:
                    p0=h.position();h.step_dir('DOWN');h.step_dir('UP');e['responds']=True
                else:
                    for _ in range(3):h.press('A',after=100)
                    h.step(200)
                    e['alive_after_A']=h.emu.screenshot().convert('RGB').tobytes()!=a0
                rr=h.hang_report(30);e['black']=(rr['black_top'],rr['black_bottom']);e['hung']=rr['hung']
            except Exception as ex:
                e['error']=str(ex)
            e['secs']=round(time.time()-t0)
            rep.append(e);print(json.dumps(e,default=str),flush=True)
            (out/'report.json').write_text(json.dumps(rep,default=str,indent=1))
