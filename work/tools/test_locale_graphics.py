"""ROM-free rejection and preservation tests for prepared locale graphics."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gfx
import locale_graphics as lg
import msgtool as m
from test_gfx import _ncgr


class CodeView:
    def __init__(self, files):
        self.files = dict(files)

    def get(self, key):
        return self.files[key]

    def set(self, key, data):
        self.files[key] = data


class PixelMerge(unittest.TestCase):
    def test_preserves_newer_layout_and_donor_translation(self):
        baseline = [[(0, 1), (0, 2), (0, 3)]]
        donor = [[(0, 1), (0, 7), (0, 3)]]
        current = [[(0, 8), (0, 2), (0, 3)]]
        self.assertEqual(lg.pixel_merge(baseline, donor, current), [[(0, 8), (0, 7), (0, 3)]])
        self.assertEqual(current[0][1], (0, 2))

    def test_refuses_conflicting_edits(self):
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            lg.pixel_merge([[1]], [[2]], [[3]])

    def test_refuses_changed_dimensions(self):
        with self.assertRaisesRegex(ValueError, 'dimensions'):
            lg.pixel_merge([[1]], [[1, 2]], [[1]])


class RetailDependencies(unittest.TestCase):
    def test_accepts_matching_and_ignores_unrelated_data(self):
        lg.check_retail_dependencies([b'palette', b'old'], [b'palette', b'new'], [0])

    def test_refuses_changed_dependency(self):
        with self.assertRaisesRegex(ValueError, 'dependency 0 differs'):
            lg.check_retail_dependencies([b'palette'], [b'changed'], [0])


class PreparedAssets(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.before = _ncgr([[1] * 64])
        self.after = _ncgr([[2] * 64])
        self.unrelated = b'unrelated member'
        self.archive = m.Narc([self.before, self.unrelated]).build()
        self.files = {'a/0/0/8': self.archive}
        self.code = CodeView({'overlay14': b'abcdefgh'})
        (self.root/'asset.bin').write_bytes(self.after)
        (self.root/'code.bin').write_bytes(b'XY')
        self.receipt = dict(schema=2, locale='es', fallback_policy='allow-listed', fallbacks=[],
            archives=[dict(narc='a/0/0/8', before_sha256=lg.sha(self.archive))],
            members=[dict(narc='a/0/0/8', member=0, before_sha256=lg.sha(self.before),
                          after_sha256=lg.sha(self.after), asset='asset.bin')],
            code_ranges=[dict(file='overlay14', offset=2, length=2, before_sha256=lg.sha(b'cd'),
                              after_sha256=lg.sha(b'XY'), asset='code.bin')])

    def run_apply(self):
        (self.root/'manifest.json').write_text(json.dumps(self.receipt))
        # ROM-free fixture only. Real prepare separately exercises actual loader checks.
        with patch.object(gfx, 'check_layouts', return_value=[]):
            return lg.apply_prepared(self.files.__getitem__, self.files.__setitem__, self.code, self.root)

    def unchanged(self):
        self.assertEqual(self.files['a/0/0/8'], self.archive)
        self.assertEqual(self.code.get('overlay14'), b'abcdefgh')

    def test_replaces_only_selected_member_and_code_range(self):
        self.run_apply()
        self.assertEqual(m.Narc.parse(self.files['a/0/0/8']).files, [self.after, self.unrelated])
        self.assertEqual(self.code.get('overlay14'), b'abXYefgh')

    def test_changed_dependency_rejected_before_mutation(self):
        changed = m.Narc([self.before, b'changed palette or dependency']).build()
        self.files['a/0/0/8'] = changed
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            self.run_apply()
        self.assertEqual(self.files['a/0/0/8'], changed)
        self.assertEqual(self.code.get('overlay14'), b'abcdefgh')

    def test_tampered_payload_rejected_before_mutation(self):
        (self.root/'asset.bin').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            self.run_apply()
        self.unchanged()

    def test_bad_code_guard_does_not_partially_apply_archives(self):
        self.receipt['code_ranges'][0]['before_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            self.run_apply()
        self.unchanged()

    def test_size_change_rejected_even_with_updated_payload_hash(self):
        larger = _ncgr([[2] * 64, [3] * 64])
        (self.root/'asset.bin').write_bytes(larger)
        self.receipt['members'][0]['after_sha256'] = lg.sha(larger)
        with self.assertRaisesRegex(ValueError, 'depth/count'):
            self.run_apply()
        self.unchanged()

    def test_code_range_cannot_grow(self):
        (self.root/'code.bin').write_bytes(b'XYZ')
        self.receipt['code_ranges'][0]['after_sha256'] = lg.sha(b'XYZ')
        with self.assertRaisesRegex(ValueError, 'size changed'):
            self.run_apply()
        self.unchanged()

    def test_listed_fallback_is_reported_and_hash_checked(self):
        self.receipt['fallbacks'] = [dict(id='known-label', label='Known English label',
            kind='member', narc='a/0/0/8', member=1, sha256=lg.sha(self.unrelated))]
        result = self.run_apply()
        self.assertEqual(result['fallbacks'][0]['id'], 'known-label')
        self.assertEqual(m.Narc.parse(self.files['a/0/0/8']).files[1], self.unrelated)

    def test_changed_fallback_is_not_silently_accepted(self):
        self.receipt['fallbacks'] = [dict(id='known-label', kind='member',
            narc='a/0/0/8', member=1, sha256='0' * 64)]
        with self.assertRaisesRegex(ValueError, 'fallback known-label'):
            self.run_apply()
        self.unchanged()

    def test_strict_mode_rejects_listed_fallback_before_mutation(self):
        self.receipt['fallback_policy'] = 'error'
        self.receipt['fallbacks'] = [dict(id='known-label')]
        with self.assertRaisesRegex(ValueError, 'require listed fallbacks'):
            self.run_apply()
        self.unchanged()

    def test_missing_required_asset_still_errors_in_default_mode(self):
        (self.root/'asset.bin').unlink()
        with self.assertRaises(FileNotFoundError):
            self.run_apply()
        self.unchanged()

    def test_legacy_stage_cannot_bypass_fallback_policy(self):
        self.receipt['schema'] = 1
        self.receipt.pop('fallbacks')
        with self.assertRaisesRegex(ValueError, 'regenerate'):
            self.run_apply()
        self.unchanged()

    def test_path_escape_rejected(self):
        self.receipt['members'][0]['asset'] = '../outside.bin'
        with self.assertRaisesRegex(ValueError, 'escapes'):
            self.run_apply()
        self.unchanged()


if __name__ == '__main__':
    unittest.main()
