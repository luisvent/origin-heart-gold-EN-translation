"""Strict functional evidence composition. No driver status alone is a proof."""
import json
from pathlib import Path
from native_plan import comprehensive, identity, item_id, gate_job, doubles_job, LAYERS
from native_items_cases import ADDITIONS, BERRY_FLUTE, NO_EFFECT, CASES, usable
from support import sha256


def need(ok, message):
    if not ok:raise ValueError(message)


def item_dependencies(item, condition='positive'):
    return [item_id(item,c,m,condition) for c in CASES[item]['categories'] for m in ('all','restricted')]


CONTRACTS = {
    'items.remembered':[gate_job('remembered',i)['id'] for i in (791,65535)]+['gate-persistence-item-00017'],
    'items.doubles_slot1':[doubles_job(g,0)['id'] for g in ('accept','item','target')],
    'items.doubles_slot2':[doubles_job(g,1)['id'] for g in ('accept','item','target')],
    'items.restricted':[j for i in (17,*ADDITIONS,*BERRY_FLUTE) for j in item_dependencies(i)],
    'items.no_effect':[j for i in NO_EFFECT for j in item_dependencies(i,'no-effect')],
    'growth.no_banking':['battle','caprise','multiko'],
    'progression.skipped_decreases':['progression-skipped-koga','edges-gap','progression-plateau-81','progression-plateau-89'],
}
for item in ADDITIONS:CONTRACTS[f'items.addition_{item}']=item_dependencies(item)
for gate,key in (('accept','items.accept'),('item','items.backstop_item'),('target','items.backstop_target')):
    CONTRACTS[key]=[gate_job(gate)['id']]
for key in ('runtime.begin_free','runtime.root_reuse','growth.two_participants','growth.bench_share_on',
            'growth.bench_share_off','growth.partial_messages','growth.zero_messages'):
    CONTRACTS[key]=['battle']
for key in ('growth.caprise_no_banking','runtime.next_cap'):CONTRACTS[key]=['caprise']
for key in ('growth.multiko_participation','growth.deferred'):CONTRACTS[key]=['multiko']
for case in ('prefix','erika-prewin','erika-win','skipped-koga','plateau-81','plateau-89'):
    CONTRACTS['progression.fixture_'+case]=['progression-'+case]
for case,key in (('gap','progression.fixture_gapclosure'),('overlevel','growth.overlevel'),('curve','growth.other_curve_partial')):
    CONTRACTS[key]=['edges-'+case]
CONTRACTS['runtime.ordinary_3']=CONTRACTS['items.doubles_slot1']+CONTRACTS['items.doubles_slot2']

SPECS={j['id']:j for j in comprehensive()}
TRACE = {
    'native_exclusions.py':('exclusions-trace.json',('input_binding','local','remote')),
    'native_special.py':('special-trace.json',('battles',)),
    'native_lifecycle.py':('lifecycle-trace.json',('case','battles','inputs','allocations','destroyed_heaps','menu_owners','stack_samples')),
    'native_entries.py':('entries-trace.json',('case','battles','inputs')),
    'native_items.py':('items-trace.json',('battle','inputs','overlay_address_reuse')),
    'native_items_gates.py':('gate-trace.json',('battle','inputs','fixture')),
    'native_items_doubles.py':('doubles-trace.json',('battle','inputs','fixture')),
    'native_items_persistence.py':('persistence-trace.json',('battles','boundary','inputs','fixture')),
    'native_battle.py':('battle-trace.json',('battles','scope','inputs','overlay_address_reuse')),
    'native_progression.py':('progression-trace.json',('battle','inputs')),
    'native_caprise.py':('caprise-trace.json',('battles','field_states','inputs')),
    'native_multiko.py':('multiko-trace.json',('battles','inputs','enemy_input')),
    'native_edges.py':('edges-trace.json',('battles','case','metadata','recipient_growth','field_states','inputs')),
}


def allowed_cases(report):
    driver=report.get('driver','native_ui.py');key=identity(report)
    if driver=='native_exclusions.py':return {'growth.native_exclusions'}
    if driver=='native_special.py':return {'runtime.exclude_special'}
    if driver=='native_lifecycle.py':
        from native_lifecycle_oracles import CASES
        return {CASES[report['case']]}
    if driver=='native_entries.py':
        from native_entries_oracles import CASES
        return set(CASES[report['case']])
    if driver=='native_items.py':return {'runtime.ordinary_1'}
    if driver=='native_items_gates.py':
        from native_items_gates_oracles import GATES
        r=report['battle']
        return {GATES[r['gate']][2]} if r['fault_item']==17 and r['gate'] in GATES else set()
    if driver in ('native_items_doubles.py','native_items_persistence.py'):return set()
    return {case for case,deps in CONTRACTS.items() if deps==[key]}


def checked_artifacts(path, report):
    checked={}
    lists=[report['checkpoint_artifacts']] if 'checkpoint_artifacts' in report else []
    lists += [r['artifacts'] for r in report.get('cases',{}).values() if r.get('status')=='passed' and 'artifacts' in r]
    for rows in lists:
        seen=set()
        for row in rows:
            p=Path(row['path']).resolve()
            need(p.is_relative_to(path.parent.resolve()) and p not in seen,'foreign/duplicate artifact')
            need(p.is_file() and sha256(p)==row['sha256'],'missing/changed artifact')
            need(p not in checked or checked[p]==row['sha256'],'conflicting artifact hashes')
            seen.add(p);checked[p]=row['sha256']
    need(bool(checked),'missing hashed artifacts')
    return checked


def required_artifacts(report):
    driver=report['driver'];run=report.get('battle',{})
    names=[TRACE[driver][0]]
    if driver=='native_exclusions.py':
        for flags in (0,1):
            prefix=f'local-{flags}/'
            names += [prefix+'result.json',prefix+f'exclusions-share-{flags}-menu.png',prefix+f'exclusions-share-{flags}-finished.png']
            names += [prefix+f'share-{flags}-slot-{slot}-{phase}.bin' for slot in (3,4) for phase in ('before','after')]
            names += [prefix+folder+'/'+name for folder,level in (('egg-fixture',1),('fainted-fixture',8)) for name in ('fixture-templates.json','fixture-seed.bin',f'fixture-level-{level}.bin')]
            prefix=f'remote-{flags}/'
            names += [prefix+'result.json',prefix+'remote-growth-field.png']
            names += [prefix+f'remote-{phase}-{rid}.bin' for rid in range(7,13) for phase in ('before','after')]
        return names
    if driver=='native_special.py':
        return names+[f'special-{flags}/'+name for flags in (0,7) for name in ('native-lead.bin','native-entry-menu.png','native-special-field.png')]
    if driver=='native_lifecycle.py':
        names += ['fixture-templates.json','fixture-seed.bin']+[r['name']+'-finished.png' for r in report['battles']]
        if report['case']=='load_identity': names += ['native-saved.sav','native-reset-loader.png']
        return names
    if driver=='native_entries.py':
        names += [r['name']+'-menu.png' for r in report['battles']]
        if report['case'] in ('grass','roamer'):
            names += ['native-lead.bin']+[r['name']+'-field.png' for r in report['battles']]
        return names
    if driver.startswith('native_items'):
        names+=['items-fixture.json']
        if driver=='native_items.py':
            names+=['fixture-templates.json','fixture-seed.bin','damaged.bin','healthy.bin',
                    'enemy-native-before.bin','trainer-launch-diagnostic.json','trainer-menu.png',
                    'bag-categories.png','returned-menu.png']
            if usable(run):
                names+=['party-targets.png','party-selected.png']
                if CASES[run['item']]['kind']=='pp-one':names+=['move-choices.png','move-selected.png']
        elif driver=='native_items_gates.py':
            names+=['fixture-templates.json','fixture-seed.bin','damaged.bin','healthy.bin','enemy-native-before.bin',
                    'trainer-launch-diagnostic.json','trainer-menu.png','bag-categories.png','denied-menu.png','continued-menu.png']
            if run['gate']=='remembered':names+=['remembered-cleared.png']
            if run['gate']=='target':names+=['party-targets.png','bag-reopened.png']
        elif driver=='native_items_doubles.py':
            names+=['trainer-launch-diagnostic.json','double-first-menu.png','double-second-pending.png',
                    'double-denied.png','double-continued.png']
            if run['gate']=='target':names+=['double-party-targets.png','double-bag-reopened.png']
        else:
            names+=['persistence-enemy.bin','damaged.bin','enemy-native-before.bin']
            names += [n+'.png' for n in ('first-menu','first-potion-used','field-after-ko','field-restricted',
                                        'second-menu','second-bag','second-returned')]
    else:
        names+=['fixture-templates.json','fixture-seed.bin']
        names += [r['name']+'-finished.png' for r in report.get('battles',[run])]
        if driver=='native_caprise.py':names+=['badge-only-boundary.png']
        if driver=='native_multiko.py':names+=['enemy-input.bin','enemy-input.json','native-style-set-draft.png']
        if driver=='native_edges.py' and report['case']=='gap':names+=['gap-badge-only.png']
        if driver=='native_edges.py' and report['case']=='overlevel':
            names+=['level100/'+n for n in ('fixture-templates.json','fixture-seed.bin','fixture-level-100.bin')]
    return names


def rerun_oracle(report, path=None):
    driver=report['driver']
    if driver=='native_exclusions.py':
        from native_exclusions_oracles import validate_report
        need(path is not None,'recipient exclusion oracle requires raw native artifacts')
        validate_report(report,Path(path).parent)
    elif driver=='native_special.py':
        from native_special_oracles import validate
        need(path is not None,'special oracle requires native record artifacts')
        validate(report['battles'],Path(path).parent)
    elif driver=='native_lifecycle.py':
        from native_lifecycle_oracles import validate
        validate(report, Path(path).parent if path is not None else None)
    elif driver=='native_entries.py':
        from native_entries_oracles import validate
        validate(report)
    elif driver=='native_items.py':
        from native_items_oracles import checkpoint
        need(report['battle'].get('checkpoint')=='passed','unfinished item checkpoint')
        checkpoint(report['battle'])
    elif driver=='native_items_gates.py':
        if report['battle']['gate']=='remembered':
            from native_items_remembered import continued
        else:
            from native_items_gates_oracles import continued
        continued(report['battle'])
    elif driver=='native_items_doubles.py':
        from native_items_doubles import validate
        validate(report['battle'])
    elif driver=='native_items_persistence.py':
        from native_items_persistence import validate
        validate(report)
    elif driver=='native_progression.py':
        from native_progression_oracles import validate
        validate(report['battle'])
    elif driver=='native_caprise.py':
        from native_caprise_oracles import validate
        validate(report)
    elif driver=='native_edges.py':
        from native_edges_oracles import validate
        validate(report)
    elif driver=='native_multiko.py':
        from native_multiko_oracles import validate_matrix
        validate_matrix(report['battles'])
    elif driver=='native_battle.py':
        from native_battle_oracles import validate_run, compare_caps, compare_share, root_reuse
        rows=report['battles'];scope=report['scope']
        names=['zero-off','zero-on']+(['share-off-cap-off','share-off-cap-on','partial-off','partial-on'] if scope=='matrix' else [])
        need(scope in ('pair','matrix') and [r['name'] for r in rows]==names,'incomplete/foreign battle matrix')
        for r in rows:validate_run(r)
        compare_caps(*rows[:2])
        if scope=='matrix':
            compare_caps(*rows[2:4]);compare_share(rows[0],rows[2]);compare_share(rows[1],rows[3])
            compare_caps(*rows[4:],partial=True)
        root_reuse(rows)


def validate_slice(path,binding,expected=None):
    path=Path(path).resolve();r=json.loads(path.read_text())
    p=json.loads((path.parent/'process.json').read_text())
    need(bool(binding) and r.get('binding')==binding,'stale slice binding')
    need(r.get('status')==p.get('status')=='passed' and p.get('returncode')==0 and
         bool(p.get('finished_utc')) and bool(r.get('finished_utc')),'nonterminal/nonpassing slice')
    need(bool(r.get('nonce')) and r['nonce']==p.get('nonce'),'stale slice nonce')
    driver=r.get('driver','native_ui.py')
    need(driver in LAYERS and r.get('layer')==LAYERS[driver] and r.get('old_state_loaded') is False,'foreign driver/layer/state')
    key=identity(r)
    if expected:
        need(expected['status']=='passed' and key==expected['id'] and driver==expected['driver'] and
             r['layer']==expected['layer'] and r['nonce']==expected['nonce'] and
             p.get('invocation')==expected['invocation'] and p.get('job_id')==key,'not this invocation/job/attempt')
    if driver=='native_ui.py':
        checked_artifacts(path,r)
        if r.get('page_navigation'):
            from native_ui_oracles import validate_page_navigation
            trace=json.loads((path.parent/'ui.page_navigation.trace.json').read_text())
            need(trace.get('page_navigation')==r['page_navigation'],'navigation report/trace disagreement')
            validate_page_navigation(r['page_navigation'])
        return r
    need(key in SPECS and SPECS[key]['driver']==driver,'wrong slice identity')
    for case,row in r.get('cases',{}).items():
        need(row.get('status')!='failed','actual failed case: '+case)
        if row.get('status')=='passed':need(case in allowed_cases(r),'slice claimed wrong case: '+case)
    checked=checked_artifacts(path,r)
    for name in required_artifacts(r):need((path.parent/name).resolve() in checked,'missing required artifact: '+name)
    trace=json.loads((path.parent/TRACE[driver][0]).read_text())
    need(trace.get('binding')==binding,'trace binding differs')
    for field in TRACE[driver][1]:
        need(field in r and field in trace and r[field]==trace[field],'report/trace disagreement: '+field)
    if driver=='native_entries.py' and r['case']=='roamer':
        need(r.get('roamer_fixture')==trace.get('roamer_fixture') and r.get('roamer_fixture') is not None,'roamer fixture/report disagreement')
    if driver.startswith('native_items'):
        fixture=json.loads((path.parent/'items-fixture.json').read_text())
        need(fixture==r['fixture'],'fixture/report disagreement')
    # Referenced before/after binary observations are evidence too, not loose paths.
    def visit(value):
        if isinstance(value,dict):
            for k,v in value.items():
                if k in ('before_path','after_path'):need(Path(v).resolve() in checked,'unhashed/foreign referenced input')
                else:visit(v)
        elif isinstance(value,list):
            for v in value:visit(v)
    visit(trace)
    rerun_oracle(r,path)
    return r


def frozen_snapshots(reports):
    """Observed battle snapshots only; no claim about changing setup18C or scripts."""
    from native_battle_oracles import events
    for report in reports:
        for run in report.get('battles',[report.get('battle')]):
            cap=events(run,'captured');need(len(cap)==1,'missing frozen capture')
            snap=cap[0]['snapshot'];active=False;observed=0
            for e in run['events']:
                if e['name']=='captured':active=True
                if active and 'snapshot' in e:
                    need(e['snapshot']==snap,'snapshot changed within battle');observed+=1
                if e['name']=='free':active=False
            need(observed>=3 and not active,'incomplete frozen snapshot observations')


def compose(manifest,paths,binding,expected=None):
    """Use every required current constituent exactly once; diagnostics aren't vetoes."""
    rows={};errors={};global_errors=[];nonces=set();seen_paths=set();case_failures=set()
    for value in paths:
        path=Path(value).resolve();key=None
        try:
            need(path not in seen_paths,'duplicate report path');seen_paths.add(path)
            if expected is not None:
                need(str(path) in expected,'foreign invocation report');key=expected[str(path)]['id']
            if not path.exists():raise ValueError('missing constituent report')
            raw=json.loads(path.read_text());key=key or identity(raw)
            if raw.get('binding')==binding:
                case_failures.update(k for k,v in raw.get('cases',{}).items() if v.get('status')=='failed')
            need(key not in rows and key not in errors,'duplicate constituent')
            r=validate_slice(path,binding,expected.get(str(path)) if expected is not None else None)
            need(r['nonce'] not in nonces,'duplicate process nonce');nonces.add(r['nonce'])
            rows[key]=(r,path)
        except (ValueError,KeyError,OSError,AssertionError,TypeError,IndexError) as exc:
            if key:errors[key]=str(exc)
            else:global_errors.append(str(exc))
    results={}
    for definition in manifest['cases']:
        case=definition['id']
        if case not in CONTRACTS or not definition.get('driver'):continue
        deps=CONTRACTS[case]
        try:
            need(case not in case_failures,'current failed composite declaration')
            need(not global_errors,'malformed/duplicate report inventory: '+'; '.join(global_errors))
            for dep in deps:
                need(dep not in errors,dep+': '+errors.get(dep,''))
                need(dep in rows,'missing constituent: '+dep)
            reports=[rows[d][0] for d in deps]
            if case=='growth.no_banking' or case in ('growth.bench_share_off','growth.partial_messages'):
                need(rows['battle'][0]['scope']=='matrix','six-battle Share/Cap/partial matrix required')
            if case=='runtime.root_reuse':
                from native_battle_oracles import root_reuse
                need(root_reuse(reports[0]['battles']),'same root with changed settings not observed')
            if case in ('growth.no_banking','progression.skipped_decreases'):
                frozen_snapshots(reports)
            if case.startswith('items.addition_') or case in ('items.restricted','items.no_effect'):
                from native_items_evidence import compare_inputs
                grouped={}
                for r in reports:grouped.setdefault((r['battle']['item'],r['battle'].get('condition','positive')),[]).append(r)
                for group in grouped.values():
                    for r in group[1:]:compare_inputs(group[0],r)
            results[case]=dict(status='passed',proof_layer='composed native observations',
                constituents=[dict(job=d,report=str(rows[d][1]),nonce=rows[d][0]['nonce']) for d in deps])
        except (ValueError,KeyError,OSError,AssertionError,TypeError,IndexError) as exc:
            results[case]=dict(status='incomplete',reason=str(exc),required_constituents=deps)
    return results
