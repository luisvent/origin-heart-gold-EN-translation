"""Doubles pending-action oracle regressions; no native execution."""
from copy import deepcopy
import unittest
from support import scratch
from test_native_items import sample
from native_items_cases import GATE_ITEM

GATE_BYTES=GATE_ITEM.to_bytes(2,'little')+b'\0'
from native_items_doubles import validate, validate_denial, selected_command
from native_items_gates_oracles import GATES
from native_items_gates_matrix import plan_doubles, plan, report_paths


def evidence(gate='item',slot=1):
    r=sample(False);r['gate']=gate;r['fault_slot']=slot;r['options']=dict(after=0x200)
    r['events']=[e for e in r['events'] if e['name'] in ('constructor','captured','begin')]
    for e in r['events']:
        if e['name']=='constructor':e['flags']=3
        if e['name']=='captured':e['context']['flags']=3
    r['events'].append(dict(name='double_fixture',frame=10))
    r['before']['mons']['14']=dict(deepcopy(r['before']['mons']['13']),id=14,address=9000)
    root=r['before']['snapshot']['root']
    def bind(slot,rid):
        engine=deepcopy(r['before']['mons'][str(rid)]);ui=engine['address']+0x10000
        command=dict(controller=100,owner=0,slot=slot,slot_count=2,actor_id=rid,actor=ui,destination=2000+slot*12,command='00'*12)
        return dict(root=root,view=root+0x54,roster=root+0x60,ui=ui,engine=engine['address'],id=rid,command=command,
            ui_state=dict(engine,address=ui),engine_state=engine,hashes=['a'*64,'a'*64],backing=[4000,5000])
    a,b=bind(0,1),bind(1,2);r['first_actor']=a;r['second_actor']=b
    for binding in (a,b):r['events'].append(dict(name='controller_actor_lookup',view=binding['view'],owner=0,
        slot=binding['command']['slot'],result=binding['ui']))
    encoded=(1+(150<<8)).to_bytes(4,'little').hex()+'0000000001000000'
    def pair(binding,frame):
        command=binding['command'];dest=command['destination']
        return [dict(name='move_command',move=150,target_position=slot,destination=dest,command=deepcopy(command),
            encoded=((1+(150<<8)+(slot<<4)).to_bytes(4,'little').hex()+'00000000'+binding['id'].to_bytes(4,'little').hex()),
            target_bindings=[] if phase=='preliminary' else [dict(name='position_resolver',
                view=binding['view'],position=slot,result=binding['ui'],frame=frame)],
            frame=frame+i,lr=lr,callsite=site,callsite_bytes=raw,encoder_phase=phase)
            for i,(slot,lr,site,raw,phase) in enumerate(((5,0x0221200B,0x02212006,'eef7abfc','preliminary'),
                (2*command['slot'],0x02212673,0x0221266E,'eef777f9','selected')))]
    first_pair=pair(a,12);r['events']+=first_pair;r['first_command']=deepcopy(first_pair[-1])
    pending=dict(destination=2000,bytes=encoded);r['pending_initial']=deepcopy(pending)
    raw=bytearray(0x30);raw[0x1a]=4;changed=bytearray(raw);changed[0x18:0x1b]=GATE_BYTES
    r['events'].append(dict(name='double_fault',kind='nativeFaultInput',gate=gate,frame=20,target=None,binding=deepcopy(b),before=raw.hex(),after=changed.hex(),
        registers_before=[0]*16,registers_after=[0]*16,result=0,args_after=dict(item=0,category=4),
        command_before=deepcopy(b['command']),command_after=deepcopy(b['command']),command_return=deepcopy(b['command']),
        pending_before=deepcopy(pending),pending_after=deepcopy(pending),pending_return=deepcopy(pending)))
    r['events'] += [dict(name='lists',frame=15,lists=[[],[dict(item=151,quantity=3)],[],[]]),
                     dict(name='schedule',frame=22,handler=0x02202445)]
    r['queued']=deepcopy(r['before']);r['denied']=deepcopy(r['before']);r['command_denied']=deepcopy(b['command'])
    r['pending_denied']=deepcopy(pending);r['denied_event_count']=len(r['events'])
    r['events']+=pair(b,30)
    r['after']=deepcopy(r['denied'])
    for rid in (1,2,13,14):
        r['events'].append(dict(name='action',actor=dict(id=rid),move=150))
        r['after']['mons'][str(rid)]['pp'][0]-=1;r['after']['mons'][str(rid)]['original_pp'][0]-=1
    fault=next(e for e in r['events'] if e['name']=='double_fault')
    if slot==0:
        # First pair is submitted only AFTER denial; there is no pending other command.
        r['events']=[e for e in r['events'] if e not in first_pair]
        r['denied_event_count']-=2
        for e in first_pair:e['frame']+=20
        r['events'][r['denied_event_count']:r['denied_event_count']]=first_pair
        r['first_command']=deepcopy(first_pair[-1])
        pending=dict(state='not_yet_selected',slot=1)
        r['pending_initial']=deepcopy(pending);r['pending_denied']=deepcopy(pending)
        for key in ('pending_before','pending_after','pending_return'):fault[key]=deepcopy(pending)
        for key in ('command_before','command_after','command_return'):fault[key]=deepcopy(a['command'])
        fault['binding']=deepcopy(a);r['command_denied']=deepcopy(a['command'])
    if gate!='item':
        raw=bytearray.fromhex(fault['before']);raw[0x18:0x1b]=b'\x97\x00\x01'
        fault['before']=raw.hex();raw[0x18:0x1b]=GATE_BYTES;fault['after']=raw.hex()
        fault['result']=GATES[gate][1]
    if gate=='target':
        actor=a if slot==0 else b;fault['target']=slot;r['selected_ui_slot']=slot
        entries=[dict(ui_slot=i,id=x['id'],mon=x['ui'],backing=x['backing'][0],
            source_sha256=x['hashes'][0],copy_sha256=x['hashes'][0],hp=x['ui_state']['hp'],maxhp=x['ui_state']['maxhp'])
            for i,x in enumerate((a,b))]
        r['party_mapping']=dict(controller=actor['command']['controller'],count=2,entries=entries)
        reopen=dict(name='lists',frame=21,lists=[[],[dict(item=151,quantity=3)],[],[]])
        r['reopened_list']=deepcopy(reopen)
        added=[dict(name='accept',after=dict(item=151)),dict(name='commit_item',result=151),reopen]
        r['events'][r['denied_event_count']:r['denied_event_count']]=added;r['denied_event_count']+=len(added)
    return r


class DoublesTests(unittest.TestCase):
    def test_whole_continuation_removed_is_only_a_denial_checkpoint(self):
        for gate in GATES:
            for slot in (0,1):
                r=evidence(gate,slot)
                del r['after']
                r['events']=r['events'][:r['denied_event_count']]
                with self.subTest(gate=gate,slot=slot):
                    validate_denial(r)
                    with self.assertRaisesRegex(AssertionError,'continuation/readback'):
                        validate(r)

    def test_distinct_local_slots_keep_pending_first_action(self):
        r=evidence();validate(r)
        # Native target bookkeeping may finalize after move encoder returns.
        # Snapshot the real queued command; require its move identity and stability.
        pending=dict(r['pending_initial'],bytes=r['pending_initial']['bytes'][:8]+'01000000'+'01000000')
        r['pending_initial']=deepcopy(pending);r['pending_denied']=deepcopy(pending)
        fault=next(e for e in r['events'] if e['name']=='double_fault')
        for key in ('pending_before','pending_after','pending_return'):fault[key]=deepcopy(pending)
        validate(r)

    def test_adversarial_pending_owner_input_turn_and_registry_changes_fail(self):
        for mutation in ('flags','owner','same_actor','slot','view','backing','lookup','pending','input','register',
                         'result','command','early_turn','early_slot','extra_turn','lost_second','hp','bag'):
            r=evidence();f=next(e for e in r['events'] if e['name']=='double_fault')
            if mutation=='flags':next(e for e in r['events'] if e['name']=='captured')['context']['flags']=1
            elif mutation=='owner':r['second_actor']['command']['owner']=1
            elif mutation=='same_actor':r['second_actor']['id']=1
            elif mutation=='slot':r['second_actor']['command']['slot']=0
            elif mutation=='view':r['second_actor']['view']+=4
            elif mutation=='backing':r['second_actor']['hashes'][0]='b'*64
            elif mutation=='lookup':next(e for e in r['events'] if e['name']=='controller_actor_lookup')['result']+=4
            elif mutation=='pending':r['pending_denied']['bytes']='00'*12
            elif mutation=='input':
                raw=bytearray.fromhex(f['after']);raw[0x1b]=1;f['after']=raw.hex()
            elif mutation=='register':f['registers_after'][0]=0
            elif mutation=='result':f['result']=GATE_ITEM
            elif mutation=='command':r['command_denied']['destination']+=12
            elif mutation in ('early_turn','early_slot'):
                r['events'].insert(0,dict(name='action' if mutation=='early_turn' else 'slot_advance'));r['denied_event_count']+=1
            elif mutation=='extra_turn':r['events'].append(dict(name='action',actor=dict(id=1),move=150))
            elif mutation=='lost_second':r['events']=[e for e in r['events'] if not(e['name']=='action' and e['actor']['id']==2)]
            elif mutation=='hp':r['after']['mons']['1']['hp']+=1
            else:r['denied']['quantity']=2
            if mutation=='register':f['registers_after'][0]=13
            with self.subTest(mutation=mutation),self.assertRaises(AssertionError):validate(r)

    def test_native_preliminary_selector5_is_not_a_duplicate_action_or_final_choice(self):
        r=evidence();a=r['first_actor'];rows=[e for e in r['events'] if e['name']=='move_command' and e['command']['actor_id']==a['id']]
        self.assertEqual(selected_command(rows,a),rows[1])
        for mutation in ('reverse','missing','duplicate','lr','bytes','destination','actor','slot','mapping','missing_mapping','wrong_view','output'):
            bad=deepcopy(rows)
            if mutation=='reverse':bad.reverse()
            elif mutation=='missing':bad=bad[1:]
            elif mutation=='duplicate':bad.append(deepcopy(bad[-1]))
            elif mutation=='lr':bad[0]['lr']=bad[1]['lr']
            elif mutation=='bytes':bad[1]['callsite_bytes']='00000000'
            elif mutation=='destination':bad[0]['destination']+=12
            elif mutation=='actor':bad[1]['command']['actor_id']=2
            elif mutation=='slot':bad[1]['target_position']=5
            elif mutation=='mapping':bad[1]['target_bindings'][0]['result']+=4
            elif mutation=='missing_mapping':bad[1]['target_bindings']=[]
            elif mutation=='wrong_view':bad[1]['target_bindings'][0]['view']+=4
            else:bad[1]['encoded']='00'*12
            with self.subTest(mutation=mutation),self.assertRaises(AssertionError):selected_command(bad,a)

    def test_second_actor_target_position2_requires_native_self_mapping(self):
        r=evidence();b=r['second_actor']
        rows=[e for e in r['events'] if e['name']=='move_command' and e['command']['actor_id']==b['id']]
        self.assertEqual(selected_command(rows,b)['target_position'],2)
        # A syntactically valid position0 command is still the wrong actor.
        rows[1]['target_position']=0
        raw=bytearray.fromhex(rows[1]['encoded']);raw[0]=1;rows[1]['encoded']=raw.hex()
        with self.assertRaises(AssertionError):selected_command(rows,b)

    def test_all_gates_both_slots_and_honest_pending_state(self):
        for gate in GATES:
            for slot in (0,1):
                with self.subTest(gate=gate,slot=slot):validate(evidence(gate,slot))
        for mutation in ('pending_claim','early_selection','wrong_gate','wrong_return','wrong_input',
                         'missing_reopen','wrong_target','copy','allowed_use','post_denial_turn'):
            r=evidence('target',0);f=next(e for e in r['events'] if e['name']=='double_fault')
            if mutation=='pending_claim':r['pending_initial']=dict(destination=123,bytes='00'*12)
            elif mutation=='early_selection':
                r['events'].insert(0,dict(name='local_actor_selected',command=dict(slot=1)));r['denied_event_count']+=1
            elif mutation=='wrong_gate':f['gate']='accept'
            elif mutation=='wrong_return':f['result']=13
            elif mutation=='wrong_input':f['before']='00'*48
            elif mutation=='missing_reopen':r['reopened_list']['frame']=0
            elif mutation=='wrong_target':f['target']=1
            elif mutation=='copy':r['party_mapping']['entries'][0]['copy_sha256']='b'*64
            elif mutation=='allowed_use':next(e for e in r['events'] if e['name']=='commit_item')['result']=0
            else:r['after']['mons']['1']['pp'][0]+=1
            with self.subTest(mutation=mutation),self.assertRaises(AssertionError):validate(r)

    def test_six_jobs_retain_distinct_gate_slot_evidence_and_prior_runs(self):
        with scratch('doubles-matrix-') as tmp:
            first=plan_doubles(tmp,full=True);second=plan_doubles(tmp,full=True)
            self.assertEqual({(j['double_gate'],j['slot']) for j in first},{(g,s) for g in GATES for s in (0,1)})
            self.assertEqual(len(first),6);self.assertEqual(len(report_paths(tmp)),6)
            self.assertTrue(set(j['out'] for j in first).isdisjoint(j['out'] for j in second))
            self.assertTrue(all((j['out']/'result.json').exists() for j in first+second))

    def test_one_doubles_job_is_isolated_from_singles_gate_index(self):
        with scratch('doubles-index-') as tmp:
            plan(tmp);first=plan_doubles(tmp);second=plan_doubles(tmp)
            self.assertEqual(len(first),1);self.assertTrue(first[0]['doubles'])
            self.assertNotEqual(first[0]['out'],second[0]['out'])
            self.assertEqual(len(report_paths(tmp)),4)
            self.assertTrue((first[0]['out']/'result.json').exists())


if __name__=='__main__':unittest.main()
