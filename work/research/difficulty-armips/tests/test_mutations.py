"""Prove the real-C drivers reject representative regressions in isolated copies.
Shipping sources are read only. Mutants never reach the installer or emulator.
"""
import subprocess
import unittest
from ndspy.narc import NARC
from support import SOURCE, OUTPUT, ROOT, command, load_rom
from evidence import write_json

class DriverMutationTests(unittest.TestCase):
    def check_mutant(self,name,modules,defines,mutated,old,new,case=None):
        stage=OUTPUT/'mutations'/(case or name);stage.mkdir(parents=True,exist_ok=True)
        status={'status':'running','layer':'test sensitivity, deliberately broken source copy'}
        write_json(stage/'result.json',status)
        try:
            text=(SOURCE/'native'/f'{mutated}.c').read_text();self.assertEqual(text.count(old),1)
            source=stage/f'{mutated}.c';source.write_text(text.replace(old,new))
            if name=='items':
                rows=NARC(load_rom().getFileByName('a/0/1/7')).files
                (stage/'masks.h').write_text('static const unsigned masks[] = {'+','.join(str(int.from_bytes(b[8:10],'little')>>11) for b in rows)+'};\n')
            sources=[source if n==mutated else SOURCE/'native'/f'{n}.c' for n in modules]
            cmd=['clang','-std=c99','-O1','-Wall','-Wextra','-Werror','-I',SOURCE/'native','-I',stage,
                 *['-D'+d for d in defines],SOURCE/'tests/drivers'/f'{name}_check.c',*sources,'-o',stage/'mutant']
            command(cmd)
            result=subprocess.run([stage/'mutant'],cwd=ROOT,text=True,capture_output=True,timeout=30)
            (stage/'run.log').write_text(result.stdout+result.stderr)
            self.assertNotEqual(result.returncode,0,'driver falsely accepted mutant')
            self.assertIn('Assertion failed',result.stderr)
            status.update(status='passed',mutant_returncode=result.returncode,mutation={'old':old,'new':new})
        finally:
            if status['status']=='running':status['status']='failed'
            write_json(stage/'result.json',status)

    def test_growth_unclamped_output_rejected(self):
        self.check_mutant('growth',['growth','policy'],['DG_GROWTH_HOST_TEST'],'growth',
                         '*amount = dg_clamp_exp(read32(mon + 0x18u), *amount, ceiling, 1u);',
                         '*amount = dg_clamp_exp(read32(mon + 0x18u), *amount, ceiling, 0u);')
    def test_options_textspeed_bit_loss_rejected(self):
        self.check_mutant('options',['options','settings'],['DG_OPTIONS_HOST_TEST'],'settings',
                         '(w & ~DG_DIFFICULTY_MASK)', '(w & ~(DG_DIFFICULTY_MASK | 4u))')
    def test_items_full_restore_wrong_category_rejected(self):
        self.check_mutant('items',['items','policy'],['DG_ITEMS_HOST_TEST'],'items',
                         'case 23: return 12u;', 'case 23: return 4u;')
    def test_items_observed_wrong_bag_offset_rejected(self):
        self.check_mutant('items',['items','policy'],['DG_ITEMS_HOST_TEST'],'items',
                         'bag = read32(setup + 0x108u);', 'bag = read32(setup + 0x168u);',
                         case='items-old-bag-offset')
    def test_items_unbound_arbitrary_bag_rejected(self):
        self.check_mutant('items',['items','policy'],['DG_ITEMS_HOST_TEST'],'items',
                         'read32(args + 4u) != bag', '0', case='items-unbound-bag')
    def test_runtime_replay_acceptance_rejected(self):
        self.check_mutant('runtime',['runtime','caps','settings'],['DG_RUNTIME_HOST_TEST','DG_CAPS_HOST_TEST'],'runtime',
                         'if (control != 0u) return 0;', 'if (control == 0xFFFFFFFFu) return 0;')
    def test_runtime_cap_decreases_rejected(self):
        self.check_mutant('runtime',['runtime','caps','settings'],['DG_RUNTIME_HOST_TEST','DG_CAPS_HOST_TEST'],'caps',
                         'if (maxima[i]>cap) cap=maxima[i];', 'cap=maxima[i];')
    def test_runtime_scripted_wild_bypass_rejected(self):
        self.check_mutant('runtime',['runtime','caps','settings'],['DG_RUNTIME_HOST_TEST','DG_CAPS_HOST_TEST'],'runtime',
                         'if (control == 8u) return flags == 0u;', 'if (control == 8u) return 0;')
    def test_runtime_control8_overbroad_acceptance_rejected(self):
        self.check_mutant('runtime',['runtime','caps','settings'],['DG_RUNTIME_HOST_TEST','DG_CAPS_HOST_TEST'],'runtime',
                         'if (control == 8u) return flags == 0u;', 'if (control == 8u) return 1;')
    def test_revival_wrong_attribute_rejected(self):
        self.check_mutant('items',['items','policy'],['DG_ITEMS_HOST_TEST'],'items',
                         'attr != 38u', 'attr != 23u',case='revival-attribute')
    def test_revival_missing_all_scope_rejected(self):
        self.check_mutant('items',['items','policy'],['DG_ITEMS_HOST_TEST'],'items',
                         '(s->flags & DG_ITEMS_ALL) == 0u', '0',case='revival-all')
    def test_revival_unbound_actor_rejected(self):
        self.check_mutant('items',['items','policy'],['DG_ITEMS_HOST_TEST'],'items',
                         '!local_mon(root, (uintptr_t)actor)', 'actor == 0',case='revival-actor')
