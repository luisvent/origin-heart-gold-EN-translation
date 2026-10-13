"""Guarded binary scope and miniature-font capacity regressions."""
import json
import os
from pathlib import Path
import shutil
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import asmpatch
import fixes
import msgtool as m
from hardcoded import RomView

ROOT = Path(__file__).resolve().parents[2]
CN = ROOT / 'work/rom/origin_v4.0.3_cn.nds'
ARMIPS = os.environ.get('ARMIPS') or shutil.which('armips')


@unittest.skipUnless(CN.exists() and ARMIPS and Path(ARMIPS).is_file(), 'existing CN ROM and pinned ARMIPS required')
class AbilityBannerTests(unittest.TestCase):
    def setUp(self):
        self.fix = next(f for f in fixes.load_all() if f['id'] == 'ability-banner')
        self.rom = m.load_rom(CN)

    def test_only_two_instructions_change(self):
        before = [bytes(f) for f in self.rom.files]
        arm9, y9 = bytes(self.rom.arm9), bytes(self.rom.arm9OverlayTable)
        view = RomView(self.rom)
        oid = view.overlay('overlay14').fileID
        old = view.get('overlay14')
        asmpatch.apply(self.rom, [self.fix], ARMIPS)
        new = RomView(self.rom).get('overlay14')
        expected = bytearray(old)
        for offset, raw in ((0x25F2A, b'\x70\x22'), (0x25F2C, b'\x10\x31')):
            expected[offset:offset + 2] = raw
        self.assertEqual(new, bytes(expected))
        self.assertEqual([i for i, b in enumerate(before) if b != bytes(self.rom.files[i])], [oid])
        self.assertEqual(bytes(self.rom.arm9), arm9)
        self.assertEqual(bytes(self.rom.arm9OverlayTable), y9)
        self.assertFalse(self.fix['enabled'])

    def test_bad_original_is_rejected_without_mutation(self):
        view = RomView(self.rom)
        data = bytearray(view.get('overlay14'))
        data[0x25F2A] ^= 1
        view.set('overlay14', bytes(data))
        with self.assertRaises(asmpatch.AsmError):
            asmpatch.apply(self.rom, [self.fix], ARMIPS)
        self.assertEqual(RomView(self.rom).get('overlay14'), bytes(data))

    def test_every_current_ability_fits_miniature_font(self):
        # Font member 12 metrics match native font5 samples: 82/84/78 pixels.
        font = m.Narc.parse(m.get_file(self.rom, m.FONT_NARC_PATH)).files[12]
        start = int.from_bytes(font[4:8], 'little')
        cm = m.Charmap.load([str(ROOT / 'work/tools/charmap_en.tsv')])
        def width(text):
            return sum(font[start + cm.enc[c] - 1] for c in text)
        self.assertEqual(width('Battle Armor'), 82)
        self.assertEqual(width('EmbodyAspect'), 84)
        self.assertEqual(width('Feraligatr’s'), 78)
        self.assertEqual(width('WWWWWWWWWW’s'), 83)
        self.assertLessEqual(16 + width('WWWWWWWWWW’s'), 112)
        entries = json.loads((ROOT / 'work/translate/banks/a027/0711.json').read_text())['strings']
        sizes = [width(s['en']) for s in entries if s['en']]
        self.assertEqual(len(sizes), 327)
        self.assertLessEqual(max(sizes), 84)
        # Whole ability row occupies [112-width,112), nickname [16,94).
        for n in sizes:
            self.assertGreaterEqual(112 - n, 28)
            self.assertLessEqual(112, 120)
        self.assertLessEqual(16 + width('Feraligatr’s'), 112)


if __name__ == '__main__':
    unittest.main()
