"""Verify the Blackthorn tutor repair: Play Rough (583) replaces Flail (175) in the four places, nothing else moves."""

import copy
import hashlib
import struct
import sys
import unittest

HERE = __import__("pathlib").Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "docs")]
import fixes as F
import msgtool as M
import narcpatch as N
import romdata as R

MEMBER = 944
FLAIL, PLAY_ROUGH, DRACO_METEOR = 175, 583, 434
# pc of the command -> (command name, operand offset inside the command)
SITES = {1925: ("MonHasMove", 4), 3461: ("SetMonMove", 6), 3551: ("PokemonSummaryScreen", 5), 3619: ("SetMonMove", 6)}


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class BlackthornTutorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = M.load_rom(F.ROM_CN)
        cls.archive = M.get_file(rom, "a/0/1/2")
        cls.fix = next(f for f in F.load_all() if f["id"] == "tutor-blackthorn-play-rough")
        cls.cmds = R.cmds()

    def apply(self, archive=None, fix=None):
        store = {"a/0/1/2": self.archive if archive is None else archive}
        report = N.apply(store.__getitem__, store.__setitem__, [fix or self.fix])
        self.assertEqual(N.verify(store.__getitem__, report), "ok (4 entries, 1 members)")
        return M.Narc.parse(store["a/0/1/2"]).files

    def move_operands(self, data):
        """Every (pc, command, move operand) of the member's tutor commands, decoded from the script."""
        _, ins = R.disasm(data)
        out = {}
        for pc, (op, args, _, _) in ins.items():
            name = self.cmds[op][0]
            if name in ("MonHasMove", "SetMonMove", "PokemonSummaryScreen"):
                out[pc] = (name, args[1] if name == "MonHasMove" else args[-1])
        return out

    def test_original_script_uses_flail_where_the_text_says_play_rough(self):
        ops = self.move_operands(M.Narc.parse(self.archive).files[MEMBER])
        flail = {pc: v[0] for pc, v in ops.items() if v[1] == FLAIL}
        self.assertEqual(flail, {pc: s[0] for pc, s in SITES.items()})
        # the other half of the script (Draco Meteor) is already right and has the same four commands
        self.assertEqual(sum(1 for v in ops.values() if v[1] == DRACO_METEOR), 4)

    def test_only_the_four_operands_change(self):
        before = M.Narc.parse(self.archive).files
        after = self.apply()
        self.assertEqual([i for i in range(len(before)) if before[i] != after[i]], [MEMBER])
        a, b = before[MEMBER], after[MEMBER]
        self.assertEqual(len(a), len(b))
        expected = sorted(o for pc, (_, off) in SITES.items() for o in (pc + off, pc + off + 1))
        changed = [k for k, (x, y) in enumerate(zip(a, b)) if x != y]
        self.assertEqual(changed, [pc + off + d for pc, (_, off) in sorted(SITES.items()) for d in (0, 1)])
        self.assertEqual(sorted(changed), expected)
        for pc, (_, off) in SITES.items():
            self.assertEqual(struct.unpack_from("<H", a, pc + off)[0], FLAIL)
            self.assertEqual(struct.unpack_from("<H", b, pc + off)[0], PLAY_ROUGH)

    def test_decode_shows_play_rough_everywhere_and_nothing_else_differs(self):
        a = M.Narc.parse(self.archive).files[MEMBER]
        after = self.apply()[MEMBER]
        _, ins_a = R.disasm(a)
        _, ins_b = R.disasm(after)
        self.assertEqual(sorted(ins_a), sorted(ins_b))
        diff = {pc for pc in ins_a if ins_a[pc] != ins_b[pc]}
        self.assertEqual(diff, set(SITES))
        ops = self.move_operands(after)
        self.assertEqual({pc for pc, v in ops.items() if v[1] == PLAY_ROUGH}, set(SITES))
        self.assertFalse([pc for pc, v in ops.items() if v[1] == FLAIL])

    def test_move_table_names(self):
        import json

        with open(HERE.parent / "translate/banks/a027/0739.json", encoding="utf-8") as f:
            names = {s["id"]: s["zh"] for s in json.load(f)["strings"]}
        self.assertEqual((names[FLAIL], names[PLAY_ROUGH]), ("抓狂", "嬉闹"))

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
        bad[3467] ^= 1
        files[MEMBER] = bytes(bad)
        fix = copy.deepcopy(self.fix)
        for e in fix["narc_bytes"]:
            e["member_sha1"] = hashlib.sha1(bad).hexdigest()
        store = {"a/0/1/2": M.Narc(files).build()}
        with self.assertRaisesRegex(N.NarcPatchError, "expected"):
            N.apply(store.__getitem__, store.__setitem__, [fix])


if __name__ == "__main__":
    unittest.main()
