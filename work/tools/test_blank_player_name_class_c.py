"""Tests for the blank-player-name-class-c fix: five BufferPlayersName inserts (members 115, 738, 829).

Run:  python3 -m unittest -v work/tools/test_blank_player_name_class_c.py
"""

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
import scriptinsert as SI
import test_script_insert as T

FIX_ID = "blank-player-name-class-c"
SITES = {115: [0x16C8], 738: [0x7EE, 0x828], 829: [0x967, 0x9EF]}


class Registry(unittest.TestCase):
    def test_fix_is_registered_and_disabled(self):
        fx = next(f for f in F.load_all() if f["id"] == FIX_ID)
        self.assertFalse(fx["enabled"])
        self.assertEqual(sorted(e["member"] for e in fx["script_insert"]), [115, 738, 738, 829, 829])
        for e in fx["script_insert"]:
            self.assertEqual(e["insert"], "BE 00 00")
            self.assertIn(int(e["offset"], 16), SITES[e["member"]])
        probs = []
        F._validate_entries(fx, FIX_ID, probs)
        self.assertEqual(probs, [])


@unittest.skipUnless(F.ROM_CN.exists() and F.ROM_CN.stat().st_size > 100_000_000, "needs local Chinese ROM")
class RealMembers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = M.get_file(M.load_rom(F.ROM_CN), "a/0/1/2")
        cls.fixes = {f["id"]: f for f in F.load_all()}
        cls.fix = cls.fixes[FIX_ID]
        cls.before = M.Narc.parse(cls.archive).files

    def patched(self, *ids):
        store = {"a/0/1/2": self.archive}
        rows = N.apply(store.__getitem__, store.__setitem__, [self.fixes[i] for i in ids])
        self.assertTrue(N.verify(store.__getitem__, rows).startswith("ok"))
        return M.Narc.parse(store["a/0/1/2"]).files

    def test_only_three_members_change_by_inserts_only(self):
        files = self.patched(FIX_ID)
        self.assertEqual([i for i in range(len(self.before)) if self.before[i] != files[i]], [115, 738, 829])
        for m, offsets in SITES.items():
            ent = [(o, bytes.fromhex("BE0000")) for o in offsets]
            T.RealMembers.check_member(self, self.before[m], files[m], ent)
            SI.Layout(files[m])
            grow = len(files[m]) - len(self.before[m])
            self.assertGreaterEqual(grow, 3 * len(offsets))
            self.assertLess(grow, 3 * len(offsets) + 4 * 12)

    def test_inserted_command_sits_right_before_the_message(self):
        files = self.patched(FIX_ID)
        want = {115: [159], 738: [44, 44], 829: [81, 86]}
        for m, ids in want.items():
            _, old = R.disasm(self.before[m])
            _, ins = R.disasm(files[m])
            found = []
            for pc, (op, args, nxt, _) in sorted(ins.items()):
                if R.cmds()[op][0] == "BufferPlayersName" and args == [0]:
                    n_op, n_args, _, _ = ins[nxt]
                    found.append((R.cmds()[n_op][0], n_args[0] if n_args else None))
            old_buffers = sum(1 for v in old.values() if R.cmds()[v[0]][0] == "BufferPlayersName" and v[1] == [0])
            new_found = [x for x in found if x[0] == "NPCMsg" and x[1] in ids]
            self.assertEqual(sorted(x[1] for x in new_found)[-len(ids):], sorted(ids))
            self.assertEqual(sum(1 for v in ins.values() if R.cmds()[v[0]][0] == "BufferPlayersName") - sum(
                1 for v in old.values() if R.cmds()[v[0]][0] == "BufferPlayersName"), len(ids))
            self.assertGreaterEqual(len(found), old_buffers)

    def test_with_the_other_blank_name_fixes_in_any_order(self):
        ids = ["blank-player-name", "blank-player-name-batch", FIX_ID]
        a = self.patched(*ids)
        b = self.patched(*reversed(ids))
        self.assertEqual(a, b)
        solo = self.patched(FIX_ID)
        for m in SITES:
            self.assertEqual(a[m], solo[m])

    def test_with_tutor_saffron_volt_switch_on_member_829(self):
        # the Saffron tutor's byte edits (same size) run first; the two member 829 inserts accept the edited member
        sid = "tutor-saffron-volt-switch"
        a = self.patched(sid, FIX_ID)
        b = self.patched(FIX_ID, sid)
        self.assertEqual(a, b)
        tutor_only = self.patched(sid)[829]
        want = SI.insert(tutor_only, [(o, bytes.fromhex("BE0000")) for o in SITES[829]])
        self.assertEqual(a[829], want)
        SI.Layout(a[829])
        R.disasm(a[829])                                    # decodes cleanly
        self.assertEqual(a[829].count(bytes.fromhex("0902")) - self.before[829].count(bytes.fromhex("0902")), 3)
        for m in (115, 738):
            self.assertEqual(a[m], self.patched(FIX_ID)[m])

    def test_guard_refuses_another_member(self):
        store = {"a/0/1/2": self.archive}
        fx = copy.deepcopy(self.fix)
        fx["script_insert"][0]["member_sha1"] = ["0" * 40]
        with self.assertRaises(N.NarcPatchError):
            N.apply(store.__getitem__, store.__setitem__, [fx])


if __name__ == "__main__":
    unittest.main()
