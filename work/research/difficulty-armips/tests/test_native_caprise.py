"""Synthetic sensitivity tests of continuity/award checks; never ARM evidence."""
import copy
import unittest
from unittest.mock import patch
from native_caprise_oracles import STAGES, validate, validate_boundary


class CapRiseTests(unittest.TestCase):
    @staticmethod
    def sample():
        runs=[];states={}
        def party(exp,ev,pps):
            return [dict(pid=7,species=19,exp=value,level=12 if i==0 else 8,
                         evs=[0,0,0,ev,0,0]) for i,value in enumerate(exp)]
        def state(summary,pps,badge):
            raw=bytearray(32);raw[0x1c]=badge
            mons=[dict(pid=m['pid'],speciesId=19,experience=m['exp'],checksumOk=True,flags=0,
                       moves=[dict(id=82,pp=pp[0]),dict(id=150,pp=pp[1])]) for m,pp in zip(summary,pps)]
            return dict(frame=100,save=1,party=2,bag=3,bag_raw='00',profile=4,vars=5,
                        vars_raw='00',profile_raw=raw.hex(),options_address=6,options_word=8,
                        progression=dict(badges=badge,erika=False,prewin=False,clair=False),
                        party_raw=str((summary,pps)),mons=mons)
        exp=[1728,512,512];pps=[[30,30] for _ in exp]
        for n,spec in enumerate(STAGES):
            before=party(exp,n,pps);pre=state(before,pps,n)
            native=[100,200,100];amount=[0 if n==0 else 100,200,100]
            exp=[e+a for e,a in zip(exp,amount)];pps[0][1]-=1;pps[1][0]-=1
            after=party(exp,n+1,pps);post=state(after,pps,n)
            rows=[]
            for i in (1,2,3):
                rows.extend([dict(name='ev',id=i,values=[0,0,0,0,0,1]),
                             dict(name='eligible',id=i,phase='first',native_result=1,native_deferred=0,
                                  native_amount=native[i-1],amount=amount[i-1])])
                if amount[i-1]:rows.append(dict(name='apply',id=i,amount=amount[i-1]))
            run=dict(name='cap12' if n==0 else 'cap20',before=before,after=after,
                     threshold=1728 if n==0 else 8000,events=rows)
            runs.append(run)
            if n==0:
                states['initial']=pre;states['after_first']=post
                states['after_badge']=copy.deepcopy(post)
                raw=bytearray.fromhex(post['profile_raw']);raw[0x1c]=1
                states['after_badge']['profile_raw']=raw.hex();states['after_badge']['progression']['badges']=1
            else:
                states['before_second']=pre;states['after_second']=post
        return dict(battles=runs,field_states=states)

    def test_badge_boundary_allows_only_one_bit_without_party_inventory_or_pp_reset(self):
        report=self.sample();a=report['field_states']['after_first'];b=report['field_states']['after_badge']
        validate_boundary(a,b)
        for key in ('party_raw','bag_raw','vars_raw','save','options_word','frame','mons'):
            bad=copy.deepcopy(b);bad[key]='changed'
            with self.subTest(key=key),self.assertRaises(AssertionError):validate_boundary(a,bad)
        bad=copy.deepcopy(b);raw=bytearray.fromhex(bad['profile_raw']);raw[0]=1;bad['profile_raw']=raw.hex()
        with self.assertRaises(AssertionError):validate_boundary(a,bad)

    def test_banking_redistribution_ev_loss_and_pp_reset_rejected(self):
        with patch('native_caprise_oracles.validate_readers'),patch('native_caprise_oracles.root_reuse'):
            validate(self.sample())
            for mutation in ('bank','redistribute','ev_request','ev_backing','pp_reset','party_reset',
                             'cap12_award','profile_midbattle','zero_native','missing_boundary'):
                r=self.sample();first,second=r['battles'];states=r['field_states']
                if mutation=='bank':
                    next(e for e in second['events'] if e['name']=='apply' and e['id']==1)['amount']+=100
                elif mutation=='redistribute':
                    next(e for e in first['events'] if e['name']=='apply' and e['id']==2)['amount']+=100
                elif mutation=='ev_request':first['events'][0]['values']=[0]*6
                elif mutation=='ev_backing':first['after'][0]['evs']=[0]*6
                elif mutation=='pp_reset':states['after_second']['mons'][0]['moves'][1]['pp']+=1
                elif mutation=='party_reset':states['before_second']['party_raw']='reset'
                elif mutation=='cap12_award':first['events'].append(dict(name='apply',id=1,amount=100))
                elif mutation=='profile_midbattle':states['after_second']['progression']['badges']=0
                elif mutation=='zero_native':
                    next(e for e in second['events'] if e['name']=='eligible' and e['id']==1)['native_amount']=0
                else:del states['after_badge']
                with self.subTest(mutation=mutation),self.assertRaises(AssertionError):validate(r)

    def test_no_empty_or_synthetic_trace_can_pass_real_gameplay_oracles(self):
        with self.assertRaises(AssertionError):validate(dict(battles=[]))
        with self.assertRaises((AssertionError,KeyError)):validate(self.sample())
