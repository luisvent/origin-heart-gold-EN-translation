"""Verify the Cynthia romance-scene repair: three byte edits, branch structure otherwise untouched."""

import copy
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "docs")]
import fixes as F
import msgtool as M
import narcpatch as N
import romdata as R


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class RomanceMailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = M.load_rom(F.ROM_CN)
        cls.archive = M.get_file(rom, "a/0/1/2")
        cls.fix = next(f for f in F.load_all() if f["id"] == "romance-mail-mismatch")

    def apply(self, fix=None):
        store = {"a/0/1/2": self.archive}
        report = N.apply(store.__getitem__, store.__setitem__, [fix or self.fix])
        self.assertTrue(N.verify(store.__getitem__, report).startswith("ok"))
        return M.Narc.parse(store["a/0/1/2"]).files

    def test_only_three_bytes_change(self):
        before = M.Narc.parse(self.archive).files
        after = self.apply()
        changed = [i for i in range(len(before)) if before[i] != after[i]]
        self.assertEqual(changed, [842, 843])
        diffs = {i: [(o, x, y) for o, (x, y) in enumerate(zip(before[i], after[i])) if x != y] for i in changed}
        self.assertEqual(diffs[842], [(7163, 212, 218), (8419, 139, 144)])
        self.assertEqual(diffs[843], [(2440, 143, 144)])
        for i in changed:
            self.assertEqual(len(before[i]), len(after[i]))

    def test_branch_consistency(self):
        before = M.Narc.parse(self.archive).files
        after = self.apply()
        C = R.cmds()
        name = lambda ins, pc: C[ins[pc][0]][0]
        _, i842 = R.disasm(after[842])
        _, i843 = R.disasm(after[843])
        _, o842 = R.disasm(before[842])
        self.assertEqual(set(i842), set(o842))
        # Cynthia: check item 144 (842@7063, 843@1318) == taken item (842@8417, 843@2438)
        self.assertEqual(i842[7063][1][0], 144)
        self.assertEqual(i843[1318][1][0], 144)
        self.assertEqual(i842[8417][1][0], 144)
        self.assertEqual(i843[2438][1][0], 144)
        for pc in (7161, 7228, 8389):
            self.assertEqual(name(i842, pc), "NPCMsg")
            self.assertEqual(i842[pc][1], [218])
        # Other branches (Yellow, Green, Misty) are untouched and self-consistent.
        for chk, take, ins in ((6462, 7811, i842), (6707, 8075, i842), (6887, 8246, i842)):
            self.assertEqual(ins[chk][1][0], ins[take][1][0])
        self.assertEqual((i843[1345][1][0], i843[2836][1][0]), (143, 143))
        self.assertEqual((i843[1372][1][0], i843[3234][1][0]), (137, 137))
        # Misty love letter left as in the hack (D-2332): check 137, take 139.
        self.assertEqual((i843[1399][1][0], i843[3637][1][0]), (137, 139))

    def test_guards_reject_changed_source(self):
        for mem, off in ((842, 7163), (842, 8419), (843, 2440), (843, 5)):
            files = M.Narc.parse(self.archive).files
            bad = bytearray(files[mem])
            bad[off] ^= 1
            files[mem] = bytes(bad)
            store = {"a/0/1/2": M.Narc(files).build()}
            original = store["a/0/1/2"]
            with self.assertRaises(N.NarcPatchError):
                N.apply(store.__getitem__, store.__setitem__, [self.fix])
            self.assertEqual(store["a/0/1/2"], original)


if __name__ == "__main__":
    unittest.main()
