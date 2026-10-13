"""Independent native exclusion checks; invalid native records always fail."""
from pathlib import Path
import sys
from support import ROOT,sha256
import hashlib
import json
from native_battle_oracles import require, validate_run, compare_share

FIELDS = ('pid', 'species', 'exp', 'evs', 'level', 'checksum_ok', 'bad_egg')


def record(path, directory):
    sys.path.insert(0,str(ROOT/"work/tools"))
    import save_core
    path = Path(path).resolve()
    require(path.is_relative_to(Path(directory).resolve()), 'foreign raw recipient artifact')
    raw = path.read_bytes()
    require(len(raw) == 236, 'incomplete native recipient record')
    mon = save_core.compatibility_mon(save_core.request('decodePokemon', raw, diagnostic=False))
    return raw, mon


def fixture_metadata(report, run, directory):
    base=Path(run['negative_records'][0]['before_path']).resolve().parent
    require(base.is_relative_to(Path(directory).resolve()),'foreign local fixture source')
    source_sha=sha256(ROOT/'work/build/memcheck/full_bag_6mons.sav')
    for name,slot,level,party_slot in (('egg-fixture',1,1,3),('fainted-fixture',2,8,4)):
        folder=base/name
        meta=json.loads((folder/'fixture-templates.json').read_text())
        require(meta['candidate_sha256']==report['binding']['candidate_sha256']
                and meta['battery_sha256']==source_sha and meta['seed_slot']==slot,
                'stale or foreign negative fixture provenance')
        _,seed=record(folder/'fixture-seed.bin',directory)
        raw,template=record(folder/f'fixture-level-{level}.bin',directory)
        require(hashlib.sha256(raw).hexdigest()==meta['templates'][str(level)]['sha256']
                and seed['pid']==template['pid']==run['before'][party_slot]['pid']
                and template['species']==19 and template['level']==level,
                'negative fixture identity/template mismatch')
    require(len({run['before'][i]['pid'] for i in (0,3,4)})==3,
            'excluded recipients need distinct observed fixture identities')


def validate_local(report, directory):
    require(report.get('old_state_loaded') is False and len(report['battles']) == 1,
            'local exclusion must use one fresh boot')
    run = report['battles'][0]
    require(run['flags'] in (0, 1) and len(run['before']) == len(run['after']) == 5,
            'foreign local exclusion matrix')
    validate_run(dict(run, before=run['before'][:3], after=run['after'][:3]))
    require(all(m['checksum_ok'] and not m['bad_egg'] for m in run['before']+run['after']),
            'invalid excluded or positive native record')
    require(run['empty_slot']['root'] != 0 and run['empty_slot']['resolver'] == 0,
            'empty party recipient has native backing')
    require(not any(e.get('id') == 6 and e['name'] in ('calculate','eligible','apply','ev')
                    for e in run['events']), 'empty recipient reward operation')
    require([row['slot'] for row in run['negative_records']] == [3,4],
            'egg/fainted raw observations missing')
    samples=run['record_stabilization']
    require(1<=len(samples)<=61 and samples[-1]['closed'] is True
            and all(r['closed'] is False for r in samples[:-1])
            and all(b['frame']==a['frame']+1 for a,b in zip(samples,samples[1:]))
            and len({r['owner'] for r in samples})==1 and samples[-1]['owner']!=0
            and not 0x02020680<=samples[-1]['pc']<0x020206CA
            and len(samples[-1]['record_sha256'])==5,
            'native record snapshot is open, stale or unbounded')
    for row in run['negative_records']:
        slot = row['slot']
        _, before = record(row['before_path'], directory)
        raw_after, after = record(row['after_path'], directory)
        require(hashlib.sha256(raw_after).hexdigest()==samples[-1]['record_sha256'][slot],
                'native closed snapshot and raw excluded output disagree')
        require({k:before[k] for k in FIELDS} == run['before'][slot]
                and {k:after[k] for k in FIELDS} == run['after'][slot],
                'raw recipient/report mismatch')
        require(all(before[k] == after[k] for k in ('pid','species','exp','evs','level','isEgg')),
                'excluded native growth or identity changed')
        if slot == 3:
            require(before['isEgg'] and before['exp'] == 0, 'egg fixture missing')
        else:
            require(not before['isEgg'] and before['hp'] == after['hp'] == 0,
                    'fainted fixture missing or revived')
        eligible = [e for e in run['events'] if e['name']=='eligible' and e['id']==slot+1]
        require(eligible and all(e['native_amount']==e['amount']==e['native_result']==e['result']==0
                                 and e['raw_before']==e['raw_after'] for e in eligible),
                'native excluded eligibility changed')
        require(not any(e.get('id') == slot+1 and e['name'] in ('apply','ev')
                        for e in run['events']), 'excluded award callback')
    fixture_metadata(report,run,directory)
    return run


def validate_remote(run, directory):
    require(run['flags'] in (0,1) and run.get('old_state_loaded') is False,
            'foreign partner settings or boot')
    require(run['command'] == ['TrainerBattle',6,8,0,1], 'foreign native partner constructor')
    events = run['events']
    def one(name):
        rows = [e for e in events if e['name']==name]
        require(len(rows)==1, 'missing/duplicated '+name)
        return rows[0]
    ctor, capture = one('constructor'), one('captured')
    context = capture['context']
    require(ctor['lr'] in (0x020507AD, 0x02048EEF) and ctor['args'][:4]==[11,0x4B,8,385] and ctor['flags']==context['flags']==0x4B
            and ctor['control']==context['control']==0 and ctor['setup']==context['setup'],
            'native partner entry identity mismatch')
    snap = capture['snapshot']
    require(snap['allowed']==1 and snap['epoch']>0 and snap['flags']==run['flags']
            and capture['save_owner']==context['save']==context['published_save']!=0
            and capture['setup_owner']==context['setup'] and snap['root']==context['root']!=0,
            'native partner ownership/settings absent')
    for phase in ('before','after'):
        require([r['id'] for r in run['remote_'+phase]]==list(range(7,13)),
                'all six remote recipients required')
        for row in run['remote_'+phase]:
            raw, mon = record(row['path'], directory)
            require(raw.hex()==row['raw'] and hashlib.sha256(raw).hexdigest()==row['sha256']
                    and all(mon[k]==row[k] for k in ('pid','species','exp','evs')),
                    'remote raw/hash/observation mismatch')
            require(row['mon'] and row['backing'], 'remote native backing missing')
    for before,after in zip(run['remote_before'],run['remote_after']):
        require(all(before[k]==after[k] for k in ('id','mon','backing','pid','species','exp','evs')),
                'remote recipient gained growth or changed owner')
    require(not any(e.get('id') in range(7,13) and e['name'] in ('apply','ev') for e in events),
            'remote native award callback')
    require(len(run['before'])==len(run['after'])==3
            and all(m['checksum_ok'] and not m['bad_egg'] for m in run['before']+run['after']),
            'invalid local partner recipients')
    require(any(e['name']=='action' and e['actor']['id']==1 and e['selected']==e['move']==82 for e in events),
            'native local fighter command missing')
    require(one('original_begin')['frame']==capture['frame'],'original partner entry bypassed')
    for slot in range(3):
        awards=[e for e in events if e['name']=='apply' and e['id']==slot+1]
        evs=[e for e in events if e['name']=='ev' and e['id']==slot+1]
        before,after=run['before'][slot],run['after'][slot]
        require(after['exp']-before['exp']==sum(e['amount'] for e in awards),
                'local EXP differs from actual native applications')
        # Native reward rows store Speed last; boxed Pokémon store Speed fourth.
        require(all(after['evs'][i]-before['evs'][i]==sum(e['values'][(0,1,2,5,3,4)[i]] for e in evs) for i in range(6)),
                'local EVs differ from actual native applications')
    require(run['after'][0]['exp']>run['before'][0]['exp'], 'positive local fighter absent')
    for slot in (1,2):
        before,after=run['before'][slot],run['after'][slot]
        require(after['exp']>before['exp'] if run['flags']==0 else after['exp']==before['exp'],
                'native partner bench Share control failed')
    require(one('teardown')['frame']<one('free')['frame']
            and one('original_free')['root']==context['root']
            and one('original_free')['snapshot']['epoch']==0 and run['turns'][-1]['field'],
            'native partner lifecycle missing')


def validate(local, remote, directory):
    require(len(local)==len(remote)==2, 'missing local/remote Share pair')
    local_runs=[validate_local(r,directory) for r in local]
    require([r['flags'] for r in local_runs]==[0,1] and [r['flags'] for r in remote]==[0,1],
            'missing ON/OFF controls')
    compare_share(*(dict(r,before=r['before'][:3],after=r['after'][:3]) for r in local_runs))
    for run in remote:validate_remote(run,directory)
    return ('growth.native_exclusions',)


def validate_report(report,directory):
    require(report['input_binding']['negative_seed_save_sha256']==report['binding']['negative_seed_save_sha256']==sha256(ROOT/'work/build/memcheck/full_bag_6mons.sav'),
            'stale negative fixture seed source')
    for kind in ('local','remote'):
        require(len(report[kind])==2,'missing fresh exclusion controls')
        for flags,child in enumerate(report[kind]):
            saved=json.loads((Path(directory)/f'{kind}-{flags}'/'result.json').read_text())
            require(saved==child and child.get('status')=='passed' and child.get('finished_utc')
                    and child.get('binding')==report['binding'] and child.get('nonce')==report['nonce']
                    and child.get('old_state_loaded') is False,
                    'foreign, stale or nonterminal exclusion child')
    return validate(report['local'],report['remote'],directory)
