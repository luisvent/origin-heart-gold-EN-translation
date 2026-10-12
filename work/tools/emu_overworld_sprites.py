#!/usr/bin/env python3
"""emu_overworld_sprites - see the overworld-pokemon-sprites fix in the emulator.

Boots a ROM from a battery save, teleports the player next to a door of a map that has a stationary Pokemon with a
vanilla sprite id, walks out and back in (so the map loads with its objects), walks to a spot where the Pokemon is
on screen and saves the top screen. Run it on the Chinese ROM, on a build without the fix and on a build with it:

    <venv>/bin/python work/tools/emu_overworld_sprites.py --rom ROM.nds --out DIR [--case pewter,lighthouse]
        [--sav work/build/memcheck/full_bag_6mons.sav] [--compare OTHER_DIR]

Cases (event member / object, the Pokemon the object says it is):
    pewter       Pewter Pokemon Center, zone 475, Jigglypuff (events 428 object 5, 1004 -> 468): Patrat before
    lighthouse   Olivine Lighthouse light room, zone 225, Ampharos (events 211 objects 1, 2, 1031 -> 612): Audino before

Writes <out>/<case>.png (the 256x192 top screen) and <out>/overworld_sprites.json (sha256 of each). With --compare the
pixels of a case are compared with the same case of another run's folder (a build without the fix, the Chinese ROM).
Nothing is written next to the ROM or the save. See work/notes/overworld-pokemon-sprite-mismatch_fix.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

# case -> (zone, start x, z, leave, enter, target x, z)
CASES = {
    "pewter": (475, 8, 18, "DOWN", "UP", 6, 15),
    "lighthouse": (225, 9, 9, "DOWN", "UP", 9, 9),
    "pewter-talk": (475, 8, 18, "DOWN", "UP", 5, 14),   # also talks to the Pokemon: text box and PlayCry species
    "cianwood-talk": (236, 8, 18, "DOWN", "UP", 10, 14),                  # Pokemon Center Unown (cry Flaaffy -> Unown)
}
PLAYCRY_CALL = 0x020487F0   # arm9: `bl` to the cry player inside the PlayCry script command; r1 = species, r2 = form


def default_sav() -> str:
    """work/build/memcheck/full_bag_6mons.sav of this checkout, else of the main checkout (a git worktree has no work/build)."""
    rel = Path("work") / "build" / "memcheck" / "full_bag_6mons.sav"
    here = TOOLS.parent.parent / rel
    if here.exists():
        return str(here)
    import subprocess
    try:
        common = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=TOOLS, capture_output=True, text=True,
                                check=True).stdout.strip()
        main = (Path(common) if Path(common).is_absolute() else TOOLS / common).resolve().parent / rel
        if main.exists():
            return str(main)
    except (OSError, subprocess.CalledProcessError):
        pass
    return str(here)


def run_case(rom: str, sav: str, out: Path, name: str) -> dict:
    from emu_harness import Harness, SaveFile
    zone, px, pz, leave, enter, tx, tz, *face = CASES[name]
    sf = SaveFile(sav)
    sf.place_player(zone, px, pz, leave)
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        path = os.path.join(tmp, "t.sav")
        sf.write(path)
        with Harness(rom, path, out=out, verbose=False) as h:
            h.set_clock(datetime(2026, 10, 9, 12))
            h.boot_to_menu()
            h.continue_game()
            h.step(60)
            h.walk(leave, 1)
            h.step(200)             # through the door: the other map loads
            h.walk(enter, 1)
            h.step(200)             # and back in: the map loads normally, with its objects
            arrived = h.walk_to(tx, tz)
            h.step(30)
            cries = []
            if name.endswith("-talk"):
                h.on_exec(PLAYCRY_CALL, lambda m: cries.append(m.reg.r1))
                h.walk(face[0] if face else "UP", 1)         # blocked by the Pokemon: only turns
                h.press("A", frames=6)
                h.step(150)
            shot = h.screenshot(name)
    from PIL import Image
    top = Image.open(shot).crop((0, 0, 256, 192))
    top.save(shot)
    return {"case": name, "arrived": bool(arrived), "png": str(shot), "sha256": hashlib.sha256(top.tobytes()).hexdigest(),
            "playcry_species": cries}


def diff_fraction(a: str, b: str) -> float:
    from PIL import Image, ImageChops
    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    d = ImageChops.difference(ia, ib).convert("L").point(lambda v: 255 if v else 0)
    return sum(1 for v in d.getdata() if v) / (ia.width * ia.height)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--case", default=",".join(CASES))
    ap.add_argument("--sav", default=default_sav())
    ap.add_argument("--compare", help="another run's folder: print the fraction of differing pixels per case")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cases = a.case.split(",")
    if len(cases) == 1:
        rows = [run_case(a.rom, a.sav, out, cases[0])]
    else:
        # one emulator per process: DeSmuME does not start a second time in the same process
        import subprocess
        rows = []
        for c in cases:
            subprocess.run([sys.executable, str(Path(__file__).resolve()), "--rom", a.rom, "--out", a.out, "--sav", a.sav,
                            "--case", c], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            f = out / f"{c}.json"
            rows.append(json.loads(f.read_text()) if f.exists() else {"case": c, "arrived": False, "png": None, "sha256": None})
    if len(cases) == 1:
        (out / f"{cases[0]}.json").write_text(json.dumps(rows[0]))
    for r in rows:
        if a.compare and r["png"]:
            other = Path(a.compare) / f"{r['case']}.png"
            r["diff_fraction_vs_compare"] = diff_fraction(r["png"], str(other)) if other.exists() else None
        print(json.dumps(r))
    if len(cases) > 1:
        (out / "overworld_sprites.json").write_text(json.dumps(rows, indent=1))
    return 0 if all(r["arrived"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
