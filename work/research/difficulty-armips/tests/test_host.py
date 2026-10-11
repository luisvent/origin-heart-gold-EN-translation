"""ASan/UBSan over actual shipping C; mocks replace native primitives only."""
import os
import subprocess
import unittest
from support import ROOT, SOURCE, OUTPUT, command, load_rom, sha256
from evidence import write_json

class SanitizedHostTests(unittest.TestCase):
    def run_driver(self, name, modules, defines):
        stage=OUTPUT/'host'/name;stage.mkdir(parents=True,exist_ok=True)
        report={'status':'running','layer':'host shipping C with native primitive mocks; not ARM execution'}
        write_json(stage/'provenance.json',report)
        try:
            driver=SOURCE/'tests/drivers'/f'{name}_check.c'
            if name=='items':
                from ndspy.narc import NARC
                rows=NARC(load_rom().getFileByName('a/0/1/7')).files
                masks=[int.from_bytes(b[8:10],'little')>>11 for b in rows]
                (stage/'masks.h').write_text('static const unsigned masks[] = {'+','.join(map(str,masks))+'};\n')
            sources=[SOURCE/'native'/f'{m}.c' for m in modules]
            argv=['clang','-std=c99','-O1','-g','-Wall','-Wextra','-Werror',
                  '-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer',
                  '-I',SOURCE/'native','-I',stage,*['-D'+d for d in defines],driver,*sources,'-o',stage/'check']
            command(argv)
            env=dict(os.environ,ASAN_OPTIONS='halt_on_error=1:detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
            run=subprocess.run([stage/'check'],cwd=ROOT,env=env,text=True,capture_output=True,timeout=90)
            (stage/'run.log').write_text(run.stdout+run.stderr)
            report.update(command=list(map(str,argv)),sources={str(p.relative_to(ROOT)):sha256(p) for p in [driver,*sources,*sorted((SOURCE/'native').glob('*.h'))]},
                          binary_sha256=sha256(stage/'check'),returncode=run.returncode)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertNotIn('runtime error:',run.stderr)
            self.assertNotIn('ERROR: AddressSanitizer',run.stderr)
            self.assertIn('PASS',run.stdout)
            report['status']='passed'
        finally:
            if report['status']=='running':report['status']='failed'
            write_json(stage/'provenance.json',report)

    def test_settings_options_sanitized(self):
        self.run_driver('options',['settings','options'],['DG_OPTIONS_HOST_TEST'])
    def test_runtime_caps_sanitized(self):
        self.run_driver('runtime',['runtime','caps','settings'],['DG_RUNTIME_HOST_TEST','DG_CAPS_HOST_TEST'])
    def test_items_sanitized(self):
        self.run_driver('items',['items','policy'],['DG_ITEMS_HOST_TEST'])
    def test_growth_sanitized(self):
        self.run_driver('growth',['growth','policy'],['DG_GROWTH_HOST_TEST'])
