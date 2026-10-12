"""The four price/coin script-operand fixes together with the other fixes that edit the same script members.

Members: 895 (fortune-ideal-price-check), 156 (ssanne-tm-price-check, and a blank-player-name-batch insert),
903 (gamecorner-500-coins), 94 (haircut-younger-price-check).  The [[narc_bytes]] entries run first on the hack's
member, the [[script_insert]] entries after them, so the order of the fix list must not matter and every patched
member must still decode.

Run:  python3 -m unittest -v work/tools/test_price_fixes_combined.py
"""

import hashlib
import itertools
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "docs")]
import fixes as F
import msgtool as M
import narcpatch as N
import romdata as R
import scriptinsert as SI

PRICE = ["fortune-ideal-price-check", "ssanne-tm-price-check", "gamecorner-500-coins", "haircut-younger-price-check"]
BLANK = ["blank-player-name", "blank-player-name-batch", "blank-player-name-class-c"]
MEMBERS = {895: "fortune-ideal-price-check", 156: "ssanne-tm-price-check", 903: "gamecorner-500-coins",
           94: "haircut-younger-price-check"}


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class Combined(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = M.get_file(M.load_rom(F.ROM_CN), "a/0/1/2")
        cls.fixes = {f["id"]: f for f in F.load_all()}
        cls.before = M.Narc.parse(cls.archive).files

    def patched(self, *ids):
        store = {"a/0/1/2": self.archive}
        rows = N.apply(store.__getitem__, store.__setitem__, [self.fixes[i] for i in ids])
        self.assertTrue(N.verify(store.__getitem__, rows).startswith("ok"))
        return M.Narc.parse(store["a/0/1/2"]).files

    def test_price_fixes_touch_only_their_members(self):
        a = self.patched(*PRICE)
        self.assertEqual([i for i in range(len(a)) if a[i] != self.before[i]], sorted(MEMBERS))
        for m, fid in MEMBERS.items():
            self.assertEqual(a[m], self.patched(fid)[m])
            self.assertEqual(len(a[m]), len(self.before[m]))

    def test_member_156_after_the_ticket_fix_has_the_hash_the_batch_accepts(self):
        h = hashlib.sha1(self.patched("ssanne-tm-price-check")[156]).hexdigest()
        self.assertEqual(h, "eed182a4532fce39637da59ed2b1c49fa5a8c5b9")
        entry = next(e for e in F.script_insert_entries([self.fixes["blank-player-name-batch"]])
                     if e["member"] == 156)
        self.assertIn(h, entry["member_sha1"])

    def test_price_fixes_with_every_blank_name_fix_in_any_order(self):
        ids = PRICE + BLANK
        want = self.patched(*ids)
        for perm in (list(reversed(ids)), BLANK + PRICE, ids[1::2] + ids[::2]):
            self.assertEqual(self.patched(*perm), want)
        # a member 156 that has both the price fix and the batch insert
        price_only = self.patched("ssanne-tm-price-check")[156]
        batch_only = self.patched("blank-player-name-batch")[156]
        self.assertGreater(len(want[156]), len(price_only))
        self.assertEqual(len(want[156]), len(batch_only))
        for m in MEMBERS:
            SI.Layout(want[m])
            R.disasm(want[m])                               # decodes cleanly

    def test_ssanne_price_operand_survives_the_batch_insert(self):
        both = self.patched("ssanne-tm-price-check", "blank-player-name-batch")[156]
        _, ins = R.disasm(both)
        amounts = [v[1][1] for v in ins.values() if R.cmds()[v[0]][0] == "HasEnoughMoneyImmediate"]
        self.assertIn(4000, amounts)
        self.assertNotIn(400, amounts)

    def test_all_pairs_commute(self):
        for x, y in itertools.combinations(PRICE + ["blank-player-name-batch"], 2):
            self.assertEqual(self.patched(x, y), self.patched(y, x))


if __name__ == "__main__":
    unittest.main()
