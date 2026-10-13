"""Execute the actual assembled collector with adversarial native-helper stubs."""

import unittest
from pathlib import Path
import asmpatch
import fixes
import hardcoded
import msgtool
from honey_gather_thumb import Thumb, md, OVB

ROM = Path(__file__).resolve().parents[1] / "rom/origin_v4.0.3_cn.nds"
ENTRY = 0x0222BCC8
RET = 0x0DEAD000
OUT = 0x02302000
PARTY = 0x02303000
ACTOR = 0x02310000
MON = 0x02320000
BAG = 0x02330000
CONTEXT = 0x02340000


class Collector(Thumb):
    def __init__(self, code, mons, rolls=(), room=True):
        super().__init__(code)
        self.mons = mons
        self.rolls = iter(rolls)
        self.room = room
        self.awards = []
        self.random = []
        self.w32(0x02255BAC, 0x02300000)
        self.w32(0x02300010, 0x02301000)
        self.w32(0x02301004, PARTY)
        self.w32(0x02301108, BAG)
        for i, m in enumerate(mons):
            a = ACTOR + i * 0x500
            self.w32(a + 0x10, MON + i * 236)
            self.w32(a + 0x16, m.get("ability", 118))
            self.w32(a + 0x20, m.get("item", 0))
            self.w8(a + 0x24, m.get("level", 31))
        for i in range(16):
            self.w8(OUT - 2 + i, 0xA7)
        self.decoded = {}

    def native(self, pc):
        r = self.r
        if pc == 0x02073398:
            assert r[0] == PARTY
            return len(self.mons)
        if pc == 0x02230920:
            assert r[:2] == [CONTEXT, 0]
            assert r[2] < len(self.mons)
            return ACTOR + r[2] * 0x500
        if pc == 0x0206D848:
            assert r[1:3] == [0x4C, 0]
            assert (r[0] - MON) % 236 == 0 and 0 <= (r[0] - MON) // 236 < len(self.mons)
            return int(self.mons[(r[0] - MON) // 236].get("egg", False))
        if pc == 0x02217BE8:
            return 415
        if pc == 0x022167B4:
            return MON + ((r[0] - ACTOR) // 0x500) * 236
        if pc == 0x02217BF8:
            return self.mons[(r[0] - ACTOR) // 0x500].get("ability", 118)
        if pc == 0x02218104:
            return self.mons[(r[0] - ACTOR) // 0x500].get("level", 31)
        if pc == 0x020F1218:
            return r[0] // r[1]
        if pc in (0x022264C0, 0x0222646C):
            roll = next(self.rolls)
            self.random.append((pc, r[0], roll))
            return int(roll < r[0]) if pc == 0x022264C0 else roll % r[0]
        if pc == 0x02076A08:
            assert r[0] == BAG and r[2:4] == [1, 5]
            room = self.room if isinstance(self.room, bool) else len(self.awards) < self.room
            if room:
                self.awards.append(r[1])
            return int(room)
        return None

    def run(self):
        saved = [0xA5000000 + i for i in range(4, 8)]
        self.r[:3] = [CONTEXT, 0, OUT]
        self.r[4:8] = saved
        self.r[13:15] = [self.stack_top, RET | 1]
        pc = ENTRY
        for _ in range(10000):
            if pc == RET:
                assert self.r[4:8] == saved and self.r[13] == self.stack_top
                assert self.r8(OUT - 1) == 0xA7 and self.r8(OUT + 2 * len(self.mons)) == 0xA7
                return self.r[0], [self.r8(OUT + 2 * i) | self.r8(OUT + 2 * i + 1) << 8 for i in range(len(self.mons))]
            result = self.native(pc)
            if result is not None:
                assert self.r[13] % 8 == 0, hex(pc)
                self.clobber_callers()
                self.r[0] = result
                pc = self.r[14] & ~1
            else:
                if pc not in self.decoded:
                    self.decoded[pc] = next(md.disasm(self.ov[pc - OVB : pc - OVB + 4], pc, 1))
                pc = self.step(self.decoded[pc], pc)
        raise AssertionError("collector did not return")


@unittest.skipUnless(ROM.exists() and ROM.stat().st_size > 100_000_000, "needs local Chinese ROM")
class HoneyGatherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            assembler = asmpatch.find_armips()
        except asmpatch.AsmError as exc:
            raise unittest.SkipTest(str(exc)) from exc
        cls.native = hardcoded.RomView(msgtool.load_rom(str(ROM))).get("overlay14")
        cls.fix = next(f for f in fixes.load_all() if f["id"] == "honey-gather")
        cls.patched = asmpatch.assemble([cls.fix], {"overlay14": cls.native}, assembler)[0]["overlay14"]

    def test_all_levels_and_rolls(self):
        for level in range(1, 101):
            for roll in range(100):
                c = Collector(self.patched, [dict(level=level)], [roll])
                success = roll < 5 * ((level - 1) // 10 + 1)
                self.assertEqual(c.run(), (int(success), [94 if success else 0]), (level, roll))
                self.assertEqual(c.awards, [94] if success else [])

    def test_native_reproduces_honey_omission(self):
        c = Collector(self.native, [dict(level=100)], [])
        self.assertEqual(c.run(), (0, [0]))
        self.assertEqual(c.random, [])

    def test_eligibility(self):
        for mon in [dict(egg=True), dict(item=1), dict(item=94), dict(ability=0), dict(ability=139), dict(ability=237)]:
            c = Collector(self.patched, [mon], [])
            self.assertEqual(c.run(), (0, [0]), mon)
            self.assertEqual(c.random, [])

    def test_full_bag_and_last_slot(self):
        for ability in [53, 118]:
            rolls = [0, 0] if ability == 53 else [0]
            c = Collector(self.patched, [dict(ability=ability)], rolls, room=False)
            self.assertEqual(c.run(), (0, [0]))
            self.assertEqual(c.awards, [])
        c = Collector(self.patched, [{}] * 6, [0] * 6, room=1)
        self.assertEqual(c.run(), (1, [94, 0, 0, 0, 0, 0]))

    def test_multiple_holders_and_mixed_party(self):
        c = Collector(self.patched, [{}] * 6, [0] * 6)
        self.assertEqual(c.run(), (6, [94] * 6))
        c = Collector(
            self.patched,
            [{}, dict(egg=True), dict(ability=53, item=1), dict(item=94), dict(ability=30), {}],
            [0, 0, 0, 99],
        )
        result = c.run()
        self.assertEqual(result[0], 2)
        self.assertEqual(result[1][0], 94)
        self.assertEqual(result[1][1], 0)
        self.assertEqual(result[1][3:], [0, 0, 0])
        self.assertEqual(len(c.awards), 2)
        self.assertEqual(Collector(self.patched, []).run(), (0, []))

    def test_pickup_matches_native_every_band_and_reward_roll(self):
        for level in [1, 10, 11, 20, 21, 30, 31, 40, 41, 50, 51, 60, 61, 70, 71, 80, 81, 90, 91, 100]:
            for roll in range(100):
                mons = [dict(ability=53, level=level, item=1)]
                a = Collector(self.native, mons, [0, roll])
                b = Collector(self.patched, mons, [0, roll])
                self.assertEqual(a.run(), b.run(), (level, roll))
                self.assertEqual(a.awards, b.awards)
                self.assertEqual(a.random, b.random)
        for gate in range(10, 100):
            c = Collector(self.patched, [dict(ability=53)], [gate])
            self.assertEqual(c.run(), (0, [0]))

    def test_only_declared_region_changes_and_no_growth(self):
        self.assertEqual(len(self.native), len(self.patched))
        diffs = [i for i, (a, b) in enumerate(zip(self.native, self.patched)) if a != b]
        self.assertTrue(diffs)
        self.assertTrue(all(0x2B4E8 <= i < 0x2B5E0 for i in diffs))

    def test_guards_reject_changed_dependencies(self):
        for addr in [0x22167B4, 0x2217BF8, 0x2218104, 0x221679C, 0x2216154, ENTRY]:
            image = bytearray(self.native)
            image[addr - OVB] ^= 1
            with self.assertRaises(asmpatch.AsmError):
                asmpatch.assemble([self.fix], {"overlay14": bytes(image)}, asmpatch.find_armips())


if __name__ == "__main__":
    unittest.main()
