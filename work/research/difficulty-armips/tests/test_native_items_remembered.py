"""Remembered malformed-input oracles and retained-job coverage, no emulator."""
import unittest
from support import scratch
from native_items_cases import GATE_ITEM
from native_plan import PERSISTENCE_ID
from test_native_items_gates import gate_sample
from native_items_remembered import continued
from native_items_gates_matrix import plan, plan_remembered, report_paths


def sample(item):
    r=gate_sample('accept',item);r['gate']='remembered'
    e=next(x for x in r['events'] if x['name']=='fault_input')
    old=bytearray(0x30);old[0x1b]=1 # exercise native remembered category clearing
    injected=bytearray(old);injected[0x1c:0x1e]=item.to_bytes(2,'little')
    returned=bytearray(old);returned[0x1b]=0
    e.update(name='remembered_fault_input',seam=0x021EC250,ui=0x02270000,
        before=old.hex(),after=injected.hex(),returned=returned.hex(),result=0,
        args_after=dict(remembered=0))
    wrappers=dict(name='remembered_wrapper_input',item=item,quantity=1,result=0,ui=e['ui'],
        bag=r['before']['bag_address'],args=dict(address=e['address'],remembered=item,owner=0,tutorial=0))
    for x in r['events']:
        if x['name']=='lists':x['args']=dict(remembered=0)
    r['events'].insert(0,wrappers);r['denied_event_count']+=1
    return r


class RememberedTests(unittest.TestCase):
    def test_invalid_remembered_ids_clear_natively_then_continue(self):
        for item in (791,65535):continued(sample(item))

    def test_no_metadata_count_output_forcing_or_partial_clear_can_pass(self):
        for item in (791,65535):
            for mutation in ('count','metadata','register','extra_write','forced_result','category','item',
                             'wrapper_item','wrapper_ui','wrapper_bag','turn','inventory','state','slot','later_effect'):
                r=sample(item);e=next(x for x in r['events'] if x['name']=='remembered_fault_input')
                w=next(x for x in r['events'] if x['name']=='remembered_wrapper_input')
                if mutation in ('count','metadata','turn'):
                    r['events'].insert(0,dict(name={'count':'fault_count','metadata':'fault_metadata','turn':'action'}[mutation]))
                    r['denied_event_count']+=1
                elif mutation=='register':e['registers_after'][0]+=1
                elif mutation=='extra_write':
                    raw=bytearray.fromhex(e['after']);raw[0x18]=GATE_ITEM;e['after']=raw.hex()
                elif mutation=='forced_result':
                    raw=bytearray.fromhex(e['after']);raw[0x1c:0x1e]=bytes(2);e['after']=raw.hex()
                elif mutation in ('category','item'):
                    raw=bytearray.fromhex(e['returned']);raw[0x1b if mutation=='category' else 0x1c]=1;e['returned']=raw.hex()
                elif mutation.startswith('wrapper_'):w[mutation.removeprefix('wrapper_')]+=1
                elif mutation=='inventory':r['denied']['quantity']=2
                elif mutation=='state':r['after']['mons']['1']['hp']+=1
                elif mutation=='slot':r['command_denied']['slot']=1
                else:r['events'].append(dict(name='effect'))
                with self.subTest(item=item,mutation=mutation),self.assertRaises(AssertionError):continued(r)

    def test_remembered_jobs_are_distinct_and_cannot_replace_potion_gate_results(self):
        with scratch('remembered-jobs-') as tmp:
            gates=plan(tmp);remembered=plan_remembered(tmp)
            self.assertEqual({j['fault_item'] for j in remembered},{791,65535})
            self.assertEqual(len(report_paths(tmp)),5)
            again=plan_remembered(tmp)
            self.assertEqual(len(report_paths(tmp)),5)
            self.assertTrue(all((j['out']/'result.json').exists() for j in gates+remembered))
            self.assertTrue(all(a['out']!=b['out'] for a,b in zip(remembered,again)))
        # Complete composition requires both invalid-ID diagnostics AND the
        # authentic two-battle remembered-item persistence continuation.
        import json
        from support import SOURCE
        manifest=json.loads((SOURCE/'tests/required_native.json').read_text())
        from native_composites import CONTRACTS
        from evidence import validate_native
        self.assertEqual(next(c for c in manifest['cases'] if c['id']=='items.remembered')['driver'],
                         'native_composites.py')
        self.assertEqual(len(CONTRACTS['items.remembered']),3)
        self.assertIn(PERSISTENCE_ID,CONTRACTS['items.remembered'])
        self.assertNotEqual(validate_native(manifest,[],{})['items.remembered']['status'],'passed')


if __name__=='__main__':unittest.main()
