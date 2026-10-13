"""Verifier tests: builder/verify.py passes a correct installation and catches each kind of wrong byte.

    .venv/bin/python -m unittest discover -s work/advanced-ai/testbench/unit -p 'test_verify*.py'

The synthetic cases install onto test_install.synthetic_rom(), then change one thing in the output (through ndspy,
or a raw byte for the header) and expect the named check to fail. The real-ROM cases check that the rc8 release
without the AI fails and that an installation onto it passes; they skip when the ROM is missing.
"""
import contextlib
import io
import struct
import sys
import tempfile
import unittest
from pathlib import Path

import ndspy.narc
import ndspy.rom

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_install as ti  # noqa: E402
from test_install import install, verify  # noqa: E402


class Synthetic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        cls.payload = ti.synthetic_payload(d / "payload")
        cls.marks = ti.write_marks(d / "marks.json")
        cls.rom = ti.synthetic_rom()
        cls.pins = ti.synthetic_pins(cls.rom)
        (d / "in.nds").write_bytes(cls.rom)
        install.install(d / "in.nds", d / "out.nds", cls.payload, cls.marks, cls.pins)
        cls.out = (d / "out.nds").read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def report(self, data, with_input=True):
        return verify.verify(data, self.payload, self.marks, self.rom if with_input else None,
                             overlay11_sha256=self.pins.overlay11_sha256)

    def failing(self, data, fragment, with_input=True):
        r = self.report(data, with_input)
        self.assertFalse(r["ok"])
        self.assertTrue(any(fragment in e for e in r["errors"]), r["errors"])

    def mutate(self, edit):
        rom = ndspy.rom.NintendoDSRom(self.out)
        edit(rom)
        return rom.save()

    def test_correct_installation_passes(self):
        r = self.report(self.out)
        self.assertTrue(r["ok"], r["errors"])
        self.assertGreater(r["checked"], 30)
        self.assertTrue(self.report(self.out, with_input=False)["ok"])

    def test_the_uninstalled_input_fails(self):
        r = self.report(self.rom, with_input=False)
        self.assertFalse(r["ok"])
        for fragment in ("autoload sections", "hook 0x02223D10", "overlay 10 = overlay 11", "byte 2 = marks"):
            self.assertTrue(any(fragment in e for e in r["errors"]), fragment)

    def test_a_hook_to_the_wrong_target(self):
        def edit(rom):
            data = bytearray(rom.files[14])
            off = 0x02203736 - 0x022007E0
            data[off:off + 4] = install.thumb_bl(0x02203736, ti.SYMBOLS["ai_entry"] + 2)
            rom.files[14] = bytes(data)
        self.failing(self.mutate(edit), "hook 0x02203736: bl ai_entry")

    def test_a_hook_that_is_not_a_bl(self):
        def edit(rom):
            data = bytearray(rom.files[14])
            off = 0x022153C2 - 0x022007E0
            data[off:off + 4] = bytes.fromhex("0ef03dfb")
            rom.files[14] = bytes(data)
        self.failing(self.mutate(edit), "hook 0x022153C2: bl ai_lead")

    def test_overlay_10_with_a_wrong_byte(self):
        def edit(rom):
            data = bytearray(rom.files[10])
            data[-1] ^= 1
            rom.files[10] = bytes(data)
        self.failing(self.mutate(edit), "overlay 10 = overlay 11, 0x20 zero bytes, slot.bin")

    def test_y9_entry_10_with_a_wrong_bss(self):
        def edit(rom):
            table = bytearray(rom.arm9OverlayTable)
            struct.pack_into("<I", table, 32 * 10 + 12, 0x20)
            rom.arm9OverlayTable = bytes(table)
        self.failing(self.mutate(edit), "y9 entry 10")

    def test_a_word_left_as_before(self):
        def edit(rom):
            arm = rom.loadArm9()
            struct.pack_into("<I", arm.sections[0].data, 0x020D1A28 - 0x02000000, 0x01FF8FC0)
            rom.arm9 = arm.save(compress=False)
        self.failing(self.mutate(edit), "ITCM arena empty")

    def test_an_autoload_section_with_a_wrong_byte(self):
        def edit(rom):
            arm = rom.loadArm9()
            arm.sections[5].data[0] ^= 1
            rom.arm9 = arm.save(compress=False)
        self.failing(self.mutate(edit), "autoload main: payload bytes and bss")

    def test_a_missing_trainer_mark(self):
        def edit(rom):
            narc = ndspy.narc.NARC(rom.files[15])
            narc.files[5] = narc.files[5][:2] + b"\0" + narc.files[5][3:]
            rom.files[15] = narc.save()
        self.failing(self.mutate(edit), "trainer header byte 2 = marks")

    def test_another_file_changed(self):
        def edit(rom):
            rom.files[3] = b"\x01" + rom.files[3][1:]
        self.failing(self.mutate(edit), "every other ROM file unchanged")

    def test_overlay_14_changed_outside_the_hooks(self):
        def edit(rom):
            data = bytearray(rom.files[14])
            data[0x100] ^= 1
            rom.files[14] = bytes(data)
        self.failing(self.mutate(edit), "every other ROM file unchanged")

    def test_a_broken_header_crc(self):
        data = bytearray(self.out)
        data[0x0B] ^= 1
        self.failing(bytes(data), "header CRC")

    def test_cli_exit_codes(self):
        d = Path(self.tmp.name)
        (d / "bad.nds").write_bytes(self.rom)
        args = ["--payload", str(self.payload), "--marks", str(self.marks)]
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            self.assertEqual(verify.main([str(d / "bad.nds"), *args]), 1)
        self.assertIn("FAIL hook 0x02223D10", printed.getvalue())


@unittest.skipUnless(ti.RC8_RELEASE.exists() and (ti.PAYLOAD / "payload.json").exists(),
                     "needs work/build/advanced-ai/base/rc8_release.nds and the committed payload/")
class RealRom(unittest.TestCase):
    def test_rc8_release_fails_and_its_installation_passes(self):
        data = ti.RC8_RELEASE.read_bytes()
        self.assertFalse(verify.verify(data, ti.PAYLOAD, ti.MARKS)["ok"])
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ai.nds"
            install.install(ti.RC8_RELEASE, out, ti.PAYLOAD, ti.MARKS)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(verify.main([str(out), "--input", str(ti.RC8_RELEASE)]), 0)


if __name__ == "__main__":
    unittest.main()
