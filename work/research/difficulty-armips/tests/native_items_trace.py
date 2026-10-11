"""Read-only, candidate-code guarded ITEMS observations. No outcome writes."""
import hashlib
from native_battle_helpers import registers
from native_battle_input import mon_state as battle_mon_state
from native_battle_oracles import require


def ram_pointer(address, size, label):
    require(address % 4 == 0 and 0x02000000 <= address <= 0x023DC000-size,
            f'invalid {label} pointer {address:#x} (size {size:#x})')
    return address


def mon_state(h, address):
    ram_pointer(address,0x2a4,'item BattleMon')
    state = battle_mon_state(h, address)
    # 02216D28: active status i iff word(mon+3C+8*i)&7 != 0.
    state['statuses'] = [h.u32(address+0x3c+8*i) & 7 for i in range(1,6)]
    # Literal words in022170A8/02218E58 are252h, not25Ah. The shared
    # helper observes the original view; expose both explicitly for items.
    state.update(moves=[h.u16(address+0x252+18*i) for i in range(4)],
        pp=[h.u8(address+0x254+18*i) for i in range(4)],
        pp_max=[h.u8(address+0x255+18*i) for i in range(4)],
        original_moves=[h.u16(address+0x25a+18*i) for i in range(4)],
        original_pp=[h.u8(address+0x25c+18*i) for i in range(4)],
        original_pp_max=[h.u8(address+0x25d+18*i) for i in range(4)],
        pp_linked=[h.u8(address+0x262+18*i) for i in range(4)])
    return state


def read_inventory(h, bag, selected_item=17):
    """Bag has no capacity header: validate range then all physical slots.

    Native allocation/copy size864h; inventory occupies860h and the last four
    bytes are retained in the raw comparison. Never read null/ITCM as a Bag.
    """
    from emu_harness import POCKETS
    ram_pointer(bag,0x864,'battle Bag')
    raw = h.read(bag,0x864)
    require(len(raw) == 0x864, 'short native Bag read')
    matches = []
    for name,(offset,count) in POCKETS.items():
        seen=set()
        for slot in range(count):
            at=offset+4*slot
            item=int.from_bytes(raw[at:at+2],'little')
            quantity=int.from_bytes(raw[at+2:at+4],'little')
            require((item == quantity == 0) or (1 <= item <= 790 and 1 <= quantity <= 999),
                    f'invalid {name} slot{slot}: item={item}, quantity={quantity}')
            require(item == 0 or item not in seen, f'duplicate item in {name}')
            seen.add(item)
            if item == selected_item: matches.append((at,quantity))
    require(len(matches) == 1, 'selected item missing/ambiguous in full Bag')
    at, quantity = matches[0]
    return dict(bag_address=bag, bag_header=raw[:32].hex(), bag=raw.hex(),
                item=selected_item, quantity=quantity, item_offset=at)


class ItemsTrace:
    def __init__(self, session, run):
        self.s, self.h, self.run = session, session.h, run
        self.controller = None
        self.move_ui = None
        self.hp_watch = None
        for name in ('dg_battle_begin', 'dg_bag_item_attr', 'dg_bag_accept',
                     'dg_bag_commit_item', 'dg_bag_commit_target', 'dg_bag_remembered', 'dg_bag_effect_attr'):
            session.hook(session.labels[name] & ~1, getattr(self, name))
        for address, callback in ((0x02050C34, self.constructor), (0x02214CA6, self.captured),
                (0x02202954, self.parent), (0x02200A30, self.command),
                (0x02221674, self.effect), (0x02215A2C, self.consume),
                (0x0221D7A8, self.action), (0x02221CE8, self.status_effect),
                (0x022217C8, self.outcome), (0x02221B84, self.ordinary_hp),
                (0x02221936, self.failure_message), (0x02221F68, self.pp_one),
                (0x02221FFC, self.pp_all), (0x02221E30, self.revive),
                (0x022151A0, self.target_resolver),
                (0x02223610, self.revival_dispatch), (0x0222ADFC, self.revival_hp_call),
                (0x02217834, self.revival_hp_add),
                (0x0222A0A0, self.revival_adjust), (0x02224BF8, self.revival_event)):
            session.hook(address, callback)
        session.hook(0x021EC2CC, self.list_build, overlay=9)
        session.hook(0x021EB4D8, self.fade_close, overlay=9)
        session.hook(0x021E56FC, self.move_menu, overlay=9)
        session.hook(0x021E575A, self.move_selected, overlay=9)
        for address in (0xffff0004, 0xffff000c, 0xffff0010):
            session.hook(address, lambda: self.event('exception'))

    def event(self, name, **data):
        require(len(self.run['events']) < 6000, 'ITEMS bounded trace overflow')
        r = registers(self.h)
        row = dict(name=name, frame=self.h.frame, lr=r[14], sp=r[13], **data)
        self.run['events'].append(row)
        return row

    def snapshot(self):
        a = self.s.labels['snapshot']
        return dict(zip(('flags', 'cap', 'allowed', 'root', 'epoch'),
                        [self.h.u32(a+4*i) for i in range(5)]))

    def constructor(self):
        row = self.event('constructor', args=registers(self.h)[:4])
        def finish():
            setup = registers(self.h)[0]
            row.update(setup=setup, flags=self.h.u32(setup), control=self.h.u32(setup+0x18c))
        self.s.returned(finish)

    def dg_battle_begin(self):
        self.event('begin', snapshot=self.snapshot())

    def captured(self):
        h = self.h
        root = ram_pointer(h.u32(0x02255BAC),0x274,'battle root')
        setup = ram_pointer(h.u32(root+0x10),0x1d4,'battle setup')
        bag = h.u32(setup+0x108)
        info = h.u32(setup+0xf8)
        self.event('bag_binding',root=root,setup=setup,bag=bag,trainer_info=info)
        ram_pointer(bag,0x864,'battle Bag')
        ram_pointer(info,0x20,'TrainerInfo')
        self.event('captured', snapshot=self.snapshot(), generation=h.u32(self.s.labels['generation']),
            setup_owner=h.u32(self.s.labels['setup_owner']), save_owner=h.u32(self.s.labels['save_owner']),
            context=dict(root=root, setup=setup, flags=h.u32(setup), control=h.u32(setup+0x18c),
                save=h.u32(setup+0x1c0), published_save=h.save, trainer_info=info,
                bag=bag, options_copy=h.u16(h.u32(setup+0x130))))

    def args(self, address):
        h = self.h
        ram_pointer(address,0x30,'Bag args')
        return dict(address=address, trainer_info=h.u32(address), bag=h.u32(address+4),
            heap=h.u32(address+8), owner=h.u32(address+0xc), tutorial=h.u32(address+0x10),
            item=h.u16(address+0x18), category=h.u8(address+0x1a),
            remembered=h.u16(address+0x1c))

    def fade_close(self):
        # State13 is also the successful Use fade, not a denial indicator.
        ui = ram_pointer(registers(self.h)[0],4,'Bag UI')
        self.event('fade_close_state13', args=self.args(self.h.u32(ui)))

    def parent(self):
        self.controller = registers(self.h)[0]

    def command_state(self):
        h, c = self.h, self.controller
        require(c is not None, 'native Bag parent controller not observed')
        dest = h.u32(c+0x588)
        require(0x02000000 <= dest <= 0x023DC000-12, 'invalid native command destination')
        actor = ram_pointer(h.u32(c+0x584),0x18,'command actor')
        return dict(controller=c, actor=actor, actor_id=h.u8(actor+0x14), owner=h.u8(c+2),
            slot=h.u8(c+0x599), destination=dest, command=h.read(dest,12).hex())

    def dg_bag_item_attr(self):
        item, attr, heap, ui = registers(self.h)[:4]
        if attr != 13: return
        row = self.event('mask', item=item, heap=heap, ui=ui, args=self.args(self.h.u32(ui)))
        self.s.returned(lambda: row.update(result=registers(self.h)[0]))

    def list_build(self):
        ui = registers(self.h)[0]
        def finish():
            counts = list(self.h.read(ui+0x114f, 5))
            require(all(n <= 36 for n in counts), 'native list overflow')
            lists = [[dict(item=self.h.u16(ui+0x3c+0x90*c+4*i),
                           quantity=self.h.u16(ui+0x3e+0x90*c+4*i)) for i in range(n)]
                     for c,n in enumerate(counts)]
            self.event('lists', ui=ui, args=self.args(self.h.u32(ui)), counts=counts, lists=lists,
                       command=self.command_state())
        self.s.returned(finish, overlay=9)

    def dg_bag_accept(self):
        ui = registers(self.h)[0]; args = self.h.u32(ui)
        row = self.event('accept', before=self.args(args))
        self.s.returned(lambda: row.update(result=registers(self.h)[0], after=self.args(args)))

    def dg_bag_remembered(self):
        r = registers(self.h)
        row = self.event('remembered', bag=r[0], item=r[1], quantity=r[2], heap=r[3])
        self.s.returned(lambda: row.update(result=registers(self.h)[0]))

    def dg_bag_commit_item(self):
        args = registers(self.h)[0]
        row = self.event('commit_item', before=self.args(args), command=self.command_state())
        self.s.returned(lambda: row.update(result=registers(self.h)[0], after=self.args(args)))

    def dg_bag_commit_target(self):
        controller, party = registers(self.h)[:2]
        self.controller = controller
        row = self.event('commit_target', target=self.h.u8(party+0xd),
                         party=self.party_args(party),
                         before=self.args(self.h.u32(controller+0x5c8)), command=self.command_state())
        self.s.returned(lambda: row.update(result=registers(self.h)[0]))

    def party_mapping(self):
        h = self.h; c = self.controller
        require(c is not None, 'party mapping requires native parent')
        args = self.party_args(h.u32(c+0x5c4))
        roster = ram_pointer(h.u32(c+0x1c),0x1c,'parent party roster')
        count = h.u8(roster+0x18)
        party = ram_pointer(args['party'],8+236*6,'temporary UI party')
        require(count == h.u32(party+4) == 3 and h.u32(party) == 6,
                'unexpected native roster/UI party allocation')
        entries = []
        for slot in range(count):
            mon = ram_pointer(h.u32(roster+4*slot),0x20,'roster BattleMon')
            backing = ram_pointer(h.u32(mon+0x10),236,'roster backing record')
            copied = party+8+236*slot
            entries.append(dict(ui_slot=slot,mon=mon,id=h.u8(mon+0x14),hp=h.u16(mon+0x1e),
                maxhp=h.u16(mon+0x1c),backing=backing,copied=copied,
                source_sha256=hashlib.sha256(h.read(backing,236)).hexdigest(),
                copy_sha256=hashlib.sha256(h.read(copied,236)).hexdigest()))
        return self.event('party_mapping',controller=c,roster=roster,count=count,args=args,entries=entries)

    def target_resolver(self):
        r = registers(self.h)
        # The same getter is used elsewhere. Only this parent's accepted
        # target call02202C06 proves UI index -> native recipient identity.
        if r[14] != 0x02202C0B:return
        row = self.event('target_resolved',roster=r[0],ui_slot=r[1])
        def finish():
            mon = ram_pointer(registers(self.h)[0],0x20,'resolved item target')
            row.update(mon=mon,id=self.h.u8(mon+0x14),hp=self.h.u16(mon+0x1e),
                       backing=self.h.u32(mon+0x10))
        self.s.returned(finish)

    def watch_revive_hp(self, before):
        """Diagnostic only: no expected value inference and no memory writes."""
        from native_items_cases import case_for
        case = case_for(self.run)
        if case['kind'] != 'revive' or not self.run['flags'] & 4:return
        require(self.hp_watch is None, 'duplicate revival HP watch')
        mon = before['mons'][str(case['target_slot']+1)]['address']
        address = ram_pointer(mon,0x20,'watched revival target')+0x1e
        self.hp_watch = address
        self.event('revive_hp_watch_start',address=address,mon=mon,hp=self.h.u16(address))
        def changed(written, size):
            # Match Harness.on_exec's exception bridge: ctypes must never
            # swallow diagnostic errors and permit an apparently valid run.
            if self.h._hook_error is not None:return
            try:
                r = registers(self.h); pc = r[15] & ~1
                code_start = pc-16
                require(0x02000000 <= code_start <= 0x023DC000-48,
                        'HP write PC outside captured native code')
                self.event('revive_hp_write',address=address,written=written,size=size,
                    observed_hp=self.h.u16(address),registers=r,code_start=code_start,
                    code=self.h.read(code_start,48).hex(),
                    stack=self.h.read(r[13],64).hex() if 0x02000000 <= r[13] <= 0x02800000-64 else None)
            except BaseException as exc:
                self.h._hook_error = (address,exc)
        self.h.emu.memory.register_write(address,changed,size=2)

    def stop_hp_watch(self):
        if self.hp_watch is None:return
        address = self.hp_watch
        self.h.emu.memory.register_write(address,None,size=2)
        self.hp_watch = None
        self.event('revive_hp_watch_stop',address=address,hp=self.h.u16(address))

    def revival_dispatch(self):
        if self.hp_watch is None:return
        address = ram_pointer(registers(self.h)[0],0x50,'revival dispatch arguments')
        row = self.event('revival_dispatch',address=address,data=self.h.read(address,0x50).hex(),
                         hp=self.h.u16(self.hp_watch))
        self.s.returned(lambda:row.update(result=registers(self.h)[0],after_hp=self.h.u16(self.hp_watch)))

    def revival_adjust(self):
        r = registers(self.h)
        if self.hp_watch is None or r[0]+0x1e != self.hp_watch:return
        row = self.event('revival_adjust',registers=r,hp=self.h.u16(self.hp_watch))
        self.s.returned(lambda:row.update(after_hp=self.h.u16(self.hp_watch)))

    def revival_event(self):
        r = registers(self.h)
        if self.hp_watch is not None and r[0] == 0x31:
            self.event('revival_event31',registers=r,hp=self.h.u16(self.hp_watch))

    def revival_hp_add(self):
        r = registers(self.h)
        if self.hp_watch is None or r[0]+0x1e != self.hp_watch:return
        row = self.event('revival_hp_add',mon=r[0],amount=r[1],hp=self.h.u16(self.hp_watch))
        self.s.returned(lambda:row.update(result=registers(self.h)[0],after_hp=self.h.u16(self.hp_watch)))

    def revival_hp_call(self):
        if self.hp_watch is None:return
        r = registers(self.h)
        row = self.event('revival_hp_call',recipient=r[0],amount=r[1],hp=self.h.u16(self.hp_watch))
        self.s.returned(lambda:row.update(result=registers(self.h)[0],after_hp=self.h.u16(self.hp_watch)))

    def party_args(self, address):
        h = self.h
        ram_pointer(address,0x34,'item party args')
        return dict(address=address, party=h.u32(address), target=h.u8(address+0xd),
            item=h.u16(address+0x1e), owner=h.u32(address+0x24),
            category=h.u8(address+0x2f), move_slot=h.u8(address+0x30),
            complete=h.u8(address+0x32))

    def move_menu(self):
        ui = registers(self.h)[0]
        if self.move_ui != ui:
            self.move_ui = ui
            self.event('move_menu',ui=ui,party=self.party_args(self.h.u32(ui)))

    def move_selected(self):
        r = registers(self.h)
        # Native strb at575E writes r5 to args+30; observe before the write.
        self.event('move_selected',slot=r[5],party=self.party_args(self.h.u32(r[4])))

    def dg_bag_effect_attr(self):
        r=registers(self.h)
        if r[1] not in (23,38):return
        require(r[13]%4==0 and 0x02000000<=r[13]<=0x02800000-4,'invalid effect attr stack')
        target=ram_pointer(self.h.u32(r[13]),0x20,'effect attr target')
        actor=ram_pointer(r[3],0x20,'effect attr actor')
        row=self.event('effect_attr',item=r[0],attr=r[1],heap=r[2],actor=actor,target=target,
                       actor_id=self.h.u8(actor+0x14),target_id=self.h.u8(target+0x14))
        self.s.returned(lambda:row.update(result=registers(self.h)[0]))

    def ordinary_hp(self):self.effect_callback('ordinary_hp')

    def failure_message(self):
        r=registers(self.h)
        self.event('failure_message',actor_id=r[0],message=r[1])

    def outcome(self):
        r = registers(self.h)
        require(r[14] == 0x022216AF and r[13] % 4 == 0 and
                0x02000000 <= r[13] <= 0x02800000-0x20, 'unexpected native item outcome caller/stack')
        address = self.h.u32(r[13]+4)
        require(address == r[13]+0x14, 'item outcome pointer does not belong to caller frame')
        row = self.event('outcome',address=address,actor=mon_state(self.h,r[0]),
                         item=r[1],move_slot=r[2],target_id=r[3])
        self.s.returned(lambda:row.update(words=[self.h.u32(address+4*i) for i in range(3)]))

    def effect_callback(self, name):
        r = registers(self.h); address = r[0]
        row = self.event(name,item=r[1],move_slot=r[3],before=mon_state(self.h,address))
        self.s.returned(lambda:row.update(result=registers(self.h)[0],after=mon_state(self.h,address)))

    def pp_one(self): self.effect_callback('pp_one')
    def pp_all(self): self.effect_callback('pp_all')
    def revive(self): self.effect_callback('revive')

    def command(self):
        r = registers(self.h); dest = r[0]
        row = self.event('command', destination=dest, item=r[1], target=r[2], move_slot=r[3],
                         before=self.h.read(dest,12).hex())
        self.s.returned(lambda: row.update(after=self.h.read(dest,12).hex()))

    def effect(self):
        r = registers(self.h)
        self.event('effect', actor=mon_state(self.h,r[0]), item=r[1], move_slot=r[2], target_id=r[3])

    def status_effect(self):
        r = registers(self.h); address = r[0]
        row = self.event('status_effect', status_id=r[3], before=mon_state(self.h,address))
        self.s.returned(lambda: row.update(result=registers(self.h)[0], after=mon_state(self.h,address)))

    def consume(self):
        owner, item = registers(self.h)[:2]
        self.event('consume', owner=owner, item=item)

    def action(self):
        r = registers(self.h)
        self.event('action', actor=mon_state(self.h,r[0]), move=self.h.u16(r[1]))

    def state(self):
        h = self.h; root = h.u32(0x02255BAC)
        require(root == self.snapshot()['root'] and self.snapshot()['epoch'] > 0,
                'ITEMS state requires current native battle root')
        ram_pointer(root,0x274,'battle root')
        setup = ram_pointer(h.u32(root+0x10),0x1d4,'battle setup')
        bag = h.u32(setup+0x108)
        self.event('inventory_probe',root=root,setup=setup,bag=bag)
        inventory = read_inventory(h,bag,self.run['item'])
        # This fixture stocks one selected item and no other items. Record the
        # entire native bag so an unrelated inventory mutation cannot be hidden.
        return dict(mons={str(i):mon_state(h,h.u32(root+0x1d0+4*i)) for i in (1,2,3,13)},
            **inventory, snapshot=self.snapshot())
