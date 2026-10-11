"""Native fault INPUT is the sole live mutation; all other probes read only."""
import hashlib
from native_items_trace import ItemsTrace, ram_pointer, mon_state
from native_battle_helpers import registers
from native_battle_oracles import require


class GateTrace(ItemsTrace):
    def __init__(self,session,run):
        self.armed=False;self.injected=False;self.in_gate=False
        super().__init__(session,run)
        session.hook(0x02230920,self.actor_lookup)
        session.hook(0x02076410,self.metadata)
        session.hook(0x021EB298,self.native_accept,overlay=9)
        session.hook(0x02201FE0,self.schedule)
        session.hook(0x02202166,self.slot_advance)

    def actor_lookup(self):
        r=registers(self.h)
        if r[14]!=0x02202083:return
        row=self.event('controller_actor_lookup',view=r[0],owner=r[1],slot=r[2])
        self.s.returned(lambda:row.update(result=registers(self.h)[0]))

    def actor_binding(self):
        # Native0220207E ->02230920 ->022151A0 selects from UI view's
        # owner roster.02215170(1)=root+54; (0)=root+144. Engine's ID
        # table is view+8C=root+1D0. Distinct clones must not be pointer-equal.
        h=self.h;command=self.command_state();root=self.snapshot()['root']
        c=command['controller'];view=ram_pointer(h.u32(c+0x28),0xf0,'controller recipient view')
        owner,slot=command['owner'],command['slot']
        require(view==root+0x54 and owner==slot==0,'unexpected singles controller view/owner/slot')
        roster=ram_pointer(view+0xc+0x1c*owner,0x1c,'controller active roster')
        count=h.u8(roster+0x18)
        require(slot<count<=6,'controller actor slot outside native roster')
        ui=ram_pointer(h.u32(roster+4*slot),0x2a4,'UI actor')
        require(ui==command['actor'],'native roster disagrees with controller actor')
        rid=h.u8(ui+0x14);require(1<=rid<=6,'nonlocal UI actor')
        ui_table=ram_pointer(h.u32(view+0x8c+4*rid),0x2a4,'UI ID resolver')
        engine=ram_pointer(h.u32(root+0x1d0+4*rid),0x2a4,'engine ID resolver')
        ub=ram_pointer(h.u32(ui+0x10),236,'UI actor backing')
        eb=ram_pointer(h.u32(engine+0x10),236,'engine actor backing')
        row=dict(root=root,view=view,roster=roster,count=count,owner=owner,slot=slot,
            ui=ui,ui_table=ui_table,engine=engine,id=rid,ui_backing=ub,engine_backing=eb,
            ui_backing_sha256=hashlib.sha256(h.read(ub,236)).hexdigest(),
            engine_backing_sha256=hashlib.sha256(h.read(eb,236)).hexdigest(),
            ui_state=mon_state(h,ui),engine_state=mon_state(h,engine))
        self.run.setdefault('actor_bindings',[]).append(row)
        return row

    def metadata(self):
        if self.in_gate and registers(self.h)[0]==self.run['fault_item']:
            self.event('fault_metadata',item=registers(self.h)[0],attr=registers(self.h)[1])

    def native_accept(self):
        if self.in_gate:self.event('blocked_native_accept')

    def schedule(self):
        if self.injected:self.event('schedule',controller=registers(self.h)[0],handler=registers(self.h)[1])

    def slot_advance(self):
        if self.injected:self.event('slot_advance',registers=registers(self.h))

    def fault(self,gate,args,target=None):
        if not self.armed or gate!=self.run['gate']:return
        require(not self.injected,'duplicate armed input injection')
        self.armed=False;self.injected=True;self.in_gate=True
        ram_pointer(args,0x30,'fault Bag args');old=self.args(args)
        state=self.command_state();snap=self.snapshot()
        require(old['owner']==old['tutorial']==state['owner']==0 and snap['flags']==0 and snap['allowed']==1,
                'fault not in owned restricted Bag')
        require(old['bag']==self.run['before']['bag_address'] and
                old['item']==(0 if gate=='item' else 151) and old['category']==(4 if gate=='item' else 1),
                'unexpected pre-fault native selection')
        require(state['actor_id']==1 and state['slot']==0,'wrong fault actor/slot')
        if gate=='target':require(target is not None and target<6,'target was already cancelled')
        row=self.event('fault_input',kind='nativeFaultInput',gate=gate,item=self.run['fault_item'],
            address=args,before=self.h.read(args,0x30).hex(),registers_before=registers(self.h),
            command_before=state,snapshot=snap,target=target,actor_binding=self.actor_binding())
        # Exactly the selected-item INPUT bytes. No register/command/outcome edits.
        self.h.write(args+0x18,self.run['fault_item'].to_bytes(2,'little')+b'\0')
        row.update(after=self.h.read(args,0x30).hex(),registers_after=registers(self.h),
                   command_after=self.command_state())
        def finish():
            row.update(result=registers(self.h)[0],args_after=self.args(args),command_return=self.command_state())
            self.in_gate=False
        self.s.returned(finish)

    def dg_bag_accept(self):
        self.fault('accept',self.h.u32(registers(self.h)[0]));super().dg_bag_accept()

    def dg_bag_commit_item(self):
        self.fault('item',registers(self.h)[0]);super().dg_bag_commit_item()

    def dg_bag_commit_target(self):
        c,p=registers(self.h)[:2];self.controller=c
        self.fault('target',self.h.u32(c+0x5c8),self.h.u8(p+0xd));super().dg_bag_commit_target()
