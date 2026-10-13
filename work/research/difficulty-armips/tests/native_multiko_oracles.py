"""Native sequential opponents; observed award batching, never host distribution."""
from native_battle_oracles import require, events, awards, lifecycle, root_reuse, ev_delta

CASE_ID='growth.multiko_participation'
CASE_IDS=(CASE_ID,'growth.deferred')


def validate_ev_group(prefix,rows,before,after,participants,share_off,snapshot,array):
    proofs=events(prefix,'ev_eligible');calls=events(prefix,'ev')
    require(len(proofs)==3 and {e['id'] for e in proofs}=={1,2,3},'missing native EV eligibility')
    require(all(e['id'] in rows for e in calls),'unknown EV application recipient')
    for i in (1,2,3):
        e=next(e for e in proofs if e['id']==i);record=rows[i]
        enabled=not share_off or i in participants
        require(e['lr']==0x0221F687 and e['mon']==record['mon'] and e['snapshot']==snapshot and
                e['raw_address']==array+16*record['slot'] and
                e['raw_before']==e['raw_after']==record['raw'],'EV eligibility provenance mismatch')
        require(e['result']==int(enabled) and e['branch']==('apply' if enabled else 'skip') and
                e['calls']==int(enabled),'native EV eligibility/skip branch mismatch')
        actual=[c for c in calls if c['id']==i]
        require(len(actual)==int(enabled),'participant/nonparticipant EV application mismatch')
        old=next(m for m in before if m['id']==i)['ev_storage']
        new=next(m for m in after if m['id']==i)['ev_storage']
        delta=[0]*6
        if enabled:
            c=actual[0];raw=bytes.fromhex(record['raw'])
            require(c['lr']==0x0221F6AB and c['mon']==e['mon'] and
                    c['values']==[raw[j] for j in (4,5,6,8,9,7)],'native EV application provenance/yield mismatch')
            delta=[c['values'][j] for j in (0,1,2,5,3,4)]
            require(any(delta) and c['before']==old and c['after']==new,'native battle-mon EV readback mismatch')
        require([b-a for a,b in zip(old['values'],new['values'])]==delta and
                new['total']-old['total']==sum(delta),'native battle-mon EV delta mismatch')


def validate_messages(prefix, eligible, rows):
    # Native0221F786..0221F792 skips individual messages when deferred!=0.
    # 0221F79E selects message1E/1D from raw byte11. The deferred loop at
    # 0221F804 applies positive deferred amounts without either message call.
    for i in (1,2,3):
        boosted=bytes.fromhex(rows[i]['raw'])[11]!=0
        message,lr=(0x1e,0x0221F7BD) if boosted else (0x1d,0x0221F7D7)
        expected=[(e['amount'],message,lr) for e in eligible if e['id']==i and
                  e['phase']=='first' and e['result'] and e['amount']>0 and not e['deferred']]
        actual=[(e['amount'],e['message'],e['lr']) for e in events(prefix,'message') if e['id']==i]
        require(actual==expected,'native direct/deferred message mismatch')
    require(all(e['id'] in rows for e in events(prefix,'message')),'unknown message recipient')


def aggregate_bytes(before,temporary):
    require(len(before)==len(temporary)==96,'short native aggregate record')
    out=bytearray(before)
    for slot in range(6):
        at=16*slot
        value=(int.from_bytes(before[at:at+4],'little')+int.from_bytes(temporary[at:at+4],'little'))&0xffffffff
        out[at:at+4]=value.to_bytes(4,'little')
        for j in range(4,11):out[at+j]=(before[at+j]+temporary[at+j])&255
        out[at+11]=before[at+11] or temporary[at+11]
        out[at+12]=temporary[at+12]
    return bytes(out)


def validate_run(run):
    _,snap,_=lifecycle(run)
    require(len(run['before'])==len(run['after'])==3,'wrong player party count')
    require(all(m['checksum_ok'] and not m['bad_egg'] for m in run['before']+run['after']), 'bad party record')
    ctor=events(run,'constructor');capture=events(run,'captured')[0];ctx=capture['context']
    require(len(ctor)==1 and ctor[0]['lr'] in (0x020507AD, 0x02048EEF) and ctor[0]['flags']==1 and ctor[0]['control']==0 and
            ctor[0]['setup']==ctx['setup']==capture['setup_owner'] and ctx['flags']==1 and ctx['control']==0,
            'not real native trainer6 singles constructor')
    require(ctx['root']==snap['root'] and ctx['save']==ctx['published_save']==capture['save_owner'],
            'native owner identity changed')
    fixture=events(run,'trainer_fixture')
    require(len(fixture)==1 and fixture[0]['before_begin'] and len(fixture[0]['records'])==2 and
            run['events'].index(fixture[0])<run['events'].index(events(run,'begin')[0]),'late/missing opponent inputs')
    require([(e['actor'],e['move']) for e in events(run,'move_verified')]==[(1,150),(2,82),(2,82)],
            'missing actual Splash and two Dragon Rage actions/PP')
    require([(e['opponent_id'],e['outcome']) for e in events(run,'ko_verified')]==[(13,'menu'),(14,'field')],
            'two actual KO/replacement checkpoints absent')
    switches=events(run,'switch_verified')
    require(len(switches)==1 and switches[0]['before']['id']==1 and switches[0]['after']['id']==2,
            'missing actual fighter switch')
    calc=events(run,'calculate');aggregates=events(run,'aggregate');groups=events(run,'award_group')
    require([a['opponent_id'] for a in aggregates]==[13,14] and [a['ordinal'] for a in aggregates]==[1,2],
            'native opponent aggregation missing/duplicated')
    require([i for g in groups for i in g['aggregates']]==[1,2], 'reward groups did not consume each native opponent once')
    for opponent,participants in ((13,[1,2]),(14,[2])):
        rows=[e for e in calc if e['opponent_id']==opponent]
        require(len(rows)==3 and {e['id'] for e in rows}=={1,2,3} and
                all(e['opponent_hp']==0 and sorted(e['participants'])==participants and
                    len(bytes.fromhex(e['raw_calculated']))==16 for e in rows),
                'native KO/changed participation/per-opponent calculation mismatch')
    for a in aggregates:
        require(aggregate_bytes(bytes.fromhex(a['before']),bytes.fromhex(a['temporary'])).hex()==a['combined'],
                'native aggregate EXP/EV/last-marker semantics changed')
    require(groups and len(events(run,'award_group_end'))==len(groups),'unclosed native award group')
    for g in groups:
        prefix=dict(events=[e for e in run['events'] if e.get('group')==g['group']])
        rows={row['id']:row for row in g['rows']}
        require(len(rows)==3 and set(rows)=={1,2,3},'native reward roster mismatch')
        require(g['raw_before']==g['raw_after'],'award passes mutated aggregate raw records')
        if g['aggregates']:
            last=aggregates[g['aggregates'][-1]-1]
            require(last['array']==g['array'] and last['after']==g['raw_before'], 'native aggregate not bound to award pass')
        else:
            require(not any(int.from_bytes(bytes.fromhex(r['raw'])[:4],'little') for r in rows.values()),
                    'award group has no native opponent provenance')
        elig=events(prefix,'eligible')
        require(len(g['aggregates'])==1,'per-opponent EV proof needs observed one-opponent award group')
        opponent=aggregates[g['aggregates'][0]-1]['opponent_id']
        participants=next(e['participants'] for e in calc if e['opponent_id']==opponent)
        validate_ev_group(prefix,rows,g['before'],g['after'],participants,run['flags']&1,snap,g['array'])
        validate_messages(prefix,elig,rows)
        require({e['id'] for e in elig if e['phase']=='first'}=={1,2,3},'incomplete native eligibility pass')
        for e in elig:
            require(e['snapshot']==snap and e['resolved']==e['mon']==rows[e['id']]['mon'], 'award identity/snapshot drift')
            require(e['raw_before']==e['raw_after']==rows[e['id']]['raw'],'raw native reward changed')
            require(e['result']==e['native_result'] and e['deferred']==e['native_deferred'],'native boolean/deferred changed')
            want=e['native_amount']
            if want and run['flags']&2:
                require(e.get('threshold')==run['threshold'] and e['threshold_species']==19,'native cap threshold missing')
                want=min(want,max(0,e['threshold']-e['cache_before']))
            require(e['amount']==want,'wrong native final recipient award')
        for i in (1,2,3):
            raw=bytes.fromhex(rows[i]['raw'])
            ev_request=[raw[j] for j in (4,5,6,8,9,7)]
            expected_ev=[ev_request] if int.from_bytes(raw[:4],'little')>0 else []
            require([e['values'] for e in events(prefix,'ev') if e['id']==i]==expected_ev,
                    'native EV request differs from observed aggregate record')
            received=[e for e in elig if e['id']==i and e['result'] and e['amount']>0]
            accepted=[e['amount'] for e in received if (e['phase']=='first' and not e['deferred']) or
                      (e['phase']=='deferred' and e['deferred'])]
            require(awards(prefix,'apply',i)==awards(prefix,'command',i)==accepted,'native application/group total mismatch')
            old=next(e for e in g['before'] if e['id']==i);new=next(e for e in g['after'] if e['id']==i)
            require(old['cache']==old['exp'] and new['cache']==new['exp'] and old['checksum_ok'] and new['checksum_ok'] and
                    new['cache']-old['cache']==sum(accepted),'group cache/backing/EXP continuity mismatch')
            backing=[e for e in events(prefix,'cache_backing') if e['id']==i]
            require(len(backing)==len(accepted) and all(e['cache']==e['backing']['exp'] and
                    e['backing']['checksum_ok'] for e in backing),'missing/invalid application backing trace')
    require(all(e['group'] is not None for name in ('eligible','ev','message','apply','command','cache_backing')
                for e in events(run,name)), 'unbound award outside native group')
    for i in (1,2,3):
        require(run['after'][i-1]['exp']-run['before'][i-1]['exp']==sum(awards(run,'apply',i)), 'final EXP total mismatch')
        evs=[e['values'] for e in events(run,'ev') if e['id']==i]
        native=[sum(row[j] for row in evs) for j in (0,1,2,5,3,4)]
        require(ev_delta(run,i-1)==native,'native EV aggregate/backing mismatch')
        if run['flags']&1 and i==3:
            require(not evs and not awards(run,'apply',i) and native==[0]*6,'Share OFF bench grew')
        else:require(evs and any(native),'participant/Share ON native EV positive control absent')
        require(run['after'][i-1]['level']>=run['before'][i-1]['level'],'downlevel')
    require(events(run,'share') and all(e['result']==(0 if run['flags']&1 else 1) for e in events(run,'share')),'native Share setting missing')
    require(not events(run,'exception'),'native CPU exception')
    if run['flags']&2:
        require(run['before'][0]['exp']==run['after'][0]['exp']==run['threshold'] and
                not awards(run,'apply',1) and not awards(run,'message',1),'capped fighter/then-bench gained EXP')


def compare(runs):
    require(len(runs)==2,'need Cap OFF/ON pair')
    off,on=runs
    for run in runs:validate_run(run)
    root_reuse(runs)
    require(off['flags'] in (0,1) and on['flags']==off['flags']+2 and off['before']==on['before'] and
            off['enemy_input']==on['enemy_input'],'paired inputs differ')
    require(off['after'][0]['level']==12,'OFF control changed capped recipient level; needs a smaller opponent input')
    def raw(run):
        return [(e['group'],e['id'],e['phase'],e['raw_before'],e['native_amount'],e['native_deferred'],e['native_result'])
                for e in events(run,'eligible')]
    require(raw(off)==raw(on),'caps changed native reward grouping/distribution/eligibility')
    for a,b in zip(events(off,'aggregate'),events(on,'aggregate')):
        require(all(a[k]==b[k] for k in ('opponent_id','before','temporary','combined','after')),
                'caps changed upstream native per-opponent aggregate')
    require(sum(awards(off,'apply',1))>0,'uncapped control award missing')
    for i in (1,2,3):
        require(ev_delta(off,i-1)==ev_delta(on,i-1),'caps changed native EV totals')
        require([e['values'] for e in events(off,'ev') if e['id']==i]==
                [e['values'] for e in events(on,'ev') if e['id']==i],'caps changed native EV requests')
        if i!=1:require(awards(off,'apply',i)==awards(on,'apply',i),'discarded EXP redistributed')


def compare_share(on,off):
    require(on['flags'] in (0,2) and off['flags']==on['flags']+1 and
            on['before']==off['before'] and on['enemy_input']==off['enemy_input'],
            'multi-KO Share pair inputs differ')
    def calculations(run):
        return {(e['opponent_id'],e['id']):e for e in events(run,'calculate')}
    baseline,disabled=calculations(on),calculations(off)
    require(set(baseline)==set(disabled)=={(op,i) for op in (13,14) for i in (1,2,3)},
            'missing per-opponent Share comparison')
    for key,e in disabled.items():
        control=baseline[key]
        require(e['participants']==control['participants'],'Share changed actual participation')
        raw=bytes.fromhex(e['raw_calculated']);native=bytes.fromhex(control['raw_calculated'])
        if e['id'] in e['participants']:
            require(raw==native,'Share changed native participant EXP/EV record')
            require(int.from_bytes(raw[:4],'little')>0,
                    'participant native EXP/EV positive control absent')
        else:
            require(int.from_bytes(native[:4],'little')>0,
                    'Share ON bench native positive control absent')
            require(not any(raw[:4]),'Share OFF nonparticipant per-opponent EXP nonzero')
        # EXP calculator returns before EV construction. Bind EV to the native
        # completed per-opponent temporary record, before aggregation.
        def temporary(run,record):
            aggregate=next(a for a in events(run,'aggregate') if a['opponent_id']==record['opponent_id'])
            offset=record['raw_address']-aggregate['temporary_address']
            require(offset in (0,16,32),'per-opponent temporary recipient ownership mismatch')
            return bytes.fromhex(aggregate['temporary'])[offset:offset+16]
        actual_ev=temporary(off,e)[4:10];control_ev=temporary(on,control)[4:10]
        require(any(control_ev),'native per-opponent EV positive control absent')
        # Raw EV yield is constructed for bench too; native eligibility, not
        # erasure of yield bytes, suppresses application (validate_ev_group).
        require(actual_ev==control_ev,'Share changed native per-opponent raw EV yield')
    require(not awards(off,'apply',3) and ev_delta(off,2)==[0]*6 and not
            [e for e in events(off,'ev') if e['id']==3],'always-benched Share OFF recipient grew')


def validate_matrix(runs):
    require([r['flags'] for r in runs]==[0,2,1,3],'need all four Share/Cap controls in order')
    compare(runs[:2]);compare(runs[2:]);root_reuse(runs)
    compare_share(runs[0],runs[2]);compare_share(runs[1],runs[3])
    # Positive deferred bench and the capped former fighter must both execute
    # the real native deferred path. The generic run oracle checks application
    # exactly once, message suppression, raw/boolean preservation and backing.
    for run in runs[:2]:
        deferred=[e for e in events(run,'eligible') if e['phase']=='deferred' and
                  e['native_deferred']==1 and e['native_result']==1 and e['native_amount']>0]
        require(any(e['id']==3 and e['amount']>0 for e in deferred),'positive native deferred bench absent')
        require(any(e['id']==1 and (e['amount']==0 if run['flags']&2 else e['amount']>0)
                    for e in deferred),'former fighter native deferred cap contrast absent')
