"""Trainer6 native two-record constructor; deterministic pre-entry inputs only."""
import hashlib
from pathlib import Path
from evidence import write_json
from native_battle_helpers import registers
from native_battle_oracles import require, events
from native_items_fixture import launch_diagnostic
from native_items_trace import ram_pointer
from support import sha256


def set_style(session):
    """Select native normal Options STYLE=SET, preserving every other bit."""
    h=session.h;session.menu_state=None
    session.touch(123,113,after=240);h.step(60)
    state=session.menu_state
    require(state is not None and h.u32(session.labels['page']+24)==state and
            h.u32(session.labels['page']+48)==0,'normal Options did not open')
    address=h.u32(state+0x24);before=h.u16(address)
    for _ in range(2):session.press('DOWN',after=4)
    require((h.u32(state+16)>>2)&7==2,'normal STYLE row not selected')
    if h.u16(state+0x86+0x54*2)==0:session.press('RIGHT',after=30)
    require(h.u16(state+0x86+0x54*2)==1 and h.u16(address)==before,'SET draft/input mismatch')
    session.checkpoint('native-style-set-draft',dict(address=address,before=before))
    session.touch(149,180,after=240)
    require(h.u16(address)==before|0x40,'native STYLE apply changed wrong bits')
    return dict(address=address,before=before,after=h.u16(address),method='normal Options UI')


def prepare_enemy(receipt,out,templates):
    from ndspy.rom import NintendoDSRom
    from ndspy.narc import NARC
    from emu_harness import encode_pokemon
    import save_core
    rom=NintendoDSRom.fromFile(receipt['output']['path'])
    meta=bytes(NARC(rom.getFileByName('a/0/5/5')).files[6])
    native_party=bytes(NARC(rom.getFileByName('a/0/5/6')).files[6])
    require(len(meta)==20 and meta[3]==2 and not any(meta[4:12]) and not any(meta[16:20]),
            'trainer6 is no longer itemless singles/two mons')
    raw=encode_pokemon(templates[5],moves=[150,0,0,0],pp=[40,0,0,0],currentHp=1)
    mon=save_core.request('decodePokemon',raw,diagnostic=False)
    require(mon['flags']==0 and mon['checksumOk'] and not mon['isEgg'] and
            mon['speciesId']==19 and mon['party']['level']==5 and mon['party']['currentHp']==1,
            'invalid typed enemy fixture')
    path=Path(out)/'enemy-input.bin';path.write_bytes(raw)
    metadata=dict(trainer=6,trainer_sha256=hashlib.sha256(meta).hexdigest(),trainer_bytes=meta.hex(),
                  native_party_sha256=hashlib.sha256(native_party).hexdigest(),
                  path=str(path),sha256=sha256(path),decoded=mon,
                  purpose='Two deterministic valid HP1/Splash inputs before native begin; no live outcomes edited')
    write_json(Path(out)/'enemy-input.json',metadata)
    return raw,metadata


def install_launch_hook(session,trace,raw):
    import save_core
    def launch():
        if trace.run is None:return
        h=session.h;run=trace.run;r=registers(h)
        launch_diagnostic(session,trace,r);setup=r[1]
        require(not events(run,'trainer_fixture') and not events(run,'begin') and h.in_field() and
                trace.snapshot()['epoch']==0 and r[14]==0x02050815,'late/repeated/wrong trainer launch')
        ctor=events(run,'constructor')
        require(len(ctor)==1 and ctor[0]['lr']==0x020507AD and ctor[0]['setup']==setup and
                ctor[0]['flags']==1 and ctor[0]['control']==0,'not native TrainerBattle6,0 constructor')
        require(h.u32(setup)==1 and h.u32(setup+0x18c)==0 and h.u32(setup+0x1c0)==h.save,
                'trainer pre-entry identity mismatch')
        party=ram_pointer(h.u32(setup+8),8+6*236,'native enemy party')
        require(h.u32(party)==6 and h.u32(party+4)==2,'native trainer6 party count mismatch')
        records=[]
        for slot in range(2):
            address=party+8+236*slot;original=h.read(address,236)
            path=session.out/f"{run['name']}-enemy-{slot}-before.bin";path.write_bytes(original)
            decoded=save_core.request('decodePokemon',original,diagnostic=False)
            require(decoded['flags']==0 and decoded['checksumOk'] and not decoded['isEgg'],
                    'invalid native-created enemy; no repair/retry')
            records.append(dict(slot=slot,address=address,before_path=str(path),before_sha256=sha256(path),
                                before=decoded,after_sha256=hashlib.sha256(raw).hexdigest()))
        # Both native originals validated before the first fixture write.
        for record in records:
            h.write(record['address'],raw)
            require(h.read(record['address'],236)==raw,'enemy input readback failed')
        trace.event('trainer_fixture',setup=setup,party=party,records=records,before_begin=True)
    session.hook(0x0204FCE4,launch)
