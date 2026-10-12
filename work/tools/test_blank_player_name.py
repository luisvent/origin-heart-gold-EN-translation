"""Verify the blank-player-name script repairs: bytes, structure and guards."""

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

BUFFER, NPCMSG = 190, 45


RELATIVE_OPS = {22, 23, 24, 25, 26, 28, 29, 225, 94}  # GoTo family, Call, ApplyMovement: operand = offset from the instruction end


def absolute_targets(ins):
    """Sorted (name, non-relative args, absolute target) of every instruction with a relative operand."""
    return sorted(
        (R.cmds()[op][0], tuple(args[:-1]), nxt + args[-1]) for op, args, nxt, _ in ins.values() if op in RELATIVE_OPS
    )


def ops(ins):
    return {pc: (R.cmds()[v[0]][0], v[1]) for pc, v in ins.items()}


@unittest.skipUnless(F.ROM_CN.exists() and F.ROM_CN.stat().st_size > 100_000_000, "needs local Chinese ROM")
class BlankPlayerNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = M.get_file(M.load_rom(F.ROM_CN), "a/0/1/2")
        cls.fix = next(f for f in F.load_all() if f["id"] == "blank-player-name")
        store = {"a/0/1/2": cls.archive}
        N.apply(store.__getitem__, store.__setitem__, [cls.fix])
        cls.before = M.Narc.parse(cls.archive).files
        cls.after = M.Narc.parse(store["a/0/1/2"]).files

    def test_only_three_members_change_and_sizes_hold(self):
        self.assertEqual([i for i in range(len(self.before)) if self.before[i] != self.after[i]], [111, 171, 733])
        for m in (111, 171, 733):
            self.assertEqual(len(self.before[m]), len(self.after[m]))

    def test_clair_buffer_index_matches_tag(self):
        _, a = R.disasm(self.before[111])
        _, b = R.disasm(self.after[111])
        self.assertEqual(a[213][1], [0])
        self.assertEqual(b[213][1], [1])
        self.assertEqual(a[216][1], [29])  # message 127#29 reads {VAR:0103:1}
        self.assertEqual([pc for pc in a if a[pc] != b[pc]], [213])

    def test_photographer_buffer_precedes_first_message(self):
        _, a = R.disasm(self.before[733])
        _, b = R.disasm(self.after[733])
        self.assertEqual([ops(a)[p][0] for p in (1026, 1029, 1031, 1033, 1036)],
                         ["NPCMsg", "WaitButton", "CloseMsg", "BufferPlayersName", "NPCMsg"])
        self.assertEqual([ops(b)[p] for p in (1026, 1029, 1032, 1034, 1036)],
                         [("BufferPlayersName", [0]), ("NPCMsg", [20]), ("WaitButton", []), ("CloseMsg", []), ("NPCMsg", [29])])
        self.assertEqual(self.before[733][1036:], self.after[733][1036:])

    def test_route2_three_branches(self):
        _, a = R.disasm(self.before[171])
        _, b = R.disasm(self.after[171])
        for msg, buf in ((463, 480), (1457, 1474), (1565, 1582)):
            self.assertEqual(a[buf][0], BUFFER)
            self.assertEqual(a[msg][:2], (NPCMSG, [26]))
            self.assertEqual(b[msg][0], BUFFER)
            self.assertEqual(b[msg + 3][:2], (NPCMSG, [26]))
            self.assertEqual(self.before[171][buf + 3:buf + 5], self.after[171][buf + 3:buf + 5])

    def test_every_relative_operand_keeps_its_absolute_target(self):
        for m in (111, 171, 733):
            _, a = R.disasm(self.before[m])
            _, b = R.disasm(self.after[m])
            self.assertEqual(len(a), len(b))
            self.assertEqual(absolute_targets(a), absolute_targets(b), m)
        # Brock's three branches: the ApplyMovement that moved 3 bytes still ends at the same place
        _, a = R.disasm(self.before[171])
        _, b = R.disasm(self.after[171])
        for old, new in ((470, 473), (1464, 1467), (1572, 1575)):
            self.assertEqual(a[old][0], 94)
            self.assertEqual(b[new][0], 94)
            self.assertEqual(a[old][2] + a[old][1][1], b[new][2] + b[new][1][1])
            self.assertEqual(a[old][1][0], b[new][1][0])

    def test_entry_tables_unchanged(self):
        for m in (111, 171, 733):
            self.assertEqual(R.script_entries(self.before[m]), R.script_entries(self.after[m]))

    def test_member_guard_rejects_changed_source(self):
        for m, off in ((111, 215), (171, 480), (733, 1033)):
            files = M.Narc.parse(self.archive).files
            bad = bytearray(files[m])
            bad[off] ^= 1
            files[m] = bytes(bad)
            store = {"a/0/1/2": M.Narc(files).build()}
            original = store["a/0/1/2"]
            with self.assertRaises(N.NarcPatchError):
                N.apply(store.__getitem__, store.__setitem__, [copy.deepcopy(self.fix)])
            self.assertEqual(store["a/0/1/2"], original)


if __name__ == "__main__":
    unittest.main()
