"""Fail-closed checkpoint oracles, independently mutation-tested on the host."""
from copy import deepcopy
from native_battle_oracles import require
from native_items_cases import category_for, usable, case_for


def events(run, name):
    return [e for e in run['events'] if e['name'] == name]


def trainer_entry(run):
    constructors, captures = events(run,'constructor'), events(run,'captured')
    require(len(constructors) == len(captures) == len(events(run,'begin')) == 1,
            'missing/duplicate real trainer lifecycle observations')
    ctor, capture = constructors[0], captures[0]
    c, snap = capture['context'], capture['snapshot']
    require(ctor['lr'] == 0x020507AD and ctor['flags'] == 1 and ctor['control'] == 0,
            'wrong trainer constructor/caller')
    require(c['setup'] == ctor['setup'] == capture['setup_owner'] and
            c['save'] == c['published_save'] == capture['save_owner'] and c['save'] != 0,
            'trainer save/setup ownership not proven')
    require(c['flags'] == 1 and c['control'] == 0 and snap['allowed'] == 1 and
            snap['epoch'] == capture['generation'] > 0 and snap['root'] == c['root'] and
            snap['flags'] == run['flags'], 'trainer native capture classification/settings rejected')
    require(c['options_copy'] == run['options']['after'], 'trainer copied Options mismatch')
    require(not events(run,'exception'), 'native exception in ITEMS checkpoint')
    enemy = events(run,'enemy_fixture')
    require(len(enemy) == 1 and enemy[0]['before_begin'] and
            enemy[0]['frame'] <= events(run,'begin')[0]['frame'], 'enemy fixture did not precede entry')


def input_fixture(state, case):
    target_id = case['target_slot']+1
    for key,mon in state['mons'].items():
        is_target = int(key) == target_id
        hp = case['hp'] if is_target and case['hp'] is not None else mon['maxhp']
        require(mon['hp'] == hp and mon['maxhp'] > 21, 'wrong initial HP/fainted eligibility')
        status_id = case['status_id'] if is_target else 0
        require(len(mon['statuses']) == 5 and all((v != 0) == (i == status_id)
                for i,v in enumerate(mon['statuses'],1)), 'wrong initial status fixture')
        pp_target = is_target and case['kind'].startswith('pp-')
        moves = [82,150,0,0] if pp_target else [150,0,0,0]
        pp = list(case.get('initial_pp',(4,7,0,0))) if pp_target else [40,0,0,0]
        maximum = [10,40,0,0] if pp_target else [40,0,0,0]
        require(mon['moves'] == mon['original_moves'] == moves and
                mon['pp'] == mon['original_pp'] == pp and
                mon['pp_max'] == mon['original_pp_max'] == maximum and
                mon['pp_linked'] == [1]*4, 'wrong initial active/original PP fixture')


def selected_party_entry(mapping, case, before):
    entries=mapping['entries'];args=mapping['args']
    require(mapping['count'] == len(entries) == 3 and args['owner'] == 0,
            'wrong native party mapping owner/count')
    require([e['ui_slot'] for e in entries] == [0,1,2] and
            {e['id'] for e in entries} == {1,2,3} and len({e['mon'] for e in entries}) == 3,
            'native party mapping has missing/duplicate recipients')
    for entry in entries:
        mon=before['mons'][str(entry['id'])]
        require(entry['hp'] == mon['hp'] and entry['maxhp'] == mon['maxhp'] and
                entry['source_sha256'] == entry['copy_sha256'] and len(entry['copy_sha256']) == 64 and
                entry['copied'] == args['party']+8+236*entry['ui_slot'],
                'displayed party record does not match native roster source')
    selected=entries[case['ui_slot']]
    require(selected['id'] == case['target_slot']+1, 'configured UI slot maps to wrong native recipient')
    if case['kind']=='revive':
        require(0<selected['hp']<selected['maxhp'] if case.get('no_effect') else selected['hp']==0,
                'displayed Revive target eligibility differs from fixture')
    return selected


def effect_expected(before, case):
    expected = deepcopy(before)
    if case.get('no_effect'):return expected
    if case['kind'] == 'revive':
        expected['hp'] = max(1,before['maxhp']//2) if case['healing'] == 254 else before['maxhp']
    elif case['kind'].startswith('pp-'):
        slots = (case['move_slot'],) if case['kind'] == 'pp-one' else range(4)
        for slot in slots:
            missing = before['pp_max'][slot]-before['pp'][slot]
            restored = missing if case['pp_amount'] == 127 else min(missing,case['pp_amount'])
            expected['pp'][slot] += restored
            expected['original_pp'][slot] += restored
    else:
        expected['hp'] = min(before['maxhp'],before['hp']+case['healing'])
        expected['statuses'] = [0]*5
    return expected


def checkpoint(run):
    trainer_entry(run)
    item = run['item']; case = case_for(run)
    no_effect=case['no_effect']; quantity=3 if no_effect else 2
    category = category_for(run)
    before, after = run['before'], run['after']
    require(before['snapshot'] == after['snapshot'], 'snapshot changed during item selection')
    require(before['item'] == after['item'] == item and before['quantity'] == 3, 'wrong inventory fixture')
    for key in ('1','2','3','13'):
        require(before['mons'][key]['id'] == after['mons'][key]['id'] == int(key), 'wrong target identity')
    lists = events(run,'lists')
    require(lists and events(run,'mask'), 'no native visible-list/mask evidence')
    capture = events(run,'captured')[0]['context']
    require(before['bag_address'] == after['bag_address'] == capture['bag'] and
            len(bytes.fromhex(before['bag'])) == len(bytes.fromhex(after['bag'])) == 0x864,
            'inventory evidence lacks full native Bag identity/range')
    for row in lists:
        args = row['args']
        require(args['owner'] == args['tutorial'] == 0 and args['trainer_info'] == capture['trainer_info'] and
                args['bag'] == capture['bag'], 'Bag ownership/context mismatch')
    masks = [e['result'] for e in events(run,'mask') if e['item'] == item]
    require(masks, 'Selected item never tested by installed list wrapper')
    expected_lists = [[] for _ in range(5)]
    for visible_category in case['categories']:
        expected_lists[visible_category] = [dict(item=item,quantity=3)]
    target_id = case['target_slot']+1; target_key = str(target_id)
    status_id = case['status_id']
    input_fixture(before,case)
    if usable(run):
        require(all(n == case['mask'] for n in masks) and all(row['lists'] == expected_lists and row['counts'] == [len(v) for v in expected_lists] for row in lists),
                'ALL did not expose exactly selected item in its category')
        for name in ('accept','commit_item','commit_target','command','effect','outcome'):
            require(len(events(run,name)) == 1, 'expected exactly one native '+name)
        accepted = events(run,'accept')[0]
        require(accepted['before']['item'] == accepted['after']['item'] == item and
                accepted['before']['category'] == accepted['after']['category'] == category and
                accepted['result'] == 13 and events(run,'commit_item')[0]['result'] == item,
                'ALL selected item rejected by native gates')
        mappings=events(run,'party_mapping');resolutions=events(run,'target_resolved')
        require(len(mappings) == len(resolutions) == 1, 'missing/duplicate native party identity mapping')
        mapping=mappings[0];selected=selected_party_entry(mapping,case,before);resolved=resolutions[0]
        require(mapping['args']['item'] == item and mapping['args']['category'] == category and
                resolved['roster'] == mapping['roster'] and resolved['ui_slot'] == case['ui_slot'] and
                resolved['id'] == target_id and resolved['mon'] == selected['mon'] and
                resolved['backing'] == selected['backing'] and resolved['hp'] == selected['hp'],
                'native target resolver disagrees with displayed identity')
        target = events(run,'commit_target')[0]
        require(target['target'] == target['result'] == case['ui_slot'] and
                target['command']['controller'] == mapping['controller'] and
                target['party']['address'] == mapping['args']['address'] and
                target['party']['party'] == mapping['args']['party'], 'wrong party UI target/owner')
        command = events(run,'command')[0]
        encoded = bytes.fromhex(command['after'])
        word = int.from_bytes(encoded[:4], 'little')
        require(len(encoded) == 12 and int.from_bytes(encoded[4:8],'little') == target_id and
                int.from_bytes(encoded[8:12],'little') == 1, 'wrong encoded native target/command marker')
        parent = target['command']
        require(parent['owner'] == parent['slot'] == 0 and parent['actor_id'] == 1 and parent['actor'] != 0 and
                parent['destination'] == command['destination'] and parent['command'] == command['before'],
                'wrong command owner/slot/actor/destination')
        require(command['item'] == item and command['target'] == target_id and command['move_slot'] == case['move_slot'] and (word >> 20) & 255 == case['move_slot'] and word & 15 == 2 and (word >> 4) & 0xffff == item,
                'native command was not a selected item action')
        effect = events(run,'effect')[0]
        consumes=events(run,'consume')
        require(len(consumes)==(0 if no_effect else 1),'wrong native consumption count')
        if consumes:require(consumes[0]['item']==item and consumes[0]['owner']==0,'wrong consuming item/owner')
        require(effect['item'] == item and
                effect['actor']['id'] == 1 and effect['actor']['address'] == before['mons']['1']['address'] and
                effect['target_id'] == target_id and effect['move_slot'] == case['move_slot'],
                'wrong effect actor/target/move or consuming owner')
        outcome = events(run,'outcome')[0]
        require(outcome['item'] == item and outcome['actor'] == effect['actor'] and
                outcome['target_id'] == target_id and outcome['move_slot'] == case['move_slot'] and
                outcome['words'] == [0,0 if no_effect else 1,0], 'wrong native effect outcome/consumption words')
        expected_target = effect_expected(before['mons'][target_key],case)
        require(after['quantity'] == quantity and after['mons'][target_key] == expected_target,
                'selected item effect/quantity mismatch')
        old_bag, new_bag = bytearray.fromhex(before['bag']), bytearray.fromhex(after['bag'])
        require(before['item_offset'] == after['item_offset'] == {'medicine':0x5e8,'berries':0x688,'battle':0x7e8}[case['pocket']], 'unexpected stocked slot')
        offset = before['item_offset']+2
        old_bag[offset:offset+2] = quantity.to_bytes(2,'little')
        require(old_bag == new_bag, 'unexpected inventory mutation')
        require(len(events(run,'action')) == 1 and events(run,'action')[0]['actor']['id'] == 13 and
                events(run,'action')[0]['move'] == 150, 'item did not consume exactly one native enemy turn')
        for key in ('1','2','3','13'):
            expected = deepcopy(before['mons'][key])
            if key == target_key: expected = expected_target
            elif key == '13':
                expected['pp'][0] -= 1
                expected['original_pp'][0] -= 1
            require(expected == after['mons'][key], 'unexpected change outside selected target/Splash')
        callback = {'pp-one':'pp_one','pp-all':'pp_all','revive':'revive'}.get(case['kind'])
        for name in ('pp_one','pp_all','revive'):
            rows = events(run,name)
            require(len(rows) == (1 if name == callback else 0), 'wrong/missing native effect callback '+name)
            if rows:
                row = rows[0]
                require(row['item'] == item and row['before'] == before['mons'][target_key] and
                        row['after'] == expected_target and row['result'] == (0 if no_effect else 1),
                        'native callback failed or used wrong target/PP/HP')
                if case['kind'].startswith('pp-'):
                    require(row['move_slot'] == case['move_slot'], 'PP callback received wrong move slot')
        if case['kind'] == 'pp-one':
            choices = events(run,'move_selected')
            require(events(run,'move_menu') and len(choices) == 1 and choices[0]['slot'] == case['move_slot'],
                    'missing/wrong native Ether move selection')
            for party in (choices[0]['party'],target['party']):
                require(party['target'] == case['ui_slot'] and party['item'] == item and party['owner'] == 0,
                        'move choice used wrong party/item/owner')
            require(target['party']['move_slot'] == case['move_slot'], 'party return lost selected move')
        failures=events(run,'failure_message')
        require(len(failures)==(1 if no_effect else 0) and
                all(e['actor_id']==1 and e['message']==0x3f for e in failures),
                'wrong/missing native no-effect message')
        ordinary=events(run,'ordinary_hp')
        if no_effect and item!=17:require(not ordinary,'unexpected ordinary HP callback for no-effect control')
        if no_effect and item==17:
            require(len(ordinary)==1 and ordinary[0]['result']==0 and
                    ordinary[0]['before']==ordinary[0]['after']==before['mons'][target_key],
                    'full-HP Potion did not reject healing natively')
        if case['kind']=='revive':
            require(not ordinary and not events(run,'revival_adjust'),'revival reached redundant ordinary-heal path')
            attrs=events(run,'effect_attr')
            require(len(attrs)==2 and {e['attr']:e['result'] for e in attrs}=={23:1,38:0},
                    'revival attributes were not retained23/suppressed38')
            require(all(e['item']==item and e['actor_id']==1 and e['target_id']==target_id and
                        e['actor']==before['mons']['1']['address'] and e['target']==before['mons'][target_key]['address']
                        for e in attrs),'revival attr actor/target identity mismatch')
            for name in ('revival_hp_add','revival_hp_call','revival_dispatch'):
                require(len(events(run,name))==(0 if no_effect else 1),'wrong native revival count '+name)
            if not no_effect:
                addition=events(run,'revival_hp_add')[0]
                require(addition['lr']==0x0222AE0F and addition['mon']==before['mons'][target_key]['address'] and
                        addition['hp']==0 and addition['amount']==addition['after_hp']==expected_target['hp'],
                        'wrong/repeated native revival HP add')
                call=events(run,'revival_hp_call')[0]
                require(call['recipient']==target_id and call['amount']==expected_target['hp'] and
                        call['hp']==0 and call['after_hp']==expected_target['hp'],'wrong native revival HP call')
        if no_effect and item==18:
            cures=events(run,'status_effect')
            require(len(cures)==1 and cures[0]['status_id']==5 and cures[0]['result']==0,
                    'healthy Antidote did not reject absent poison natively')
        cures = events(run,'status_effect')
        successful = [c for c in cures if c['result'] == 1]
        require(len(successful) == (1 if status_id else 0), 'missing/duplicate native status cure')
        for cure in cures:
            require(cure['before']['address'] == before['mons'][target_key]['address'] and
                    cure['before']['id'] == target_id, 'status handler used another target')
            expected = dict(cure['before'])
            if cure['result'] == 1:
                require(cure['status_id'] == status_id and cure['before']['statuses'][status_id-1] != 0,
                        'native handler cured wrong/absent status')
                expected['statuses'] = [0]*5
            else:
                require(cure['result'] == 0, 'invalid native status result')
            require(cure['after'] == expected, 'unexpected mutation inside status handler')
    else:
        require(all(n == 0 for n in masks) and all(row['counts'] == [0]*5 for row in lists),
                'restricted selected item visible')
        require(before == after, 'restricted Bag/cancel changed inventory, HP, PP, or snapshot')
        require(not any(events(run,n) for n in ('accept','command','effect','consume','action','status_effect','outcome','pp_one','pp_all','revive','move_selected','target_resolved','party_mapping','ordinary_hp','effect_attr','failure_message','revival_hp_add')),
                'restricted hidden item committed an action')
        require(run['command_before_cancel'] == run['command_after_cancel'],
                'restricted cancel altered command/actor/slot')
        closed = events(run,'fade_close_state13')
        require(closed and all(e['args']['item'] == 0 and e['args']['category'] == 4 for e in closed),
                'native cancel must fade with cleared item and cancel category4')
        committed = events(run,'commit_item')
        require(committed and all(e['before']['item'] == 0 and e['result'] == 0 and
                e['after']['item'] == 0 and e['after']['category'] == 4 for e in committed),
                'native cancel did not return a cleared Bag selection')
    return True
