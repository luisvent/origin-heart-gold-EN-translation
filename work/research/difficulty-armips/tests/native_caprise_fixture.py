"""Read-only field continuity records and exactly one between-battle badge input."""
from native_battle_oracles import require


def field_state(session,trace,options):
    import save_core
    from emu_harness import ARR_PARTY, ARR_BAG, ARR_VARS_FLAGS
    h=session.h
    require(trace.run is None and trace.free_scope is None and h.in_field() and
            trace.snapshot()==dict(flags=0,cap=0,allowed=0,root=0,epoch=0),
            'continuity checkpoint requires completed field lifetime')
    def pointer(address,size):
        require(address%4==0 and 0x02000000<=address<=0x023DC000-size,'invalid field owner')
        return address
    party=pointer(h.array(ARR_PARTY),8+6*236)
    require(h.u32(party)==6 and h.u32(party+4)==3,'continuity party shape changed')
    raw=h.read(party,8+6*236)
    mons=[save_core.request('decodePokemon',raw[8+i*236:8+(i+1)*236],diagnostic=False) for i in range(3)]
    require(all(m['flags']==0 and m['checksumOk'] and not m['isEgg'] for m in mons),
            'invalid closed continuity party; no repair')
    bag=pointer(h.array(ARR_BAG),0x864)
    profile=pointer(h.array(1)+4,32)
    variables=pointer(h.array(ARR_VARS_FLAGS),0x379)
    return dict(frame=h.frame,save=h.save,party=party,party_raw=raw.hex(),mons=mons,
                bag=bag,bag_raw=h.read(bag,0x864).hex(),profile=profile,profile_raw=h.read(profile,32).hex(),
                vars=variables,vars_raw=h.read(variables,0x379).hex(),
                options_address=options['address'],options_word=h.u16(options['address']),
                progression=dict(badges=h.u8(profile+0x1c)|(h.u8(profile+0x1f)<<8),
                                 erika=h.get_flag(1220),prewin=h.get_flag(1173),clair=h.get_flag(209)))


def advance_badge(session,trace,options,before, *, old_badges=0, new_badges=1):
    # No emulator steps, menu calls or party/inventory writes in this boundary.
    require(field_state(session,trace,options)==before,'field state drift before badge input')
    raw=bytes.fromhex(before['profile_raw'])
    require(raw[0x1c]|(raw[0x1f]<<8)==old_badges and
            old_badges^new_badges in (1,32),'unexpected badge-only boundary')
    session.h.w8(before['profile']+0x1c,new_badges&255)
    after=field_state(session,trace,options)
    expected=dict(before)
    changed=bytearray(raw);changed[0x1c]=new_badges&255
    expected['profile_raw']=changed.hex()
    expected['progression']=dict(before['progression'],badges=new_badges)
    require(after==expected,'badge input changed party, inventory or another field')
    return after
