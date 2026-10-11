"""Read-only native trace oracles. These checks never compute a replacement award.

The OFF battle supplies the observed native request; ON must preserve that raw
request and every other recipient. Missing observations are failures, not zeros.
"""
def require(ok, message):
    if not ok:
        raise AssertionError(message)


def events(run, name):
    return [e for e in run['events'] if e['name'] == name]


def awards(run, name, recipient):
    return [e['amount'] for e in events(run, name) if e['id'] == recipient]


def next_generation(generation):
    require(type(generation) is int and 0 <= generation <= 0xFFFFFFFF,
            'generation is not uint32')
    return ((generation + 1) & 0xFFFFFFFF) or 1


def lifecycle(run):
    """Validate every begin/capture/free seam; return entry and exit generations."""
    names = ('begin', 'original_begin', 'captured', 'free', 'original_free')
    rows = {}
    for name in names:
        found = events(run, name)
        require(len(found) == 1, f'need exactly one lifecycle {name}')
        rows[name] = found[0]
    require([e['name'] for e in run['events'] if e['name'] in names] == list(names),
            'lifecycle seam order mismatch')
    begin, captured, free, released = (rows[n] for n in ('begin', 'captured', 'free', 'original_free'))
    empty = dict(flags=0, cap=0, allowed=0, root=0, epoch=0)
    snap = captured['snapshot']
    start = begin.get('generation')
    epoch = next_generation(start)
    require(begin['snapshot'] == empty, 'begin retained prior snapshot')
    require(captured['generation'] == snap['epoch'] == epoch,
            'begin did not advance generation exactly once')
    require(snap['root'] != 0 and snap['allowed'] == 1 and snap['cap'] == run.get('expected_cap',12) and
            snap['flags'] == run['flags'], 'expected-cap snapshot missing')
    require(free.get('generation') == epoch and free['snapshot'] == snap and
            free['root'] == released['root'] == snap['root'], 'free entry lifetime mismatch')
    require(released['generation'] == next_generation(epoch),
            'free did not advance generation exactly once')
    require(released['snapshot'] == run['final_snapshot'] == empty,
            'teardown revived snapshot')
    return start, snap, released['generation']


def validate_run(run):
    """One completed, ordinary wild battle with exactly two local participants."""
    before, after = run['before'], run['after']
    require(len(before) == len(after) == 3, 'fixture must retain all three party slots')
    for mon in before + after:
        require(mon['checksum_ok'] and not mon['bad_egg'], 'invalid party checksum/egg')
    lifecycle(run)
    moves = events(run, 'move_verified')
    require(moves and moves[0]['actor']==1 and moves[0]['move']==150 and
            all(e['actor']==2 and e['move']==82 for e in moves[1:]) and len(moves)>1,
            'missing actual Splash/Dragon Rage input and PP verification')
    switches = events(run, 'switch_verified')
    require(len(switches)==1 and switches[0]['before']['id']==1 and switches[0]['after']['id']==2,
            'missing actual native fighter1 to fighter2 switch')
    begin, captured = events(run, 'begin'), events(run, 'captured')
    free, original_free = events(run, 'free'), events(run, 'original_free')
    require(len(begin) == len(captured) == len(free) == len(original_free) == 1,
            'need exactly one installed begin/capture/free/original free')
    native_begin = events(run, 'original_begin')
    require(len(native_begin) == 1, 'original begin must execute once')
    order = [e['name'] for e in run['events']]
    require(order.index('begin') < order.index('original_begin') < order.index('captured'),
            'original begin must precede snapshot capture')
    snap = captured[0]['snapshot']
    require(snap['allowed'] == 1 and snap['epoch'] > 0 and snap['cap'] == run.get('expected_cap',12),
            'ordinary expected-cap snapshot missing')
    require(snap['flags'] == run['flags'], 'Options flags were not captured')
    ctx = captured[0]['context']
    constructors = events(run, 'constructor')
    require(len(constructors) == 1 and constructors[0]['setup'] == ctx['setup'] and
            constructors[0]['flags'] == 0 and constructors[0]['control'] == 0,
            'real ordinary0 setup constructor missing')
    # This fixture uses script WildBattle, not random encounters: constructor0
    # returns via02050433, whose caller ORs8 before entering the battle overlay.
    require(constructors[0]['lr'] == 0x02050433 and ctx['flags'] == 0 and
            ctx['control'] == 8 and ctx['save'] == ctx['published_save'],
            'actual scripted-wild0/control8 caller/save identity mismatch')
    require(ctx['root'] == snap['root'] and ctx['setup'] == captured[0]['setup_owner'] and
            ctx['save'] == captured[0]['save_owner'] and captured[0]['generation'] == snap['epoch'],
            'snapshot provider owner/epoch mismatch')
    require(free[0]['root'] == original_free[0]['root'] == snap['root'], 'free changed root argument')
    require(original_free[0]['snapshot'] == dict(flags=0, cap=0, allowed=0, root=0, epoch=0),
            'snapshot not invalidated before original free')
    require(original_free[0]['generation'] != snap['epoch'], 'free did not advance generation')
    require(run['final_snapshot'] == original_free[0]['snapshot'], 'teardown revived snapshot')
    calculations = events(run, 'calculate')
    require(calculations, 'no native defeated-opponent reward calculations')
    require(all(e['opponent_hp']==0 for e in calculations), 'reward calculation lacks native KO/HP0 evidence')
    fixture=events(run,'opponent_hp_fixture')
    require(len(fixture)==1 and fixture[0]['phase']['begin_observed'] is False and
            order.index('opponent_hp_fixture')<order.index('begin'), 'HP input was not prepared before battle entry')
    require({tuple(sorted(e['participants'])) for e in calculations} == {(1, 2)},
            'engine did not record exactly fighters1/2; bench must never participate')
    require({e['id'] for e in calculations} >= {1, 2, 3}, 'native roster calculation incomplete')
    share = events(run, 'share')
    require(share and all(e['result'] == (0 if run['flags'] & 1 else 1) for e in share),
            'installed native share wrapper not observed or wrong result')
    elig = events(run, 'eligible')
    require({e['id'] for e in elig if e['phase'] == 'first'} >= {1, 2, 3},
            'first-pass native eligibility missing')
    for e in elig:
        require(e['raw_before'] == e['raw_after'], 'late wrapper changed raw reward')
        require(e['native_deferred'] == e['deferred'] and e['native_result'] == e['result'],
                'native eligibility/deferred result changed')
        require(e['snapshot'] == snap and e['resolved'] == e['mon'], 'snapshot/recipient identity drift')
        if e['native_amount'] and run['flags'] & 2:
            require(e.get('threshold') == run['threshold'], 'native species cap threshold missing')
            want = min(e['native_amount'], max(0, e['threshold'] - e['cache_before']))
        else:
            want = e['native_amount']
        require(e['amount'] == want, 'wrong final native recipient amount')
    for i in (1, 2, 3):
        ev = [e for e in events(run, 'ev') if e['id'] == i]
        require(len(ev) == (0 if i == 3 and run['flags'] & 1 else 1), 'native EV eligibility mismatch')
        if ev:
            require(order.index('ev') < order.index('eligible'), 'EV pass must precede late EXP clamp')
        applications = awards(run, 'apply', i)
        commands = awards(run, 'command', i)
        messages = awards(run, 'message', i)
        eligible = [e for e in elig if e['id'] == i and
                    ((e['phase'] == 'first' and not e['deferred']) or
                     (e['phase'] == 'deferred' and e['deferred']))]
        accepted = [e['amount'] for e in eligible if e['amount'] > 0 and e['result']]
        require(applications == commands == accepted, f'id{i}: native application/command mismatch')
        # Native deferred pass has no per-recipient 1D/1E queue. Require these
        # messages for immediate awards only; never label a 1F event a message.
        immediate = [e['amount'] for e in eligible if e['phase'] == 'first' and e['amount'] > 0 and e['result']]
        require(messages == immediate, f'id{i}: native message mismatch')
        require(len(applications) <= 1, 'single KO applied more than once')
        require(after[i-1]['exp'] - before[i-1]['exp'] == sum(applications), 'backing party EXP differs')
        require(after[i-1]['level'] >= before[i-1]['level'], 'unexpected downlevel')
        for e in events(run, 'cache_backing'):
            if e['id'] == i:
                require(e['cache'] == e['backing']['exp'] and e['backing']['checksum_ok'],
                        'native cache/backing/checksum disagreement')
        require(len([e for e in events(run, 'cache_backing') if e['id'] == i]) == len(applications),
                'missing native cache/backing application readback')
    require(order.index('captured') < order.index('calculate') < order.index('free'),
            'reward outside captured lifetime')
    require(not events(run, 'exception'), 'native CPU exception')


def ev_delta(run, slot):
    return [b-a for a, b in zip(run['before'][slot]['evs'], run['after'][slot]['evs'])]


def compare_caps(off, on, partial=False):
    validate_run(off); validate_run(on)
    require(off['before'] == on['before'], 'paired input party changed')
    require(off['flags'] ^ on['flags'] == 2, 'pair must differ only by Cap')
    def raw(run):
        return [(e['id'], e['phase'], e['raw_before'], e['native_amount'], e['native_deferred'])
                for e in events(run, 'eligible')]
    require(raw(off) == raw(on), 'caps changed native distribution/eligibility')
    native = sum(awards(off, 'apply', 1))
    require(native > 7, 'fixture did not produce enough native EXP for partial/zero contrast')
    require(sum(awards(on, 'apply', 1)) == (7 if partial else 0), 'capped fighter award incorrect')
    if partial:
        require(awards(on, 'message', 1) == [7], 'partial recipient must have real message7')
        require(on['after'][0]['exp'] == on['threshold'] and on['after'][0]['level'] == 12,
                'partial cap cache/backing level threshold mismatch')
    else:
        require(not awards(on, 'message', 1), 'zero cap emitted positive EXP message')
        require(on['after'][0]['level'] == on['before'][0]['level'], 'zero cap changed level')
    for i in (1, 2, 3):
        require(ev_delta(off, i-1) == ev_delta(on, i-1), 'cap suppressed/changed native EVs')
        if i < 3:
            require(any(v > 0 for v in ev_delta(on, i-1)), 'fighter EV positive control missing')
        if i != 1:
            require(awards(off, 'apply', i) == awards(on, 'apply', i), 'rejected EXP redistributed')
    require(sum(awards(on, 'apply', 2)) > 0, 'uncapped fighter native award missing')


def compare_share(on, off):
    validate_run(on); validate_run(off)
    require(on['before'] == off['before'] and on['flags'] ^ off['flags'] == 1, 'Share pair input mismatch')
    for i in (1, 2):
        require(awards(on, 'apply', i) == awards(off, 'apply', i), 'Share changed fighter EXP')
        require(ev_delta(on, i-1) == ev_delta(off, i-1), 'Share changed fighter EV')
    require(sum(awards(on, 'apply', 3)) > 0 and any(v > 0 for v in ev_delta(on, 2)),
            'bench Share ON positive control missing')
    require(not awards(off, 'apply', 3) and ev_delta(off, 2) == [0]*6, 'bench Share OFF grew')
    require(not [e for e in events(off, 'ev') if e['id'] == 3], 'bench Share OFF EV application executed')


def root_reuse(runs):
    """Check the whole uninterrupted trace; prove changed settings at cap12 only."""
    previous = {}
    seen_generations = set()
    previous_end = None
    observed = False
    for run in runs:
        start, snap, end = lifecycle(run)
        if previous_end is not None:
            require(start == previous_end, 'generation discontinuity between battles')
        elif start:
            seen_generations.add(start)
        for generation in (snap['epoch'], end):
            require(generation not in seen_generations, 'revived historical generation')
            seen_generations.add(generation)
        if snap['root'] in previous:
            old = previous[snap['root']]
            if snap['flags'] != old['flags']:
                observed = True
        previous[snap['root']] = snap
        previous_end = end
    return observed
