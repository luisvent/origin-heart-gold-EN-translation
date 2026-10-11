"""Strict typed input fixtures, written only before dg_battle_begin.

The constructor/launch seams are candidate ARM9 code, not an injected outcome.
No generator, checksum repair, policy/eligibility write, or live BattleMon edit.
"""
import hashlib
from pathlib import Path
import tempfile
from evidence import write_json
from native_battle_fixture import prepare_fixture_templates
from native_battle_helpers import registers
from native_battle_oracles import require
from support import ROOT, sha256


TRAINER = 5  # candidate a/0/5/5: one mon, singles, no trainer items
ENEMY_PARTY_OFFSET = 8  # setup+4+4*owner; +F8/+FC are 32-byte trainer info


def launch_diagnostic(session, trace, registers_at_launch):
    """Persist bounded raw observations before any fixture assertion or write."""
    h = session.h
    setup = registers_at_launch[1]
    row = trace.event('trainer_launch_diagnostic', setup=setup,
                      registers=list(registers_at_launch), selected_party_offset=ENEMY_PARTY_OFFSET,
                      setup_readable=setup % 4 == 0 and 0x02000000 <= setup <= 0x023DC000-0x1d4)
    if row['setup_readable']:
        row['setup_bytes'] = h.read(setup,0x1d4).hex()
        row['pointers'] = []
        for offset in (4,8,12,16,0xf8,0xfc,0x100,0x104):
            address = h.u32(setup+offset)
            item = dict(offset=offset,address=address,
                        kind='pokemon_party' if offset < 0xf8 else 'trainer_info',
                        header_readable=address % 4 == 0 and 0x02000000 <= address <= 0x023DC000-32)
            row['pointers'].append(item)
            if item['header_readable']:
                header = h.read(address,32)
                item.update(header=header.hex(),word0=int.from_bytes(header[:4],'little'),
                            word1=int.from_bytes(header[4:8],'little'))
                if offset < 0xf8:
                    item.update(capacity=item['word0'],count=item['word1'])
    write_json(session.out/'trainer-launch-diagnostic.json',row)
    return row


def prepare(receipt, out, item=17, condition="positive"):
    from native_items_cases import case_for
    case = case_for(dict(item=item,condition=condition))
    import save_core
    from emu_harness import SaveFile, POCKETS, encode_pokemon
    from ndspy.rom import NintendoDSRom
    from ndspy.narc import NARC
    out = Path(out)
    templates = prepare_fixture_templates(receipt, out)
    rom = NintendoDSRom.fromFile(receipt['output']['path'])
    trainer = bytes(NARC(rom.getFileByName('a/0/5/5')).files[TRAINER])
    enemy = bytes(NARC(rom.getFileByName('a/0/5/6')).files[TRAINER])
    payload = bytes(NARC(rom.getFileByName('a/0/1/7')).files[item])
    pocket_id = (int.from_bytes(payload[8:10],'little') >> 7) & 15
    pocket_names = ('items','medicine','balls','tm','berries','mail','battle','key')
    require(pocket_id < len(pocket_names) and pocket_names[pocket_id] == case['pocket'],
            'native physical pocket metadata changed')
    if case['restricted_allowed']:
        require((int.from_bytes(payload[8:10],'little') >> 11) & 31 == case['mask'],
                'eligible native battle mask changed')
    splash = bytes(NARC(rom.getFileByName('a/0/1/1')).files[150])
    require(len(trainer) == 20 and trainer[3] == 1 and not any(trainer[4:12]) and trainer[16] == 0,
            'trainer metadata no longer describes itemless singles with one mon')
    require(len(payload) == 34 and payload[11:13] == bytes([case['dispatch'], 1]), 'native item dispatch changed')
    require(payload[14] == case['status_payload'] and payload[27] == case['healing'] and payload[28] == case['pp_amount'],
            'native status/HP effect payload changed')
    require(len(splash) == 16 and splash[6] == 40, 'candidate Splash PP changed')
    full = encode_pokemon(templates[12], moves=[150, 0, 0, 0], pp=[splash[6], 0, 0, 0])
    damaged = encode_pokemon(full, status=case['status'],
                             **({'currentHp':case['hp']} if case['hp'] is not None else {}))
    if case['kind'].startswith('pp-'):
        dragon = bytes(NARC(rom.getFileByName('a/0/1/1')).files[82])
        require(dragon[6] == 10, 'candidate Dragon Rage PP changed')
        damaged = encode_pokemon(damaged,moves=[82,150,0,0],pp=list(case['initial_pp']))
    # Revalidate the sealed closed records before writing any fixture.
    decoded = [save_core.request('decodePokemon', raw, diagnostic=False) for raw in (damaged, full)]
    require(all(m['flags'] == 0 and m['checksumOk'] and not m['isEgg'] for m in decoded),
            'invalid typed item fixture')
    require(decoded[1]['party']['currentHp'] == decoded[1]['party']['stats']['hp'] > 21,
            'Potion fixture needs a full healthy control with >21 HP')
    paths = []
    for name, raw in (('damaged', damaged), ('healthy', full)):
        path = out / (name+'.bin'); path.write_bytes(raw); paths.append(path)
    source = ROOT/'work/build/memcheck/trainer.sav'
    battery = SaveFile(source)
    battery.transaction([dict(type='setPocket', name=name, items=[[item, 3]] if name == case['pocket'] else [])
                         for name in POCKETS])
    # Save-core deliberately refuses to overwrite an existing destination.
    # Retain earlier inputs, including the former fixed items-input.sav, and
    # allocate a fresh owned directory even if this OUT/nonce is reused.
    input_dir = Path(tempfile.mkdtemp(prefix='items-input-',dir=out))
    target = input_dir/'items-input.sav'; battery.write(target)
    metadata = dict(candidate_sha256=receipt['output']['sha256'], source_battery_sha256=sha256(source),
                    input_battery_path=str(target), input_battery_sha256=sha256(target), trainer_id=TRAINER,
                    trainer_sha256=hashlib.sha256(trainer).hexdigest(),
                    enemy_record_sha256=hashlib.sha256(enemy).hexdigest(),
                    item=item, condition=condition, pocket=case['pocket'], pocket_id=pocket_id, target_slot=case['target_slot'], ui_slot=case['ui_slot'], move_slot=case['move_slot'], payload=list(payload), splash=list(splash), healing=case['healing'],
                    records=[dict(path=str(p), sha256=sha256(p), decoded=d) for p,d in zip(paths,decoded)])
    write_json(out/'items-fixture.json', metadata)
    write_json(input_dir/'provenance.json', metadata)
    return dict(damaged=damaged, healthy=full, target_slot=case['target_slot'], battery=target, metadata=metadata)


def install_player(session, trace, fixture):
    h = session.h
    require(h.in_field() and trace.snapshot()['epoch'] == 0 and not trace.run['events'],
            'player fixture must precede battle construction')
    party = h.array(2)
    require(h.u32(party) == 6, 'invalid player party allocation')
    raws = [fixture['healthy']]*3
    raws[fixture['target_slot']] = fixture['damaged']
    for slot, raw in enumerate(raws):
        h.write(party+8+236*slot, raw)
    h.w32(party+4, len(raws))
    trace.run['player_fixture'] = dict(frame=h.frame, party=party,
        hashes=[hashlib.sha256(raw).hexdigest() for raw in raws], before_begin=True)


def install_enemy_at_launch(session, trace, fixture):
    """One pre-entry fixture callback; all subsequent execution hooks read only."""
    import save_core
    h = session.h
    applied = []
    def launch():
        r = registers(h)
        launch_diagnostic(session,trace,r)
        require(not applied, 'unexpected second trainer launch')
        require(r[14] == 0x02050815, 'not the ordinary TrainerBattle launch caller')
        constructors = [e for e in trace.run['events'] if e['name'] == 'constructor']
        require(len(constructors) == 1 and constructors[0]['lr'] == 0x020507AD,
                'unexpected trainer constructor provenance')
        setup = r[1]
        require(constructors[0]['setup'] == setup and constructors[0]['flags'] == 1 and
                constructors[0]['control'] == 0, 'trainer constructor did not return flags1/control0')
        require(not any(e['name'] in ('begin', 'captured', 'effect', 'command') for e in trace.run['events'])
                and trace.snapshot()['epoch'] == 0 and h.in_field(), 'late enemy fixture edit')
        require(h.u32(setup) == 1 and h.u32(setup+0x18c) == 0 and h.u32(setup+0x1c0) == h.save,
                'trainer setup owner/control changed before launch')
        # Native02050CAA stores allocated Pokémon parties at setup+4+4*owner.
        # Native02072742 reads that exact family before Party_Init(...,6).
        # setup+F8+4*owner is a different, 32-byte trainer-info allocation.
        party = h.u32(setup+ENEMY_PARTY_OFFSET)
        require(party % 4 == 0 and 0x02000000 <= party <= 0x023DC000-0x5b0,
                'invalid constructor enemy party pointer')
        capacity, count = h.u32(party), h.u32(party+4)
        require(capacity == 6 and count == 1,
                f'enemy party {party:#x} at setup+8 has capacity={capacity}, count={count}; '
                'see trainer-launch-diagnostic.json')
        raw = h.read(party+8, 236)
        original = session.out/'enemy-native-before.bin'; original.write_bytes(raw)
        # Failure preserves this raw record. Never repair invalid native output.
        native = save_core.request('decodePokemon', raw, diagnostic=False)
        require(native['flags'] == 0 and native['checksumOk'] and not native['isEgg'] and
                native['party']['currentHp'] > 0, 'invalid native trainer mon before fixture')
        replacement = fixture['healthy']
        h.write(party+8, replacement)
        require(h.read(party+8, 236) == replacement, 'enemy fixture write failed')
        row = trace.event('enemy_fixture', setup=setup, party=party, address=party+8,
            party_offset=ENEMY_PARTY_OFFSET,capacity=capacity,count=count,
            before_path=str(original), before_sha256=sha256(original),
            after_sha256=hashlib.sha256(replacement).hexdigest(), native=native,
            before_begin=True, purpose='Valid full-HP Splash-only party input; effects and gates untouched')
        applied.append(row)
    session.hook(0x0204FCE4, launch)
    return applied
