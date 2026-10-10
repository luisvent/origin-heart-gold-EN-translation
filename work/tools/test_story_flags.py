"""Exact source guards and actual native execution for the issue9 no-op repair.

Only local ROMs supply instruction/script bytes. The generic executor rejects
the original bad operand at its assertion boundary; wider original-write tests
remain private evidence with an explicit returning-assertion fixture.
"""

import copy
import hashlib
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "docs")]
import fixes as F
import msgtool as M
import narcpatch as P
import native_script_state as N
import romdata as R

FIX_ID = "mortar-invalid-flag-noop"


def apply(archive, fixes):
    store = {"a/0/1/2": archive}
    report = P.apply(store.__getitem__, store.__setitem__, fixes)
    assert P.verify(store.__getitem__, report).startswith("ok")
    return store["a/0/1/2"]


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class StoryFlagTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = N.load_source(F.ROM_CN)
        cls.archive = M.get_file(M.load_rom(F.ROM_CN), "a/0/1/2")
        cls.fix = next(f for f in F.load_all() if f["id"] == FIX_ID)
        cls.fixed = {**cls.source, "scripts": M.Narc.parse(apply(cls.archive, [cls.fix])).files}

    def test_exact_operand_only_and_story_tail(self):
        before, after = self.source["scripts"], self.fixed["scripts"]
        self.assertEqual([i for i, (a, b) in enumerate(zip(before, after)) if a != b], [962])
        a, b = bytes(before[962]), bytes(after[962])
        self.assertEqual(len(a), len(b))
        self.assertEqual([i for i, (x, y) in enumerate(zip(a, b)) if x != y], [1821, 1822])
        ea, ia = R.disasm(a)
        eb, ib = R.disasm(b)
        self.assertEqual(ea, eb)
        self.assertEqual(set(ia), set(ib))
        self.assertEqual([pc for pc in ia if ia[pc] != ib[pc]], [1819])
        for pc, args in ((1815, [675]), (1819, [0]), (1823, [670]), (1827, [0x409F, 7])):
            self.assertEqual(ib[pc][1], args)
        self.assertEqual(R.cmds()[ib[1833][0]][0], "ReleaseAll")
        self.assertEqual(R.cmds()[ib[1835][0]][0], "End")
        # Route1, NPC hide/clear sites and unrelated legendary state stay intact.
        for member in (98, 168, 246, 822):
            self.assertEqual(before[member], after[member])

    def test_whole_member_guard_is_atomic(self):
        for offset in (0, 136, 1821, len(self.source["scripts"][962]) - 1):
            with self.subTest(offset=offset):
                files = M.Narc.parse(self.archive).files
                changed = bytearray(files[962])
                changed[offset] ^= 1
                files[962] = bytes(changed)
                archive = M.Narc(files).build()
                store = {"a/0/1/2": archive}
                with self.assertRaisesRegex(P.NarcPatchError, "SHA-1"):
                    P.apply(store.__getitem__, store.__setitem__, [self.fix])
                self.assertEqual(store["a/0/1/2"], archive)

    def test_operand_guard_independent_of_member_pin(self):
        fix = copy.deepcopy(self.fix)
        files = M.Narc.parse(self.archive).files
        changed = bytearray(files[962])
        changed[1821] ^= 1
        files[962] = bytes(changed)
        fix["narc_bytes"][0]["member_sha1"] = hashlib.sha1(changed).hexdigest()
        archive = M.Narc(files).build()
        store = {"a/0/1/2": archive}
        with self.assertRaisesRegex(P.NarcPatchError, "expected"):
            P.apply(store.__getitem__, store.__setitem__, [fix])
        self.assertEqual(store["a/0/1/2"], archive)

    def test_composes_with_completed_expedition_patch(self):
        gate = next(f for f in F.load_all() if f["id"] == "expedition-completed-progress")
        forward = M.Narc.parse(apply(self.archive, [gate, self.fix])).files
        reverse = M.Narc.parse(apply(self.archive, [self.fix, gate])).files
        self.assertEqual(forward, reverse)
        a, b = bytes(self.source["scripts"][962]), bytes(forward[962])
        self.assertEqual([i for i, (x, y) in enumerate(zip(a, b)) if x != y], [136, 1821, 1822])
        self.assertEqual(b[136:138], bytes.fromhex("0436"))
        self.assertEqual(b[1819:1823], bytes.fromhex("1e000000"))

    def test_actual_native_set0_has_no_persisted_read_or_write(self):
        scene = N.Scene(self.fixed)
        before = bytes(scene.cpu.r8(N.VARS + i) for i in range(0x500))
        scene.one(962, 1819)
        self.assertEqual(scene.trace[0]["args"], [0])
        self.assertEqual(scene.trace[0]["cursor"], 1823)
        self.assertFalse(scene.trace[0]["writes"])
        self.assertEqual(bytes(scene.cpu.r8(N.VARS + i) for i in range(0x500)), before)
        self.assertIn(0x0204F894, scene.cpu.executed)  # real resolver call
        self.assertNotIn(0x0204F8AC, scene.cpu.executed)  # no persisted LDRB
        self.assertNotIn(0x0204F8B2, scene.cpu.executed)  # no persisted STRB
        original = N.Scene(self.source)
        with self.assertRaisesRegex(RuntimeError, "native assertion reached"):
            original.one(962, 1819)

    def test_actual_native_tail_and_unrelated_array_bytes(self):
        for state675 in (False, True):
            for state670 in (False, True):
                scene = N.Scene(self.fixed)
                scene.cpu.fixture_flag(675, state675)
                scene.cpu.fixture_flag(670, state670)
                scene.cpu.fixture_var(0x409F, 6)
                before = bytes(scene.cpu.r8(N.VARS + i) for i in range(0x500))
                end = scene.run(962, 1815)
                self.assertEqual(end, 1835)
                self.assertTrue(scene.cpu.flag(675))
                self.assertFalse(scene.cpu.flag(670))
                self.assertEqual(scene.cpu.var(0x409F), 7)
                after = bytes(scene.cpu.r8(N.VARS + i) for i in range(0x500))
                expected = bytearray(before)
                expected[0x2E0 + (675 >> 3)] |= 1 << (675 & 7)
                expected[0x2E0 + (670 >> 3)] &= ~(1 << (670 & 7))
                expected[2 * (0x409F - 0x4000)] = 7
                self.assertEqual(after, bytes(expected))
                noop = next(row for row in scene.trace if row["pc"] == 1819)
                self.assertFalse(noop["writes"])
                self.assertEqual([r["pc"] for r in scene.trace], [1815, 1819, 1823, 1827, 1833, 1835])


if __name__ == "__main__":
    unittest.main()
