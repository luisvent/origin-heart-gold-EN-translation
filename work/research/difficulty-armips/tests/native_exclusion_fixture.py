"""Deterministic input-only fixtures through the existing sealed save-core API.

No native generator, checksum repair, retries, battle awards or custom codec.
Personal stats/growth thresholds come from the exact installed candidate.
"""
import base64
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from support import ROOT, sha256
from evidence import write_json
from native_battle_oracles import require


SCRIPT = r'''
import {readFileSync} from 'node:fs';
const input=JSON.parse(readFileSync(0,'utf8'));
const {verifyBuildIdentity}=await import(input.core+'/scripts/build-identity.mjs');
const identity=verifyBuildIdentity();
const {readSave}=await import(input.core+'/dist/save.js');
const {decodePokemonDetails,patchPokemonFixture,patchPokemonStats,patchPokemonMoves}=await import(input.core+'/dist/pokemon.js');
const {mapStats,calculateStats}=await import(input.core+'/dist/stats.js');
if(verifyBuildIdentity().buildId!==identity.buildId)throw Error('core changed during import');
const seed=readSave(Uint8Array.from(Buffer.from(input.save,'base64'))).partyRecords[input.seedSlot];
const source=decodePokemonDetails(seed); // strictly closed, valid checksum; never diagnostic mode
if(source.isEgg || !source.party)throw Error('seed must be a non-egg party record');
const ivs=mapStats(()=>15),evs=mapStats(()=>0),templates={};
for(const level of input.levels){
  let mon=patchPokemonFixture(seed,{species:input.species,item:0,ability:input.ability,form:0,status:0},{tailPolicy:'preserve'});
  // All requested levels differ from this pinned source level. Refuse a stale
  // stat-cache no-op after a species edit instead of guessing valid metadata.
  if(source.party.level===level)throw Error('fixture requires a level change for stat recalculation');
  mon=patchPokemonStats(mon,{level,nature:0,ivs,evs},input.personal,input.thresholds);
  mon=patchPokemonMoves(mon,[{id:82,pp:30,ppUps:0},{id:150,pp:30,ppUps:0},
                             {id:0,pp:0,ppUps:0},{id:0,pp:0,ppUps:0}]);
  let decoded=decodePokemonDetails(mon);
  mon=patchPokemonFixture(mon,{currentHp:decoded.party.stats.hp,status:0},{tailPolicy:'preserve'});
  decoded=decodePokemonDetails(mon);
  const expected=calculateStats(input.personal.baseStats,ivs,evs,level,0,input.species);
  if(decoded.speciesId!==input.species || decoded.party.level!==level || decoded.experience!==input.thresholds[level] ||
     JSON.stringify(decoded.party.stats)!==JSON.stringify(expected) || decoded.party.currentHp!==expected.hp ||
     decoded.party.status!==0 || decoded.isEgg || !decoded.checksumOk)throw Error('invalid prepared fixture');
  templates[level]={raw:Buffer.from(mon).toString('base64'),decoded};
}
if(verifyBuildIdentity().buildId!==identity.buildId)throw Error('core changed during fixture preparation');
console.log(JSON.stringify({templates,seed:Buffer.from(seed).toString('base64'),build:identity.buildId}));
'''


def prepare_fixture_templates(receipt, out, levels=(12,11,8), *, species=19,seed_slot=0):
    from ndspy.rom import NintendoDSRom
    from ndspy.narc import NARC
    require(type(seed_slot) is int and 0<=seed_slot<6,'invalid strict seed index')
    levels=tuple(sorted(set(levels)))
    require(levels and all(type(n) is int and 1<=n<=100 for n in levels), 'invalid fixture levels')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    source=ROOT/'work/build/memcheck/full_bag_6mons.sav'
    rom_path=Path(receipt['output']['path'])
    require(sha256(rom_path)==receipt['output']['sha256'], 'fixture candidate hash mismatch')
    rom=NintendoDSRom.fromFile(str(rom_path))
    personal=bytes(NARC(rom.getFileByName('a/0/0/2')).files[species])
    growth=bytes(NARC(rom.getFileByName('a/0/0/3')).files[personal[19]])
    thresholds=list(struct.unpack('<101I',growth))
    request=dict(seedSlot=seed_slot,species=species,ability=personal[22],core=(ROOT/'work/save-core').as_uri(),save=base64.b64encode(source.read_bytes()).decode(),
                 personal=dict(baseStats=list(personal[:6]),growthRate=personal[19]),thresholds=thresholds,levels=levels)
    process=subprocess.run(['node','--input-type=module','-e',SCRIPT],input=json.dumps(request),
                           text=True,capture_output=True,timeout=30,cwd=ROOT)
    require(process.returncode==0, 'typed fixture preparation failed: '+process.stderr)
    result=json.loads(process.stdout)
    records={int(level):base64.b64decode(row['raw'],validate=True) for level,row in result['templates'].items()}
    require(set(records)==set(levels) and all(len(r)==236 for r in records.values()), 'invalid template output')
    (out/'fixture-seed.bin').write_bytes(base64.b64decode(result['seed'],validate=True))
    for level,record in records.items():(out/f'fixture-level-{level}.bin').write_bytes(record)
    write_json(out/'fixture-templates.json',dict(
        seed_slot=seed_slot,method=f'typed save-core edits of strict valid battery slot{seed_slot}; input-only; native generator unused',
        candidate_sha256=receipt['output']['sha256'],battery_sha256=sha256(source),core_build=result['build'],
        personal_sha256=hashlib.sha256(personal).hexdigest(),growth_sha256=hashlib.sha256(growth).hexdigest(),
        species=species,personal=request['personal'],thresholds=thresholds,
        templates={level:dict(sha256=hashlib.sha256(records[int(level)]).hexdigest(),decoded=row['decoded'])
                   for level,row in result['templates'].items()}))
    return records
