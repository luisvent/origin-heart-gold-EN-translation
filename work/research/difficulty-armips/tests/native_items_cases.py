"""Implemented HP/status paths. A table entry alone never grants native evidence.

Payload expectations are numeric data read from candidate a/0/1/7. Party status
bits map through ov14's importer to the native major-status IDs below.
"""
STATUS_IDS = {0: 0, 1: 2, 8: 5, 16: 4, 32: 3, 64: 1}


def medicine(name, category, mask, status=0, hp=None, healing=0, status_payload=0, kind='hp-status', target_slot=0, ui_slot=None, move_slot=0, pp_amount=0, restricted_allowed=False, pocket="medicine", dispatch=2):
    return dict(name=name, category=category, categories=(0,1) if mask == 12 else (category,),
                mask=mask, status=status, status_id=STATUS_IDS[status], hp=hp,
                healing=healing, status_payload=status_payload, kind=kind,
                target_slot=target_slot, ui_slot=target_slot if ui_slot is None else ui_slot, move_slot=move_slot, pp_amount=pp_amount, restricted_allowed=restricted_allowed, pocket=pocket, dispatch=dispatch)


CASES = {
    17: medicine('Potion',0,4,hp=1,healing=20),
    18: medicine('Antidote',1,8,status=8,status_payload=2),
    19: medicine('Burn Heal',1,8,status=16,status_payload=4),
    20: medicine('Ice Heal',1,8,status=32,status_payload=8),
    21: medicine('Awakening',1,8,status=1,status_payload=1),
    22: medicine('Parlyz Heal',1,8,status=64,status_payload=16),
    23: medicine('Full Restore',0,12,status=8,hp=1,healing=255,status_payload=63),
    24: medicine('Max Potion',0,4,hp=1,healing=255),
    25: medicine('Hyper Potion',0,4,hp=1,healing=200),
    27: medicine('Full Heal',1,8,status=8,status_payload=63),
    34: medicine('Energy Powder',0,4,hp=1,healing=50),
    35: medicine('Energy Root',0,4,hp=1,healing=200),
    42: medicine('Lava Cookie',1,8,status=8,status_payload=63),
    54: medicine('Old Gateau',1,8,status=8,status_payload=63),
}
HP_STATUS = tuple(CASES)
CASES.update({
    28: medicine('Revive',0,4,hp=0,healing=254,kind='revive',target_slot=1,ui_slot=2),
    29: medicine('Max Revive',0,4,hp=0,healing=255,kind='revive',target_slot=1,ui_slot=2),
    37: medicine('Revival Herb',0,4,hp=0,healing=255,kind='revive',target_slot=1,ui_slot=2),
    38: medicine('Ether',0,16,kind='pp-one',move_slot=1,pp_amount=10),
    39: medicine('Max Ether',0,16,kind='pp-one',move_slot=1,pp_amount=127),
    40: medicine('Elixir',0,16,kind='pp-all',pp_amount=10),
    41: medicine('Max Elixir',0,16,kind='pp-all',pp_amount=127),
})
PP_ONLY = (38,39,40,41)
PP_REVIVE = (38,28,39,40,41,29,37)
ADDITIONS = tuple(i for i in CASES if i != 17)
# Preserve the twenty additions separately from already-native eligible items.
BERRY_FLUTE = (151,155,154,65)
CASES.update({
    151: medicine('Pecha Berry',1,8,status=8,status_payload=2,restricted_allowed=True,pocket='berries',dispatch=0),
    155: medicine('Oran Berry',0,4,hp=1,healing=10,restricted_allowed=True,pocket='berries',dispatch=0),
    154: medicine('Leppa Berry',0,16,kind='pp-one',move_slot=1,pp_amount=10,restricted_allowed=True,pocket='berries',dispatch=0),
    65: medicine('Blue Flute',1,8,status=1,status_payload=1,restricted_allowed=True,pocket='battle',dispatch=0),
})


def usable(run):
    return bool(run['flags'] & 4 or CASES[run['item']]['restricted_allowed'])


# Implemented paths still require native acceptance of every paired slice.
PENDING_ADDITIONS = ()


def category_for(run):
    category = run.get('category', CASES[run['item']]['category'])
    if category not in CASES[run['item']]['categories']:
        raise AssertionError('item selection category is outside implemented contract')
    return category


NO_EFFECT = (17,18,38,28)


def case_for(run):
    case=dict(CASES[run['item']])
    condition=run.get('condition','positive')
    if condition not in ('positive','no-effect'):
        raise AssertionError('unknown item fixture condition')
    case['no_effect']=condition=='no-effect'
    case['initial_pp']=(4,7,0,0)
    if case['no_effect']:
        if run['item'] not in NO_EFFECT:raise AssertionError('unsupported no-effect item')
        case.update(status=0,status_id=0,hp=None,initial_pp=(10,40,0,0))
        if run['item']==28:
            case.update(hp=1,ui_slot=1)  # living injured bench, not a fainted or full-HP control
    return case
