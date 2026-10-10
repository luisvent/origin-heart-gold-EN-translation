"""Verify Magcargo's guarded branch repair and native outcome semantics."""

import copy
import hashlib
import sys
import unittest
from pathlib import Path

import ndspy.codeCompression

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "docs")]
import double_target_thumb_model as T
import fixes as F
import msgtool as M
import narcpatch as N
import romdata as R


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class MagcargoLossTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = M.load_rom(F.ROM_CN)
        cls.arm9 = ndspy.codeCompression.decompress(rom.arm9)
        cls.archive = M.get_file(rom, "a/0/1/2")
        cls.fix = next(f for f in F.load_all() if f["id"] == "magcargo-loss-whiteout")

    def apply(self):
        store = {"a/0/1/2": self.archive}
        report = N.apply(store.__getitem__, store.__setitem__, [self.fix])
        self.assertEqual(N.verify(store.__getitem__, report), "ok (1 entries, 1 members)")
        return M.Narc.parse(store["a/0/1/2"]).files

    def native_won(self, raw):
        # Execute the actual helper with the existing Thumb interpreter, not a
        # duplicate Python implementation of its result predicate.
        cpu = T.CPU(b"", 0)
        cpu.r[0], cpu.r[14] = raw, 0x0DEAD001
        pc = 0x0205172C
        for _ in range(12):
            if pc == 0x0DEAD000:
                return cpu.r[0]
            ins = next(T.md.disasm(self.arm9[pc - 0x02000000:pc - 0x02000000 + 4], pc, 1))
            pc = cpu.step(ins, pc)
        self.fail("native outcome helper did not return")

    def test_actual_native_outcome_helper(self):
        # Pin the entire tiny helper and its caller's call/store sequence.
        self.assertEqual(self.arm9[0x5172C:0x5173C].hex(), "022801d0032801d10020704701207047")
        self.assertEqual(self.arm9[0x48E12:0x48E1A].hex(), "206808f08afc2880")
        for raw in list(range(256)) + [0x100, 0xFFFF, 0xFFFFFFFF]:
            with self.subTest(raw=raw):
                self.assertEqual(self.native_won(raw), int(raw not in (2, 3)))

    def test_only_loss_branch_changes_and_all_outcomes(self):
        before = M.Narc.parse(self.archive).files
        after = self.apply()
        self.assertEqual([i for i in range(len(before)) if before[i] != after[i]], [17])
        a, b = before[17], after[17]
        self.assertEqual(len(a), 14766)
        self.assertEqual(len(a), len(b))
        self.assertEqual([i for i, (x, y) in enumerate(zip(a, b)) if x != y], list(range(2549, 2553)))
        entries, ins = R.disasm(a)
        newentries, newins = R.disasm(b)
        self.assertEqual(entries, newentries)
        self.assertEqual(set(ins), set(newins))
        self.assertEqual([p for p in ins if ins[p] != newins[p]], [2546])
        self.assertEqual(ins[2546][3], 2519)
        self.assertEqual(newins[2546][3], 3914)
        self.assertEqual(newins[2546][1][0], 1)  # equality
        self.assertEqual(newins[2540][1], [0x800C, 0])
        self.assertEqual(newins[2529][1], [219, 65320, 0])
        self.assertEqual([R.cmds()[newins[p][0]][0] for p in (3914, 3916, 3918)], ["WhiteOut", "ReleaseAll", "End"])
        for raw in range(8):
            destination = newins[2546][3] if self.native_won(raw) == 0 else newins[2546][2]
            self.assertEqual(destination, 3914 if raw in (2, 3) else 2553)
        # Native one-visit visibility, decline, progress and every nonloss hide
        # command are preserved. No new flag allocation or map-init recovery.
        self.assertEqual(newins[2493][1], [1155])
        self.assertEqual(newins[2509][1], [0x40B7, 1])
        self.assertEqual(newins[2553][1], [1155])
        hidden = [row[1][0] for p, row in newins.items() if 2553 <= p <= 2587 and R.cmds()[row[0]][0] == "HidePerson"]
        self.assertEqual(sorted(hidden), [3, 5, 8, 9, 10, 12, 13])
        self.assertEqual(b[648:700], a[648:700])
        self.assertEqual(b[2553:], a[2553:])
        self.assertEqual(before[278], after[278])

    def test_whole_member_guard_rejects_changed_source(self):
        for offset in (0, 648, 2493, 2549, 2553, 14765):
            files = M.Narc.parse(self.archive).files
            bad = bytearray(files[17])
            bad[offset] ^= 1
            files[17] = bytes(bad)
            store = {"a/0/1/2": M.Narc(files).build()}
            original = store["a/0/1/2"]
            with self.assertRaises(N.NarcPatchError):
                N.apply(store.__getitem__, store.__setitem__, [self.fix])
            self.assertEqual(store["a/0/1/2"], original)

    def test_expected_bytes_guard_independently(self):
        files = M.Narc.parse(self.archive).files
        bad = bytearray(files[17])
        bad[2549] ^= 1
        files[17] = bytes(bad)
        fix = copy.deepcopy(self.fix)
        fix["narc_bytes"][0]["member_sha1"] = hashlib.sha1(bad).hexdigest()
        store = {"a/0/1/2": M.Narc(files).build()}
        original = store["a/0/1/2"]
        with self.assertRaisesRegex(N.NarcPatchError, "expected"):
            N.apply(store.__getitem__, store.__setitem__, [fix])
        self.assertEqual(store["a/0/1/2"], original)


if __name__ == "__main__":
    unittest.main()
