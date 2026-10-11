"""Composite sensitivity and complete denial continuation; no native execution."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from composite_fixtures import BINDING, report_for, write_report
from native_composites import CONTRACTS
from evidence import validate_native, write_json
from support import scratch, sha256, SOURCE


def manifest(*cases):return dict(cases=[dict(id=k,driver='composite') for k in cases])


class CompositeTests(unittest.TestCase):
    def test_shipping_manifest_enables_existing_composite_contracts(self):
        shipping=json.loads((SOURCE/'tests/required_native.json').read_text())
        cases={r['id']:r for r in shipping['cases']}
        for case in CONTRACTS:
            self.assertTrue(cases[case]['driver'], case)
        case='items.doubles_slot1'
        paths=self.reports(case)
        self.assertEqual(validate_native(shipping,paths,BINDING)[case]['status'],'passed')
        self.assertNotEqual(validate_native(shipping,paths[:-1],BINDING)[case]['status'],'passed')

    def setUp(self):
        self.temp=scratch('composite-host-');self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)

    def reports(self,case):
        return [write_report(self.root/key,report_for(key)) for key in CONTRACTS[case]]

    def status(self,case,paths):
        return validate_native(manifest(case),paths,BINDING)[case]

    def test_remembered_requires_both_invalid_ids_and_authentic_two_battle_continuation(self):
        case='items.remembered';paths=self.reports(case)
        self.assertEqual(self.status(case,paths)['status'],'passed')
        for i in range(3):self.assertNotEqual(self.status(case,paths[:i]+paths[i+1:])['status'],'passed')
        r=report_for(CONTRACTS[case][0]);r['battle']['events'].insert(0,dict(name='fault_metadata'))
        r['battle']['denied_event_count']+=1;write_report(paths[0].parent,r)
        self.assertNotEqual(self.status(case,paths)['status'],'passed')
        paths=self.reports(case);r=report_for(CONTRACTS[case][-1]);r['battles'].pop()
        write_report(paths[-1].parent,r)
        self.assertNotEqual(self.status(case,paths)['status'],'passed')

    def test_all_six_doubles_gate_slots_require_whole_continuation(self):
        for case in ('items.doubles_slot1','items.doubles_slot2','runtime.ordinary_3'):
            paths=self.reports(case);self.assertEqual(self.status(case,paths)['status'],'passed')
            for i,key in enumerate(CONTRACTS[case]):
                self.assertNotEqual(self.status(case,paths[:i]+paths[i+1:])['status'],'passed')
                r=report_for(key);run=r['battle'];del run['after'];run['events']=run['events'][:run['denied_event_count']]
                write_report(paths[i].parent,r)
                self.assertNotEqual(self.status(case,paths)['status'],'passed')
                write_report(paths[i].parent,report_for(key))

    def test_restricted_needs_every_negative_and_hp_status_pp_flute_positive(self):
        case='items.restricted';paths=self.reports(case)
        self.assertEqual(self.status(case,paths)['status'],'passed')
        for i in range(len(paths)):
            with self.subTest(missing=paths[i].parent.name):
                self.assertNotEqual(self.status(case,paths[:i]+paths[i+1:])['status'],'passed')
        for key in ('item-155-category-0-restricted','item-151-category-1-restricted',
                    'item-154-category-0-restricted','item-065-category-1-restricted'):
            r=report_for(key);r['battle']['after']=deepcopy(r['battle']['before'])
            write_report(self.root/key,r)
            self.assertNotEqual(self.status(case,paths)['status'],'passed')
            write_report(self.root/key,report_for(key))

    def test_current_revival_additions_require_attributes_and_exactly_one_native_hp_add(self):
        for item in (28,29,37):
            case=f'items.addition_{item}';paths=self.reports(case)
            self.assertEqual(self.status(case,paths)['status'],'passed')
            key=CONTRACTS[case][0];r=report_for(key)
            r['battle']['events']=[e for e in r['battle']['events'] if e['name']!='effect_attr']
            write_report(paths[0].parent,r)
            self.assertNotEqual(self.status(case,paths)['status'],'passed')

    def test_no_effect_requires_all_four_current_pairs(self):
        case='items.no_effect';paths=self.reports(case)
        self.assertEqual(self.status(case,paths)['status'],'passed')
        for i in range(len(paths)):
            self.assertNotEqual(self.status(case,paths[:i]+paths[i+1:])['status'],'passed')

    def test_diagnostic_incomplete_does_not_veto_but_real_failed_does(self):
        case='items.doubles_slot2';paths=self.reports(case);key=CONTRACTS[case][0]
        for state,want in (('incomplete','passed'),('failed','incomplete')):
            r=report_for(key);r['cases'][case]=dict(status=state,reason='diagnostic scope')
            write_report(paths[0].parent,r)
            self.assertEqual(self.status(case,paths)['status'],want)

    def test_every_constituent_is_terminal_bound_hashed_and_replayed(self):
        case='items.doubles_slot2';paths=self.reports(case);path=paths[-1];key=CONTRACTS[case][-1]
        mutations=('binding','nonce','process_failed','process_running','process_unfinished','exit_code',
                   'report_failed','report_unfinished','driver','layer','old_state','missing_artifacts','missing_required',
                   'duplicate_artifact','foreign_artifact','changed_artifact','trace_disagrees','trace_binding',
                   'wrong_case','wrong_slot','missing_after','truncated_report','truncated_trace','missing_process')
        for mutation in mutations:
            write_report(path.parent,report_for(key));r=json.loads(path.read_text());pp=path.parent/'process.json';p=json.loads(pp.read_text())
            if mutation=='binding':r['binding']={'stale':True}
            elif mutation=='nonce':p['nonce']='old'
            elif mutation=='process_failed':p['status']='failed'
            elif mutation=='process_running':p['status']='running'
            elif mutation=='process_unfinished':del p['finished_utc']
            elif mutation=='exit_code':p['returncode']=7
            elif mutation=='report_failed':r['status']='failed'
            elif mutation=='report_unfinished':del r['finished_utc']
            elif mutation=='driver':r['driver']='native_items.py'
            elif mutation=='layer':r['layer']='host model'
            elif mutation=='old_state':r['old_state_loaded']=True
            elif mutation=='missing_artifacts':r['checkpoint_artifacts']=[]
            elif mutation=='missing_required':r['checkpoint_artifacts'].pop()
            elif mutation=='duplicate_artifact':r['checkpoint_artifacts'].append(r['checkpoint_artifacts'][0])
            elif mutation=='foreign_artifact':r['checkpoint_artifacts'].append(dict(path=str(paths[0]),sha256=sha256(paths[0])))
            elif mutation=='changed_artifact':(path.parent/'double-continued.png').write_bytes(b'changed')
            elif mutation in ('trace_disagrees','trace_binding'):
                tp=path.parent/'doubles-trace.json';t=json.loads(tp.read_text())
                if mutation=='trace_disagrees':t['battle']['after']['quantity']-=1
                else:t['binding']={}
                write_json(tp,t);r['checkpoint_artifacts'][0]['sha256']=sha256(tp)
            elif mutation=='wrong_case':r['cases']['growth.no_banking']=dict(status='passed',artifacts=r['checkpoint_artifacts'])
            elif mutation=='wrong_slot':r['battle']['fault_slot']=0
            elif mutation=='missing_after':del r['battle']['after']
            write_json(path,r);write_json(pp,p)
            if mutation=='truncated_report':path.write_text('{')
            if mutation=='truncated_trace':(path.parent/'doubles-trace.json').write_text('{')
            if mutation=='missing_process':pp.unlink()
            with self.subTest(mutation=mutation):self.assertNotEqual(self.status(case,paths)['status'],'passed')
        self.reports(case)
        for values in (paths+paths[:1],paths+[write_report(self.root/'duplicate',report_for(CONTRACTS[case][0]))]):
            self.assertNotEqual(self.status(case,values)['status'],'passed')

    def test_growth_composition_requires_distinct_jobs_oracles_matrix_and_frozen_snapshot(self):
        # Isolate composition from the already separately tested growth oracles.
        # Even these well-enveloped synthetic reports fail WITHOUT the patch.
        for case in ('growth.no_banking','progression.skipped_decreases'):
            paths=self.reports(case)
            self.assertNotEqual(self.status(case,paths)['status'],'passed')
            with patch('native_composites.rerun_oracle') as oracle:
                self.assertEqual(self.status(case,paths)['status'],'passed')
                self.assertEqual(oracle.call_count,len(paths))
                for i in range(len(paths)):
                    self.assertNotEqual(self.status(case,paths[:i]+paths[i+1:])['status'],'passed')
                r=report_for(CONTRACTS[case][0]);run=r.get('battles',[r.get('battle')])[0]
                run['events'][1]['snapshot']['cap']+=1
                write_report(paths[0].parent,r)
                self.assertNotEqual(self.status(case,paths)['status'],'passed')
            if case=='growth.no_banking':
                r=report_for('battle');r['scope']='pair';r['battles']=r['battles'][:2];write_report(paths[0].parent,r)
                with patch('native_composites.rerun_oracle'):
                    self.assertNotEqual(self.status(case,paths)['status'],'passed')

    def test_failed_current_duplicate_cannot_hide_behind_good_constituent(self):
        case='items.doubles_slot1';paths=self.reports(case);r=report_for(CONTRACTS[case][0]);r['status']='failed'
        failed=write_report(self.root/'failed',r)
        for values in (paths+[failed],[failed]+paths):self.assertNotEqual(self.status(case,values)['status'],'passed')
