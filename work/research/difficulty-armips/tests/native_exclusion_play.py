from native_exclusion_snapshot import wait_closed_party
from native_battle import prepare_opponent
from native_battle_input import BattleInput
from native_battle_helpers import party_summary
from native_battle_oracles import validate_run, require
def validate_positive(run):
    require(len(run['before'])==len(run['after'])==5,'five-recipient fixture changed')
    validate_run(dict(run,before=run['before'][:3],after=run['after'][:3]))

def play_battle(session, trace, run):
    h = session.h
    trace.run = run
    run['opponent'] = prepare_opponent(session,trace,run)
    require(h.wait_screen('battle_menu', 1800), 'wild constructor did not reach command menu')
    session.checkpoint(run['name']+'-menu', run)
    # Fail on missing accepted entry before consuming any battle inputs.
    snap=trace.snapshot()
    require(snap['allowed']==1 and snap['epoch']>0 and snap['cap']==run.get('expected_cap',12) and snap['flags']==run['flags'],
            'installed native entry did not publish the accepted expected-cap snapshot')
    inputs=BattleInput(session,trace,run)
    require(inputs.move(1,150,1,'splash')=='menu', 'Splash unexpectedly ended battle')
    inputs.switch()
    require(inputs.move(0,82,2,'dragon-1')=='field', 'native attack did not KO the pre-entry HP1 opponent')
    h.step(180)
    wait_closed_party(session,run)
    run.update(after=party_summary(h), final_snapshot=trace.snapshot())
    session.checkpoint(run['name']+'-finished', run)
    validate_positive(run)
    trace.run = None

