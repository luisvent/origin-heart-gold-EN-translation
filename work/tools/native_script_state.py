"""Bounded offline execution of local ROM Thumb script state handlers.

No full-game emulation, source-save edits or ROM patching. Unsupported commands
fail unless explicitly listed as a scene stub. Every executed instruction and
ROM data read is retained for paired byte pinning. All saves are private RAM.
"""

from pathlib import Path
import sys, struct, hashlib, json

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "work/tools"), str(ROOT / "work/tools/docs")]
from double_target_thumb_model import CPU, md
import romdata as R
import ndspy.rom, ndspy.narc, ndspy.codeCompression

BASE, TABLE = 0x02000000, 0x020F793C
CTX, ENV, SAVE, VARS, SPECIAL, SCRIPT = (0x02300000, 0x02301000, 0x02302000, 0x02303000, 0x02304000, 0x02400000)
RET = 0x0DEAD000
OBJECT, MANAGER = 0x02305000, 0x02306000
NATIVE = {
    "CompareVarToValue",
    "GoTo",
    "GoToIf",
    "SetVar",
    "CopyVar",
    "Warp",
    "HidePerson",
    "AddVar",
    "SubVar",
    "SetFlag",
    "ClearFlag",
    "CheckFlag",
    "CheckBattleWon",
}
SCENE = set(
    """PlaySE LockAll BufferRivalsName FacePlayer NPCMsg WaitButton
TouchscreenMenuHide CloseMsg TouchscreenMenuShow ReleaseAll PlayCry WaitCry
ScrCmd_609 ApplyMovement WaitMovement MovePersonFacing BufferPlayersName
GenderMsgBox ToggleFollowingPokemonMovement WaitFollowingPokemonMovement
FollowingPokemonMovement FadeScreen WaitFade AlphPuzzle RestoreOverworld Wait
ScreenShake ScrCmd_102 ScrCmd_109 MenuInit MenuItemAdd MenuExec
WildBattle TrainerBattle MultiBattle CallStd ScrCmd_573 ScrCmd_561
ScrCmd_564 ScrCmd_565 ScrCmd_566 ScrCmd_567 ScrCmd_568 ScrCmd_569
ScrCmd_570 ScrCmd_571 ScrCmd_572""".split()
)
ALLOWED_CODE = [
    (0x0203F514, 0x0203F57C),
    (0x0203FAB0, 0x0203FB88),
    (0x02040110, 0x02040124),
    (0x02040208, 0x02040232),
    (0x02040368, 0x02040390),
    (0x02040440, 0x020404F4),
    (0x020405F0, 0x02040728),
    (0x0204F864, 0x0204F948),
    (0x02042AF8, 0x02042B68),
    (0x020416FC, 0x0204172E),
    (0x0205D57C, 0x0205D59C),
    (0x0205E3F0, 0x0205E3F4),
    (0x0205E6A8, 0x0205E6B4),
    (0x0205E4E0, 0x0205E4E8),
    (0x0205E360, 0x0205E368),
    (0x0205E2DC, 0x0205E2DE),
    (0x02048DF0, 0x02048E1E),
    (0x0205172C, 0x0205173C),
]


def digest(b):
    return hashlib.sha256(b).hexdigest()


def load_source(path):
    """Read local ROM bytes; caller owns hash pins and expected script variant."""
    raw = Path(path).read_bytes()
    rom = ndspy.rom.NintendoDSRom(raw)
    return {
        "arm9": bytes(ndspy.codeCompression.decompress(rom.arm9)),
        "scripts": ndspy.narc.NARC(rom.getFileByName("a/0/1/2")).files,
        "events": ndspy.narc.NARC(rom.getFileByName("a/0/3/2")).files,
        "sha256": digest(raw),
    }


class NativeCPU(CPU):
    def __init__(self, arm9):
        super().__init__(b"", 0)
        self.arm9 = arm9
        self.rom_reads = set()
        self.executed = {}
        self.writes = []
        self.warp_requests = []
        self.object_flags = {}
        self.object_stubs = []
        self.script = b""
        self.w32(CTX + 0x80, ENV)
        self.w32(ENV + 0xC, SAVE)
        self.w32(ENV + 0x3C, MANAGER)
        self.w32(MANAGER + 0x128, ENV)
        self.w32(OBJECT + 0xB4, MANAGER)

    def r8(self, a):
        if BASE <= a < BASE + len(self.arm9):
            self.rom_reads.add(a)
            return self.arm9[a - BASE]
        if SCRIPT <= a < SCRIPT + len(self.script):
            return self.script[a - SCRIPT]
        if any(
            lo <= a < hi
            for lo, hi in [
                (CTX, CTX + 0x100),
                (ENV, ENV + 0x100),
                (SAVE, SAVE + 0x100),
                (VARS, VARS + 0x500),
                (SPECIAL, SPECIAL + 0x300),
                (OBJECT, OBJECT + 0x100),
                (MANAGER, MANAGER + 0x200),
                (self.stack_top - 0x1000, self.stack_top),
            ]
        ):
            return self.mem.get(a, 0)
        raise RuntimeError(f"unmapped read {a:08x}")

    def w8(self, a, v):
        # Initial parent CPU fixture setup precedes this bounded memory map.
        if hasattr(self, "arm9") and not any(
            lo <= a < hi
            for lo, hi in [
                (CTX, CTX + 0x100),
                (ENV, ENV + 0x100),
                (SAVE, SAVE + 0x100),
                (VARS, VARS + 0x500),
                (SPECIAL, SPECIAL + 0x300),
                (OBJECT, OBJECT + 0x100),
                (MANAGER, MANAGER + 0x200),
                (self.stack_top - 0x1000, self.stack_top),
            ]
        ):
            raise RuntimeError(f"unmapped write {a:08x}")
        self.mem[a] = v & 255
        if hasattr(self, "writes") and VARS <= a < VARS + 0x500:
            self.writes.append({"address": hex(a), "value": v & 255})

    def w16(self, a, v):
        self.w8(a, v)
        self.w8(a + 1, v >> 8)

    def r16(self, a):
        return self.r8(a) | (self.r8(a + 1) << 8)

    def varptr(self, i):
        if 0x4000 <= i < 0x4170:
            return VARS + 2 * (i - 0x4000)
        # Actual resolver literal is 0x7FD6, not 0x8000: these are environment
        # attribute indices. Raw battle outcome uses independent attribute 0x18.
        if 0x8000 <= i < 0x8080:
            return SPECIAL + 4 * (i - 0x7FD6)
        raise RuntimeError(f"unsupported fixture variable {i:x}")

    def var(self, i):
        return self.r16(self.varptr(i))

    def fixture_var(self, i, v):
        self.w16(self.varptr(i), v)

    def flag(self, f):
        return bool(self.r8(VARS + 0x2E0 + (f >> 3)) & (1 << (f & 7)))

    def fixture_flag(self, f, v):
        assert 0 < f <= 3231
        a = VARS + 0x2E0 + (f >> 3)
        mask = 1 << (f & 7)
        self.w8(a, (self.r8(a) | mask) if v else (self.r8(a) & ~mask))

    def call(self, fn, *args):
        for i, a in enumerate(args):
            self.r[i] = a & 0xFFFFFFFF
        self.r[13], self.r[14], pc = self.stack_top, RET | 1, fn & ~1
        for steps in range(10000):
            if pc == RET:
                return self.r[0]
            if pc == 0x0204F858:
                assert self.r[0] == SAVE
                self.clobber_callers()
                self.r[0] = VARS
                pc = self.r[14] & ~1
                continue
            if pc == 0x0203FA2C:
                assert self.r[0] == ENV and 0 <= self.r[1] < 0x80
                result = SPECIAL + 4 * self.r[1]
                self.clobber_callers()
                self.r[0] = result
                pc = self.r[14] & ~1
                continue
            if pc == 0x02052A4C:
                # Field-map warp service is omitted. Its arguments were decoded
                # and resolved by the actual native Warp handler, not Python.
                self.warp_requests.append(
                    {
                        "field": hex(self.r[0]),
                        "map": self.r[1],
                        "warp_id": self.r[2],
                        "x": self.r[3],
                        "z": self.r32(self.r[13]),
                        "direction": self.r32(self.r[13] + 4),
                    }
                )
                self.clobber_callers()
                self.r[0] = 0
                pc = self.r[14] & ~1
                continue
            if pc == 0x0205DFDC:
                assert self.r[0] == MANAGER
                object_id = self.r[1]
                if object_id not in self.object_flags:
                    raise RuntimeError(f"no object metadata fixture for {object_id}")
                flag = self.object_flags[object_id]
                self.w32(OBJECT + 0x1C, flag)
                self.object_stubs.append({"object_id": object_id, "flag": flag, "lookup": "fixture"})
                self.clobber_callers()
                self.r[0] = OBJECT
                pc = self.r[14] & ~1
                continue
            if pc == 0x0205D52C:
                assert self.r[0] == OBJECT
                self.object_stubs.append({"destroy": "omitted"})
                self.clobber_callers()
                self.r[0] = 0
                pc = self.r[14] & ~1
                continue
            if pc == 0x02025B2C:
                raise RuntimeError("native assertion reached")
            if not any(lo <= pc < hi for lo, hi in ALLOWED_CODE):
                raise RuntimeError(f"code outside bounded executor {pc:08x}")
            code = bytes(self.r8(pc + i) for i in range(4))
            ins = next(md.disasm(code, pc, 1))
            self.executed[pc] = code[: ins.size].hex()
            pc = self.step(ins, pc)
        raise RuntimeError("instruction budget exhausted")

    def step(self, ins, pc):
        mn, ops = ins.mnemonic, ins.operands
        rg = lambda i: self.regnum(ops[i].reg)
        if mn == "strh":
            self.w16(self.addr(ops[1], pc), self.r[rg(0)])
        elif mn == "rors":
            a = self.r[rg(0)]
            sh = self.val(ops[1]) & 255
            if sh:
                shmod = sh & 31
                result = ((a >> shmod) | (a << (32 - shmod))) & 0xFFFFFFFF if shmod else a
                self.C = bool(result >> 31)
                self.r[rg(0)] = self.flags_nz(result)
        elif mn == "tst":
            self.flags_nz(self.r[rg(0)] & self.val(ops[1]))
        elif mn == "bics":
            self.r[rg(0)] = self.flags_nz(self.r[rg(0)] & ~self.val(ops[1]))
        else:
            return super().step(ins, pc)
        self.r[15] = pc + ins.size
        return pc + ins.size

    def command(self, op, pc):
        self.w32(CTX + 8, SCRIPT + pc + 2)
        handler = self.r32(TABLE + 4 * op) & ~1
        start = len(self.writes)
        warp_start = len(self.warp_requests)
        object_start = len(self.object_stubs)
        ret = self.call(handler, CTX)
        return {
            "handler": hex(handler),
            "return": ret,
            "cursor": self.r32(CTX + 8) - SCRIPT,
            "warp_requests": self.warp_requests[warp_start:],
            "object_stubs": self.object_stubs[object_start:],
            "compare": self.r8(CTX + 2),
            "writes": self.writes[start:],
        }


class Scene:
    def __init__(self, source):
        self.source = source
        self.cpu = NativeCPU(source["arm9"])
        self.trace = []
        self.stubs = []
        self.members = set()
        self.outcomes = []
        self.choices = []
        self.coords = (16, 81)
        self.outputs = {}
        self.object_flags = {}
        zones = json.loads((ROOT / "work/translate/bank_maps.json").read_text())["_zones"]
        for z in zones:
            if z["scripts_bank"] in (23, 45, 50, 52, 92, 842, 943, 962):
                for ob in R.parse_events(source["events"][z["events_bank"]])["obj"]:
                    self.object_flags[(z["scripts_bank"], ob["id"])] = ob["flag"]

    def run(self, member, pc, stop=(), limit=1500):
        b = bytearray(self.source["scripts"][member])
        self.cpu.script = bytes(b)
        self.members.add(member)
        self.cpu.object_flags = {oid: flag for (m, oid), flag in self.object_flags.items() if m == member}
        _, ins = R.disasm(bytes(b))
        cmds = R.cmds()
        for _ in range(limit):
            if pc in stop:
                self.trace.append({"member": member, "pc": pc, "stop": True})
                return pc
            if pc not in ins:
                raise RuntimeError(f"undecoded script {member}@{pc}")
            op, args, nxt, target = ins[pc]
            name = cmds[op][0]
            row = {"member": member, "pc": pc, "name": name, "args": args}
            if name in NATIVE:
                row.update(self.cpu.command(op, pc))
                nxt = row["cursor"]
            elif name == "End":
                self.trace.append(row)
                return pc
            elif name == "WhiteOut":
                row["stub"] = "whiteout scene boundary"
                self.trace.append(row)
                return pc
            elif name == "GetMenuChoice":
                if not self.choices:
                    raise RuntimeError("missing menu fixture")
                value = self.choices.pop(0)
                self.cpu.fixture_var(args[0], value)
                row["stub"] = {"menu_choice": value}
            elif name == "GetPlayerCoords":
                for i, v in zip(args, self.coords):
                    self.cpu.fixture_var(i, v)
                row["stub"] = {"coords": self.coords}
            elif name == "ShowPerson":
                row["stub"] = {"actor_creation_omitted": args[0]}
            elif name in ("TrainerBattle", "WildBattle", "MultiBattle"):
                if not self.outcomes:
                    raise RuntimeError("missing battle fixture")
                raw = self.outcomes.pop(0)
                self.cpu.w32(SPECIAL + 4 * 0x18, raw)
                row["stub"] = {"raw_battle_outcome": raw}
            elif name in self.outputs:
                values = self.outputs[name]
                for i, v in zip(args, values):
                    self.cpu.fixture_var(i, v)
                row["stub"] = {"output": values}
            elif name in SCENE:
                row["stub"] = "scene command omitted"
            else:
                raise RuntimeError(f"unsupported scene command {member}@{pc} {name}{args}")
            if "stub" in row:
                self.stubs.append({"member": member, "pc": pc, "name": name, "fixture": row["stub"]})
            self.trace.append(row)
            pc = nxt
        raise RuntimeError("script budget exhausted")

    def one(self, member, pc):
        b = bytes(self.source["scripts"][member])
        _, ins = R.disasm(b)
        self.run(member, pc, stop=(ins[pc][2],))

    def snapshot(self):
        return {
            "vars": {hex(i): self.cpu.var(i) for i in (0x4099, 0x409F, 0x40AB)},
            "flags": {str(i): self.cpu.flag(i) for i in (273, 546, 565, 1120, 1331, 2105, 2110, 2188)},
            "trace": self.trace,
            "stubs": self.stubs,
            "native_instruction_bytes": {hex(k): v for k, v in sorted(self.cpu.executed.items())},
        }


def coords(raw):
    p = 0
    n = struct.unpack_from("<I", raw, p)[0]
    p += 4 + 20 * n
    n = struct.unpack_from("<I", raw, p)[0]
    p += 4 + 32 * n
    n = struct.unpack_from("<I", raw, p)[0]
    p += 4 + 12 * n
    n = struct.unpack_from("<I", raw, p)[0]
    p += 4
    return [
        dict(
            zip(
                ("script", "x", "z", "width", "height", "level", "value", "var"),
                struct.unpack_from("<HhhHHHHH", raw, p + 16 * i),
            )
        )
        for i in range(n)
    ]
