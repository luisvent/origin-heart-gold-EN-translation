#!/usr/bin/env python3
"""Fresh-boot ability-banner fixture. Run from repo root; outputs are private.

Both Pokémon have Mold Breaker to trigger both banners. Override only the
renderer argument to display the requested ability, without changing mechanics.
"""
import argparse
import json
from pathlib import Path
import emu_harness as E
from emu_fixes import lead


def run(rom, sav, out, ability=4):
    rows, pending, widths = [], [], []
    with E.start_at(109, 16, 14, rom=rom, sav=sav, out=out, verbose=False) as h:
        lead(h, 160, level=40, moves=[150])  # Feraligatr: ten-character nickname
        h.edit_party_mon(0, ability=104, item=0)
        def entry(h):
            h.reg.r0 = ability
        def width(h):
            widths.append({'frame': h.frame, 'ability_width': h.reg.r0,
                           'nickname_width': h.reg.r7})
        def render(h):
            rows.append({'frame': h.frame, 'font': h.reg.r1, 'x': h.reg.r3,
                         'y': h.u32(h.reg.sp), 'width': h.u8(h.reg.r0 + 7) * 8,
                         'height': h.u8(h.reg.r0 + 8) * 8})
            pending.append(h.frame + 80)
        h.on_exec(0x02226658, entry)
        h.on_exec(0x02226708, width)
        h.on_exec(0x0222674C, render)
        h.on_exec(0x0222676C, render)
        wild = E.wild_battle(h, 452, 20, moves=[150])
        for a in wild['copies']:
            p = int(a, 16)
            h.write(p, E.encode_pokemon(h.read(p, 136), ability=104))
        # Native slide-in runs while the introduction advances.
        for i in range(2400):
            h.step(1)
            while pending and h.frame >= pending[0]:
                pending.pop(0)
                h.screenshot('banner-' + str(h.frame))
            if i % 90 == 80:
                h.press('B', after=0)
            if i > 100 and h.on_screen('battle_menu'):
                break
        assert h.on_screen('battle_menu'), 'battle failed to reach command menu'
        assert len(rows) >= 4, 'both sides did not display a banner'
        report = {'ability': ability, 'rows': rows, 'widths': widths, 'menu': True}
        Path(out, 'trace.json').write_text(json.dumps(report, indent=2) + '\n')
        return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', type=Path, required=True)
    p.add_argument('--sav', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--ability', type=int, default=4)
    a = p.parse_args()
    print(json.dumps(run(a.rom.resolve(), a.sav.resolve(), a.out.resolve(), a.ability)))
