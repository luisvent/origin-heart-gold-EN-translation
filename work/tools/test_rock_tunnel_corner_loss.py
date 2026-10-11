"""Verify the real script repair, source guards and unchanged quest structure."""

import copy
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


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class CornerLossTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = M.load_rom(F.ROM_CN)
        cls.archive = M.get_file(rom, "a/0/1/2")
        cls.fix = next(f for f in F.load_all() if f["id"] == "rock-tunnel-corner-loss")

    def apply(self, archive=None, fix=None):
        store = {"a/0/1/2": self.archive if archive is None else archive}
        report = N.apply(store.__getitem__, store.__setitem__, [fix or self.fix])
        self.assertEqual(N.verify(store.__getitem__, report), "ok (1 entries, 1 members)")
        return M.Narc.parse(store["a/0/1/2"]).files

    def test_only_loss_branch_changes(self):
        before = M.Narc.parse(self.archive).files
        after = self.apply()
        self.assertEqual([i for i in range(len(before)) if before[i] != after[i]], [129])
        a, b = before[129], after[129]
        self.assertEqual(len(a), 6030)
        self.assertEqual(len(a), len(b))
        self.assertEqual([i for i, (x, y) in enumerate(zip(a, b)) if x != y], list(range(2900, 2904)))
        entries_a, ins_a = R.disasm(a)
        entries_b, ins_b = R.disasm(b)
        self.assertEqual(entries_a, entries_b)
        self.assertEqual(set(ins_a), set(ins_b))
        self.assertEqual([pc for pc in ins_a if ins_a[pc] != ins_b[pc]], [2897])
        self.assertEqual(ins_a[2897][3], 3782)
        self.assertEqual(ins_b[2897][3], 2734)
        self.assertEqual(ins_b[2897][1][0], 1)  # equality: won == 0
        self.assertEqual(ins_b[2879][1], [606, 0, 0, 0])
        self.assertEqual([R.cmds()[ins_b[pc][0]][0] for pc in (2734, 2736, 2738)], ["WhiteOut", "ReleaseAll", "End"])
        # Victory writes only the corner flag; the reward/completion readers and
        # writers, and all other children's loss branches remain byte-identical.
        self.assertEqual(b[2904:2918], a[2904:2918])
        self.assertEqual(ins_b[2911][1], [1966])
        self.assertEqual(b[1283:1624], a[1283:1624])
        self.assertEqual(
            sum(row[3] == 2734 for row in ins_b.values()), sum(row[3] == 2734 for row in ins_a.values()) + 1
        )

    def test_whole_member_guard_rejects_changed_source(self):
        for offset in (0, 2879, 2900, 2911, 6029):
            files = M.Narc.parse(self.archive).files
            bad = bytearray(files[129])
            bad[offset] ^= 1
            files[129] = bytes(bad)
            store = {"a/0/1/2": M.Narc(files).build()}
            original = store["a/0/1/2"]
            with self.assertRaises(N.NarcPatchError):
                N.apply(store.__getitem__, store.__setitem__, [self.fix])
            self.assertEqual(store["a/0/1/2"], original)

    def test_expected_bytes_guard_independently(self):
        files = M.Narc.parse(self.archive).files
        bad = bytearray(files[129])
        bad[2900] ^= 1
        files[129] = bytes(bad)
        fix = copy.deepcopy(self.fix)
        fix["narc_bytes"][0]["member_sha1"] = hashlib.sha1(bad).hexdigest()
        store = {"a/0/1/2": M.Narc(files).build()}
        original = store["a/0/1/2"]
        with self.assertRaisesRegex(N.NarcPatchError, "expected"):
            N.apply(store.__getitem__, store.__setitem__, [fix])
        self.assertEqual(store["a/0/1/2"], original)


if __name__ == "__main__":
    unittest.main()
