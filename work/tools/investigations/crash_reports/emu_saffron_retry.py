#!/usr/bin/env python3
"""Saffron full-NPC retry matrix. No ROM writes; private copies of source saves.
Uses native debug generation for consistent species/EXP/stats, and checks live heaps.
"""
import argparse, datetime, hashlib, json, struct
from pathlib import Path
from types import SimpleNamespace
import sys; TOOLS = Path(__import__('os').environ.get('EMU_TOOLS_DIR', Path(__file__).parent)); sys.path.insert(0, str(TOOLS))
import emu_harness as E
import memcheck

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe_party(h, swap=None):
 h.retry_snapshot=None;h.retry_swap=swap;h.retry_requested=True
 for _ in range(1200):
  h.step(1)
  if not h.retry_requested:return h.retry_snapshot
 raise RuntimeError('No safe encrypted party snapshot at native getter return')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--rom',type=Path,required=True);p.add_argument('--save',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 p.add_argument('--no-reset',action='store_true',help='Retain emulator state between cases for leak/fragmentation checks')
 p.add_argument('--pre-menu',choices=['none','bag','pokemon'],default='none')
 p.add_argument('--fill-party',action='store_true')
 p.add_argument('--cases',default='preserve0,preserve1,preserve2,gallade,gardevoir,ninetales,mewtwo')
 a=p.parse_args();a.rom=a.rom.resolve();a.save=a.save.resolve();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
 report={'rom':str(a.rom),'rom_sha256':sha(a.rom),'save':str(a.save),'save_sha256':sha(a.save),'cases':[]}; active={};events=[]
 def emit(kind,**kw):
  event={'event':kind,**kw};events.append(event)
  with (a.out/'events.jsonl').open('a') as f:f.write(json.dumps(event)+'\n')
  print(json.dumps(event),flush=True)
 def edit(s):s.set_pocket('items',[(93,20)]+[(i,n) for i,n in s.pocket('items') if i!=93])
 def hooks(h):
  h.retry_requested=False
  def safe_return(h):
   if not h.retry_requested:return
   base=h.array(E.ARR_PARTY);count=h.u32(base+4)
   if not 1<=count<=6:return
   raws=[h.read(base+8+236*i,236) for i in range(count)]
   if any(struct.unpack_from('<H',r,4)[0]&3 for r in raws):return
   party=[E.decode_party_pokemon(r) for r in raws]
   if not all(m['checksum_ok'] and not m['bad_egg'] for m in party):return
   if h.retry_swap is not None:
    i,j=h.retry_swap
    h.write(base+8+236*i,raws[j]);h.write(base+8+236*j,raws[i]);party[i],party[j]=party[j],party[i]
   h.retry_snapshot=party;h.retry_requested=False
  h.on_exec(0x0206D8BE,safe_return)
  def ev(kind,**kw):
   if active:emit(kind,case=active['case'],frame=h.frame,**kw)
  h.on_exec(0x02025B2C,lambda h:ev('assert',lr=hex(h.reg.lr)))
  h.on_exec(0x0201B284,lambda h:ev('allocation_failure',heap=h.reg.r6) if h.reg.r4==0 else None)
  h.on_exec(0x02026ED4,lambda h:ev('copy_overflow',capacity=h.u16(h.reg.r5),units=h.reg.r4) if h.reg.r4>h.u16(h.reg.r5) else None)
  def bank(h):
   if active and h.reg.r2==736 and h.reg.r3==66:active['app']=True;ev('app_open')
  h.on_exec(0x0200BA98,bank)
  def listed(h):
   if not active:return
   values=[]
   for i in range(41):
    v=h.u16(h.reg.r4+2*i);values.append(v)
    if v==65535:break
   active['eligible']=values;ev('eligible_moves',moves=values)
  h.on_exec(0x02090F18,listed)
  def builder(h):
   if active:
    expected=h.array(E.ARR_PARTY)+8+236*active['slot']
    ev('builder_owner',actual=hex(h.reg.r0),expected=hex(expected))
    if h.reg.r0!=expected:active['wrong_slot']=True
  h.on_exec(0x02090E30,builder)
  def desc(h):
   if active and active.get('app') and h.u16(h.reg.r0+4)==27 and h.u16(h.reg.r0+6)==738:
    active.setdefault('displayed',set()).add(h.reg.r1)
  h.on_exec(0x0200BB0C,desc)
  h.on_exec(0x0204E1BC,lambda h:ev('app_init'))
  def party(h):
   if active:active['party_ui']=True;ev('party_ui')
  import ndspy.rom
  rom=ndspy.rom.NintendoDSRom.fromFile(str(a.rom))
  cmds=json.loads((TOOLS/'docs/script_cmds.json').read_text())
  opcode=next(int(k) for k,v in cmds.items() if v[0]=='PartySelectUI')
  addr=struct.unpack_from('<I',rom.arm9,0xF793C+opcode*4)[0]&~1
  h.on_exec(addr,party)
  probe=SimpleNamespace(mem=h.mem,heap_checks=0,heap_table_errors=[],armed=True)
  def heapcheck(h):
   if active and h.frame%30==0:
    bad=memcheck.Probe.heap_walk(probe)
    if bad:ev('heap_corruption',detail=bad);raise RuntimeError(bad)
  h._per_frame.append(heapcheck)
  h.minspare={}
  def spare_hook(h):
   heap,req,align,hid=h.reg.r0,h.reg.r1+0x10,h.reg.r2,h.reg.r3&0xFF
   if not heap or not active:return
   p,big,n=h.u32(heap+0x24),0,0
   while p and n<4096:
    if h.u16(p)!=memcheck.FREE_SIG:return
    big=max(big,h.u32(p+4));p=h.u32(p+12);n+=1
   sp=big-req-0x10-(abs(align)-4 if abs(align)>4 else 0)
   cur=h.minspare.get(hid)
   if cur is None or sp<cur[0]:h.minspare[hid]=(sp,req-0x10,h.frame)
  h.on_exec(memcheck.ALLOC,spare_hook)
  h.retry_probe=probe
 try:
  with E.start_at(None,rom=a.rom,sav=a.save,out=a.out,edit=edit,hooks=hooks,clock=datetime.datetime(2026,10,9,12)) as h:
   h.check_code({0x02090F18:'07b0f0bd',0x0201B284:'002c',0x02026ED4:'2888',0x0206D8BE:'70bd'})
   baseline=a.out/'baseline.dst';h.save_state(baseline)
   generated={'gallade':(475,100,0),'gardevoir':(282,50,0),'ninetales':(38,50,1),'mewtwo':(150,100,0)}
   for ci,case in enumerate(a.cases.split(',')):
    if not a.no_reset or ci==0:h.load_state(baseline)
    active.clear();entry={'case':case,'sequence':ci};start=len(events)
    try:
     slot=int(case[8:]) if case.startswith('preserve') else 0
     if case in generated:
      species,level,form=generated[case];n0=len(h.party()) if False else h.u32(h.array(E.ARR_PARTY)+4)
      try:entry['generated']=h.generate_pokemon(species,level=level,form=form)
      except RuntimeError as ex:
       if 'invalid closed' not in str(ex):raise
       h.generated_slot=min(n0,5) if n0<6 else 5;entry['gen_snapshot_retry']=True
      h.step(60)
      snapshot=safe_party(h)
      entry['generated']=dict(snapshot[h.generated_slot],slot=h.generated_slot)
      safe_party(h,swap=(0,h.generated_slot))
     if a.fill_party:
      while h.u32(h.array(E.ARR_PARTY)+4)<6:
       try:h.generate_pokemon(143 if h.u32(h.array(E.ARR_PARTY)+4)==4 else 208,level=50)
       except RuntimeError as ex:
        if 'invalid closed' not in str(ex):raise
       h.step(60)
     if a.pre_menu!='none':
      h.field_menu(a.pre_menu)
      for _ in range(4):h.press('B',after=90)
     if slot>=len(h.party()):entry['outcome']='unavailable_slot';report['cases'].append(entry);continue
     entry['party']=safe_party(h)
     if not all(m['checksum_ok'] and not m['bad_egg'] for m in entry['party']):raise RuntimeError('Invalid fixture party')
     h.warp(399,8,6,0);h.step(90)
     active.update(case=case,party_ui=False,app=False,slot=slot);h.screenshot(case+'_house')
     for _ in range(24):
      h.press('A',after=180)
      if active['party_ui']:break
     if not active['party_ui']:raise RuntimeError('NPC did not launch party picker')
     h.step(180);h.screenshot(case+'_party')
     h.touch(*E.PARTY_SLOTS[slot],frames=12,after=180)
     for _ in range(10):
      if active['app'] or active.get('eligible')==[65535]:break
      h.press('A',after=180)
     h.step(120);h.screenshot(case+'_app')
     entry.update(app_opened=active['app'],eligible=active.get('eligible'),slot=slot)
     if not active['app']:
      if active.get('eligible')==[65535]:
       h.press('B',after=120);h.press('B',after=120);entry['outcome']='no_eligible_moves'
      else:raise RuntimeError('No app despite selection')
     else:
      # Exercise all entries in the list, including move descriptions and expanded types.
      for i in range(min(42,len(active.get('eligible',[])))):h.press('DOWN',after=20)
      h.press('B',after=90);h.press('A',after=180)
      for _ in range(3):h.press('B',after=90)
      h.step(120);h.screenshot(case+'_returned');before=h.position();h.step_dir('DOWN');after=h.position()
      entry['movement']=[before,after];entry['heart_scales']=E.bag_items(h).get(93,0)
      if before==after:raise RuntimeError('No field movement after cancel')
      if entry['heart_scales']!=20:raise RuntimeError('Cancel changed Heart Scales')
      if any(e['event'] in ['assert','allocation_failure','copy_overflow','heap_corruption'] for e in events[start:]):raise RuntimeError('Native fault observed')
      entry['outcome']='passed'
     entry['displayed_moves']=sorted(active.get('displayed',set()))
     if active.get('wrong_slot'):raise RuntimeError('Party picker selected a different slot')
     if any(e['event'] in ['assert','allocation_failure','copy_overflow','heap_corruption'] for e in events[start:]):raise RuntimeError('Native fault observed')
     if h.retry_probe.heap_table_errors:raise RuntimeError('Heap observation incomplete: '+str(h.retry_probe.heap_table_errors))
     if entry['outcome']=='no_eligible_moves':
      before=h.position();h.step_dir('DOWN');after=h.position();entry['movement']=[before,after]
      entry['heart_scales']=E.bag_items(h).get(93,0)
      if before==after or entry['heart_scales']!=20:raise RuntimeError('No-eligible rejection did not return safely')
     if entry['outcome']=='passed' and not set(entry['eligible'][:-1]).issubset(active.get('displayed',set())):
      raise RuntimeError('Scroll coverage missed move descriptions')
    except Exception as ex:
     entry['outcome']='failed';entry['error']=str(ex);h.screenshot(case+'_failure');h.save_state(a.out/(case+'_failure.dst'))
    report['cases'].append(entry);emit('result',**entry);active.clear()
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
   report['heap_checks']=h.retry_probe.heap_checks;report['minspare']={str(k):v for k,v in h.minspare.items()};report['heap_table_errors']=h.retry_probe.heap_table_errors
 finally:
  report['rom_unchanged']=sha(a.rom)==report['rom_sha256'];report['save_unchanged']=sha(a.save)==report['save_sha256']
  (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 return int(any(c['outcome']=='failed' for c in report['cases']))
if __name__=='__main__':raise SystemExit(main())
