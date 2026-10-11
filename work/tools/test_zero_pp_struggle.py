"""Execute the assembled zero-PP command guard, including its native constructor.

Local CN ROM and armips v0.11.0 are required. External actor helpers are adversarial
ABI stubs; this tests branch behavior, writes, precedence and caller preservation.
"""

from pathlib import Path
import itertools
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import asmpatch
import fixes
import hardcoded
import msgtool
import double_target_thumb_model as model

BASE = 0x022007E0
GUARD = 0x0222C550
FIGHT_RETURN = 0x02202F81
ACTOR, RECORD = 0x02300000, 0x02301000
ROM = Path(__file__).resolve().parents[1] / "rom/origin_v4.0.3_cn.nds"


class CPU(model.CPU):
    def __init__(self, code, *, dead=False, flags=(), stored=(), target=13, number=1):
        super().__init__(code, 0)
        self.dead, self.flags, self.stored = dead, flags, stored
        self.target, self.number = target, number

    def step(self, ins, pc):
        if ins.mnemonic == "ldm":
            regs = [self.regnum(o.reg) for o in ins.operands]
            base = self.r[regs[0]]
            for i, reg in enumerate(regs[1:]):
                self.r[reg] = self.r32(base + i * 4)
            self.r[regs[0]] = base + 4 * (len(regs) - 1)
            return pc + 2
        if ins.mnemonic in ("bics", "tst"):
            lhs, rhs = (self.val(o) for o in ins.operands)
            value = lhs & (~rhs if ins.mnemonic == "bics" else rhs)
            if ins.mnemonic == "bics":
                self.r[self.regnum(ins.operands[0].reg)] = value & 0xFFFFFFFF
            self.flags_nz(value)
            return pc + 2
        if ins.mnemonic == "mul":
            raise AssertionError("unexpected multiplication")
        return super().step(ins, pc)

    def run(self, ret, record=RECORD):
        self.r[:2] = [ACTOR, record]
        saved = [0xA5000000 + i for i in range(4, 8)]
        self.r[4:8] = saved
        self.r[13], self.r[14], pc = self.stack_top, ret, GUARD
        for _ in range(2000):
            if pc == (ret & ~1):
                assert self.r[4:8] == saved and self.r[13] == self.stack_top
                return self.r[0]
            args = self.r[:4]
            result = None
            if pc == 0x02216538:
                result = int(self.dead)
            elif pc == 0x02217104:
                result = int(args[1] in self.flags)
            elif pc == 0x02216D28:
                result = int(args[1] in self.stored)
            elif pc == 0x022167A0:
                result = self.number
            elif pc == 0x02217B10:
                result = self.target
            elif pc == 0x02216F54:
                result = 247
            elif pc == 0x02216D3C:
                self.w32(args[0], 0x11223344)
                self.w32(args[0] + 4, 0x55667788)
                result = 0
            elif pc == 0x02216D70:
                assert args[:2] == [0x11223344, 0x55667788]
                result = 101
            if result is not None:
                self.calls.append(hex(pc))
                self.clobber_callers()
                self.r[0] = result
                pc = self.r[14] & ~1
                continue
            ins = next(model.md.disasm(self.ov[pc - BASE : pc - BASE + 4], pc, 1))
            pc = self.step(ins, pc)
        raise AssertionError("guard did not return")

    def slots(self, moves, pp):
        for i, (move, p) in enumerate(zip(moves, pp)):
            self.w8(ACTOR + 0x25A + 18 * i, move & 255)
            self.w8(ACTOR + 0x25B + 18 * i, move >> 8)
            self.w8(ACTOR + 0x25C + 18 * i, p)
        for i in range(12):
            self.w8(RECORD + i, 0xA7)


try:
    ARMIPS = asmpatch.find_armips()
    asmpatch.check_armips(ARMIPS)
except asmpatch.AsmError:
    ARMIPS = None


@unittest.skipUnless(ROM.exists() and ARMIPS, "needs local CN ROM and armips v0.11.0")
class StruggleGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = hardcoded.RomView(msgtool.load_rom(str(ROM))).get("overlay14")
        cls.fix = next(f for f in fixes.load_all() if f["id"] == "zero-pp-struggle")
        armips = ARMIPS
        asmpatch.check_armips(armips)
        images, _, _ = asmpatch.assemble([cls.fix], {"overlay14": cls.native}, armips)
        cls.patched = images["overlay14"]

    def test_all_slot_presence_and_pp_masks(self):
        for presence, available in itertools.product(range(16), repeat=2):
            moves = [122 if presence & (1 << i) else 0 for i in range(4)]
            pp = [1 if available & (1 << i) else 0 for i in range(4)]
            cpu = CPU(self.patched)
            cpu.slots(moves, pp)
            before = cpu.r32(RECORD)
            result = cpu.run(FIGHT_RETURN)
            self.assertEqual(result, int(not (presence & available)))
            if result:
                self.assertEqual((cpu.r32(RECORD) >> 8) & 0xFFFF, 165)
                self.assertEqual((cpu.r32(RECORD) >> 4) & 15, 13)
                self.assertEqual(cpu.r32(RECORD + 4), 0)
                self.assertEqual(cpu.r32(RECORD + 8), 1)
            else:
                self.assertEqual(cpu.r32(RECORD), before)

    def test_other_callers_do_not_force_struggle(self):
        for ret in (0x022021A7, 0x0220220B, 0x0222FFFF):
            cpu = CPU(self.patched)
            cpu.slots([122, 0, 0, 0], [0] * 4)
            self.assertEqual(cpu.run(ret), 0)
            self.assertEqual(cpu.r32(RECORD), 0xA7A7A7A7)

    def test_existing_precedence_matches_native(self):
        for dead, flags, stored, record in itertools.product(
            (False, True), ((), (1,), (4,), (1, 4)), ((), (26,), (27,), (26, 27)), (0, RECORD)
        ):
            outputs = []
            for code in (self.native, self.patched):
                cpu = CPU(code, dead=dead, flags=flags, stored=stored)
                cpu.slots([122] * 4, [1] * 4)
                outputs.append((cpu.run(FIGHT_RETURN, record), [cpu.r32(RECORD + i) for i in (0, 4, 8)]))
            self.assertEqual(outputs[0], outputs[1], (dead, flags, stored, record))

    def test_guards_reject_changed_input(self):
        bad = bytearray(self.native)
        bad[0x2BD70] ^= 1
        with self.assertRaises(asmpatch.AsmError):
            asmpatch.assemble([self.fix], {"overlay14": bytes(bad)}, ARMIPS)


if __name__ == "__main__":
    unittest.main()
