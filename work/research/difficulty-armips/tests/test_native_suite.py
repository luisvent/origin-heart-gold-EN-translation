"""Pure inventory and fake-supervisor invocation tests; never starts an emulator."""
import json
from pathlib import Path
import types
import unittest
from unittest.mock import patch
from native_plan import comprehensive, selected
from native_suite import create, execute, resume, evidence_selection, inventory
from evidence import write_json, validate_native
from support import scratch, SOURCE


class SuiteTests(unittest.TestCase):
    def test_comprehensive_inventory_deterministic_and_every_implemented_selector_present(self):
        a=comprehensive();self.assertEqual(a,comprehensive());self.assertEqual(len(a),102)
        self.assertEqual(len({j['id'] for j in a}),102)
        self.assertIn('entries-roamer',{j['id'] for j in a})
        self.assertIn('excluded-special',{j['id'] for j in a})
        self.assertIn('growth-exclusions',{j['id'] for j in a})
        drivers={j['driver'] for j in a}
        self.assertEqual(len(drivers),14)
        self.assertEqual(a[4]['args'],['--scope','matrix'])
        self.assertEqual(sum(j['driver']=='native_progression.py' for j in a),6)
        self.assertEqual(sum(j['driver']=='native_items_doubles.py' for j in a),6)
        self.assertEqual(sum(j['driver']=='native_edges.py' for j in a),3)
        full_restore=[j for j in a if j['id'].startswith('item-023')]
        self.assertEqual(len(full_restore),4)
        self.assertEqual(sum(j['driver']=='native_items.py' for j in a),60)
        self.assertEqual(sum(j['id'].startswith('gate-remembered-') for j in a),2)
        positions={j['id']:i for i,j in enumerate(a)}
        for i,j in enumerate(a):self.assertTrue(all(positions[d]<i for d in j['dependencies']))

    def test_targeted_modes_remain_bounded_and_pure(self):
        a=types.SimpleNamespace(native_plan='targeted',native_phase='items',items_scope='remembered-invalid')
        self.assertEqual(len(selected(a)),2)
        a.items_scope='doubles-checkpoint';self.assertEqual(len(selected(a)),1)
        a.items_scope='doubles-gates';self.assertEqual(len(selected(a)),6)
        a.native_phase='battle';a.battle_scope='edges';a.edge_cases=['curve','curve']
        self.assertEqual([j['id'] for j in selected(a)],['edges-curve'])
        with patch('pathlib.Path.mkdir',side_effect=AssertionError('dry planner wrote files')):
            comprehensive();selected(a)

    def test_fail_stop_inventory_and_retry_do_not_import_old_passes(self):
        with scratch('suite-host-') as tmp:
            root=Path(tmp);binding={'unchanged':True};jobs=comprehensive()[:4]
            suite,path=create(jobs,binding,{'success':True},root=root/'suite')
            calls=[];failed={'reload'}
            def supervisor(argv,out,timeout,env,nonce,invocation,job_id):
                calls.append((job_id,nonce,dict(env)))
                p=dict(status='failed' if job_id in failed else 'passed',nonce=nonce,returncode=7 if job_id in failed else 0,
                       finished_utc='host fake',invocation=invocation,job_id=job_id)
                write_json(out/'process.json',p)
                write_json(out/'result.json',dict(status=p['status'],nonce=nonce,binding=binding,cases={}))
                return p
            checked=[]
            def validator(p,binding,expected):checked.append((p,expected))
            self.assertFalse(execute(suite,path,30,supervisor=supervisor,validator=validator))
            self.assertEqual(inventory(suite)['completed'],['ui'])
            self.assertEqual(inventory(suite)['failed'],['reload'])
            self.assertEqual(inventory(suite)['unstarted'],['cold0','newgame'])
            paths,expected=evidence_selection(suite)
            self.assertEqual(len(paths),2)
            # An old passed job exists nearby, but is never selected by the suite.
            old=root/'old/cold0/result.json';write_json(old,dict(status='passed',binding=binding,cases={'ui.title_textspeed':dict(status='passed')}))
            self.assertNotIn(old,paths)
            self.assertNotEqual(validate_native(dict(cases=[dict(id='ui.title_textspeed',driver='native_ui.py')]),paths,binding,expected)['ui.title_textspeed']['status'],'passed')
            with self.assertRaisesRegex(ValueError,'unchanged binding'):resume(path,{'changed':True})
            failed.clear();suite=resume(path,binding)
            self.assertFalse(execute(suite,path,30,['reload'],supervisor=supervisor,validator=validator))
            self.assertEqual(inventory(suite)['unstarted'],['cold0','newgame'])
            self.assertTrue(execute(suite,path,30,supervisor=supervisor,validator=validator))
            self.assertEqual([c[0] for c in calls],['ui','reload','reload','cold0','newgame'])
            self.assertEqual(len({c[1] for c in calls}),len(calls))
            self.assertEqual(len(suite['jobs'][1]['attempts']),2)
            paths,expected=evidence_selection(suite)
            self.assertEqual(len(paths),4)
            self.assertNotIn(Path(suite['jobs'][1]['attempts'][0]['out'])/'result.json',paths)
            self.assertEqual(calls[3][2]['DG_UI_OUT'],suite['jobs'][0]['attempts'][0]['out'])
            self.assertEqual(calls[3][2]['DG_RELOAD_OUT'],suite['jobs'][1]['attempts'][-1]['out'])
            with self.assertRaises(ValueError):execute(suite,path,30,['ui'],supervisor=supervisor,validator=validator)

    def test_zero_exit_with_bad_oracle_is_failed_and_later_jobs_unstarted(self):
        with scratch('suite-invalid-') as tmp:
            suite,path=create(comprehensive()[:3],{'b':1},{'success':True},root=Path(tmp))
            def supervisor(*args,**kw):return {'status':'passed','nonce':kw['nonce']}
            def reject(*a,**kw):raise AssertionError('truncated observations')
            self.assertFalse(execute(suite,path,30,supervisor=supervisor,validator=reject))
            self.assertEqual(inventory(suite)['failed'],['ui'])
            self.assertEqual(inventory(suite)['unstarted'],['reload','cold0'])
            suite['jobs'][0]['status']='running';write_json(path,suite)
            self.assertEqual(resume(path,{'b':1})['jobs'][0]['status'],'interrupted')

    def test_invocation_nonce_and_job_identity_checked_even_when_report_and_supervisor_agree(self):
        from composite_fixtures import report_for,write_report,BINDING
        from native_composites import validate_slice
        key='gate-doubles-item-slot1-item-00017'
        with scratch('suite-nonce-') as tmp:
            p=write_report(Path(tmp),report_for(key),invocation='selected')
            expected=dict(id=key,driver='native_items_doubles.py',layer='native ARM gameplay doubles diagnostic',
                          nonce=key,invocation='selected',status='passed')
            validate_slice(p,BINDING,expected)
            for field,value in (('nonce','old'),('invocation','other'),('id','other'),('status','unstarted'),('driver','native_items.py')):
                with self.subTest(field=field),self.assertRaises(ValueError):validate_slice(p,BINDING,dict(expected,**{field:value}))

    def test_manifest_keeps_history_and_requires_two_page_navigation(self):
        m=json.loads((SOURCE/'tests/required_native.json').read_text())
        self.assertEqual(len(m['cases']),79)
        self.assertEqual([r['id'] for r in m['user_excluded_native']],['runtime.exclude_link'])
        self.assertEqual(m['user_excluded_native'][0]['decision'],'D-2330')
        self.assertEqual(next(r for r in m['cases'] if r['id']=='ui.page_navigation')['driver'],'native_ui.py')
        for r in m['cases']:
            for k in ('requirement','risk','proof_layers','exclusions'):self.assertIn(k,r)
        for key in ('runtime.load_identity','runtime.arena'):
            self.assertEqual(next(r for r in m['cases'] if r['id']==key)['driver'],'native_lifecycle.py')
        self.assertEqual(next(r for r in m['cases'] if r['id']=='growth.native_exclusions')['driver'],'native_exclusions.py')
        for key in ('runtime.frozen_control',
                    'items.contexts','items.reopen_pagination','runtime.exclude_replay','runtime.exclude_facility','progression.erika_routes'):
            self.assertIsNone(next(r for r in m['cases'] if r['id']==key)['driver'])
