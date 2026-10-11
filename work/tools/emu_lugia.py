"""Fresh-boot melonDS regression for D-2297 / lugia-animation-state-bounds.

Requires the user's Whirl Islands pre-scene battery save. Runs the real event from
map 244 (16,38), but replaces three battles/win checks with GoTo commands
in disposable script RAM. This is a cutscene diagnostic, not a normal playthrough.
No code, graphics, party or battery-save edits. Reports original prefetch abort or
completion of the fixed scene (story variable 0x40A4 = 8). Skipping battles does
not exercise their normal cleanup, so this diagnostic does not assert post-battle
walking; a normal battle replay is separate evidence.
Run from the repository root; see work/notes/lugia_freeze_fix_20261009.md.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path

SCRIPT_SHA256 = "df4d62fcd84657d7d1d54c4d512c757d89e0e8c4065751815adc4f9527c12a49"
SAVE_SHA256 = "6dcb4b9acd82a7dc349e3d7432445fb10f2c9d9dd52d51f08c86b9dd5f86f04d"
BATTLE_SKIPS = ((469, 494), (881, 906), (1270, 1295))


def identity(path):
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def scene_passes(report, expect):
    """Fail closed on missing evidence or unrelated faults, even at the final flag."""
    faults = report.get("exceptions", {})
    if any(k not in faults for k in ("data_aborts", "prefetch_aborts", "undefined")):
        return False
    if expect == "original":
        return (faults["prefetch_aborts"] > 0 and faults["data_aborts"] == 0 and
                faults["undefined"] == 0 and report.get("story_var") == 7 and
                any("prefetch abort (00001004)" in s for s in report.get("logs", [])))
    return (expect == "fixed" and report.get("story_var") == 8 and
            report.get("in_field") is True and
            tuple(report.get("position", ()))[:1] == (244,) and
            not any(faults[k] for k in ("data_aborts", "prefetch_aborts", "undefined")))


def run(rom, sav, out, expect):
    # Only native execution needs ROM parsing and the emulator harness. Keep the
    # scene oracle importable by the standard-library-only portable test gate.
    import ndspy.narc
    import ndspy.rom
    import emu_harness as E

    rom, sav, out = (Path(p).resolve() for p in (rom, sav, out))
    build_root = Path(__file__).resolve().parents[1] / "build"
    if not out.is_relative_to(build_root.resolve()) or out == build_root.resolve():
        raise ValueError("output must be a new directory inside work/build")
    out.mkdir(parents=True, exist_ok=False)
    inputs = {"rom": identity(rom), "save": identity(sav)}
    if inputs["save"]["sha256"] != SAVE_SHA256:
        raise ValueError("save differs from the reviewed pre-scene fixture")
    r = ndspy.rom.NintendoDSRom.fromFile(str(rom))
    script = bytes(ndspy.narc.NARC(r.getFileByName("a/0/1/2")).files[104])
    if hashlib.sha256(script).hexdigest() != SCRIPT_SHA256:
        raise ValueError("script 104 differs from the reviewed Origin v4.0.3 event")
    report = {"inputs": inputs, "expect": expect, "diagnostic_only": True,
              "battle_skips": BATTLE_SKIPS, "emulator": "melonDS", "pass": False}
    try:
        with E.Harness(str(rom), str(sav), out=out, emulator="melonds",
                       rtc=datetime.datetime(2026, 10, 9, 12), verbose=False) as h:
            h.boot_to_menu()
            h.continue_game()
            if h.position() != (244, 16, 38):
                raise ValueError(f"expected supplied Whirl Islands save, got {h.position()}")
            h.press("B", after=30)
            h.step_dir("UP")
            h.step(480)
            ram = h.read(0x02000000, 0x400000)
            offset = ram.find(script)
            if offset < 0 or ram.find(script, offset + 1) >= 0:
                raise ValueError("expected exactly one loaded copy of script 104")
            base = 0x02000000 + offset
            report["script_base"] = hex(base)
            report["edits"] = []
            for pc, dest in BATTLE_SKIPS:
                replacement = E.script_bytes(("GoTo", dest - pc - 6))
                report["edits"].append({"offset": pc, "destination": dest,
                                        "before": h.read(base + pc, 6).hex(),
                                        "after": replacement.hex()})
                h.write(base + pc, replacement)
            h.screenshot("start")
            for n in range(180):
                h.press("B", after=90)
                if n % 10 == 0:
                    h.screenshot(f"scene_{n:03}")
                if h.arm9_abort() or h.get_var(0x40A4) == 8:
                    break
            h.step(180)
            h.screenshot("result")
            report.update(frame=h.frame, position=h.position(),
                          story_var=h.get_var(0x40A4), in_field=h.in_field(),
                          exceptions=h.cpu_exceptions(), regs=h.melon.regs(),
                          logs=h.melon.log_lines())
            report["pass"] = scene_passes(report, expect)
            h.save_state(out / "result.ml1")
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    report["inputs_unchanged"] = inputs == {"rom": identity(rom), "save": identity(sav)}
    report["pass"] = report["pass"] and report["inputs_unchanged"]
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom", required=True)
    p.add_argument("--sav", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--expect", required=True, choices=("original", "fixed"))
    a = p.parse_args()
    return run(a.rom, a.sav, a.out, a.expect)


if __name__ == "__main__":
    raise SystemExit(main())
