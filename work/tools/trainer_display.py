"""D-2487: full opponent names via unique packed keys and a guarded native formatter.

No game text lives here. Five authorized references obtain their display text from
an EN-shaped workspace; the exporter receives a validated plan, and the compiler
must install its matching locale-specific payload before saving. Standalone export
continues to refuse oversized names. This module never writes a ROM file.
"""
from pathlib import Path
import hashlib
import json
import struct
import subprocess
import tempfile

IDS = frozenset((17, 59, 632, 666, 745))
ENTRY = 0x0202703C
EXPECT = bytes.fromhex('f8b50c1c0090201c')
LIMIT = 0x01FFA000


def key(sid):
    if sid not in IDS:
        raise ValueError('unapproved full-name reference')
    return f'T{sid:05d}'


def encoded(text):
    import msgtool as m
    import textmetrics as tm
    if not isinstance(text, str) or not text or '{' in text or '\n' in text:
        raise ValueError('display names must be nonempty plain single-line text')
    cm = m.Charmap.load([str(tm.CHARMAP_EN)])
    units = m.encode_text(text, cm)
    if len(units) > 64:
        raise ValueError('display name exceeds the bounded runtime asset')
    return units


def eligible(sid, text):
    return sid in IDS and isinstance(text, str) and len(text) > 10


def plan(workspace):
    p = Path(workspace) / 'a027/0719.json'
    if not p.exists():
        return {}
    return plan_rows(json.loads(p.read_text())['strings'])


def plan_rows(rows):
    result = {}
    reserved = {key(sid) for sid in IDS}
    for row in rows:
        text = row.get('en')
        if text in reserved:
            raise ValueError('an internal trainer display key occurs in source text')
        if eligible(row['id'], text):
            if row.get('status') not in ('draft', 'reviewed', 'tm'):
                raise ValueError('full display name is not ready for export')
            encoded(text)
            result[row['id']] = text
    return result


def stored_text(sid, text, aliases):
    if sid not in aliases:
        return text
    if aliases[sid] != text:
        raise ValueError('trainer display plan is stale')
    encoded(text)
    return key(sid)


def digest(aliases):
    return hashlib.sha256(json.dumps(aliases, sort_keys=True, ensure_ascii=False).encode()).hexdigest()



# Reviewed Thumb instructions, independently checked by disassembly and actual
# native execution. Literal pool and text tables are reconstructed below. This
# allows verification to reject self-consistent but altered build receipts.
CODE = bytes.fromhex(
    'f3b5041c0d1c6888052827d1184e3088002823d00020291c0831095a325a91421ad1'
    '02300a28f6d377896088c21921888a420dd262804000211c08310918f66830880880'
    '02360231013ff9d109480880201cf6bc08bc18471036d8e7f3bc08bc9e46f8b50c'
    '1c0090201c034b18470000')


def expected_payload(aliases, base):
    import msgtool as m
    import textmetrics as tm
    if not aliases or set(aliases)-IDS:
        raise ValueError('invalid trainer display aliases')
    cm = m.Charmap.load([str(tm.CHARMAP_EN)])
    assert len(CODE) == 112
    table = base + len(CODE) + 12
    result = bytearray(CODE + struct.pack('<III', table, 0xFFFF, (ENTRY+8)|1))
    names = bytearray()
    name_base = table + (len(aliases)+1)*16
    for sid,text in sorted(aliases.items()):
        units = encoded(text)
        packed = m.encode_text('{COMPRESSED}'+key(sid),cm)[:-1]
        result.extend(struct.pack('<6HI',*packed,len(units)-1,name_base+len(names)))
        names.extend(struct.pack('<'+'H'*len(units),*units))
    result.extend(bytes(16))
    result.extend(names)
    result.extend(bytes((-len(result))%4))
    return bytes(result)


def assemble(aliases, base, armips):
    """Assemble code/data only; base is the next free aligned ITCM address."""
    import asmpatch
    import msgtool as m
    import textmetrics as tm
    if base % 4 or not 0x01FF8000 <= base < LIMIT or not aliases:
        raise ValueError('invalid trainer display placement')
    if set(aliases) - IDS:
        raise ValueError('unapproved display alias')
    asmpatch.check_armips(armips)
    source = '''.nds
.thumb
.create "payload.bin", BASE
push {r0,r1,r4-r7,lr}
mov r4,r0
mov r5,r1
ldrh r0,[r5,2]
cmp r0,5
bne fallback
ldr r6,=table
next:
ldrh r0,[r6]
cmp r0,0
beq fallback
mov r0,0
compare:
mov r1,r5
add r1,8
ldrh r1,[r1,r0]
ldrh r2,[r6,r0]
cmp r1,r2
bne advance
add r0,2
cmp r0,10
blo compare
ldrh r7,[r6,10]
ldrh r0,[r4,2]
add r2,r0,r7
ldrh r1,[r4]
cmp r2,r1
bhs no_space
strh r2,[r4,2]
lsl r0,r0,1
mov r1,r4
add r1,8
add r1,r1,r0
ldr r6,[r6,12]
copy:
ldrh r0,[r6]
strh r0,[r1]
add r6,2
add r1,2
sub r7,1
bne copy
ldr r0,=0xFFFF
strh r0,[r1]
no_space:
mov r0,r4
pop {r1,r2,r4-r7}
pop {r3}
bx r3
advance:
add r6,16
b next
fallback:
pop {r0,r1,r4-r7}
pop {r3}
mov lr,r3
; Replay exactly the overwritten native prologue, preserving caller ABI.
push {r3-r7,lr}
mov r4,r1
str r0,[sp]
mov r0,r4
ldr r3,=0x02027045
bx r3
.pool
.align 4
table:
'''.replace('BASE', hex(base))
    cm = m.Charmap.load([str(tm.CHARMAP_EN)])
    for sid, text in sorted(aliases.items()):
        packed = m.encode_text('{COMPRESSED}' + key(sid), cm)[:-1]
        assert len(packed) == 5
        units = encoded(text)[:-1]
        source += '.dh ' + ','.join(map(str, packed + [len(units)])) + '\n'
        source += f'.dw name{sid}\n'
    source += '.dw 0,0,0,0\n'
    for sid, text in sorted(aliases.items()):
        source += f'name{sid}:\n.dh ' + ','.join(map(str, encoded(text))) + '\n'
    source += '.align 4\n.close\n'
    with tempfile.TemporaryDirectory(prefix='trainer-display-') as folder:
        p = Path(folder)
        (p/'payload.asm').write_text(source)
        subprocess.run([str(armips), '-erroronwarning', 'payload.asm'], cwd=p, check=True,
                       capture_output=True, text=True, timeout=60)
        blob = (p/'payload.bin').read_bytes()
    if base + len(blob) > LIMIT:
        raise ValueError('trainer display payload exceeds ITCM limit')
    if blob != expected_payload(aliases, base):
        raise ValueError('assembled trainer formatter differs from reviewed instruction contract')
    return blob


def trampoline(base):
    return bytes.fromhex('004b1847') + struct.pack('<I', base | 1)


def apply(rom, aliases, armips):
    if not aliases:
        return {'enabled': False}
    import hardcoded
    view = hardcoded.RomView(rom)
    main = bytearray(view.get('arm9'))
    offset = ENTRY - 0x02000000
    if main[offset:offset+8] != EXPECT:
        raise ValueError('trainer formatter signature differs; refusing display support')
    section = next(s for s in rom.loadArm9().sections if s.ramAddress == 0x01FF8000)
    if section.bssSize:
        raise ValueError('trainer formatter requires appendable ITCM without BSS')
    old = view.get('itcm')
    if len(old) % 32:
        raise ValueError('trainer display requires an aligned ITCM allocation boundary')
    padding = bytes((-len(old)) % 4)
    base = 0x01FF8000 + len(old) + len(padding)
    blob = assemble(aliases, base, armips)
    end = (base + len(blob) + 31) & ~31
    if end > LIMIT or struct.unpack_from('<I', main, 0xD1A28)[0] != base:
        raise ValueError('ITCM allocation boundary differs; refusing display support')
    struct.pack_into('<I', main, 0xD1A28, end)
    main[offset:offset+8] = trampoline(base)
    other = [(s.ramAddress, bytes(s.data), s.bssSize) for s in rom.loadArm9().sections[1:]
             if s.ramAddress != 0x01FF8000]
    view.set('arm9', bytes(main))
    view.set('itcm', old + padding + blob + bytes(end-base-len(blob)))
    after = [(s.ramAddress, bytes(s.data), s.bssSize) for s in rom.loadArm9().sections[1:]
             if s.ramAddress != 0x01FF8000]
    if after != other:
        raise ValueError('display support changed another autoload section')
    receipt = {'enabled': True, 'base': base, 'itcm_end': end, 'bytes': len(blob), 'payload_sha256': hashlib.sha256(blob).hexdigest(),
               'aliases': aliases, 'alias_sha256': digest(aliases), 'storage': 'unique compressed six-character keys',
               'capacity': 'append only when full name plus terminator fits destination'}
    verify(rom, receipt)
    return receipt


def verify(rom, receipt):
    if not receipt.get('enabled'):
        return {'enabled': False}
    import hardcoded
    if (not 0x01FF8620 <= receipt['base'] < LIMIT or receipt['base'] % 4
            or not 0 < receipt['bytes'] <= LIMIT-receipt['base']):
        raise ValueError('invalid trainer display receipt placement')
    aliases = {int(k): v for k,v in receipt['aliases'].items()}
    if digest(aliases) != receipt['alias_sha256'] or set(aliases)-IDS:
        raise ValueError('invalid trainer display receipt')
    view = hardcoded.RomView(rom)
    main = view.get('arm9')
    if main[ENTRY-0x02000000:ENTRY-0x02000000+8] != trampoline(receipt['base']):
        raise ValueError('trainer display trampoline differs')
    off = receipt['base']-0x01FF8000
    blob = view.get('itcm')[off:off+receipt['bytes']]
    if (blob != expected_payload(aliases,receipt['base']) or len(blob) != receipt['bytes']
            or hashlib.sha256(blob).hexdigest() != receipt['payload_sha256']):
        raise ValueError('trainer display payload differs')
    end = receipt['itcm_end']
    if (end != ((receipt['base']+receipt['bytes']+31)&~31) or end > LIMIT
            or len(view.get('itcm')) != end-0x01FF8000
            or struct.unpack_from('<I', main, 0xD1A28)[0] != end):
        raise ValueError('trainer display allocation boundary differs')
    return {'enabled': True, 'aliases': len(aliases), 'payload': 'verified',
            'base': receipt['base'], 'itcm_end': end}


def verify_export(directory, aliases):
    """The five keys must actually be exported before a matching runtime is installed."""
    if not aliases:
        return
    import msgtool as m
    import textmetrics as tm
    cm = m.Charmap.load([str(tm.CHARMAP_EN)])
    data = json.loads((Path(directory)/'a027/0719.json').read_text())
    rows = {r['id']:r['text'] for r in data['strings']}
    for sid in aliases:
        text = rows.get(sid)
        if not isinstance(text,str) or m.encode_text(text,cm) != m.encode_text('{COMPRESSED}'+key(sid),cm):
            raise ValueError(f'trainer display key missing or mismatched at 0719#{sid}')


def verify_storage(rom, receipt):
    if not receipt.get('enabled'):
        return
    import msgtool as m
    import textmetrics as tm
    cm = m.Charmap.load([str(tm.CHARMAP_EN)])
    narc = m.Narc.parse(m.get_file(rom,'a/0/2/7'))
    _,strings,_ = m.decrypt_bank(narc.files[719])
    for sid in receipt['aliases']:
        sid = int(sid)
        if strings[sid] != m.encode_text('{COMPRESSED}'+key(sid),cm):
            raise ValueError(f'native trainer storage differs at 0719#{sid}')


def before_display(rom, receipt):
    """Read-only view of the preceding assembly stage for its existing strict checks.

    Validate the complete new tail first, then undo only the two owned main-code
    regions and truncate that tail. ndspy restores autoload bookkeeping. Other
    assembly bytes remain subject to the original hashes and region checks.
    """
    verify(rom, receipt)
    if not receipt.get('enabled'):
        return rom
    import copy
    prior = copy.copy(rom)
    code = rom.loadArm9()
    main = code.sections[0].data
    main[ENTRY-0x02000000:ENTRY-0x02000000+8] = EXPECT
    struct.pack_into('<I', main, 0xD1A28, receipt['base'])
    itcm = next(s for s in code.sections if s.ramAddress == 0x01FF8000)
    itcm.data = itcm.data[:receipt['base']-0x01FF8000]
    prior.arm9 = bytes(code.save(compress=False))
    return prior
