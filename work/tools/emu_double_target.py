#!/usr/bin/env python3
"""Fresh-boot horizontal-fallback emulator regression, one case per process. Requires local ROM/save and py-desmume.

Run from the repo root. Set EMU_HARNESS_DATA to the checkout with the local saves.
On headless macOS use SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy.
Example: .venv/bin/python work/tools/emu_double_target.py --rom /scratch/cn.nds \
    --case lastR --out /scratch/results
No downloads. ROMs/saves are never modified; output must be outside versioned files.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import emu_harness as E

PARTY_LIST = [((5, 197), (224, 208, 184)), ((250, 197), (224, 208, 184)), ((20, 362), (248, 248, 248))]
PARTY_SUBMENU = [((5, 197), (224, 208, 184)), ((20, 362), (56, 144, 224))]
SUBMENU_SHIFT = (128, 108)


def matches(h, samples, tolerance=24):
    img = h.emu.screenshot().convert("RGB")
    return all(max(abs(a - b) for a, b in zip(img.getpixel(xy), rgb)) <= tolerance
               for xy, rgb in samples)


def identity(path):
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


GL = 0x02255B90; G_TGT = GL + 0x14
QUADS = {"FL": (0, 0, 128, 64), "FR": (128, 0, 256, 64), "OL": (0, 64, 128, 128), "OR": (128, 64, 256, 128), "CANCEL": (0, 128, 256, 192)}
SLOTNAME = {0: "lead(OL)", 1: "foeR(FR)", 2: "partner(OR)", 3: "foeL(FL)", 4: "cancel"}
SLOTQUAD = {0: "OL", 1: "FR", 2: "OR", 3: "FL", 4: "CANCEL"}
PROBES = ("UP", "DOWN", "LEFT", "RIGHT", "DOWN,UP")
SPREAD_MODES = (1, 2, 3, 5, 7)
TOUCH = {"FL": (64, 40), "FR": (192, 40), "OL": (64, 104), "OR": (192, 104)}

class Run:
    def __init__(self, h, tag, outdir):
        self.h, self.tag, self.out, self.log, self.n = h, tag, outdir, [], 0
        self.last_avail, self.pres, self._slot, self.who = None, {}, None, None
        h.on_exec(0x02212700, lambda h: setattr(self, "last_avail", list(h.read(h.reg.r5, 4))))
        h.on_exec(0x022196AC, lambda h: setattr(self, "_slot", h.reg.r0))
        h.on_exec(0x022196BA, lambda h: self.pres.__setitem__(self._slot, h.reg.r0))
        h.on_exec(0x02212632, self.native_target)
        h.on_exec(0x02212634, lambda h: self.rec(ev="accepted", who=self.who, slot=h.reg.r6))
        h.on_exec(0x0221266E, lambda h: self.rec(ev="engine_target", who=self.who, slot=h.reg.r2))
    def native_target(self, h):
        mode, mask = self.avail()
        self.rec(ev="native_target", mode=mode, avail=mask, representative=h.reg.r0)
    def bottom(self): return self.h.emu.screenshot().convert("RGB").crop((0, 192, 256, 384))
    def quad(self):
        img = self.bottom(); px = img.load(); best, bc = None, 0
        for q, (x0, y0, x1, y1) in QUADS.items():
            c = sum(1 for x in range(x0, x1, 2) for y in range(y0, y1, 2) if (lambda p: p[0] > 200 and p[1] < 40 and p[2] < 40)(px[x, y]))
            if c > bc: best, bc = q, c
        return best if bc > 3 else None
    def req(self):
        p = self.h.u32(GL + 4)
        return self.h.u32(p + 0x3EC) if 0x02000000 <= p < 0x02400000 else 0
    def actor(self):
        p = self.h.u32(GL + 4); return self.h.u8(p + 0x1B2)
    def present(self):
        return [self.pres.get(s) for s in range(4)]
    def avail(self):
        r = self.req()
        if not r: return None
        return self.h.u8(r + 3), self.last_avail
    def shot(self, name):
        self.n += 1; p = self.h.screenshot(f"{self.tag}_{self.n:03d}_{name}"); return os.path.basename(str(p))
    def rec(self, **kw):
        kw.setdefault("tgt", self.h.u8(G_TGT))
        self.log.append(kw); print(json.dumps(kw), flush=True)
    def wait_menu(self, frames=2400):
        """Advance to the next command menu / party list / field. Returns 'menu', 'party', 'field' or None."""
        idle = 0
        for i in range(0, frames, 10):
            self.h.step(10)
            if self.h.on_screen("battle_menu"): self.h.step(20); return "menu"
            if self.h.in_field(): return "field"
            if matches(self.h, PARTY_LIST): return "party"
            idle += 10
            if idle % 300 == 0: self.h.press("B", after=0)
        return None
    def target(self, label, pick, probe=True):
        """On an open target screen: show the key cursor, record it, probe the 4 directions, then pick."""
        h = self.h
        self.who = label
        mode, av = self.avail()
        if pick == 'empty':
            empty = next(s for s in (1, 3) if self.present()[s] == 0)
            h.touch(*TOUCH[{1:'FR',3:'FL'}[empty]], frames=10, after=60)
            assert self.req(), 'empty foe touch unexpectedly confirmed a move'
            self.rec(ev='empty_touch', empty=empty, avail=self.avail())
            pick = 'A'
        q0 = self.quad()
        if q0 is None:           # touch mode: the first key press only switches to key mode
            h.press("R", frames=6, after=40); q0 = self.quad()
        if q0 is None:
            h.press("UP", frames=6, after=40); q0 = self.quad()
        info = dict(ev="target", who=label, actor=self.actor(), mode=mode, avail=av, present=self.present(),
                    init_quad=q0, init=SLOTNAME.get(h.u8(G_TGT)), shot=self.shot(f"{label}_init"))
        if probe:
            st = os.path.join(self.out, f"{self.tag}_probe.dst"); h.save_state(st); res = {}
            for d in ("UP", "DOWN", "LEFT", "RIGHT"):
                h.load_state(st); h.press(d, frames=6, after=40)
                r1 = (self.quad(), SLOTNAME.get(h.u8(G_TGT)))
                h.press(d, frames=6, after=40)
                res[d] = [r1, (self.quad(), SLOTNAME.get(h.u8(G_TGT)))]
                if d == "UP": info["up_shot"] = self.shot(f"{label}_up")
            # escape attempt: Down then Up (via the cancel row)
            h.load_state(st)
            for k in ("DOWN", "UP"): h.press(k, frames=6, after=40)
            res["DOWN,UP"] = (self.quad(), SLOTNAME.get(h.u8(G_TGT)))
            h.load_state(st); info["probe"] = res
        if pick == 'cancel':
            for key in ('DOWN', 'DOWN'): h.press(key, frames=6, after=40)
            assert h.u8(G_TGT) == 4
            for direction in ('LEFT', 'RIGHT'):
                h.press(direction, frames=6, after=40)
                assert h.u8(G_TGT) == 4 and self.quad() == 'CANCEL'
                self.rec(ev='cancel_horizontal', direction=direction)
            for key in ('A', 'B'):
                h.press(key, frames=6, after=80)
                assert not self.req(), 'cancel did not close target selection'
                self.rec(ev='cancel', key=key)
                h.touch(*E.MOVE_BUTTONS[0], frames=10, after=80)
                assert self.req(), 'move did not reopen target selection'
                h.press('R', frames=6, after=40)
                assert h.u8(G_TGT) in (1,3) and av[h.u8(G_TGT)]
                self.rec(ev='reenter', key=key)
            pick = 'A'
        self.rec(**info)
        self.rec(ev="pick", who=label, pick=pick)
        if pick.startswith("touch:"):
            h.touch(*TOUCH[pick[6:]], frames=10, after=60)
        else:
            for k in pick.split(","): h.press(k, frames=6, after=50)
        h.step(30)
        if self.req():   # a second screen (self-target confirmation) or a refused touch
            self.rec(ev="still_target", who=label, avail=self.avail(), quad=self.quad(), shot=self.shot(f"{label}_again"))
            h.press("A", frames=6, after=50); h.step(30)
    def command(self, label, move, pick, probe=True):
        h = self.h
        h.touch(*E.BATTLE_BUTTONS["fight"], frames=10, after=60)
        h.touch(*E.MOVE_BUTTONS[move], frames=10, after=80)
        h.step(20)
        if self.req():
            self.target(label, pick, probe)
        else:
            self.rec(ev="no_target_screen", who=label, shot=self.shot(f"{label}_notarget"))

def prepare_fixture(sf, moves):
    """Edit only the disposable battery copy before boot; strict codec gates apply."""
    before = [mon['species'] for mon in sf.party()]
    for i, mv in enumerate(moves):
        sf.edit_party_mon(i, moves=list(mv) + [0] * (4 - len(mv)),
                          pp=[30] * len(mv) + [0] * (4 - len(mv)))
    after = sf.party()
    assert [mon['species'] for mon in after] == before
    assert all(mon['checksum_ok'] and not mon['bad_egg'] for mon in after)


def wait_fixture(h, expected, max_frames=120):
    """Frame boundaries can pause native crypt loops; read only until all records close."""
    for _ in range(max_frames):
        party = h.party()
        if (all(mon['checksum_ok'] and not mon['bad_egg'] and mon['flags'] == 0 for mon in party)
                and [(mon['species'], mon['moves']) for mon in party] == expected):
            return
        h.step(1)
    raise AssertionError('prepared party did not reach a valid closed snapshot')


def start_battle(h, script):
    h.run_script(program=E.script_bytes(("LockAll",), script, ("ReleaseAll",), ("End",)))
    for k in range(120):
        h.step(30)
        if h.on_screen("battle_menu"): return True
        if k % 2: h.press("A", after=4)
    return False

def play(r, turns):
    """turns: list of {actor_id: (move, pick, probe)} keyed 0 (lead) / 2 (partner); party: slot to send in."""
    for t, plan in enumerate(turns):
        st = r.wait_menu()
        while st == "party":
            slot = plan.get("send", 2)
            r.rec(ev="party_list", turn=t + 1, shot=r.shot(f"t{t+1}_party"))
            r.h.touch(*E.PARTY_SLOTS[slot], frames=10, after=60)
            if matches(r.h, PARTY_SUBMENU): r.h.touch(*SUBMENU_SHIFT, frames=10, after=90)
            st = r.wait_menu()
        if st != "menu":
            r.rec(ev="end", turn=t + 1, state=st, shot=r.shot(f"t{t+1}_end")); return
        cmds = plan["cmds"]; k = 0
        while st == "menu" and k < len(cmds):
            a = r.actor()
            r.rec(ev="menu", turn=t + 1, actor=a, k=k)
            mv, pick, probe = cmds[k]
            r.command(f"t{t+1}_c{k}", mv, pick, probe); k += 1
            r.h.step(40)
            st = "menu" if r.h.on_screen("battle_menu") else None
    st = r.wait_menu()
    r.rec(ev="final", state=st, present=r.present(), shot=r.shot("final"))


MOVES = [28, 150, 394]  # Sand Attack, Splash, Flare Blitz (KO without ending both sides)
CASES = ('lastR', 'lastL', 'leak', 'field', 'spread', 'multi', 'wildR', 'wildL', 'cancel', 'empty', 'single', 'allyL', 'allyR')

def scenario(case):
    moves = [MOVES] * 6
    battle = ('TrainerBattle', 6, 6, 0, 0)
    normal = {'cmds': [(0, 'A', True), (0, 'A', True)]}
    if case in ('lastR', 'lastL', 'wildR', 'wildL', 'cancel', 'empty', 'allyL', 'allyR'):
        side = 'FL' if case.endswith('L') else 'FR'
        turns = [{'cmds': [(2, 'touch:'+side, True), (1, 'A', True)]}, normal, normal]
        if case == 'allyL':
            turns[1] = {'cmds': [(0, 'A', True), (0, 'LEFT,A', True)]}
        if case == 'allyR':
            turns[1] = {'cmds': [(0, 'RIGHT,A', True), (0, 'A', True)]}
        if case in ('cancel','empty'):
            turns[1] = {'cmds': [(0, case, True), (0, 'A', True)]}
    elif case == 'single':
        battle = ('TrainerBattle', 6, 0, 0, 0)
        turns = [{'cmds': [(0, 'A', True)]} for _ in range(3)]
    elif case == 'leak':
        battle = ('TrainerBattle', 40, 40, 0, 0)
        turns = [{'cmds': [(0, 'A', True), (1, 'A', True)]}, normal, normal]
    elif case == 'field':
        battle = ('TrainerBattle', 40, 40, 0, 0)
        moves = [[240, 28, 150]] * 6  # Rain Dance: mode 3
        turns = [{'cmds': [(0, 'DOWN,UP,A', True), (0, 'DOWN,UP,A', True)]},
                 {'cmds': [(1, 'A', True), (1, 'A', True)]}]
    elif case == 'spread':
        battle = ('TrainerBattle', 40, 40, 0, 0)
        moves = [[28, 89, 45]] * 6  # Earthquake: lead mode 2 / partner mode 7; Growl mode 1
        turns = [{'cmds': [(0, 'A', True), (1, 'DOWN,UP,A', True)]},
                 {'cmds': [(1, 'DOWN,UP,A', True), (2, 'DOWN,UP,A', True)]}]
    else:
        battle = ('MultiBattle', 385, 6, 8, 0)
        turns = [{'cmds': [(2, 'touch:FR', True)]},
                 {'cmds': [(2, 'touch:FR', True)]}, {'cmds': [(0, 'A', True)]}]
    return moves, battle, turns


def expected_nav(mask, cur, direction, horizontal=True):
    """UI geometry oracle, independent of the assembler and Thumb model."""
    grid = [3, 1, 0, 2, 4, 4]
    start = max(i for i, slot in enumerate(grid) if slot == cur)
    x, y = start % 2, start // 2
    if direction in ('LEFT', 'RIGHT'):
        nx = x + (-1 if direction == 'LEFT' else 1)
        if nx not in (0, 1):
            return cur
        adjacent = grid[2 * y + nx]
        if adjacent == 4 or mask[adjacent]:
            return adjacent
        if horizontal:
            diagonal = grid[2 * (1 - y) + nx]
            if mask[diagonal]:
                return diagonal
        return cur
    dy = -1 if direction == 'UP' else 1
    for column in (x, 1 - x):
        row = y + dy
        while row in range(3):
            slot = grid[2 * row + column]
            if slot == 4 or mask[slot]:
                return slot
            row += dy
    return cur


def validate(rows, case, horizontal=True):
    targets = [r for r in rows if r.get('ev') == 'target']
    assert targets or case == 'single', 'no target screens observed'
    byname = {v: k for k, v in SLOTNAME.items()}
    modes = {r['mode'] for r in targets}
    for row in targets:
        mode, mask = row['mode'], row['avail']
        assert row.get('init') in byname, ('unknown initial slot', row)
        initial = byname[row['init']]
        assert len(mask) == 4
        if mode in (8, 9):
            assert initial in (1, 3) and mask[initial], row
        # Spread highlights cover a group; quad()'s winning region need not be the
        # representative's quadrant (and may even be CANCEL). Only an actual
        # CANCEL cursor has a meaningful single-region assertion in those modes.
        if mode not in SPREAD_MODES or initial == 4:
            assert row.get('init_quad') == SLOTQUAD[initial], ('initial visual mismatch', row)
        probes = row.get('probe')
        assert isinstance(probes, dict) and set(probes) == set(PROBES), ('incomplete or unknown probes', row)
        for direction in PROBES:
            results = probes[direction]
            assert isinstance(results, (list, tuple)), (row['who'], direction, 'invalid probe shape', results)
            if direction == 'DOWN,UP':
                samples, directions = [results], ('DOWN', 'UP')
            else:
                assert len(results) == 2, (row['who'], direction, 'expected two samples', results)
                samples, directions = results, (direction, direction)
            for sample in samples:
                assert isinstance(sample, (list, tuple)) and len(sample) == 2, (row['who'], direction, 'invalid sample pair', sample)
                assert isinstance(sample[1], str) and sample[1] in byname, (row['who'], direction, 'unknown slot', sample)
            cur = initial
            for index, d in enumerate(directions):
                if mode in SPREAD_MODES:
                    cur = 4 if d == 'DOWN' else next((s for s in range(4) if mask[s]),4) if d == 'UP' else cur
                else:
                    cur = expected_nav(mask, cur, d, horizontal)
                if direction == 'DOWN,UP' and index == 0:
                    continue  # The report records only the final composed result.
                sample = samples[0] if direction == 'DOWN,UP' else samples[index]
                assert byname[sample[1]] == cur, (row['who'], direction, sample[1], cur)
                if mode not in SPREAD_MODES or cur == 4:
                    assert sample[0] == SLOTQUAD[cur], (row['who'], direction, 'visual mismatch', sample, cur)
    if case in ('lastR','lastL','leak'):
        assert len(targets) == 6, 'three turns for both battlers required'
        assert targets[0]['init_quad'] == 'FL'
        for row in targets[2:]:
            assert row['init_quad'] == ('FR' if case == 'lastL' else 'FL')
        if case.startswith('last'):
            empty = 1 if case == 'lastR' else 3
            assert all(r['present'][empty] == 0 for r in targets[2:])
    if case in ('field', 'spread'):
        expected_modes = [3, 3, 8, 9] if case == 'field' else [8, 7, 2, 1]
        assert [r['who'] for r in targets] == ['t1_c0', 't1_c1', 't2_c0', 't2_c1'], targets
        assert [r['actor'] for r in targets] == [1, 2, 1, 2], targets
        assert [r['mode'] for r in targets] == expected_modes, targets
    if case in ('field','spread'):
        native = [r for r in rows if r.get('ev') == 'native_target']
        required = {3} if case == 'field' else {7}
        assert required.issubset({r['mode'] for r in native}), native
        for row in native:
            assert row['representative'] == next(i for i,v in enumerate(row['avail']) if v), row
    if case in ('wildR','wildL','multi','cancel','empty'):
        later = targets[2:] if case != 'multi' else targets[1:]
        empty = 3 if case == 'wildL' else 1
        if case == 'multi':
            # The first KO is replaced; the following turn exhausts that trainer.
            assert targets[-1]['present'][empty] == 0, targets[-1]
            later = [r for r in later if r['present'][empty] == 0]
        assert later and all(r['present'][empty] == 0 for r in later), later
        for row in later:
            assert row['init_quad'] == ('FR' if empty == 3 else 'FL'), row
            assert row['avail'][empty] == 0 and row['avail'][4-empty], row
    if case == 'cancel':
        assert [r['direction'] for r in rows if r.get('ev') == 'cancel_horizontal'] == ['LEFT', 'RIGHT']
        assert [r['key'] for r in rows if r.get('ev') == 'cancel'] == ['A','B']
        assert len([r for r in rows if r.get('ev') == 'reenter']) == 2
    if case == 'empty': assert any(r.get('ev') == 'empty_touch' for r in rows)
    if case in ('allyL', 'allyR'):
        assert [row['who'] for row in targets] == [f't{turn}_c{cmd}' for turn in range(1, 4) for cmd in range(2)], 'incomplete three-turn command sequence'
        assert [row['actor'] for row in targets] == [1, 2] * 3, 'unexpected actor sequence'
        label, direction, ally, initial, mask, mode = (
            ('t2_c1', 'LEFT', 0, 1, [1, 1, 0, 0], 9) if case == 'allyL' else
            ('t2_c0', 'RIGHT', 2, 3, [0, 0, 1, 1], 8))
        row = next(r for r in targets if r['who'] == label)
        assert row['avail'] == mask and row['mode'] == mode, row
        missing = 3 if case == 'allyL' else 1
        assert row['present'][missing] == 0, row
        assert byname[row['init']] == initial, row
        expected = ally if horizontal else initial
        assert byname[row['probe'][direction][0][1]] == expected, row
        accepted = [r['slot'] for r in rows if r.get('ev') == 'accepted' and r.get('who') == label]
        engine = [r['slot'] for r in rows if r.get('ev') == 'engine_target' and r.get('who') == label]
        assert accepted == [expected] and engine == [expected], (accepted, engine, expected)
        engine_index = next(i for i, r in enumerate(rows) if r.get('ev') == 'engine_target' and r.get('who') == label)
        assert any(r.get('ev') == 'menu' and r.get('turn') == 3 and r.get('actor') == 1
                   for r in rows[engine_index + 1:]), 'no next turn after engine acceptance'
    if case == 'single':
        assert len([r for r in rows if r.get('ev') == 'no_target_screen']) == 3
    if case.startswith('wild'):
        assert any(r.get('ev') == 'wild' and r['n'] == 2 for r in rows)
        assert len(targets) >= 4
    if case == 'multi': assert len(targets) >= 3
    assert rows[-1].get('state') in ('menu','field'), 'battle failed to progress'
    return {'pass': True, 'target_screens': len(targets), 'modes': sorted(modes),
            'navigation': 'horizontal-fallback' if horizontal else 'historical-option2'}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rom',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--case',required=True,choices=CASES)
    ap.add_argument('--sav', type=Path, default=E.DEF_SAVES / 'full_bag_6mons.sav')
    ap.add_argument('--expect-option2', action='store_true', help='fresh-boot negative control: historical navigation')
    args=ap.parse_args()
    out=args.out.resolve()
    build = Path(__file__).resolve().parents[1] / 'build'
    if not out.is_relative_to(build.resolve()) or out == build.resolve():
        ap.error('output must be a new directory inside work/build')
    out.mkdir(parents=True,exist_ok=False)
    args.rom = args.rom.resolve()
    args.sav = args.sav.resolve()
    inputs = {'rom': identity(args.rom), 'save': identity(args.sav)}
    moves,battle,turns=scenario(args.case)
    fixture_expected = []
    def fixture(sf):
        prepare_fixture(sf, moves)
        fixture_expected.extend((mon['species'], mon['moves']) for mon in sf.party())
    wild=args.case.startswith('wild')
    with E.start_at(315 if wild else None,17 if wild else None,24 if wild else None,
                    rom=args.rom, sav=args.sav, flags=(2423,2424,2425,2426) if wild else (),out=out,
                    verbose=False,clock=datetime.datetime(2026,10,9,12),
                    edit=fixture) as h:
        wait_fixture(h, fixture_expected)
        r=Run(h,args.case,str(out))
        if wild:
            log=E.WildLog(h)
            for attempt in range(40):
                n=len(log.rows)
                for step in range(400):
                    h.walk('LEFT' if (step//3)%2 else 'RIGHT',1)
                    if len(log.rows)>n: break
                h.step(300)
                if len(log.rows)-n >= 2: break
                h.flee(battle_menu_wait=20)
            r.rec(ev='wild',n=len(log.rows)-n,species=[x['species'] for x in log.rows[n:]])
            assert len(log.rows)-n == 2, 'no wild double found'
            assert h.wait_screen('battle_menu',2000)
        else:
            assert start_battle(h,battle), 'battle menu not reached'
        play(r,turns)
        # Validation must not mutate the evidence log.
        result=validate(json.loads(json.dumps(r.log)),args.case,not args.expect_option2)
    assert inputs == {'rom': identity(args.rom), 'save': identity(args.sav)}, 'input modified'
    (out/'report.json').write_text(json.dumps({'case':args.case,'inputs':inputs, 'inputs_unchanged':True,
                                             'emulator':'desmume', 'fresh_boot':True, **result,'log':r.log},indent=2))
    print(json.dumps(result),flush=True)

if __name__ == '__main__':
    main()
