"""Mutation tests for native special-context exclusion and its positive control."""
import copy
import unittest
from native_special_oracles import ZERO, validate


def fixture():
    rows = []
    for flags in (0, 7):
        mon = dict(pid=5, species=20, exp=8000, evs=[0]*6, level=20,
                   checksum_ok=True, bad_egg=False)
        context = dict(flags=0, control=1, setup=0x022A0000, root=0x022B0000,
                       save=0x02200000, published_save=0x02200000)
        rows.append(dict(flags=flags, command=['ScrCmd_250', 19, 5],
            before=[mon], after=[copy.deepcopy(mon)], pp_before=[40,0,0,0], pp_after=[39,0,0,0],
            inputs=[dict(touch=[32,35])], after_snapshot=dict(ZERO),
            events=[dict(name='constructor',frame=1,lr=0x02050639,args=[11,0,5,0],
                         setup=context['setup'],flags=0,control=0),
                    dict(name='original_begin',frame=2),
                    dict(name='captured',frame=2,context=context,snapshot=dict(ZERO),save_owner=0,setup_owner=0),
                    dict(name='action',frame=10,actor=dict(id=1),move=82,selected=82),
                    dict(name='teardown',frame=20), dict(name='free',frame=21),
                    dict(name='original_free',frame=21,root=context['root'])],
            control_trace=[dict(frame=f,control=1,snapshot=dict(ZERO),sp=0x027E1000) for f in range(3,8)]))
    return rows


class SpecialAcceptance(unittest.TestCase):
    def test_complete_paired_native_exclusion(self):
        self.assertEqual(validate(fixture()), ('runtime.exclude_special',))

    def test_missing_default_or_enabled_control_rejected(self):
        for rows in (fixture()[:1], fixture()[1:], fixture()[::-1]):
            with self.assertRaises(AssertionError): validate(rows)

    def test_foreign_constructor_or_entry_rejected(self):
        for field,value in (('lr',0x020507AD),('flags',4),('control',1),('setup',0x022A0004)):
            rows=fixture(); rows[1]['events'][0][field]=value
            with self.subTest(field=field), self.assertRaises(AssertionError): validate(rows)
        rows=fixture(); rows[1]['events'][2]['context']['control']=0
        with self.assertRaises(AssertionError): validate(rows)

    def test_difficulty_owner_or_snapshot_publication_rejected(self):
        for field in ('save_owner','setup_owner'):
            rows=fixture(); rows[1]['events'][2][field]=0x02200000
            with self.subTest(field=field), self.assertRaises(AssertionError): validate(rows)
        rows=fixture(); rows[1]['events'][2]['snapshot']['epoch']=1
        with self.assertRaises(AssertionError): validate(rows)

    def test_missing_continuation_or_changed_native_control_rejected(self):
        rows=fixture(); rows[1]['control_trace'].pop()
        with self.assertRaises(AssertionError): validate(rows)
        rows=fixture(); rows[1]['control_trace'][3]['control']=0
        with self.assertRaises(AssertionError): validate(rows)

    def test_no_original_action_or_no_native_pp_use_rejected(self):
        rows=fixture(); rows[1]['events'][3]['move']=150
        with self.assertRaises(AssertionError): validate(rows)
        rows=fixture(); rows[1]['pp_after']=[40,0,0,0]
        with self.assertRaises(AssertionError): validate(rows)

    def test_growth_award_or_missing_original_teardown_rejected(self):
        rows=fixture(); rows[1]['after'][0]['exp']+=1
        with self.assertRaises(AssertionError): validate(rows)
        rows=fixture(); rows[1]['events'].append(dict(name='ev'))
        with self.assertRaises(AssertionError): validate(rows)
        rows=fixture(); rows[1]['events'].pop()
        with self.assertRaises(AssertionError): validate(rows)
