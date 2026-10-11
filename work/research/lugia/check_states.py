"""Isolated melonDS animation dispatcher comparison on a reviewed Lugia checkpoint.

Savestates include code: only the dispatcher is synchronized from each input ROM.
This is an isolated routine test, not a fresh boot of the supplied candidate ROM.
Use emu_lugia.py for the separate fresh-boot cutscene check.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import emu_harness as E
import ndspy.rom

TABLE = 0x02208F70
DISPATCH = 0x021F80E0
OBJ = 0x022A300C  # reviewed appearance checkpoint: object 13, special-model sprite 426
STATES = (0, 1, 2, 3, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(a):
    out = Path(a.out).resolve()
    root = Path(__file__).resolve().parents[2] / "build"
    if not out.is_relative_to(root.resolve()) or out == root.resolve():
        raise ValueError("output must be a new directory inside work/build")
    out.mkdir(parents=True, exist_ok=False)
    paths = {k: getattr(a, k) for k in ("rom", "control", "state", "sav")}
    report = {"isolated_checkpoint_test": True, "inputs": {k: digest(p) for k, p in paths.items()},
              "rows": [], "pass": False}
    blocks = {}
    for k in ("rom", "control"):
        overlay = ndspy.rom.NintendoDSRom.fromFile(paths[k]).loadArm9Overlays()[1]
        blocks[k] = bytes(overlay.data[DISPATCH - overlay.ramAddress:DISPATCH - overlay.ramAddress + 24])
    if blocks["rom"] == blocks["control"]:
        raise ValueError("candidate and control dispatchers must differ")
    try:
        with E.Harness(a.rom, a.sav, out=out, emulator="melonds", verbose=False) as h:
            priv = OBJ + 0x108

            def observe(state):
                gfx = h.u32(priv)
                def model():
                    return {"cache": h.u32(priv + 0x10), "anim": h.u16(gfx + 0xB6),
                            "frame": h.u32(gfx + 0xB8)}
                h.w32(OBJ + 0xA0, state)
                before = model()
                h.melon.clear_exceptions()
                h.melon.watch(TABLE, 16, read=True, write=False)
                h.step(3)
                hits = h.melon.watch_hits()
                row = {"state": state, "before": before, "after": model(), "hits": list(hits),
                       "dropped": hits.dropped, "state_after": h.u32(OBJ + 0xA0),
                       "exceptions": h.cpu_exceptions()}
                if hits.dropped or any(row["exceptions"][k] for k in
                                       ("data_aborts", "prefetch_aborts", "undefined")):
                    raise AssertionError(f"lost trace or CPU fault: {row}")
                return row

            reference = {}
            for variant, states in (("control", (0, 1)), ("rom", STATES)):
                for state in states:
                    h.load_state(a.state)
                    if (h.u32(OBJ + 8), h.u32(OBJ + 16)) != (13, 426):
                        raise ValueError("checkpoint does not contain the reviewed Lugia object")
                    h.write(DISPATCH, blocks[variant])
                    row = observe(state)
                    row["variant"] = variant
                    report["rows"].append(row)
                    if row["state_after"] != state:
                        raise AssertionError("scene changed the forced state during the observation")
                    if state <= 1:
                        if len(row["hits"]) != 3 or any(hit["addr"] != TABLE + 4 * state
                                                       for hit in row["hits"]):
                            raise AssertionError("supported state did not dispatch once per frame")
                        if row["after"]["cache"] != state:
                            raise AssertionError("supported state was not cached")
                        if variant == "control":
                            reference[state] = row["after"]
                        elif row["after"] != reference[state]:
                            raise AssertionError("supported animation differs from the original")
                    else:
                        if row["hits"] or row["before"] != row["after"]:
                            raise AssertionError("invalid state dispatched or changed the frame/cache")
                        recovery = observe(1)
                        recovery["variant"] = "recovery"
                        report["rows"].append(recovery)
                        if recovery["after"] != reference[1] or len(recovery["hits"]) != 3:
                            raise AssertionError("animation did not resume after an invalid state")
            report["pass"] = True
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    report["inputs_unchanged"] = report["inputs"] == {k: digest(p) for k, p in paths.items()}
    report["pass"] &= report["inputs_unchanged"]
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("rom", "control", "state", "sav", "out"):
        p.add_argument("--" + name, required=True)
    raise SystemExit(check(p.parse_args()))
