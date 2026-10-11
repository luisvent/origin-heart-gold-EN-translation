"""Malformed remembered-input slice; authentic two-battle persistence is separate."""
from copy import deepcopy
from native_battle_helpers import registers
from native_battle_oracles import require
from native_items_trace import ram_pointer
from native_items_gates_trace import GateTrace
from native_items_gates_oracles import actor_identity
from native_items_oracles import events, trainer_entry


class RememberedTrace(GateTrace):
    def __init__(self,session,run):
        super().__init__(session,run)
        session.hook(0x021EC250,self.remembered_input,overlay=9)
        session.hook(0x02076B20,self.native_count)

    def metadata(self):
        if self.in_gate:
            self.event('fault_metadata',item=registers(self.h)[0],attr=registers(self.h)[1])

    def native_count(self):
        if self.in_gate:
            self.event('fault_count',bag=registers(self.h)[0],item=registers(self.h)[1])

    def remembered_input(self):
        if not self.armed:return
        require(not self.injected,'duplicate remembered injection')
        self.armed=False;self.injected=True;self.in_gate=True
        r=registers(self.h);ui=ram_pointer(r[0],4,'remembered UI')
        args=ram_pointer(self.h.u32(ui),0x30,'remembered args');old=self.args(args)
        require(old['owner']==old['tutorial']==old['remembered']==0 and
                old['bag']==self.run['before']['bag_address'],'unexpected remembered fixture/owner')
        row=self.event('remembered_fault_input',kind='nativeFaultInput',item=self.run['fault_item'],
            seam=0x021EC250,ui=ui,address=args,before=self.h.read(args,0x30).hex(),
            registers_before=r,command_before=self.command_state(),snapshot=self.snapshot(),
            actor_binding=self.actor_binding())
        # Input before021EC256 ldrh. No register, inventory, eligibility or result writes.
        self.h.write(args+0x1c,self.run['fault_item'].to_bytes(2,'little'))
        row.update(after=self.h.read(args,0x30).hex(),registers_after=registers(self.h),
                   command_after=self.command_state())
        def finish():
            row.update(result=registers(self.h)[0],returned=self.h.read(args,0x30).hex(),
                       args_after=self.args(args),command_return=self.command_state())
            self.in_gate=False
        self.s.returned(finish,overlay=9)

    def dg_bag_remembered(self):
        r=registers(self.h)
        if self.in_gate:
            # Wrapper's fifth UI argument on the aligned AAPCS stack.
            require(r[13]%4==0 and 0x02000000<=r[13]<=0x02800000-4,'invalid remembered stack')
            ui=ram_pointer(self.h.u32(r[13]),4,'remembered wrapper UI')
            row=self.event('remembered_wrapper_input',bag=r[0],item=r[1],quantity=r[2],heap=r[3],
                           ui=ui,args=self.args(self.h.u32(ui)))
            self.s.returned(lambda:row.update(result=registers(self.h)[0]))
        super().dg_bag_remembered()


def denied(run):
    trainer_entry(run)
    rows=events(run,'remembered_fault_input');require(len(rows)==1,'missing/duplicate remembered fault')
    e=rows[0];item=run['fault_item']
    require(item in (791,65535) and e['item']==item and e['kind']=='nativeFaultInput' and
            e['seam']==0x021EC250,'wrong remembered input seam/ID')
    old=bytes.fromhex(e['before']);injected=bytes.fromhex(e['after']);returned=bytes.fromhex(e['returned'])
    expected=bytearray(old);expected[0x1c:0x1e]=item.to_bytes(2,'little')
    require(len(old)==len(injected)==len(returned)==0x30 and old[0x1c:0x1e]==b'\0\0' and
            injected==expected,'remembered injection changed non-input bytes or reseeded stale fixture')
    expected[0x1b:0x1e]=bytes(3)
    require(returned==expected and e['result']==0 and e['args_after']['remembered']==0,
            'native remembered validator did not clear ID/category itself')
    require(e['address']%4==0 and 0x02000000<=e['address']<=0x023DC000-0x30,
            'invalid remembered args pointer')
    require(e['registers_before']==e['registers_after'],'remembered fault modified registers')
    command=e['command_before']
    require(command==e['command_after']==e['command_return']==run['command_denied'],
            'remembered validation changed command/owner/slot')
    require(run['before']==run['denied'] and e['snapshot']==run['before']['snapshot'] and
            e['snapshot']['flags']==0 and e['snapshot']['allowed']==1,'remembered validation changed state/context')
    actor_identity(e['actor_binding'],command,run['before']['mons']['1'])
    require(e['actor_binding']['root']==e['snapshot']['root'],'remembered actor from another battle')
    wrappers=events(run,'remembered_wrapper_input');require(len(wrappers)==1,'missing/duplicate wrapper lookup')
    w=wrappers[0]
    require(w['item']==item and w['quantity']==1 and w['result']==0 and
            w['ui']==e['ui'] and w['bag']==run['before']['bag_address'] and
            w['args']['address']==e['address'] and w['args']['remembered']==item and
            w['args']['owner']==w['args']['tutorial']==0,'remembered wrapper did not receive actual injected input')
    lookups=events(run,'controller_actor_lookup')
    require(any(x['view']==e['actor_binding']['view'] and x['owner']==x['slot']==0 and
                x.get('result')==command['actor'] for x in lookups),'missing native actor lookup')
    for name in ('fault_metadata','fault_count','fault_input','command','effect','consume','outcome',
                 'action','accept','commit_target','slot_advance','exception'):
        require(not events(run,name),'invalid remembered input reached '+name)
    lists=events(run,'lists')
    require(lists and all(x['args']['remembered']==0 and x['lists'][1]==[dict(item=151,quantity=3)] and
            not any(y['item']==17 or y['item']>790 for ls in x['lists'] for y in ls) for x in lists),
            'remembered list retained invalid shortcut or lost native filtering')
    require(any(x['handler']==0x02202445 for x in events(run,'schedule')),'Back continuation missing')


def continued(run):
    denied(dict(run,events=run['events'][:run['denied_event_count']]))
    expected=deepcopy(run['denied'])
    for key in ('1','13'):
        expected['mons'][key]['pp'][0]-=1;expected['mons'][key]['original_pp'][0]-=1
    require(run['after']==expected,'remembered continuation changed unrelated state/inventory')
    actions=events(run,'action')
    require(len(actions)==2 and sorted((x['actor']['id'],x['move']) for x in actions)==[(1,150),(13,150)],
            'remembered continuation did not execute one Splash per actor')
    require(not any(events(run,n) for n in ('command','effect','consume','outcome','exception')),
            'remembered item escaped to later execution')
