"""Actual native per-opponent records and award-group boundaries; read only."""
from native_battle import BattleTrace
from native_battle_helpers import registers
from native_battle_oracles import require
from native_battle_input import BattleInput, mon_state
from native_items_trace import ram_pointer


def opponent_binding(proof, snapshot, view, count, pointer, rid):
    """Full two-member roster plus an observed native singles position lookup."""
    require(count==2,'trainer6 UI opponent roster size changed')
    require(proof is not None,'native opponent position lookup missing')
    require(proof.get('snapshot')==snapshot and proof.get('view')==view,
            'stale native opponent position lookup')
    require((proof.get('position'),proof.get('owner'),proof.get('slot'))==(1,1,0),
            'native singles opponent owner/slot mismatch')
    require(proof.get('result')==pointer and proof.get('id')==rid,
            'native opponent position lookup no longer matches live roster')


class MultiTrace(BattleTrace):
    def __init__(self,session):
        super().__init__(session)
        self.group=None;self.group_count=0;self.pending_aggregates=[];self.aggregate_scope=None
        self.position_scope=None;self.opponent_position=None
        self.ev_scope=None
        session.hook(0x022288E8,self.aggregate)
        session.hook(0x0221F5E8,self.award_group)
        session.hook(0x02228910,self.temporary)
        session.hook(0x0222896E,self.combined)
        session.hook(0x022151D0,self.position_resolver)
        session.hook(0x02228580,self.position_mapping)
        session.hook(0x0221F68A,lambda:self.ev_branch('apply'))
        session.hook(0x0221F6DA,self.ev_iteration_end)

    def native_eligible(self):
        r=registers(self.h)
        if self.run is None or r[14]!=0x0221F687:
            return super().native_eligible()
        require(self.group is not None and self.ev_scope is None,'unbound/nested native EV eligibility')
        amount,deferred,mon,raw=r[:4]
        rid=self.h.u8(mon+0x14);root=self.snapshot()['root']
        require(self.h.u32(root+0x1d0+4*rid)==mon,'EV eligibility recipient ownership mismatch')
        row=self.event('ev_eligible',id=rid,mon=mon,raw_address=raw,
                       raw_before=self.h.read(raw,16).hex(),snapshot=self.snapshot(),calls=0)
        self.ev_scope=row
        self.s.returned(lambda:row.update(result=registers(self.h)[0],amount=self.h.u32(amount),
            deferred=self.h.u32(deferred),raw_after=self.h.read(raw,16).hex()))

    def ev_branch(self,branch):
        require(self.ev_scope is not None,'EV branch outside native eligibility lifetime')
        self.ev_scope['branch']=branch

    def ev_iteration_end(self):
        require(self.ev_scope is not None,'EV iteration outside native eligibility lifetime')
        self.ev_scope.setdefault('branch','skip')
        self.ev_scope=None

    def ev(self):
        if self.run is None:return
        r=registers(self.h);scope=self.ev_scope
        require(scope is not None and r[14]==0x0221F6AB and r[0]==scope['id'],
                'EV application lacks exact native eligibility caller/recipient')
        scope['calls']+=1
        super().ev();row=self.run['events'][-1];mon=scope['mon']
        row.update(mon=mon,before=self.ev_storage(mon))
        self.s.returned(lambda:row.update(after=self.ev_storage(mon)))

    def ev_storage(self,mon):
        # Native02218A7C updates mon+248 total, +24A..24F HP/Atk/Def/Speed/SpA/SpD.
        return dict(total=self.h.u16(mon+0x248),values=list(self.h.read(mon+0x24a,6)))

    def position_resolver(self):
        if self.run is None:return
        r=registers(self.h);snapshot=self.snapshot()
        if not snapshot['allowed'] or r[0]!=snapshot['root']+0x54 or r[1]!=1:return
        require(self.position_scope is None,'nested opponent position lookup')
        row=self.event('opponent_position',view=r[0],position=r[1],snapshot=snapshot)
        self.position_scope=row
        def finish():
            pointer=registers(self.h)[0]
            row.update(result=pointer,id=self.h.u8(pointer+0x14) if pointer else None)
            self.opponent_position=row
            self.position_scope=None
        self.s.returned(finish)

    def position_mapping(self):
        # Only the mapper invoked inside this exact native resolver lifetime.
        # 022151DE BL02228580 returns to022151E2; output bytes are on its stack.
        row=self.position_scope;r=registers(self.h)
        if row is None or r[14]!=0x022151E3:return
        require(r[0]==row['position'],'native position mapper argument mismatch')
        owner,slot=r[1:3]
        row.update(owner_address=owner,slot_address=slot)
        self.s.returned(lambda:row.update(owner=self.h.u8(owner),slot=self.h.u8(slot)))

    def event(self,name,**data):
        return super().event(name,group=self.group,**data)

    def reset(self):
        require(self.group is None and self.pending is None and self.free_scope is None,'unfinished trace lifetime')
        require(not self.pending_aggregates and self.aggregate_scope is None,
                'unconsumed native reward inputs')
        require(self.position_scope is None,'unfinished native opponent resolver')
        require(self.ev_scope is None,'unfinished native EV eligibility iteration')
        self.opponent_position=None
        self.group_count=0

    def engine(self):
        from emu_harness import decode_pokemon
        h=self.h;root=ram_pointer(h.u32(0x02255bac),0x274,'reward root')
        require(root==self.snapshot()['root'],'reward root ownership changed')
        rows=[]
        for i in (1,2,3):
            mon=ram_pointer(h.u32(root+0x1d0+4*i),0x2a4,'reward recipient')
            require(h.u8(mon+0x14)==i,'reward recipient ID mismatch')
            backing=ram_pointer(h.u32(mon+0x10),236,'reward backing')
            d=decode_pokemon(h.read(backing,236))
            rows.append(dict(id=i,mon=mon,cache=h.u32(mon+0x18),backing=backing,
                exp=d['exp'],level=d['level'],evs=d['evs'],ev_storage=self.ev_storage(mon),
                checksum_ok=d['checksum_ok']))
        return rows

    def calculate(self):
        if self.run is None:return
        raw,mon,opponent=registers(self.h)[:3]
        super().calculate()
        row=self.run['events'][-1]
        row.update(opponent_id=self.h.u8(opponent+0x14),raw_address=raw)
        self.s.returned(lambda:row.update(raw_calculated=self.h.read(raw,16).hex()))

    def aggregate(self):
        if self.run is None:return
        array,args=registers(self.h)[:2];opponent=self.h.u32(args+4)
        row=self.event('aggregate',array=array,opponent=opponent,opponent_id=self.h.u8(opponent+0x14),
                       before=self.h.read(array,96).hex())
        require(self.aggregate_scope is None,'nested opponent aggregation')
        self.aggregate_scope=row
        row['ordinal']=len([e for e in self.run['events'] if e['name']=='aggregate'])
        def finish():
            row['after']=self.h.read(array,96).hex()
            self.pending_aggregates.append(row)
            self.aggregate_scope=None
        self.s.returned(finish)

    def temporary(self):
        if self.aggregate_scope is not None:
            address=registers(self.h)[4]
            self.aggregate_scope.update(temporary_address=address,temporary=self.h.read(address,96).hex())

    def combined(self):
        if self.aggregate_scope is not None:
            self.aggregate_scope['combined']=self.h.read(self.aggregate_scope['array'],96).hex()

    def award_group(self):
        if self.run is None:return
        require(self.group is None,'nested native award group')
        roster,array=registers(self.h)[:2]
        count=self.h.u8(roster+0x18)
        require(count==3,'award roster must retain three local recipients')
        self.group_count+=1;self.group=self.group_count
        rows=[]
        for slot in range(count):
            mon=self.h.u32(roster+4*slot)
            rows.append(dict(slot=slot,id=self.h.u8(mon+0x14),mon=mon,
                             raw=self.h.read(array+16*slot,16).hex()))
        aggregates=list(self.pending_aggregates);self.pending_aggregates.clear()
        row=self.event('award_group',roster=roster,array=array,rows=rows,before=self.engine(),
                       raw_before=self.h.read(array,96).hex(),
                       aggregates=[a['ordinal'] for a in aggregates])
        def finish():
            row.update(after=self.engine(),raw_after=self.h.read(array,96).hex())
            self.event('award_group_end')
            self.group=None
        self.s.returned(finish)


class MultiInput(BattleInput):
    opponent_id=13
    roster_ids=(1,2,3,13,14)

    def state(self,allow_absent_ui=False,raw=None):
        row=super().state(allow_absent_ui,raw)
        # Only real command checkpoints require an active opponent object.
        # Animation/party transitions keep the base probe's not-ready semantics.
        if not row.get('field') and row.get('ui_available') and self.h.on_screen('battle_menu'):
            h=self.h;view=row['root']+0x54;roster=view+0xc+0x1c
            pointer=h.u32(roster);count=h.u8(roster+0x18)
            if raw is not None:raw.update(enemy_roster=roster,enemy_pointer=pointer,enemy_count=count,
                                         enemy_position=self.trace.opponent_position)
            # 022150CA..0221511C appends every party member and increments +18.
            # 022151D0 resolves a battle position via02228580, then indexes that
            # full roster. A singles trainer with two Pokemon still has count2.
            active=mon_state(h,pointer);rid=active['id']
            opponent_binding(self.trace.opponent_position,self.trace.snapshot(),view,count,pointer,rid)
            require(rid in (13,14) and h.u32(view+0x8c+4*rid)==pointer,'native active opponent ID table mismatch')
            require(row['mons'][str(rid)]['hp']==active['hp'],'UI/engine opponent HP mismatch')
            row['enemy_active']=active
        return row

    def move(self,slot,move,actor,label):
        state=self.point(label+'-opponent-proof')
        require(state['enemy_active']['id']==self.opponent_id and state['enemy_active']['hp']==1,
                'wrong active native opponent before move')
        outcome=super().move(slot,move,actor,label)
        if move==82:
            if self.opponent_id==13:
                require(outcome=='menu','first KO ended trainer battle')
                state=self.point('second-opponent-menu')
                require(state['enemy_active']['id']==14 and state['mons']['13']['hp']==0 and
                        state['active']['id']==2,'native opponent replacement or actor continuity failed')
            else:require(outcome=='field','second KO did not end trainer battle')
            self.trace.event('ko_verified',opponent_id=self.opponent_id,actor=actor,outcome=outcome)
        return outcome
