"""Tests for emu_battle_heal.py (Potion / berry then Roar: health-bar NULL sprite) and its tie to the fix
work/patches/battle-heal-hpbar-switched-out. No emulator is started."""
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_battle_heal as B  # noqa: E402

FIX_ID = 'battle-heal-hpbar-switched-out'
FIX_DIR = Path(__file__).resolve().parent.parent / 'patches' / FIX_ID
ROM_CN = Path(__file__).resolve().parent.parent / 'rom' / 'origin_v4.0.3_cn.nds'


def trial(**kw):
    t = {"delay": 0, "result": "menu", "lead_id": 1, "heals": [{"id": 1, "hp": 20}, {"id": 7, "hp": 28}],
         "lead_dragged_out": False, "lead_bar_ok": True, "skipped_heals": 0, "bars_without_sprite": 0,
         "null_sprite_reads": 0}
    t.update(kw)
    return t


class Judge(unittest.TestCase):
    def test_original_needs_the_null_read(self):
        self.assertEqual(B.failures("original", [trial(bars_without_sprite=1, null_sprite_reads=1)], []), [])
        self.assertTrue(B.failures("original", [trial()], []))

    def test_fixed_needs_a_skipped_heal_and_no_null_read(self):
        self.assertEqual(B.failures("fixed", [trial(skipped_heals=1)], []), [])
        self.assertTrue(B.failures("fixed", [trial()], []))                       # condition not reached
        self.assertTrue(B.failures("fixed", [trial(skipped_heals=1, null_sprite_reads=1)], []))
        self.assertTrue(B.failures("fixed", [trial(skipped_heals=1, bars_without_sprite=1)], []))

    def test_common(self):
        self.assertTrue(B.failures("fixed", [trial(skipped_heals=1, result="stuck")], []))
        self.assertTrue(B.failures("fixed", [trial(skipped_heals=1, heals=[{"id": 7, "hp": 28}])], []))
        self.assertTrue(B.failures("fixed", [trial(skipped_heals=1, lead_bar_ok=False)], []))
        self.assertTrue(B.failures("fixed", [trial(skipped_heals=1)], ["boom"]))
        self.assertTrue(B.failures("fixed", [], []))


class Hooks(unittest.TestCase):
    def machine(self, **regs):
        mem = {B.GAUGE_SPRITE_LOAD: B.GAUGE_SPRITE_LOAD_OP}
        return SimpleNamespace(frame=5, reg=SimpleNamespace(**{"r0": 0, "r1": 0, "r2": 0, "lr": 0, **regs}),
                               u16=lambda a: mem[a], u32=lambda a: 0)

    def test_heal_only_from_the_handler(self):
        t = B.Trace()
        t.active = True
        t.heal(self.machine(r1=7, r2=28, lr=B.HEAL_CMD_RETURN))
        t.heal(self.machine(r1=3, r2=1, lr=0x02000001))
        self.assertEqual(t.heals, [{"frame": 5, "id": 7, "hp": 28}])

    def test_bar_and_null_read(self):
        t = B.Trace()
        t.active = True
        t.task(self.machine(r1=0x022C147C))
        t.gauge(self.machine(r0=0))
        t.gauge(self.machine(r0=0x022E58DC))
        self.assertEqual(t.bars, {0x022C147C: {"frame": 5, "sprite": 0}})
        self.assertEqual(t.null_reads, 1)


class TiedToFix(unittest.TestCase):
    def test_fix_regions_match_the_constants(self):
        text = (FIX_DIR / 'fix.toml').read_text()
        caller = re.search(r'offset = "0x4C08"\nexpect = "0x6A98"', text)
        self.assertIsNotNone(caller)
        self.assertEqual(B.CALLER_ORIGINAL, bytes.fromhex("986a"))
        m = re.search(r'offset = "0x2D844"\nexpect = "([0-9A-F ]+)"', text)
        halfwords = bytes.fromhex(''.join(h[2:] + h[:2] for h in m.group(1).split()))
        self.assertEqual(halfwords, B.ROUTINE_ORIGINAL)
        self.assertEqual(B.BAR_ROUTINE - B.OV14_BASE, 0x2D844)
        self.assertEqual(B.CALLER_EDIT - B.OV14_BASE, 0x4C08)

    def test_listing_new_bytes(self):
        listing = (FIX_DIR / f'{FIX_ID}.listing').read_text()
        new = [ln for ln in listing.splitlines() if ln.startswith('+ 0222E') or ln.startswith('+ 0222D')]
        data = b''.join(bytes.fromhex(''.join(h[2:] + h[:2] for h in ln.split()[2:4] if re.fullmatch('[0-9A-F]{4}', h)))
                        for ln in new)
        self.assertEqual(data[:len(B.ROUTINE_FIXED)], B.ROUTINE_FIXED)
        self.assertIn('+ 022053E8  0E08', listing)

    def test_refuses_existing_report(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'report.json').write_text('{}')
            args = SimpleNamespace(rom=__file__, sav=__file__, out=d, expect='fixed', delays='0')
            with self.assertRaises(ValueError):
                B.run(args)

    @unittest.skipUnless(ROM_CN.exists(), 'needs the Chinese ROM')
    def test_chinese_rom_is_original(self):
        B.validate_rom(ROM_CN, 'original')
        with self.assertRaises(ValueError):
            B.validate_rom(ROM_CN, 'fixed')


class PartyFixture(unittest.TestCase):
    def test_half_hp_preserves_boxed_data_and_checksums_for_every_shuffle(self):
        import emu_harness as E
        from test_emu_harness import _encrypted_mon
        for seed in range(32):
            raw = _encrypted_mon(seed=seed, party=True)
            state = {"raw": raw}
            h = SimpleNamespace(array=lambda _id: 0, read=lambda _a, _n: state["raw"],
                                write=lambda _a, data: state.update(raw=data))
            B.set_party_hp(h, 0, 0.5)
            after = E.decode_party_pokemon(state["raw"])
            self.assertEqual(state["raw"][:136], raw[:136])
            self.assertEqual(after["hp"], 10)
            self.assertEqual(after["stats"], E.decode_party_pokemon(raw)["stats"])
            self.assertTrue(after["checksum_ok"])


if __name__ == '__main__':
    unittest.main()
