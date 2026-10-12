#!/usr/bin/env python3
"""Read the abilities the game gives a trainer's Pokemon (trainer-abilities, D-2401), straight from the emulator.

Starts a battle against a trainer record with the game's own TrainerBattle command and hooks the party loader
(arm9 0x0207285C, after it applied the stored ability; r4 = the finished Pokemon). Prints one line per Pokemon:
    RES <trainer> <species> <level> ability <id>
One trainer per process (DeSmuME cannot restart in a process). Needs the Chinese or an English build as --rom and
the supplied save. Example:
    python3 work/tools/emu_trainer_abilities.py --rom work/build/fix/en.nds --sav full_bag_6mons.sav 356
Nothing is written to the ROM or the save."""
import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_harness as E  # noqa: E402

LOADER_AFTER_ABILITY = 0x0207285C


def trainer_abilities(rom, sav, trainer, out):
    rows = []
    with E.start_at(None, rom=rom, sav=sav, out=out, verbose=False, clock=datetime.datetime(2026, 10, 9, 12)) as h:
        def hook(h):
            m = E.decode_party_pokemon(h.read(h.reg.r4, 236))
            rows.append((m["species"], m["level"], m["ability"]))
        h.on_exec(LOADER_AFTER_ABILITY, hook)
        h.trainer_battle(trainer)
        h.step(600)
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--sav", required=True)
    ap.add_argument("--out", default=str(E.DEF_OUT / "trainer-abilities"))
    ap.add_argument("trainer", type=int, help="trainer record (a/0/5/5)")
    a = ap.parse_args(argv)
    for species, level, ability in trainer_abilities(a.rom, a.sav, a.trainer, Path(a.out)):
        print(f"RES {a.trainer} {species} {level} ability {ability}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
