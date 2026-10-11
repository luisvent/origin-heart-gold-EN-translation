"""Durable sequential job planning; no emulator construction or subprocesses."""
import json
import uuid
from pathlib import Path
from evidence import write_json
from native_items_cases import CASES, HP_STATUS, PP_REVIVE, PP_ONLY, BERRY_FLUTE, ADDITIONS, NO_EFFECT


def variants(scope, item):
    items = {'single':(item,), 'hp-status':HP_STATUS, 'pp-revive-checkpoint':(38,28),
             'pp-revive':PP_REVIVE, 'pp-only':PP_ONLY, 'berry-flute-checkpoint':(151,65),
             'berry-flute':BERRY_FLUTE, 'oran-leppa':(155,154), 'no-effect':NO_EFFECT, 'all-additions':(17,*ADDITIONS)}[scope]
    return [(i,c) for i in items for c in CASES[i]['categories']]


def plan(root, scope, item):
    """Never reuse a run directory. Invalidate selected index entries pre-spawn.

    Unselected cases can accumulate under identical global source binding. The
    validator still rejects every older source, nonce or partial paired run.
    """
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    invocation=uuid.uuid4().hex
    index_path=root/'latest.json'
    index=json.loads(index_path.read_text()) if index_path.exists() else dict(format=1,cases={})
    jobs=[]
    selected_variants=variants(scope,item)
    for item,category in selected_variants:
        condition='no-effect' if scope=='no-effect' else 'positive'
        key=f'item-{item:03d}-category-{category}'+('-no-effect' if condition=='no-effect' else '')
        paths=[]
        for mode in ('all','restricted'):
            out=root/'runs'/invocation/key/mode
            out.mkdir(parents=True,exist_ok=False)
            write_json(out/'result.json',dict(status='interrupted',cases={},reason='planned invocation pending'))
            jobs.append(dict(name=f'{key}-{mode}',item=item,category=category,condition=condition,mode=mode,
                             out=out,pair=invocation))
            paths.append(str((out/'result.json').resolve()))
        index['cases'][key]=paths
    write_json(index_path,index)
    return jobs


def report_paths(root):
    root=Path(root).resolve();index_path=root/'latest.json'
    if not index_path.exists():return []
    index=json.loads(index_path.read_text());paths=[]
    if index.get('format') != 1:raise ValueError('unsupported ITEMS index')
    for key,values in index['cases'].items():
        if len(values) != 2:raise ValueError('ITEMS index needs both modes')
        for value in values:
            path=Path(value).resolve()
            if not path.is_relative_to(root/'runs') or path.name != 'result.json' or path.parent.parent.name != key:
                raise ValueError('ITEMS index path outside owned case')
            paths.append(path)
    if len(set(paths)) != len(paths):raise ValueError('duplicate ITEMS indexed report')
    return paths
