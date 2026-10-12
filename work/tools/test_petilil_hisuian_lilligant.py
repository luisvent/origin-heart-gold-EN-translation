#!/usr/bin/env python3
"""petilil-hisuian-lilligant (D-2334): the evolution setup builds species 549 (Lilligant) for the form-species id
1361, not 548 (Petilil). Run:
    ARMIPS=/path/to/armips python3 -I -m unittest -v work/tools/test_petilil_hisuian_lilligant.py
The ROM tests are skipped without armips v0.11.0 or work/rom/origin_v4.0.3_cn.nds."""
import struct
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import asmpatch as A  # noqa: E402
import fixes as F  # noqa: E402

ROM_CN = HERE.parent / "rom" / "origin_v4.0.3_cn.nds"


def _armips():
    try:
        p = A.find_armips()
        A.check_armips(p)
        return p
    except A.AsmError:
        return None


ARMIPS = _armips()
FIX = "petilil-hisuian-lilligant"
SITE = 0x74148            # arm9 offset of the 1361 case of the evolution setup (RAM 0x02074148)

OLD = "2589 1C38 2170 AA09 00AD"       # movs r5,#0x89 ; adds r0,r7,#0 ; movs r1,#0x70 ; add r2,sp,#0x24 ; lsls r5,r5,#2
# adds r0,r7,#0 ; movs r1,#0x70 ; add r2,sp,#0x24 ; lsls r5,r1,#2 ; adds r5,#0x65   (0x70 * 4 + 0x65 = 549)
NEW = "1C38 2170 AA09 008D 3565"


def hw(text):
    return b"".join(struct.pack("<H", int(x, 16)) for x in text.split())


class Registry(unittest.TestCase):
    def test_region_and_numbers(self):
        fx = {f["id"]: f for f in F.load_all()}[FIX]
        (region,) = fx["code"]
        self.assertEqual((region["file"], region["offset"], region["expect"]), ("arm9", "0x74148", OLD))
        # the new species is Lilligant: 0x70 * 4 + 0x65, the old one 0x89 * 4
        self.assertEqual(0x70 * 4 + 0x65, 549)
        self.assertEqual(0x89 << 2, 548)
        self.assertEqual(int.from_bytes(hw(NEW)[6:8], "little"), 0x008D)

    def test_no_overlap_with_evolution_moves(self):
        fixes = {f["id"]: f for f in F.load_all()}
        mine = (SITE, SITE + 10)
        for r in fixes["evolution-moves"]["code"]:
            lo = int(r["offset"], 16)
            hi = lo + len(r["expect"].split()) * 2
            self.assertTrue(hi <= mine[0] or lo >= mine[1], r["id"])


@unittest.skipUnless(ROM_CN.exists() and ARMIPS, "Chinese ROM or armips missing")
class Bytes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import hardcoded as hc
        import msgtool as m
        cls.hc, cls.m = hc, m
        cls.fixes = {f["id"]: f for f in F.load_all()}

    def arm9(self, ids):
        rom = self.m.load_rom(ROM_CN)
        A.apply(rom, [self.fixes[i] for i in ids], ARMIPS)
        return bytes(self.hc.RomView(rom).get("arm9"))

    def test_only_these_ten_bytes_change(self):
        old = bytes(self.hc.RomView(self.m.load_rom(ROM_CN)).get("arm9"))
        new = self.arm9([FIX])
        self.assertEqual(old[SITE:SITE + 10], hw(OLD))
        self.assertEqual(new[SITE:SITE + 10], hw(NEW))
        self.assertEqual(new[:SITE], old[:SITE])
        self.assertEqual(new[SITE + 10:], old[SITE + 10:])
        # the SetMonData call and the branch after it are the hack's
        self.assertEqual(new[SITE + 10:SITE + 14], hw("F7F9 FF0D"))

    def test_with_evolution_moves(self):
        both = self.arm9(["evolution-moves", FIX])
        only_moves = self.arm9(["evolution-moves"])
        diff = [i for i in range(len(both)) if both[i] != only_moves[i]]
        self.assertTrue(diff and SITE <= diff[0] and diff[-1] < SITE + 10)
        self.assertEqual(both[SITE:SITE + 10], hw(NEW))


if __name__ == "__main__":
    unittest.main()
