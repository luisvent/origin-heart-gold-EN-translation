"""Source guards and actual-ROM native predicates for the two issue10 repairs."""

import copy
import hashlib
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "docs")]
import fixes as F
import msgtool as M
import narcpatch as N
import native_script_state as S
import romdata as R

FIX_IDS = ("expedition-completed-progress", "hooh-panel-silver-marker")


def patched_archive(archive, fixes):
    store = {"a/0/1/2": archive}
    report = N.apply(store.__getitem__, store.__setitem__, fixes)
    assert N.verify(store.__getitem__, report) == "ok (2 entries, 2 members)"
    return store["a/0/1/2"]


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class SharedProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = S.load_source(F.ROM_CN)
        cls.archive = M.get_file(M.load_rom(F.ROM_CN), "a/0/1/2")
        cls.fixes = [f for f in F.load_all() if f["id"] in FIX_IDS]
        cls.fixed = {**cls.source, "scripts": M.Narc.parse(patched_archive(cls.archive, cls.fixes)).files}

    def test_exact_operands_and_structure(self):
        before, after = self.source["scripts"], self.fixed["scripts"]
        self.assertEqual([i for i, (a, b) in enumerate(zip(before, after)) if a != b], [45, 962])
        for member, offsets, instruction in ((45, [184, 185], 182), (962, [136], 134)):
            with self.subTest(member=member):
                a, b = bytes(before[member]), bytes(after[member])
                self.assertEqual(len(a), len(b))
                self.assertEqual([i for i, (x, y) in enumerate(zip(a, b)) if x != y], offsets)
                ea, ia = R.disasm(a)
                eb, ib = R.disasm(b)
                self.assertEqual(ea, eb)
                self.assertEqual(set(ia), set(ib))
                self.assertEqual([pc for pc in ia if ia[pc] != ib[pc]], [instruction])
        _, leader = R.disasm(bytes(after[962]))
        self.assertEqual(leader[128][1], [0x409F, 10])
        self.assertEqual(leader[134][1][0], 4)
        self.assertEqual(leader[134][3], 5827)
        _, panel = R.disasm(bytes(after[45]))
        self.assertEqual(R.cmds()[panel[182][0]][0], "ClearFlag")
        self.assertEqual(panel[182][1], [0])
        # No global remap, dream rewrite, header change or save migration.
        for member in (23, 50, 52, 92, 98, 106, 149, 216, 842, 943):
            self.assertEqual(before[member], after[member])

    def test_whole_member_guards_fail_before_mutation(self):
        for fix in self.fixes:
            entry = fix["narc_bytes"][0]
            member, offset = entry["member"], int(entry["offset"], 16)
            for bad_offset in (0, offset, len(self.source["scripts"][member]) - 1):
                with self.subTest(fix=fix["id"], offset=bad_offset):
                    files = M.Narc.parse(self.archive).files
                    changed = bytearray(files[member])
                    changed[bad_offset] ^= 1
                    files[member] = bytes(changed)
                    store = {"a/0/1/2": M.Narc(files).build()}
                    original = store["a/0/1/2"]
                    with self.assertRaises(N.NarcPatchError):
                        N.apply(store.__getitem__, store.__setitem__, [fix])
                    self.assertEqual(store["a/0/1/2"], original)

    def test_expected_operand_guards_independently(self):
        for source_fix in self.fixes:
            fix = copy.deepcopy(source_fix)
            entry = fix["narc_bytes"][0]
            member, offset = entry["member"], int(entry["offset"], 16)
            files = M.Narc.parse(self.archive).files
            changed = bytearray(files[member])
            changed[offset] ^= 1
            files[member] = bytes(changed)
            entry["member_sha1"] = hashlib.sha1(changed).hexdigest()
            store = {"a/0/1/2": M.Narc(files).build()}
            original = store["a/0/1/2"]
            with self.assertRaisesRegex(N.NarcPatchError, "expected"):
                N.apply(store.__getitem__, store.__setitem__, [fix])
            self.assertEqual(store["a/0/1/2"], original)

    def test_native_expedition_gate(self):
        for state in (*range(13), 65535):
            before, after = (S.Scene(src) for src in (self.source, self.fixed))
            for scene in (before, after):
                scene.cpu.fixture_var(0x409F, state)
            old = before.run(962, 117, stop=(174, 2359, 2370, 5827))
            new = after.run(962, 117, stop=(174, 2359, 2370, 5827))
            self.assertEqual(new, 5827 if state >= 10 else old)
            self.assertEqual(after.cpu.var(0x409F), state)
            self.assertTrue(after.cpu.executed)
            self.assertFalse([w for row in after.trace for w in row.get("writes", [])])

    def test_native_late_leader_cannot_restart_battle(self):
        for state in (10, 11, 12):
            for choice in (0, 1):
                for raw in range(8):
                    s = S.Scene(self.fixed)
                    s.cpu.fixture_var(0x409F, state)
                    s.choices, s.outcomes = [choice, 0], [raw]
                    s.run(962, 117)
                    self.assertEqual(s.cpu.var(0x409F), state)
                    self.assertFalse(any(r["name"] == "TrainerBattle" for r in s.trace))
                    self.assertIn(5827, [r["pc"] for r in s.trace])
        # Original failure control really overwrites eligibility.
        s = S.Scene(self.source)
        s.cpu.fixture_var(0x409F, 11)
        s.choices, s.outcomes = [0, 0], [1]
        s.run(962, 117)
        self.assertEqual(s.cpu.var(0x409F), 3)

    def test_native_precompletion_paths_and_beast_release_unchanged(self):
        for state in (0, 1, 2, 4, 6, 7, 8, 9):
            for choice, raw in ((0, 1), (1, 1), (0, 2), (0, 3)):
                scenes = [S.Scene(src) for src in (self.source, self.fixed)]
                for s in scenes:
                    s.cpu.fixture_var(0x409F, state)
                    s.choices, s.outcomes = [choice, 0], [raw]
                    s.run(962, 117)
                # Condition operand itself differs; all actual cursors, native
                # writes, outcomes and remaining script commands must match.
                snapshots = [scene.snapshot() for scene in scenes]
                for snapshot in snapshots:
                    row = next(row for row in snapshot["trace"] if row["pc"] == 134)
                    row["args"] = [1, *row["args"][1:]]
                self.assertEqual(*snapshots)
        s = S.Scene(self.fixed)
        s.cpu.fixture_var(0x409F, 10)
        s.one(842, 2223)
        self.assertEqual(s.cpu.var(0x409F), 11)
        eligible = [r for r in S.coords(s.source["events"][5]) if r["var"] == 0x409F and r["value"] == 11]
        self.assertEqual(len(eligible), 1)  # parsed selector, not native map entry
        s.run(23, 6937, stop=(6959,))
        self.assertEqual(s.cpu.var(0x409F), 12)

    def test_native_panel_and_silver_arrival(self):
        for source, fixed in ((self.source, False), (self.fixed, True)):
            for solved in (False, True):
                for marker in (False, True):
                    s = S.Scene(source)
                    s.cpu.fixture_flag(565, marker)
                    s.cpu.fixture_flag(273, True)
                    s.cpu.fixture_flag(2426, solved)
                    s.outputs = {"ScrCmd_729": [0]}
                    s.run(45, 14)
                    expected = marker and (fixed or not solved)
                    self.assertEqual(s.cpu.flag(565), expected)
                    self.assertEqual(s.cpu.flag(273), not solved)
                    self.assertEqual(s.cpu.flag(546), solved)
                    if solved:
                        self.assertEqual(s.cpu.warp_requests[0]["map"], 315)
                        self.assertEqual([s.cpu.warp_requests[0][k] for k in ("x", "z", "direction")], [5, 24, 0])
                        clear = next(r for r in s.trace if r["pc"] == 182)
                        self.assertEqual(bool(clear["writes"]), not fixed)
                    else:
                        self.assertFalse(s.cpu.warp_requests)
                    s.cpu.fixture_flag(1980, True)
                    s.cpu.fixture_flag(1981, True)
                    s.cpu.fixture_var(0x40AB, 3)
                    arrival = s.run(50, 2675, stop=(3303, 3305, 3377, 3438, 3499))
                    self.assertEqual(arrival, 3499 if expected else 3305)
        s = S.Scene(self.fixed)
        s.one(149, 190)
        self.assertTrue(s.cpu.flag(565))

    def test_native_legitimate_silver_completion_stays_unchanged(self):
        for raw in range(8):
            scenes = [S.Scene(src) for src in (self.source, self.fixed)]
            for s in scenes:
                s.cpu.fixture_flag(565, True)
                s.coords, s.outcomes = (16, 33), [raw]
                s.run(50, 2436)
                self.assertEqual(s.cpu.flag(565), raw in (2, 3))
            self.assertEqual(scenes[0].snapshot(), scenes[1].snapshot())

    def test_executor_rejects_unknown_code_and_memory(self):
        cpu = S.NativeCPU(self.source["arm9"])
        with self.assertRaisesRegex(RuntimeError, "outside bounded"):
            cpu.call(0x02000000)
        with self.assertRaisesRegex(RuntimeError, "unmapped read"):
            cpu.r8(0x03000000)
        with self.assertRaisesRegex(RuntimeError, "unmapped write"):
            cpu.w8(0x03000000, 1)


if __name__ == "__main__":
    unittest.main()
