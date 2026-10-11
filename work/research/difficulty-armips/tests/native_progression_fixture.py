"""Typed valid party and saved progression inputs, strictly before battle entry."""
import hashlib
from native_battle_oracles import require


def install(session, trace, templates, spec):
    from emu_harness import ARR_PARTY, ARR_VARS_FLAGS, decode_pokemon, encode_pokemon
    h=session.h
    require(trace.run is None and h.in_field() and trace.snapshot()['epoch']==0,
            'progression fixture requires field before battle entry')
    raws=[templates[spec['level']],templates[8],encode_pokemon(templates[8],item=216)]
    require(all(decode_pokemon(r)['checksum_ok'] for r in raws), 'invalid typed party input')
    party=h.array(ARR_PARTY)
    require(h.u32(party)==6, 'invalid party owner')
    for i,raw in enumerate(raws):h.write(party+8+236*i,raw)
    h.w32(party+4,3)
    # Native02029428 reads profile+1C for IDs0..7, +1F for IDs8..15.
    profile=h.array(1)+4
    h.w8(profile+0x1c,spec['badges']&255);h.w8(profile+0x1f,spec['badges']>>8)
    for flag,value in ((1220,spec['erika']),(1173,spec['prewin']),(209,False)):
        h.set_flag(flag,value)
        require(h.get_flag(flag)==value, 'progression flag input readback mismatch')
    require(h.u8(profile+0x1c)|(h.u8(profile+0x1f)<<8)==spec['badges'], 'badge input readback mismatch')
    require(all(h.read(party+8+236*i,236)==raw for i,raw in enumerate(raws)), 'party input readback mismatch')
    return dict(spec=dict(spec),frame=h.frame,save=h.save,profile=profile,vars=h.array(ARR_VARS_FLAGS),
                party_sha256=[hashlib.sha256(r).hexdigest() for r in raws],
                note='Pre-entry save/party inputs only; no victory script claim; no live BattleMon or award writes')
