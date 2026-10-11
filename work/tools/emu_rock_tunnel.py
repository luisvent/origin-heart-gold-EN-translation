"""Focused native Rock Tunnel corner-child loss/win/reward verification.

Fresh private battery per run. Native object interactions and battle outcome;
no script/result/HP patch. --without expects the reproduced unfixed crash.
Strict snapshots reject open/decrypted or checksum-invalid transient records.
"""

import argparse
import datetime
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_harness as E
import msgtool as M

FLAGS = (1966, 1554, 1884, 1885, 1868)
SEED = Path("work/build/memcheck/full_bag_6mons.sav")


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def flags(h):
    return {str(f): h.get_flag(f) for f in FLAGS}


def match(h, samples):
    im = h.emu.screenshot().convert("RGB")
    return all(max(abs(a - b) for a, b in zip(im.getpixel(xy), rgb)) <= 24 for xy, rgb in samples)


PARTY_LIST = [((5, 197), (224, 208, 184)), ((250, 197), (224, 208, 184)), ((20, 362), (248, 248, 248))]
PARTY_SUBMENU = [((5, 197), (224, 208, 184)), ((20, 362), (56, 144, 224))]


class Log:
    def __init__(self, h, entry, expected):
        self.h = h
        self.events = []
        self.ctx = None
        self.base = None
        self.msg = None
        self.entry = entry
        self.expected = expected
        self.patch = None
        h.on_exec(E.TALK_OBJ_START, self.talk)
        h.on_exec(E.SCRIPT_STARTED, self.started)
        for op, name in [
            (17, "compare"),
            (28, "gotoif"),
            (30, "setflag"),
            (53, "close"),
            (213, "battle"),
            (219, "whiteout"),
            (220, "won"),
            (97, "release"),
            (2, "end"),
        ]:
            addr = h.u32(0x020F793C + op * 4) & ~1
            h.on_exec(addr, lambda h, op=op, name=name: self.command(h, op, name))
        h.on_exec(0x021EE288, lambda h: self.message(h))
        h.on_exec(0x02051B3C, lambda h: self.add(t="whiteout_task", r0=hex(h.reg.r0)))
        h.on_exec(
            0x02048E18,
            lambda h: self.add(t="won_result", won=h.reg.r0, battle_result=h.u32(h.reg.r4), destination=hex(h.reg.r5)),
        )

    def add(self, **kw):
        self.events.append(dict(frame=self.h.frame, **kw))

    def talk(self, h):
        if h.read(E.TALK_OBJ_START, 4) == bytes.fromhex(E.OV1_SIG[E.TALK_OBJ_START]):
            self.add(t="talk_object", script=h.reg.r1, object_ptr=hex(h.reg.r2))

    def started(self, h):
        ctx = h.reg.r4
        pc = h.u32(ctx + 8)
        if self.ctx is None:
            self.ctx = ctx
            self.base = pc - self.entry
            assert h.read(self.base + 2900, 4) == self.expected, "loaded script differs from ROM"
        self.add(t="script_started", ctx=hex(ctx), pc=hex(pc), offset=pc - self.base)

    def message(self, h):
        if h.read(0x021EE288, 8) != bytes.fromhex("18b581b0041ca268"):
            return
        ctx = h.reg.r0
        pc = h.u32(ctx + 8)
        self.msg = h.u8(pc)
        self.add(t="message", id=self.msg, offset=pc - 2 - self.base if self.base else None)

    def command(self, h, op, name):
        ctx = h.reg.r0
        if self.ctx is None or ctx != self.ctx:
            return
        pc = h.u32(ctx + 8)
        row = dict(t=name, offset=pc - 2 - self.base, ctx_head=h.read(ctx, 8).hex(), args=h.read(pc, 8).hex())
        if name == "battle":
            row["trainers"] = list(struct.unpack("<HH", h.read(pc, 4)))
        if name == "close":
            self.msg = None
        if name == "gotoif":
            row["target"] = pc + 5 + struct.unpack("<i", h.read(pc + 1, 4))[0] - self.base
        self.add(**row)
        if name in ("won", "gotoif", "compare"):
            ret = h.reg.lr & ~1

            def returned(h, ctx=ctx, name=name, ret=ret):
                self.add(
                    t=name + "_return", offset=h.u32(ctx + 8) - self.base, ctx_head=h.read(ctx, 8).hex(), r0=h.reg.r0
                )
                h.on_exec(ret, None)

            h.on_exec(ret, returned)


def strict_party(h):
    """Read all raw records at one paused boundary, then decode strictly.

    diagnostic=False rejects open native records AND checksum mismatches. Never
    repair, save or interpret a rejected transient as party evidence.
    """
    a = h.array(E.ARR_PARTY)
    count = h._party_count(a)
    raw = h.read(a + 8, 236 * count)
    rows = []
    for i in range(count):
        mon = E._save_core.compatibility_mon(
            E._save_core.request("decodePokemon", raw[i * 236 : (i + 1) * 236], diagnostic=False)
        )
        rows.append({k: mon[k] for k in ("species", "level", "hp", "stats", "moves", "pp", "checksum_ok", "flags")})
    assert h.read(a + 8, 236 * count) == raw, "party changed during snapshot"
    return rows


def snapshot(h, log):
    # Native whiteout frees the original script context. Only retain a cursor
    # that still points into this member; a freed context is not script evidence.
    cursor = h.u32(log.ctx + 8) if log.ctx else None
    offset = cursor - log.base if cursor is not None else None
    if offset is not None and not 0 <= offset < 6030:
        offset = None
    row = dict(
        frame=h.frame,
        field=h.in_field(),
        position=h.position(),
        pc=hex(h.reg.pc),
        flags=flags(h),
        money=h.u32(h.array(1) + 0x18),
        script_offset=offset,
    )
    try:
        row["party"] = strict_party(h)
    except ValueError as error:
        row["party"] = None
        row["party_unavailable"] = str(error)
    return row


def stable_party(h):
    for _ in range(300):
        try:
            return dict(frame=h.frame, party=strict_party(h))
        except ValueError:
            h.step(1)
    raise AssertionError("no strictly valid closed party in 300 frames")


def talk(h, entry, expected, *, battle=False):
    log = Log(h, entry, expected)
    h.press("A", after=10)
    for _ in range(45 if battle else 20):
        if battle and any(e["t"] == "battle" for e in log.events):
            break
        h.press("A", after=60)
    assert any(e["t"] == "talk_object" and e["script"] == (18 if entry == 1624 else 8) for e in log.events)
    assert any(e["t"] == "script_started" and e["offset"] == entry for e in log.events)
    return log


def finish_battle(h, log):
    for _ in range(100):
        if h.on_screen("battle_menu"):
            break
        h.press("B", after=30)
    if not h.on_screen("battle_menu"):
        h.screenshot("menu-not-reached")
        print("MENU_NOT_REACHED", json.dumps(log.events), flush=True)
        raise AssertionError("native command menu absent")
    h.screenshot("battle")
    nxt, idle = 1, 0
    for step in range(900):
        h.step(15)
        if any(e["t"] == "won" for e in log.events):
            return step
        if h.on_screen("battle_menu"):
            h.touch(*E.BATTLE_BUTTONS["fight"], frames=10, after=40)
            h.touch(*E.MOVE_BUTTONS[0], frames=10, after=60)
            idle = 0
        elif match(h, PARTY_LIST):
            h.touch(*E.PARTY_SLOTS[nxt], frames=10, after=60)
            if match(h, PARTY_SUBMENU):
                h.touch(128, 108, frames=10, after=90)
                if match(h, PARTY_SUBMENU):
                    h.press("B", after=40)
                    h.press("B", after=40)
            nxt, idle = nxt % 5 + 1, 0
        else:
            idle += 1
            if idle % 4 == 0:
                h.press("B", after=0)
            assert idle <= 160, "battle UI stopped progressing"
    raise AssertionError("battle exceeded finite 900-step bound")


def fixture(sf):
    # Other children already found: prove their progress survives either result.
    for f in FLAGS:
        sf.set_flag(f, f in (1554, 1884, 1885))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--without", action="store_true")
    p.add_argument("--win", action="store_true")
    a = p.parse_args()
    assert not (a.without and a.win), "baseline uses loss only"
    rom, out, seed = Path(a.rom).resolve(), Path(a.out).resolve(), SEED.resolve()
    out.mkdir(parents=True, exist_ok=True)
    member = M.Narc.parse(M.get_file(M.load_rom(rom), "a/0/1/2")).files[129]
    expected = bytes.fromhex("6e030000" if a.without else "56ffffff")
    assert member[2900:2904] == expected
    result = dict(
        rom=str(rom),
        rom_sha256=digest(rom),
        seed_sha256=digest(seed),
        without=a.without,
        win=a.win,
        fixture="native generated clones; other children found",
    )
    with E.start_at(
        None, rom=rom, sav=seed, out=out, verbose=False, clock=datetime.datetime(2026, 10, 9, 12), edit=fixture
    ) as h:
        h.generate_pokemon(129, level=5, item=0)
        party = h.array(E.ARR_PARTY)
        raw = h.read(party + 8 + 236 * h.generated_slot, 236)
        for i in range(6):
            h.write(party + 8 + 236 * i, raw)
        h.w32(party + 4, 6)
        for i in range(6):
            h.edit_party_mon(i, **E.moveset([150], [40]))
        if a.win:
            h.generate_pokemon(150, level=100, item=0)
            h.edit_party_mon(h.generated_slot, **E.moveset([94], [40]))
            h.swap_party(0, h.generated_slot)
        result["fixture_party"] = stable_party(h)
        print("FIXTURE", json.dumps(result["fixture_party"]), flush=True)
        h.warp(342, 43, 99, E.DIRS["UP"])
        h.step(60)
        result["before_flags"] = flags(h)
        h.screenshot("before")
        log = talk(h, 1624, expected, battle=True)
        print("NATIVE_BATTLE", json.dumps(log.events), flush=True)
        assert any(e.get("trainers") == [606, 0] and e["args"].startswith("5e0200000000") for e in log.events)
        result["battle_steps"] = finish_battle(h, log)
        print("BATTLE_COMPLETE", h.frame, flush=True)
        result["exit_start"] = snapshot(h, log)
        result["postbattle_trace"] = []
        for i in range(40):
            h.press("B", after=60)
            result["postbattle_trace"].append(snapshot(h, log))
            if i in (0, 9, 19, 39):
                h.screenshot("post-" + str(i))
        result["after"] = snapshot(h, log)
        h.screenshot("after")
        h.save_state(out / "after.dst")
        result["events"] = list(log.events)
        assert any(e["t"] == "won_result" and e["won"] == int(a.win) for e in log.events)
        if a.without:
            assert any(e["t"] == "gotoif" and e["offset"] == 2897 and e["target"] == 3782 for e in log.events)
            assert not any(e["t"] == "whiteout" for e in log.events)
            assert not h.in_field() and h.position()[0] == 342
            assert flags(h) == result["before_flags"]
            result["closed_after_loss"] = stable_party(h)
            assert all(m["hp"] == 0 for m in result["closed_after_loss"]["party"])
        elif a.win:
            assert h.in_field() and flags(h) == dict(result["before_flags"], **{"1966": True})
            assert any(e["t"] == "message" and e["id"] == 76 for e in log.events)
            assert any(e["t"] == "setflag" and e["offset"] == 2911 for e in log.events)
            assert not any(e["t"] == "whiteout" for e in log.events)
            second = talk(h, 1624, expected)
            result["already_won"] = dict(events=second.events, after=snapshot(h, second))
            assert not any(e["t"] == "battle" for e in second.events)
            assert any(e["t"] == "message" and e["id"] == 76 for e in second.events)
            assert flags(h) == result["after"]["flags"]
            result["reward_gate_verification"] = "structural: entire native reward region unchanged"
        else:
            assert any(e["t"] == "gotoif" and e["offset"] == 2897 and e["target"] == 2734 for e in log.events)
            assert any(e["t"] == "whiteout" and e["offset"] == 2734 for e in log.events)
            assert any(e["t"] == "whiteout_task" for e in log.events)
            assert h.in_field() and h.position()[0] == 501
            assert flags(h) == result["before_flags"]
            result["healed_closed_party"] = stable_party(h)
            assert all(m["hp"] == m["stats"][0] > 0 for m in result["healed_closed_party"]["party"])
            old = h.position()
            h.walk("DOWN", 1)
            h.step(60)
            result["movement"] = dict(before=old, after=h.position())
            assert old != h.position(), "player control not restored"
            h.warp(342, 43, 99, E.DIRS["UP"])
            h.step(60)
            retry = talk(h, 1624, expected, battle=True)
            result["retry"] = dict(events=retry.events, flags=flags(h))
            assert any(e.get("trainers") == [606, 0] for e in retry.events)
            assert flags(h) == result["before_flags"]
        result["seed_unchanged"] = digest(seed) == result["seed_sha256"]
        assert result["seed_unchanged"]
        result["passed"] = True
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(
            "PASS",
            json.dumps({k: result[k] for k in ("rom_sha256", "without", "win", "passed", "seed_unchanged")}),
            flush=True,
        )


if __name__ == "__main__":
    main()
