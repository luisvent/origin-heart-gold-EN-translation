"""First bounded functional progression checkpoint; six independent cold boots.

Predicates are explicit inputs, never claims of native victory-script execution.
Expected caps are independently pinned D-2312 examples, not computed by shipping C.
"""
CASES = {
    'prefix': dict(badges=0x0001, erika=False, prewin=False, cap=20, level=20),
    'erika-prewin': dict(badges=0x0007, erika=False, prewin=True, cap=38, level=38),
    'erika-win': dict(badges=0x0007, erika=True, prewin=True, cap=55, level=55),
    'skipped-koga': dict(badges=0xFFDF, erika=False, prewin=False, cap=55, level=55),
    'plateau-81': dict(badges=0x007F, erika=False, prewin=False, cap=100, level=81),
    'plateau-89': dict(badges=0x07FF, erika=False, prewin=False, cap=100, level=89),
}


def plan(base):
    return [dict(name='progression-'+name, progression=name, out=base/name) for name in CASES]


def report_paths(base):
    return [base/name/'result.json' for name in CASES]
