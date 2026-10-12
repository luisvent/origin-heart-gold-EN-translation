"""Verify the S.S. Anne voyage fix: boarding sets the pre-party flag 1440 and nothing else in the scripts changes."""

import copy
import hashlib
import sys
import unittest

HERE = __import__("pathlib").Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "docs")]
import fixes as F
import msgtool as M
import narcpatch as N
import romdata as R

SAILOR, SAILOR_OFF = 155, 152
PRE_PARTY = 1440


def name(cmds, op):
    return cmds[op][0]


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class SsAnneSoftlockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = M.load_rom(F.ROM_CN)
        cls.archive = M.get_file(rom, "a/0/1/2")
        cls.fix = next(f for f in F.load_all() if f["id"] == "ss-anne-softlock")
        cls.cmds = R.cmds()
        cls.files = M.Narc.parse(cls.archive).files

    def apply(self, archive=None, fix=None):
        store = {"a/0/1/2": self.archive if archive is None else archive}
        report = N.apply(store.__getitem__, store.__setitem__, [fix or self.fix])
        self.assertEqual(N.verify(store.__getitem__, report), "ok (1 entries, 1 members)")
        return M.Narc.parse(store["a/0/1/2"]).files

    def flag_ops(self, files, flag):
        """Every (member, pc, command name) that sets, clears or checks flag, over the whole archive."""
        out = []
        for i, data in enumerate(files):
            _, ins = R.disasm(data)
            for pc, (op, args, _, _) in ins.items():
                if name(self.cmds, op) in ("SetFlag", "ClearFlag", "CheckFlag") and args == [flag]:
                    out.append((i, pc, name(self.cmds, op)))
        return sorted(out)

    def test_cause_nothing_sets_the_flag_before_the_hijack(self):
        ops = self.flag_ops(self.files, PRE_PARTY)
        sets = [o for o in ops if o[2] == "SetFlag"]
        clears = [o for o in ops if o[2] == "ClearFlag"]
        self.assertEqual(sets, [(156, 6350, "SetFlag")])        # the hijack evacuation only
        self.assertEqual(clears, [(157, 550, "ClearFlag"), (161, 1901, "ClearFlag")])   # the two party starts
        checks = {(m, pc) for m, pc, n in ops if n == "CheckFlag"}
        self.assertIn((157, 124), checks)                      # the Captain's HM01 branch
        self.assertIn((156, 1023), checks)

    def test_replaced_instruction_is_dead_and_next_jump_not_taken(self):
        data = self.files[SAILOR]
        _, ins = R.disasm(data)
        # linear run 117..152: ClearFlag 235, SetFlag 554, ClearFlag 556, SetFlag 555, CheckBadge,
        # CompareVarToValue, GoToIf, then the CheckFlag 235 we replace
        pcs = [117, 121, 125, 129, 133, 139, 145, 152]
        self.assertEqual([name(self.cmds, ins[p][0]) for p in pcs],
                         ["ClearFlag", "SetFlag", "ClearFlag", "SetFlag", "CheckBadge", "CompareVarToValue",
                          "GoToIf", "CheckFlag"])
        self.assertEqual(ins[117][1], [235])
        self.assertEqual(ins[152][1], [235])
        for a, b in zip(pcs, pcs[1:]):
            self.assertEqual(ins[a][2], b)
        # nothing jumps into the run, so 235 is clear when offset 152 is reached
        targets = {t for (_, _, _, t) in ins.values() if t is not None}
        self.assertFalse(targets & set(pcs[1:]))
        self.assertEqual(ins[145][1][0], 1)                    # GoToIf EQ after the compare with 1: badge branch
        self.assertEqual(ins[156][1][0], 1)                    # the GoToIf after the replaced instruction: EQ
        self.assertEqual(name(self.cmds, ins[156][0]), "GoToIf")

    def test_only_the_four_bytes_change_and_decode_stays_equal(self):
        after = self.apply()
        changed = [i for i in range(len(self.files)) if self.files[i] != after[i]]
        self.assertEqual(changed, [SAILOR])
        a, b = self.files[SAILOR], after[SAILOR]
        self.assertEqual(len(a), len(b))
        diff_bytes = [k for k, (x, y) in enumerate(zip(a, b)) if x != y]
        self.assertTrue(all(SAILOR_OFF <= k < SAILOR_OFF + 4 for k in diff_bytes))
        self.assertEqual(b[SAILOR_OFF : SAILOR_OFF + 4].hex(), "1e00a005")
        _, ins_a = R.disasm(a)
        _, ins_b = R.disasm(b)
        self.assertEqual(set(ins_a), set(ins_b))
        diff = [pc for pc in ins_a if ins_a[pc] != ins_b[pc]]
        self.assertEqual(diff, [SAILOR_OFF])
        self.assertEqual(name(self.cmds, ins_b[SAILOR_OFF][0]), "SetFlag")
        self.assertEqual(ins_b[SAILOR_OFF][1], [PRE_PARTY])
        self.assertEqual(ins_b[SAILOR_OFF][2], ins_a[SAILOR_OFF][2])   # same length

    def test_flag_writers_after_the_fix(self):
        after = self.apply()
        sets = [o for o in self.flag_ops(after, PRE_PARTY) if o[2] == "SetFlag"]
        self.assertEqual(sets, [(155, SAILOR_OFF, "SetFlag"), (156, 6350, "SetFlag")])

    def test_guards_reject_changed_source(self):
        files = M.Narc.parse(self.archive).files
        bad = bytearray(files[SAILOR])
        bad[SAILOR_OFF - 1] ^= 1
        files[SAILOR] = bytes(bad)
        store = {"a/0/1/2": M.Narc(files).build()}
        original = store["a/0/1/2"]
        with self.assertRaises(N.NarcPatchError):
            N.apply(store.__getitem__, store.__setitem__, [self.fix])
        self.assertEqual(store["a/0/1/2"], original)

    def test_expected_bytes_guard_independently(self):
        files = M.Narc.parse(self.archive).files
        bad = bytearray(files[SAILOR])
        bad[SAILOR_OFF] ^= 1
        files[SAILOR] = bytes(bad)
        fix = copy.deepcopy(self.fix)
        fix["narc_bytes"][0]["member_sha1"] = hashlib.sha1(bad).hexdigest()
        store = {"a/0/1/2": M.Narc(files).build()}
        with self.assertRaisesRegex(N.NarcPatchError, "expected"):
            N.apply(store.__getitem__, store.__setitem__, [fix])


if __name__ == "__main__":
    unittest.main()
