"""Static migration checks only. No ROM, emulator, save, or historical command replay."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
BASE = 0x023DF000


def run(args, cwd, success=True):
    result = subprocess.run([str(x) for x in args], cwd=cwd, text=True, capture_output=True)
    if (result.returncode == 0) != success:
        raise RuntimeError(f"{args[0]}: unexpected exit {result.returncode}\n{result.stdout}{result.stderr}")
    return result


def branch(at, target, link=False):
    delta = target - at - 8
    assert delta % 4 == 0 and -(1 << 25) <= delta < (1 << 25)
    return (0xEB000000 if link else 0xEA000000) | ((delta >> 2) & 0xFFFFFF)


def elf_sections(path):
    data = path.read_bytes()
    header = struct.unpack_from('<16sHHIIIIIHHHHHH', data)
    assert header[0][:6] == b'\x7fELF\x01\x01'
    sections = [struct.unpack_from('<10I', data, header[6] + i * header[11])
                for i in range(header[12])]
    names_section = sections[header[13]]
    names = data[names_section[4]:names_section[4] + names_section[5]]
    return {names[s[0]:names.index(b'\0', s[0])].decode():
            (s[3], data[s[4]:s[4] + s[5]]) for s in sections if s[1] == 1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--armips', required=True)
    parser.add_argument('--gnu-wrapper', type=Path, required=True,
                        help='Recovered line-2785 wrapper.s; read as source, never executed')
    parser.add_argument('--linker', required=True)
    parser.add_argument('--include-dir', type=Path, default=ROOT / 'work/patches/include',
                        help='Current armips guard includes; specify for the older recovery checkout')
    parser.add_argument('--out', type=Path, default=ROOT / 'work/build/difficulty-armips-port/check.json')
    args = parser.parse_args()
    armips = Path(args.armips).resolve()
    banner = run([armips], ROOT, success=False)
    assert 'armips assembler v0.11.0' in banner.stdout + banner.stderr
    wrapper = args.gnu_wrapper.resolve()
    checks = []
    with tempfile.TemporaryDirectory(prefix='difficulty-armips-') as tmp:
        stage = Path(tmp)
        rom = stage / 'rom'
        rom.mkdir()
        shutil.copytree(args.include_dir.resolve(), stage / 'include')
        run([armips, SOURCE / 'foundation.asm', '-definelabel', 'BRIDGE_DISPATCH',
             '0x023DF301', '-sym', stage / 'foundation.sym'], stage)
        payload = (stage / 'foundation.bin').read_bytes()
        words = [0xE92D500F, 0xE10F0000, 0xE92D0003, 0xE59F0020,
                 0xE3A01000, 0xE5801004, 0xE5801008, 0xE59F1014,
                 0xE5801000, 0xE8BD0003, 0xE128F000, 0xE8BD500F,
                 branch(BASE + 48, 0x020F1B64), BASE + 0x100, 0x44524631]
        assert payload[:60] == struct.pack('<15I', *words)
        assert payload[60:0x200] == bytes(0x200 - 60)
        checks.append('bootstrap equals corrected historical linked-build words; state starts zero')
        # Compile the historical GNU wrapper independently to check every instruction,
        # branch and pool entry in the armips translation.
        run(['clang', '--target=arm-none-eabi', '-mcpu=arm946e-s', '-c', wrapper,
             '-o', stage / 'wrapper.o'], ROOT)
        (stage / 'reference.ld').write_text('''SECTIONS {
 . = 0x023df200; .prefix : { *(.prefix) }
 . = ALIGN(16); .wrapper : { *(.wrapper) }
 bridge_dispatch = 0x023df301;
 /DISCARD/ : { *(.ARM.attributes) }
}\n''')
        run([args.linker, '-T', stage / 'reference.ld', '-o', stage / 'reference.elf',
             stage / 'wrapper.o'], ROOT)
        reference = elf_sections(stage / 'reference.elf')
        for section in ('.prefix', '.wrapper'):
            address, data = reference[section]
            assert payload[address - BASE:address - BASE + len(data)] == data, section
        checks.append('Thumb prefix and ARM wrapper byte-identical to independently linked GNU source')
        run([armips, SOURCE / 'foundation.asm'], stage, success=False)
        checks.append('missing native dispatcher rejected')
        original = bytearray(0x1106A0)
        expected = {0x908: branch(0x02000908, 0x020F1B64, True),
                    0xD1970: 0x023E0000, 0x3E544: 0xFF00F7EA}
        for offset, value in expected.items():
            struct.pack_into('<I', original, offset, value)
        image = rom / 'arm9.bin'
        image.write_bytes(original)
        run([armips, SOURCE / 'hooks.asm', '-definelabel', 'GUARDS_REAL', '1'], rom)
        patched = image.read_bytes()
        assert len(patched) == len(original)
        allowed = {i for off in expected for i in range(off, off + 4)}
        assert all(a == b or i in allowed for i, (a, b) in enumerate(zip(original, patched)))
        assert struct.unpack_from('<I', patched, 0x908)[0] == branch(0x02000908, BASE, True)
        assert struct.unpack_from('<I', patched, 0xD1970)[0] == BASE
        delta = BASE + 0x200 - (0x0203E544 + 4)
        assert patched[0x3E544:0x3E548] == struct.pack('<HH', 0xF000 | ((delta >> 12) & 0x7FF),
                                                     0xF800 | ((delta >> 1) & 0x7FF))
        checks.append('hooks change only the three declared four-byte regions with expected targets')
        for offset in expected:
            wrong = bytearray(original)
            wrong[offset] ^= 1
            image.write_bytes(wrong)
            result = run([armips, SOURCE / 'hooks.asm', '-definelabel', 'GUARDS_REAL', '1'],
                         rom, success=False)
            assert 'guard failed' in result.stdout + result.stderr
            assert image.read_bytes() == wrong
        checks.append('each corrupted hook guard rejects input without changing the file')
    report = dict(scope='Static assembly migration only; no ROM or runtime validation',
                  checks=checks, foundation_bytes=len(payload),
                  foundation_sha256=hashlib.sha256(payload).hexdigest(),
                  reference_sha256=hashlib.sha256(wrapper.read_bytes()).hexdigest(),
                  sources={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in (SOURCE / 'foundation.asm', SOURCE / 'hooks.asm')})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
