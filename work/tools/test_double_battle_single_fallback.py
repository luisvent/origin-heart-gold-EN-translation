"""Run the real trainer-battle setup (arm9 0x02050768) with the double-battle-single-fallback hook assembled in,
over the Chinese arm9, with the native helpers stubbed. Not an emulator; the emulator runs are in
work/notes/double-battle-single-fallback_fix.md."""

import unittest
from pathlib import Path

import asmpatch
import fixes
import hardcoded
import msgtool
from honey_gather_thumb import Thumb, md

ROM = Path(__file__).resolve().parents[1] / "rom/origin_v4.0.3_cn.nds"
BASE = 0x02000000
SETUP = 0x02050768
RET = 0x0DEAD000
FIELD = 0x02300000
SAVE = 0x02301000
PARTY = 0x02302000
NEWSETUP = 0x02303000
SP = 0x027E0000


class Setup(Thumb):
    """Thumb runner over the arm9 image (the base class reads an overlay at 0x022007E0)."""

    def __init__(self, arm9, party_count, t1, t2, partner, flag=0):
        super().__init__(arm9)
        self.arm9 = arm9
        self.decoded = {}
        self.count = party_count
        self.types = []
        self.w32(FIELD + 0xC, SAVE)
        # the setup function's own stack arguments: [sp+0x28] = flag (0x801 single), [sp+0x2C] = 0 (skips tst)
        self.args = (t1, t2, partner)
        self.w32(SP + 0x00, flag)
        self.w32(SP + 0x04, 0)
        self.w32(SP + 0x08, 11)
        self.w32(SP + 0x0C, 0)
        self.w32(SP + 0x10, 0)

    def r8(self, a):
        if BASE <= a < BASE + len(self.arm9):
            return self.arm9[a - BASE]
        return self.mem.get(a, 0)

    def native(self, pc):
        r = self.r
        if pc == 0x0204FAD4:
            return FIELD            # the field system (the real one is [ctx + 0x18])
        if pc == 0x0207365C:
            assert r[0] == SAVE
            return PARTY
        if pc == 0x02073398:
            assert r[0] == PARTY
            return self.count
        if pc == 0x02050C34:
            assert r[0] == 11
            self.types.append(r[1])
            return NEWSETUP
        if pc in (0x0205125C, 0x02072544, 0x0202D180, 0x0202D328, 0x02050B44, 0x02050B58, 0x0204FCE4):
            return 0
        return None

    def run(self):
        t1, t2, partner = self.args
        self.r[:4] = [0x1234, t1, t2, partner]
        self.r[4:8] = [0xA4, 0xA5, 0xA6, 0xA7]
        self.r[13:15] = [SP, RET | 1]
        pc = SETUP
        for _ in range(2000):
            if pc == RET:
                return
            result = self.native(pc)
            if result is not None:
                self.clobber_callers()
                self.r[0] = result
                pc = self.r[14] & ~1
            else:
                if pc not in self.decoded:
                    self.decoded[pc] = next(md.disasm(bytes(self.arm9[pc - BASE:pc - BASE + 4]), pc, 1))
                pc = self.step(self.decoded[pc], pc)
        raise AssertionError("setup did not return")


@unittest.skipUnless(ROM.exists() and ROM.stat().st_size > 100_000_000, "needs local Chinese ROM")
class DoubleBattleSingleFallback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = hardcoded.RomView(msgtool.load_rom(str(ROM))).get("arm9")
        cls.fix = next(f for f in fixes.load_all() if f["id"] == "double-battle-single-fallback")
        cls.patched = asmpatch.assemble([cls.fix], {"arm9": cls.native}, asmpatch.find_armips())[0]["arm9"]

    def run_type(self, image, n, t1, t2, partner=0, flag=0):
        s = Setup(bytes(image), n, t1, t2, partner, flag)
        s.run()
        self.assertEqual(len(s.types), 1)
        return s.types[0]

    def test_native_types_unchanged_by_party(self):
        # the original: the party never matters (the freeze), so the control cases pin the harness itself
        for n in (0, 1, 2, 6):
            self.assertEqual(self.run_type(self.native, n, 951, 951), 3)
            self.assertEqual(self.run_type(self.native, n, 777, 778), 0x13)
            self.assertEqual(self.run_type(self.native, n, 5, 0), 1)
            self.assertEqual(self.run_type(self.native, n, 5, 0, flag=1), 0x801)
            self.assertEqual(self.run_type(self.native, n, 64, 5, partner=0), 0x13)
            self.assertEqual(self.run_type(self.native, n, 507, 508, partner=64), 0x4B)

    def test_double_with_fewer_than_two_becomes_single(self):
        for n in (0, 1):
            self.assertEqual(self.run_type(self.patched, n, 951, 951), 1)     # same trainer twice
            self.assertEqual(self.run_type(self.patched, n, 777, 778), 1)     # two trainers
            self.assertEqual(self.run_type(self.patched, n, 786, 787, partner=0), 1)

    def test_two_or_more_unchanged(self):
        for n in (2, 3, 6):
            self.assertEqual(self.run_type(self.patched, n, 951, 951), 3)
            self.assertEqual(self.run_type(self.patched, n, 777, 778), 0x13)

    def test_multi_battle_with_partner_stays_double(self):
        for n in (0, 1, 2, 6):
            self.assertEqual(self.run_type(self.patched, n, 507, 508, partner=64), 0x4B)

    def test_single_battles_untouched(self):
        for n in (0, 1, 2, 6):
            self.assertEqual(self.run_type(self.patched, n, 5, 0), 1)
            self.assertEqual(self.run_type(self.patched, n, 5, 0, flag=1), 0x801)
            self.assertEqual(self.run_type(self.patched, n, 507, 0, partner=64), 1)

    def test_trainer_two_cleared_on_downgrade(self):
        # trainer 2 is stored in the setup at +0x24 (the stub setup is a plain memory block)
        for n, want in ((1, 0), (2, 778)):
            s = Setup(bytes(self.patched), n, 777, 778, 0)
            s.run()
            self.assertEqual(s.r32(NEWSETUP + 0x24), want)
            self.assertEqual(s.r32(NEWSETUP + 0x1C), 777)

    def test_only_two_regions_change(self):
        diff = [i for i in range(len(self.native)) if self.native[i] != self.patched[i]]
        self.assertTrue(all(0x48EC8 <= i < 0x48EF4 or 0x507A4 <= i < 0x507AC for i in diff))
        self.assertEqual(len(self.patched), len(self.native))


if __name__ == "__main__":
    unittest.main()
