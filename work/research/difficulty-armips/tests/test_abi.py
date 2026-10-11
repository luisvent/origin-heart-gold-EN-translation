"""Compiled data layouts, real instruction ABI and emission bounds."""
import json
from pathlib import Path
import shutil
import unittest
from candidate_tools import assembled, build
from support import SOURCE, scratch, command

class NativeStaticABITests(unittest.TestCase):
    def test_target_arm_struct_layout(self):
        with scratch('layout-') as tmp:
            p=Path(tmp)/'layout.c'
            p.write_text('''#include <stddef.h>
#include "growth.h"
#include "settings.h"
_Static_assert(sizeof(DG_GrowthSnapshot)==20,"snapshot ABI");
_Static_assert(offsetof(DG_GrowthSnapshot,root)==12,"snapshot root");
_Static_assert(offsetof(DG_GrowthSnapshot,epoch)==16,"snapshot epoch");
_Static_assert(sizeof(struct DG_SettingsTxn)==20,"ARM transaction ABI");
_Static_assert(offsetof(struct DG_SettingsTxn,draft_flags)==16,"draft ABI");
''')
            command([build.CLANG,*build.FLAGS,'-std=c11','-I',SOURCE/'native','-fsyntax-only',p])

    def test_actual_runtime_adapters_restore_args_sp_and_callee_saved(self):
        from runtime_abi_model import check_adapters
        self.assertEqual(check_adapters(),40)

    def test_actual_options_thunks_and_single_halfword_commit(self):
        stage,_,_,_,_,_,payload,report=assembled()
        hooks=json.loads((SOURCE/'native/options_hooks.json').read_text())['hooks']
        from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
        md=Cs(CS_ARCH_ARM,CS_MODE_THUMB);md.detail=True
        span=next(s for s in report['stub_spans'] if s['file']=='options-stubs.bin')
        for i,h in enumerate(hooks):
            addr=span['start']+8*i;blob=payload[addr-build.BASE:addr-build.BASE+8]
            self.assertEqual([(x.mnemonic,x.op_str) for x in md.disasm(blob[:4],addr)], [('ldr','r3, [pc, #0]'),('bx','r3')])
            self.assertEqual(int.from_bytes(blob[4:],'little'),report['elf_labels'][h['target']])
        symbol=next(s for s in report['symbols'] if s['name']=='dg_options_apply')
        start=(symbol['value']&~1)-build.BASE
        ops=list(md.disasm(payload[start:start+symbol['size']],symbol['value']&~1))
        stores=[i for i in ops if i.mnemonic=='strh']
        self.assertEqual(len(stores),1)

    def test_asm_rejects_unaligned_and_overflowed_stub_placement(self):
        stage,_,_,_,raw,_,_,report=assembled()
        for name,label in [('items.asm','ITEM_STUB_BASE'),('options.asm','DG_OPTIONS_STUB_BASE'),('runtime.asm','DG_RUNTIME_STUB_BASE')]:
            cmd=next(c['argv'][:] for c in report['commands'] if c['argv'][0]==build.ARMIPS and any(Path(a).name==name for a in c['argv'][1:]))
            with scratch('bad-stub-layout-') as tmp:
                tmp=Path(tmp)
                for f in ('c-symbols.inc','options.asm','runtime.asm'):
                    if (stage/f).exists():shutil.copyfile(stage/f,tmp/f)
                for f,b in raw.items():(tmp/f).write_bytes(b)
                for span in report['stub_spans']:(tmp/span['file']).write_bytes(bytes(span['end']-span['start']))
                cmd=[a.replace(str(stage),str(tmp)) for a in cmd]
                index=cmd.index(label)+1
                for address in (0x023DC001,0x023DFFFC,0xFFFFFFFC):
                    cmd[index]=hex(address)
                    before={p.name:p.read_bytes() for p in tmp.glob('*.bin')}
                    with self.subTest(source=name,address=hex(address)):
                        command(cmd,success=False)
                        self.assertEqual(before,{p.name:p.read_bytes() for p in tmp.glob('*.bin')})
