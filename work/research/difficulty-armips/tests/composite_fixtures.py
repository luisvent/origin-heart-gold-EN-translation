"""Synthetic host-test inputs only. Never retained or registered as native proof."""
from copy import deepcopy
from pathlib import Path
from evidence import write_json
from support import sha256
from native_composites import SPECS, TRACE, required_artifacts

BINDING={'synthetic':'host-only'}


def report_for(job_id):
    spec=SPECS[job_id];args=dict(zip(spec['args'][::2],spec['args'][1::2]))
    r=dict(driver=spec['driver'],layer=spec['layer'],binding=deepcopy(BINDING),nonce=job_id,
           status='passed',finished_utc='synthetic terminal',old_state_loaded=False,cases={},inputs=[],
           overlay_address_reuse={})
    if spec['driver']=='native_items.py':
        from test_native_items import medicine_sample
        i=int(args['--item']);c=int(args['--category']);m=args['--mode'];condition=args['--condition']
        run=medicine_sample(i,c,m=='all',condition)
        run.update(name=m,category=c,condition=condition,checkpoint='passed')
        r.update(battle=run,items_pair='synthetic-pair')
    elif spec['driver']=='native_items_gates.py':
        if args['--gate']=='remembered':
            from test_native_items_remembered import sample
            r['battle']=sample(int(args['--fault-item']))
        else:
            from test_native_items_gates import gate_sample
            r['battle']=gate_sample(args['--gate'],int(args['--fault-item']))
    elif spec['driver']=='native_items_doubles.py':
        from test_native_items_doubles import evidence
        r['battle']=evidence(args['--gate'],int(args['--slot']))
        r['battle']['fault_item']=17
    elif spec['driver']=='native_items_persistence.py':
        from test_native_items_persistence import evidence
        r.update(evidence())
    else:
        # Composition/wiring tests isolate the individual growth oracles. This
        # deliberately incomplete payload MUST fail the real strict oracle.
        def run(name):
            snap=dict(epoch=1,flags=2,cap=12,root=100,allowed=1)
            return dict(name=name,events=[dict(name=n,snapshot=deepcopy(snap)) for n in ('captured','eligible','free')])
        if spec['driver']=='native_battle.py':
            r.update(scope='matrix',battles=[run(n) for n in ('zero-off','zero-on','share-off-cap-off','share-off-cap-on','partial-off','partial-on')])
        elif spec['driver']=='native_progression.py':r['battle']=run(args['--case'])
        elif spec['driver']=='native_caprise.py':r.update(battles=[run('cap12'),run('cap20')],field_states={})
        elif spec['driver']=='native_multiko.py':r.update(battles=[run('synthetic-'+str(i)) for i in range(4)],enemy_input={})
        elif spec['driver']=='native_edges.py':r.update(case=args['--case'],battles=[run('first'),run('second')],
                                                      metadata={},recipient_growth={},field_states={})
    if spec['driver'].startswith('native_items'):
        r['fixture']={key:1 for key in ('candidate_sha256','source_battery_sha256','input_battery_sha256',
            'trainer_id','trainer_sha256','enemy_record_sha256','item','payload','splash','target_slot','ui_slot','move_slot')}
        r['fixture'].update(records=[dict(sha256='same')],condition=r.get('battle',{}).get('condition','positive'))
    return r


def write_report(out, r, *, invocation=None):
    """Rehash mutations to force oracle/trace checks, not just digest rejection."""
    from native_plan import identity
    out=Path(out);out.mkdir(parents=True,exist_ok=True);r=deepcopy(r)
    for name in required_artifacts(r):
        p=out/name;p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():p.write_bytes(b'synthetic host-only observation')
    if 'fixture' in r:write_json(out/'items-fixture.json',r['fixture'])
    write_json(out/TRACE[r['driver']][0],{k:v for k,v in r.items() if k!='checkpoint_artifacts'})
    r['checkpoint_artifacts']=[dict(path=str((out/n).resolve()),sha256=sha256(out/n)) for n in required_artifacts(r)]
    process=dict(status='passed',returncode=0,finished_utc='synthetic terminal',nonce=r['nonce'])
    if invocation:process.update(invocation=invocation,job_id=identity(r))
    write_json(out/'process.json',process);write_json(out/'result.json',r)
    return out/'result.json'
