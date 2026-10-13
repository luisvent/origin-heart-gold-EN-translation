"""Unique, independently retained singles gate jobs; no native execution here."""
import json
import uuid
from pathlib import Path
from evidence import write_json
from native_items_gates_oracles import GATES
from native_items_cases import GATE_ITEM


def plan(root,item=GATE_ITEM):
    return _plan(root,[(gate,item) for gate in GATES])


def plan_remembered(root):
    return _plan(root,[('remembered',item) for item in (791,65535)])


def plan_persistence(root):
    jobs=_plan(root,[('persistence',GATE_ITEM)])
    for job in jobs:job['persistence']=True
    return jobs


def plan_doubles(root,full=False):
    specs=[(gate,slot) for slot in (0,1) for gate in GATES] if full else [('item',1)]
    jobs=_plan(root,[(f'doubles-{gate}-slot{slot}',GATE_ITEM) for gate,slot in specs])
    for job,(gate,slot) in zip(jobs,specs):job.update(doubles=True,double_gate=gate,slot=slot)
    return jobs


def _plan(root,specs):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    invocation=uuid.uuid4().hex;path=root/'latest.json'
    index=json.loads(path.read_text()) if path.exists() else dict(format=1,cases={})
    jobs=[]
    for gate,item in specs:
        key=f'gate-{gate}-item-{item:05d}';out=root/'runs'/invocation/key
        out.mkdir(parents=True,exist_ok=False)
        write_json(out/'result.json',dict(status='interrupted',cases={},reason='planned gate pending'))
        index['cases'][key]=str((out/'result.json').resolve())
        jobs.append(dict(name=key,out=out,gate=gate,fault_item=item))
    write_json(path,index);return jobs


def report_paths(root):
    root=Path(root).resolve();index=root/'latest.json'
    if not index.exists():return []
    data=json.loads(index.read_text());paths=[]
    if data.get('format')!=1:raise ValueError('unsupported gate index')
    for key,value in data['cases'].items():
        p=Path(value).resolve()
        if not p.is_relative_to(root/'runs') or p.name!='result.json' or p.parent.name!=key:
            raise ValueError('gate index path outside owned case')
        paths.append(p)
    if len(set(paths))!=len(paths):raise ValueError('duplicate gate path')
    return paths
