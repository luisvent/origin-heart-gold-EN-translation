"""Offline runner controls; no emulator or ROM required."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_struggle as S


class Turns(unittest.TestCase):
    def run_turn(self, case="last-pp", turn=1, without=True, *, usability=True,
                 action=False, menu=True, before_pp=None, after_pp=None):
        before = {"number": 1, "moves": [45, 0, 0, 0], "pp": [0] * 4 if before_pp is None else before_pp}
        after = {**before, "pp": before["pp"] if after_pp is None else after_pp}
        # Earlier turns must not satisfy the current turn's observation checks.
        t = SimpleNamespace(phase="test", rows=[{"kind": "usability", "actor": before, "move": 45}])
        h = Mock()
        h.on_screen.return_value = menu
        h.wait_screen.return_value = True

        def touch(x, y, **kw):
            if (x, y) == S.E.MOVE_BUTTONS[0]:
                if usability:
                    t.rows.append({"kind": "usability", "actor": before, "move": 45})
                if action:
                    t.rows.append({"kind": "action", "actor": before, "move": 165})

        h.touch.side_effect = touch
        with patch.object(S, "active", return_value=1), \
             patch.object(S, "snapshot", side_effect=[before, after]), \
             patch.object(S, "advance", return_value="menu") as advance:
            result = S.run_turn(h, t, Path("unused"), case, turn, without)
        return result, advance.call_count

    def test_original_exhausted_turns_reject(self):
        for case, turn in (("last-pp", 1), ("four-zero", 0), ("one-zero", 0),
                           ("trainer5", 0), ("double", 0)):
            with self.subTest(case=case):
                self.assertEqual(self.run_turn(case, turn), ("rejected", 0))

    def test_original_usable_turns_advance(self):
        for case in ("last-pp", "positive", "enemy"):
            with self.subTest(case=case):
                self.assertEqual(self.run_turn(case, 0), ("menu", 1))

    def test_fixed_turns_advance(self):
        for case in ("four-zero", "one-zero", "positive", "last-pp", "trainer5", "double", "enemy"):
            for turn in range(2 if case == "last-pp" else 1):
                with self.subTest(case=case, turn=turn):
                    self.assertEqual(self.run_turn(case, turn, False), ("menu", 1))

    def test_rejection_requires_current_usability_observation(self):
        with self.assertRaisesRegex(AssertionError, "usability check absent"):
            self.run_turn(usability=False)

    def test_rejection_requires_no_action(self):
        with self.assertRaisesRegex(AssertionError, "unexpectedly submitted"):
            self.run_turn(action=True)

    def test_rejection_requires_menu_recovery(self):
        with self.assertRaisesRegex(AssertionError, "return to command menu"):
            self.run_turn(menu=False)

    def test_rejection_requires_unchanged_zero_pp(self):
        for kw in ({"before_pp": [1, 0, 0, 0]}, {"after_pp": [1, 0, 0, 0]}):
            with self.subTest(kw=kw), self.assertRaisesRegex(AssertionError, "exhausted PP"):
                self.run_turn(**kw)


if __name__ == "__main__":
    unittest.main()
