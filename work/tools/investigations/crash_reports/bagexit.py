#!/usr/bin/env python3
"""Quick battle-Bag exit: in a wild battle touch BAG, wait d frames (2..60), press B (or touch back); check the battle menu returns, no abort/hang. Several battles."""
import sys,datetime,json,argparse,random
from pathlib import Path
sys.path.insert(0,'/Users/simonvergauwen/Developer/poke/work/tools')
import emu_harness as E
from PIL import ImageChops
p=argparse.ArgumentParser();p.add_argument('--rom');p.add_argument('--out');p.add_argument('--emulator',default='desmume')
p.add_argument('--battles',type=int,default=3);p.add_argument('--trials',type=int,default=20);p.add_argument('--seed',type=int,default=1)
a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
sav='/Users/simonvergauwen/Developer/poke/work/build/memcheck/full_bag_6mons.sav'
random.seed(a.seed);rep=[];BAG=(36,165)
def is_pocket(h):
    r,g,bl=h.emu.screenshot().convert('RGB').getpixel((236,192+178))
    return bl>r+60 and bl>g+20
def bottom(h):return h.emu.screenshot().convert('RGB').crop((20,192+40,236,192+130))
with E.start_at(109,16,14,rom=a.rom,sav=sav,out=out,clock=datetime.datetime(2026,10,9,12),emulator=a.emulator) as h:
    for b in range(a.battles):
        # walk in grass until the field is left
        steps=0
        while h.in_field() and steps<3000:
            for d in ('LEFT','RIGHT'):
                for _ in range(3):
                    h.walk(d,1);steps+=1
                    if not h.in_field():break
                if not h.in_field():break
        if h.in_field():rep.append({'battle':b,'error':'no battle'});print('no battle',flush=True);break
        h.step(500);base=bottom(h);h.screenshot(f'b{b}_menu')
        for t in range(a.trials):
            d=random.choice([0,1,2,3,4,6,8,10,14,20,30,45,60]);how=random.choice(['B','touch','holdB','holdB','mashB'])
            h.touch(*BAG,frames=8,after=d)
            if how=='B':h.press('B',after=0)
            elif how=='holdB':h.hold('B');h.step(random.choice([3,10,25,40]));h.release('B')
            elif how=='mashB':
                for _ in range(8):h.press('B',after=3)
            else:h.touch(230,176,frames=6,after=0)
            h.step(240)
            e={'battle':b,'trial':t,'delay':d,'how':how}
            need=0
            while is_pocket(h) and need<6:
                h.press('B',after=200);need+=1
            e['extra_B_needed']=need
            e['stuck']=is_pocket(h)
            rr=h.hang_report(30);e['hung']=rr['hung'];e['abort']=rr.get('abort')
            if h.emulator=='melonds':e['exc']=h.cpu_exceptions()['data_aborts']
            # still responsive? reopen the bag and leave again
            if not e['stuck']:
                h.touch(*BAG,frames=8,after=240);e['reopens']=is_pocket(h)
                n2=0
                while is_pocket(h) and n2<6:
                    h.press('B',after=200);n2+=1
                e['leaves_again']=not is_pocket(h)
            rep.append(e)
            if e['stuck'] or e.get('reopens') is False or e.get('leaves_again') is False or e['hung']:
                h.screenshot(f'b{b}_t{t}_BAD');print('BAD',json.dumps(e,default=str),flush=True);(out/'report.json').write_text(json.dumps(rep,default=str,indent=1));sys.exit(2)
        print('battle',b,'done',flush=True)
        (out/'report.json').write_text(json.dumps(rep,default=str,indent=1))
        h.flee()
        h.step(120)
print('trials',len([r for r in rep if 'trial' in r]),'stuck',sum(1 for r in rep if r.get('stuck')),'extraB',sorted(set(r['extra_B_needed'] for r in rep if 'trial' in r)))
