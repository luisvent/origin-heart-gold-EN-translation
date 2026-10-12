"""Verify the Forest of Time guard: the Sammy arrival scene (script 1) and the Marauder scene (script 3) of
a/0/1/2 member 52 end at once unless flag 2105 (the Sammy chapter is active) is set."""

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

MEMBER, ENTRY1, ENTRY3, BLOCK = 52, 34, 437, 13        # two 13-byte guards
FLAG, VAR = 2105, 0x4099


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class ForestOfTimeSammyGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = M.load_rom(F.ROM_CN)
        cls.archive = M.get_file(rom, "a/0/1/2")
        cls.fix = next(f for f in F.load_all() if f["id"] == "forest-of-time-sammy-guard")
        cls.C = R.cmds()

    def apply(self, fix=None):
        store = {"a/0/1/2": self.archive}
        report = N.apply(store.__getitem__, store.__setitem__, [fix or self.fix])
        self.assertTrue(N.verify(store.__getitem__, report).startswith("ok"))
        return M.Narc.parse(store["a/0/1/2"]).files

    def view(self, data):
        entries, ins = R.disasm(data)
        return entries, ins, lambda pc: self.C[ins[pc][0]][0]

    def test_only_member_52_grows(self):
        before = M.Narc.parse(self.archive).files
        after = self.apply()
        self.assertEqual([i for i in range(len(before)) if before[i] != after[i]], [MEMBER])
        self.assertIn(len(after[MEMBER]) - len(before[MEMBER]), range(2 * BLOCK, 2 * BLOCK + 4))

    def test_guards_and_entries(self):
        before = M.Narc.parse(self.archive).files[MEMBER]
        after = self.apply()[MEMBER]
        e0, ins0, n0 = self.view(before)
        e1, ins1, n1 = self.view(after)
        self.assertEqual((n0(ENTRY1), n0(ENTRY3)), ("ScrCmd_609", "ScrCmd_609"))
        # script 1 and script 3 are the 1st and 3rd header entries; they now point at the inserted CheckFlag
        self.assertEqual((e0[0], e0[2]), (ENTRY1, ENTRY3))
        self.assertEqual(e1[0], ENTRY1)
        shift = BLOCK
        self.assertEqual(e1[2], ENTRY3 + shift)
        for start, old in ((ENTRY1, ENTRY1 + BLOCK), (ENTRY3 + shift, ENTRY3 + 2 * shift)):
            names = []
            pc = start
            for _ in range(3):
                names.append(n1(pc))
                pc = ins1[pc][2]
            self.assertEqual(names, ["CheckFlag", "GoToIf", "End"])
            self.assertEqual(ins1[start][1], [FLAG])
            gt = ins1[ins1[start][2]]
            self.assertEqual(gt[1][0], 1)                       # jumps when the flag IS set
            self.assertEqual(gt[3], old)                        # over the End, to the old first command
            self.assertEqual(n1(old), "ScrCmd_609")

    def test_rest_of_script_unchanged(self):
        before = M.Narc.parse(self.archive).files[MEMBER]
        after = self.apply()[MEMBER]
        _, ins0, _ = self.view(before)
        _, ins1, _ = self.view(after)
        inserted = set()
        starts = [ENTRY1, ENTRY3 + BLOCK]
        for s in starts:
            pc = s
            for _ in range(3):
                inserted.add(pc)
                pc = ins1[pc][2]

        def seq(ins, skip):
            return [(self.C[ins[p][0]][0], ins[p][1][:-1] if ins[p][0] in SI.REL_OPS else ins[p][1])
                    for p in sorted(ins) if p not in skip]
        self.assertEqual(seq(ins0, ()), seq(ins1, inserted))

    def test_flag_and_var_facts(self):
        """The reasoning the guard rests on: flag 2105 is set by the ranger's Sammy scene (file 92) right before
        0x4099 = 3, cleared only by file 52's finale, and is otherwise only an object hide flag."""
        rom = R.Rom()
        sets, clears, var_writes = [], [], []
        for f, data in enumerate(rom["scripts"]):
            try:
                _, ins = R.disasm(data)
            except Exception:
                continue
            for pc, (op, a, _n, _t) in sorted(ins.items()):
                name = self.C[op][0]
                if name == "SetFlag" and a == [FLAG]:
                    sets.append((f, pc))
                if name == "ClearFlag" and a == [FLAG]:
                    clears.append((f, pc))
                if name == "SetVar" and a[0] == VAR:
                    var_writes.append((f, pc, a[1]))
        self.assertEqual(sets, [(92, 5364)])
        self.assertEqual(clears, [(52, 2401)])
        self.assertIn((92, 5372, 3), var_writes)               # the one genuine start of the Sammy chapter
        ins92 = R.disasm(rom["scripts"][92])[1]
        # the ranger's scene: SetFlag 2105, HidePerson 17 (the ranger), SetVar 0x4099 = 3, ClearFlag 1120 (actors)
        self.assertEqual([(self.C[ins92[p][0]][0], ins92[p][1]) for p in (5364, 5368, 5372, 5378)],
                         [("SetFlag", [FLAG]), ("HidePerson", [17]), ("SetVar", [VAR, 3]), ("ClearFlag", [1120])])
        # the Forest's two scenes sit on coordinate triggers on 0x4099 = 3 and 5 of the zone-327 events
        zone = next(z for z in R.read_json(str(F.WORK / "translate" / "bank_maps.json"))["_zones"] if z["zone_id"] == 327)
        self.assertEqual(zone["scripts_bank"], MEMBER)

    def test_guards_reject_changed_source(self):
        for off in (ENTRY1, ENTRY3, 5):
            files = M.Narc.parse(self.archive).files
            bad = bytearray(files[MEMBER])
            bad[off] ^= 1
            files[MEMBER] = bytes(bad)
            store = {"a/0/1/2": M.Narc(files).build()}
            original = store["a/0/1/2"]
            with self.assertRaises(N.NarcPatchError):
                N.apply(store.__getitem__, store.__setitem__, [self.fix])
            self.assertEqual(store["a/0/1/2"], original)


if __name__ == "__main__":
    unittest.main()
