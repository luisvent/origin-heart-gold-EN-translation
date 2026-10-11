"""Reject false reward announcements even when the Bag stays unchanged."""

import unittest

from emu_honey_gather import assert_rewards


def negative_trace(case, baseline=False):
    item = 11 if case == "pickup-full" else 94 if case == "full" and not baseline else None
    party_size = 3 if case == "multiple" else 2
    return dict(
        case=case,
        before=999 if case == "full" else 1,
        after=999 if case == "full" else 1,
        pickup_before=999,
        pickup_after=999,
        party_before=[{}] * party_size,
        entries=[dict(side=0)],
        returns=[dict(count=0, items=[0] * party_size)],
        bag_calls=[] if item is None else [dict(item=item, qty=1)],
    )


CASES = [(case, False) for case in ("held", "full", "failed-roll", "pickup-full")]
CASES += [(case, True) for case in ("win", "trainer", "multiple", "held", "full", "failed-roll")]


class RewardTraceTests(unittest.TestCase):
    def test_valid_negative_results(self):
        for case, baseline in CASES:
            with self.subTest(case=case, baseline=baseline):
                assert_rewards(negative_trace(case, baseline), baseline)

    def test_phantom_reward_is_rejected_with_unchanged_bag(self):
        for case, baseline in CASES:
            # Reject a false count, a stale item slot, and a complete false award
            # independently: checking just one of count/items is insufficient.
            empty_items = negative_trace(case, baseline)["returns"][0]["items"]
            false_items = empty_items.copy()
            false_items[1] = 94
            for count, items in [(1, empty_items), (0, false_items), (1, false_items)]:
                with self.subTest(case=case, baseline=baseline, count=count, items=items):
                    row = negative_trace(case, baseline)
                    row["returns"] = [dict(count=count, items=items)]
                    with self.assertRaises(AssertionError):
                        assert_rewards(row, baseline)

    def test_missing_or_duplicate_hooks_cannot_pass(self):
        for field in ("entries", "returns"):
            for count in (0, 2):
                with self.subTest(field=field, count=count):
                    row = negative_trace("full")
                    row[field] *= count
                    with self.assertRaises(AssertionError):
                        assert_rewards(row)

    def test_unexpected_or_missing_bag_call_is_rejected(self):
        for case, baseline in CASES:
            with self.subTest(case=case, baseline=baseline):
                row = negative_trace(case, baseline)
                row["bag_calls"] = [] if row["bag_calls"] else [dict(item=94, qty=1)]
                with self.assertRaises(AssertionError):
                    assert_rewards(row, baseline)

    def test_full_party_output_must_be_present_and_zero(self):
        for items in ([], [0], [0, 0, 0], [94, 0]):
            with self.subTest(items=items):
                row = negative_trace("full")
                row["returns"][0]["items"] = items
                with self.assertRaises(AssertionError):
                    assert_rewards(row)

    def test_original_pickup_false_award_is_only_accepted_as_baseline(self):
        row = negative_trace("pickup-full")
        row["returns"] = [dict(count=1, items=[0, 11])]
        assert_rewards(row, baseline=True)
        with self.assertRaises(AssertionError):
            assert_rewards(row)


if __name__ == "__main__":
    unittest.main()
