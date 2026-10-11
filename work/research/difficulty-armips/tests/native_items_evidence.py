"""Accept an addition only from both supervised, source-bound effect slices."""
import json
from pathlib import Path
from support import sha256
from native_items_oracles import checkpoint
from native_items_cases import CASES, category_for


def validate_item_pair(paths, binding, item, condition="positive"):
    try:
        rows = {}
        for path in map(Path, paths):
            if not path.exists():continue
            report = json.loads(path.read_text())
            if report.get('driver') != 'native_items.py' or report.get('battle',{}).get('item') != item:continue
            if report['battle'].get('condition','positive') != condition:continue
            process = json.loads((path.parent/'process.json').read_text())
            if report.get('status') != 'passed' or process.get('status') != 'passed':raise ValueError('nonpassing item slice')
            if report.get('binding') != binding or not binding:raise ValueError('stale item binding')
            if not report.get('nonce') or report['nonce'] != process.get('nonce'):raise ValueError('stale item nonce')
            if report.get('old_state_loaded') is not False or report.get('layer') != 'native ARM gameplay items':raise ValueError('not fresh native ITEMS execution')
            artifacts = report.get('checkpoint_artifacts',[])
            if not artifacts:raise ValueError('missing item checkpoint artifacts')
            checked = set()
            for a in artifacts:
                target = Path(a['path']).resolve()
                if not target.is_relative_to(path.parent.resolve()) or sha256(target) != a['sha256']:raise ValueError('changed/outside item artifact')
                checked.add(target)
            for name in ('items-trace.json','items-fixture.json','trainer-menu.png','bag-categories.png','returned-menu.png'):
                if (path.parent/name).resolve() not in checked:raise ValueError('missing required item artifact')
            trace = json.loads((path.parent/'items-trace.json').read_text())
            fixture = json.loads((path.parent/'items-fixture.json').read_text())
            if trace['binding'] != binding or trace['battle'] != report['battle'] or fixture != report['fixture']:raise ValueError('item report/artifact mismatch')
            run = report['battle']
            if fixture.get('condition','positive') != condition:raise ValueError('wrong item fixture condition')
            if run.get('checkpoint') != 'passed':raise ValueError('unfinished item checkpoint')
            checkpoint(run)
            mode = run['name']
            key = (category_for(run),mode)
            if mode not in ('all','restricted') or key in rows or run['flags'] != (4 if mode == 'all' else 0):raise ValueError('wrong/duplicate item mode')
            rows[key] = (report,path)
        expected = {(c,m) for c in CASES[item]['categories'] for m in ('all','restricted')}
        if set(rows) != expected:raise ValueError('need ALL/restricted pair for every item list location')
        reports = [rows[key][0] for key in sorted(expected)]
        a = reports[0]
        for b in reports[1:]:
            compare_inputs(a,b)
        if len({r['nonce'] for r in reports}) != len(reports):raise ValueError('reused item process nonce')
        return dict(status='passed', reports=[str(rows[k][1]) for k in sorted(expected)])
    except (ValueError,KeyError,OSError,AssertionError,TypeError) as exc:
        return dict(status='incomplete',reason=str(exc))


def compare_inputs(a,b):
    if not a.get('items_pair') or a['items_pair'] != b.get('items_pair'):
        raise ValueError('item slices from different pair invocations')
    if a['fixture'].get('condition','positive') != b['fixture'].get('condition','positive'):
        raise ValueError('item fixture condition mismatch')
    for key in ('candidate_sha256','source_battery_sha256','input_battery_sha256','trainer_id',
                'trainer_sha256','enemy_record_sha256','item','payload','splash','target_slot','ui_slot','move_slot'):
        if a['fixture'][key] != b['fixture'][key]:raise ValueError('item fixture mismatch: '+key)
    if [r['sha256'] for r in a['fixture']['records']] != [r['sha256'] for r in b['fixture']['records']]:
        raise ValueError('item party fixture mismatch')


def validate_antidote_pair(paths,binding):
    return validate_item_pair(paths,binding,18)


def validate_no_effect(paths,binding):
    from native_items_cases import NO_EFFECT
    results={str(item):validate_item_pair(paths,binding,item,'no-effect') for item in NO_EFFECT}
    return dict(status='passed' if all(r['status']=='passed' for r in results.values()) else 'incomplete',
                slices=results,scope='HP/status/PP/living-injured revival; both settings, strict native outcomes')
