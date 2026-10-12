"""Verify overworld-pokemon-sprites: stationary overworld Pokemon get the sprite of their own species.

Sprite ids 428.. are the hack's following-Pokemon sprites: id = 428 + the species' base offset in
data/pokemon_overworld_info.narc (file index = species, first u16 = offset). Ids 994..1046 are vanilla's NPC-Pokemon sprites,
which that table redefined as Generation 5 species (1004 = Patrat, 1031 = Audino)."""

import struct
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "docs")]
import fixes as F
import msgtool as M
import narcpatch as N

FIX = "overworld-pokemon-sprites"
# (events member, object id) -> species (national dex) the object is, from its own message speaker / PlayCry
EXPECT = {
    (428, 5): 39,      # Pewter Pokemon Center, "Jigglypuff: Buli, buli!"
    (179, 2): 39,      # Goldenrod Radio Tower 2F, Jigglypuff
    (211, 1): 181, (211, 2): 181,     # Olivine Lighthouse, "Amphy: Ammm-pha!"
    (193, 1): 67, (193, 2): 67, (193, 3): 67,   # Department Store basement Machoke
    (240, 8): 25, (240, 9): 25,       # Battle Tower Pikachu
    (299, 28): 1,                     # S.S. Aqua Bulbasaur (label and sound say Bulbasaur; cry disagrees: needs user check)
    (218, 8): 700,                    # Kirk's Sylveon (label wins over the Lumineon cry: needs user check)
    (477, 0): 382,                    # Embedded Tower Kyogre
    (82, 27): 376, (188, 27): 376,    # second Metagross object, same script as the 837 ones
}
VANILLA_BLOCK = range(994, 1047)
# Herdier / Palpitoad: the hack's own choices (their ids are those species' follower ids); the silent objects have no Chinese text or
# cry that proves the vanilla species (Moomoo Farm 1035, Mount Moon Clefairy event 1003, Pokeathlon Poliwrath 1011): not changed.
KEPT = {(384, 9): 1007, (361, 2): 1036, (251, 1): 1011, (253, 1): 1011}
KEPT.update({(201, i): 1035 for i in (1, 3, 4, 5, 6)})
KEPT.update({(465, i): 1003 for i in range(6)})


def objects(member: bytes):
    nb = struct.unpack_from("<I", member, 0)[0]
    p = 4 + 20 * nb
    no = struct.unpack_from("<I", member, p)[0]
    return [struct.unpack_from("<HH", member, p + 4 + 32 * i) for i in range(no)]


@unittest.skipUnless(F.ROM_CN.exists(), "needs local Chinese ROM")
class OverworldPokemonSpritesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = M.load_rom(F.ROM_CN)
        cls.archive = M.get_file(rom, "a/0/3/2")
        table = M.Narc.parse(M.get_file(rom, "data/pokemon_overworld_info.narc")).files
        cls.base = {i: struct.unpack_from("<H", f, 0)[0] for i, f in enumerate(table) if i}
        cls.fix = next(f for f in F.load_all() if f["id"] == FIX)

    def apply(self):
        store = {"a/0/3/2": self.archive}
        report = N.apply(store.__getitem__, store.__setitem__, [self.fix])
        self.assertTrue(N.verify(store.__getitem__, report).startswith("ok"))
        return M.Narc.parse(store["a/0/3/2"]).files

    def follower_sprite(self, species):
        return 428 + self.base[species]

    def test_only_sprite_ids_change(self):
        before = M.Narc.parse(self.archive).files
        after = self.apply()
        n_entries = len(self.fix["narc_bytes"])
        diff = 0
        for b, a in zip(before, after):
            self.assertEqual(len(a), len(b))
            diff += sum(x != y for x, y in zip(a, b))
            for (ib, sb), (ia, sa) in zip(objects(b), objects(a)):
                self.assertEqual(ib, ia)
        self.assertGreaterEqual(diff, n_entries)           # each entry changes at least one byte of its u16
        self.assertLessEqual(diff, 2 * n_entries)

    def test_named_objects_draw_their_species(self):
        before = M.Narc.parse(self.archive).files
        after = self.apply()
        for (member, oid), species in EXPECT.items():
            self.assertNotEqual(objects(before[member])[oid][1], self.follower_sprite(species), (member, oid))
            self.assertEqual(objects(after[member])[oid][1], self.follower_sprite(species), (member, oid))

    def test_pewter_and_lighthouse_regression(self):
        before = M.Narc.parse(self.archive).files
        after = self.apply()
        self.assertEqual(objects(before[428])[5][1], 1004)     # Patrat on the Chinese ROM
        self.assertEqual(objects(after[428])[5][1], 468)       # Jigglypuff
        self.assertEqual(objects(before[211])[1][1], 1031)     # Audino
        self.assertEqual(objects(after[211])[1][1], 612)       # Ampharos

    def test_no_vanilla_pokemon_id_left_except_the_hacks_own(self):
        after = self.apply()
        left = {}
        for member, f in enumerate(after):
            try:
                objs = objects(f)
            except struct.error:
                continue
            for oid, sprite in objs:
                if sprite in VANILLA_BLOCK:
                    left[(member, oid)] = sprite
        self.assertEqual(left, KEPT)

    def test_guards_reject_changed_source(self):
        files = M.Narc.parse(self.archive).files
        e = self.fix["narc_bytes"][0]
        bad = bytearray(files[e["member"]])
        bad[int(e["offset"], 16)] ^= 1
        files[e["member"]] = bytes(bad)
        store = {"a/0/3/2": M.Narc(files).build()}
        original = store["a/0/3/2"]
        with self.assertRaises(N.NarcPatchError):
            N.apply(store.__getitem__, store.__setitem__, [self.fix])
        self.assertEqual(store["a/0/3/2"], original)


if __name__ == "__main__":
    unittest.main()
