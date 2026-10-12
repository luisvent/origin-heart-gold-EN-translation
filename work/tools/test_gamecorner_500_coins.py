"""Verify gamecorner-500-coins: only the listed operand bytes change, the script structure is untouched, the guards refuse another member."""

import hashlib
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "docs")]
import fixes as F
import msgtool as M
import narcpatch as N
import romdata as R

MEMBER = 903
EDITS = [(7596, 'CheckGiveCoins', 1, 50, 500), (7623, 'GiveCoins', 0, 50, 500)]


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class FixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = M.load_rom(F.ROM_CN)
        cls.archive = M.get_file(rom, "a/0/1/2")
        cls.fix = next(f for f in F.load_all() if f["id"] == "gamecorner-500-coins")
        cls.before = M.Narc.parse(cls.archive).files
        _, cls.ins_before = R.disasm(cls.before[MEMBER])

    def apply(self, archive=None):
        store = {"a/0/1/2": self.archive if archive is None else archive}
        report = N.apply(store.__getitem__, store.__setitem__, [self.fix])
        self.assertTrue(N.verify(store.__getitem__, report).startswith("ok"))
        return M.Narc.parse(store["a/0/1/2"]).files

    def test_member_sha1_is_the_hacks(self):
        self.assertEqual(hashlib.sha1(self.before[MEMBER]).hexdigest(), "b18925a2b274f2056c29b18773b0861d08c3c53f")

    def test_only_the_operands_change(self):
        after = self.apply()
        self.assertEqual([i for i in range(len(self.before)) if self.before[i] != after[i]], [MEMBER])
        a, b = self.before[MEMBER], after[MEMBER]
        self.assertEqual(len(a), len(b))
        diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        # every differing byte lies inside the operand of a listed edit
        spans = [(pc + 2, min(p for p in self.ins_before if p > pc)) for pc, *_ in EDITS]
        for i in diff:
            self.assertTrue(any(lo <= i < hi for lo, hi in spans), i)
        self.assertLessEqual(len(diff), 4)

    def test_operands_and_structure(self):
        after = self.apply()
        C = R.cmds()
        names = lambda ins, pc: C[ins[pc][0]][0]
        entries_b, i_before = R.disasm(self.before[MEMBER])
        entries_a, i_after = R.disasm(after[MEMBER])
        self.assertEqual(entries_a, entries_b)
        self.assertEqual(set(i_after), set(i_before))
        for pc in i_before:
            self.assertEqual((i_after[pc][0], i_after[pc][2], i_after[pc][3]), (i_before[pc][0], i_before[pc][2], i_before[pc][3]))
        edited = {e[0] for e in EDITS}
        for pc in i_before:
            if pc not in edited:
                self.assertEqual(i_after[pc][1], i_before[pc][1], pc)
        for pc, cmd, argi, old, new in EDITS:
            self.assertEqual(names(i_before, pc), cmd)
            self.assertEqual(names(i_after, pc), cmd)
            self.assertEqual(i_before[pc][1][argi], old)
            self.assertEqual(i_after[pc][1][argi], new)

    def test_guard_refuses_another_member(self):
        files = M.Narc.parse(self.archive).files
        tampered = bytearray(files[MEMBER])
        tampered[-1] ^= 1
        files[MEMBER] = bytes(tampered)
        narc = M.Narc.parse(self.archive)
        narc.files = files
        with self.assertRaises(N.NarcPatchError):
            self.apply(narc.build() if hasattr(narc, "build") else None)


if __name__ == "__main__":
    unittest.main()
