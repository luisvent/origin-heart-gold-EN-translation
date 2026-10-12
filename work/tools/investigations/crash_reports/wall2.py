#!/usr/bin/env python3
"""PC box wallpaper picker: Organize Boxes > box title > Wallpaper; touch every thumbnail on every page (previews load the wallpaper resources), then apply each (更换壁纸/CHANGE) and re-check. Abort/hang/black checks (melonDS) per step."""
import sys,datetime,json,argparse,struct
from pathlib import Path
sys.path.insert(0,'/Users/simonvergauwen/Developer/poke/work/tools')
import emu_harness as E
p=argparse.ArgumentParser();p.add_argument('--rom');p.add_argument('--out');p.add_argument('--emulator',default='melonds')
p.add_argument('--pages',type=int,default=7);p.add_argument('--apply',action='store_true')
a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
sav='/Users/simonvergauwen/Developer/poke/work/build/memcheck/full_bag_6mons.sav'
THUMBS=[60,105,150,198];rep=[]
def sig(h):
    im=h.emu.screenshot().convert('RGB').crop((0,192+60,170,384-30));return im.tobytes()
with E.start_at(69,4,9,rom=a.rom,sav=sav,out=out,clock=datetime.datetime(2026,10,9,12),emulator=a.emulator) as h:
    h.step(60)
    if h.emulator=='melonds':
        h.write(0x21e5d5e,struct.pack('<H',0x21FB));h.write(0x21e5d66,struct.pack('<H',0x00C9));h.write(0x21e5d6a,struct.pack('<H',0x3102))
        h.press('A',after=60)
    else: h.run_script(script_id=2010,settle=60)
    for i in range(3):h.press('A',after=250)
    h.step(300);h.press('DOWN',after=100);h.press('A',after=600)
    def check(tag):
        rr=h.hang_report(30);e={'tag':tag,'black':(rr['black_top'],rr['black_bottom']),'abort':rr.get('abort')}
        if h.emulator=='melonds':ex=h.cpu_exceptions();e['exc']=(ex['data_aborts'],ex['prefetch_aborts'],ex['undefined'])
        rep.append(e);print(json.dumps(e,default=str),flush=True)
        (out/'report.json').write_text(json.dumps(rep,default=str,indent=1))
        return bool(e['abort']) or (e['black'][0] and e['black'][1])
    def open_picker():
        h.touch(70,28,frames=15,after=300);h.touch(213,100,frames=15,after=400)
    open_picker()
    for pg in range(a.pages):
        for t,x in enumerate(THUMBS):
            h.touch(x,34,frames=15,after=150);h.screenshot(f'p{pg}_t{t}')
            if check(f'preview p{pg} t{t}'):sys.exit(1)
        h.touch(244,34,frames=15,after=200)
        h.screenshot(f'p{pg}_next')
    if a.apply:
        h.touch(213,128,frames=15,after=500);h.screenshot('applied')
        check('apply')
