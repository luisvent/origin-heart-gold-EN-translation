"""Separate-process battery/default probes, dispatched only by supervised run.py.

No old states, RTC/movie overrides, host settings writes or emulator reset calls.
Only the Harness's import/cold-boot setup touches the emulator reset API.
"""
import json
import os
from pathlib import Path
import shutil
import traceback
from support import ROOT, OUTPUT, sha256
from evidence import write_json, utc, register_values
from native_ui_oracles import inspect_battery


def run(args):
    from native_ui import candidate_binding, Harness
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    assert out.is_relative_to(OUTPUT)
    result={'status':'running','layer':'native ARM gameplay UI','old_state_loaded':False,
            'nonce':os.environ.get('DG_TEST_NONCE'),'started_utc':utc(),'cases':{},'phase':args.phase,
            'pid':os.getpid(),'events':[],'inputs':[]}
    path=out/'result.json'
    def flush():write_json(path,result)
    flush()
    try:
        receipt,binding=candidate_binding(args.receipt);result['binding']=binding
        source=Path(os.environ.get('DG_UI_OUT',out.parent/'ui')).resolve();saved=None;checkpoint=None
        if args.phase in ('reload','cold0'):
            checkpoint_path=source/('title-zero.json' if args.phase=='cold0' else 'persistence.json')
            checkpoint=json.loads(checkpoint_path.read_text())
            process=json.loads((source/'process.json').read_text())
            assert process['status'] in ('passed','failed') and process.get('finished_utc')
            assert checkpoint['binding']==binding and checkpoint['nonce']==process['nonce']
            saved=Path(checkpoint['saved_battery']['path']).resolve()
            assert saved.is_relative_to(source) and sha256(saved)==checkpoint['saved_battery']['sha256']
            assert checkpoint['save_expected']==checkpoint['battery_inspection']['options']
            assert checkpoint['battery_inspection']['counter']!=checkpoint['battery_before']['counter']
            result['prerequisite']={'checkpoint_sha256':sha256(checkpoint_path),
                                    'nonce':process['nonce'],'source_pid':process['pid'],
                                    'battery_sha256':sha256(saved)}
            assert os.getpid()!=process['pid'],'reload is not a new process'
            copied=out/'reload.sav';shutil.copyfile(saved,copied)
        else:
            copied=None  # genuine blank emulator battery, never a fixture word
        os.environ['SDL_AUDIODRIVER']='dummy'
        labels=receipt['build']['elf_labels'];payload=(Path(receipt['artifacts'])/'resident.bin').read_bytes()
        with Harness(rom=Path(receipt['output']['path']),sav=copied,out=out,verbose=False,emulator='desmume') as h:
            state={};initial=[];startup=[];printer=[];publication=[]
            def hook(name):
                def record(h):
                    a=register_values(h.reg)
                    if name=='input':state['address']=a[0]
                    elif len(result['events'])<300:result['events'].append({'name':name,'frame':h.frame,'args':a})
                return record
            for name in ('dg_menu_init','dg_menu_exit','dg_menu_field_getter'):
                h.on_exec(labels[name]&~1,hook(name))
            h.on_exec(labels['dg_menu_input']&~1,hook('input'))
            def initialized(h):
                bank=getattr(h.reg,'r',h.reg);p=bank[4]&0xffffffff
                initial.append({'frame':h.frame,'address':p,'word':h.u16(p)})
            h.on_exec(0x0202b1aa,initialized)  # actual native Options_Init return
            def published(h):
                runtime=h.u32(0x021106c8)
                assert 0x02000000<=runtime<0x023dc000
                offset=h.u32(runtime+0x2e02c)
                publication.append({'frame':h.frame,'save':runtime,'flag':h.u32(runtime+4),
                                    'array1_offset':offset,'word':h.u16(runtime+0x10+offset)})
            h.on_exec(0x02000cdc,published)

            h.on_exec(0x020040b8,lambda h:startup.append({'frame':h.frame,'title':register_values(h.reg)[0]}))
            def printed(h):
                a=register_values(h.reg)
                if len(printer)<3000:printer.append({'frame':h.frame,'word':a[0],'masked':a[1]})
                assert a[1]==a[0]&4,'actual printer mask consumed difficulty bits'
            h.on_exec(0x01ff876a,printed)
            def press(button,after):
                result['inputs'].append({'frame':h.frame,'key':button,'after':after});h.press(button,after=after)
            def touch(x,y,after):
                result['inputs'].append({'frame':h.frame,'touch':[x,y],'after':after});h.touch(x,y,after=after)
            def point(name):
                actual=bytearray(h.read(0x023dc000,len(payload)))
                for a,z in receipt['build']['zero_ranges']:actual[a-0x023dc000:z-0x023dc000]=payload[a-0x023dc000:z-0x023dc000]
                assert actual==payload,'resident immutable payload changed'
                h.screenshot(name);result['initializers']=initial;result['startup']=startup;result['printer']=printer;result['publication']=publication
                flush();print(json.dumps({'phase':args.phase,'point':name,'frame':h.frame}),flush=True)
            h.step(2400);press('START',700);point('title')
            press('A',200);point('continue-or-newgame')
            press('A',900);point('loaded-or-intro')
            options=h.array(1);word=h.u16(options)
            result['options']={'save':h.save,'address':options,'word':word}
            if args.phase in ('reload','cold0'):
                assert h.in_field(),'copied battery did not reach field'
                assert word==checkpoint['save_expected'],'native SaveData did not reload full Options word'
                result['battery_inspection']=inspect_battery(copied,checkpoint['save_options_offset'])
                assert all(s['coherent'] for s in result['battery_inspection']['slots']),'CRC/mirror pair invalid'
                assert result['battery_inspection']==checkpoint['battery_inspection']
                for custom in (True,False):
                    if custom:h.hold('L');h.step(2)
                    before=len(result['events']);touch(123,113,240)
                    if custom:h.release('L')
                    h.step(60)
                    assert len(result['events'])>before and 'address' in state
                    d=state['address'];assert h.u32(d+0x24)==options
                    # Both actual Options pages share one resident owner;
                    # mode identifies the visible page, not ownership.
                    assert h.u32(labels['page']+24)==d
                    assert h.u32(labels['page']+48)==int(custom)
                    assert h.u16(options)==word
                    point('reloaded-'+('difficulty' if custom else 'normal'))
                    press('B',240);assert h.u16(options)==word
                # A real field message starts the native text printer; no text
                # injection or fabricated message duration is used.
                touch(123,73,180);point('reloaded-save-prompt');press('B',180)
                assert startup and startup[-1]['title']==((word>>4)&1),'startup title extraction mismatch'
                assert printer and any(e['word']==word for e in printer),'no native text-printer read of reloaded Options'
                assert sha256(saved)==checkpoint['saved_battery']['sha256']
                files=[out/'reloaded-difficulty.png',out/'reloaded-normal.png',out/'reloaded-save-prompt.png',out/'title.png',copied]
                if args.phase=='reload':
                    case='ui.save_reload'
                else:
                    # Combine two fresh native cold boots with the full UI
                    # matrix. Each prerequisite must match this source binding
                    # and its own supervised invocation; copy reviewed evidence
                    # into this case's artifact directory for a durable closure.
                    other_dir=Path(os.environ.get('DG_RELOAD_OUT',out.parent/'reload')).resolve()
                    other=json.loads((other_dir/'result.json').read_text())
                    other_process=json.loads((other_dir/'process.json').read_text())
                    ui=json.loads((source/'result.json').read_text())
                    assert other['status']==other_process['status']=='passed'
                    assert other['nonce']==other_process['nonce'] and other['binding']==binding
                    assert ui['status']=='passed' and ui['binding']==binding and ui['nonce']==process['nonce']
                    assert {(r['flags'],r['title'],r['speed']) for r in ui['permutations']}=={(f,t,s) for f in range(8) for t in range(2) for s in range(2)}
                    assert not [v for v in ui['preview'] if v['mode']=='custom' and v['name']!='row']
                    assert word&0x14==0 and other['options']['word']&0x14==0x14
                    assert word&0x8028==other['options']['word']&0x8028==0x8028
                    assert {startup[-1]['title'],other['startup'][-1]['title']}=={0,1}
                    assert any(p['word']==word and p['masked']==0 for p in printer)
                    assert any(p['word']==other['options']['word'] and p['masked']==4 for p in other['printer'])
                    for name,src in [('fast-result.json',other_dir/'result.json'),('fast-process.json',other_dir/'process.json'),
                                     ('fast-title.png',other_dir/'title.png'),('fast-printer.png',other_dir/'reloaded-save-prompt.png'),
                                     ('ui-matrix.json',source/'result.json'),('ui-process.json',source/'process.json')]:
                        dst=out/name;shutil.copyfile(src,dst);files.append(dst)
                    result['combined_cold_values']={'title':[0,1],'textspeed':[0,1],'ui_permutations':32,
                                                   'fast_nonce':other['nonce'],'ui_nonce':ui['nonce']}
                    case='ui.title_textspeed'
                trace=out/'reload.trace.json';write_json(trace,result);files.append(trace)
                result['cases'][case]={'status':'passed','artifacts':[{'path':str(p),'sha256':sha256(p)} for p in files]}
            else:
                # Exact native default, not merely the absence of difficulty
                # flags. Publication must follow initialization; selecting New
                # Game runs the initializer again after the title input.
                assert word==0x204,'fresh Options defaults differ from native initializer'
                matches=[e for e in initial if e['address']==options and e['word']==word]
                assert len(matches)>=2 and matches[0]['frame']<2400<matches[-1]['frame']
                assert publication and publication[0]['save']==h.save and publication[0]['word']==word
                assert matches[0]['frame']<=publication[0]['frame']<matches[-1]['frame']
                assert publication[0]['flag']==0 and h.u32(h.save+4)==0,'blank new game unexpectedly claims a cartridge save'
                assert h.u32(0x021106c8)==h.save,'native published SaveData identity differs'
                assert word&0x8028==0
                legacy=json.loads((source/'result.json').read_text())
                legacy_process=json.loads((source/'process.json').read_text())
                assert legacy['status']==legacy_process['status']=='passed'
                assert legacy['binding']==binding and legacy['nonce']==legacy_process['nonce']
                assert legacy['options_before']==legacy['battery_before']['options']==0x200
                assert all(s['coherent'] for s in legacy['battery_before']['slots'])
                assert legacy['options_before']&0x8028==0
                assert sha256(ROOT/'work/build/memcheck/trainer.sav')==binding['battery_source_sha256']
                result['legacy']={'word':legacy['options_before'],'battery':legacy['battery_before'],
                                  'nonce':legacy['nonce'],'source_sha256':binding['battery_source_sha256']}
                point('newgame-defaults')
                files=[out/'newgame-defaults.png',out/'continue-or-newgame.png']
                for name,src in [('legacy-result.json',source/'result.json'),('legacy-process.json',source/'process.json')]:
                    dst=out/name;shutil.copyfile(src,dst);files.append(dst)
                trace=out/'defaults.trace.json';write_json(trace,result);files.append(trace)
                result['cases']['ui.legacy_newgame']={'status':'passed','artifacts':[{'path':str(p),'sha256':sha256(p)} for p in files]}
        assert candidate_binding(args.receipt)[1]==binding,'sources changed during replay'
        result['status']='passed'
    except BaseException:
        result.update(status='failed',failure=traceback.format_exc());flush();raise
    finally:
        result['finished_utc']=utc();flush()
    return 0
