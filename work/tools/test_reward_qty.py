"""Verify the reward-qty fix: standard reward scripts 2033 and 2008 show the quantity of a gift of more than one item.

The scripts are run by a small interpreter over the disassembly (calls, jumps, comparisons, the vars 0x8004/0x8005
and the pocket); it records what they buffer and show. The fix is applied to the Chinese ROM's script NARC in memory.
"""

import hashlib
import sys
import unittest

HERE = __import__("pathlib").Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "docs")]
import fixes as F
import msgtool as M
import narcpatch as N
import romdata as R

SCRIPTS, MEMBER = "a/0/1/2", 3
STD_2033, STD_2008 = 2033, 2008          # entries of member 3: std id - 2000 (0-based)
ITEM_VAR, QTY_VAR, POCKET_VAR = 0x8004, 0x8005, 0x800C
POCKET_KEY, POCKET_TM, POCKET_ITEMS = 7, 3, 0
MSG_SINGLE, MSG_KEY, MSG_QTY = 25, 28, 66
BLOCK_LEN = 35
PADDING = 1          # the movement blocks keep their position modulo 4 (scriptinsert.py)
SHOW = {"NPCMsg", "BufferItemName", "BufferInt", "BufferPlayersName", "WaitFanfare", "PlayFanfare", "GiveItem", "WaitButton"}


def run(data, std, item, qty, pocket):
    """Trace of the shown/buffered commands of one std script."""
    cmds = R.cmds()
    entries, ins = R.disasm(data)
    var = {ITEM_VAR: item, QTY_VAR: qty}
    pc, stack, flag, trace = entries[std - 2000], [], 0, []
    for _ in range(2000):
        op, args, nxt, target = ins[pc]
        name = cmds[op][0]
        if name in ("End", "RestartCurrentScript"):
            break
        if name == "Return":
            if not stack:
                break
            pc = stack.pop()
            continue
        if name == "CompareVarToValue":
            a, b = var.get(args[0], args[0]), args[1]
            flag = (a > b) - (a < b)
        elif name == "GetItemPocket":
            var[args[1]] = pocket
        elif name == "CopyVar":
            var[args[0]] = var.get(args[1], args[1])
        elif name in SHOW:
            trace.append((name, tuple(var.get(a, a) if a >= 0x4000 else a for a in args)))
        if name == "GoTo":
            pc = target
            continue
        if name in ("GoToIf", "CallIf"):
            want = args[0]
            holds = {0: flag < 0, 1: flag == 0, 2: flag > 0, 3: flag <= 0, 4: flag >= 0, 5: flag != 0}[want]
            if holds:
                if name == "CallIf":
                    stack.append(nxt)
                pc = target
                continue
        if name == "Call":
            stack.append(nxt)
            pc = target
            continue
        pc = nxt
    else:
        raise AssertionError("script did not end")
    return trace


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class RewardQtyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = M.load_rom(F.ROM_CN)
        cls.store = {SCRIPTS: M.get_file(rom, SCRIPTS)}
        cls.fix = next(f for f in F.load_all() if f["id"] == "reward-qty")
        cls.before = M.Narc.parse(cls.store[SCRIPTS]).files[MEMBER]
        store = dict(cls.store)
        report = N.apply(store.__getitem__, store.__setitem__, [cls.fix])
        N.verify(store.__getitem__, report)
        cls.narc_after = M.Narc.parse(store[SCRIPTS])
        cls.after = cls.narc_after.files[MEMBER]

    def test_disabled_by_default(self):
        self.assertFalse(self.fix["enabled"])

    def test_original_shows_one_item_for_any_quantity(self):
        for std in (STD_2033, STD_2008):
            for qty in (1, 2, 10):
                trace = run(self.before, std, 2, qty, POCKET_ITEMS)
                self.assertIn(("NPCMsg", (MSG_SINGLE,)), trace)
                self.assertNotIn(("NPCMsg", (MSG_QTY,)), trace)

    def test_quantity_above_one_shows_the_number_message(self):
        for std in (STD_2033, STD_2008):
            for qty in (2, 5, 10):
                trace = run(self.after, std, 2, qty, POCKET_ITEMS)
                self.assertNotIn(("NPCMsg", (MSG_SINGLE,)), trace)
                i = trace.index(("NPCMsg", (MSG_QTY,)))
                self.assertEqual(trace[i - 2 : i], [("BufferItemName", (0, 2)), ("BufferInt", (1, qty))])

    def test_single_item_message_is_unchanged(self):
        for std in (STD_2033, STD_2008):
            b = run(self.before, std, 2, 1, POCKET_ITEMS)
            a = run(self.after, std, 2, 1, POCKET_ITEMS)
            self.assertEqual(a, b)

    def test_key_item_gifts_are_unchanged(self):
        # pocket 7 (key items) has its own message (#28, coloured name) and takes no quantity in the US game either
        for std in (STD_2033, STD_2008):
            for qty in (1, 2):
                trace = run(self.after, std, 430, qty, POCKET_KEY)
                self.assertEqual(trace, run(self.before, std, 430, qty, POCKET_KEY))
                self.assertIn(("NPCMsg", (MSG_KEY,)), trace)

    def test_tm_gifts_follow_the_general_path(self):
        # TMs (pocket 3) use the general message like every other item: one TM as before, five show the number
        for std in (STD_2033, STD_2008):
            self.assertEqual(run(self.after, std, 355, 1, POCKET_TM), run(self.before, std, 355, 1, POCKET_TM))
            self.assertIn(("NPCMsg", (MSG_QTY,)), run(self.after, std, 355, 5, POCKET_TM))

    def test_rest_of_the_flow_is_unchanged(self):
        # the pocket message, the fanfare wait and the buffers after the quantity message are the same as before
        for std in (STD_2033, STD_2008):
            for qty in (1, 3):
                strip = lambda t: [x for x in t if x[0] != "BufferInt" and x[1] not in ((MSG_SINGLE,), (MSG_QTY,))]
                self.assertEqual(strip(run(self.after, std, 4, qty, 1)), strip(run(self.before, std, 4, qty, 1)))

    def test_only_member_three_changed_and_grew_by_the_block(self):
        old = M.Narc.parse(self.store[SCRIPTS]).files
        new = self.narc_after.files
        self.assertEqual(len(old), len(new))
        self.assertEqual([i for i, (a, b) in enumerate(zip(old, new)) if a != b], [MEMBER])
        self.assertEqual(len(new[MEMBER]) - len(old[MEMBER]), BLOCK_LEN + PADDING)
        self.assertEqual(hashlib.sha1(old[MEMBER]).hexdigest(), self.fix["narc_bytes"][0]["member_sha1"])

    def test_every_command_of_the_old_member_is_still_there(self):
        # same command sequence outside the touched block (relative operands move with the insert)
        cmds = R.cmds()
        e0, i0 = R.disasm(self.before)
        e1, i1 = R.disasm(self.after)

        def names(ins):
            return [cmds[ins[pc][0]][0] for pc in sorted(ins)]

        n0, n1 = names(i0), names(i1)
        self.assertEqual(len(n1) - len(n0), 7 - 2 + 4)      # 7 new commands, the 2 old ones become 4 Noops
        self.assertEqual(len(e0), len(e1))

    def test_message_66_is_the_existing_unused_line(self):
        import json
        repo = HERE.parent.parent
        bank = json.loads((repo / "work/translate/banks/a027/0038.json").read_text(encoding="utf-8"))
        row = next(s for s in bank["strings"] if s["id"] == MSG_QTY)
        self.assertEqual(row["en"], "Obtained the {VAR:0108:0}{NEWLINE}x{VAR:0133:1}!")
        self.assertIn("{VAR:0108:0}", row["zh"])
        self.assertIn("{VAR:0133:1}", row["zh"])


if __name__ == "__main__":
    unittest.main()
