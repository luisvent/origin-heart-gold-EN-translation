#!/usr/bin/env python3
"""Move sweep on melonDS: use every move once as the player and once as the foe in one wild battle and report
data aborts (the freezes DeSmuME does not show), hangs and moves the game refuses to select.

    .venv/bin/python work/tools/emu_move_sweep.py --rom ROM.nds --sav full_bag_6mons.sav --out DIR \
        [--moves 675,704 | --first 1 --last 920] [--sides foe,player] [--shard 0 --nshards 3]

One battle is reached once (Pal Park grass, map 109, walking between (16,40) and (17,40)) and saved as a melonDS
state. For every move the state is loaded and the battle's own move records (the actor structure, moves at +0x25A,
18 bytes apart, PP at +0x25C) are overwritten: the player's slot 0 holds the move (side "player") or Tackle with
the foe holding the move (side "foe"); both HP fields are set to 900, so no turn ends the battle by chance. The turn
is played with FIGHT -> slot 0 and A/B presses, up to --turns turns. A row is written per case to
DIR/results_<shard>.jsonl: result per turn ("menu" = back at the command menu, "field" = the battle ended, "hang" =
the screen stopped changing, "timeout" = still changing but never back, e.g. the game refuses the selection),
the data-abort count since the case started and the faulting instruction. After an abort the process exits with
status 3 (the core stays in abort mode after a state load); run through a loop that restarts it (rows already in
the file are skipped), see work/notes/throat-chop-freeze_fix.md.

Not a regression test of the game's text: it only looks for freezes. Needs the melonDS shim (melonds_backend.md).
"""
import argparse
import datetime
import hashlib
import json
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_harness as E  # noqa: E402

LEAD_MOVE, SPLASH = 33, 150          # the lead's slot-0 move in the save (Tackle), the filler (Splash)
ACTOR_MOVES, ACTOR_PP, ACTOR_HP, ACTOR_MAXHP = 0x25A, 0x25C, 0x1E, 0x1C
ACTOR_STRIDE_FOE = 0x414             # the wild foe's actor follows the player's (checked: number 13, flag 8)
PAL_PARK = (109, 16, 40)
STATIC_FRAMES = 600                  # a screen that does not change for this long is a hang


def play_turn(h, frames=2400):
    """FIGHT -> slot 0, then press A every second until the command menu is back."""
    h.touch(*E.BATTLE_BUTTONS["fight"], frames=10, after=40)
    h.touch(*E.MOVE_BUTTONS[0], frames=10, after=60)
    last, static = None, 0
    for i in range(0, frames, 15):
        h.step(15)
        if h.in_field():
            return "field"
        if h.on_screen("battle_menu"):
            return "menu"
        shot = hashlib.md5(h.emu.screenshot().convert("RGB").tobytes()).hexdigest()
        static = static + 15 if shot == last else 0
        last = shot
        if i % 60 == 45:
            h.press("A", after=0)
        if static >= STATIC_FRAMES:
            return "hang"
    return "timeout"


def find_player_actors(h):
    """Addresses of the player's battle actor records (the battle keeps two copies, both are written): Tackle,
    Splash, empty at +0x25A with 18-byte spacing, battler number 1, and the foe (flag 8) after it."""
    ram = bytes(h.read(0x02000000, 0x400000))
    needle = struct.pack("<H", LEAD_MOVE)
    found = []
    i = ram.find(needle)
    while i >= 0:
        if (i % 2 == 0 and struct.unpack_from("<H", ram, i + 18)[0] == SPLASH
                and struct.unpack_from("<H", ram, i + 36)[0] == 0):
            base = 0x02000000 + i - ACTOR_MOVES
            if h.u8(base + 0x14) == 1 and h.u8(base + ACTOR_STRIDE_FOE + 0x14) & 8:
                found.append(base)
        i = ram.find(needle, i + 1)
    if not found:
        raise RuntimeError("player's battle actor not found")
    return found


def set_actor(h, addr, moves):
    h.w16(addr + ACTOR_MAXHP, 900)
    h.w16(addr + ACTOR_HP, 900)
    for k in range(4):
        h.w16(addr + ACTOR_MOVES + 18 * k, moves[k] if k < len(moves) else 0)
        h.w8(addr + ACTOR_PP + 18 * k, 20 if k < len(moves) else 0)


def reach_battle(h, state):
    steps = 0
    while h.in_field() and steps < 600:
        for tile in ((16, 40), (17, 40)):
            h.walk_to(*tile)
            steps += 1
            if not h.in_field():
                break
    for _ in range(100):
        h.step(30)
        if h.on_screen("battle_menu"):
            break
        h.press("A", after=4)
    if not h.on_screen("battle_menu"):
        raise RuntimeError("no battle command menu")
    h.step(20)
    h.save_state(state)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--rom", required=True)
    ap.add_argument("--sav", required=True, help="a save with a one-Pokemon party at Pal Park (full_bag_6mons.sav)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--moves", help="comma list of move ids (default: --first..--last)")
    ap.add_argument("--first", type=int, default=1)
    ap.add_argument("--last", type=int, default=920)
    ap.add_argument("--sides", default="foe,player")
    ap.add_argument("--turns", type=int, default=2)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--state", help="reuse this melonDS state (else it is made in --out)")
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    moves = [int(x) for x in a.moves.split(",")] if a.moves else list(range(a.first, a.last + 1))
    moves = moves[a.shard::a.nshards]
    results = out / f"results_{a.shard}.jsonl"
    done = set()
    if results.exists():
        for line in results.read_text().splitlines():
            row = json.loads(line)
            done.add((row["move"], row["side"]))

    def edit(sf):
        sf.edit_party_mon(0, **E.moveset([LEAD_MOVE, SPLASH], [20, 20]))
        sf.set_party_count(1)

    clock = datetime.datetime(2026, 10, 9, 12)
    with E.start_at(*PAL_PARK, direction="DOWN", rom=Path(a.rom).resolve(), sav=Path(a.sav).resolve(), clock=clock,
                    out=out, emulator="melonds", edit=edit) as h, open(results, "a") as log:
        state = Path(a.state) if a.state and Path(a.state).exists() else out / "battle.state"
        if state.exists():
            h.load_state(state)
        else:
            reach_battle(h, state)
        bases = find_player_actors(h)
        for move in moves:
            for side in a.sides.split(","):
                if (move, side) in done:
                    continue
                t0 = time.time()
                h.load_state(state)
                before = h.cpu_exceptions()["data_aborts"]
                for base in bases:
                    set_actor(h, base, [move, SPLASH] if side == "player" else [LEAD_MOVE, SPLASH])
                    set_actor(h, base + ACTOR_STRIDE_FOE, [SPLASH] if side == "player" else [move])
                turns = []
                for _ in range(a.turns):
                    turns.append(play_turn(h))
                    if turns[-1] != "menu":
                        break
                    h.step(30)
                aborted = h.cpu_exceptions()["data_aborts"] > before or h.melon.regs()["mode"] == 0x17
                abort = h.arm9_abort() if aborted else None
                row = {"move": move, "side": side, "turns": turns, "seconds": round(time.time() - t0, 1),
                       "abort": {"fault_pc": hex(abort["fault_pc"]), "abort_lr": hex(abort["abort_lr"])}
                       if abort else None}
                if abort or turns[-1] not in ("menu", "field"):
                    h.screenshot(f"{side}_{move}")
                log.write(json.dumps(row) + "\n")
                log.flush()
                print(row, flush=True)
                if abort:
                    return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
