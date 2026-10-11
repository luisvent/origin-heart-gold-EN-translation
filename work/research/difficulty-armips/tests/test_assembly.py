"""Run armips against disposable copies of actual CN ARM9 data."""
from pathlib import Path
import os
import shutil
import struct
import unittest
from support import CN, SOURCE, ROOT, arm9_main, command, load_rom, scratch


class AssembledFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.armips = os.environ.get('ARMIPS') or shutil.which('armips')
        if not cls.armips:
            raise unittest.SkipTest('Set ARMIPS to the existing local v0.11.0 executable')
        cls.armips = str(Path(cls.armips).resolve())
        banner = command([cls.armips], success=False)
        if 'armips assembler v0.11.0' not in banner.stdout + banner.stderr:
            raise AssertionError('Unreviewed armips version')
        if not CN.exists():
            raise unittest.SkipTest('Local Chinese ROM unavailable')
        cls.arm9 = arm9_main(load_rom())

    def setUp(self):
        self.stage = scratch('assembled-')
        self.addCleanup(self.stage.cleanup)
        self.path = Path(self.stage.name)
        (self.path / 'rom').mkdir()
        shutil.copytree(ROOT / 'work/patches/include', self.path / 'include')

    def assemble_hooks(self, raw, success=True):
        image = self.path / 'rom/arm9.bin'
        image.write_bytes(raw)
        result = command([self.armips, SOURCE / 'hooks.asm', '-definelabel', 'GUARDS_REAL', '1'],
                         cwd=image.parent, success=success)
        return image.read_bytes(), result

    def test_real_rom_hooks_targets_and_declared_regions(self):
        patched, _ = self.assemble_hooks(self.arm9)
        allowed = {off + i for off in (0x908, 0xD1970, 0x3E544) for i in range(4)}
        self.assertEqual(len(patched), len(self.arm9))
        self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(self.arm9, patched))))
        op = struct.unpack_from('<I', patched, 0x908)[0]
        self.assertEqual(op >> 24, 0xEB)
        imm = op & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        self.assertEqual(0x02000908 + 8 + (imm << 2), 0x023DF000)
        self.assertEqual(struct.unpack_from('<I', patched, 0xD1970)[0], 0x023DF000)
        hi, lo = struct.unpack_from('<HH', patched, 0x3E544)
        self.assertEqual(hi & 0xF800, 0xF000)
        self.assertEqual(lo & 0xF800, 0xF800)
        self.assertEqual(0x0203E548 + ((hi & 0x7FF) << 12) + ((lo & 0x7FF) << 1), 0x023DF200)

    def test_each_corrupted_guard_fails_without_output_mutation(self):
        for offset in (0x908, 0xD1970, 0x3E544):
            with self.subTest(offset=hex(offset)):
                corrupted = bytearray(self.arm9)
                corrupted[offset] ^= 1
                after, result = self.assemble_hooks(corrupted, success=False)
                self.assertIn('guard failed', result.stdout + result.stderr)
                self.assertEqual(after, corrupted)

    def test_foundation_initial_state_and_dispatch_literal(self):
        command([self.armips, SOURCE / 'foundation.asm', '-definelabel',
                 'BRIDGE_DISPATCH', '0x023DF301'], cwd=self.path)
        data = (self.path / 'foundation.bin').read_bytes()
        self.assertEqual(data[0x100:0x200], bytes(0x100))
        self.assertIn(struct.pack('<I', 0x023DF301), data[0x210:])
        self.assertLessEqual(len(data), 0xE00)
        self.assertEqual(struct.unpack_from('<I', data, 52)[0], 0x023DF100)
        self.assertEqual(struct.unpack_from('<I', data, 56)[0], 0x44524631)

    def test_missing_native_dispatch_rejected(self):
        result = command([self.armips, SOURCE / 'foundation.asm'], cwd=self.path, success=False)
        self.assertIn('bridge_dispatch', (result.stdout + result.stderr).lower())
