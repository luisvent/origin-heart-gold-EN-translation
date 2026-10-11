"""Invocation-owned sequential execution, durable inventory and bounded retries."""
import json
from pathlib import Path
import sys
import uuid
from evidence import write_json, utc, bound_process
from support import OUTPUT, SOURCE


def inventory(suite):
    jobs=suite['jobs']
    return dict(planned=[j['id'] for j in jobs],
                completed=[j['id'] for j in jobs if j['status']=='passed'],
                failed=[j['id'] for j in jobs if j['status'] in ('failed','interrupted')],
                unstarted=[j['id'] for j in jobs if j['status']=='unstarted'],
                running=[j['id'] for j in jobs if j['status']=='running'])


def save(suite, path):
    suite['inventory']=inventory(suite)
    write_json(path,suite)


def create(jobs, binding, host, *, root=None):
    nonce=uuid.uuid4().hex
    root=Path(root or OUTPUT/'native-suites'/nonce).resolve()
    if not root.is_relative_to(OUTPUT):raise ValueError('suite outside owned output')
    suite=dict(format=1,invocation=nonce,binding=binding,host_static=host,started_utc=utc(),
               root=str(root),jobs=[dict(j,status='unstarted',attempts=[]) for j in jobs])
    path=root/'invocation.json';save(suite,path)
    return suite,path


def resume(path, binding):
    path=Path(path).resolve()
    if not path.is_relative_to(OUTPUT):raise ValueError('suite outside owned output')
    suite=json.loads(path.read_text())
    if suite['format']!=1 or suite['binding']!=binding or not binding:
        raise ValueError('retry requires exact unchanged binding')
    if Path(suite['root']).resolve()!=path.parent:raise ValueError('foreign suite root')
    if not suite['host_static']['success']:raise ValueError('suite host checks did not pass')
    for j in suite['jobs']:
        if j['status']=='running':
            j['status']='interrupted';j['attempts'][-1]['status']='interrupted'
    save(suite,path)
    return suite


def evidence_selection(suite):
    """Only the latest attempt of each planned job; never scan old directories."""
    paths=[];expected={}
    for j in suite['jobs']:
        if not j['attempts']:continue
        a=j['attempts'][-1];p=Path(a['out'])/'result.json'
        paths.append(p)
        expected[str(p.resolve())]=dict(id=j['id'],driver=j['driver'],layer=j['layer'],
            nonce=a['nonce'],invocation=suite['invocation'],status=j['status'])
    return paths,expected


def execute(suite, path, timeout, retry_jobs=None, *, supervisor=bound_process, validator=None):
    from native_composites import validate_slice
    validator=validator or validate_slice
    jobs={j['id']:j for j in suite['jobs']}
    selected=list(retry_jobs) if retry_jobs is not None else [j['id'] for j in suite['jobs'] if j['status']!='passed']
    if len(selected)!=len(set(selected)) or any(i not in jobs or jobs[i]['status']=='passed' for i in selected):
        raise ValueError('retry selects unknown, duplicate or already completed jobs')
    suite['selected_jobs']=selected;save(suite,path)
    for j in suite['jobs']:
        if j['id'] not in selected:continue
        if any(jobs[d]['status']!='passed' for d in j['dependencies']):
            j['reason']='prerequisite not completed';save(suite,path);break
        nonce=uuid.uuid4().hex
        out=Path(suite['root'])/'attempts'/nonce/j['id']
        argv=[sys.executable,str(SOURCE/'tests'/j['driver']),*j['args'],'--out',str(out)]
        a=dict(nonce=nonce,out=str(out),argv=argv,status='running',started_utc=utc())
        j['attempts'].append(a);j['status']='running';j.pop('reason',None)
        save(suite,path)  # durable before spawn, even if the parent is killed
        write_json(out/'result.json',dict(status='interrupted',nonce=nonce,cases={},reason='invocation pending'))
        env={'DG_ITEMS_PAIR':suite['invocation']}
        for dependency,var in (('ui','DG_UI_OUT'),('reload','DG_RELOAD_OUT')):
            if dependency in j['dependencies']:env[var]=jobs[dependency]['attempts'][-1]['out']
        try:
            process=supervisor(argv,out,120 if j['id'] in ('reload','cold0','newgame') else timeout,
                env=env,nonce=nonce,invocation=suite['invocation'],job_id=j['id'])
            a['process']=process
            if process['status']!='passed':raise ValueError('supervisor '+process['status']+': '+process.get('reason','child failure'))
            validator(out/'result.json',suite['binding'],expected=dict(id=j['id'],driver=j['driver'],layer=j['layer'],
                nonce=nonce,invocation=suite['invocation'],status='passed'))
            a['status']=j['status']='passed'
        except KeyboardInterrupt:
            a['status']=j['status']='interrupted';j['reason']='parent interrupted'
        except Exception as exc:
            a['status']=j['status']='failed';j['reason']=str(exc)
        finally:
            a['finished_utc']=utc();save(suite,path)
        if j['status']!='passed':break
    suite['finished_utc']=utc();save(suite,path)
    return all(j['status']=='passed' for j in suite['jobs'])
