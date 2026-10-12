"""Verify the Giovanni hot-spring loss repair: one inserted WhiteOut block on the loss path, win path untouched."""

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

MEMBER, OFFSET, GROWTH, PADDED = 844, 819, 13, 16   # 13 inserted bytes + 3 zero bytes keeping the movement blocks 4-aligned


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class GiovanniHotSpringLossTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = M.load_rom(F.ROM_CN)
        cls.archive = M.get_file(rom, "a/0/1/2")
        cls.fix = next(f for f in F.load_all() if f["id"] == "giovanni-hotspring-loss")
        cls.C = R.cmds()

    def apply(self, fix=None):
        store = {"a/0/1/2": self.archive}
        report = N.apply(store.__getitem__, store.__setitem__, [fix or self.fix])
        self.assertTrue(N.verify(store.__getitem__, report).startswith("ok"))
        return M.Narc.parse(store["a/0/1/2"]).files

    def names(self, data):
        _, ins = R.disasm(data)
        return ins, lambda pc: self.C[ins[pc][0]][0]

    def test_only_member_844_grows(self):
        before = M.Narc.parse(self.archive).files
        after = self.apply()
        changed = [i for i in range(len(before)) if before[i] != after[i]]
        self.assertEqual(changed, [MEMBER])
        self.assertEqual(len(after[MEMBER]), len(before[MEMBER]) + PADDED)

    def test_loss_path_whites_out_and_win_path_is_unchanged(self):
        before = M.Narc.parse(self.archive).files[MEMBER]
        after = self.apply()[MEMBER]
        ins0, n0 = self.names(before)
        ins1, n1 = self.names(after)
        # before: ... CheckBattleWon, CompareVarToValue 0, GoToIf = -> L1890, HidePerson 7
        self.assertEqual([n0(p) for p in (809, 813, 819, 826)],
                         ["CheckBattleWon", "CompareVarToValue", "GoToIf", "HidePerson"])
        self.assertEqual(ins0[819][3], 1890)
        # after: the new GoToIf != skips WhiteOut/ReleaseAll/End to the original GoToIf (now at 832)
        self.assertEqual([n1(p) for p in (809, 813, 819, 826, 828, 830, 832, 839)],
                         ["CheckBattleWon", "CompareVarToValue", "GoToIf", "WhiteOut", "ReleaseAll", "End",
                          "GoToIf", "HidePerson"])
        self.assertEqual(ins1[819][1], [5, 6])           # condition 5 (!=), +6
        self.assertEqual(ins1[819][3], 832)
        self.assertEqual(ins1[832][1][0], 1)             # original condition (=: loss) unchanged
        self.assertEqual(ins1[832][3], 1890 + GROWTH)    # still the hot-spring block, shifted
        # Every instruction outside the inserted block is the same command with the same operands, in order.
        def view(ins, skip):
            return [(self.C[ins[p][0]][0], ins[p][1][:-1] if ins[p][0] in SI.REL_OPS else ins[p][1])
                    for p in sorted(ins) if p not in skip]
        old = view(ins0, ())
        new = view(ins1, set(range(819, 819 + GROWTH)))
        self.assertEqual(old, new)

    def test_every_jump_and_movement_target_is_preserved(self):
        before = M.Narc.parse(self.archive).files[MEMBER]
        after = self.apply()[MEMBER]
        ins0, _ = self.names(before)
        ins1, _ = self.names(after)
        pcs0 = sorted(ins0)
        pcs1 = [p for p in sorted(ins1) if not 819 <= p < 819 + GROWTH]
        self.assertEqual(len(pcs0), len(pcs1))
        new_of = dict(zip(pcs0, pcs1))
        for p0 in pcs0:
            op, a0, n0, _ = ins0[p0]
            if op not in SI.REL_OPS:
                continue
            p1 = new_of[p0]
            t0, t1 = n0 + a0[-1], ins1[p1][2] + ins1[p1][1][-1]
            if op == 94:                                   # ApplyMovement: the same movement bytes
                end0 = t0
                while R.struct.unpack_from("<H", before, end0)[0] != 0xFE:
                    end0 += 4
                end1 = t1
                while R.struct.unpack_from("<H", after, end1)[0] != 0xFE:
                    end1 += 4
                self.assertEqual(before[t0:end0 + 2], after[t1:end1 + 2], p0)
            elif t0 == 826:                                # the win path's first command (HidePerson 7)
                self.assertEqual(t1, 819)                  # a target on an insertion point lands on the inserted bytes
            else:
                self.assertEqual(new_of[t0], t1, (p0, t0))

    def test_hot_spring_block_still_shared(self):
        """L1890 keeps its other user (the hot spring's stage 4, var 0x4110 = 4)."""
        after = self.apply()[MEMBER]
        ins, name = self.names(after)
        users = sorted(p for p in ins if ins[p][3] == 1890 + GROWTH)
        self.assertEqual(users, [832, 1783 + GROWTH])
        self.assertEqual(name(1890 + GROWTH), "NPCMsg")

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
