"""Execute approved target-navigation machine code against exhaustive masks (local CN ROM required).

DOUBLE_TARGET_CN_ROM overrides work/rom/origin_v4.0.3_cn.nds.
Run with the project venv, which supplies capstone and ndspy; set ARMIPS to local v0.11.0.
"""
import os
from pathlib import Path
import sys
import struct
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hardcoded
import msgtool
import asmpatch
import fixes
import hashlib
import double_target_thumb_model as model

ROM = Path(os.environ.get('DOUBLE_TARGET_CN_ROM', str(Path(__file__).resolve().parents[1] / 'rom/origin_v4.0.3_cn.nds')))
try:
    ARMIPS = asmpatch.find_armips()
    asmpatch.check_armips(ARMIPS)
except asmpatch.AsmError:
    ARMIPS = None

G = model.G
FIRST, FOE, ENTRY, NAV = 0x02212784, 0x02212788, 0x022127AA, 0x022127B8
DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0)]
GRID = [3, 1, 0, 2, 4, 4]


def expected_replacement_regions():
    """Independent Thumb encoding of the reviewed design (no armips output/listing read).

    Nonbranch halfwords use ARM Thumb-1 instruction fields; branch displacement and PC-relative
    literal loads are calculated here from labels. This is the source for intentionally updated
    digest and overlay golden pins, rather than re-pinning whatever the assembler produces.
    """
    words, labels, relocations = [], {}, []
    def label(name): labels[name] = FIRST + 2 * len(words)
    def emit(*values): words.extend(values)
    def branch(target, condition=None):
        relocations.append((len(words), 'b', target, condition)); emit(0)
    def bl(target):
        relocations.append((len(words), 'bl', target, None)); emit(0, 0)
    def literal(register, target):
        relocations.append((len(words), 'ldr', target, register)); emit(0)

    label('first'); emit(0x21E4); branch('scan')              # mov r1,#E4; b scan
    label('foe'); emit(0x2187)                              # mov r1,#87
    label('scan'); emit(0xB51C, 0x1C0C, 0x4669, 0x2201)     # push r2-r4,lr; r4=r1; r1=sp; r2=1
    bl(model.MASK)
    label('next'); emit(0x2003, 0x4020, 0x4669, 0x5C09, 0x2901)
    branch('first_done', 0); emit(0x08A4); branch('next', 1); emit(0x2004)
    label('first_done'); emit(0xBD1C)
    label('entry'); literal(1, 'global'); emit(0x694A, 0x0852)  # target load; LSR sets carry from odd bit
    branch('repair', 2); emit(0x2205, 0x614A)
    label('repair'); branch(model.REPAIR)
    label('nav'); emit(0xB5F8, 0x1C06, 0x1C0F, 0x0055)
    literal(0, 'global'); emit(0x6840, 0x21FB, 0x0089, 0x5840, 0x4669, 0x2201)
    bl(model.MASK); literal(3, 'grid'); emit(0x2405)
    label('find'); emit(0x5D18, 0x42B0); branch('found', 0); emit(0x3C01); branch('find', 1)
    label('found'); emit(0x1C22)
    label('advance'); emit(0x2001, 0x4020, 0x19C0, 0x2801); branch('edge', 8)
    emit(0x19E4, 0x1964, 0x2C05); branch('edge', 8)
    emit(0x5D18, 0x2804); branch('done', 0); emit(0x4669, 0x5C09, 0x2901); branch('done', 0)
    emit(0x2F00); branch('advance', 0); emit(0x2002); branch('retry')
    label('edge'); emit(0x2F00); branch('stay', 1); emit(0x2001)
    label('retry'); emit(0x2A08); branch('stay', 2); emit(0x4042, 0x1C14, 0x2208); branch('advance')
    label('stay'); emit(0x1C30)
    label('done'); emit(0xBDF8)
    assert len(words) % 2 == 0, 'literal pool alignment'
    label('global'); emit(model.G & 0xFFFF, model.G >> 16)
    label('grid'); emit(0xCD44, 0x0224)
    for index, operation, target, parameter in relocations:
        address = FIRST + 2 * index
        target = labels[target] if isinstance(target, str) else target
        delta = target - (address + 4)
        if operation == 'bl':
            words[index:index + 2] = [0xF000 | ((delta >> 12) & 0x7FF),
                                    0xF800 | ((delta >> 1) & 0x7FF)]
        elif operation == 'ldr':
            offset = target - ((address + 4) & ~3)
            assert offset % 4 == 0 and 0 <= offset < 1024
            words[index] = 0x4800 | (parameter << 8) | (offset // 4)
        else:
            assert delta % 2 == 0
            words[index] = ((0xE000 | ((delta // 2) & 0x7FF)) if parameter is None else
                            (0xD000 | (parameter << 8) | ((delta // 2) & 0xFF)))
    assert len(words) == 82 and labels['entry'] == ENTRY and labels['nav'] == NAV
    def encode_bl(address, target):
        delta = target - address - 4
        return struct.pack('<HH', 0xF000 | ((delta >> 12) & 0x7FF), 0xF800 | ((delta >> 1) & 0x7FF))
    return {
        0x11FA4: struct.pack('<82H', *words),
        **{address - model.OVB: encode_bl(address, NAV)
           for address in (0x02212880, 0x02212896, 0x022128AE, 0x022128C4)},
        0x11DB6: encode_bl(0x02212596, ENTRY),
        0x1224C: encode_bl(0x02212A2C, FOE),
        0x1223A: struct.pack('<4H', 0x2C04, 0xD00A, 0xD804, 0x46C0),
    }


def first(mask, spread=False):
    return next((s for s in (range(4) if spread else (3, 1, 0, 2)) if mask & (1 << s)), 4)


def nav(mask, cur, dx, dy, retry, horizontal_retry=False):
    start = max(i for i, s in enumerate(GRID) if s == cur)
    if dx:
        x, y = start % 2 + dx, start // 2
        if not 0 <= x < 2:  # outward edge, including CANCEL: unchanged
            return cur
        adjacent = GRID[2 * y + x]
        if adjacent == 4 or mask & (1 << adjacent):
            return adjacent
        if horizontal_retry:
            diagonal = GRID[2 * (y ^ 1) + x]  # ineligible neighbor proves y is a Pokemon row
            if mask & (1 << diagonal):
                return diagonal
        return cur
    for idx in ([start, start ^ 1] if retry and dx == 0 else [start]):
        x, y = idx % 2, idx // 2
        while True:
            x, y = x + dx, y + dy
            if not (0 <= x < 2 and 0 <= y < 3):
                break
            s = GRID[2 * y + x]
            if s == 4 or mask & (1 << s):
                return s
    return cur


@unittest.skipUnless(ROM.exists() and ARMIPS, 'needs local CN ROM and armips v0.11.0')
class TargetCodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = hardcoded.RomView(msgtool.load_rom(str(ROM))).get('overlay14')
        cls.fix = next(f for f in fixes.load_all() if f['id'] == 'double-battle-targeting')
        images, _, _ = asmpatch.assemble([cls.fix], {'overlay14': cls.native}, ARMIPS)
        cls.patched = images['overlay14']

    def test_approved_horizontal_fallback_patch_digest(self):
        digest = hashlib.sha256()
        expected = expected_replacement_regions()
        independently_patched = bytearray(self.native)
        for offset, blob in expected.items():
            independently_patched[offset:offset + len(blob)] = blob
        self.assertEqual(self.patched, bytes(independently_patched))
        for entry in self.fix['code']:
            offset = int(entry['offset'], 16)
            size = 2 * len(fixes.halfwords(entry['expect']))
            digest.update(self.patched[offset:offset + size])
            self.assertEqual(self.patched[offset:offset + size], expected[offset])
        self.assertEqual(digest.hexdigest(), "259a43fbdd573c8f7eb6d754af01dcbd13438d7a56ffd6233466e92085bc1914")

    def call(self, addr, mask, *args, target=0, spread=0, native=False):
        cpu = model.CPU(self.native if native else self.patched, mask, spread, target)
        saved = [0xA5000000 + n for n in range(4, 8)]
        cpu.r[4:8] = saved
        result = cpu.call(addr, *args)
        self.assertEqual(cpu.r[4:8], saved, 'callee-saved registers')
        self.assertEqual(cpu.r[13], cpu.stack_top, 'stack balance')
        return result, cpu.r32(G + 0x14)

    def test_native_and_foe_orders_all_masks(self):
        for mask in range(16):
            original = self.call(FIRST, mask, 0x02310000, native=True)[0]
            self.assertEqual(original, first(mask, True))
            self.assertEqual(self.call(FIRST, mask, 0x02310000)[0], original)
            self.assertEqual(self.call(FOE, mask, 0x02310000)[0], first(mask))

    def test_vertical_navigation_160_cases_unchanged_from_option2(self):
        changed = 0
        for mask in range(16):
            for cur in range(5):
                for dx, dy in DIRS[:2]:
                    old = self.call(0x022127A4, mask, cur, dx, dy, native=True)[0]
                    new = self.call(NAV, mask, cur, dx, dy)[0]
                    self.assertEqual(old, nav(mask, cur, dx, dy, False))
                    self.assertEqual(new, nav(mask, cur, dx, dy, True))
                    if old != new:
                        changed += 1
                        self.assertEqual(old, cur)
                        self.assertEqual(dx, 0)
        self.assertEqual(changed, 11)

    def test_horizontal_navigation_160_exact_transitions(self):
        changed = 0
        for mask in range(16):
            for cur in range(5):
                for dx, dy in DIRS[2:]:
                    with self.subTest(mask=mask, cur=cur, dx=dx):
                        old = self.call(0x022127A4, mask, cur, dx, dy, native=True)[0]
                        new = self.call(NAV, mask, cur, dx, dy)[0]
                        self.assertEqual(old, nav(mask, cur, dx, dy, False))
                        self.assertEqual(new, nav(mask, cur, dx, dy, True, True))
                        if new != old:
                            changed += 1
                            index = max(i for i, s in enumerate(GRID) if s == cur)
                            self.assertLess(cur, 4, 'CANCEL horizontal behavior stays native')
                            self.assertTrue(0 <= index % 2 + dx < 2, 'outward edges stay native')
                            neighbor = GRID[index + dx]
                            self.assertFalse(mask & (1 << neighbor), 'only ineligible neighbors retry')
                            self.assertEqual(new, GRID[(index ^ 2) + dx])
        self.assertEqual(changed, 16)

    def test_all_eligible_slots_and_cancel_reachable_from_every_eligible_start(self):
        # Exhaust arbitrary eligibility subsets, not just normal foe-target masks. A graph check catches
        # the mask 0b0011 trap that individual legal-output checks did not detect in historical Option 2.
        starts = 0
        for mask in range(16):
            vertices = {4} | {slot for slot in range(4) if mask & (1 << slot)}
            edges = {slot: {self.call(NAV, mask, slot, dx, dy)[0] for dx, dy in DIRS}
                     for slot in vertices}
            for start in vertices:
                reached, pending = {start}, [start]
                while pending:
                    for neighbor in edges[pending.pop()]:
                        self.assertIn(neighbor, vertices, 'navigation never selects an ineligible slot')
                        if neighbor not in reached:
                            reached.add(neighbor)
                            pending.append(neighbor)
                self.assertEqual(reached, vertices, f'mask={mask:04b}, start={start}')
                starts += 1
        self.assertEqual(starts, 48)

    def test_missing_left_foe_mode9_graph_regression(self):
        # Presence mask 7 produces eligibility [1,1,0,0] in this mode: entry foe 1 -> ally 0 via Left.
        self.assertEqual(self.call(ENTRY, 3, 0x02310000, target=0)[1], 1)
        self.assertEqual(self.call(NAV, 3, 1, -1, 0)[0], 0)
        self.assertEqual(self.call(NAV, 3, 0, 1, 0)[0], 1)

    def test_repair_256_cases(self):
        for mask in range(16):
            for target in [0, 1, 2, 3, 4, 5, 0xFFFFFFFF, 0x80000000]:
                for spread in (0, 1):
                    want = first(mask, spread)
                    if target == 4 or (not spread and target < 4 and mask & (1 << target)):
                        want = target
                    self.assertEqual(self.call(model.REPAIR, mask, 0x02310000, target=target, spread=spread)[1], want)

    def test_entry_416_cases_including_unsigned_boundaries(self):
        for mask in range(16):
            for target in [0, 1, 2, 3, 4, 5, 7, 0x7FFFFFFF, 0x80000000, 0x80000001,
                           0xFFFFFFFE, 0xFFFFFFFF, 0xFFFFFFFD]:
                for spread in (0, 1):
                    want = first(mask, spread)
                    if not spread and target in (1, 3) and mask & (1 << target):
                        want = target
                    self.assertEqual(self.call(ENTRY, mask, 0x02310000, target=target, spread=spread)[1], want)

    def test_spread_call_sites_unchanged(self):
        for addr in (0x0221262E, 0x02212866, 0x022128FC, 0x02212958, 0x02212A06):
            off = addr - model.OVB
            self.assertEqual(self.patched[off:off + 4], self.native[off:off + 4])

if __name__ == '__main__':
    unittest.main()
