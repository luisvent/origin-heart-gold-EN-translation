"""Verify the Pallet Town photographer guard: one inserted block, the rest of member 733 unchanged.

Run:  python3 -m unittest -v work/tools/test_photographer_no_healthy_mon.py   (needs the local Chinese ROM)
"""

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

MEMBER = 733
GUARD_AT = 136
FIX_ID = "photographer-no-healthy-mon"
TAIL = ["GetStdMsgNaix", "MsgBoxExtern", "WaitButton", "CloseMsg", "ReleaseAll", "End"]


def names(data, start, count):
    _, ins = R.disasm(data)
    out, pc = [], start
    for _ in range(count):
        op, args, nxt, _tgt = ins[pc]
        out.append((R.cmds()[op][0], args, pc, nxt))
        pc = nxt
    return out


@unittest.skipUnless(F.ROM_CN.exists() and F.ROM_CN.stat().st_size > 100_000_000, "needs local Chinese ROM")
class PhotographerGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = M.get_file(M.load_rom(F.ROM_CN), "a/0/1/2")
        cls.fixes = {f["id"]: f for f in F.load_all()}
        cls.fix = cls.fixes[FIX_ID]
        cls.original = M.Narc.parse(cls.archive).files[MEMBER]

    def apply(self, *fix_ids):
        store = {"a/0/1/2": self.archive}
        report = N.apply(store.__getitem__, store.__setitem__, [self.fixes[i] for i in fix_ids])
        self.assertTrue(N.verify(store.__getitem__, report).startswith("ok"))
        return M.Narc.parse(store["a/0/1/2"]).files[MEMBER]

    def test_registered_and_off_by_default(self):
        self.assertFalse(self.fix["enabled"])
        self.assertEqual(self.fix["kind"], "narc")
        self.assertEqual(F.validate([self.fix]) if hasattr(F, "validate") else [], [])

    def test_the_original_script_is_what_the_fix_assumes(self):
        d = self.original
        self.assertEqual(hashlib.sha1(d).hexdigest(), self.fix["script_insert"][0]["member_sha1"][0])
        album = names(d, GUARD_AT, 3)
        self.assertEqual([a[0] for a in album], ["PhotoAlbumIsFull", "CompareVarToValue", "GoToIf"])
        decline = names(d, 851, len(TAIL))                  # the reply for answering No, ends the script
        self.assertEqual([a[0] for a in decline], TAIL)
        self.assertEqual(decline[-1][3], 871)
        self.assertEqual(names(d, 129, 1)[0][0], "GoToIf")  # Yes/No choice: No jumps to 851

    def test_inserted_block_is_count_compare_skip_and_the_decline_reply(self):
        new = self.apply(FIX_ID)
        self.assertEqual(len(new), len(self.original) + 39 + 1)            # 39 bytes + one byte of alignment
        seq = names(new, GUARD_AT, 3 + len(TAIL) + 1)
        self.assertEqual([s[0] for s in seq],
                         ["CountAliveMons", "CompareVarToValue", "GoToIf"] + TAIL + ["PhotoAlbumIsFull"])
        self.assertEqual(seq[0][1], [0x800C, 6])                          # 6 skips no ordinary party slot
        self.assertEqual(seq[1][1], [0x800C, 0])
        self.assertEqual(seq[2][1][0], 5)                                  # "not equal"
        _, ins = R.disasm(new)
        self.assertEqual(ins[seq[2][2]][3], seq[-1][2])                    # healthy: the jump lands on the album check
        # the copy of the decline reply is the original's, argument for argument
        orig = names(self.original, 851, len(TAIL))
        self.assertEqual([(s[0], s[1]) for s in seq[3:3 + len(TAIL)]], [(o[0], o[1]) for o in orig])
        self.assertEqual(seq[3 + len(TAIL) - 1][0], "End")

    def test_every_other_command_is_unchanged_and_reachable(self):
        new = self.apply(FIX_ID)
        _, a = R.disasm(self.original)
        _, b = R.disasm(new)
        va = [(R.cmds()[op][0], tuple(args)) for pc, (op, args, nx, t) in sorted(a.items())]
        vb = [(R.cmds()[op][0], tuple(args)) for pc, (op, args, nx, t) in sorted(b.items())]
        # same commands in the same order plus the 9 inserted ones; relative operands may differ (relocated)
        self.assertEqual(len(vb), len(va) + 9)

        def strip(rows):
            return [(n, a if n not in ("GoTo", "GoToIf", "ApplyMovement", "Call", "CallIf") else a[:-1])
                    for n, a in rows]
        k = sorted(b).index(GUARD_AT)
        inserted = vb[k:k + 9]
        self.assertEqual(strip(vb[:k]) + strip(vb[k + 9:]), strip(va))
        self.assertEqual([n for n, _ in inserted],
                         ["CountAliveMons", "CompareVarToValue", "GoToIf"] + TAIL)

    def test_combines_with_blank_player_name_in_the_same_member(self):
        both = self.apply("blank-player-name", FIX_ID)
        only = self.apply(FIX_ID)
        blank = self.apply("blank-player-name")
        self.assertEqual(len(both), len(only))
        self.assertEqual(hashlib.sha1(blank).hexdigest(), self.fix["script_insert"][0]["member_sha1"][1])
        # the rotation (BufferPlayersName before NPCMsg 20) survives next to the guard
        _, ins = R.disasm(both)
        ops = [R.cmds()[ins[pc][0]][0] for pc in sorted(ins)]
        self.assertIn("CountAliveMons", ops)
        pcs = sorted(ins)
        i = next(i for i, pc in enumerate(pcs) if ins[pc][0] == 45 and ins[pc][1] == [20])   # NPCMsg 20
        self.assertEqual(R.cmds()[ins[pcs[i - 1]][0]][0], "BufferPlayersName")

    def test_refuses_a_member_that_is_not_the_hacks(self):
        store = {"a/0/1/2": self.archive}
        bad = copy.deepcopy(self.fix)
        bad["script_insert"][0]["member_sha1"] = ["0" * 40]
        with self.assertRaises(N.NarcPatchError):
            N.apply(store.__getitem__, store.__setitem__, [bad])
        bad = copy.deepcopy(self.fix)
        bad["script_insert"][0]["expect"] = "00 00 00 00"
        with self.assertRaises(N.NarcPatchError):
            N.apply(store.__getitem__, store.__setitem__, [bad])


if __name__ == "__main__":
    unittest.main()
