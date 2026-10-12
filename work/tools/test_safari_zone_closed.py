"""Verify the Safari Zone closure: no gate counter reaches the entry warp, the door warps leave map 357, the rest is intact."""

import json
import sys
import unittest

HERE = __import__("pathlib").Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "docs")]
import fixes as F
import msgtool as M
import narcpatch as N
import romdata as R

SCRIPTS, EVENTS, MEMBER_SCRIPT, MEMBER_EVENTS = "a/0/1/2", "a/0/3/2", 119, 167
SAFARI_MAP = 357
CLOSED = 46
COUNTERS = (1, 2, 4, 5)          # information, pay, Link and friend counters
UNTOUCHED = (3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)


def reach(ins, cmds, start):
    seen, todo = set(), [start]
    while todo:
        pc = todo.pop()
        if pc in seen or pc not in ins:
            continue
        seen.add(pc)
        op, _, nxt, target = ins[pc]
        name = cmds[op][0]
        if name in ("End", "Return", "RestartCurrentScript"):
            continue
        if target is not None:
            todo.append(target)
        if name != "GoTo":
            todo.append(nxt)
    return seen


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class SafariZoneClosedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = M.load_rom(F.ROM_CN)
        cls.store = {p: M.get_file(rom, p) for p in (SCRIPTS, EVENTS)}
        cls.fix = next(f for f in F.load_all() if f["id"] == "safari-zone-closed")
        cls.cmds = R.cmds()
        cls.before_scripts = M.Narc.parse(cls.store[SCRIPTS]).files[MEMBER_SCRIPT]
        cls.before_events = M.Narc.parse(cls.store[EVENTS]).files[MEMBER_EVENTS]
        store = dict(cls.store)
        report = N.apply(store.__getitem__, store.__setitem__, [cls.fix])
        N.verify(store.__getitem__, report)
        cls.after_scripts = M.Narc.parse(store[SCRIPTS]).files[MEMBER_SCRIPT]
        cls.after_events = M.Narc.parse(store[EVENTS]).files[MEMBER_EVENTS]

    def names_from(self, data, script):
        entries, ins = R.disasm(data)
        return {self.cmds[ins[pc][0]][0] for pc in reach(ins, self.cmds, entries[script - 1])}

    def test_original_counters_can_warp_into_the_zone(self):
        self.assertIn("Warp", self.names_from(self.before_scripts, 2))
        self.assertIn("Warp", self.names_from(self.before_scripts, 5))
        warps = [w["dest"] for w in R.parse_events(self.before_events)["warp"]]
        self.assertEqual(warps.count(SAFARI_MAP), 2)

    def test_no_counter_reaches_a_warp_or_a_game_start(self):
        for script in COUNTERS:
            names = self.names_from(self.after_scripts, script)
            self.assertNotIn("Warp", names, script)
            self.assertNotIn("SafariZoneAction", names, script)
            self.assertNotIn("SubMoneyImmediate", names, script)
            self.assertIn("NPCMsg", names, script)

    def test_counter_shows_the_closed_notice_first(self):
        entries, ins = R.disasm(self.after_scripts)
        for script in COUNTERS:
            pc, ops = entries[script - 1], []
            for _ in range(8):
                op, args, pc, _ = ins[pc]
                ops.append((self.cmds[op][0], tuple(args)))
            self.assertIn(("NPCMsg", (CLOSED,)), ops[:4], script)
            names = [n for n, _ in ops]
            i = names.index("NPCMsg")
            self.assertEqual(names[i : i + 4], ["NPCMsg", "WaitButton", "CloseMsg", "ReleaseAll"])

    def test_other_scripts_unchanged(self):
        e0, i0 = R.disasm(self.before_scripts)
        e1, i1 = R.disasm(self.after_scripts)
        for script in UNTOUCHED:
            # offsets move with the insert: compare names and plain operands, not the relative jump operand
            def key(ins, pc):
                op, args, _, target = ins[pc]
                name = self.cmds[op][0]
                return (name, list(args[:-1]) if target is not None or name == "ApplyMovement" else list(args))

            a = [key(i0, pc) for pc in sorted(reach(i0, self.cmds, e0[script - 1]))]
            b = [key(i1, pc) for pc in sorted(reach(i1, self.cmds, e1[script - 1]))]
            self.assertEqual(a, b, script)

    def test_variable_and_flag_writes_are_unchanged(self):
        def writes(data):
            # what the entries that are not counters can still write; the counters' old paths are dead code now
            entries, ins = R.disasm(data)
            pcs = set()
            for n, e in enumerate(entries, 1):
                if n not in COUNTERS:
                    pcs |= reach(ins, self.cmds, e)
            return sorted((self.cmds[ins[pc][0]][0], tuple(ins[pc][1])) for pc in pcs
                          if self.cmds[ins[pc][0]][0] in ("SetVar", "SetFlag", "ClearFlag", "AddVar"))

        self.assertEqual(writes(self.before_scripts), writes(self.after_scripts))

    def test_door_warps_no_longer_lead_to_the_zone(self):
        before = R.parse_events(self.before_events)
        after = R.parse_events(self.after_events)
        self.assertEqual(len(before["warp"]), len(after["warp"]))
        self.assertEqual([(w["x"], w["z"]) for w in after["warp"] if w["dest"] == SAFARI_MAP], [(0, 0), (0, 0)])
        moved = [(b, a) for b, a in zip(before["warp"], after["warp"]) if b != a]
        self.assertEqual([(b["x"], b["z"], b["dest"]) for b, _ in moved], [(5, 2, SAFARI_MAP), (19, 2, SAFARI_MAP)])
        for _, a in moved:
            self.assertEqual((a["x"], a["z"]), (0, 0))
        self.assertEqual(before["bg"], after["bg"])
        self.assertEqual(before["obj"], after["obj"])
        self.assertEqual(after["warp"][0], before["warp"][0])    # the exit to Fuchsia City stays

    def test_notice_is_in_the_message_bank(self):
        repo = HERE.parent.parent
        bank = json.loads((repo / "work/translate/banks/a027/0133.json").read_text(encoding="utf-8"))
        row = next(s for s in bank["strings"] if s["id"] == CLOSED)
        self.assertIn("closed", row["en"])
        self.assertEqual(row["origin"], "agent")


if __name__ == "__main__":
    unittest.main()
