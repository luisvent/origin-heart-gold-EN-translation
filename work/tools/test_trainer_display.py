"""Full-name export guard, bounded storage and native receipt regressions (D-2487)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import trainer_display as td
import msgtool as m
import textmetrics as tm
import ws
import qa
import hardcoded


class TrainerDisplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root/'ws'
        self.extract = self.root/'extract'
        for p in (self.work, self.extract):
            (p/'a027').mkdir(parents=True)
        self.names = {17:'Swarm example',59:'Flock example',632:'Wild example',666:'Mixed group example',745:'Group example'}
        self.bank = {'narc':'a027','bank':719,'strings':[
            {'id':sid,'zh':'名','en':text,'status':'draft'} for sid,text in self.names.items()]
            +[{'id':462,'zh':'名','en':'Example','status':'draft'}]}
        (self.work/'a027/0719.json').write_text(json.dumps(self.bank))
        (self.extract/'a027/0719.json').write_text(json.dumps({'bank':719,'seed':7,'strings':[
            {'id':r['id'],'text':r['zh']} for r in self.bank['strings']]}))

    def test_standalone_export_refuses_long_names_without_formatter(self):
        _,problems=ws.export(self.work,self.extract,self.root/'out')
        self.assertEqual(len(problems),5)
        out=json.loads((self.root/'out/a027/0719.json').read_text())
        self.assertTrue(all(not r['text'].startswith('{COMPRESSED}T00') for r in out['strings']))

    def test_matching_plan_exports_unique_packed_keys_and_preserves_singular(self):
        aliases=td.plan(self.work)
        counts,problems=ws.export(self.work,self.extract,self.root/'out',trainer_aliases=aliases)
        self.assertFalse(problems)
        rows={r['id']:r['text'] for r in json.loads((self.root/'out/a027/0719.json').read_text())['strings']}
        cm=m.Charmap.load([str(tm.CHARMAP_EN)])
        for sid in self.names:
            self.assertEqual(rows[sid],'{COMPRESSED}'+td.key(sid))
            self.assertLessEqual(len(m.encode_text(rows[sid],cm)),8)
        self.assertEqual(rows[462],'{COMPRESSED}Example')
        self.assertEqual(counts['compressed'],6)
        td.verify_export(self.root/'out',aliases)
        rows[17]='{COMPRESSED}Wrong'
        path=self.root/'out/a027/0719.json'
        data=json.loads(path.read_text())
        data['strings'][0]['text']=rows[17]
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):td.verify_export(self.root/'out',aliases)

    def test_stale_plan_and_reserved_source_keys_are_refused(self):
        with self.assertRaises(ValueError):td.stored_text(17,'Changed example',self.names)
        self.bank['strings'][0]['en']='T00017'
        (self.work/'a027/0719.json').write_text(json.dumps(self.bank))
        with self.assertRaises(ValueError):td.plan(self.work)

    def test_full_text_qa_keeps_ordinary_and_raw_names_bounded(self):
        self.assertFalse([i for i in qa.check_bank(self.bank,glossary=False) if i['level']=='error'])
        self.bank['strings'] += [
            {'id':463,'zh':'名','en':'Excess ordinary name','status':'draft'},
            {'id':707,'zh':'名','en':'Excess raw name','status':'draft'}]
        errors=[i for i in qa.check_bank(self.bank,glossary=False) if i['level']=='error']
        self.assertEqual({i['id'] for i in errors},{463,707})
        self.bank['strings'][0]['en']='Long{NEWLINE}name'
        self.assertTrue([i for i in qa.check_bank(self.bank,glossary=False) if i['id']==17 and i['level']=='error'])

    def test_payload_rejects_unapproved_ids_and_placement(self):
        for names,base in [({462:'Example'},0x01ff9800),({17:'Example'},0x01ff9801),({17:'Example'},0x02000000)]:
            with self.assertRaises(ValueError):td.assemble(names,base,'unused')
        with self.assertRaises(ValueError):td.encoded('x'*64)
        with self.assertRaises(ValueError):td.encoded('Name{VAR:0100:0}')

    def test_receipt_rejects_missing_hook_payload_and_allocation_boundary(self):
        import hashlib,struct
        blob=b'\0'*32;base=0x01ff8620;end=base+len(blob)
        main=bytearray(0xD1A30);offset=td.ENTRY-0x02000000
        main[offset:offset+8]=td.trampoline(base);struct.pack_into('<I',main,0xD1A28,end)
        images={'arm9':bytes(main),'itcm':bytes(0x620)+blob}
        view=SimpleNamespace(get=lambda key:images[key])
        receipt={'enabled':True,'base':base,'itcm_end':end,'bytes':len(blob),'aliases':self.names,
                 'alias_sha256':td.digest(self.names),'payload_sha256':hashlib.sha256(blob).hexdigest()}
        with patch.object(hardcoded,'RomView',return_value=view), patch.object(td,'expected_payload',return_value=blob):
            self.assertTrue(td.verify(None,receipt)['enabled'])
            images['itcm']=images['itcm'][:-1]+b'\1'
            with self.assertRaises(ValueError):td.verify(None,receipt)
            images['itcm']=bytes(0x620)+blob
            images['arm9']=bytes(len(main))
            with self.assertRaises(ValueError):td.verify(None,receipt)


class SyntheticCompositionTests(unittest.TestCase):
    def test_append_reparse_and_prior_stage_hash_are_exact(self):
        """Exercise ndspy autoload reconstruction using zero-filled synthetic code."""
        import struct,ndspy.code,asmpatch
        try:
            assembler=asmpatch.find_armips()
            asmpatch.check_armips(assembler)
        except asmpatch.AsmError as ex:
            self.skipTest(str(ex))
        code=object.__new__(ndspy.code.MainCodeFile)
        code.ramAddress=0x02000000;code.codeSettingsOffs=0x100
        main=bytearray(0xD1A40)
        struct.pack_into('<I',main,0x80,0x02000100)
        struct.pack_into('<I',main,0xD1A28,0x01FF8620)
        off=td.ENTRY-0x02000000;main[off:off+8]=td.EXPECT
        code.sections=[ndspy.code.MainCodeFile.Section(main,0x02000000,0,implicit=True),
                       ndspy.code.MainCodeFile.Section(bytes(0x620),0x01FF8000,0),
                       ndspy.code.MainCodeFile.Section(bytes(range(96)),0x027E0000,0)]
        class Synthetic:
            def loadArm9(self):
                return ndspy.code.MainCodeFile(self.arm9,0x02000000,0x02000084)
        rom=Synthetic();rom.arm9=bytes(code.save(compress=False));before=rom.arm9
        aliases={17:'Swarm example',666:'Mixed group example'}
        receipt=td.apply(rom,aliases,assembler)
        self.assertEqual(td.verify(rom,receipt)['aliases'],2)
        self.assertEqual(td.before_display(rom,receipt).arm9,before)
        import build
        self.assertEqual(build.verify_text_speed(rom,{'enabled':False,'reason':'not-selected'},receipt)['status'],'not-enabled')
        with self.assertRaises(ValueError):build.verify_text_speed(rom,{'enabled':False,'reason':'not-selected'})
        self.assertNotEqual(rom.arm9,before)
        # A self-consistent receipt must not hide altered native instructions.
        import hashlib,copy
        changed=bytearray(rom.arm9)
        parsed=rom.loadArm9();itcm=parsed.sections[1]
        itcm.data[receipt['base']-0x01FF8000] ^= 1
        rom.arm9=bytes(parsed.save(compress=False))
        forged=copy.deepcopy(receipt)
        tail=bytes(itcm.data[receipt['base']-0x01FF8000:receipt['base']-0x01FF8000+receipt['bytes']])
        forged['payload_sha256']=hashlib.sha256(tail).hexdigest()
        with self.assertRaises(ValueError):td.verify(rom,forged)
        rom.arm9=bytes(changed)
        # A second install or an altered SDK arena bound is rejected.
        with self.assertRaises(ValueError):td.apply(rom,aliases,assembler)
        rom.arm9=before
        broken=bytearray(rom.arm9);struct.pack_into('<I',broken,0xD1A28,0x01FF8600);rom.arm9=bytes(broken)
        with self.assertRaisesRegex(ValueError,'allocation boundary'):td.apply(rom,aliases,assembler)
        self.assertEqual(rom.arm9,bytes(broken))

if __name__=='__main__':unittest.main()
