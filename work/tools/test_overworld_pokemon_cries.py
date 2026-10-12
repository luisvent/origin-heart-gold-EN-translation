"""Verify overworld-pokemon-cries: the cry of 29 stationary overworld Pokemon is the species they are labelled and drawn as.

Sprite ids 428.. are following-Pokemon sprites (id = 428 + base offset of data/pokemon_overworld_info.narc, file index = species).
In scope: objects whose Chinese speaker label (or nickname) and drawn sprite agree but whose PlayCry plays another species (user decision
2026-10-12, D-2398). Out of scope and asserted unchanged: Kirk's Sylveon, the S.S. Aqua Bulbasaur, Viridian Doduo, Pokeathlon Pidgey, the
Route 21 Lairon (open questions D-2399 / D-2400)."""

import struct
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "docs")]
import fixes as F
import msgtool as M
import narcpatch as N
import romdata as R

FIX = "overworld-pokemon-cries"
IN_SCOPE = [(14, 17),
    (30, 11),
    (36, 2),
    (45, 5),
    (45, 7),
    (50, 14),
    (75, 10),
    (75, 21),
    (81, 11),
    (84, 14),
    (177, 23),
    (177, 33),
    (177, 34),
    (177, 35),
    (178, 16),
    (196, 17),
    (236, 8),
    (362, 9),
    (372, 8),
    (379, 2),
    (404, 2),
    (427, 10),
    (427, 38),
    (429, 9),
    (492, 12),
    (492, 14),
    (492, 16),
    (503, 2),
    (503, 15)]   # (zone, object)
OUT_OF_SCOPE = [(232, 8), (328, 28), (50, 20), (280, 10), (93, 15)]


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class OverworldPokemonCriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = M.load_rom(F.ROM_CN)
        cls.scripts = M.get_file(rom, "a/0/1/2")
        cls.events = M.Narc.parse(M.get_file(rom, "a/0/3/2")).files
        table = M.Narc.parse(M.get_file(rom, "data/pokemon_overworld_info.narc")).files
        cls.rows = [struct.unpack("<3H", f) for f in table]
        cls.fix = next(f for f in F.load_all() if f["id"] == FIX)
        cls.zones = {z["zone_id"]: z for z in R.read_json(str(F.WORK / "translate" / "bank_maps.json"))["_zones"]}
        cls.C = R.cmds()

    def apply(self):
        store = {"a/0/1/2": self.scripts}
        report = N.apply(store.__getitem__, store.__setitem__, [self.fix])
        self.assertTrue(N.verify(store.__getitem__, report).startswith("ok"))
        return M.Narc.parse(store["a/0/1/2"]).files

    def species_of(self, sprite):
        for i, r in enumerate(self.rows):
            if i and sprite in (428 + r[0], 428 + r[1] if r[1] else -1):
                return i
        forms = sorted((r[2], i) for i, r in enumerate(self.rows) if r[2])     # alternative forms (Unown letters ...)
        base, species = max(f for f in forms if f[0] <= sprite - 428)
        self.assertLess(sprite - 428 - base, 60)
        return species

    def obj(self, zone, oid):
        z = self.zones[zone]
        return z, next(o for o in R.parse_events(self.events[z["events_bank"]])["obj"] if o["id"] == oid)

    def cries(self, data, script_id):
        entries, ins = R.disasm(data)
        known = R.const_prop(entries, ins)
        todo, seen, out = [entries[script_id - 1]], set(), []
        while todo:
            p = todo.pop()
            while p in ins and p not in seen:
                seen.add(p)
                op, a, n, t = ins[p]
                if self.C[op][0] == "PlayCry":
                    v = R.val(a[0], known.get(p, {}))
                    if a[0] < 0x4000 and v is not None:
                        out.append(v & 0x7FF)
                if t is not None:
                    todo.append(t)
                if op in R.TERM or (op in R.JUMPS and R.JUMPS[op]):
                    break
                p = n
        return out

    def test_fix_is_disabled_and_has_no_text(self):
        self.assertFalse(self.fix["enabled"])  # switched off at merge (Status paragraph in fix.toml)
        self.assertNotIn("string", self.fix)
        self.assertEqual(len(self.fix["narc_bytes"]), 23)

    def test_only_species_halfwords_change(self):
        before = M.Narc.parse(self.scripts).files
        after = self.apply()
        diff = sum(x != y for b, a in zip(before, after) for x, y in zip(a, b))
        self.assertTrue(23 <= diff <= 46)
        self.assertTrue(all(len(a) == len(b) for a, b in zip(before, after)))

    def test_in_scope_cry_is_the_drawn_species(self):
        before = M.Narc.parse(self.scripts).files
        after = self.apply()
        for zone, oid in IN_SCOPE:
            z, o = self.obj(zone, oid)
            species = self.species_of(o["sprite"])
            old = self.cries(bytes(before[z["scripts_bank"]]), o["script"])
            new = self.cries(bytes(after[z["scripts_bank"]]), o["script"])
            self.assertTrue(new and all(c == species for c in new), (zone, oid, species, new))
            self.assertTrue(any(c != species for c in old), (zone, oid, old))

    def test_out_of_scope_cries_unchanged(self):
        before = M.Narc.parse(self.scripts).files
        after = self.apply()
        for zone, oid in OUT_OF_SCOPE:
            z, o = self.obj(zone, oid)
            self.assertEqual(self.cries(bytes(before[z["scripts_bank"]]), o["script"]),
                             self.cries(bytes(after[z["scripts_bank"]]), o["script"]), (zone, oid))

    def test_named_cases(self):
        before = M.Narc.parse(self.scripts).files
        after = self.apply()
        for zone, oid, old, new in ((429, 9, 791, 507), (404, 2, 820, 536), (178, 16, 9, 3), (81, 11, 157, 156)):
            z, o = self.obj(zone, oid)
            self.assertEqual(self.cries(bytes(before[z["scripts_bank"]]), o["script"])[0], old)
            self.assertEqual(self.cries(bytes(after[z["scripts_bank"]]), o["script"])[0], new)

    def test_guards_reject_changed_source(self):
        files = M.Narc.parse(self.scripts).files
        e = self.fix["narc_bytes"][0]
        bad = bytearray(files[e["member"]])
        bad[int(e["offset"], 16)] ^= 1
        files[e["member"]] = bytes(bad)
        store = {"a/0/1/2": M.Narc(files).build()}
        original = store["a/0/1/2"]
        with self.assertRaises(N.NarcPatchError):
            N.apply(store.__getitem__, store.__setitem__, [self.fix])
        self.assertEqual(store["a/0/1/2"], original)


if __name__ == "__main__":
    unittest.main()
