"""The test bench's battery saves (.dsv): made locally, found by SHA-256, never committed.

  ADVAI_ES_REPO=/path/to/spanish/repo .venv/bin/python work/advanced-ai/testbench/lib/saves.py make [NAME ...]
                                                                          # write them (default all; or --es-repo DIR)
  .venv/bin/python work/advanced-ai/testbench/lib/saves.py check                            # which ones are in place

The Spanish test bench boots its runs from saves in its tests/ folder (violet_gym.dsv: the field at the Violet City
Gym door, a level-100 lead, the event NPCs hidden; the pre-battle state of aibench, aivsai, aiprops and the checks is
made from it). `make` takes each one from the Spanish workspace's commit dc8577c with `git show` (read only) and
writes it to work/build/advanced-ai/saves/ (ignored); path() hands a tool the file only when its SHA-256 is the one
recorded here, so every run starts from the same bytes. The saves are game data: keep them out of git (*.dsv is
ignored).
"""
import argparse
import hashlib
import os
import subprocess
import sys

import tbpaths

ES_REPO = os.environ.get('ADVAI_ES_REPO')     # the Spanish workspace repository (or --es-repo)
ES_COMMIT = 'dc8577c'
# name -> SHA-256 of work_es/tests/<name>.dsv at dc8577c
SAVES = {
    'violet_gym': '42434c064575c14dafe587cb2a9f30fa21dd2a786d6b7cc91d53ec8b6d65e02b',
    'party_nostatus': '2e6dc14b5075bfba550d5e8becb3bbad8d3ed81ff2d24d611cb6a7d932c31b64',
    'party': 'fc3444105a40edac3a90c5671421ee33fca36325f1944991bc68692ab0f4a811',
    'items': '3e11d85e6e65d67ac3a84528890ac53a6a5df73d3b00722b165c25ef254fa596',
    'whiteout': 'acb0743f2449abc8a466c4950ed132797d2e882348804ce120cad671b0b697a4',
    'blank': 'bb7684028d47e3eb2a36e5b345d60d4a0eed29f0307731fa36d3c83bb2968be3',
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def path(name):
    """The checked save `name` (SAVES), or exit with how to make it."""
    if name not in SAVES:
        raise KeyError('no test save %r (known: %s)' % (name, ', '.join(sorted(SAVES))))
    p = os.path.join(tbpaths.SAVES, name + '.dsv')
    if not os.path.exists(p):
        sys.exit('the test save %s is missing: run %s make %s' % (tbpaths.rel(p), tbpaths.rel(__file__), name))
    got = sha256(p)
    if got != SAVES[name]:
        sys.exit('%s has SHA-256 %s, not %s: run %s make %s' % (tbpaths.rel(p), got, SAVES[name], tbpaths.rel(__file__), name))
    return p


def make(names, repo):
    os.makedirs(tbpaths.SAVES, exist_ok=True)
    for name in names:
        data = subprocess.run(['git', '-C', repo, 'show', '%s:work_es/tests/%s.dsv' % (ES_COMMIT, name)], check=True,
                              capture_output=True).stdout
        got = hashlib.sha256(data).hexdigest()
        if got != SAVES[name]:
            sys.exit('%s.dsv at %s has SHA-256 %s, not %s' % (name, ES_COMMIT, got, SAVES[name]))
        out = os.path.join(tbpaths.SAVES, name + '.dsv')
        tmp = out + '.tmp'
        with open(tmp, 'wb') as f:
            f.write(data)
        os.replace(tmp, out)
        print('%s  %s' % (got, tbpaths.rel(out)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=('make', 'check'))
    ap.add_argument('names', nargs='*')
    ap.add_argument('--es-repo', default=ES_REPO, help='the Spanish workspace repository (default: ADVAI_ES_REPO)')
    a = ap.parse_args()
    names = a.names or sorted(SAVES)
    unknown = [n for n in names if n not in SAVES]
    if unknown:
        ap.error('unknown save(s): %s' % ', '.join(unknown))
    if a.action == 'make':
        if not a.es_repo:
            ap.error('give --es-repo DIR or set ADVAI_ES_REPO to the Spanish workspace repository')
        return make(names, a.es_repo)
    bad = 0
    for name in names:
        p = os.path.join(tbpaths.SAVES, name + '.dsv')
        state = 'missing' if not os.path.exists(p) else 'ok' if sha256(p) == SAVES[name] else 'WRONG SHA-256'
        bad += state != 'ok'
        print('%-15s %s' % (name, state))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
