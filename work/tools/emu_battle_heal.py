"""Reproduce the Potion-then-Roar health-bar NULL read (Maxie's gauntlet, Lavender Town) on DeSmuME.

The fix is work/patches/battle-heal-hpbar-switched-out (overlay 14, D-2281). The hack's battle engine computes a
whole turn first and then plays it back. A Potion's playback (handler 0x022053D0) calls 0x0222E024 with the healed
Pokemon's id; that routine finds the battler showing it (0x02228740) from the party order after the whole turn. When
the same turn forces the healed Pokemon out (Houndoom's Roar in the gauntlet's second wave), the lookup returns 5,
the battler-to-bar table gives health bar 0, which a double battle never sets up, and the bar task's gauge drawing
loads that bar's NULL sprite pointer and reads address 0 (ldr r0, [r0] at 0x02210C9E). melonDS 1.1 raises a data
abort there and the game freezes; DeSmuME reads address 0 and goes on, so this scenario follows the read instead.

One baseline: Continue from the supplied save, a Lv100 Marshtomp from the hack's generator as the lead (half HP,
Surf/Growl/Protect/Splash), Potions in the Medicine pocket, then the gauntlet's second wave with the game's own
MultiBattle command (partner Green 524 against Magmortar 527 and Houndoom 528), stopped at the first command menu.
Each trial restores the baseline, waits a few frames, uses a Potion on the lead from the battle Bag and plays the
turn out. With the fixed clock the turn is the same in every trial and on both builds: the Potion heals the lead,
the partner's Azumarill eats its Sitrus Berry, and Houndoom's Roar drags Azumarill out (Ditto comes in), so the
berry's healing playback is for a Pokemon that has left the field (the same path as a Potion on a Pokemon that
Roar drags out, which melonDS reproduces with the lead). Read-only execution hooks: the bar routine's entry (healed Pokemon), the bar
task (which bar, its sprite pointer) and the gauge's sprite load (a NULL pointer). Nothing is written to the ROM,
its code or the battle; the input ROM and save files are never written. The clock is fixed (repeatable runs).
--expect original: some healing playback animates a bar without a sprite and the gauge reads address 0;
--expect fixed: a healing playback is skipped (no bar task), the lead's bar still animates, no NULL sprite is read.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path

OV14_BASE = 0x022007E0
HEAL_CMD = 0x022053D0               # Potion playback handler; its bl to the bar routine returns to 0x022053F6
HEAL_CMD_RETURN = 0x022053F7
BAR_ROUTINE = 0x0222E024            # (r1 = Pokemon id, r2 = HP, r3 = done flag)
BAR_TASK = 0x0222DFE8               # SysTask(r0 = task, r1 = health bar)
GAUGE_SPRITE_LOAD = 0x02210C9E      # ldr r0, [r0]: the bar's sprite (r0 = bar's [+0x34])
GAUGE_SPRITE_LOAD_OP = 0x6800
BAR_SPRITE = 0x34
BAR_TASK_STATE = 0x23
PARTY_LISTS_PTR = 0x02215188        # -> G; party lists at G + 0x150 + k * 0x1C (u32 Pokemon pointers, u8 count at +0x18)
MON_ID = 0x14
CALLER_EDIT = 0x022053E8            # 'ldr r0, [r3, #0x28]' (original) / 'lsr r0, r1, #0x18' (fixed)
ROUTINE_ORIGINAL = bytes.fromhex(
    "70b5081c161c1d1cfaf788fbe7f748fb0c490a68ab21890052183c2141435418201c311ce2f70cfd201cfa22a5630021297023"
    "3001700448211c9200dff508ff70bdc046745c2502e9df2202")
ROUTINE_FIXED = bytes.fromhex(
    "70b5161c1d1cfaf789fb052818d0e7f747fb0b303c2148430a4909680c181834201c311ce2f70cfda563002129702320215405"
    "48211cfa229200dff509ff70bd287070bd745c2502e9df2202")
CALLER_ORIGINAL = bytes.fromhex("986a")
CALLER_FIXED = bytes.fromhex("080e")
CLOCK = datetime.datetime(2026, 10, 9, 12)
MARSHTOMP, POTION = 259, 17
LEAD_MOVES, LEAD_PP = [57, 45, 182, 150], [15, 40, 10, 40]
WAVE2 = (("LockAll",), ("MultiBattle", 524, 527, 528, 0), ("ReleaseAll",), ("End",))
DELAYS = (0, 4, 8, 12, 16, 20, 24, 28)
SAMPLE_LIMIT = 12


def add_arguments(parser):
    parser.add_argument("--rom", required=True, help="local original or fixed Origin v4.0.3 ROM")
    parser.add_argument("--sav", required=True, help="local raw battery save (work/build/memcheck/full_bag_6mons.sav); "
                        "imported without changing the file")
    parser.add_argument("--out", required=True, help="new evidence directory (must not already contain report.json)")
    parser.add_argument("--expect", required=True, choices=("original", "fixed"),
                        help="original: the dragged-out Potion target reads a NULL sprite; fixed: no trial may")
    parser.add_argument("--delays", default=",".join(map(str, DELAYS)),
                        help="frames waited at the command menu before each trial, comma-separated")


def file_identity(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": str(path), "size": path.stat().st_size, "sha256": digest.hexdigest()}


def expected_code(expect):
    return ((CALLER_ORIGINAL, ROUTINE_ORIGINAL) if expect == "original" else (CALLER_FIXED, ROUTINE_FIXED))


def validate_rom(path, expect):
    """Reject unfamiliar code before emulation: overlay 14's load address, the handler edit and the bar routine."""
    import ndspy.rom
    rom = ndspy.rom.NintendoDSRom.fromFile(str(path))
    ov = rom.loadArm9Overlays([14])[14]
    if ov.ramAddress != OV14_BASE:
        raise ValueError(f"overlay 14 loads at {ov.ramAddress:#x}, not {OV14_BASE:#x}")
    data = bytes(ov.data)
    caller, routine = expected_code(expect)
    if data[CALLER_EDIT - OV14_BASE:CALLER_EDIT - OV14_BASE + 2] != caller:
        raise ValueError("overlay 14 Potion handler differs from the expected " + expect + " code")
    if data[BAR_ROUTINE - OV14_BASE:BAR_ROUTINE - OV14_BASE + len(routine)] != routine:
        raise ValueError("overlay 14 health-bar routine differs from the expected " + expect + " routine")


def set_party_hp(h, slot, fraction):
    """Current HP of a party Pokemon (party extension +6, encrypted with the PID stream) to fraction of its max."""
    import emu_harness as E
    a = h.array(E.ARR_PARTY) + 8 + 236 * slot
    raw = bytearray(h.read(a, 236))
    mon = E.decode_party_pokemon(raw)
    hp = max(1, int(mon["stats"][0] * fraction))
    h.write(a, E.encode_pokemon(raw, currentHp=hp))


def party_order(h):
    """The battle engine's player party list (k = 0): the id bytes of its Pokemon, in order."""
    g = h.u32(h.u32(PARTY_LISTS_PTR))
    lst = g + 0x144 + 0xC
    n = h.u8(lst + 0x18)
    return [h.u8(h.u32(lst + 4 * i) + MON_ID) for i in range(min(n, 6))]


class Trace:
    """Read-only hooks; callbacks never raise (errors are collected)."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.heals, self.bars, self.null_reads, self.errors = [], {}, 0, []
        self.active = False

    def _guard(self, fn, h):
        try:
            if self.active:
                fn(h)
        except Exception as exc:
            if len(self.errors) < SAMPLE_LIMIT:
                self.errors.append(f"{type(exc).__name__}: {exc}")

    def install(self, h):
        h.on_exec(BAR_ROUTINE, lambda m: self._guard(self.heal, m))
        h.on_exec(BAR_TASK, lambda m: self._guard(self.task, m))
        h.on_exec(GAUGE_SPRITE_LOAD, lambda m: self._guard(self.gauge, m))

    @staticmethod
    def remove(h):
        for addr in (BAR_ROUTINE, BAR_TASK, GAUGE_SPRITE_LOAD):
            h.on_exec(addr, None)

    def heal(self, h):
        if h.reg.lr == HEAL_CMD_RETURN:
            self.heals.append({"frame": h.frame, "id": h.reg.r1 & 0xFF, "hp": h.reg.r2})

    def task(self, h):
        bar = h.reg.r1
        if 0x02000000 <= bar < 0x02400000 and bar not in self.bars:
            self.bars[bar] = {"frame": h.frame, "sprite": h.u32(bar + BAR_SPRITE)}

    def gauge(self, h):
        if h.u16(GAUGE_SPRITE_LOAD) == GAUGE_SPRITE_LOAD_OP and h.reg.r0 == 0:
            self.null_reads += 1


def potion(h, E, slot=0):
    h.touch(*E.BATTLE_BUTTONS["bag"], frames=10, after=120)
    h.touch(64, 40, frames=10, after=90)          # HP/PP RESTORE
    h.touch(64, 28, frames=10, after=90)          # the first item: Potion
    h.touch(128, 172, frames=10, after=120)       # USE
    h.touch(*E.PARTY_SLOTS[slot], frames=10, after=0)


def wait_menu(h, max_frames, field=True):
    for i in range(0, max_frames, 15):
        h.step(15)
        if h.on_screen("battle_menu"):
            return "menu"
        if field and h.in_field():
            return "field"
        if i % 45 == 30:
            h.press("B", after=0)
    return "stuck"


def setup(h, E):
    h.boot_to_menu()
    h.continue_game()
    h.press("B", after=30)
    mon = h.generate_pokemon(MARSHTOMP, level=100)
    h.swap_party(0, mon["slot"])
    h.edit_party_mon(0, moves=LEAD_MOVES, pp=LEAD_PP)
    set_party_hp(h, 0, 0.5)
    h.bag_put_first(POTION, 99, pocket="medicine")
    h.run_script(program=E.script_bytes(*WAVE2))
    if wait_menu(h, 9000, field=False) != "menu":
        raise RuntimeError("the second wave's command menu did not appear")


def failures(expect, trials, errors):
    """Everything that keeps the run from passing; empty means it passed. A 'skipped' heal is a healing playback
    that started no health-bar task (the fix's not-on-field exit)."""
    reasons = []
    if errors:
        reasons.append("hook errors")
    if not trials:
        reasons.append("no trial ran")
    if any(t["result"] != "menu" for t in trials):
        reasons.append("a trial did not return to the command menu")
    if any(not any(x["id"] == t["lead_id"] for x in t["heals"]) for t in trials):
        reasons.append("the lead's Potion playback was not seen in every trial")
    if any(not t["lead_bar_ok"] for t in trials if not t["lead_dragged_out"]):
        reasons.append("the lead's health bar (with its sprite) was not animated")
    if expect == "original":
        if not any(t["null_sprite_reads"] and t["bars_without_sprite"] for t in trials):
            reasons.append("original defect not observed: no healing playback animated a bar without a sprite "
                           "and read address 0")
    else:
        if any(t["null_sprite_reads"] or t["bars_without_sprite"] for t in trials):
            reasons.append("a bar without a sprite was animated / a NULL sprite was read")
        if not any(t["skipped_heals"] for t in trials):
            reasons.append("no healing playback for a Pokemon off the field happened: the defect's condition was "
                           "not reached")
    return reasons


def run(args, harness_factory=None):
    """Return 0 only when the trials meet the expectation."""
    delays = [int(x) for x in str(args.delays).split(",")]
    rom, sav, out = Path(args.rom).resolve(), Path(args.sav).resolve(), Path(args.out).resolve()
    if (out / "report.json").exists():
        raise ValueError("refusing to overwrite an existing report.json; choose a new --out")
    identity = {"rom": file_identity(rom), "save": file_identity(sav)}
    out.mkdir(parents=True, exist_ok=True)
    report = {"schema": 1, "expect": args.expect, "inputs": identity, "trials": [], "passed": False,
              "setup": "One imported battery save, fixed clock; generator Marshtomp Lv100 as the lead at half HP, "
                       "Potions; the game's MultiBattle command (524 vs 527 + 528); baseline restored before each "
                       "trial; read-only hooks."}
    trace = Trace()
    try:
        validate_rom(rom, args.expect)
        if harness_factory is None:
            from emu_harness import Harness
            harness_factory = Harness
        import emu_harness as E
        with harness_factory(rom, sav=sav, out=out / "screens", rtc=CLOCK, emulator="desmume") as h:
            setup(h, E)
            baseline = out / "baseline.dst"
            h.save_state(baseline)
            before = party_order(h)
            trace.install(h)
            for d in delays:
                h.load_state(baseline)
                trace.reset()
                h.step(d)
                trace.active = True
                potion(h, E, 0)
                result = wait_menu(h, 6000)
                trace.active = False
                order = party_order(h) if result == "menu" else []
                bars = {f"0x{k:08x}": v for k, v in trace.bars.items()}
                row = {"delay": d, "result": result, "lead_id": before[0], "order_before": before, "order_after": order,
                       "lead_dragged_out": bool(order) and order[0] != before[0],
                       "heals": trace.heals, "bars": bars,
                       "bars_without_sprite": sum(1 for v in trace.bars.values() if v["sprite"] == 0),
                       "skipped_heals": len(trace.heals) - len(trace.bars),
                       "lead_bar_ok": any(v["sprite"] for v in trace.bars.values()),
                       "null_sprite_reads": trace.null_reads,
                       "screen": str(h.screenshot(f"trial_{d}_{result}"))}
                report["trials"].append(row)
            Trace.remove(h)
        report["hook_errors"] = trace.errors
        report["failures"] = failures(args.expect, report["trials"], trace.errors)
        report["passed"] = not report["failures"]
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        report["inputs_unchanged"] = all(file_identity(p) == identity[k] for k, p in (("rom", rom), ("save", sav)))
        report["passed"] = report["passed"] and report["inputs_unchanged"]
        temporary = out / "report.json.tmp"
        temporary.write_text(json.dumps(report, indent=2) + "\n")
        temporary.replace(out / "report.json")
    print(json.dumps({"passed": report["passed"], "report": str(out / "report.json"), "error": report.get("error"),
                      "failures": report.get("failures"),
                      "trials": [{k: t[k] for k in ("delay", "result", "lead_dragged_out", "skipped_heals",
                                                    "bars_without_sprite", "null_sprite_reads")} for t in report["trials"]]}))
    return 0 if report["passed"] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    add_arguments(parser)
    args = parser.parse_args(argv)
    try:
        return run(args)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
