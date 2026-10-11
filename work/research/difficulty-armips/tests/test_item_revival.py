"""Independent native source contract; no emulator or mutable event-token oracle."""
import json
import struct
import unittest
import ndspy.rom
from ndspy.narc import NARC
from support import SOURCE, ROOT
from candidate_tools import install

class RevivalSourceTests(unittest.TestCase):
    def test_original_sources_and_independent_dependency_guards(self):
        pins=json.loads((SOURCE/'research/items-revival-pins.json').read_text())
        for name in ('cn','en'):
            rom=ndspy.rom.NintendoDSRom.fromFile(ROOT/pins['inputs'][name]['path'])
            raw={'arm9.bin':bytes(rom.loadArm9().sections[0].data),
                 'overlay14.bin':bytes(rom.loadArm9Overlays()[14].data)}
            self.assertEqual(len(install.validate_item_revival(raw, source=name)),14)
            for row in pins['ranges']:
                bad=dict(raw); data=bytearray(bad[row['file']])
                data[int(row['start'],16)-install.BASES[row['file']]]^=1
                bad[row['file']]=bytes(data)
                with self.subTest(source=name,label=row['label']),self.assertRaisesRegex(ValueError,'item revival dependency'):
                    install.validate_item_revival(bad, source=name)
            ov=raw['overlay14.bin']; base=install.BASES['overlay14.bin']
            table=[(ov[a-base],struct.unpack_from('<I',ov,a-base+4)[0])
                   for a in range(0x0224D19C,0x0224D234,8)]
            self.assertEqual(len(table),19)
            self.assertEqual(table[8],(23,0x02221E31))
            self.assertEqual(table[-1],(38,0x02221B85))
            self.assertEqual(ov[0x022218C0-base:0x022218C4-base],bytes.fromhex('54f6a6fd'))
            items=NARC(rom.getFileByName('a/0/1/7')).files
            for item in (28,29,37):
                data=items[item]
                self.assertEqual(int.from_bytes(data[8:10],'little')>>11,0)
                self.assertTrue(data[15]&1) # native attr23 decoder
                self.assertTrue(data[19]&4) # native attr38 decoder
                self.assertEqual(data[27],254 if item==28 else 255)
