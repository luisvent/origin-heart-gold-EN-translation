#!/usr/bin/env python3
"""Reward quantity check (fix reward-qty), one emulator run per case, DeSmuME.

Stands in the Viridian Pokemon Academy (zone 159) and runs a reward through the standard reward script (CallStd 2033),
recording the messages shown (NPCMsg ids), the BufferInt calls and the Bag before and after. Cases:
  academy   the teacher's real reward bytes (script file 859 @976-1037): 2 Ultra Balls, then items 493 and 494
  qty5      5 Potions (item 17) through CallStd 2033 (a quantity of more than 1 that is not the Academy)
  qty1      1 Potion through CallStd 2033 (must be unchanged by the fix)
  tm5       5 x TM28 (item 355, as the script file 761 reward does) through CallStd 2033 (TMs use the general message)
  key       the Rule Book (item 430, a key item) through CallStd 2033 (key items have their own message #28, unchanged)
  std2008   5 Potions through CallStd 2008 (the second standard reward script that shares the message block)
  fullbag   the academy reward with 999 Ultra Balls already in the Bag (the Bag cannot take 2 more)
Expected on the Chinese ROM and on a build without the fix (--without): the single-item message #25 whatever the
quantity. With the fix: #66 for the quantity cases (BufferInt slot 1 = the quantity), #25 / #28 as before for qty1 / tm.

    .venv/bin/python work/tools/emu_reward_qty.py --rom build.nds --out DIR [--without] [--sav SAVE] [--cases academy,...]
"""
import argparse
import datetime
import json
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "docs"))
import emu_harness as E

SEED = Path("work/build/memcheck/full_bag_6mons.sav")
OP_NPCMSG, OP_BUFINT, OP_BUFITEM = 45, 198, 194
ZONE, X, Y = 159, 6, 9                     # Viridian Pokemon Academy, inside the door
MSG_BANK, SCRIPT_FILE = 552, 859
ACADEMY_START, ACADEMY_END = 976, 1038     # NPCMsg 38 ... CloseMsg of the teacher's reward (script file 859)
CASES = {
    "academy": dict(),
    "qty5": dict(std=2033, item=17, qty=5),
    "qty1": dict(std=2033, item=17, qty=1),
    "tm5": dict(std=2033, item=355, qty=5, clear_tm=True),
    "key": dict(std=2033, item=430, qty=1),
    "std2008": dict(std=2008, item=17, qty=5),
    "fullbag": dict(full=True),
}
SINGLE, KEY, QTY = 25, 28, 66


def bag(h):
    """Every {item: qty} of the Bag pockets that matter here."""
    out = {}
    base = h.array(E.ARR_BAG)
    for name, (off, cap) in E.POCKETS.items():
        if name in ("items", "balls", "tm", "medicine"):
            raw = h.read(base + off, 4 * cap)
            for i in range(cap):
                item, qty = struct.unpack_from("<HH", raw, 4 * i)
                if item:
                    out[item] = out.get(item, 0) + qty
    return out


def program(spec):
    if "std" not in spec:
        import romdata as R
        data = R.Rom().d["scripts"][SCRIPT_FILE][ACADEMY_START:ACADEMY_END]
        return E.script_bytes(("LockAll",)) + data + E.script_bytes(("SetVar", E.SENTINEL_VAR, 0x5A5A), ("ReleaseAll",), ("End",))
    return E.script_bytes(("LockAll",), ("SetVar", 0x8004, spec["item"]), ("SetVar", 0x8005, spec["qty"]), ("CallStd", spec["std"]),
                          ("WaitButton",), ("CloseMsg",), ("SetVar", E.SENTINEL_VAR, 0x5A5A), ("ReleaseAll",), ("End",))


def run_case(rom, out, name, spec, sav=SEED):
    out.mkdir(parents=True, exist_ok=True)
    row = {"case": name, "msgs": [], "bufint": [], "bufitem": []}

    def edit(sf):
        if spec.get("clear_tm"):
            sf.set_pocket("tm", [])
        if spec.get("full"):
            sf.set_pocket("balls", [(2, 999)])

    with E.start_at(ZONE, X, Y, rom=rom, sav=sav, out=out, verbose=False, clock=datetime.datetime(2026, 10, 9, 12),
                    edit=edit, direction="DOWN") as h:
        h.press("B", after=30)
        table = 0x020F793C

        def on_msg(h):
            row["msgs"].append(h.u8(h.u32(h.reg.r0 + 8)))

        def on_int(h):
            p = h.u32(h.reg.r0 + 8)
            row["bufint"].append([h.u8(p), int.from_bytes(h.read(p + 1, 2), "little")])

        def on_item(h):
            p = h.u32(h.reg.r0 + 8)
            row["bufitem"].append([h.u8(p), int.from_bytes(h.read(p + 1, 2), "little")])

        h.on_exec(h.u32(table + 4 * OP_NPCMSG) & ~1, on_msg)
        h.on_exec(h.u32(table + 4 * OP_BUFINT) & ~1, on_int)
        h.on_exec(h.u32(table + 4 * OP_BUFITEM) & ~1, on_item)
        row["bag_before"] = bag(h)
        h.set_var(E.SENTINEL_VAR, 0)
        h.run_script(file=SCRIPT_FILE, index=0, msg_bank=MSG_BANK, program=program(spec), settle=60)
        shots = 0
        for _ in range(40):
            if h.get_var(E.SENTINEL_VAR) == 0x5A5A:
                break
            h.screenshot(f"msg{shots}")
            shots += 1
            h.press("A", after=60)
        h.step(60)
        row["finished"] = h.get_var(E.SENTINEL_VAR) == 0x5A5A
        h.screenshot("end")
        row["bag_after"] = bag(h)
    row["bag_delta"] = {str(k): v - row["bag_before"].get(k, 0) for k, v in row["bag_after"].items() if v != row["bag_before"].get(k, 0)}
    return row


def expected(name, row, without):
    msgs = row["msgs"]
    if not row["finished"]:
        return False
    if name == "academy" or name == "fullbag":
        # three GiveItem calls: 2 Ultra Balls, then one each of 493 and 494, then the teacher's closing line (51)
        singles = msgs.count(SINGLE)
        if without:
            return singles == 3 and QTY not in msgs and row["bufint"] == []
        return singles == 2 and msgs.count(QTY) == 1 and row["bufint"] == [[1, 0x8005]]
    if name in ("qty5", "std2008"):
        if without:
            return SINGLE in msgs and QTY not in msgs and row["bufint"] == [] and row["bag_delta"].get("17") == 5
        return QTY in msgs and SINGLE not in msgs and row["bufint"] == [[1, 0x8005]] and row["bag_delta"].get("17") == 5
    if name == "qty1":
        return SINGLE in msgs and QTY not in msgs and row["bufint"] == [] and row["bag_delta"].get("17") == 1
    if name == "tm5":
        if without:
            return SINGLE in msgs and QTY not in msgs and row["bufint"] == [] and row["bag_delta"].get("355") == 5
        return QTY in msgs and SINGLE not in msgs and row["bufint"] == [[1, 0x8005]] and row["bag_delta"].get("355") == 5
    if name == "key":
        return KEY in msgs and SINGLE not in msgs and QTY not in msgs and row["bufint"] == []
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--without", action="store_true", help="the ROM is the Chinese ROM or a build without the fix")
    ap.add_argument("--sav", default=str(SEED))
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
        r["expected"] = expected(name, r, a.without)
        ok &= r["expected"]
        rows.append(r)
        print(json.dumps(r), flush=True)
    (out / "result.json").write_text(json.dumps({"rom": str(rom), "without": a.without, "pass": ok, "rows": rows}, indent=1))
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
