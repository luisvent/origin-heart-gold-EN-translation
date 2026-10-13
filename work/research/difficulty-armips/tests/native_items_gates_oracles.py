"""Input-only fault provenance and native cancellation/continuation oracles."""
from copy import deepcopy
from native_battle_oracles import require
from native_items_oracles import events, trainer_entry
from native_items_cases import GATE_ITEM

GATES = {'accept':('dg_bag_accept',13,'items.accept'),
         'item':('dg_bag_commit_item',0,'items.backstop_item'),
         'target':('dg_bag_commit_target',6,'items.backstop_target')}


def injection(row, gate, item):
    require(row['kind']=='nativeFaultInput' and row['gate']==gate and row['item']==item,
            'wrong fault input identity')
    before,after=bytes.fromhex(row['before']),bytes.fromhex(row['after'])
    expected=bytearray(before);expected[0x18:0x1b]=item.to_bytes(2,'little')+b'\0'
    require(len(before)==len(after)==0x30 and after==expected,'fault modified more than selected-item input')
    old_item=int.from_bytes(before[0x18:0x1a],'little')
    require(old_item==(0 if gate=='item' else 151) and before[0x1a]==(4 if gate=='item' else 1),
            'fault was not armed from the expected native UI input')
    require(row['address']%4==0 and 0x02000000<=row['address']<=0x023DC000-0x30,
            'fault input pointer invalid')
    require(row['registers_before']==row['registers_after'],'fault changed registers')
    require(row['command_before']==row['command_after'],'fault changed command or slot')
    require(row['snapshot']['flags']==0 and row['snapshot']['allowed']==1 and row['snapshot']['epoch']>0,
            'fault has no valid restricted context')


def actor_identity(binding,command,engine):
    b=binding
    require(b['root']>0 and b['view']==b['root']+0x54 and
            b['roster']==b['view']+0xc+0x1c*b['owner'] and b['owner']==command['owner']==0 and
            b['slot']==command['slot']==0 and 0<=b['slot']<b['count']<=6,
            'wrong native actor view/roster/owner/slot')
    require(b['ui']==b['ui_table']==command['actor'] and
            b['engine']==engine['address'] and b['id']==command['actor_id']==engine['id']==1,
            'native actor resolver identity mismatch')
    require(b['ui_backing']!=0 and b['engine_backing']!=0 and
            len(b['ui_backing_sha256'])==64 and b['ui_backing_sha256']==b['engine_backing_sha256'],
            'UI and engine actor backing copies differ')
    expected=dict(engine,address=b['ui'])
    require(b['engine_state']==engine and b['ui_state']==expected,'UI and engine actor state differs')


def selected_target(run):
    binding=run['target_actor_binding'];command=run['target_command']
    actor_identity(binding,command,run['before']['mons']['1'])
    mapping=run['party_mapping'];slot=run['selected_ui_slot']
    require(mapping['controller']==command['controller'] and 0<=slot<mapping['count'],
            'party mapping belongs to another controller/slot')
    entry=mapping['entries'][slot]
    require(entry['ui_slot']==slot and entry['id']==binding['id'] and entry['mon']==binding['ui'] and
            entry['backing']==binding['ui_backing'] and
            entry['source_sha256']==entry['copy_sha256']==binding['ui_backing_sha256'] and
            entry['hp']==binding['ui_state']['hp'] and entry['maxhp']==binding['ui_state']['maxhp'],
            'selected party UI copy does not resolve to the native actor')


def denied(run):
    trainer_entry(run)
    gate,item=run['gate'],run['fault_item'];rows=events(run,'fault_input')
    require(len(rows)==1,'missing/repeated fault injection')
    row=rows[0];injection(row,gate,item)
    require(row['result']==GATES[gate][1] and row['args_after']['item']==0 and
            row['args_after']['category']==4,'native gate did not clear/cancel')
    require(row['args_after']['address']==row['address'],'native gate changed input ownership')
    before,after=run['before'],run['denied']
    require(before==after,'denied input changed battle state/inventory/snapshot')
    command=row['command_before']
    require(command==row['command_return']==run['command_denied'] and command['owner']==command['slot']==0 and
            command['actor_id']==1,
            'denial changed native actor/owner/slot/command')
    actor_identity(row['actor_binding'],command,before['mons']['1'])
    require(row['actor_binding']['root']==before['snapshot']['root'],'actor view from another battle')
    lookups=events(run,'controller_actor_lookup')
    require(any(e['view']==row['actor_binding']['view'] and e['owner']==command['owner'] and
                e['slot']==command['slot'] and e.get('result')==command['actor'] for e in lookups),
            'native controller actor lookup not observed')
    require(row['snapshot']==before['snapshot'],'fault epoch differs from battle')
    lists=events(run,'lists')
    require(lists and all(any(e['item']==151 for e in x['lists'][1]) and
            not any(e['item']==GATE_ITEM for entries in x['lists'] for e in entries) for x in lists),
            'restricted list did not retain Pecha/exclude the DEFAULT-denied item')
    for name in ('command','effect','outcome','consume','action','target_resolved','ordinary_hp','status_effect','pp_one','pp_all','revive','exception'):
        require(not events(run,name),'denied input reached native '+name)
    require(not events(run,'slot_advance'),'denied input advanced command slot')
    require(any(e['handler']==0x02202445 for e in events(run,'schedule')),
            'native command-selection continuation absent')
    if gate=='target':
        require(row['target']<6 and len(lists)>=2 and lists[-1]['frame']>=row['frame'],
                'target denial did not reopen native Bag')
        selected_target(run)
        require(row['target']==run['selected_ui_slot'],'native target returned another UI slot')
        require(events(run,'accept')[-1]['after']['item']==151 and
                events(run,'commit_item')[0]['result']==151,'target probe bypassed actual allowed Use')
    require(not events(run,'blocked_native_accept'),'denied Use reached original acceptance')
    if item>790:require(not events(run,'fault_metadata'),'invalid ID reached native metadata')


def continued(run):
    # Recheck denial on its frozen event prefix, not on post-Fight observations.
    prefix=dict(run,events=run['events'][:run['denied_event_count']]);denied(prefix)
    after=deepcopy(run['denied'])
    for key in ('1','13'):
        after['mons'][key]['pp'][0]-=1;after['mons'][key]['original_pp'][0]-=1
    require(run['after']==after,'Fight continuation changed unexpected HP/status/PP/inventory')
    actions=events(run,'action')
    require(len(actions)==2 and sorted((e['actor']['id'],e['move']) for e in actions)==[(1,150),(13,150)],
            'continuation did not execute exactly one native Splash per actor')
    require(not any(events(run,n) for n in ('command','effect','consume','outcome','exception')),
            'fault item escaped into continuation')
