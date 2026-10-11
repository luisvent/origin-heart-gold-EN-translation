"""Read-only functional progression acceptance; no outcome substitutions."""
from native_battle_oracles import require, events, awards, ev_delta, validate_run
from native_progression_cases import CASES


def validate_readers(run, spec, *, expected_flags=2):
    require(run['fixture']['spec']==spec and run['expected_cap']==spec['cap'] and run['flags']==expected_flags,
            'progression case input/expected-cap mismatch')
    validate_run(run)  # all native raw/final/EV/boolean/deferred/message/cache/lifetime checks
    fixture=run['fixture']
    readers=events(run,'cap_reader')
    require(len(readers)==1 and readers[0]['save']==fixture['save'] and
            readers[0]['result']==spec['cap'], 'native cap-for-save observation missing')
    reader=readers[0]
    for name,key in (('profile','profile'),('vars','vars')):
        rows=reader[name]
        require(len(rows)==1 and rows[0]['arg']==fixture['save'] and rows[0]['result']==fixture[key],
                'native '+name+' owner mismatch')
    badges=reader['badge']
    require([e['id'] for e in badges]==list(range(16)), 'native badge reader span/order incomplete')
    require(all(e['owner']==fixture['profile'] and e['result']==((spec['badges']>>e['id'])&1)
                for e in badges), 'native badge predicate mismatch')
    flags=reader['flag']
    require(len(flags)==2 and {e['id'] for e in flags}=={1220,209}, 'native flag reader set mismatch')
    require(all(e['owner']==fixture['vars'] and e['result']==int(spec['erika'] if e['id']==1220 else False)
                for e in flags), 'native flag predicate mismatch')
    order=[e['name'] for e in run['events']]
    require(order.index('original_begin')<order.index('cap_reader')<order.index('captured'),
            'progression reads outside real native entry')


def validate(run):
    spec=CASES[run['name']]
    validate_readers(run,spec)
    require(run['before'][0]['level']==spec['level'] and run['before'][0]['species']==19,
            'wrong growth control recipient')
    require(any(e['id']==1 and e['native_amount']>0 and e['native_result'] for e in events(run,'eligible')),
            'missing positive native award before clamp')
    for slot in range(3):
        require(any(v>0 for v in ev_delta(run,slot)), 'native EV positive control missing')
    require(awards(run,'apply',2) and awards(run,'apply',3), 'other recipient positive controls missing')
    if spec['level']==spec['cap']:
        require(run['before'][0]['exp']==run['threshold'] and not awards(run,'apply',1) and
                not awards(run,'message',1) and run['after'][0]['exp']==run['before'][0]['exp'],
                'result-changing zero cap failed')
    else:
        require(spec['cap']==100 and spec['level'] in (81,89), 'unknown plateau case')
        require(run['before'][0]['exp']>run['obsolete_threshold'] and
                run['after'][0]['exp']>run['before'][0]['exp'] and awards(run,'apply',1),
                'plateau did not allow actual growth beyond obsolete80/88 ceiling')
        require(all(e['amount']==e['native_amount'] for e in events(run,'eligible')),
                'plateau unexpectedly rejected native award')
