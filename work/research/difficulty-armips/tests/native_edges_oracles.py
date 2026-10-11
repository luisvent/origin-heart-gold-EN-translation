"""Bounded functional edge controls; story scripts and broad exclusions remain open."""
from native_battle_oracles import require,events,awards,ev_delta,root_reuse
from native_progression_oracles import validate_readers
from native_caprise_oracles import native_awards

CASES={'gap':'progression.fixture_gapclosure','overlevel':'growth.overlevel',
       'curve':'growth.other_curve_partial'}


def specs(case):
    if case=='gap':
        return [dict(badges=b,erika=False,prewin=False,cap=c,level=55)
                for b,c in ((0xffdf,55),(0xffff,100))]
    return [dict(badges=0,erika=False,prewin=False,cap=12,level=20 if case=='overlevel' else 11)]*2


def validate_boundary(before,after):
    raw=bytearray.fromhex(before['profile_raw'])
    require(raw[0x1c]==0xdf and raw[0x1f]==0xff,'missing Koga gap/later badges')
    raw[0x1c]=0xff
    require(after==dict(before,profile_raw=raw.hex(),progression=dict(before['progression'],badges=0xffff)),
            'gap closure changed party/inventory or more than Koga badge')


def validate_recipient_thresholds(run,tables):
    for e in events(run,'eligible'):
        if 'threshold' not in e:continue
        require(e['id'] in (1,2,3),'unknown threshold recipient')
        species=run['before'][e['id']-1]['species']
        require(str(species) in tables,'missing actual recipient growth table')
        table=tables[str(species)]
        require(table['species']==species and e['threshold_species']==species,
                'native threshold species differs from actual pre-entry recipient')
        require(e['threshold']==table['thresholds'][run['expected_cap']]==run['threshold'],
                'native threshold differs from actual recipient ROM growth curve')


def validate(report):
    case=report['case'];runs=report['battles'];require(case in CASES and len(runs)==2,'incomplete edge pair')
    meta=report['metadata'];require(meta['species']==(1 if case=='curve' else 19),'wrong edge species metadata')
    if case=='curve':require(meta['personal']['growthRate']!=report['reference_growth_rate'],
                             'second species did not use another native growth curve')
    for index,(run,spec) in enumerate(zip(runs,specs(case))):
        flags=2 if case=='gap' or index else 0
        validate_readers(run,spec,expected_flags=flags)
        require(run['threshold']==meta['thresholds'][spec['cap']],'threshold not bound to candidate species table')
        validate_recipient_thresholds(run,report.get('recipient_growth',{}))
        # The gap's second entry carries native victory evolution unchanged.
        # Initial/reset controls still require the fixture species exactly.
        expected_species=runs[0]['after'][0]['species'] if case=='gap' and index else meta['species']
        require(run['before'][0]['species']==expected_species and run['before'][0]['level']==spec['level'],
                'wrong lead fixture')
        require(all(a['level']<=b['level'] for a,b in zip(run['before'],run['after'])),'native downlevel')
    root_reuse(runs)
    first,second=runs
    if case=='gap':
        states=report['field_states'];validate_boundary(states['before'],states['after'])
        require(states['entry']==states['after'] and second['before']==first['after'],
                'gap boundary reset party or altered inputs')
        require(first['before'][0]['exp']==first['after'][0]['exp']==first['threshold'] and
                native_awards(first,1) and not awards(first,'apply',1),'gap55 did not discard positive award')
        require(second['before'][0]['exp']<second['threshold'] and native_awards(second,1),
                'closed gap lacks newly permitted growth')
        for i in (1,2,3):
            require(awards(second,'apply',i)==native_awards(second,i),'gap closure banked or redistributed EXP')
            require(ev_delta(first,i-1)==ev_delta(second,i-1) and any(ev_delta(first,i-1)),
                    'gap cap changed native EV baseline')
        return
    require(first['before']==second['before'],'edge controls have different party inputs')
    def native(run):
        return [(e['id'],e['phase'],e['raw_before'],e['native_amount'],e['native_result'],e['native_deferred'])
                for e in events(run,'eligible')]
    require(native(first)==native(second),'cap changed native eligibility/distribution')
    for i in (1,2,3):
        require(ev_delta(first,i-1)==ev_delta(second,i-1),'cap changed native EV baseline')
        if i!=1:require(awards(first,'apply',i)==awards(second,'apply',i),'edge rejected EXP redistributed')
    require(native_awards(first,1),'uncapped lead positive control missing')
    if case=='overlevel':
        require(second['before'][0]['exp']>second['threshold'] and
                second['after'][0]['exp']==second['before'][0]['exp'] and second['after'][0]['level']==20 and
                not awards(second,'apply',1) and not awards(second,'message',1),'over-cap recipient grew/downleveled')
        for run in runs:
            require(run['before'][1]['species']==run['after'][1]['species']==20 and
                    run['before'][1]['level']==run['after'][1]['level']==100 and
                    run['before'][1]['exp']==run['after'][1]['exp']==meta['thresholds'][100],
                    'level100 native exclusion changed EXP/level')
            elig=[e for e in events(run,'eligible') if e['id']==2]
            require(elig and all(e['native_amount']==e['amount']==0 and e['native_result']==e['result']==1
                                for e in elig),'level100 original eligibility semantics changed')
            require(not awards(run,'apply',2) and not awards(run,'message',2),'level100 emitted award')
    else:
        require(first['before'][0]['exp']==first['threshold']-7 and
                sum(awards(first,'apply',1))>7 and awards(second,'apply',1)==[7] and
                awards(second,'message',1)==[7] and second['after'][0]['exp']==second['threshold'] and
                second['after'][0]['level']==12,'other-curve native partial growth mismatch')
