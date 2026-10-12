"""Verify the weekday-sibling ribbon repair: only the invalid opcode bytes change and the scripts now run to End."""

import copy
import struct
import sys
import unittest

HERE = __import__("pathlib").Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "docs")]
import fixes as F
import msgtool as M
import narcpatch as N
import romdata as R

SIBLINGS = {225: 3985, 232: 12121, 243: 2334, 246: 764, 934: 5653, 937: 2784, 958: 1078}
TAIL = ["CloseMsg", "ReleaseAll", "End"]


def op_at(data, pc):
    return struct.unpack_from("<H", data, pc)[0]


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class SiblingRibbonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = M.load_rom(F.ROM_CN)
        cls.archive = M.get_file(rom, "a/0/1/2")
        cls.fix = next(f for f in F.load_all() if f["id"] == "sibling-ribbon-freeze")
        cls.cmds = R.cmds()

    def apply(self, archive=None, fix=None):
        store = {"a/0/1/2": self.archive if archive is None else archive}
        report = N.apply(store.__getitem__, store.__setitem__, [fix or self.fix])
        self.assertEqual(N.verify(store.__getitem__, report), "ok (7 entries, 7 members)")
        return M.Narc.parse(store["a/0/1/2"]).files

    def test_original_has_exactly_seven_out_of_range_commands(self):
        limit = max(self.cmds) + 1
        self.assertEqual(limit, 843)
        found = {}
        for i, data in enumerate(M.Narc.parse(self.archive).files):
            _, ins = R.disasm(data)
            for pc, (_, _, nxt, _) in ins.items():
                if nxt + 2 <= len(data) and nxt not in ins and op_at(data, nxt) >= limit:
                    if ins[pc][0] not in (2, 27) and self.cmds[ins[pc][0]][0] != "GoTo":
                        found[i] = nxt
        self.assertEqual(found, SIBLINGS)
        for i, off in SIBLINGS.items():
            self.assertEqual(op_at(M.Narc.parse(self.archive).files[i], off), 2009)

    def test_only_the_two_bytes_change_and_script_reaches_end(self):
        before = M.Narc.parse(self.archive).files
        after = self.apply()
        self.assertEqual([i for i in range(len(before)) if before[i] != after[i]], sorted(SIBLINGS))
        for i, off in SIBLINGS.items():
            a, b = before[i], after[i]
            self.assertEqual(len(a), len(b))
            self.assertEqual([k for k, (x, y) in enumerate(zip(a, b)) if x != y], [off, off + 1])
            self.assertEqual(b[off : off + 2], b"\x00\x00")
            self.assertEqual(self.cmds[0][0], "Noop")
            _, ins_a = R.disasm(a)
            _, ins_b = R.disasm(b)
            # every instruction that decoded before is unchanged
            self.assertTrue(all(ins_b[pc] == row for pc, row in ins_a.items()))
            # after PlayFanfare: Noop, CloseMsg, ReleaseAll, End, all decoded now
            names, pc = [], off - 4
            for _ in range(5):
                names.append(self.cmds[ins_b[pc][0]][0])
                pc = ins_b[pc][2]
            self.assertEqual(names, ["PlayFanfare", "Noop"] + TAIL)
            self.assertEqual(ins_b[off - 4][1], [20])
            self.assertEqual(self.cmds[ins_b[off - 10][0]][0], "GiveRibbon")
            self.assertNotIn(off, [r[3] for r in ins_a.values()])  # no jump lands in the patched bytes

    def test_no_out_of_range_command_remains(self):
        limit = max(self.cmds) + 1
        for i, off in SIBLINGS.items():
            data = self.apply()[i]
            _, ins = R.disasm(data)
            self.assertTrue(all(row[0] < limit for row in ins.values()))
            self.assertIn(off + 2, ins)

    def test_guards_reject_changed_source(self):
        for member, off in SIBLINGS.items():
            files = M.Narc.parse(self.archive).files
            bad = bytearray(files[member])
            bad[off - 1] ^= 1
            files[member] = bytes(bad)
            store = {"a/0/1/2": M.Narc(files).build()}
            original = store["a/0/1/2"]
            with self.assertRaises(N.NarcPatchError):
                N.apply(store.__getitem__, store.__setitem__, [self.fix])
            self.assertEqual(store["a/0/1/2"], original)

    def test_expected_bytes_guard_independently(self):
        import hashlib

        files = M.Narc.parse(self.archive).files
        bad = bytearray(files[225])
        bad[3985] ^= 1
        files[225] = bytes(bad)
        fix = copy.deepcopy(self.fix)
        fix["narc_bytes"][0]["member_sha1"] = hashlib.sha1(bad).hexdigest()
        store = {"a/0/1/2": M.Narc(files).build()}
        with self.assertRaisesRegex(N.NarcPatchError, "expected"):
            N.apply(store.__getitem__, store.__setitem__, [fix])


if __name__ == "__main__":
    unittest.main()
