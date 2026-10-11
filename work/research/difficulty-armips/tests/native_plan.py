"""Pure deterministic job inventory; no filesystem writes or emulator imports."""
from native_items_cases import CASES, ADDITIONS, BERRY_FLUTE, NO_EFFECT, HP_STATUS, PP_REVIVE, PP_ONLY
from native_progression_cases import CASES as PROGRESSION

LAYERS = {
    'native_exclusions.py': 'native ARM gameplay recipient exclusions',
    'native_special.py': 'native ARM gameplay excluded special context',
    'native_lifecycle.py': 'native ARM gameplay lifecycle',
    'native_entries.py': 'native ARM gameplay entry constructors',
    'native_ui.py': 'native ARM gameplay UI',
    'native_battle.py': 'native ARM gameplay battle',
    'native_progression.py': 'native ARM gameplay progression',
    'native_caprise.py': 'native ARM gameplay cap rise',
    'native_multiko.py': 'native ARM gameplay multiple KOs',
    'native_edges.py': 'native ARM gameplay growth edges',
    'native_items.py': 'native ARM gameplay items',
    'native_items_gates.py': 'native ARM gameplay item gates',
    'native_items_doubles.py': 'native ARM gameplay doubles diagnostic',
    'native_items_persistence.py': 'native ARM gameplay remembered persistence',
}
GATES = ('accept', 'item', 'target')


def job(name, driver, *args, dependencies=()):
    return dict(id=name, driver=driver, layer=LAYERS[driver], args=list(map(str,args)),
                dependencies=list(dependencies))


def item_id(item, category, mode, condition='positive'):
    return f'item-{item:03d}-category-{category}'+('-no-effect' if condition=='no-effect' else '')+'-'+mode


def item_jobs(items, condition='positive'):
    return [job(item_id(i,c,m,condition),'native_items.py','--item',i,'--category',c,
                '--mode',m,'--condition',condition)
            for i in items for c in CASES[i]['categories'] for m in ('all','restricted')]


def gate_job(gate, item=17):
    return job(f'gate-{gate}-item-{item:05d}','native_items_gates.py','--gate',gate,'--fault-item',item)


def doubles_job(gate, slot):
    return job(f'gate-doubles-{gate}-slot{slot}-item-00017','native_items_doubles.py','--gate',gate,'--slot',slot)


def ui_jobs():
    return [job('ui','native_ui.py','--phase','ui'),
            job('reload','native_ui.py','--phase','reload',dependencies=('ui',)),
            job('cold0','native_ui.py','--phase','cold0',dependencies=('ui','reload')),
            job('newgame','native_ui.py','--phase','newgame',dependencies=('ui',))]


def progression_jobs():
    return [job('progression-'+case,'native_progression.py','--case',case) for case in PROGRESSION]


def edge_jobs(cases=('gap','overlevel','curve')):
    return [job('edges-'+case,'native_edges.py','--case',case) for case in dict.fromkeys(cases)]


def comprehensive():
    jobs = ui_jobs()+[job('battle','native_battle.py','--scope','matrix')]+progression_jobs()
    jobs += [job('entries-'+case,'native_entries.py','--case',case) for case in ('grass','trainer13','trainer4b','roamer')]
    jobs += [job('lifecycle-'+case,'native_lifecycle.py','--case',case) for case in ('arena','load_identity')]
    jobs += [job('caprise','native_caprise.py'),job('multiko','native_multiko.py')]+edge_jobs()
    jobs += [job('excluded-special','native_special.py'),job('growth-exclusions','native_exclusions.py')]
    jobs += item_jobs((17,*ADDITIONS))+item_jobs(BERRY_FLUTE)+item_jobs(NO_EFFECT,'no-effect')
    jobs += [gate_job(g) for g in GATES]+[gate_job('remembered',i) for i in (791,65535)]
    # Also retain the driver's implemented invalid selected-item selectors;
    # these diagnostics never replace real Potion or remembered-ID coverage.
    jobs += [gate_job(g,i) for i in (791,65535) for g in GATES]
    jobs += [job('gate-persistence-item-00017','native_items_persistence.py')]
    jobs += [doubles_job(g,s) for s in (0,1) for g in GATES]
    assert len(jobs)==len({j['id'] for j in jobs})
    return jobs


def selected(args):
    if args.native_plan=='comprehensive':return comprehensive()
    phases=('ui','battle','items') if args.native_phase=='all' else (args.native_phase,)
    jobs=[]
    for phase in phases:
        if phase=='ui':jobs += ui_jobs()
        elif phase=='battle':
            scope=args.battle_scope
            if scope in ('pair','matrix'):
                jobs.append(job('battle','native_battle.py','--scope',scope))
                if args.native_phase=='all':
                    jobs += progression_jobs()+[job('caprise','native_caprise.py'),job('multiko','native_multiko.py')]+edge_jobs()
            elif scope=='progression':jobs += progression_jobs()
            elif scope=='edges':jobs += edge_jobs(args.edge_cases)
            else:jobs.append(job(scope,'native_'+scope+'.py'))
        else:
            scope=args.items_scope
            if scope=='gates':jobs += [gate_job(g,args.items_gate_item) for g in GATES]
            elif scope=='remembered-invalid':jobs += [gate_job('remembered',i) for i in (791,65535)]
            elif scope=='remembered-persistence':jobs.append(job('gate-persistence-item-00017','native_items_persistence.py'))
            elif scope.startswith('doubles-'):
                jobs += ([doubles_job(g,s) for s in (0,1) for g in GATES] if scope=='doubles-gates' else [doubles_job('item',1)])
            else:
                items={'single':(args.items_item,), 'hp-status':HP_STATUS,'pp-revive-checkpoint':(38,28),
                       'pp-revive':PP_REVIVE,'pp-only':PP_ONLY,'berry-flute-checkpoint':(151,65),
                       'berry-flute':BERRY_FLUTE,'oran-leppa':(155,154),'no-effect':NO_EFFECT,
                       'all-additions':(17,*ADDITIONS)}[scope]
                jobs += item_jobs(items,'no-effect' if scope=='no-effect' else 'positive')
    return jobs


def identity(report):
    """Derive a slice identity from content, never a claimed case or filename."""
    driver=report.get('driver','native_ui.py')
    if driver=='native_exclusions.py':return 'growth-exclusions'
    if driver=='native_special.py':return 'excluded-special'
    if driver=='native_lifecycle.py':return 'lifecycle-'+report['case']
    if driver=='native_entries.py':return 'entries-'+report['case']
    if driver=='native_ui.py':return report.get('phase','ui')
    if driver=='native_battle.py':return 'battle'
    if driver=='native_caprise.py':return 'caprise'
    if driver=='native_multiko.py':return 'multiko'
    if driver=='native_edges.py':return 'edges-'+report['case']
    if driver=='native_progression.py':return 'progression-'+report['battle']['name']
    if driver=='native_items_persistence.py':return 'gate-persistence-item-00017'
    r=report['battle']
    if driver=='native_items.py':return item_id(r['item'],r['category'],r['name'],r.get('condition','positive'))
    if driver=='native_items_gates.py':return f"gate-{r['gate']}-item-{r['fault_item']:05d}"
    if driver=='native_items_doubles.py':return f"gate-doubles-{r['gate']}-slot{r['fault_slot']}-item-{r['fault_item']:05d}"
    raise ValueError('unknown native slice driver')
