import sys,datetime
sys.path.insert(0,__import__('pathlib').Path(__file__).resolve().parents[2])
import emu_harness as E
rom,out,outsav=sys.argv[1:4]
def edit(sf):sf.set_pocket('items',[(93,20)]+[(i,n) for i,n in sf.pocket('items') if i!=93])
def gen(h,sp,lv,fm=0):
    try:h.generate_pokemon(sp,level=lv,form=fm)
    except RuntimeError as ex:
        if 'invalid closed' not in str(ex):raise
    h.step(60)
with E.start_at(None,rom=rom,sav=str(__import__('pathlib').Path(__file__).resolve().parents[3]/'build/origin_hg_v4.0.3_en_wip.sav'),out=out,edit=edit,clock=datetime.datetime(2026,10,9,12)) as h:
    gen(h,475,100)   # Gallade slot 3
    gen(h,143,50); gen(h,208,50)
    h.warp(399,8,6,0);h.step(90);h.screenshot('house')
    h.field_menu('save')
    h.press('A',after=200);h.press('A',after=300);h.step(900);h.screenshot('s5');h.press('A',after=200);h.step(200);h.screenshot('s6')
    print(h.emu.backup.export_file(outsav))
