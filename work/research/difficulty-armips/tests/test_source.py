"""Read-only checks of the actual source ROM, not extracted cache/log assertions."""
import struct
import json
import hashlib
import tomllib
import unittest
from support import CN, SOURCE, arm9_main, load_rom


class SourceROMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not CN.is_file():
            raise unittest.SkipTest('Local untouched Chinese ROM unavailable')
        cls.rom = load_rom()
        cls.arm9 = arm9_main(cls.rom)
        cls.overlays = cls.rom.loadArm9Overlays()

    def test_scripted_wild_control_caller_contract(self):
        # Fresh CN bytes must match the reviewed completed-EN caller/constructor,
        # replay marker and begin leaf; this is static evidence, not gameplay.
        pins=json.loads((SOURCE/'research/runtime-classifier-pins.json').read_text())
        for row in pins['ranges']:
            data,base=(self.arm9,0x02000000) if row['image']=='arm9' else (
                bytes(self.overlays[14].data),self.overlays[14].ramAddress)
            a,z=int(row['start'],16)-base,int(row['end'],16)-base
            with self.subTest(label=row['label']):
                self.assertEqual(hashlib.sha256(data[a:z]).hexdigest(),row['sha256'])

    def test_declared_resident_guards_against_rom(self):
        manifest = tomllib.loads((SOURCE / 'fix.toml').read_text())
        self.assertGreater(len(manifest['code']), 0)
        for entry in manifest['code']:
            with self.subTest(region=entry['id']):
                data = self.arm9 if entry['file'] == 'arm9' else bytes(
                    self.overlays[int(entry['file'].removeprefix('overlay'))].data)
                # Manifest values are little-endian halfwords, not hex byte strings.
                expected = b''.join(struct.pack('<H', int(w, 16))
                                    for w in entry['expect'].split())
                off = int(entry['offset'], 0)
                self.assertEqual(data[off:off + len(expected)], expected)

    def test_items_bag_binding_native_sources(self):
        pins=json.loads((SOURCE/'research/items-binding-pins.json').read_text())
        for row in pins['ranges']:
            data,base=(self.arm9,0x02000000) if row['file']=='arm9.bin' else (
                bytes(self.overlays[14].data),self.overlays[14].ramAddress)
            a,z=int(row['start'],16)-base,int(row['end'],16)-base
            with self.subTest(label=row['label']):
                self.assertEqual(hashlib.sha256(data[a:z]).hexdigest(),row['sha256'])
        # Decode the actual creator's offset and consuming instruction pair,
        # independently of the C fixture and historical prose.
        ov=self.overlays[14];a=0x02202A50-ov.ramAddress
        self.assertEqual(bytes(ov.data[a:a+4]),bytes.fromhex('42208000'))
        self.assertEqual((ov.data[a] << 2),0x108)

    def test_exp_share_getter_and_unique_guard(self):
        signature = bytes.fromhex('0120704764207047')
        found = [(i, bytes(ov.data).find(signature)) for i, ov in self.overlays.items()
                 if signature in ov.data]
        self.assertEqual(found, [(14, 0x14FE0)])
        self.assertEqual(self.overlays[14].ramAddress, 0x022007E0)

    def test_exp_share_callsite_reaches_native_getter(self):
        ov = self.overlays[14]
        address = 0x022289EA
        hi, lo = struct.unpack_from('<HH', ov.data, address - ov.ramAddress)
        self.assertEqual(hi & 0xF800, 0xF000)
        self.assertEqual(lo & 0xF800, 0xF800)
        delta = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
        if delta & (1 << 22):
            delta -= 1 << 23
        self.assertEqual(address + 4 + delta, 0x022157C0)
