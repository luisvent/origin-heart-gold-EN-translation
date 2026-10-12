"""Small reusable cold-boot/input/code-identity helpers for native battle drivers.

Only fixture preparation writes party/save inputs. Execution hooks are read-only.
No savestate, forced outcome, eligibility change, or emulated function call.
"""
import hashlib
from contextlib import contextmanager
from pathlib import Path
from evidence import write_json
from native_battle_oracles import require


@contextmanager
def capture_failure(h, out):
    """Preserve the last visible state before Harness destroys the emulator."""
    try:
        yield
    except BaseException:
        try:
            h.screenshot('failure')
            write_json(Path(out)/'failure-state.json', dict(frame=h.frame, registers=registers(h)))
            # Raw diagnostic only, before emulator destruction. Never decode,
            # repair, or feed a failing native record back into fixture creation.
            party=h.array(2)
            count=h.u32(party+4)
            if h.u32(party)==6 and 0<=count<=6:
                raw=h.read(party,8+236*count)
                (Path(out)/'failure-party.bin').write_bytes(raw)
                write_json(Path(out)/'failure-party.json',dict(address=party,count=count,
                    sha256=hashlib.sha256(raw).hexdigest(),scope='unmodified diagnostic bytes, validity unknown'))
        except Exception:
            pass  # retain the original gameplay/probe exception
        raise


def registers(h):
    bank = getattr(h.reg, 'r', h.reg)
    return [bank[i] & 0xffffffff for i in range(16)]


class NativeSession:
    def __init__(self, h, receipt, out):
        from ndspy.rom import NintendoDSRom
        self.h, self.receipt, self.out = h, receipt, Path(out)
        self.labels = receipt['build']['elf_labels']
        self.payload = (Path(receipt['artifacts']) / 'resident.bin').read_bytes()
        rom = NintendoDSRom.fromFile(receipt['output']['path'])
        self.overlays = rom.loadArm9Overlays([9, 14, 50])
        self.callbacks, self.inputs, self.reused_addresses = {}, [], {}
        self.active = None
        self.menu_state = None
        self.hook(self.labels['dg_menu_input'] & ~1, self.menu_input)

    def menu_input(self):
        self.menu_state = registers(self.h)[0]

    def code(self, address, size=8, overlay=None):
        if 0x023DC000 <= address < 0x023DC000 + len(self.payload):
            return self.payload[address-0x023DC000:address-0x023DC000+size]
        # Only battle overlay addresses use this automatic guard. Options
        # functions use resident labels, so no ambiguous overlay50 lookup.
        o = self.overlays[14 if overlay is None else overlay]
        if o.ramAddress <= address < o.ramAddress + len(o.data):
            return bytes(o.data[address-o.ramAddress:address-o.ramAddress+size])
        if overlay is not None:
            raise ValueError(f'{address:#x} outside explicit overlay{overlay}')
        return None  # static ARM9, already candidate/resident bound

    def hook(self, address, callback, *, overlay=None):
        # Guard each registration separately: an address can hold distinct
        # overlays in one session. Never infer ov9 identity from an ov14 range.
        expected = self.code(address) if overlay is None else self.code(address, overlay=overlay)
        def guarded():
            if expected is not None and self.h.read(address, len(expected)) != expected:
                self.reused_addresses[address] = self.reused_addresses.get(address, 0) + 1
                return
            callback()
        if address not in self.callbacks:
            self.callbacks[address] = []
            def dispatch(h):
                for fn in list(self.callbacks[address]):
                    fn()
            self.h.on_exec(address, dispatch)
        self.callbacks[address].append(guarded)
        return guarded

    def returned(self, callback, *, overlay=None):
        r = registers(self.h)
        address, sp = r[14] & ~1, r[13]
        def done():
            if registers(self.h)[13] == sp:
                self.callbacks[address].remove(token)
                callback()
        token = self.hook(address, done, overlay=overlay)

    def resident(self):
        data = bytearray(self.h.read(0x023DC000, len(self.payload)))
        for a, z in self.receipt['build']['zero_ranges']:
            data[a-0x023DC000:z-0x023DC000] = self.payload[a-0x023DC000:z-0x023DC000]
        require(data == self.payload, 'candidate resident immutable bytes changed')

    def press(self, key, after=20):
        self.inputs.append(dict(frame=self.h.frame, key=key, after=after))
        self.h.press(key, after=after)

    def touch(self, x, y, after=30):
        self.inputs.append(dict(frame=self.h.frame, touch=[x, y], after=after))
        self.h.touch(x, y, frames=6, after=after)

    def checkpoint(self, name, data):
        self.resident()
        self.h.screenshot(name)
        write_json(self.out / (name+'.json'), data)
        print(name, 'frame', self.h.frame, flush=True)

    def boot(self):
        self.h.step(2400)
        self.press('START', after=700)
        self.press('A', after=200)
        self.press('A', after=900)
        require(self.h.in_field(), 'cold candidate boot did not reach field')
        self.h.check_code()
        self.resident()

    def options(self, flags):
        self.menu_state = None
        self.inputs.append(dict(frame=self.h.frame, hold='L'))
        self.h.hold('L'); self.h.step(2)
        self.touch(123, 113, after=240)
        self.h.release('L'); self.h.step(60)
        require(self.menu_state is not None, 'native Options callback not reached')
        state = self.menu_state
        require(self.h.u32(self.labels['page']+24) == state, 'held-L page not active')
        options = self.h.u32(state+0x24)
        old = self.h.u16(options)
        for y, bit in ((35, 4), (55, 1), (75, 2)):
            self.touch(200 if flags & bit else 128, y)
        require(self.h.u16(options) == old, 'Options draft wrote live word')
        self.touch(149, 180, after=240)
        expected = (old & ~0x8028) | (0x8000 if flags & 1 else 0) | (8 if flags & 2 else 0) | (0x20 if flags & 4 else 0)
        require(self.h.u16(options) == expected, 'native Apply did not set requested flags')
        return dict(address=options, before=old, after=expected)


def party_summary(h):
    return [{k: m[k] for k in ('pid', 'species', 'exp', 'evs', 'level', 'checksum_ok', 'bad_egg')}
            for m in h.party()]


def prepare_templates(session):
    """Deterministic typed seed-party fixture; no game/debug-generator calls."""
    from native_battle_fixture import prepare_fixture_templates
    return prepare_fixture_templates(session.receipt,session.out)


def prepare_opponent(session, trace, run):
    """HP1 is a pre-entry party input, never a write to a live BattleMon."""
    from emu_harness import wild_battle, encode_pokemon
    import save_core
    h=session.h
    opponent=wild_battle(h,129,15,moves=[150],pp=[40],item=0)
    run['opponent']=opponent  # retain creation evidence even if validation fails

    def before_entry():
        constructors=[e for e in run['events'] if e['name']=='constructor']
        require(len(constructors)==1 and constructors[0]['flags']==0 and constructors[0]['control']==0,
                'opponent fixture lacks native flags0/control0 constructor provenance')
        require(not any(e['name'] in ('begin','captured','action','teardown') for e in run['events']),
                'opponent input edit attempted after native battle entry')
        require(h.in_field() and trace.snapshot()['epoch']==0, 'opponent edit requires pre-entry field lifetime')
        setup=constructors[0]['setup']
        require(h.u32(setup)==0 and h.u32(setup+0x18c) in (0,8) and h.u32(setup+0x1c0)==h.save,
                'native pre-entry setup owner/control changed')
        return dict(frame=h.frame,setup=setup,flags=h.u32(setup),control=h.u32(setup+0x18c),
                    save=h.save,begin_observed=False)

    phase=before_entry()
    prepared=[]
    require(opponent['copies'], 'no native-born opponent records')
    for index,text in enumerate(opponent['copies']):
        address=int(text,16)
        require(address % 4==0 and 0x02000000<=address<=0x023DC000-236, 'invalid opponent fixture address')
        raw=h.read(address,236)
        prefix=session.out/f"{run['name']}-opponent-{index}"
        original=Path(str(prefix)+'-before.bin');original.write_bytes(raw)
        # A bad native record is retained and rejected, never repaired/retried.
        mon=save_core.request('decodePokemon',raw,diagnostic=False)
        require(mon['pid']==opponent['pid'] and mon['speciesId']==129 and mon['party']['level']==15 and
                mon['party']['currentHp']>0 and not mon['isEgg'], 'unexpected native opponent party input')
        edited=encode_pokemon(raw,currentHp=1)
        after=save_core.request('decodePokemon',edited,diagnostic=False)
        expected=dict(mon,party=dict(mon['party'],currentHp=1))
        require(after==expected and edited[:136]==raw[:136], 'HP fixture changed another native field')
        target=Path(str(prefix)+'-hp1.bin');target.write_bytes(edited)
        record=dict(address=address,before_hp=mon['party']['currentHp'],after_hp=1,
                    species=129,level=15,pid=mon['pid'],exp=mon['experience'],
                    before_path=str(original),before_sha256=hashlib.sha256(raw).hexdigest(),
                    after_path=str(target),after_sha256=hashlib.sha256(edited).hexdigest())
        prepared.append((address,raw,edited,record))
    # Validate all copies before the first write. No emulator frames elapse here.
    for address,raw,edited,record in prepared:
        require(before_entry()==phase and h.read(address,236)==raw, 'opponent changed during fixture preparation')
        h.write(address,edited)
        require(h.read(address,236)==edited, 'opponent HP input write did not persist')
    opponent['hp_fixture']=dict(phase=phase,records=[p[3] for p in prepared],
        purpose='Pre-battle current HP1 input; species/level/EXP unchanged; native damage/KO/rewards untouched')
    trace.event('opponent_hp_fixture',**opponent['hp_fixture'])
    return opponent


def install_fixture(session, templates, partial, benches=((8, 0),), fighter_moves=None):
    """Fighters 1 and 2 plus one bench slot per (level, held item) in `benches`.

    The default is one itemless level-8 bench slot. Held-item runs add a
    non-holder and an Exp. Share (216) holder on the bench; a level-11 bench
    entry sits 3 EXP below the cap-12 threshold so CAP can clamp its share.
    """
    from emu_harness import ARR_PARTY, decode_pokemon, encode_pokemon
    h = session.h
    require(h.in_field(), 'fixture edits require field')
    threshold = decode_pokemon(templates[12])['exp']
    first = encode_pokemon(templates[11], exp=threshold-7) if partial else templates[12]
    raws = [first, templates[8]]
    if fighter_moves:
        raws = [encode_pokemon(r, moves=fighter_moves[0], pp=fighter_moves[1]) for r in raws]
    for level, item in benches:
        raw = templates[level]
        if level == 11:
            raw = encode_pokemon(raw, exp=threshold-3)
        raws.append(encode_pokemon(raw, item=item) if item else raw)
    party = h.array(ARR_PARTY)
    require(h.u32(party) == 6, 'invalid native party allocation')
    for slot, raw in enumerate(raws):
        h.write(party+8+236*slot, raw)
    h.w32(party+4, len(raws))
    profile = h.array(1)+4
    h.w8(profile+0x1c, 0); h.w8(profile+0x1f, 0)
    h.set_flag(1220, False); h.set_flag(209, False)
    return dict(threshold=threshold, party_sha256=[hashlib.sha256(r).hexdigest() for r in raws],
                badge_bytes=[h.u8(profile+0x1c), h.u8(profile+0x1f)],
                erika=h.get_flag(1220), clair=h.get_flag(209),
                note='Party/progression inputs only; Options selected via actual UI; no battle outcome writes')


def native_free_callsite(session):
    """Resolve the wrapper's literal-loaded native free call from bound bytes.

    The candidate compiler emits Thumb LDR Rt,[PC,#imm]; BLX Rt. Require one
    such call to native0201B33D inside the receipt-labelled wrapper, rather than
    accepting any resident LR or pinning a build-dependent absolute address.
    """
    start=session.labels['dg_battle_root_free'] & ~1
    end=min([a & ~1 for a in session.labels.values() if (a & ~1)>start]+[start+128])
    end=min(end,start+128)
    base=0x023DC000;payload=session.payload
    def word(address,size):
        offset=address-base
        require(0<=offset<=len(payload)-size,'free callsite outside bound resident')
        return int.from_bytes(payload[offset:offset+size],'little')
    found=[]
    for address in range(start,end-2,2):
        ldr=word(address,2)
        if ldr & 0xf800 != 0x4800:continue
        register=(ldr>>8)&7
        if word(address+2,2)!=0x4780|(register<<3):continue
        literal=((address+4)&~3)+4*(ldr&255)
        if word(literal,4)==0x0201B33D:
            found.append(dict(address=address,lr=(address+4)|1,
                              code=payload[address-base:address-base+4]))
    require(len(found)==1,'need exactly one bound original-free callsite in wrapper')
    return found[0]


TRAINER_SINGLES, TRAINER_DOUBLES = 5, 6   # a/0/5/5: one mon singles; two-mon doubles (flags 3)


class TrainerLaunch:
    """Replace the native enemy team with HP1 Splash-only input records at launch.

    One callback at the native TrainerBattle launch (0x0204FCE4, ARM9), registered
    once per session. Like the wild HP1 fixture it writes party INPUT before
    dg_battle_begin; nothing here edits a live BattleMon or any reward.
    """
    def __init__(self, session, trace, templates):
        from emu_harness import encode_pokemon
        self.s, self.h, self.trace = session, session.h, trace
        self.enemy = encode_pokemon(templates[12], moves=[150, 0, 0, 0], pp=[40, 0, 0, 0], currentHp=1)
        self.run = None
        session.hook(0x0204FCE4, self.launch)

    def arm(self, run, owners, flags):
        self.run, self.owners, self.flags, self.applied = run, owners, flags, []

    def launch(self):
        run = self.run
        if run is None:
            return
        import save_core
        h = self.h
        r = registers(h)
        setup = r[1]
        require(not self.applied and r[14] == 0x02050815, 'not the single ordinary TrainerBattle launch')
        require(h.in_field() and self.trace.snapshot()['epoch'] == 0, 'enemy fixture needs the pre-entry field lifetime')
        require(h.u32(setup) == self.flags and h.u32(setup+0x18c) == 0 and h.u32(setup+0x1c0) == h.save,
                f'native trainer setup flags {h.u32(setup):#x}/control {h.u32(setup+0x18c):#x} not {self.flags}/0')
        records = []
        for owner in self.owners:
            party = h.u32(setup+4+4*owner)
            require(party % 4 == 0 and 0x02000000 <= party <= 0x023DC000-0x5b0, 'invalid enemy party pointer')
            capacity, count = h.u32(party), h.u32(party+4)
            require(capacity == 6 and 0 <= count <= 6, f'enemy party shape {capacity}/{count}')
            for slot in range(count):
                address = party+8+236*slot
                raw = h.read(address, 236)
                before = self.s.out/f"{run['name']}-enemy{owner}-{slot}-before.bin"; before.write_bytes(raw)
                native = save_core.request('decodePokemon', raw, diagnostic=False)
                require(native['checksumOk'] and not native['isEgg'] and native['party']['currentHp'] > 0, 'invalid native enemy')
                h.write(address, self.enemy)
                require(h.read(address, 236) == self.enemy, 'enemy fixture write failed')
                after = self.s.out/f"{run['name']}-enemy{owner}-{slot}-hp1.bin"; after.write_bytes(self.enemy)
                records.append(dict(owner=owner, slot=slot, address=address, before_path=str(before),
                                    after_path=str(after), species=native['speciesId']))
        require(records, 'native enemy team absent')
        self.applied.append(records)
        phase = dict(frame=h.frame, setup=setup, flags=h.u32(setup), control=h.u32(setup+0x18c), begin_observed=False)
        run['opponent'] = dict(kind='trainer', hp_fixture=dict(phase=phase, records=records,
                               purpose='Splash-only HP1 enemy party input written before battle entry'))
        self.trace.event('opponent_hp_fixture', **run['opponent']['hp_fixture'])
