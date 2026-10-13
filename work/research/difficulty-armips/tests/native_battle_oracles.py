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
    slots = run.get('slots', 3); holders = set(run.get('holders', ()))
    require(len(before) == len(after) == slots, 'fixture must retain all party slots')
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
    # Scripted WildBattle: constructor flags0/control0, caller ORs control 8 before entry.
    # Script TrainerBattle (singles): flags1/control0 from the trainer constructor.
    kind = run.get('kind', 'wild')
    # The trainer constructor (02050C34) is called from 020507A8 in the Chinese code (return address 020507AD) and, with the
    # enabled double-battle-single-fallback fix, from its wrapper at 02048EEA (return address 02048EEF): the same call sequence.
    lr, cflags, ccontrol = {'wild': ((0x02050433,), 0, 8), 'trainer': ((0x020507AD, 0x02048EEF), 1, 0)}[kind]
    require(len(constructors) == 1 and constructors[0]['setup'] == ctx['setup'] and
            constructors[0]['flags'] == cflags and constructors[0]['control'] == 0,
            'real ordinary setup constructor missing')
    require(constructors[0]['lr'] in lr and ctx['flags'] == cflags and
            ctx['control'] == ccontrol and ctx['save'] == ctx['published_save'],
            f'actual {kind} caller/save identity mismatch')
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
    require({e['id'] for e in calculations} >= set(range(1, slots+1)), 'native roster calculation incomplete')
    share = events(run, 'share')
    # SHARE OFF keeps the native share only for a recipient holding Exp. Share.
    require(share and all(e['result'] == (0 if run['flags'] & 1 and e.get('id') not in holders else 1) for e in share),
            'installed native share wrapper not observed or wrong result')
    require({e.get('id') for e in share} >= set(range(3, slots+1)),
            'share wrapper must be observed for every benched recipient')
    elig = events(run, 'eligible')
    require({e['id'] for e in elig if e['phase'] == 'first'} >= set(range(1, slots+1)),
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
    for i in range(1, slots+1):
        ev = [e for e in events(run, 'ev') if e['id'] == i]
        require(len(ev) == (0 if i >= 3 and i not in holders and run['flags'] & 1 else 1), 'native EV eligibility mismatch')
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
    for i in range(1, off.get('slots', 3)+1):
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


def bench_gain(run):
    """(EXP gain, EV gain list) of the bench slot (party index 2) of one completed run."""
    return (run['after'][2]['exp'] - run['before'][2]['exp'], ev_delta(run, 2))


def holder_verdict(runs, expect='fixed'):
    """Exp. Share holder vs non-holder bench under SHARE OFF/ON and CAP OFF/ON.

    `runs` maps a name to a completed run; every run has one bench slot (party
    index 2) that either holds an Exp. Share (run['bench_item'] == 216) or not.
    expect='fixed': SHARE OFF still shares with the holder (same EXP and EVs as
    SHARE ON, CAP clamp applied), never with the non-holder.
    expect='baseline': the rc7 behaviour (SHARE OFF shares with nobody).
    Returns the list of failed checks (empty when all hold) and the gains table.
    """
    gains = {name: bench_gain(run) for name, run in runs.items()}
    failed = []
    def check(ok, text):
        if not ok: failed.append(text)
    on = gains.get('share-on-holder')
    check(on is not None and on[0] > 3 and any(v > 0 for v in on[1]), 'SHARE ON holder control gets no EXP/EV')
    off_h, off_n = gains.get('share-off-holder'), gains.get('share-off-plain')
    check(off_n == (0, [0]*6), 'SHARE OFF non-holder bench received EXP or EVs')
    if expect == 'fixed':
        check(off_h == on, 'SHARE OFF holder does not get the SHARE ON EXP and EVs')
        cap_h, cap_n = gains.get('share-off-cap-holder'), gains.get('share-off-cap-plain')
        check(cap_h is not None and cap_h[0] == 3 and cap_h[1] == off_h[1],
              'CAP did not clamp the holder to the cap threshold (3 EXP) with unchanged EVs')
        check(cap_n == (0, [0]*6), 'CAP + SHARE OFF non-holder received EXP or EVs')
    else:
        check(off_h == (0, [0]*6), 'baseline: SHARE OFF holder unexpectedly shares')
    return failed, gains


def validate_double(run):
    """Doubles (script TrainerBattle 6,6, setup flags 3): lifecycle, snapshot and per-recipient wrapper results.

    Reward accounting is outcome based (party EXP/EV before/after plus the final
    per-recipient amounts): two KOs in one turn are accumulated by the engine
    before its EXP passes, so the single-KO per-event ledger of validate_run
    does not apply.
    """
    before, after = run['before'], run['after']
    slots = len(before)
    require(slots == len(after) == 3, 'doubles fixture must retain three party slots')
    for mon in before + after:
        require(mon['checksum_ok'] and not mon['bad_egg'], 'invalid party checksum/egg')
    holders = set(run.get('holders', ()))
    begin, captured = events(run, 'begin'), events(run, 'captured')
    free, original_free = events(run, 'free'), events(run, 'original_free')
    require(len(begin) == len(captured) == len(free) == len(original_free) == 1,
            'need exactly one installed begin/capture/free/original free')
    snap, ctx = captured[0]['snapshot'], captured[0]['context']
    require(snap['allowed'] == 1 and snap['epoch'] > 0 and snap['cap'] == run.get('expected_cap', 12) and
            snap['flags'] == run['flags'], 'doubles snapshot missing/wrong settings')
    constructors = events(run, 'constructor')
    require(len(constructors) == 1 and constructors[0]['flags'] == 3 and constructors[0]['control'] == 0 and
            constructors[0]['lr'] in (0x020507AD, 0x02048EEF) and ctx['flags'] == 3 and ctx['control'] == 0 and
            ctx['setup'] == constructors[0]['setup'] and ctx['save'] == ctx['published_save'],
            'doubles setup is not flags3/control0 from the trainer constructor')
    require(run['final_snapshot'] == original_free[0]['snapshot'] == dict(flags=0, cap=0, allowed=0, root=0, epoch=0),
            'snapshot not invalidated at teardown')
    require(not events(run, 'exception'), 'native CPU exception')
    fixture = events(run, 'opponent_hp_fixture')
    require(len(fixture) == 1 and fixture[0]['phase']['begin_observed'] is False and
            [e['name'] for e in run['events']].index('opponent_hp_fixture') < [e['name'] for e in run['events']].index('begin'),
            'enemy HP fixture not prepared before battle entry')
    calcs = events(run, 'calculate')
    require(len(calcs) >= 2 * slots and {e['id'] for e in calcs} == set(range(1, slots+1)) and
            all(e['opponent_hp'] == 0 for e in calcs), 'expected one reward calculation per recipient per defeated foe')
    require(all(set(e['participants']) == {1, 2} for e in calcs), 'both local actives must be the participants')
    share = events(run, 'share')
    require(len(share) == len(calcs), 'one share wrapper call per calculation')
    for e in share:
        want = 0 if run['flags'] & 1 and e['id'] not in holders else 1
        require(e['result'] == want and e['arg_id'] in (None, e['id']), f"share result for recipient {e['id']}: {e['result']} != {want}")
    for e in events(run, 'eligible'):
        require(e['raw_before'] == e['raw_after'] and e['native_deferred'] == e['deferred'] and
                e['native_result'] == e['result'], 'late wrapper changed raw reward/deferred/result')
        if e['native_amount'] and run['flags'] & 2:
            want = min(e['native_amount'], max(0, e['threshold'] - e['cache_before']))
        else:
            want = e['native_amount']
        require(e['amount'] == want, 'wrong final recipient amount')
    for i in (1, 2, 3):
        gained = after[i-1]['exp'] - before[i-1]['exp']
        applied = sum(awards(run, 'apply', i))
        require(gained == applied, f'slot{i}: party EXP gain {gained} != applied {applied}')
    require(after[0]['exp'] > before[0]['exp'] or run['flags'] & 2, 'fighter1 positive control missing')
    require(any(v > 0 for v in ev_delta(run, 1)), 'fighter2 EV positive control missing')
