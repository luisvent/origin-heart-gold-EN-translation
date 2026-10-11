"""Reject incomplete or misleading Lugia scene evidence."""
import copy
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from emu_lugia import scene_passes


class SceneOracle(unittest.TestCase):
    def setUp(self):
        self.fixed = {"story_var": 8, "in_field": True, "position": (244, 18, 27),
                      "exceptions": {"data_aborts": 0, "prefetch_aborts": 0, "undefined": 0}}
        self.original = copy.deepcopy(self.fixed)
        self.original.update(story_var=7, logs=["ARM9: prefetch abort (00001004)"])
        self.original["exceptions"]["prefetch_aborts"] = 1

    def test_expected_pair(self):
        self.assertTrue(scene_passes(self.fixed, "fixed"))
        self.assertTrue(scene_passes(self.original, "original"))
        self.assertFalse(scene_passes(self.fixed, "original"))
        self.assertFalse(scene_passes(self.original, "fixed"))

    def test_completion_does_not_hide_faults(self):
        for fault in self.fixed["exceptions"]:
            report = copy.deepcopy(self.fixed)
            report["exceptions"][fault] = 1
            self.assertFalse(scene_passes(report, "fixed"))

    def test_missing_evidence_and_wrong_scene_fail(self):
        for key in self.fixed:
            report = copy.deepcopy(self.fixed)
            del report[key]
            self.assertFalse(scene_passes(report, "fixed"))
        for key, value in (("story_var", 7), ("in_field", False), ("position", (236, 8, 13))):
            self.assertFalse(scene_passes({**self.fixed, key: value}, "fixed"))

    def test_unrelated_abort_is_not_a_reproduction(self):
        self.assertFalse(scene_passes({**self.original, "logs": ["prefetch abort (00000000)"]}, "original"))
        self.assertFalse(scene_passes({**self.original, "story_var": 8}, "original"))
        self.original["exceptions"]["data_aborts"] = 1
        self.assertFalse(scene_passes(self.original, "original"))
