"""Compile and execute the real native policy C on the host via ctypes.

These are arithmetic/eligibility tests, NOT proof of hooks, battle distribution,
EV application or save persistence. No replacement C/Python implementation.
"""
import ctypes
import itertools
import os
from pathlib import Path
import random
import unittest
from support import SOURCE, command, scratch, sha256

U32 = 0xFFFFFFFF


class CompiledPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src = SOURCE / 'native/policy.c'
        if not src.is_file():
            raise unittest.SkipTest('Approved native/policy.c not yet delivered')
        cls.stage = scratch('host-policy-')
        cls.addClassCleanup(cls.stage.cleanup)
        lib = Path(cls.stage.name) / 'policy.so'
        cls.source_sha256 = sha256(src)
        command([os.environ.get('CC', 'clang'), '-std=c99', '-O2', '-Wall', '-Wextra',
                 '-Werror', '-fPIC', '-shared', src, '-o', lib])
        if sha256(src) != cls.source_sha256:
            raise AssertionError('policy.c changed during compilation; rerun')
        cls.lib = ctypes.CDLL(str(lib))
        for name, argc in [('dg_clamp_exp', 4), ('dg_exp_eligible', 3),
                           ('dg_item_battle_mask', 5)]:
            fn = getattr(cls.lib, name)
            fn.argtypes = [ctypes.c_uint32] * argc
            fn.restype = ctypes.c_uint32

    def test_predicates_accept_nonzero_and_preserve_native_value(self):
        for native in (0, 1, 7, 0x80000000, U32):
            for participant, share in itertools.product((0, 1, 7, U32), repeat=2):
                self.assertEqual(self.lib.dg_exp_eligible(native, participant, share),
                                 native if participant or share else 0)
        for enabled in (1, 7, 0x80000000, U32):
            self.assertEqual(self.lib.dg_clamp_exp(99, U32, 100, enabled), 1)
            self.assertEqual(self.lib.dg_item_battle_mask(17, 0xA5, 0x5A, enabled, enabled), 0x5A)

    def test_clamp_boundaries_and_unsigned_overflow(self):
        values = [0, 1, 2, 7, 99, 100, 101, 1250000, 0x7FFFFFFF,
                  0x80000000, U32 - 1, U32]
        for current, requested, ceiling in itertools.product(values, repeat=3):
            with self.subTest(current=current, requested=requested, ceiling=ceiling):
                room = max(0, ceiling - current)  # Python exact arithmetic is the oracle.
                self.assertEqual(self.lib.dg_clamp_exp(current, requested, ceiling, 1),
                                 min(requested, room))
                self.assertEqual(self.lib.dg_clamp_exp(current, requested, ceiling, 0), requested)

    def test_clamp_every_cap_boundary(self):
        for ceiling in range(0, 4097):
            for current in {0, max(0, ceiling - 1), ceiling, ceiling + 1, U32}:
                for requested in {0, 1, ceiling, ceiling + 1, U32}:
                    actual = self.lib.dg_clamp_exp(current, requested, ceiling, 1)
                    self.assertEqual(actual, min(requested, max(0, ceiling - current)))
                    self.assertLessEqual(actual, requested)
                    if current >= ceiling:
                        self.assertEqual(actual, 0)  # Never lower an old overlevel mon.

    def test_clamp_full_width_random_vectors(self):
        rng = random.Random(0xD1FF)
        for _ in range(10000):
            current, requested, ceiling = [rng.getrandbits(32) for _ in range(3)]
            self.assertEqual(self.lib.dg_clamp_exp(current, requested, ceiling, 1),
                             min(requested, max(0, ceiling - current)))

    def test_eligibility_truth_table_caps_not_an_input(self):
        for native, participant, share in itertools.product([0, 1], repeat=3):
            self.assertEqual(self.lib.dg_exp_eligible(native, participant, share),
                             int(bool(native and (participant or share))))

    def test_independent_awards_no_redistribution_vectors(self):
        # Award magnitudes are already computed by the native battle engine.
        # Applying C to vectors proves helper isolation only, not the native caller.
        vectors = [([100, 50], [26, 13], [1, 0], [0, 13]),
                   ([100, 50], [26, 26], [1, 1], [0, 26]),
                   ([50, 100], [26, 13], [1, 0], [26, 0]),
                   ([99, 50], [26, 13], [1, 0], [1, 13]),
                   ([110, 50], [26, 13], [1, 0], [0, 13])]
        for current, awards, participated, expected in vectors:
            for share in (0, 1):
                result = [self.lib.dg_clamp_exp(c, award, 100, 1)
                          if self.lib.dg_exp_eligible(1, p, share) else 0
                          for c, award, p in zip(current, awards, participated)]
                self.assertEqual(result, [v if p or share else 0
                                          for v, p in zip(expected, participated)])

    def test_item_permissions_all_ids_and_context_differentials(self):
        for item in range(65536):
            allowed = 65 <= item <= 67 or 149 <= item <= 212
            for context, all_items in itertools.product((0, 1), repeat=2):
                expected = 0xA5 if not context else (0x5A if all_items else (0xA5 if allowed else 0))
                self.assertEqual(self.lib.dg_item_battle_mask(item, 0xA5, 0x5A, context, all_items),
                                 expected, (item, context, all_items))

    def test_item_masks_preserve_native_denial_and_exact_bits(self):
        for item in [0, 64, 65, 66, 67, 68, 148, 149, 212, 213, 65535]:
            for original, available in itertools.product([0, 1, 2, 0x80, U32], repeat=2):
                self.assertEqual(self.lib.dg_item_battle_mask(item, original, available, 0, 1), original)
                self.assertEqual(self.lib.dg_item_battle_mask(item, original, available, 1, 1), available)
                self.assertEqual(self.lib.dg_item_battle_mask(item, 0, available, 1, 0), 0)
