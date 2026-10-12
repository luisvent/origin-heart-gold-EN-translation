"""Verify the Saffron Dojo tutor repair: Volt Switch (521) replaces Charge (268) on the free-slot and retry paths."""

import copy
import hashlib
import json
import struct
import sys
import unittest

HERE = __import__("pathlib").Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "docs")]
import fixes as F
import msgtool as M
import narcpatch as N
import romdata as R

MEMBER = 829
CHARGE, VOLT_SWITCH, COUNTER = 268, 521, 68
# pc of the command -> (command name, operand offset inside the command)
SITES = {6368: ("SetMonMove", 6), 6680: ("PokemonSummaryScreen", 5), 6748: ("SetMonMove", 6)}
MAIN_PATH = {3471: "MonHasMove", 4369: "PokemonSummaryScreen", 4437: "SetMonMove", 4568: "MonHasMove"}


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class SaffronDojoTutorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = M.load_rom(F.ROM_CN)
        cls.archive = M.get_file(rom, "a/0/1/2")
        cls.fix = next(f for f in F.load_all() if f["id"] == "tutor-saffron-volt-switch")
        cls.cmds = R.cmds()

    def apply(self, archive=None, fix=None):
        store = {"a/0/1/2": self.archive if archive is None else archive}
        report = N.apply(store.__getitem__, store.__setitem__, [fix or self.fix])
        self.assertEqual(N.verify(store.__getitem__, report), "ok (3 entries, 1 members)")
        return M.Narc.parse(store["a/0/1/2"]).files

    def move_operands(self, data):
        _, ins = R.disasm(data)
        out = {}
        for pc, (op, args, _, _) in ins.items():
            name = self.cmds[op][0]
            if name in ("MonHasMove", "SetMonMove", "PokemonSummaryScreen"):
                out[pc] = (name, args[1] if name == "MonHasMove" else args[-1])
        return out

    def test_original_script_mixes_charge_and_volt_switch(self):
        ops = self.move_operands(M.Narc.parse(self.archive).files[MEMBER])
        self.assertEqual({pc: v[0] for pc, v in ops.items() if v[1] == CHARGE}, {pc: s[0] for pc, s in SITES.items()})
        self.assertEqual({pc: v[0] for pc, v in ops.items() if v[1] == VOLT_SWITCH}, MAIN_PATH)

    def test_free_slot_path_is_the_countmonmoves_branch(self):
        """CountMonMoves @4309, then 'GoToIf LE 3' @4321 jumps to 6363, whose SetMonMove is the first site."""
        _, ins = R.disasm(M.Narc.parse(self.archive).files[MEMBER])
        self.assertEqual(self.cmds[ins[4309][0]][0], "CountMonMoves")
        self.assertEqual(self.cmds[ins[4321][0]][0], "GoToIf")
        self.assertEqual((ins[4321][1][0], ins[4321][3]), (3, 6363))
        self.assertEqual(self.cmds[ins[6363][0]][0], "BufferPartyMonNick")
        self.assertEqual(ins[6363][2], 6368)

    def test_only_the_three_operands_change(self):
        before = M.Narc.parse(self.archive).files
        after = self.apply()
        self.assertEqual([i for i in range(len(before)) if before[i] != after[i]], [MEMBER])
        a, b = before[MEMBER], after[MEMBER]
        self.assertEqual(len(a), len(b))
        changed = [k for k, (x, y) in enumerate(zip(a, b)) if x != y]
        self.assertEqual(changed, [pc + off + d for pc, (_, off) in sorted(SITES.items()) for d in (0, 1)])
        for pc, (_, off) in SITES.items():
            self.assertEqual(struct.unpack_from("<H", a, pc + off)[0], CHARGE)
            self.assertEqual(struct.unpack_from("<H", b, pc + off)[0], VOLT_SWITCH)

    def test_decode_shows_volt_switch_everywhere_and_nothing_else_differs(self):
        a = M.Narc.parse(self.archive).files[MEMBER]
        after = self.apply()[MEMBER]
        _, ins_a = R.disasm(a)
        _, ins_b = R.disasm(after)
        self.assertEqual(sorted(ins_a), sorted(ins_b))
        self.assertEqual({pc for pc in ins_a if ins_a[pc] != ins_b[pc]}, set(SITES))
        ops = self.move_operands(after)
        self.assertEqual({pc for pc, v in ops.items() if v[1] == VOLT_SWITCH}, set(SITES) | set(MAIN_PATH))
        self.assertFalse([pc for pc, v in ops.items() if v[1] == CHARGE])
        # the Counter lesson of the same script is untouched
        self.assertTrue(any(v[1] == COUNTER for v in ops.values()))

    def test_move_table_names(self):
        with open(HERE.parent / "translate/banks/a027/0739.json", encoding="utf-8") as f:
            names = {s["id"]: s["zh"] for s in json.load(f)["strings"]}
        self.assertEqual((names[CHARGE], names[VOLT_SWITCH]), ("充电", "伏特替换"))

    def test_guards_reject_changed_source(self):
        files = M.Narc.parse(self.archive).files
        bad = bytearray(files[MEMBER])
        bad[3000] ^= 1
        files[MEMBER] = bytes(bad)
        store = {"a/0/1/2": M.Narc(files).build()}
        original = store["a/0/1/2"]
        with self.assertRaises(N.NarcPatchError):
            N.apply(store.__getitem__, store.__setitem__, [self.fix])
        self.assertEqual(store["a/0/1/2"], original)

    def test_expected_bytes_guard_independently(self):
        files = M.Narc.parse(self.archive).files
        bad = bytearray(files[MEMBER])
        bad[6374] ^= 1
        files[MEMBER] = bytes(bad)
        fix = copy.deepcopy(self.fix)
        for e in fix["narc_bytes"]:
            e["member_sha1"] = hashlib.sha1(bad).hexdigest()
        store = {"a/0/1/2": M.Narc(files).build()}
        with self.assertRaisesRegex(N.NarcPatchError, "expected"):
            N.apply(store.__getitem__, store.__setitem__, [fix])


if __name__ == "__main__":
    unittest.main()
