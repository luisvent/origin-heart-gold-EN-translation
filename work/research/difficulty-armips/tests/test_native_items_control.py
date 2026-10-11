"""Diagnostic controls cannot stand in for ordinary ITEMS acceptance."""
import copy
import unittest
from native_items_control import visible_categories, validate_pair, OriginalSession
from support import CN_SHA256


class ItemsControlTests(unittest.TestCase):
    def test_native_visibility_cannot_be_inferred_from_metadata_or_missing_lists(self):
        run=dict(events=[dict(name='native_item_mask',result=0),
            dict(name='lists',args=dict(owner=0,tutorial=0),lists=[[] for _ in range(5)])])
        self.assertEqual(visible_categories(run),[])
        run['events'][1]['lists'][0]=[dict(item=28,quantity=3)]
        self.assertEqual(visible_categories(run),[0])  # actual list wins over original attr0
        for mutate in (lambda r:r['events'].pop(0),lambda r:r['events'].pop(),
                       lambda r:r['events'][1]['args'].update(owner=1),
                       lambda r:r['events'][1]['lists'][0][0].update(quantity=2)):
            bad=copy.deepcopy(run);mutate(bad)
            with self.assertRaises(AssertionError):visible_categories(bad)

    def test_pair_requires_distinct_boots_same_inputs_and_no_acceptance_claims(self):
        binding=dict(candidate=dict(candidate_sha256='candidate'),cn_sha256=CN_SHA256)
        fixture=dict(input_battery_sha256='battery',source_battery_sha256='source',payload=[1],splash=[2],
                     target_slot=1,ui_slot=2,records=[dict(sha256='fainted'),dict(sha256='healthy')])
        rows=[dict(status='passed',diagnostic_only=True,cases={},pair='pair',old_state_loaded=False,
                   nonce=str(i),binding=copy.deepcopy(binding),fixture=copy.deepcopy(fixture),
                   executed_rom=dict(sha256=rom),battle=dict(variant=variant,finding='native_ui_unreachable',
                     player_fixture=dict(hashes=['healthy','fainted','healthy']),
                     events=[dict(name='enemy_fixture',after_sha256='healthy')]))
              for i,(variant,rom) in enumerate((('candidate-all-wild','candidate'),('cn-wild',CN_SHA256)))]
        self.assertFalse(validate_pair(rows,'pair')['effect_equivalence_proven'])
        for mutate in (lambda r:r[1].update(nonce='0'),lambda r:r[1].update(old_state_loaded=True),
                       lambda r:r[1]['fixture'].update(ui_slot=1),
                       lambda r:r[1]['executed_rom'].update(sha256='candidate'),
                       lambda r:r[1]['cases'].update({'items.addition_28':dict(status='passed')}),
                       lambda r:r[1]['battle']['events'][0].update(after_sha256='different'),
                       lambda r:r[1]['binding'].update(changed=True)):
            bad=copy.deepcopy(rows);mutate(bad)
            with self.assertRaises(AssertionError):validate_pair(bad,'pair')

    def test_actual_cn_attribute_return_binds_only_verified_overlay9_caller(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from support import load_rom, arm9_main
        from native_items_control import ControlTrace
        rom=load_rom();session=OriginalSession.__new__(OriginalSession)
        session.arm9=arm9_main(rom);session.overlays=rom.loadArm9Overlays([9,14])
        session.callbacks={};session.reused_addresses={}
        ov=session.overlays[9];raw=bytearray(ov.data)
        read=lambda a,n:bytes(raw[a-ov.ramAddress:a-ov.ramAddress+n])
        regs=[28,13,5]+[0]*13;regs[13]=0x027e0000;regs[14]=0x021EC30D
        hooks={}
        h=SimpleNamespace(reg=regs,frame=1,read=read,on_exec=lambda a,cb:hooks.update({a:cb}))
        session.h=h
        trace=ControlTrace.__new__(ControlTrace);trace.h=h;trace.s=session;trace.run=dict(events=[])
        # The actual CN return cannot bind to the default battle overlay.
        with self.assertRaises(AssertionError):session.code(0x021EC30C)
        self.assertEqual(read(0x021EC308,4),bytes.fromhex('8af682f8'))
        trace.native_attr();self.assertIn(0x021EC30C,hooks)
        row=trace.run['events'][-1];regs[0]=0
        at=0x021EC30C-ov.ramAddress;raw[at]^=1
        hooks[0x021EC30C](h)
        self.assertNotIn('result',row)  # wrong overlay bytes cannot complete evidence
        raw[at]^=1;hooks[0x021EC30C](h);self.assertEqual(row['result'],0)
        regs[0]=28;raw[0x021EC308-ov.ramAddress]^=1
        with self.assertRaises(AssertionError):trace.native_attr()
        # Candidate resident callers keep the ordinary payload-binding path.
        trace.s=SimpleNamespace(returned=Mock());regs[14]=0x023DC101
        trace.native_attr()
        self.assertEqual(trace.s.returned.call_args.kwargs,dict(overlay=None))

    def test_original_hooks_bind_to_original_overlay_and_static_bytes(self):
        from types import SimpleNamespace
        s=OriginalSession.__new__(OriginalSession);s.arm9=b'12345678'
        s.overlays={14:SimpleNamespace(ramAddress=0x02200000,data=b'abcdefgh'),
                    9:SimpleNamespace(ramAddress=0x02200000,data=b'ABCDEFGH')}
        self.assertEqual(s.code(0x02000000),b'12345678')
        self.assertEqual(s.code(0x02200000),b'abcdefgh')
        self.assertEqual(s.code(0x02200000,overlay=9),b'ABCDEFGH')
        with self.assertRaises(AssertionError):s.code(0x02210000)
