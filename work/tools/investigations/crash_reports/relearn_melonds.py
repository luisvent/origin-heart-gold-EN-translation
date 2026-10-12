#!/usr/bin/env python3
"""Saffron relearner on melonDS (no hooks): teleport into the house, generate mons, talk to NPC, pick party slot, watch for ARM9 aborts / black screens."""
import sys, json, datetime, argparse
from pathlib import Path
sys.path.insert(0, __import__('pathlib').Path(__file__).resolve().parents[2])
import emu_harness as E
p=argparse.ArgumentParser();p.add_argument('--rom');p.add_argument('--out');p.add_argument('--emulator',default='melonds')
p.add_argument('--cases',default='gallade,gardevoir,ninetales,mewtwo,gallade');p.add_argument('--premenu',default='bag')
p.add_argument('--sav',default='saffron_cn4.sav')
a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
edit=None
GEN={'gallade':(475,100,0),'gardevoir':(282,50,0),'ninetales':(38,50,1),'mewtwo':(150,100,0)}
def gen(h,sp,lv,fm):
    n0=h.u32(h.array(E.ARR_PARTY)+4)
    try:h.generate_pokemon(sp,level=lv,form=fm)
    except RuntimeError as ex:
        if 'invalid closed' not in str(ex):raise
    h.step(60)
    return min(n0,5)
rep={'rom':a.rom,'cases':[]}
with E.start_at(None,rom=a.rom,sav=a.sav,out=out,edit=edit,clock=datetime.datetime(2026,10,9,12),emulator=a.emulator) as h:
    h.step(60)
    for ci,case in enumerate(a.cases.split(',')):
        e={'case':case}
        if ci==0 and case=='gallade':slot=3
        else:
            sp,lv,fm=GEN[case];slot=gen(h,sp,lv,fm)
        if a.premenu!='none':
            h.field_menu(a.premenu)
            for _ in range(4):h.press('B',after=90)
        h.screenshot(f'{ci}_{case}_house')
        for i in range(8):
            h.press('A',after=150)
        h.step(60);h.screenshot(f'{ci}_{case}_party')
        h.touch(*E.PARTY_SLOTS[slot],frames=12,after=400);h.press('A',after=500)
        h.step(120);h.screenshot(f'{ci}_{case}_app')
        for i in range(30):h.press('DOWN',after=20)
        h.screenshot(f'{ci}_{case}_scrolled')
        for _ in range(4):h.press('B',after=90)
        h.press('B',after=120);h.press('A',after=300)
        for _ in range(4):h.press('B',after=120)
        h.screenshot(f'{ci}_{case}_back');p0=h.position();h.step_dir('DOWN');e['moved']=p0!=h.position()
        for _ in range(3):
            if h.position()[2]>6:h.step_dir('UP')
        e['back_at']=h.position()
        h.step(60)
        rr=h.hang_report(60)
        e['report']={k:rr[k] for k in ('screen_changed','black_top','black_bottom','hung','position','abort') if k in rr}
        if h.emulator=='melonds': e['exceptions']=h.cpu_exceptions()
        h.screenshot(f'{ci}_{case}_end');rep['cases'].append(e);print(json.dumps(e,default=str),flush=True)
        (out/'report.json').write_text(json.dumps(rep,indent=1,default=str))
        if rr.get('hung'):break
