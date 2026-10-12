"""Verify the Route 3 Misty-scene repair: a prefix on script 17 that shows the actors when flag 1303 hides them."""

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

MEMBER, OFFSET, GROWTH, PADDED = 175, 1171, 27, 28   # 27 inserted bytes + 1 zero byte keeping the movement blocks 4-aligned


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class Route3MistyActorsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = M.load_rom(F.ROM_CN)
        cls.archive = M.get_file(rom, "a/0/1/2")
        cls.fix = next(f for f in F.load_all() if f["id"] == "route3-misty-actors")
        cls.C = R.cmds()

    def apply(self, fix=None):
        store = {"a/0/1/2": self.archive}
        report = N.apply(store.__getitem__, store.__setitem__, [fix or self.fix])
        self.assertTrue(N.verify(store.__getitem__, report).startswith("ok"))
        return M.Narc.parse(store["a/0/1/2"]).files

    def view(self, data):
        entries, ins = R.disasm(data)
        return entries, ins, lambda pc: self.C[ins[pc][0]][0]

    def test_only_member_175_grows(self):
        before = M.Narc.parse(self.archive).files
        after = self.apply()
        changed = [i for i in range(len(before)) if before[i] != after[i]]
        self.assertEqual(changed, [MEMBER])
        self.assertIn(len(after[MEMBER]) - len(before[MEMBER]), range(GROWTH, GROWTH + 4))

    def test_prefix_and_entry(self):
        before = M.Narc.parse(self.archive).files[MEMBER]
        after = self.apply()[MEMBER]
        e0, ins0, n0 = self.view(before)
        e1, ins1, n1 = self.view(after)
        self.assertEqual(n0(OFFSET), "PlaySE")
        # script 17's entry (index 16 in header order) now points at the inserted CheckFlag
        i = e0.index(OFFSET)
        self.assertEqual(e1[i], OFFSET)
        self.assertEqual([n1(p) for p in (1171, 1175, 1182, 1186, 1190, 1194, 1198)],
                         ["CheckFlag", "GoToIf", "ClearFlag", "ShowPerson", "ShowPerson", "ShowPerson", "PlaySE"])
        self.assertEqual(ins1[1171][1], [1303])
        self.assertEqual(ins1[1175][1][0], 0)           # jumps when the flag is NOT set
        self.assertEqual(ins1[1175][3], 1198)           # over the reveal, to the old first command
        self.assertEqual(ins1[1182][1], [1303])
        self.assertEqual([ins1[p][1] for p in (1186, 1190, 1194)], [[28], [9], [8]])
        # these are the scene's actors: Misty 9, her second object 8, the Gyarados 28 (all hidden by flag 1303)
        zone = next(z for z in R.read_json(str(F.WORK / "translate" / "bank_maps.json"))["_zones"] if z["zone_id"] == 11)
        self.assertEqual(zone["scripts_bank"], MEMBER)
        objs = {o["id"]: o for o in R.parse_events(R.Rom()["events"][zone["events_bank"]])["obj"]}
        for oid in (8, 9, 28):
            self.assertEqual(objs[oid]["flag"], 1303)

    def test_rest_of_script_unchanged(self):
        before = M.Narc.parse(self.archive).files[MEMBER]
        after = self.apply()[MEMBER]
        _, ins0, _ = self.view(before)
        _, ins1, _ = self.view(after)

        def seq(ins, skip):
            return [(self.C[ins[p][0]][0], ins[p][1][:-1] if ins[p][0] in SI.REL_OPS else ins[p][1])
                    for p in sorted(ins) if p not in skip]
        self.assertEqual(seq(ins0, ()), seq(ins1, set(range(OFFSET, OFFSET + GROWTH))))

    def test_guards_reject_changed_source(self):
        for off in (OFFSET, 5):
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
