"""Acceptance mutations: foreign constructors/owners and unfinished entries fail."""
import copy
import unittest
from native_entries_oracles import validate


def fixture():
    context = dict(flags=0x4b, control=0, setup=0x022a0000, root=0x022b0000,
                   save=0x02200000, published_save=0x02200000)
    snap = dict(flags=0, cap=0, allowed=1, root=context['root'], epoch=1)
    run = dict(name='trainer4b', events=[dict(name='constructor',frame=1,lr=0x020507ad,
               setup=context['setup'],args=[11,0x4b,8,385],flags=0x4b,control=0),
               dict(name='captured',frame=2,context=context,snapshot=snap,
                    save_owner=context['save'],setup_owner=context['setup'])],
               control_trace=[dict(frame=i,control=0,snapshot=copy.deepcopy(snap),sp=0x027e1000)
                              for i in range(3,8)])
    return dict(case='trainer4b',battles=[run],script=[['LockAll'],['SetFlag',0x961],
                ['SetVar',0x403f,385],['TrainerBattle',6,8,0,1],['ReleaseAll'],['End']])


class EntryAcceptance(unittest.TestCase):
    def test_roamer_requires_coherent_location_and_unmodified_native_identity(self):
        r=fixture();r['case']='roamer'
        b=r['battles'][0]
        b['events'][0].update(lr=0x0224709f,flags=0x100)
        b['events'][0]['args'][1]=0x100
        b['events'][1]['context']['flags']=0x100
        b.update(returned_to_field=True,after_snapshot=dict(epoch=0))
        native=bytes.fromhex('2d000000f8dd5a131ec32a73f300830028000100')
        r['roamer_fixture']=dict(array=0x02280000,pointer=0x02280010,native=native.hex(),
            position=[41,392,203],tile=[2,False],location_table='29000000',
            writes=[dict(pointer=0x02280010,field=f,value=v) for f,v in ((4,243),(6,40))])
        b['location_input']=dict(map=41,index=8,before=native.hex(),
            after=(bytes.fromhex('29000000')+native[4:]).hex(),before_entry=True)
        self.assertEqual(validate(r),('runtime.ordinary_100',))
        for field,value in (('map',42),('index',9),('before_entry',False),
                            ('after',(bytes.fromhex('29000000')+b'\0'*16).hex())):
            bad=copy.deepcopy(r);bad['battles'][0]['location_input'][field]=value
            with self.subTest(field=field),self.assertRaises(AssertionError):validate(bad)
        bad=copy.deepcopy(r);bad['battles'][0]['events'][0]['lr']=0x02050433
        with self.assertRaises(AssertionError):validate(bad)

    def test_valid_native_input_shape(self):
        self.assertEqual(validate(fixture()),('runtime.ordinary_4b',))

    def test_foreign_constructor_or_owner_cannot_pass(self):
        mutations = [('lr',0x02050433),('setup',0x022a0100),('control',1),('flags',0x13)]
        for field,value in mutations:
            with self.subTest(field=field):
                r=fixture();r['battles'][0]['events'][0][field]=value
                with self.assertRaises(AssertionError):validate(r)
        r=fixture();r['battles'][0]['events'][1]['save_owner']+=4
        with self.assertRaises(AssertionError):validate(r)

    def test_settings_change_or_short_continuation_cannot_pass(self):
        r=fixture();r['battles'][0]['control_trace'][3]['snapshot']['flags']=3
        with self.assertRaises(AssertionError):validate(r)
        r=fixture();r['battles'][0]['control_trace'].pop()
        with self.assertRaises(AssertionError):validate(r)

    def test_partner_fixture_is_required(self):
        r=fixture();r['script'].pop(1)
        with self.assertRaises(AssertionError):validate(r)

    def test_grass_requires_both_constructors_and_native_teardown(self):
        r=fixture();r['case']='grass'
        for flag in (0,0x4a):
            b=copy.deepcopy(r['battles'][0]);b['events'][0].update(lr={0:0x0224870d,0x4a:0x0224712d}[flag],flags=flag)
            b['events'][0]['args'][1]=flag;b['events'][1]['context']['flags']=flag
            b.update(returned_to_field=True,after_snapshot=dict(epoch=0))
            if flag==0:r['battles']=[b]
            else:r['battles'].append(b)
        self.assertEqual(set(validate(r)),{'runtime.ordinary_0','runtime.ordinary_4a'})
        r['battles'][1]['after_snapshot']['epoch']=1
        with self.assertRaises(AssertionError):validate(r)


if __name__=='__main__':unittest.main()
