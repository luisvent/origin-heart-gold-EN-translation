#!/usr/bin/env python3
"""Prune redundant difficulty-installer ROMs, preserving logs and public outputs."""
import argparse
import fcntl
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'work/build/difficulty-v2/integration-impl'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='delete listed copies')
    parser.add_argument('--min-age-hours', type=float, default=1)
    args = parser.parse_args()
    if Path.cwd().resolve() != ROOT:
        parser.error('run from repository root')
    if args.min_age_hours < 0:
        parser.error('minimum age must be nonnegative')
    if not OUTPUT.is_dir():
        print('No installer output directory.')
        return
    with (OUTPUT/'.publication.lock').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (OUTPUT/'.publication.json').exists():
            parser.error('pending publication recovery; retain all recovery material')
        cutoff = time.time() - args.min_age_hours * 3600
        files = []
        for folder in sorted(OUTPUT.iterdir()):
            if folder.is_symlink() or not folder.is_dir():
                continue
            if folder.name.startswith('publication-'):
                names = ('candidate.nds', 'old-candidate.nds', 'restore-candidate.nds')
            elif folder.name.startswith('run-') and (folder/'receipt.json').is_file():
                # Only completed staging with a receipt; retain failed build evidence.
                receipt = json.loads((folder/'receipt.json').read_text())
                if Path(receipt['output']['path']).resolve() != OUTPUT/'candidate.nds':
                    continue
                names = ('candidate.pending.nds',)
            else:
                continue
            for name in names:
                path = folder/name
                if path.is_file() and not path.is_symlink() and path.stat().st_mtime < cutoff:
                    files.append((path, path.stat().st_size))
        for path, size in files:
            print(f'{size:>12} {path.relative_to(ROOT)}')
        print(f'{len(files)} copies, {sum(size for _, size in files)/2**30:.2f} GiB; '
              f'{"deleting" if args.apply else "preview only"}')
        if args.apply:
            for path, _ in files:
                path.unlink()


if __name__ == '__main__':
    main()
