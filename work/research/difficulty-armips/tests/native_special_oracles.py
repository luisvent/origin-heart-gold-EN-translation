"""Independent native special-entry and original-behaviour acceptance checks."""
from native_battle_oracles import require

ZERO = dict(flags=0, cap=0, allowed=0, root=0, epoch=0)


def validate(battles, directory=None):
    require([r['flags'] for r in battles] == [0, 7], 'missing default/enabled comparison')
    outcomes = []
    for run in battles:
        require(run['command'] == ['ScrCmd_250', 19, 5], 'foreign native special command')
        events = run['events']
        def one(name):
            rows = [e for e in events if e['name'] == name]
            require(len(rows) == 1, 'missing/duplicated native ' + name)
            return rows[0]
        ctor, capture = one('constructor'), one('captured')
        context = capture['context']
        require(ctor['lr'] == 0x02050639 and ctor['args'][:3] == [11, 0, 5], 'foreign native constructor')
        require(ctor['flags'] == ctor['control'] == 0 and ctor['setup'] == context['setup'], 'constructor identity changed')
        require(ctor['frame'] < capture['frame'] and context['flags'] == 0 and context['control'] == 1,
                'native special control not established before capture')
        require(context['save'] == context['published_save'] != 0, 'foreign SaveData')
        require(capture['snapshot'] == ZERO and capture['save_owner'] == capture['setup_owner'] == 0,
                'excluded entry published difficulty ownership')
        require(one('original_begin')['frame'] == capture['frame'], 'original entry bypassed')
        samples = run['control_trace']
        require(len(samples) == 5 and len({s['frame'] for s in samples}) == 5, 'continuation missing')
        require(all(s['control'] == 1 and s['snapshot'] == ZERO and 0x02000000 <= s['sp'] < 0x02800000
                    for s in samples), 'excluded continuation changed')
        actions = [e for e in events if e['name'] == 'action' and e['actor']['id'] == 1]
        require(len(actions) == 1 and actions[0]['move'] == actions[0]['selected'] == 82,
                'actual original move action missing')
        require(run['pp_before'] == [40, 0, 0, 0] and run['pp_after'] == [39, 0, 0, 0],
                'native move did not consume exactly one PP')
        require(len(run['before']) == len(run['after']) == 1, 'foreign party fixture')
        before, after = run['before'][0], run['after'][0]
        require(before == after and before['species'] == 20 and before['level'] == 20
                and before['checksum_ok'] and not before['bad_egg'], 'excluded recipient growth/identity changed')
        if directory is not None:
            from pathlib import Path
            import save_core
            raw = (Path(directory) / f"special-{run['flags']}" / 'native-lead.bin').read_bytes()
            require(len(raw) == 236, 'missing complete native party record')
            mon = save_core.compatibility_mon(save_core.request('decodePokemon', raw, diagnostic=False))
            require({k: mon[k] for k in before} == before and not mon['isEgg'] and mon['hp'] > 0
                    and mon['moves'] == [82, 0, 0, 0] and mon['pp'] == run['pp_before'],
                    'native input record disagrees with the observed fixture')
        require(not any(e['name'] in ('apply', 'ev', 'exception') for e in events), 'excluded award or native exception')
        require(one('teardown')['frame'] < one('free')['frame'] and one('original_free')['root'] == context['root'],
                'original teardown/root free missing')
        require(run['after_snapshot'] == ZERO and run['inputs'], 'native field return missing')
        outcomes.append((actions[0]['move'], run['pp_after'], before['exp'], before['evs'], run['after_snapshot']))
    require(outcomes[0] == outcomes[1], 'enabled special behaviour differs from default')
    return ('runtime.exclude_special',)
