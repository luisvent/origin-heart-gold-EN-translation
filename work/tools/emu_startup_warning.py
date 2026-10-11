#!/usr/bin/env python3
"""Verify the user-approved startup warning on a built English ROM.

Blank battery, ordinary buttons/touch only; execution hooks observe message reads.
Screenshots and a JSON report go under --out. Requires the existing emulator venv.
Run from the repo root:
    python work/tools/emu_startup_warning.py --rom BUILD.nds --out work/build/startup-warning
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_harness import Harness

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--rom", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
out = Path(args.out).resolve()
out.mkdir(parents=True, exist_ok=True)
rom = Path(args.rom).resolve()
with Harness(rom=rom, out=out) as h:
    rows = []

    def readmsg(_):
        if h.u16(h.reg.r0 + 6) == 816:
            rows.append({"frame": h.frame, "id": h.reg.r1, "caller": hex(h.reg.lr)})

    h.on_exec(0x0200BB0C, readmsg)
    h.on_exec(0x0200BB40, readmsg)
    h.step(2400)
    h.press("START", after=90)
    h.press("START", after=400)
    h.emu.screenshot().save(out / "01-warning.png")
    # A held before the timer expires must not leave the first notice.
    h.hold("A")
    h.step(90)
    h.release("A")
    assert [r["id"] for r in rows if r["id"] < 5] == [4], rows
    h.step(600)
    for n, label in enumerate(["welcome-and-credit", "mechanics", "free-and-attribution", "credits"], 2):
        h.press("A", after=650)
        h.emu.screenshot().save(out / f"{n:02}-{label}.png")
    assert [r["id"] for r in rows if r["id"] < 5] == [4, 0, 1, 2, 3], rows
    assert not any(r["id"] == 8 for r in rows), rows
    assert rows[-1]["id"] == 7, rows[-4:]
    h.press("A", after=240)
    h.emu.screenshot().save(out / "06-after-notices.png")
    for n in range(70):
        h.touch(128, 153, after=4)
        h.press("A", after=56)
    h.emu.screenshot().save(out / "07-new-game.png")
    (out / "report.json").write_text(
        json.dumps(
            {
                "reads": rows,
                "page_order": [4, 0, 1, 2, 3],
                "early_held_a_stayed_on_warning": True,
                "qr_caption_reads": 0,
                "frames": h.frame,
            },
            indent=2,
        )
    )
    print("PASS notice order, early held A, no caption read, final start prompt", flush=True)
