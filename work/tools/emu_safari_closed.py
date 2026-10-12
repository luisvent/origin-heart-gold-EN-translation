#!/usr/bin/env python3
"""Safari Zone closure check (fix safari-zone-closed), one emulator run per case, DeSmuME.

Walks into the Safari Zone gate hall (leave the building and come back in, so the map loads with its NPCs), talks
to a gate counter or steps on a door tile, and records which script commands ran (NPCMsg ids, Warp) and the map
afterwards. Expected, on the Chinese ROM and on a build without the fix (--without): the pay counter reaches Warp
and the player ends on map 357; on the build with the fix: the closed notice (a027/0133#46) is shown, no Warp runs
and the player stays on map 173. The two door tiles (5,2) and (19,2) are in a staff area that cannot be reached on
foot (static collision), so those cases place the player next to the door and step on it.

    .venv/bin/python work/tools/emu_safari_closed.py --rom build.nds --out DIR [--without] [--cases pay,friend,link,dratini,door-left,door-right]
"""
import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_harness as E

SEED = Path("work/build/memcheck/full_bag_6mons.sav")
OP_NPCMSG, OP_WARP = 45, 176
CLOSED_MSG = 46
BARON_VAR = 0x4057        # Baoba's progress variable: 2 = the Geodude test is open
# case -> (how to get there, how to act)
CASES = {
    "pay": dict(go=("walk", 4, 6), face="UP", presses=26),
    "friend": dict(go=("walk", 18, 6), face="UP", presses=26),
    "link": dict(go=("walk", 21, 6), face="UP", presses=26),
    # control: the Dratini gift (script 11, offered while flag 1801 "Dragonair died" is clear) does not depend on the zone
    "dratini": dict(go=("walk", 7, 13), face="UP", presses=3),
    "door-left": dict(go=("place", 5, 4), face="UP", presses=0, steps=("UP", "UP", "UP")),
    "door-right": dict(go=("place", 19, 4), face="UP", presses=0, steps=("UP", "UP", "UP")),
}


def run_case(rom, out, name, spec, sav=SEED):
    out.mkdir(parents=True, exist_ok=True)
    kind, x, y = spec["go"]
    start = (173, x, y) if kind == "place" else (173, 4, 14)
    row = {"case": name, "msgs": [], "warps": 0}
    with E.start_at(start[0], start[1], start[2], rom=rom, sav=sav, out=out, verbose=False,
                    clock=datetime.datetime(2026, 10, 9, 12), flags=spec.get("flags", ()), vars={BARON_VAR: 2}, direction="DOWN" if kind == "walk" else "UP") as h:
        h.press("B", after=30)
        h.press("B", after=30)
        table = 0x020F793C

        def on_msg(h):
            row["msgs"].append(h.u8(h.u32(h.reg.r0 + 8)))

        def on_warp(h):
            row["warps"] += 1

        h.on_exec(h.u32(table + 4 * OP_NPCMSG) & ~1, on_msg)
        h.on_exec(h.u32(table + 4 * OP_WARP) & ~1, on_warp)
        if kind == "walk":
            for _ in range(3):                       # out of the building and back in: a normal map load
                h.step_dir("DOWN")
                if h.location()["map"] != 173:
                    break
            h.step(90)
            for _ in range(4):
                h.step_dir("UP")
                h.step(30)
                if h.location()["map"] == 173:
                    break
            h.step(90)
            if x == 4:                               # the corridor in front of the pay counter
                for _ in range(30):
                    if h.position()[2] <= y or not h.step_dir("UP"):
                        break
            else:
                h.walk_to(x, y)
            h.press(spec["face"], frames=3, after=10)
        h.screenshot("0_before")
        for i in range(spec["presses"]):
            h.press("A", after=45)
            if i < 4:
                h.screenshot(f"msg{i}")
        for d in spec.get("steps", ()):
            h.step_dir(d)
            h.step(20)
        h.step(200)
        h.screenshot("1_after")
        row["map"] = h.location()["map"]
        row["position"] = list(h.position()[1:])
        row["baoba_var"] = h.get_var(BARON_VAR)
        row["flags"] = {"1801": h.get_flag(1801), "1202": h.get_flag(1202)}
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--without", action="store_true", help="the ROM is the Chinese ROM or a build without the fix")
    ap.add_argument("--sav", default=str(SEED), help="a save with the Pokédex and a party (work/build/memcheck/full_bag_6mons.sav)")
    ap.add_argument("--row-only", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--cases", default=",".join(CASES))
    a = ap.parse_args()
    rom, out = Path(a.rom).resolve(), Path(a.out).resolve()
    rows, ok = [], True
    names = a.cases.split(",")
    for name in names:
        if len(names) > 1:
            # a second emulator in one process ends the process silently (seen 2026-10-12): one process per case
            proc = subprocess.run([sys.executable, __file__, "--rom", str(rom), "--out", str(out / name), "--sav", a.sav,
                                   "--cases", name, "--row-only"], capture_output=True, text=True)
            lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("{")]
            if not lines:
                raise SystemExit(f"case {name} produced no result:\n{proc.stdout[-800:]}\n{proc.stderr[-800:]}")
            r = json.loads(lines[-1])
        else:
            r = run_case(rom, out / name, name, CASES[name], Path(a.sav).resolve())
            if a.row_only:
                print(json.dumps(r), flush=True)
                return 0
        door = name.startswith("door")
        if name == "dratini":
            expect = 101 in r["msgs"] and CLOSED_MSG not in r["msgs"]
        elif a.without:
            # the pay counter and both doors lead in; the Link/friend counters stay on the hack's own
            # "cannot be used yet" message (no wireless), so only "no closed notice" is expected of them
            expect = CLOSED_MSG not in r["msgs"] and (name not in ("pay", "door-left", "door-right") or r["map"] == 357)
        else:
            expect = r["map"] == 173 and r["warps"] == 0 and (door or CLOSED_MSG in r["msgs"])
        r["expected"] = expect
        ok &= expect
        rows.append(r)
        print(json.dumps(r), flush=True)
    (out / "result.json").write_text(json.dumps({"rom": str(rom), "without": a.without, "pass": ok, "rows": rows}, indent=1))
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
