"""Verify overworld-pokemon-cries: after the fix every stationary overworld Pokemon's PlayCry species is the species that is drawn.

Sprite ids 428.. are following-Pokemon sprites (id = 428 + base offset of data/pokemon_overworld_info.narc, file index = species).
Scripts of objects that move several actors (ApplyMovement, GenderMsgBox) are cutscenes and are not checked, except Route 21 / Lighthouse /
Pokeathlon Potential room (listed in MANUAL: their cutscene script belongs to the object)."""

import re
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
MANUAL = {(225, 1), (225, 2), (286, 3), (93, 15)}     # zone, object: shared cutscene scripts that still hold the object's own cry
SKIP = {(178, 16), (85, 27), (195, 27)}                                     # Victory Road fake-Red scene ; Indigo Plateau Metagross object 27 shares script 25 with the correct Metagross objects (question D-2350)
NOT_THE_OBJECT = {(93, 15): {122}}                     # Mr. Mime's own cry inside the Route 21 script


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
        cls.zones = R.read_json(str(F.WORK / "translate" / "bank_maps.json"))["_zones"]
        cls.C = R.cmds()

    def apply(self):
        store = {"a/0/1/2": self.scripts}
        report = N.apply(store.__getitem__, store.__setitem__, [self.fix])
        self.assertTrue(N.verify(store.__getitem__, report).startswith("ok"))
        return M.Narc.parse(store["a/0/1/2"]).files

    def species_of(self, sprite):
        hit = [i for i, r in enumerate(self.rows) if i and 428 + r[0] == sprite]
        return hit[0] if hit else None

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

    def test_only_species_halfwords_change(self):
        before = M.Narc.parse(self.scripts).files
        after = self.apply()
        diff = sum(x != y for b, a in zip(before, after) for x, y in zip(a, b))
        n = len(self.fix["narc_bytes"])
        self.assertTrue(n <= diff <= 2 * n)
        self.assertTrue(all(len(a) == len(b) for a, b in zip(before, after)))

    def test_cry_follows_drawn_sprite(self):
        after = self.apply()
        checked = bad = 0
        for z in self.zones:
            for o in R.parse_events(self.events[z["events_bank"]])["obj"]:
                key = (z["zone_id"], o["id"])
                if o["sprite"] < 428 or not 1 <= o["script"] < 9000 or key in SKIP:
                    continue
                species = self.species_of(o["sprite"])
                if species is None:
                    continue
                data = bytes(after[z["scripts_bank"]])
                entries, ins = R.disasm(data)
                if o["script"] > len(entries):
                    continue
                names = {self.C[v[0]][0] for v in ins.values()}
                cut = {self.C[ins[p][0]][0] for p in ins}  # whole file; refine per script below
                del names, cut
                flow_ops = set()
                todo, seen = [entries[o["script"] - 1]], set()
                while todo:
                    p = todo.pop()
                    while p in ins and p not in seen:
                        seen.add(p)
                        flow_ops.add(self.C[ins[p][0]][0])
                        if ins[p][3] is not None:
                            todo.append(ins[p][3])
                        if ins[p][0] in R.TERM or (ins[p][0] in R.JUMPS and R.JUMPS[ins[p][0]]):
                            break
                        p = ins[p][2]
                if key not in MANUAL and flow_ops & {"ApplyMovement", "GenderMsgBox"}:
                    continue
                ignore = NOT_THE_OBJECT.get(key, set())
                for c in self.cries(data, o["script"]):
                    if c in ignore:
                        continue
                    checked += 1
                    if c != species:
                        bad += 1
                        self.fail(f"zone {key[0]} object {key[1]} sprite {o['sprite']} draws species {species}, cry {c}")
        self.assertGreater(checked, 40)
        self.assertEqual(bad, 0)

    def test_named_cases(self):
        before = M.Narc.parse(self.scripts).files
        after = self.apply()
        z = next(z for z in self.zones if z["zone_id"] == 475)           # Pewter Pokemon Center: Patrat
        o = next(o for o in R.parse_events(self.events[z["events_bank"]])["obj"] if o["id"] == 5)
        self.assertEqual(self.cries(bytes(before[z["scripts_bank"]]), o["script"]), [39])
        self.assertEqual(self.cries(bytes(after[z["scripts_bank"]]), o["script"]), [504])
        self.assertTrue(re.fullmatch(r"[0-9a-f]{40}", self.fix["narc_bytes"][0]["member_sha1"]))

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
