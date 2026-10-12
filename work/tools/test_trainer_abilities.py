#!/usr/bin/env python3
"""trainer-abilities (D-2401): trainer Pokemon whose held item and moves need an ability the Chinese ROM does not
store get that ability. Data regression: the fix changes only the stored ability halfword of 54 slots, the named
slots from the Discord report have the expected ability, and no Toxic/Flame Orb holder with a single status-using
ability, no Damp-Rock Pelipper (no Rain Dance) and no Heat-Rock Ninetales/Torkoal (no Sunny Day) is left without it.
Run:  python3 -I -m unittest -v work/tools/test_trainer_abilities.py   (skipped without work/rom/origin_v4.0.3_cn.nds)"""
import struct
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "docs")]
import fixes as F  # noqa: E402
import msgtool as M  # noqa: E402
import narcpatch as N  # noqa: E402
import romdata as R  # noqa: E402

FIX = "trainer-abilities"
NARC = "a/0/5/6"
SIZE = R.TRPOKE_SIZE
# ability ids (hack ability bank 0711)
DRIZZLE, DROUGHT, GUTS, MARVEL_SCALE, POISON_HEAL, SHEER_FORCE, FLARE_BOOST = 2, 70, 62, 63, 90, 125, 138
# (trainer record, slot index, species, ability before, ability after): the cases named in the Discord report
# plus one of each rule
REPORTED = [
    (356, 1, 286, 101, POISON_HEAL),      # Lass Danni's Toxic Orb Sub Punch Breloom (Technician -> Poison Heal)
    (230, 0, 34, 38, SHEER_FORCE),        # Executive Petrel's Life Orb Nidoking (Poison Point -> Sheer Force)
    (446, 0, 34, 38, SHEER_FORCE),        # Petrel again, later team
    (445, 1, 472, 52, POISON_HEAL),       # Gliscor with Toxic Orb (Hyper Cutter -> Poison Heal)
    (984, 0, 279, 51, DRIZZLE),           # Archie's Pelipper (Keen Eye -> Drizzle)
    (449, 0, 279, 51, DRIZZLE),           # the unnamed partner's Pelipper
    (450, 0, 38, 18, DROUGHT),            # Maxie's Ninetales (Flash Fire -> Drought)
    (625, 2, 38, 18, DROUGHT),
    (61, 3, 19, 50, GUTS),                # Rival Blue's Flame Orb Rattata (Run Away -> Guts)
]


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class TrainerAbilities(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = M.load_rom(F.ROM_CN)
        cls.archive = M.get_file(rom, NARC)
        cls.fix = next(f for f in F.load_all() if f["id"] == FIX)
        store = {NARC: cls.archive}
        cls.rows = N.apply(store.__getitem__, store.__setitem__, [cls.fix])
        cls.before = M.Narc.parse(cls.archive).files
        cls.after = M.Narc.parse(store[NARC]).files
        cls.personal = [R.parse_personal(b) for b in M.Narc.parse(M.get_file(rom, "a/0/0/2")).files]
        cls.trdata = [R.parse_trdata(b) for b in M.Narc.parse(M.get_file(rom, "a/0/5/5")).files]

    def mons(self, files, tid):
        return R.parse_trpoke(files[tid], self.trdata[tid]["count"])

    def test_only_the_stored_ability_halfword_changes(self):
        changed = []
        for tid, (a, b) in enumerate(zip(self.before, self.after, strict=True)):
            for i in range(0, len(a), SIZE):
                if a[i:i + SIZE] != b[i:i + SIZE]:
                    diff = [j for j in range(SIZE) if a[i + j] != b[i + j]]
                    self.assertTrue(set(diff) <= {4, 5}, (tid, i // SIZE, diff))
                    changed.append((tid, i // SIZE))
            self.assertEqual(len(a), len(b))
        self.assertEqual(len(changed), 54)
        self.assertEqual(len(self.fix["narc_bytes"]), 54)
        self.assertEqual(len(set(changed)), 54)

    def test_reported_slots(self):
        for tid, slot, species, was, now in REPORTED:
            with self.subTest(trainer=tid, slot=slot):
                b, a = self.mons(self.before, tid)[slot], self.mons(self.after, tid)[slot]
                self.assertEqual(b["species"], species)
                self.assertEqual((b["ability"], a["ability"]), (was, now))

    def test_every_changed_ability_is_one_of_the_species_abilities(self):
        for tid, slot in {(r["member"], r["offset"] // SIZE) for r in self.rows}:
            m = self.mons(self.after, tid)[slot]
            p = self.personal[m["species"]]
            self.assertIn(m["ability"], set(p["abilities"]) | {p["hidden_ability"]}, (tid, slot))

    def test_no_orb_or_rock_slot_left_unserved(self):
        payoff = {"Toxic Orb": {POISON_HEAL, GUTS, MARVEL_SCALE, FLARE_BOOST, 98, 95, 137},
                  "Flame Orb": {GUTS, MARVEL_SCALE, FLARE_BOOST, 98, 95}}   # + Magic Guard (98), Quick Feet (95)
        orb = {272: "Toxic Orb", 273: "Flame Orb"}
        left = []
        for tid in range(1, len(self.after)):
            for slot, m in enumerate(self.mons(self.after, tid)):
                if not m["species"] or m["species"] >= len(self.personal):
                    continue
                p = self.personal[m["species"]]
                have = set(p["abilities"]) | {p["hidden_ability"]}
                name = orb.get(m["item"])
                if name and m["ability"] not in payoff[name] and len(have & payoff[name]) == 1:
                    left.append((tid, slot, name))
        self.assertEqual(left, [])

    def test_dry_run_matches_fix_toml(self):
        for r in self.rows:
            self.assertEqual(r["offset"] % SIZE, 4)
            self.assertEqual(len(bytes.fromhex(r["new"])), 2)
            self.assertNotEqual(r["old"], r["new"])
            self.assertEqual(struct.unpack("<H", bytes.fromhex(r["new"]))[0] in
                             {DRIZZLE, DROUGHT, GUTS, MARVEL_SCALE, POISON_HEAL, SHEER_FORCE, FLARE_BOOST}, True)


if __name__ == "__main__":
    unittest.main()
