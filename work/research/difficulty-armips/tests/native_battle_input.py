"""Bounded observed battle inputs; no B mash, state restore or outcome writes.

Read offsets/action seam come from the local emu_struggle native probes; target
request and SHIFT coordinates from emu_double_target. All execution probes use
the candidate overlay identity multiplexer, never those historical drivers.
"""
from native_battle_oracles import require


def mon_state(h, address):
    require(0x02000000 <= address <= 0x023DC000-0x2a0, 'invalid live BattleMon')
    return dict(address=address, id=h.u8(address+0x14), hp=h.u16(address+0x1e),
                maxhp=h.u16(address+0x1c),
                moves=[h.u16(address+0x25a+18*i) for i in range(4)],
                pp=[h.u8(address+0x25c+18*i) for i in range(4)])


def assert_move(before, after, actions, slot, move):
    require(before['id'] == after['id'], 'move unexpectedly changed active recipient')
    require(before['moves'][slot] == move, 'wrong fixture move slot')
    actual = [a for a in actions if a['actor']['id'] == before['id']]
    require(len(actual) == 1 and actual[0]['move'] == move,
            'expected exactly one native submitted move for the requested actor')
    require(after['pp'][slot] == before['pp'][slot]-1, 'move did not consume exactly one native PP')


class BattleInput:
    opponent_id=13
    roster_ids=(1,2,3,13)

    def __init__(self, session, trace, run):
        self.s, self.h, self.trace, self.run = session, session.h, trace, run
        self.index = 0

    def state(self, allow_absent_ui=False, raw=None):
        h = self.h
        raw = {} if raw is None else raw
        if h.in_field(): return dict(field=True)
        root = h.u32(0x02255bac)
        ui = h.u32(0x02255b94)
        raw.update(root=root, ui=ui, active_address=None)
        # Teardown releases party objects before the root. Only an observed
        # native teardown seam permits skipping those freed recipient reads.
        # This path is diagnostic only; a command checkpoint cannot use it.
        if any(e['name']=='teardown' for e in self.run.get('events', [])):
            require(allow_absent_ui and not h.on_screen('battle_menu'), 'command checkpoint during teardown')
            return dict(field=False, **raw, ui_available=False, phase='teardown',
                        active=None, request=None, command_actor=None, mons=None)
        require(0x02000000 <= root <= 0x023DC000-0x274 and
                root == self.trace.snapshot()['root'], 'battle owner changed during input')
        # The battle root owns these recipients even while the command UI is
        # destroyed for the party overlay. Do not treat a roster ID as proof
        # that it is active: only the returned command UI can certify the switch.
        mons={str(i):mon_state(h,h.u32(root+0x1d0+4*i)) for i in self.roster_ids}
        require(all(mons[str(i)]['id']==i for i in self.roster_ids), 'battle owner recipient identity changed')
        require(ui==0 or (ui % 4 == 0 and 0x02000000 <= ui <= 0x023DC000-0x3f0),
                'garbage battle UI pointer')
        if ui==0:
            require(allow_absent_ui and not h.on_screen('battle_menu'), 'invalid battle UI context')
            return dict(field=False, **raw, ui_available=False, phase='ui_absent', mons=mons,
                        active=None, request=None, command_actor=None)
        active_address=h.u32(ui+0x1f4)
        raw['active_address']=active_address
        require(active_address==0 or (active_address % 4 == 0 and
                0x02000000 <= active_address <= 0x023DC000-0x2a0), 'garbage active BattleMon pointer')
        if active_address==0:
            require(allow_absent_ui and not h.on_screen('battle_menu'), 'active BattleMon not ready at command checkpoint')
            return dict(field=False, **raw, ui_available=False, phase='ui_not_ready', mons=mons,
                        active=None, request=None, command_actor=None)
        return dict(field=False, **raw, ui_available=True, phase='ui_ready',
                    active=mon_state(h, active_address),
                    request=h.u32(ui+0x3ec), command_actor=h.u8(ui+0x1b2),
                    mons=mons)

    def point(self, label, allow_absent_ui=False):
        self.index += 1
        row = dict(label=label, frame=self.h.frame)
        self.run.setdefault('input_states', []).append(row)
        raw={}
        try:
            row.update(self.state(allow_absent_ui, raw))
        except Exception as exc:
            row.update(raw, probe_error=str(exc))
            raise
        finally:
            self.s.checkpoint(f"{self.run['name']}-input-{self.index:02d}-{label}", self.run)
        return row

    def settle(self, label, max_frames=2400):
        # A advances text without cancelling a pending native target. A visible
        # menu alone is not success: callers also require action/PP/actor proof.
        for elapsed in range(0, max_frames, 15):
            self.h.step(15)
            if self.h.in_field(): return 'field'
            if self.h.on_screen('battle_menu'): return 'menu'
            if elapsed % 120 == 105:
                self.s.press('A', after=0)
        self.point(label+'-timeout', allow_absent_ui=True)
        raise AssertionError(label+' did not return within bounded input wait')

    def move(self, slot, move, actor, label):
        from emu_harness import BATTLE_BUTTONS, MOVE_BUTTONS
        require(self.h.on_screen('battle_menu'), 'move requires visible command menu')
        before_state = self.point(label+'-before')
        before = before_state['active']
        require(before['id'] == actor, 'wrong native actor before move')
        require(before_state['mons'][str(self.opponent_id)]['hp']==1, 'native opponent did not retain the pre-entry HP1 fixture')
        start = len(self.run['events'])
        self.s.touch(*BATTLE_BUTTONS['fight'], after=60)
        self.point(label+'-moves', allow_absent_ui=True)
        self.s.touch(*MOVE_BUTTONS[slot], after=80)
        selected = self.point(label+'-selected', allow_absent_ui=True)
        if not selected['field'] and selected['request']:
            # Actual targeting driver establishes R changes touch mode to key
            # mode without choosing another target; A confirms native default.
            self.s.press('R', after=40)
            self.point(label+'-target', allow_absent_ui=True)
            self.s.press('A', after=50)
            selected = self.point(label+'-confirmed', allow_absent_ui=True)
            if not selected['field'] and selected['request']:
                self.s.press('A', after=50)
                self.point(label+'-confirmed-again', allow_absent_ui=True)
        outcome = self.settle(label)
        after_state = self.point(label+'-after')
        # Native root is freed at victory; action hook captures the move record,
        # and a PP observation is taken at command1F before teardown for final KO.
        actions = [e for e in self.run['events'][start:] if e['name']=='action']
        if outcome == 'field':
            finals = [e for e in self.run['events'][start:] if e['name']=='award_actor' and e['actor']['id']==actor]
            require(finals, 'final KO lacks live native PP readback before free')
            after = finals[-1]['actor']
        else:
            after = after_state['active']
            old_hp, new_hp = before_state['mons'][str(self.opponent_id)]['hp'], after_state['mons'][str(self.opponent_id)]['hp']
            require(new_hp < old_hp if move==82 else new_hp==old_hp,
                    'submitted move did not produce the expected native opponent HP change')
        assert_move(before, after, actions, slot, move)
        self.trace.event('move_verified', actor=actor, move=move, before=before, after=after)
        return outcome

    def switch(self):
        from emu_harness import BATTLE_BUTTONS, PARTY_SLOTS
        before = self.point('switch-before')['active']
        require(before['id']==1, 'switch fixture must begin with fighter1')
        self.s.touch(*BATTLE_BUTTONS['pokemon'], after=120)
        self.point('switch-party', allow_absent_ui=True)
        self.s.touch(*PARTY_SLOTS[1], after=90)
        self.point('switch-submenu', allow_absent_ui=True)
        self.s.touch(128,108,after=90)  # native SHIFT, not an unobserved default A
        self.point('switch-shift', allow_absent_ui=True)
        require(self.settle('switch')=='menu', 'switch unexpectedly ended battle')
        after=self.point('switch-after')['active']
        require(after['id']==2, 'native SHIFT did not activate fighter2')
        self.trace.event('switch_verified', before=before, after=after)
