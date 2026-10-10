#!/usr/bin/env python3
"""Bounded fresh-boot Struggle regression. Run from repository root, one emulator at a time.

Uses private generated party records and injected TrainerBattle commands. Captures native
battle HP/action/PP without decrypting transient party records. No natural story route claimed.
"""

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import emu_harness as E

G = 0x02255B90


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def snapshot(h, a):
    return {
        "ptr": hex(a),
        "number": h.u8(a + 0x14),
        "hp": h.u16(a + 0x1E),
        "maxhp": h.u16(a + 0x1C),
        "moves": [h.u16(a + 0x25A + 18 * i) for i in range(4)],
        "pp": [h.u8(a + 0x25C + 18 * i) for i in range(4)],
    }


def active(h):
    return h.u32(h.u32(G + 4) + 0x1F4)


class Trace:
    def __init__(self, h):
        self.h = h
        self.rows = []
        self.actors = {}
        self.hp = {}
        self.phase = ""
        self.enemy = False
        self.exhausted = set()
        h.on_exec(0x0222C550, self.guard)
        h.on_exec(0x0221D7A8, self.action)
        h.on_exec(0x0222C304, self.usability)
        h.on_frame(self.watch)

    def add(self, kind, **kw):
        self.rows.append(dict(kind=kind, frame=self.h.frame, phase=self.phase, **kw))

    def remember(self, a):
        self.actors[a] = snapshot(self.h, a)
        self.hp.setdefault(a, self.h.u16(a + 0x1E))

    def guard(self, h):
        a = h.reg.r0
        self.remember(a)
        if self.enemy and h.u8(a + 0x14) & 0x8 and a not in self.exhausted:
            for i in range(4):
                h.w8(a + 0x25C + 18 * i, 0)
            self.exhausted.add(a)
            self.add("enemy_fixture", actor=snapshot(h, a))
        self.add("guard", lr=hex(h.reg.lr), actor=snapshot(h, a))

    def action(self, h):
        a = h.reg.r0
        self.remember(a)
        self.add(
            "action",
            actor=snapshot(h, a),
            move=h.u16(h.reg.r1),
            selected=h.u16(h.reg.r1 + 2),
            record=h.read(h.reg.r1, 16).hex(),
        )

    def usability(self, h):
        self.add("usability", actor=snapshot(h, h.reg.r0), move=h.reg.r1)

    def watch(self, h):
        for a, old in list(self.hp.items()):
            now = h.u16(a + 0x1E)
            if now != old:
                self.add("hp_change", ptr=hex(a), number=h.u8(a + 0x14), before=old, after=now)
                self.hp[a] = now


def advance(h, t, out, frames=4200):
    last = None
    for i in range(0, frames, 15):
        h.step(15)
        if h.in_field():
            return "field"
        if h.on_screen("battle_menu"):
            h.step(20)
            return "menu"
        box = h.emu.screenshot().crop((0, 140, 256, 190)).tobytes()
        if box != last and len(t.rows) < 6000:
            last = box
            if i % 60 == 0:
                h.screenshot(f"{t.phase}-{i}")
        if i % 60 == 45:
            h.press("A", after=0)
    h.screenshot(t.phase + "-timeout")
    return "timeout"


def run_turn(h, t, out, case, turn, without):
    """Play a turn, or verify the original engine rejected an exhausted move."""
    start = len(t.rows)
    before = snapshot(h, active(h))
    slot = 2 if case == "positive" else 0
    h.touch(*E.BATTLE_BUTTONS["fight"], frames=10, after=40)
    h.screenshot(t.phase + "-fight")
    if case in ("positive", "last-pp", "enemy") or without:
        h.touch(*E.MOVE_BUTTONS[slot], frames=10, after=60)
    rejected = without and (
        case not in ("positive", "last-pp", "enemy") or (case == "last-pp" and turn == 1)
    )
    if rejected:
        for _ in range(8):
            h.press("B", after=30)
        observed = t.rows[start:]
        assert any(
            r["kind"] == "usability" and r["actor"]["number"] == before["number"]
            and r["move"] == before["moves"][slot] for r in observed
        ), case + " exhausted move usability check absent"
        assert not any(r["kind"] == "action" for r in observed), case + " exhausted move unexpectedly submitted"
        assert h.on_screen("battle_menu"), case + " rejection did not return to command menu"
        after = snapshot(h, active(h))
        assert after["number"] == before["number"], case + " rejection changed active battler"
        assert before["pp"] == after["pp"] == [0] * 4, case + " rejection changed exhausted PP"
        return "rejected"
    if case == "double":
        assert h.wait_screen("battle_menu", 600), "partner command absent"
        h.touch(*E.BATTLE_BUTTONS["fight"], frames=10, after=40)
        h.touch(*E.MOVE_BUTTONS[0], frames=10, after=60)
    return advance(h, t, out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rom", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--cases", default="four-zero,one-zero,positive,last-pp,trainer5,double,enemy")
    p.add_argument("--without", action="store_true")
    args = p.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rom = Path(args.rom).resolve()
    seed = Path("work/build/memcheck/full_bag_6mons.sav").resolve()
    result = {"rom": str(rom), "rom_sha256": digest(rom), "seed_sha256": digest(seed), "cases": []}
    with E.start_at(109, 16, 14, rom=rom, sav=seed, clock=datetime.datetime(2026, 10, 9, 12), out=out) as h:
        mons = [h.generate_pokemon(92, level=20, item=0) for _ in range(2)]
        party = h.array(E.ARR_PARTY)
        records = [h.read(party + 8 + 236 * m["slot"], 236) for m in mons]
        for i, raw in enumerate(records):
            h.write(party + 8 + 236 * i, raw)
        h.w32(party + 4, 2)
        h.party()
        h.save_state(out / "field.dst")
        t = Trace(h)
        for case in args.cases.split(","):
            h.load_state(out / "field.dst")
            t.rows = []
            t.actors = {}
            t.hp = {}
            t.exhausted = set()
            t.enemy = case == "enemy"
            t.phase = case + "-intro"
            h.w32(party + 4, 2 if case == "double" else 1)
            moves = [122, 101, 247, 310]
            pp = [0] * 4
            if case == "one-zero":
                moves = [122, 0, 0, 0]
            if case == "positive":
                pp = [0, 0, 1, 0]
            if case in ("last-pp", "enemy"):
                moves = [45, 0, 0, 0]
                pp = [1, 0, 0, 0] if case == "last-pp" else [40, 0, 0, 0]
            h.edit_party_mon(0, **E.moveset(moves, pp))
            if case == "double":
                h.edit_party_mon(1, **E.moveset([45, 0, 0, 0], [40, 0, 0, 0]))
            fixture = h.party()
            cmd = (
                ("TrainerBattle", 6, 6, 0, 0)
                if case == "double"
                else ("TrainerBattle", 5 if case == "trainer5" else 185, 0, 0 if case == "trainer5" else 1, 0)
            )
            h.run_script(program=E.script_bytes(("LockAll",), cmd, ("ReleaseAll",), ("End",)))
            for _ in range(100):
                h.step(30)
                if h.on_screen("battle_menu"):
                    break
                h.press("A", after=4)
            assert h.on_screen("battle_menu"), case + " command absent"
            h.step(20)
            h.screenshot(case + "-command")
            h.save_state(out / (case + "-command.dst"))
            row = {"case": case, "fixture": fixture, "initial": snapshot(h, active(h)), "turns": []}
            if case == "positive":
                t.phase = "positive-zero-slot-rejection"
                start = len(t.rows)
                h.touch(*E.BATTLE_BUTTONS["fight"], frames=10, after=40)
                h.touch(*E.MOVE_BUTTONS[0], frames=10, after=60)
                h.screenshot("positive-zero-slot-rejected")
                for _ in range(8):
                    h.press("B", after=30)
                rejected = t.rows[start:]
                assert any(r["kind"] == "usability" and r["move"] == 122 for r in rejected)
                assert not any(r["kind"] == "action" for r in rejected)
                row["zero_slot_rejection"] = rejected
                h.load_state(out / (case + "-command.dst"))
            for turn in range(2 if case == "last-pp" else 1):
                t.phase = f"{case}-turn{turn + 1}"
                start = len(t.rows)
                outcome = run_turn(h, t, out, case, turn, args.without)
                row["turns"].append(
                    {
                        "outcome": outcome,
                        "trace": t.rows[start:],
                        "final": None if outcome == "field" else snapshot(h, active(h)),
                    }
                )
                h.screenshot(t.phase + "-after")
                assert outcome != "timeout", case + " turn timeout"
                actions = [r for r in t.rows[start:] if r["kind"] == "action"]
                player = [r["move"] for r in actions if r["actor"]["number"] == 1]
                if args.without and outcome == "rejected":
                    assert not actions, case + " exhausted move unexpectedly submitted"
                elif case == "positive":
                    assert player == [247] and row["turns"][-1]["final"]["pp"] == [0] * 4
                elif case == "last-pp":
                    assert player == [45 if turn == 0 else 165]
                    assert row["turns"][-1]["final"]["pp"] == [0] * 4
                elif case == "enemy":
                    assert any(r["move"] == 165 and r["actor"]["number"] == 13 for r in actions)
                else:
                    assert player == [165], case + " did not submit native Struggle"
                    changes = [r for r in t.rows[start:] if r["kind"] == "hp_change"]
                    assert any(r["number"] == 1 and r["after"] < r["before"] for r in changes), case + " recoil absent"
                    assert any(r["number"] & 8 and r["after"] < r["before"] for r in changes), (
                        case + " foe damage absent"
                    )
            row["trace_intro"] = t.rows[
                : next((i for i, r in enumerate(t.rows) if r["phase"].endswith("turn1")), len(t.rows))
            ]
            result["cases"].append(row)
            (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
            print(
                "CASE",
                case,
                [
                    (
                        x["outcome"],
                        [(r["actor"]["number"], r["move"]) for r in x["trace"] if r["kind"] == "action"],
                        [r for r in x["trace"] if r["kind"] == "hp_change"],
                    )
                    for x in row["turns"]
                ],
                flush=True,
            )
        result["seed_unchanged"] = digest(seed) == result["seed_sha256"]
        assert result["seed_unchanged"]
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
