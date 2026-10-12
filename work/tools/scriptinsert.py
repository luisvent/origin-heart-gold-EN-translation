#!/usr/bin/env python3
"""scriptinsert - insert commands into an event-script member (a/0/1/2) and relocate everything that stores offsets.

An event-script member is: a header (one 4-byte entry per script, each the offset from the end of that header slot
to the script's first command, then the 2-byte terminator 0xFD13), the commands, and the movement data that
ApplyMovement points at (4-byte {action, count} pairs ending with action 0xFE; blocks sit in the gaps between the
code and at the end). Everything that points inside the member is relative:

  * the header slots,
  * the last (4-byte) operand of GoTo, ObjectGoTo, BGGoTo, DirectionGoTo, Call, GoToIf, CallIf, GoToIfTrainerDefeated
    and ApplyMovement: signed offset from the END of that instruction.

insert() puts bytes in front of chosen commands, keeps every one of those pointers on the same instruction or data
block, and returns the new member. It fails (ScriptInsertError) instead of guessing:
  * an insertion point that is not the start of a command reachable from an entry,
  * bytes the decoder does not explain (neither a command reached from an entry, a movement block, nor a run of
    commands that decodes cleanly to the end of its gap),
  * a command with a 4-byte operand that is not known to be a relative offset or a plain immediate,
  * an inserted block that is not whole commands.

Targets that point exactly at an insertion point land on the inserted bytes (so every path to the command runs the
inserted ones first). Movement blocks keep their position modulo 4 (the generator aligns them to 4): zero padding
goes in front of a block when the bytes inserted before it are not a multiple of 4.

Pure functions over bytes: no ROM access (the command table comes from docs/romdata.py's script_cmds.json).
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS / "docs"))

import romdata as R  # noqa: E402

TERMINATOR = 0xFD13
# commands whose LAST operand (4 bytes) is a signed offset from the end of the instruction
REL_OPS = {22, 23, 24, 25, 26, 28, 29, 225, 94}   # GoTo ObjectGoTo BGGoTo DirectionGoTo Call GoToIf CallIf GoToIfTrainerDefeated ApplyMovement
# commands with a 4-byte operand that is a plain immediate (money, coins, bank balance, LoadWord)
IMM4_OPS = {5, 110, 111, 112, 532, 794}
MOVE_END = 0xFE


class ScriptInsertError(Exception):
    pass


def u16(data, p):
    return struct.unpack_from("<H", data, p)[0]


def decode_at(data: bytes, pc: int):
    """(op, args, next_pc) for one command at pc, or None when it is not a whole known command."""
    C = R.cmds()
    if pc + 2 > len(data):
        return None
    op = u16(data, pc)
    if op not in C:
        return None
    q, args = pc + 2, []
    try:
        sizes = R._argsizes(op, data, q)
    except (IndexError, struct.error):
        return None
    for s in sizes:
        if q + s > len(data):
            return None
        args.append(int.from_bytes(data[q:q + s], "little", signed=(s == 4)))
        q += s
    return op, args, q


def operand_kind(op: int, args) -> str:
    """'rel' (last operand is an offset from the instruction end), 'imm' or 'none'. Raises on an unknown 4-byte operand."""
    if op in REL_OPS:
        return "rel"
    sizes = R.cmds()[op][1] if op not in (400, 401, 402, 465, 489) else []
    if 4 in sizes:
        if op in IMM4_OPS:
            return "imm"
        raise ScriptInsertError(f"command {op} ({R.cmds()[op][0]}) has a 4-byte operand that is not known to be a "
                                f"relative offset or an immediate")
    return "none"


class Layout:
    """What the decoder knows about one member."""

    def __init__(self, data: bytes):
        self.data = data
        try:
            self.entries = R.script_entries(data)
        except struct.error as ex:
            raise ScriptInsertError(f"not a script member: {ex}") from ex
        if not self.entries:
            raise ScriptInsertError("no script entries")
        self.header_len = 4 * len(self.entries) + 2
        if 4 * len(self.entries) + 2 > len(data) or u16(data, 4 * len(self.entries)) != TERMINATOR:
            raise ScriptInsertError("header terminator 0xFD13 not found where expected")
        _, self.ins = R.disasm(data)                       # reachable commands: pc -> (op, args, next, jump target)
        self.dead: dict = {}                               # decoded runs in gaps (not reachable): pc -> (op, args, next)
        self.blocks: list = []                             # movement blocks (start, end)
        self._explain()

    def _covered(self):
        cov = bytearray(len(self.data))
        for i in range(self.header_len):
            cov[i] = 1
        for pc, (_, _, nx, _) in self.ins.items():
            for i in range(pc, nx):
                cov[i] = 1
        for a, b in self.blocks:
            for i in range(a, b):
                cov[i] = 1
        return cov

    def _explain(self):
        data = self.data
        for pc, (op, args, nx, _) in self.ins.items():
            operand_kind(op, args)
        # movement blocks: from every ApplyMovement target, {action, count} pairs through the 0xFE end marker
        starts = sorted({nx + args[-1] for (op, args, nx, _) in self.ins.values() if op == 94})
        for s in starts:
            if not 0 <= s < len(data):
                raise ScriptInsertError(f"ApplyMovement target {s} is outside the member")
            e = s
            while True:
                if e + 2 > len(data):
                    raise ScriptInsertError(f"movement block at {s} runs past the member")
                act = u16(data, e)
                if act == MOVE_END:
                    e = min(e + 4, len(data))          # the last block of a member may end after the 2-byte marker
                    break
                e += 4
            self.blocks.append((s, e))
        self.blocks = self._merge(self.blocks)
        cov = self._covered()
        # what is left must be commands that decode cleanly up to the end of their gap (dead code, alignment zeros)
        i = 0
        while i < len(data):
            if cov[i]:
                i += 1
                continue
            j = i
            while j < len(data) and not cov[j]:
                j += 1
            pc = i
            if not any(data[i:j]):                          # zero bytes: alignment padding (in front of a block)
                i = j
                continue
            while pc < j:
                if not any(data[pc:j]):                     # ... or at the end of a run of dead code
                    break
                d = decode_at(data, pc)
                if d is None or d[2] > j:
                    raise ScriptInsertError(f"bytes {pc}..{j} are not explained (not a reachable command, a movement "
                                            f"block or a run of whole commands)")
                operand_kind(d[0], d[1])
                self.dead[pc] = d
                pc = d[2]
            i = j

    @staticmethod
    def _merge(blocks):
        out = []
        for a, b in sorted(blocks):
            if out and a <= out[-1][1]:
                out[-1] = (out[-1][0], max(out[-1][1], b))
            else:
                out.append((a, b))
        return out

    def commands(self):
        """Every decoded command, reachable or not: (pc, op, args, next_pc)."""
        for pc, (op, args, nx, _) in self.ins.items():
            yield pc, op, args, nx
        for pc, (op, args, nx) in self.dead.items():
            yield pc, op, args, nx


def check_block(block: bytes):
    """The inserted bytes must be whole commands with no relative operand (nothing in them points anywhere)."""
    pc = 0
    while pc < len(block):
        d = decode_at(block, pc)
        if d is None:
            raise ScriptInsertError(f"inserted bytes at {pc} are not a whole known command")
        kind = operand_kind(d[0], d[1])
        if kind == "rel":
            raise ScriptInsertError("inserted bytes must not contain jumps or movement (relative operands)")
        pc = d[2]


def insert(data: bytes, inserts) -> bytes:
    """insert_ex() without the positions."""
    return insert_ex(data, inserts)[0]


def insert_ex(data: bytes, inserts):
    """`inserts`: [(offset, bytes)] in original coordinates, each offset the start of a reachable command. Returns
    (the new member, {offset: where its inserted bytes start in the new member}). Several inserts at one offset are
    rejected (merge them in the caller)."""
    lay = Layout(data)
    offs = [o for o, _ in inserts]
    if len(set(offs)) != len(offs):
        raise ScriptInsertError("two inserts at the same offset")
    for off, blk in inserts:
        if off not in lay.ins:
            raise ScriptInsertError(f"offset {off} is not the start of a command reachable from an entry")
        if off < lay.header_len:
            raise ScriptInsertError(f"offset {off} is inside the header")
        if not blk:
            raise ScriptInsertError("empty insert")
        check_block(bytes(blk))
    ins = sorted((o, bytes(b)) for o, b in inserts)

    # padding in front of movement blocks so each keeps its position modulo 4
    pads = []                                              # (offset of the block, zero bytes)
    shift = 0
    pend = list(ins)
    for a, _ in lay.blocks:
        shift += sum(len(b) for o, b in pend if o < a)
        pend = [(o, b) for o, b in pend if o >= a]
        need = (-shift) % 4
        if need:
            pads.append((a, bytes(need)))
            shift += need

    cuts = sorted([(o, b, False) for o, b in ins] + [(o, b, True) for o, b in pads])   # (offset, bytes, is_pad)

    def moved(x):          # new position of the byte at x (inserts at or before x are in front of it)
        return x + sum(len(b) for o, b, _ in cuts if o <= x)

    def target(t):         # new position a pointer to t gets: bytes inserted AT t sit in front of the command, so a
        return t + sum(len(b) for o, b, pad in cuts if o < t or (pad and o == t))   # jump to t runs them; a pad stays in front of its block

    def base(nx):          # new end position of an instruction that ended at nx
        return nx + sum(len(b) for o, b, _ in cuts if o < nx)

    out = bytearray()
    prev = 0
    for o, b, _ in cuts:
        out += data[prev:o]
        out += b
        prev = o
    out += data[prev:]

    # header slots
    for i, e in enumerate(lay.entries):
        struct.pack_into("<i", out, 4 * i, target(e) - (4 * i + 4))
    # relative operands of every decoded command
    for pc, op, args, nx in lay.commands():
        if op in REL_OPS:
            tgt = nx + args[-1]
            struct.pack_into("<i", out, moved(nx - 4), target(tgt) - base(nx))
    return bytes(out), {o: target(o) for o, _ in ins}
