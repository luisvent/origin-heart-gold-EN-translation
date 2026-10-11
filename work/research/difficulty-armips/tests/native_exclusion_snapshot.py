"""Read closed party records after native crypto finishes; never repair bytes."""
from native_battle_helpers import registers
from native_battle_oracles import require


def wait_closed_party(session,run,count=5,limit=60):
    import save_core
    h=session.h
    owner=h.array(2)
    samples=run.setdefault('record_stabilization',[])
    for trial in range(limit+1):
        require(h.in_field() and h.array(2)==owner and h.u32(owner)==6
                and h.u32(owner+4)==count,'party owner/count changed during native return')
        pc=registers(h)[15]
        row=dict(frame=h.frame,pc=pc,owner=owner,closed=False)
        samples.append(row)
        # 02020680..CA is the bound ARM9 XOR/LCG routine, including the
        # subroutine called from its loop. A frame may stop inside that loop.
        if not 0x02020680<=pc<0x020206CA:
            raws=[h.read(owner+8+236*slot,236) for slot in range(count)]
            try:
                mons=[save_core.request('decodePokemon',raw,diagnostic=False) for raw in raws]
                valid=all(m['flags']==0 and m['checksumOk'] and m['party']
                          and 1<=m['party']['level']<=100 for m in mons)
            except ValueError as error:
                row['reason']=str(error)
                valid=False
            if valid and raws==[h.read(owner+8+236*slot,236) for slot in range(count)]:
                import hashlib
                row.update(closed=True,record_sha256=[hashlib.sha256(raw).hexdigest() for raw in raws])
                return owner
        if trial<limit:h.step(1)
    raise AssertionError('native party did not return to strict closed records within bounded wait')
