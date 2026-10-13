"""Tests for scriptinsert.py ([[script_insert]]) and the blank-player-name-batch fix built on it.

Run:  python3 -m unittest -v work/tools/test_script_insert.py
"""

import copy
import hashlib
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
import scriptinsert as SI

BUF = bytes.fromhex("BE0000")           # BufferPlayersName 0
OPN = {v[0]: k for k, v in R.cmds().items()}


def cmd(name, *args):
    op = OPN[name]
    sizes = R.cmds()[op][1]
    out = struct.pack("<H", op)
    for s, a in zip(sizes, args, strict=True):
        out += int(a).to_bytes(s, "little", signed=(a < 0))
    return out


def build_member(code_parts, movement=b"", pad_to=4):
    """Header (one entry at the first command) + code + padding + movement data. code_parts: list of bytes or
    callables(pos_of_end) -> bytes for relative operands, to keep the test scripts readable."""
    hdr_len = 4 + 2
    code = b"".join(code_parts)
    body = struct.pack("<i", hdr_len - 4) + struct.pack("<H", SI.TERMINATOR) + code
    pad = (-len(body)) % pad_to
    return body + bytes(pad) + movement


def disasm_seq(data):
    entries, ins = R.disasm(data)
    return entries, ins


def landing(data, ins, entries, pc_of_instr):
    """Index (in sorted reachable order) of the instruction a target lands on."""
    order = {pc: i for i, pc in enumerate(sorted(ins))}
    return order


def identity_view(data):
    """Per reachable instruction in address order: (op, plain args, resolved target as ('ins', idx) | ('data', bytes))."""
    entries, ins = R.disasm(data)
    pcs = sorted(ins)
    idx = {pc: i for i, pc in enumerate(pcs)}
    view = []
    for pc in pcs:
        op, a, nx, t = ins[pc]
        if op in SI.REL_OPS:
            tgt = nx + a[-1]
            if op == 94:
                end = tgt
                while R.struct.unpack_from("<H", data, end)[0] != 0xFE:
                    end += 4
                target = ("data", bytes(data[tgt:end + 2]), tgt % 4)
            else:
                target = ("ins", idx[tgt])
            view.append((op, tuple(a[:-1]), target))
        else:
            view.append((op, tuple(a), None))
    return view, [idx[e] for e in entries], pcs


def make_script():
    if True:
        # 0: SetVar; 1: GoToIf fwd over NPCMsg; 2: NPCMsg; 3(label): ApplyMovement; 4: GoTo back to 0; End; movement
        mv = struct.pack("<HHHH", 0x0F, 1, 0xFE, 0)
        parts = []
        a = cmd("SetVar", 0x4000, 1)
        b_len = len(cmd("GoToIf", 1, 0))
        m = cmd("NPCMsg", 5)
        c_len = len(cmd("ApplyMovement", 255, 0))
        d_len = len(cmd("GoTo", 0))
        hdr_len = 6
        base = hdr_len
        pc_b = base + len(a)
        pc_m = pc_b + b_len
        pc_c = pc_m + len(m)
        pc_d = pc_c + c_len
        pc_end = pc_d + d_len
        code_end = pc_end + 2
        data_start = code_end + ((-code_end) % 4)
        parts.append(a)
        parts.append(cmd("GoToIf", 1, pc_c - (pc_b + b_len)))              # forward, over the NPCMsg
        parts.append(m)
        parts.append(cmd("ApplyMovement", 255, data_start - (pc_c + c_len)))
        parts.append(cmd("GoTo", base - (pc_d + d_len)))                    # backward to the first command
        parts.append(cmd("End"))
        d = build_member(parts, mv)
        assert len(d) % 4 == 0
        return d, dict(pc_m=pc_m, pc_c=pc_c, pc_d=pc_d, data_start=data_start)


class Synthetic(unittest.TestCase):
    def script(self):
        return make_script()

    def test_insert_relocates_everything(self):
        d, info = self.script()
        new = SI.insert(d, [(info["pc_m"], BUF)])
        v0, e0, _ = identity_view(d)
        v1, e1, pcs = identity_view(new)
        # same instructions plus exactly the inserted one, in place
        self.assertEqual(len(v1), len(v0) + 1)
        ins_idx = [i for i, x in enumerate(v1) if x[0] == OPN["BufferPlayersName"]]
        self.assertEqual(len(ins_idx), 1)
        rest = [x for i, x in enumerate(v1) if i != ins_idx[0]]
        # targets as instruction indexes shift by one for everything after the insert: compare through a map
        def norm(view, skip):
            out = []
            for op, a, t in view:
                if t and t[0] == "ins":
                    k = t[1]
                    if skip is not None and k > skip:
                        k -= 1
                    t = ("ins", k)
                out.append((op, a, t))
            return out
        self.assertEqual(norm(rest, ins_idx[0]), norm(v0, None))
        self.assertEqual(e1, e0)
        self.assertEqual(len(new), len(d) + 3 + 1)                      # 3 bytes + 1 byte keeps the block mod 4

    def test_jump_to_the_insertion_point_runs_the_insert(self):
        d, info = self.script()
        # the GoToIf (forward) targets pc_c (ApplyMovement); insert there: the jump must land on the inserted command
        new = SI.insert(d, [(info["pc_c"], BUF)])
        entries, ins = R.disasm(new)
        goto_if = next((pc, v) for pc, v in sorted(ins.items()) if v[0] == OPN["GoToIf"])
        self.assertEqual(ins[goto_if[1][3]][0], OPN["BufferPlayersName"])

    def test_backward_jump_to_insertion_point(self):
        d, info = self.script()
        first = 6
        new = SI.insert(d, [(first, BUF)])
        entries, ins = R.disasm(new)
        self.assertEqual(entries[0], 6)
        goto = next(v for pc, v in ins.items() if v[0] == OPN["GoTo"])
        self.assertEqual(ins[goto[3]][0], OPN["BufferPlayersName"])
        self.assertEqual(goto[3], 6)

    def test_movement_block_keeps_alignment_and_content(self):
        d, info = self.script()
        for n in (1, 2, 3):
            new = SI.insert(d, [(info["pc_m"], BUF * n)])
            v0, _, _ = identity_view(d)
            v1, _, _ = identity_view(new)
            mv0 = next(x for x in v0 if x[0] == 94)[2]
            mv1 = next(x for x in v1 if x[0] == 94)[2]
            self.assertEqual(mv0[1], mv1[1])
            self.assertEqual(mv0[2], mv1[2])

    def test_refusals(self):
        d, info = self.script()
        for off in (0, 3, info["pc_m"] + 1, len(d)):
            with self.assertRaises(SI.ScriptInsertError):
                SI.insert(d, [(off, BUF)])
        with self.assertRaises(SI.ScriptInsertError):
            SI.insert(d, [(info["pc_m"], BUF), (info["pc_m"], BUF)])
        with self.assertRaises(SI.ScriptInsertError):
            SI.insert(d, [(info["pc_m"], b"\xBE")])                       # not a whole command
        with self.assertRaises(SI.ScriptInsertError):
            SI.insert(d, [(info["pc_m"], cmd("GoTo", 100))])              # a jump out of the insert
        with self.assertRaises(SI.ScriptInsertError):
            SI.insert(d, [(info["pc_m"], cmd("GoTo", -4))])               # ... or into the middle of a command
        with self.assertRaises(SI.ScriptInsertError):
            SI.insert(d, [(info["pc_m"], cmd("Call", 0))])                # only GoTo / GoToIf may jump inside
        with self.assertRaises(SI.ScriptInsertError):
            SI.insert(d, [(info["pc_m"], cmd("ApplyMovement", 255, 0))])  # no movement
            SI.insert(d, [(info["pc_m"], cmd("GoTo", 5))])                # a jump out of the insert
        with self.assertRaises(SI.ScriptInsertError):
            SI.insert(d, [(info["pc_m"], cmd("Call", 0))])                # a call in the insert
        with self.assertRaises(SI.ScriptInsertError):
            SI.insert(d, [(info["pc_m"], cmd("GoTo", -7))])               # a jump back out of the insert
        # a jump that stays inside the block (here: over the next command, to the block's end) is fine
        SI.insert(d, [(info["pc_m"], cmd("GoToIf", 5, len(cmd("End"))) + cmd("End"))])
        bad = bytearray(d)
        bad[-4] = 0x7F                                                    # break the movement block marker
        with self.assertRaises(SI.ScriptInsertError):
            SI.insert(bytes(bad), [(info["pc_m"], BUF)])

    def test_jump_inside_the_insert_is_kept_as_written(self):
        # CompareVarToValue; GoToIf != over a block of two commands (the shape of a guard); the rest is untouched
        d, info = self.script()
        skipped = cmd("NPCMsg", 9) + cmd("End")
        blk = cmd("CompareVarToValue", 0x800C, 0) + cmd("GoToIf", 5, len(skipped)) + skipped
        new, where = SI.insert_ex(d, [(info["pc_m"], blk)])
        at = where[info["pc_m"]]
        self.assertEqual(new[at:at + len(blk)], blk)                       # the insert is copied verbatim
        _, ins = R.disasm(new)
        gi = at + len(cmd("CompareVarToValue", 0, 0))
        self.assertEqual(ins[gi][3], at + len(blk))                         # the jump lands on the original NPCMsg
        self.assertEqual(ins[at + len(blk)][0], OPN["NPCMsg"])
        # a jump to the block's own end (rel 0) is accepted too; the original script's pointers still resolve
        SI.insert(d, [(info["pc_m"], cmd("GoTo", 0) + cmd("End"))])
        v0, _, _ = identity_view(d)
        v1, _, _ = identity_view(new)
        self.assertEqual(len(v1), len(v0) + 4)                              # four inserted commands, none lost

    def test_unknown_four_byte_operand_refused(self):
        d = build_member([cmd("ScrCmd_705", 1, 2), cmd("NPCMsg", 1), cmd("End")])
        with self.assertRaises(SI.ScriptInsertError):
            SI.insert(d, [(6 + 8, BUF)])

    def test_unexplained_bytes_refused(self):
        d = build_member([cmd("NPCMsg", 1), cmd("End")]) + b"\xff\xff\xff\xff\xff\xff"
        with self.assertRaises(SI.ScriptInsertError):
            SI.insert(d, [(6, BUF)])

    def test_dead_code_operand_relocated(self):
        # End; GoTo (unreachable) back to the start; insert before the first command
        first = cmd("NPCMsg", 1)
        end = cmd("End")
        dead_pc = 6 + len(first) + len(end)
        dead = cmd("GoTo", 6 - (dead_pc + len(cmd("GoTo", 0))))
        d = build_member([first, end, dead, cmd("End")])
        new = SI.insert(d, [(6, BUF)])
        # decode the dead GoTo by hand: it must still end on the (inserted) first command
        pc = dead_pc + 3
        op, args, nx = SI.decode_at(new, pc)
        self.assertEqual(op, OPN["GoTo"])
        self.assertEqual(nx + args[-1], 6)


class Stage(unittest.TestCase):
    """narcpatch.apply with [[script_insert]]: guards, report, verify, combination with [[narc_bytes]]."""

    def setUp(self):
        self.d, self.info = make_script()
        self.sha = hashlib.sha1(self.d).hexdigest()
        self.store = {"a/0/1/2": M.Narc([b"x" * 8, self.d, b"y" * 8]).build()}

    def fix(self, **kw):
        e = {"id": "i1", "narc": "a/0/1/2", "member": 1, "offset": hex(self.info["pc_m"]),
             "expect": self.d[self.info["pc_m"]:self.info["pc_m"] + 3].hex(" "), "insert": "BE 00 00",
             "member_sha1": [self.sha], "notes": "n"}
        e.update(kw)
        return [{"id": "f", "kind": "narc", "script_insert": [e]}]

    def run_stage(self, fixes):
        return N.apply(self.store.__getitem__, self.store.__setitem__, fixes)

    def test_apply_verify_and_guards(self):
        rows = self.run_stage(self.fix())
        new = M.Narc.parse(self.store["a/0/1/2"]).files[1]
        self.assertEqual(len(new), len(self.d) + 4)
        self.assertEqual(new[rows[0]["offset"]:rows[0]["offset"] + 3], BUF)
        self.assertTrue(N.verify(self.store.__getitem__, rows).startswith("ok"))
        # idempotence: a second run on the patched member is refused
        with self.assertRaises(N.NarcPatchError):
            self.run_stage(self.fix())
        for kw, msg in (({"member_sha1": ["0" * 40]}, "member SHA-1"), ({"expect": "2D 00 07"}, "expected"),
                        ({"member": 9}, "has 3 members")):
            self.store["a/0/1/2"] = M.Narc([b"x" * 8, self.d, b"y" * 8]).build()
            with self.assertRaises(N.NarcPatchError) as cm:
                self.run_stage(self.fix(**kw))
            self.assertIn(msg, str(cm.exception))

    def test_with_narc_bytes_in_the_same_member(self):
        nb = {"id": "b1", "narc": "a/0/1/2", "member": 1, "offset": "0x6", "expect": "0x0029", "new": "0x0029",
              "member_sha1": self.sha, "notes": "n"}
        nb["expect"], nb["new"] = "0x%04X" % struct.unpack_from("<H", self.d, 6), "0x%04X" % struct.unpack_from("<H", self.d, 6)
        fixes = self.fix()
        fixes[0]["narc_bytes"] = [nb]
        rows = self.run_stage(fixes)
        self.assertTrue(all(r["relocated"] for r in rows if r.get("kind") != "script_insert"))
        self.assertTrue(N.verify(self.store.__getitem__, rows).startswith("ok"))


class Schema(unittest.TestCase):
    def test_real_fix_validates(self):
        fx = next(f for f in F.load_all() if f["id"] == "blank-player-name-batch")
        self.assertTrue(fx["enabled"])
        self.assertEqual(F.validate([fx]) if hasattr(F, "validate") else [], [])

    def test_bad_entries(self):
        base = {"id": "i", "narc": "a/0/1/2", "member": 1, "offset": "0x10", "expect": "2D 00 01", "insert": "BE 00 00",
                "member_sha1": ["a" * 40], "notes": "n"}
        for key, val in (("offset", "16"), ("insert", "BE 0"), ("member_sha1", ["xyz"]), ("member_sha1", [])):
            fx = {"id": "f", "title": "t", "kind": "narc", "enabled": False, "decisions": [], "requires": [],
                  "why": "w", "what": "w", "evidence": ["e"], "script_insert": [dict(base, **{key: val})]}
            probs = []
            F._validate_entries(fx, "f", probs)
            self.assertTrue(probs, (key, val))


@unittest.skipUnless(F.ROM_CN.exists() and F.ROM_CN.stat().st_size > 100_000_000, "needs local Chinese ROM")
class RealMembers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = M.get_file(M.load_rom(F.ROM_CN), "a/0/1/2")
        cls.fixes = {f["id"]: f for f in F.load_all()}
        cls.batch = cls.fixes["blank-player-name-batch"]
        cls.before = M.Narc.parse(cls.archive).files

    def patched(self, *ids):
        store = {"a/0/1/2": self.archive}
        rows = N.apply(store.__getitem__, store.__setitem__, [self.fixes[i] for i in ids])
        self.assertTrue(N.verify(store.__getitem__, rows).startswith("ok"))
        return M.Narc.parse(store["a/0/1/2"]).files, rows

    def check_member(self, orig, new, entries):
        """Per-member: the new decode is the old decode plus exactly the inserted commands, every relative operand
        resolves to the same instruction / identical movement block, header slots hit the same instructions."""
        ins_list = sorted(entries)
        v0, e0, pcs0 = identity_view(orig)
        v1, e1, pcs1 = identity_view(new)
        n_ins = len(ins_list)
        self.assertEqual(len(v1), len(v0) + n_ins)
        # structural comparison: remove inserted commands (identified by new pc position) and compare
        skip = set()
        # walk both lists: whenever the new list has a BufferPlayersName that the old does not at this slot, it is the insert
        a, b = 0, 0
        mapping = {}
        while b < len(v1):
            if a < len(v0) and v1[b][:2] == v0[a][:2]:
                mapping[b] = a
                a += 1
                b += 1
            else:
                self.assertEqual(v1[b][0], OPN["BufferPlayersName"], f"unexpected extra command at {b}")
                skip.add(b)
                b += 1
        self.assertEqual(a, len(v0))
        self.assertEqual(len(skip), n_ins)

        def old_index(new_idx):
            # a target that lands on an inserted command means: the old command right after it
            while new_idx in skip:
                new_idx += 1
            return mapping[new_idx]

        for b, a in mapping.items():
            t0, t1 = v0[a][2], v1[b][2]
            if t0 is None:
                self.assertIsNone(t1)
            elif t0[0] == "ins":
                self.assertEqual(t1[0], "ins")
                self.assertEqual(old_index(t1[1]), t0[1], f"jump from {a} lands elsewhere")
            else:
                self.assertEqual(t0[1], t1[1])                       # identical movement block bytes
                self.assertEqual(t0[2], t1[2])                       # same alignment modulo 4
        self.assertEqual([old_index(i) for i in e1], e0)

    def test_every_batch_member(self):
        files, rows = self.patched("blank-player-name-batch")
        by_member = {}
        for e in self.batch["script_insert"]:
            by_member.setdefault(e["member"], []).append((int(e["offset"], 16), bytes.fromhex(e["insert"].replace(" ", ""))))
        self.assertEqual([i for i in range(len(self.before)) if self.before[i] != files[i]], sorted(by_member))
        self.assertEqual(len(by_member), 36)
        self.assertEqual(sum(len(v) for v in by_member.values()), 53)
        for m, ent in by_member.items():
            self.check_member(self.before[m], files[m], ent)
            # decodes cleanly end to end (Layout explains every byte) and the header terminator is intact
            SI.Layout(files[m])
            grow = len(files[m]) - len(self.before[m])
            self.assertGreaterEqual(grow, 3 * len(ent))
            self.assertLess(grow, 3 * len(ent) + 4 * 12)

    def test_with_blank_player_name(self):
        files, _ = self.patched("blank-player-name", "blank-player-name-batch")
        solo, _ = self.patched("blank-player-name")
        # member 171 got the two inserts on top of the old fix's rotations; both together still decode
        SI.Layout(files[171])
        v_solo, _, _ = identity_view(solo[171])
        v_both, _, _ = identity_view(files[171])
        self.assertEqual(len(v_both), len(v_solo) + 2)
        # the old fix's relative operand (rotated ApplyMovement) still reaches an identical movement block
        mv = lambda v: sorted(x[2][1] for x in v if x[0] == 94)
        self.assertEqual(mv(v_both), mv(v_solo))
        for m in (111, 733):
            self.assertEqual(files[m], solo[m])


    def test_with_all_overlapping_fixes(self):
        """romance-mail-mismatch (842), blank-player-name (111/171/733) and the batch together. narc_bytes entries
        run first, then the inserts, whatever the order in the fix list."""
        ids = ["romance-mail-mismatch", "blank-player-name", "blank-player-name-batch"]
        both, _ = self.patched(*ids)
        rev, _ = self.patched(*reversed(ids))
        self.assertEqual(both, rev)
        solo, _ = self.patched("blank-player-name-batch")
        rom_only, _ = self.patched("romance-mail-mismatch")
        for m in (842, 843, 111, 171, 733):
            SI.Layout(both[m])
        v_solo, _, _ = identity_view(solo[842])
        v_both, _, _ = identity_view(both[842])
        v_rom, _, _ = identity_view(rom_only[842])
        self.assertEqual(len(v_both), len(v_rom) + 1)           # the batch's one insert on top of the romance edits
        self.assertEqual(len(v_both), len(v_solo) + (len(v_rom) - len(identity_view(self.before[842])[0])))
        self.assertEqual(sorted(x[2][1] for x in v_both if x[0] == 94), sorted(x[2][1] for x in v_rom if x[0] == 94))
        self.assertEqual(both[843], rom_only[843])
        self.assertEqual([i for i in range(len(both)) if both[i] != self.before[i] and i not in {m["member"] for m in self.batch["script_insert"]} | {111, 171, 733, 842, 843}], [])

    def test_only_guards_refuse_other_roms(self):
        store = {"a/0/1/2": self.archive}
        fx = copy.deepcopy(self.batch)
        fx["script_insert"][0]["member_sha1"] = ["0" * 40]
        with self.assertRaises(N.NarcPatchError):
            N.apply(store.__getitem__, store.__setitem__, [fx])


if __name__ == "__main__":
    unittest.main()
