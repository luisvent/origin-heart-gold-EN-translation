"""Independent constructor, ownership and continuation acceptance checks."""
from native_battle_oracles import require

CASES = {'grass': ('runtime.ordinary_0', 'runtime.ordinary_4a'),
         'trainer13': ('runtime.ordinary_13',), 'trainer4b': ('runtime.ordinary_4b',),
         'roamer': ('runtime.ordinary_100',)}


def validate(report):
    case = report['case']
    require(case in CASES, 'unknown entry family')
    flags_seen = set()
    for run in report['battles']:
        constructors = [e for e in run['events'] if e['name'] == 'constructor']
        captures = [e for e in run['events'] if e['name'] == 'captured']
        require(len(constructors) == len(captures) == 1, 'entry constructor/capture missing or duplicated')
        ctor, capture = constructors[0], captures[0]
        context, snap = capture['context'], capture['snapshot']
        flags = context['flags']; flags_seen.add(flags)
        require(ctor['frame'] < capture['frame'] and ctor['setup'] == context['setup'], 'foreign constructor setup')
        require(ctor['args'][0] == 11 and ctor['args'][1] == ctor['flags'] == flags,
                'not the observed native constructor branch')
        require(ctor['control'] == context['control'] == 0, 'nonordinary native entry control')
        if case.startswith('trainer'):
            require(ctor['lr'] in (0x020507AD, 0x02048EEF), 'not the native trainer constructor')
        else:
            require(ctor['lr'] in {0: (0x0224870D,), 0x4a: (0x0224712D,),
                                   0x100: (0x0224709F, 0x02247545)}.get(flags, ()),
                    'not the native field encounter constructor')
        require(snap['allowed'] == 1 and snap['epoch'] > 0 and snap['root'] == context['root'],
                'ordinary snapshot absent or foreign')
        require(capture['save_owner'] == context['save'] == context['published_save'] != 0,
                'native SaveData identity lost')
        require(capture['setup_owner'] == context['setup'] != 0, 'native setup identity lost')
        samples = run['control_trace']
        require(len(samples) == 5 and len({s['frame'] for s in samples}) == 5, 'incomplete continuation')
        for sample in samples:
            require(sample['frame'] >= capture['frame'] and sample['snapshot'] == snap,
                    'snapshot changed within ordinary battle')
            require(sample['control'] == 0 and 0x02000000 <= sample['sp'] < 0x02800000,
                    'invalid native control/stack continuation')
        if case in ('grass', 'roamer'):
            require(run['returned_to_field'] is True and run['after_snapshot']['epoch'] == 0,
                    'natural battle teardown incomplete')
    expected = {'grass': {0, 0x4a}, 'trainer13': {0x13}, 'trainer4b': {0x4b},
                'roamer': {0x100}}[case]
    require(expected <= flags_seen <= {0,0x4a,0x100} if case == 'roamer' else
            flags_seen == expected, 'incomplete entry family')
    if case == 'roamer':
        require(1 <= len(report['battles']) <= 24, 'unbounded roamer encounter series')
        fixture = report['roamer_fixture']
        require(fixture['pointer'] == fixture['array'] + 0x10 and
                fixture['position'] == [41,392,203] and fixture['tile'] == [2,False] and
                fixture['location_table'] == '29000000', 'incoherent roamer location fixture')
        native = bytes.fromhex(fixture['native'])
        require(len(native) == 20 and int.from_bytes(native[12:14],'little') == 243 and
                native[16] == 40 and native[18] == 1 and
                int.from_bytes(native[14:16],'little') > 0, 'invalid native-created Raikou')
        require(all(w['pointer'] == fixture['pointer'] for w in fixture['writes']) and
                {w['field']:w['value'] for w in fixture['writes']}.get(4) == 243 and
                {w['field']:w['value'] for w in fixture['writes']}.get(6) == 40,
                'missing native roamer constructor writes')
        for run in report['battles']:
            loc = run['location_input']
            before, after = bytes.fromhex(loc['before']), bytes.fromhex(loc['after'])
            require(loc['before_entry'] is True and loc['map'] == 41 and loc['index'] == 8 and
                    len(before) == len(after) == 20 and before[4:] == after[4:] == native[4:] and
                    after[:4] == bytes.fromhex('29000000'), 'roamer fixture changes nonlocation input')
    elif case == 'grass':
        require(2 <= len(report['battles']) <= 24, 'unbounded natural encounter series')
    else:
        require(len(report['battles']) == 1, 'duplicate trainer entry')
        expected_prefix = [['SetFlag', 0x961], ['SetVar', 0x403f, 385]] if case == 'trainer4b' else []
        require(report['script'] == [['LockAll'], *expected_prefix,
                ['TrainerBattle', 6, 8, 0, int(case == 'trainer4b')], ['ReleaseAll'], ['End']],
                'wrong native partner/script input')
    return CASES[case]
