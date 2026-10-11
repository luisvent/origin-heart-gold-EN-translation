"""Bounded Thumb runner for the assembled post-battle collector regression.

Adapted from this project's targeting runner. Native data/Bag/PRNG helpers are
stubbed by test_honey_gather; this is not an emulator or a gameplay replay.
"""

import capstone
from capstone import arm as A

OVB = 0x022007E0
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = True


class Thumb:
    def __init__(self, ov):
        self.ov = ov
        self.r = [0] * 16
        self.mem = {}
        self.stack_top = 0x027E0000
        self.N = self.Z = self.C = self.V = False
        self.calls = []

    def r8(self, a):
        if OVB <= a < OVB + len(self.ov):
            return self.ov[a - OVB]
        return self.mem.get(a, 0)

    def w8(self, a, v):
        self.mem[a] = v & 0xFF

    def r32(self, a):
        return sum(self.r8(a + i) << (8 * i) for i in range(4))

    def w32(self, a, v):
        for i in range(4):
            self.w8(a + i, (v >> (8 * i)) & 0xFF)

    def flags_sub(self, a, b):
        res = (a - b) & 0xFFFFFFFF
        self.N, self.Z = bool(res >> 31), res == 0
        self.C = a >= b
        self.V = bool(((a ^ b) & (a ^ res)) >> 31)
        return res

    def flags_nz(self, res):
        res &= 0xFFFFFFFF
        self.N, self.Z = bool(res >> 31), res == 0
        return res

    def cond(self, cc):
        return {
            A.ARM_CC_EQ: self.Z,
            A.ARM_CC_NE: not self.Z,
            A.ARM_CC_HS: self.C,
            A.ARM_CC_LO: not self.C,
            A.ARM_CC_MI: self.N,
            A.ARM_CC_PL: not self.N,
            A.ARM_CC_HI: self.C and not self.Z,
            A.ARM_CC_LS: (not self.C) or self.Z,
            A.ARM_CC_GE: self.N == self.V,
            A.ARM_CC_LT: self.N != self.V,
            A.ARM_CC_GT: (not self.Z) and self.N == self.V,
            A.ARM_CC_LE: self.Z or self.N != self.V,
            A.ARM_CC_AL: True,
            A.ARM_CC_INVALID: True,
        }[cc]

    def clobber_callers(self):
        """External stubs must not accidentally preserve volatile registers or flags."""
        self.r[0:4] = [0xDEADBEEF, 0xBAADF00D, 0xCAFEBABE, 0xFEEDFACE]
        self.r[12] = 0xABADBABE
        self.N, self.Z, self.C, self.V = True, False, True, True

    def val(self, op):
        return self.r[self.regnum(op.reg)] if op.type == A.ARM_OP_REG else op.imm & 0xFFFFFFFF

    def addr(self, op, pc):
        m = op.mem
        base = (
            ((pc + 4) & ~3)
            if m.base == A.ARM_REG_PC
            else self.r[m.base - A.ARM_REG_R0]
            if m.base != A.ARM_REG_SP
            else self.r[13]
        )
        idx = self.r[m.index - A.ARM_REG_R0] if m.index not in (0, A.ARM_REG_INVALID) else 0
        return (base + idx + m.disp) & 0xFFFFFFFF

    def regnum(self, r):
        return {A.ARM_REG_SP: 13, A.ARM_REG_LR: 14, A.ARM_REG_PC: 15}.get(r, r - A.ARM_REG_R0)

    def step(self, ins, pc):
        mn, ops, nxt = ins.mnemonic, ins.operands, pc + ins.size
        R = lambda i: self.regnum(ops[i].reg)
        if mn == "push":
            regs = [self.regnum(o.reg) for o in ops]
            self.r[13] -= 4 * len(regs)
            for i, rg in enumerate(regs):
                self.w32(self.r[13] + 4 * i, self.r[rg])
        elif mn == "pop":
            regs = [self.regnum(o.reg) for o in ops]
            for i, rg in enumerate(regs):
                v = self.r32(self.r[13] + 4 * i)
                if rg == 15:
                    nxt = v & ~1
                else:
                    self.r[rg] = v
            self.r[13] += 4 * len(regs)
        elif mn in ("movs", "mov"):
            v = self.val(ops[1])
            self.r[R(0)] = v
            if mn == "movs":
                self.flags_nz(v)
        elif mn in ("mvns",):
            self.r[R(0)] = self.flags_nz(~self.val(ops[1]))
        elif mn in ("adds", "add", "subs", "sub"):
            if len(ops) == 2:
                a, bb = self.r[R(0)], self.val(ops[1])
            else:
                a, bb = (
                    self.r[R(1)] if ops[1].type == A.ARM_OP_REG and ops[1].reg != A.ARM_REG_PC else ((pc + 4) & ~3),
                    self.val(ops[2]),
                )
            if mn.startswith("add"):
                res = (a + bb) & 0xFFFFFFFF
                if mn == "adds":
                    self.N, self.Z = bool(res >> 31), res == 0
                    self.C = a + bb > 0xFFFFFFFF
                    self.V = bool((~(a ^ bb) & (a ^ res)) >> 31)
            else:
                res = self.flags_sub(a, bb) if mn == "subs" else (a - bb) & 0xFFFFFFFF
            self.r[R(0)] = res
        elif mn == "cmp":
            self.flags_sub(self.r[R(0)], self.val(ops[1]))
        elif mn in ("ands", "eors", "orrs"):
            a, bb = self.r[R(0)], self.val(ops[1])
            self.r[R(0)] = self.flags_nz({"ands": a & bb, "eors": a ^ bb, "orrs": a | bb}[mn])
        elif mn in ("lsls", "lsrs", "asrs"):
            a = self.r[R(1)] if len(ops) == 3 else self.r[R(0)]
            sh = self.val(ops[-1]) & 0xFF
            if mn == "lsls":
                res = a << sh
                self.C = bool(res >> 32) if sh else self.C
            elif mn == "lsrs":
                res = a >> sh
                self.C = bool((a >> (sh - 1)) & 1) if sh else self.C
            else:
                res = (a - (1 << 32) if a >> 31 else a) >> sh
                self.C = bool((a >> (sh - 1)) & 1) if sh else self.C
            self.r[R(0)] = self.flags_nz(res)
        elif mn in ("ldr", "ldrb", "ldrh", "str", "strb", "strh"):
            ad = self.addr(ops[1], pc)
            if mn == "ldr":
                self.r[R(0)] = self.r32(ad)
            elif mn == "ldrb":
                self.r[R(0)] = self.r8(ad)
            elif mn == "ldrh":
                self.r[R(0)] = self.r8(ad) | self.r8(ad + 1) << 8
            elif mn == "str":
                self.w32(ad, self.r[R(0)])
            elif mn == "strh":
                self.w8(ad, self.r[R(0)])
                self.w8(ad + 1, self.r[R(0)] >> 8)
            else:
                self.w8(ad, self.r[R(0)])
        elif mn in ("bl", "blx"):
            self.r[14] = nxt | 1
            nxt = ops[0].imm

        elif mn == "b" or mn.startswith("b") and len(mn) == 3 and mn not in ("bic", "blx"):
            if self.cond(ins.cc):
                nxt = ops[0].imm
        elif mn == "bx":
            nxt = self.r[R(0)] & ~1
        else:
            raise NotImplementedError(f"{pc:08x} {mn} {ins.op_str}")
        self.r[15] = nxt
        return nxt
