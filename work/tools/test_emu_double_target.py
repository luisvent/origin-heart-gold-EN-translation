"""Fail-closed evidence checks for the fresh-ROM double-target harness."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_double_target as target


# Hand-authored transitions in UP, DOWN, LEFT, RIGHT, DOWN/UP order. Neither
# fixtures nor their expected screenshots call the navigation oracle under test.
NAMES = ('lead(OL)', 'foeR(FR)', 'partner(OR)', 'foeL(FL)', 'cancel')
QUADS = ('OL', 'FR', 'OR', 'FL', 'CANCEL')
PROBES = ('UP', 'DOWN', 'LEFT', 'RIGHT', 'DOWN,UP')
OPENING = (8, [0, 1, 1, 1], 3, ((3, 3), (4, 4), (3, 3), (1, 1), 2))
SELF = (6, [0, 0, 1, 0], 2, ((2, 2), (4, 4), (2, 2), (2, 2), 2))
ALLY_L = (
    (8, [0, 1, 1, 0], 1, ((1, 1), (2, 4), (1, 1), (1, 1), 1)),
    (9, [1, 1, 0, 0], 1, ((1, 1), (4, 4), (0, 0), (1, 1), 1)),
)
ALLY_R = (
    (8, [0, 0, 1, 1], 3, ((3, 3), (4, 4), (3, 3), (2, 2), 2)),
    (9, [1, 0, 0, 1], 3, ((3, 3), (0, 4), (3, 3), (3, 3), 3)),
)


def target_row(spec, label='geometry', actor=1, present=None, group_quad=None):
    mode, mask, initial, transitions = spec
    def pair(slot):
        quad = group_quad if mode in (1, 2, 3, 5, 7) and slot != 4 else QUADS[slot]
        return [quad, NAMES[slot]]
    probes = {direction: [pair(s) for s in slots] if direction != 'DOWN,UP' else pair(slots)
              for direction, slots in zip(PROBES, transitions)}
    return {'ev': 'target', 'who': label, 'actor': actor, 'mode': mode,
            'avail': list(mask), 'present': present or [1, 13, 2, 14],
            'init': NAMES[initial], 'init_quad': pair(initial)[0],
            'tgt': initial, 'probe': probes}


def evidence(case='allyL', old=False):
    later = list(copy.deepcopy(ALLY_L if case == 'allyL' else ALLY_R))
    if old:
        index, direction, initial = (1, 2, 1) if case == 'allyL' else (0, 3, 3)
        mode, mask, init, transitions = later[index]
        transitions = list(transitions)
        transitions[direction] = (initial, initial)
        later[index] = (mode, mask, init, transitions)
    critical, selected = ('t2_c1', 0) if case == 'allyL' else ('t2_c0', 2)
    if old:
        selected = 1 if case == 'allyL' else 3
    rows = []
    for turn, specs in enumerate(((OPENING, SELF), later, later), 1):
        for cmd, spec in enumerate(specs):
            label = f't{turn}_c{cmd}'
            rows.append({'ev': 'menu', 'turn': turn, 'actor': cmd + 1})
            present = [1, 13, 2, 14] if turn == 1 else (
                [1, 13, 2, 0] if case == 'allyL' else [1, 0, 2, 14])
            rows.append(target_row(spec, label, cmd + 1, present))
            if label == critical:
                rows.extend([{'ev': 'accepted', 'who': label, 'slot': selected},
                             {'ev': 'engine_target', 'who': label, 'slot': selected}])
    rows.append({'ev': 'final', 'state': 'menu'})
    return rows


def isolated(row):
    return [row, {'ev': 'final', 'state': 'menu'}]


def samples(row):
    for direction in PROBES:
        values = [row['probe'][direction]] if direction == 'DOWN,UP' else row['probe'][direction]
        for index, sample in enumerate(values):
            yield direction, index, sample


class EvidenceTests(unittest.TestCase):
    def assert_rejected(self, rows, case='allyL', horizontal=True):
        with self.assertRaises(AssertionError):
            target.validate(rows, case, horizontal)

    def test_complete_mirrored_fixtures_and_historical_controls(self):
        for case in ('allyL', 'allyR'):
            with self.subTest(case=case):
                self.assertTrue(target.validate(evidence(case), case)['pass'])
                self.assertTrue(target.validate(evidence(case, old=True), case, horizontal=False)['pass'])
                self.assert_rejected(evidence(case, old=True), case)

    def test_cursor_without_engine_acceptance_is_not_a_pass(self):
        for case, label in (('allyL', 't2_c1'), ('allyR', 't2_c0')):
            for event in ('accepted', 'engine_target'):
                with self.subTest(case=case, event=event):
                    rows = evidence(case)
                    next(r for r in rows if r['ev'] == event)['slot'] = 1
                    self.assert_rejected(rows, case)
                    rows = [r for r in evidence(case) if not (r['ev'] == event and r['who'] == label)]
                    self.assert_rejected(rows, case)

    def test_acceptance_without_next_turn_is_not_a_pass(self):
        for case in ('allyL', 'allyR'):
            rows = [r for r in evidence(case) if not (r['ev'] == 'menu' and r['turn'] == 3)]
            self.assert_rejected(rows, case)

    def test_incomplete_command_sequence_is_not_a_pass(self):
        for case in ('allyL', 'allyR'):
            rows = [r for r in evidence(case) if r.get('who') != 't1_c0']
            self.assert_rejected(rows, case)

    def test_every_row_requires_every_probe(self):
        for case in ('allyL', 'allyR'):
            for row_index in (i for i, r in enumerate(evidence(case)) if r['ev'] == 'target'):
                for direction in PROBES:
                    with self.subTest(case=case, row=row_index, direction=direction):
                        rows = evidence(case)
                        del rows[row_index]['probe'][direction]
                        self.assert_rejected(rows, case)

    def test_missing_empty_or_invalid_probe_map_is_not_a_pass(self):
        for value in (None, {}, [], 'LEFT'):
            with self.subTest(value=value):
                rows = evidence()
                rows[1]['probe'] = value
                self.assert_rejected(rows)
        rows = evidence()
        del rows[1]['probe']
        self.assert_rejected(rows)

    def test_unknown_probe_key_is_not_a_pass(self):
        for unknown in ('SIDEWAYS', 'UP,DOWN', 'LEFT,LEFT'):
            rows = evidence()
            rows[1]['probe'][unknown] = rows[1]['probe']['UP']
            self.assert_rejected(rows)

    def test_cardinal_probes_require_exactly_two_samples(self):
        for direction in PROBES[:4]:
            for count in (0, 1, 3):
                with self.subTest(direction=direction, count=count):
                    rows = evidence()
                    pair = rows[1]['probe'][direction][0]
                    rows[1]['probe'][direction] = [pair] * count
                    self.assert_rejected(rows)

    def test_composed_probe_requires_one_flat_final_pair(self):
        for malformed in ([], [['OR', NAMES[2]]], [['OR', NAMES[2]]] * 2,
                          ['OR', NAMES[2], 'extra'], 'OR', None):
            with self.subTest(malformed=malformed):
                rows = evidence()
                rows[1]['probe']['DOWN,UP'] = malformed
                self.assert_rejected(rows)

    def test_repeated_samples_require_pairs(self):
        for direction in PROBES[:4]:
            for index in (0, 1):
                for malformed in (None, 'FR', [], ['FR'], ['FR', NAMES[1], 'extra'], {'quad': 'FR'}):
                    with self.subTest(direction=direction, index=index, malformed=malformed):
                        rows = evidence()
                        rows[1]['probe'][direction][index] = malformed
                        self.assert_rejected(rows)

    def test_unknown_slots_in_every_sample_are_rejected(self):
        for direction, index, _ in samples(evidence()[1]):
            for unknown in (None, 'unknown', 1, []):
                with self.subTest(direction=direction, index=index, unknown=unknown):
                    rows = evidence()
                    values = rows[1]['probe'][direction]
                    pair = values if direction == 'DOWN,UP' else values[index]
                    pair[1] = unknown
                    self.assert_rejected(rows)

    def test_wrong_stored_slots_in_every_sample_are_rejected(self):
        for direction, index, _ in samples(evidence()[1]):
            with self.subTest(direction=direction, index=index):
                rows = evidence()
                values = rows[1]['probe'][direction]
                pair = values if direction == 'DOWN,UP' else values[index]
                wrong = (NAMES.index(pair[1]) + 1) % 5
                pair[:] = [QUADS[wrong], NAMES[wrong]]
                self.assert_rejected(rows)

    def test_wrong_or_missing_visuals_in_every_sample_are_rejected(self):
        for case in ('allyL', 'allyR'):
            for direction, index, _ in samples(evidence(case)[1]):
                for visual in ('wrong', None):
                    with self.subTest(case=case, direction=direction, index=index, visual=visual):
                        rows = evidence(case)
                        values = rows[1]['probe'][direction]
                        pair = values if direction == 'DOWN,UP' else values[index]
                        pair[0] = 'FR' if visual == 'wrong' and pair[0] != 'FR' else ('OL' if visual == 'wrong' else None)
                        self.assert_rejected(rows, case)

    def test_initial_single_target_visuals_include_self_modes(self):
        specs = (OPENING, SELF, (4, [1, 0, 0, 0], 0,
                               ((0, 0), (4, 4), (0, 0), (0, 0), 0)))
        for spec in specs:
            row = target_row(spec)
            self.assertTrue(target.validate(isolated(row), 'geometry')['pass'])
            for visual in ('FR', None):
                with self.subTest(mode=spec[0], visual=visual):
                    bad = copy.deepcopy(row)
                    bad['init_quad'] = visual
                    self.assert_rejected(isolated(bad), 'geometry')
            bad = copy.deepcopy(row)
            del bad['init_quad']
            self.assert_rejected(isolated(bad), 'geometry')

    def test_self_target_probe_visuals_are_checked(self):
        for mode, initial, mask in ((4, 0, [1, 0, 0, 0]), (6, 2, [0, 0, 1, 0])):
            spec = (mode, mask, initial, ((initial, initial), (4, 4),
                                        (initial, initial), (initial, initial), initial))
            for direction, index, _ in samples(target_row(spec)):
                with self.subTest(mode=mode, direction=direction, index=index):
                    row = target_row(spec)
                    values = row['probe'][direction]
                    (values if direction == 'DOWN,UP' else values[index])[0] = 'FR'
                    self.assert_rejected(isolated(row), 'geometry')

    def test_cancel_initial_and_probe_visuals_are_checked(self):
        spec = (6, [0, 0, 1, 0], 4, ((2, 2), (4, 4), (4, 4), (4, 4), 2))
        row = target_row(spec)
        self.assertTrue(target.validate(isolated(row), 'geometry')['pass'])
        bad = copy.deepcopy(row)
        bad['init_quad'] = 'OR'
        self.assert_rejected(isolated(bad), 'geometry')
        for direction, index, sample in samples(row):
            if sample[1] == 'cancel':
                with self.subTest(direction=direction, index=index):
                    bad = copy.deepcopy(row)
                    bad['probe'][direction][index][0] = 'OR'
                    self.assert_rejected(isolated(bad), 'geometry')

    def test_spread_group_visuals_do_not_identify_representative(self):
        for mode in (1, 2, 3, 5, 7):
            # The classifier may report FL, CANCEL, or no region for a group
            # represented by foeR; all are independent of the stored slot.
            spec = (mode, [0, 1, 0, 1], 1, ((1, 1), (4, 4), (1, 1), (1, 1), 1))
            for visual in ('FL', 'CANCEL', None):
                with self.subTest(mode=mode, visual=visual):
                    row = target_row(spec, group_quad=visual)
                    self.assertTrue(target.validate(isolated(row), 'geometry')['pass'])
                    bad = copy.deepcopy(row)
                    bad['probe']['UP'][0][1] = NAMES[3]
                    self.assert_rejected(isolated(bad), 'geometry')

    def test_spread_actual_cancel_visuals_are_checked(self):
        for mode in (1, 2, 3, 5, 7):
            spec = (mode, [0, 1, 0, 1], 4, ((1, 1), (4, 4), (4, 4), (4, 4), 1))
            row = target_row(spec, group_quad='FL')
            self.assertTrue(target.validate(isolated(row), 'geometry')['pass'])
            bad = copy.deepcopy(row)
            bad['init_quad'] = 'FL'
            self.assert_rejected(isolated(bad), 'geometry')
            for direction, index, sample in samples(row):
                if sample[1] == 'cancel':
                    for visual in ('FL', None):
                        with self.subTest(mode=mode, direction=direction, index=index, visual=visual):
                            bad = copy.deepcopy(row)
                            bad['probe'][direction][index][0] = visual
                            self.assert_rejected(isolated(bad), 'geometry')
            # No eligible representative: the composed result remains CANCEL.
            empty = (mode, [0, 0, 0, 0], 4, ((4, 4), (4, 4), (4, 4), (4, 4), 4))
            row = target_row(empty)
            self.assertTrue(target.validate(isolated(row), 'geometry')['pass'])
            row['probe']['DOWN,UP'][0] = 'FL'
            self.assert_rejected(isolated(row), 'geometry')

    def test_independently_specified_navigation_transitions(self):
        transitions = (
            ([1, 1, 0, 1], 1, 'LEFT', 3, 3),  # adjacent before diagonal
            ([1, 1, 0, 0], 1, 'LEFT', 0, 1),  # left fallback / historical stay
            ([0, 0, 1, 1], 3, 'RIGHT', 2, 3),  # mirrored fallback
            ([0, 1, 1, 1], 2, 'LEFT', 3, 2),  # fallback toward the foe row
            ([1, 1, 0, 1], 0, 'RIGHT', 1, 0),
            ([0, 1, 1, 1], 3, 'DOWN', 4, 4), # same-column CANCEL before other ally
            ([1, 1, 0, 0], 1, 'DOWN', 4, 4),
            ([0, 0, 1, 1], 4, 'UP', 2, 2),
            ([1, 1, 0, 0], 4, 'UP', 1, 1),  # upward scan before alternate column
            ([1, 0, 0, 0], 4, 'UP', 0, 0),  # alternate-column retry
            ([0, 0, 0, 0], 4, 'UP', 4, 4),
            ([1, 1, 1, 1], 3, 'LEFT', 3, 3),
            ([1, 1, 1, 1], 1, 'RIGHT', 1, 1),
            ([1, 1, 1, 1], 4, 'LEFT', 4, 4),
            ([1, 1, 1, 1], 4, 'RIGHT', 4, 4),
        )
        for mask, initial, direction, new, old in transitions:
            for horizontal, expected in ((True, new), (False, old)):
                with self.subTest(mask=mask, initial=initial, direction=direction, horizontal=horizontal):
                    self.assertEqual(target.expected_nav(mask, initial, direction, horizontal), expected)


if __name__ == '__main__':
    unittest.main()
