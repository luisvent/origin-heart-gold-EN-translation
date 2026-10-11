"""Two real battles with carried party, discarded award and next-entry cap rise."""
from native_battle_oracles import require, events, awards, ev_delta, root_reuse
from native_progression_oracles import validate_readers

STAGES=(dict(badges=0,erika=False,prewin=False,cap=12,level=12),
        dict(badges=1,erika=False,prewin=False,cap=20,level=12))
CASE_IDS=('growth.caprise_no_banking','runtime.next_cap')


def validate_boundary(before,after):
    raw=bytearray.fromhex(before['profile_raw'])
    require(len(raw)==32 and raw[0x1c]==raw[0x1f]==0,'wrong pre-rise badge inputs')
    raw[0x1c]=1
    expected=dict(before,profile_raw=raw.hex(),progression=dict(before['progression'],badges=1))
    require(after==expected,'between-battle mutation beyond badge0, or party/inventory reset')


def native_awards(run,recipient):
    return [e['native_amount'] for e in events(run,'eligible') if e['id']==recipient and
            e['native_result'] and e['native_amount']>0 and
            ((e['phase']=='first' and not e['native_deferred']) or
             (e['phase']=='deferred' and e['native_deferred']))]


def validate(report):
    runs=report['battles']
    require(len(runs)==2,'need exactly two uninterrupted cap-rise battles')
    first,second=runs
    for run,spec in zip(runs,STAGES):
        validate_readers(run,spec)  # includes every strict base growth/lifecycle assertion
        require(run['before'][0]['species']==run['after'][0]['species']==19 and
                run['before'][0]['level']==12,'wrong carried level12 fighter')
        for i in (1,2,3):
            # Native EV argument order is HP/Atk/Def/SpA/SpD/Speed; backing
            # summary order is HP/Atk/Def/Speed/SpA/SpD. Magikarp yields1 Speed.
            ev=events(run,'ev');selected=[e['values'] for e in ev if e['id']==i]
            require(selected==[[0,0,0,0,0,1]] and ev_delta(run,i-1)==[0,0,0,1,0,0],
                    'native EV request/backing changed or suppressed')
            require(native_awards(run,i),'native recipient positive control missing')
            if run is second or i!=1:
                require(awards(run,'apply',i)==native_awards(run,i),'discarded EXP banked or redistributed')
        for e in events(run,'eligible'):
            if run is second or e['id']!=1:
                require(e['amount']==e['native_amount'],'uncapped final award differs from native request')
    root_reuse(runs)  # validates ALL inter-battle generations even without address reuse
    require(first['before'][0]['exp']==first['threshold'] and
            first['after'][0]['exp']==first['before'][0]['exp'] and
            not awards(first,'apply',1) and not awards(first,'message',1),
            'first battle failed to discard positive capped EXP')
    require(second['before']==first['after'],'party summary reset or EXP bank applied at boundary')
    require(second['before'][0]['exp']<second['threshold'] and
            second['after'][0]['exp']-second['before'][0]['exp']==sum(native_awards(second,1))>0,
            'cap20 did not award exactly the new native request')
    states=report['field_states']
    require(set(states)=={'initial','after_first','after_badge','before_second','after_second'},
            'incomplete raw continuity checkpoints')
    validate_boundary(states['after_first'],states['after_badge'])
    require(states['before_second']==states['after_badge'],'party or inputs changed before second constructor')
    initial=states['initial']
    for state in states.values():
        for key in ('save','party','bag','bag_raw','options_address','options_word','profile','vars'):
            require(state[key]==initial[key],'continuity owner/Bag/Options changed: '+key)
    for run,before,after in ((first,initial,states['after_first']),
                             (second,states['before_second'],states['after_second'])):
        spec=STAGES[0 if run is first else 1]
        expected_progression=dict(badges=spec['badges'],erika=False,prewin=False,clair=False)
        require(before['progression']==after['progression']==expected_progression,
                'progression changed within battle; no frozen-script claim allowed')
        for slot,(old,new) in enumerate(zip(before['mons'],after['mons'])):
            require(old['pid']==new['pid'] and old['speciesId']==new['speciesId']==19 and
                    old['experience']==run['before'][slot]['exp'] and
                    new['experience']==run['after'][slot]['exp'],'sealed party/backing identity or EXP mismatch')
            require(old['checksumOk'] and new['checksumOk'] and old['flags']==new['flags']==0,
                    'unsealed continuity record')
            expected=[dict(m) for m in old['moves']]
            if slot<2:expected[1 if slot==0 else 0]['pp']-=1
            require(new['moves']==expected,'native PP continuity reset or unexpected move action')
    for i in (1,2,3):
        want=sum(awards(first,'apply',i))+sum(native_awards(second,i))
        require(second['after'][i-1]['exp']-first['before'][i-1]['exp']==want,
                'cumulative backing EXP includes a bank or lost award')
