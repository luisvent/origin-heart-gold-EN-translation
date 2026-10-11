"""Native post-battle collector replay using isolated valid party fixtures.

Run from the worktree root. No production saves are edited. RNG seeds are
controlled only at collector entry to prove successful/failed award paths.
"""

import argparse
import datetime
import hashlib
import json
import subprocess
from pathlib import Path
import emu_harness as E

ENTRY = 0x0222BCC8
GLOBAL = 0x02255BAC


def qty(h, item):
    base = h.array(E.ARR_BAG)
    return sum(
        h.u16(base + off + 4 * i + 2)
        for off, n in E.POCKETS.values()
        for i in range(n)
        if h.u16(base + off + 4 * i) == item
    )


def assert_rewards(row, baseline=False):
    """Check both inventory changes and the reward list consumed by battle messages."""
    case = row["case"]
    no_honey = case in ("held", "full", "failed-roll") or baseline and case in ("win", "trainer", "multiple")
    if not baseline and case in ("win", "trainer", "multiple"):
        assert row["after"] == row["before"] + 1, row
        assert row["returns"][0]["count"] == 1, row
    if no_honey:
        assert row["after"] == row["before"], row
    if no_honey or case == "pickup-full" and not baseline:
        # Require a complete observed call, not a vacuous pass on an empty trace.
        assert len(row["entries"]) == len(row["returns"]) == 1, row
        expected = dict(count=0, items=[0] * len(row["party_before"]))
        assert row["returns"][0] == expected, row
        # A full stack attempts one insertion and gets rejected. Ineligible or
        # failed-roll cases must not reach Bag_AddItem at all.
        item = 11 if case == "pickup-full" else 94 if case == "full" and not baseline else None
        expected_calls = [] if item is None else [dict(item=item, qty=1)]
        assert row["bag_calls"] == expected_calls, row
    if case == "flee":
        assert row["after"] == row["before"] and not row["entries"] and not row["returns"], row
    if case.startswith("pickup"):
        full = case == "pickup-full"
        assert row["pickup_after"] == row["pickup_before"] + (0 if full else 1), row
        assert row["returns"][0]["count"] == (1 if baseline or not full else 0), row


def run(args):
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rom = Path(args.rom).resolve()
    seed = Path(args.save).resolve()
    result = dict(
        rom=str(rom),
        sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),
        seed_sha256=hashlib.sha256(seed.read_bytes()).hexdigest(),
        cases=[],
    )
    try:
        prepared = Path(args.prepared).resolve() if args.prepared else out / "prepared.sav"
        if not args.prepared:
            with E.start_at(109, 16, 14, rom=rom, sav=seed, clock=datetime.datetime(2026, 10, 10, 12), out=out) as h:
                records = []
                for species, level in [(150, 100), (415, 31), (415, 31)]:
                    mon = h.generate_pokemon(species, level=level, item=0)
                    party = h.array(E.ARR_PARTY)
                    records.append(h.read(party + 8 + 236 * mon["slot"], 236))
                records[0] = E.encode_pokemon(records[0], **E.moveset([94, 0, 0, 0], [10, 0, 0, 0]))
                records[1] = E.encode_pokemon(records[1], ability=118)
                records[2] = E.encode_pokemon(records[2], ability=118)
                for i, raw in enumerate(records):
                    (out / f"mon-{i}.bin").write_bytes(raw)
            prepared = out / "prepared.sav"
            subprocess.run(
                [
                    "node",
                    "--input-type=module",
                    "-e",
                    "import fs from 'node:fs'; import {patchPartyRecord} from './work/save-core/dist/save.js'; "
                    "let b=fs.readFileSync(process.argv[1]); for(let i=0;i<3;i++) b=patchPartyRecord(b,i,fs.readFileSync(process.argv[2]+'/mon-'+i+'.bin')); "
                    "fs.writeFileSync(process.argv[2]+'/prepared.sav',b);",
                    str(seed),
                    str(out),
                ],
                check=True,
            )
        if args.prepare_only:
            return result
        result["prepared_sha256"] = hashlib.sha256(prepared.read_bytes()).hexdigest()
        for case in args.cases.split(","):

            def prepare(sf):
                sf.set_party_count(3 if case == "multiple" else 2)
                if case == "held":
                    sf.edit_party_mon(1, item=94)
                if case.startswith("pickup"):
                    sf.edit_party_mon(1, ability=53, item=1)
                sf.set_pocket("items", [(94, 999 if case == "full" else 1)])
                if case.startswith("pickup"):
                    sf.set_pocket("balls", [(11, 999 if case == "pickup-full" else 1)])

            with E.start_at(
                109, 16, 14, rom=rom, sav=prepared, clock=datetime.datetime(2026, 10, 10, 12), out=out, edit=prepare
            ) as h:
                state = {"row": None, "inside": False, "out": 0}

                def enter(h):
                    row = state["row"]
                    state["inside"] = True
                    state["out"] = h.reg.r2
                    row["entries"].append(dict(lr=hex(h.reg.lr), side=h.reg.r1))
                    # At seed 0 the native generator returns 0, guaranteeing the
                    # first eligible chance roll. Seed 1 returns 38 (> Lv31's 20%).
                    h.w32(h.u32(GLOBAL) + 0x24C, 1 if row["case"] == "failed-roll" else 0)

                def leave(h):
                    if state["inside"]:
                        state["row"]["returns"].append(
                            dict(
                                count=h.reg.r0,
                                items=[h.u16(state["out"] + 2 * i) for i in range(len(state["row"]["party_before"]))],
                            )
                        )
                        state["inside"] = False

                def bag(h):
                    if state["inside"]:
                        state["row"]["bag_calls"].append(dict(item=h.reg.r1, qty=h.reg.r2))

                def mon_read(h):
                    if state["inside"]:
                        state["row"].setdefault("mon_reads", []).append(
                            dict(
                                ptr=hex(h.reg.r0),
                                field=h.reg.r1,
                                header=h.read(h.reg.r0, 8).hex(),
                            )
                        )

                h.on_exec(0x0206D848, mon_read)
                h.on_exec(ENTRY, enter)
                h.on_exec(0x02203140, leave)
                h.on_exec(0x022034F8, leave)
                h.on_exec(0x02076A08, bag)
                row = dict(
                    case=case,
                    before=qty(h, 94),
                    pickup_before=qty(h, 11),
                    entries=[],
                    returns=[],
                    bag_calls=[],
                    party_before=h.party(),
                )
                state.update(row=row, inside=False)
                result["cases"].append(row)
                command = ("TrainerBattle", 185, 0, 1, 0) if case == "trainer" else ("WildBattle", 19, 5, 0)
                h.run_script(program=E.script_bytes(("LockAll",), command, ("ReleaseAll",), ("End",)))
                for _ in range(140):
                    h.step(30)
                    if h.on_screen("battle_menu"):
                        break
                    h.press("A", after=4)
                assert h.on_screen("battle_menu"), "battle menu absent"
                if case == "flee":
                    h.touch(*E.BATTLE_BUTTONS["run"], frames=10, after=60)
                    for _ in range(100):
                        h.press("B", after=30)
                        if h.in_field():
                            break
                else:
                    h.fight([0], max_turns=12)
                h.step(90)
                assert h.in_field(), "did not return to field"
                row["after"] = qty(h, 94)
                row["pickup_after"] = qty(h, 11)
                row["party_after"] = h.party()
                assert all(m["checksum_ok"] and not m["bad_egg"] for m in row["party_after"]), (
                    "invalid party after battle"
                )
                row["screenshot"] = str(h.screenshot(case + "-after"))
                row["field"] = True
                assert_rewards(row, baseline=args.baseline)
                assert row["party_after"][1]["item"] == (
                    94 if case == "held" else 1 if case.startswith("pickup") else 0
                )
                (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    finally:
        if result.get("prepared_sha256"):
            result["prepared_unchanged"] = (
                hashlib.sha256(prepared.read_bytes()).hexdigest() == result["prepared_sha256"]
            )
        result["seed_unchanged"] = hashlib.sha256(seed.read_bytes()).hexdigest() == result["seed_sha256"]
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--rom", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--save", default=str(E.DEF_SAVES / "full_bag_6mons.sav"))
    p.add_argument(
        "--cases",
        default="win",
        choices=["win", "held", "full", "failed-roll", "trainer", "flee", "multiple", "pickup", "pickup-full"],
        help="One case per process (DeSmuME cannot safely restart).",
    )
    p.add_argument("--prepared")
    p.add_argument("--prepare-only", action="store_true")
    p.add_argument("--baseline", action="store_true")
    args = p.parse_args()
    if not args.prepare_only and (not args.prepared or "," in args.cases):
        p.error("First use --prepare-only, then --prepared SAVE and one --cases value per process")
    run(args)
