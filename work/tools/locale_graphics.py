#!/usr/bin/env python3
"""Prepare guarded ES graphics after the ordinary graphics stage; never save a ROM.

Run from the repository root. Raw assets/output are local, ignored game data.
The tracked selection policy pins the donor, EN rc4, and destination resources.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import gfx
import msgtool as m

WORK = Path(__file__).resolve().parent.parent
POLICY = WORK / 'graphics/locales/es/selection.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def require_hash(data, expected, label):
    if sha(data) != expected:
        raise ValueError(f'{label}: SHA-256 mismatch; re-review graphics selection')


def validate_fallbacks(fallbacks, get_file, mode):
    """Allow only explicitly recorded pixels; never catch a missing asset as fallback."""
    if mode not in ("allow-listed", "error"):
        raise ValueError(f"unknown graphics fallback policy: {mode}")
    if mode == "error" and fallbacks:
        raise ValueError("Spanish graphics require listed fallbacks: " + ", ".join(r["id"] for r in fallbacks))
    seen = set()
    for row in fallbacks:
        if row["id"] in seen:
            raise ValueError("duplicate graphics fallback id")
        seen.add(row["id"])
        fs = m.Narc.parse(get_file(row["narc"])).files
        if row["kind"] == "member":
            data = fs[row["member"]]
        elif row["kind"] == "screen_region":
            pixels = gfx.screen_to_image(gfx.NSCR(fs[row["screen"]]), gfx.NCGR(fs[row["graphic"]]))
            x0, y0, x1, y1 = row["rect"]
            if not (0 <= y0 < y1 <= len(pixels) and 0 <= x0 < x1 <= len(pixels[0])):
                raise ValueError("fallback region outside screen")
            region = [line[x0:x1] for line in pixels[y0:y1]]
            data = json.dumps(region, separators=(",", ":")).encode()
        else:
            raise ValueError("unsupported graphics fallback kind")
        require_hash(data, row["sha256"], "fallback " + row["id"])
    return fallbacks


def pixel_merge(base, donor, current):
    """Three-way merge existing indexed pixels, refusing overlapping edits."""
    if [len(x) for x in base] != [len(x) for x in donor] or [len(x) for x in base] != [len(x) for x in current]:
        raise ValueError('screen dimensions changed')
    result = [list(row) for row in current]
    for y, row in enumerate(base):
        for x, old in enumerate(row):
            new, cur = donor[y][x], current[y][x]
            if new != old:
                if cur not in (old, new):
                    raise ValueError(f'overlapping screen edits at {x},{y}')
                result[y][x] = new
    return result


def rebase_dex(original, baseline, donor, current, retail):
    """Repack sourced ES pixels into the existing audited tile pools.

    Keep the corrected header edge, search bars, direct-copy tiles 98/101,
    and the corrected member-71 list screen. Never draw new lettering.
    """
    result = list(current)
    def img(files, screen, graphic):
        return gfx.screen_to_image(gfx.NSCR(files[screen]), gfx.NCGR(files[graphic]))
    for gi, screens in ((1, [0, 7, 8]), (4, [5, 6, 9, 10, 11, 69, 70, 71])):
        g = gfx.NCGR(current[gi])
        used = {e & 1023 for files in (original, current) for s in screens for e in gfx.NSCR(files[s]).ents}
        # Header pool is already audited as unreferenced-first by make_dex_labels.
        if gi == 1:
            pool = [i for i in range(1, len(g.tiles)) if i not in used] + sorted(used - {0})
        else:
            pool = sorted(used - {0, 98, 101})
        targets = []
        for s in screens:
            if gi == 1:
                target = pixel_merge(img(baseline, s, gi), img(donor, s, gi), img(current, s, gi))
            elif s == 71:
                # Keep disabled-button artwork/palettes; source only the label band.
                target = img(current, s, gi)
                labels = img(donor, 6, gi)
                for y in range(22, 30):
                    for x in range(256):
                        target[y][x] = (target[y][x][0], labels[y][x][1])
            elif s in (5, 6, 11):
                target = img(donor, s, gi)
            else:
                target = img(current, s, gi)
            targets.append((gfx.NSCR(current[s]), target))
        if gi == 1:
            # User decision, 2026-10-13: the hack has the National Dex from the start.
            # Reuse the Spanish NACIONAL image for either runtime header selection.
            targets[1] = (gfx.NSCR(current[7]), targets[2][1])
            # Source the small switch label from Spanish retail, preserving its palette indices.
            switch = img(retail, 0, 1)
            for y in range(120, 136):
                for x in range(40, 216):
                    targets[0][1][y][x] = switch[y][x]
        tiles, entries = gfx.retile(g, targets, pool)
        if gi == 4 and any(tiles[t] != g.tiles[t] for t in (98, 101)):
            raise ValueError('Pokédex direct-copy background tiles changed')
        result[gi] = g.with_tiles(tiles)
        for s, (sc, wanted), ents in zip(screens, targets, entries):
            result[s] = sc.with_entries(ents)
            if img(result, s, gi) != wanted:
                raise ValueError(f'Pokédex screen {s}: sourced pixels not preserved')
    return result


def graphics_current(cn, us, output):
    """Run only the existing graphics stage in memory, with isolated outputs."""
    shutil.copytree(gfx.GRAPHICS / 'vendor', output / 'vendor')
    gfx.regenerate(cn, us, root=output)
    rom, base = m.load_rom(cn), m.load_rom(us)
    gfx.apply_patches(lambda p: m.get_file(rom, p), lambda p, b: m.set_file(rom, p, b),
                      lambda p: m.get_file(base, p), root=output,
                      code=gfx.CodeView(rom), us_code=gfx.CodeView(base), check_layout=True)
    return rom


def check_retail_dependencies(current, retail, members):
    """The sourced tiles must use identical palette/map/cell/animation data."""
    for i in members:
        if gfx.unpack(current[i])[0] != gfx.unpack(retail[i])[0]:
            raise ValueError(f'Spanish retail dependency {i} differs')


def plan(policy, original, baseline, donor, current, retail):
    planned, evidence = [], []
    for group in policy['archives']:
        path = group['narc']
        before = m.get_file(current, path)
        require_hash(before, group['current_archive_sha256'], path)
        old = m.Narc.parse(before)
        source = m.Narc.parse(m.get_file(donor, path)).files
        base = m.Narc.parse(m.get_file(baseline, path)).files
        new = list(old.files)
        for row in group['members']:
            i = row['member']
            require_hash(source[i], row['donor_sha256'], f'donor {path}#{i}')
            require_hash(base[i], row['baseline_sha256'], f'rc4 {path}#{i}')
            require_hash(old.files[i], row['current_sha256'], f'current {path}#{i}')
            gfx.validate_member_layout(old.files[i], source[i], f'{path}#{i}')
            new[i] = source[i]
        if group.get('rebase') == 'pokedex':
            original_files = m.Narc.parse(m.get_file(original, path)).files
            # Rebase only header/buttons; the selected ES type badges remain direct copies.
            retail_files = m.Narc.parse(m.get_file(retail, 'a/0/6/8')).files
            check_retail_dependencies(old.files, retail_files, [2])
            rebased = rebase_dex(original_files, base, source, old.files, retail_files)
            for i in (0, 1, 4, 5, 6, 7, 8, 9, 10, 11, 69, 70, 71):
                new[i] = rebased[i]
        if group.get('retail_members'):
            check_retail_dependencies(old.files, m.Narc.parse(m.get_file(retail, path)).files,
                                      group['retail_dependencies'])
        for row in group.get('retail_members', []):
            i = row['member']
            data = m.Narc.parse(m.get_file(retail, path)).files[i]
            require_hash(data, row['retail_sha256'], f'retail {path}#{i}')
            require_hash(old.files[i], row['current_sha256'], f'current {path}#{i}')
            gfx.validate_member_layout(old.files[i], data, f'retail {path}#{i}')
            new[i] = data
        for screen in group.get('additional_screens', []):
            s, gi = screen['screen'], screen['graphic']
            sc, prev = gfx.NSCR(new[s]), gfx.NSCR(old.files[s])
            # Conservative no-expansion check for unchanged consumers; not a runtime test.
            ceiling = max(e & 1023 for e in prev.ents)
            if max(e & 1023 for e in sc.ents) > ceiling:
                raise ValueError(f'{path}#{s}: screen exceeds baseline tile ceiling')
            gfx.validate_screen_tiles(sc, gfx.NCGR(new[gi]), 0, f'{path}#{s}')
        changed = []
        for i, (a, b) in enumerate(zip(old.files, new)):
            if a == b:
                continue
            gfx.validate_member_layout(a, b, f'{path}#{i}')
            planned.append(dict(narc=path, member=i, before_sha256=sha(a), after_sha256=sha(b), data=b))
            changed.append(i)
        evidence.append(dict(narc=path, before_sha256=sha(before), changed_members=changed,
                             dependencies='All other archive members are hash-guarded and preserved verbatim.'))
    code = gfx.CodeView(current)
    donor_code = gfx.CodeView(donor)
    baseline_code = gfx.CodeView(baseline)
    code_rows = []
    for row in policy['code_ranges']:
        name, off, size = row['file'], row['offset'], row['length']
        require_hash(baseline_code.get(name)[off:off+size], row['baseline_sha256'], f'rc4 {name}')
        before = code.get(name)[off:off+size]
        after = donor_code.get(name)[off:off+size]
        require_hash(before, row['current_sha256'], name)
        require_hash(after, row['donor_sha256'], f'donor {name}')
        if len(after) != size:
            raise ValueError('truncated code graphics')
        code_rows.append(dict(file=name, offset=off, length=size, before_sha256=sha(before),
                              after_sha256=sha(after), data=after))
    return planned, code_rows, evidence


def apply_prepared(get_file, set_file, code, stage, *, fallback_policy=None):
    """Future compiler hook: AFTER the ordinary graphics stage, before final verification.

    Checks every input and constructs/validates every result before any mutation.
    Does not save a ROM or modify unselected code/archive members.
    """
    stage = Path(stage)
    receipt = json.loads((stage / 'manifest.json').read_text())
    if receipt.get('schema') != 2 or receipt.get('locale') != 'es':
        raise ValueError('unsupported prepared graphics manifest; regenerate with explicit fallback policy')
    if not isinstance(receipt.get('fallbacks'), list) or receipt.get('fallback_policy') not in ('allow-listed', 'error'):
        raise ValueError('prepared graphics must declare their fallback policy and list')
    narcs, code_images = {}, {}
    for archive in receipt['archives']:
        data = get_file(archive['narc'])
        require_hash(data, archive['before_sha256'], archive['narc'])
        narcs[archive['narc']] = m.Narc.parse(data)
    def payload(row):
        path = (stage / row['asset']).resolve()
        if not path.is_relative_to(stage.resolve()):
            raise ValueError('asset escapes prepared directory')
        data = path.read_bytes()
        require_hash(data, row['after_sha256'], row['asset'])
        return data
    for row in receipt['members']:
        n = narcs[row['narc']]
        require_hash(n.files[row['member']], row['before_sha256'], row['narc'])
        data = payload(row)
        gfx.validate_member_layout(n.files[row['member']], data, row['narc'])
        n.files[row['member']] = data
    for row in receipt['code_ranges']:
        name, off, size = row['file'], row['offset'], row['length']
        data = code_images.setdefault(name, bytearray(code.get(name)))
        require_hash(data[off:off+size], row['before_sha256'], name)
        replacement = payload(row)
        if len(replacement) != size:
            raise ValueError('code graphics size changed')
        data[off:off+size] = replacement
    def merged(path):
        return narcs[path].build() if path in narcs else get_file(path)
    validate_fallbacks(receipt.get("fallbacks", []), merged,
                       fallback_policy or receipt.get("fallback_policy", "allow-listed"))
    gfx.check_layouts(merged, code)
    for rule in receipt.get('additional_screens', []):
        fs = narcs[rule['narc']].files
        sc = gfx.NSCR(fs[rule['screen']])
        if max(e & 1023 for e in sc.ents) > rule['baseline_tile_ceiling']:
            raise ValueError('screen exceeds validated baseline ceiling')
        gfx.validate_screen_tiles(sc, gfx.NCGR(fs[rule['graphic']]), 0, rule['narc'])
    # CodeView.set supports only uncompressed overlays; preflight before NARC mutation.
    if isinstance(code, gfx.CodeView):
        for name in code_images:
            if name != 'arm9' and code._ov(name).compressed:
                raise ValueError(f'{name}: compressed overlay is unsupported')
    for path, narc in narcs.items():
        set_file(path, narc.build())
    for name, data in code_images.items():
        code.set(name, bytes(data))
    return receipt


def prepare(args):
    policy = json.loads(args.policy.read_text())
    if policy.get('schema') != 1 or policy.get('locale') != 'es':
        raise ValueError('unsupported graphics selection policy')
    mode = args.fallback_policy or policy.get('fallback_policy', 'allow-listed')
    if mode == 'error' and policy.get('fallbacks'):
        validate_fallbacks(policy['fallbacks'], None, mode)
    paths = dict(cn=args.cn_rom, us=args.us_rom, donor=args.source_rom, baseline=args.baseline_rom, retail=args.spanish_rom)
    for key, path in paths.items():
        if file_sha(path) != policy['inputs'][key]['sha256']:
            raise ValueError(f'{key} ROM hash mismatch')
    out = args.out.resolve()
    if not out.is_relative_to((WORK / 'build').resolve()) and not out.is_relative_to((WORK / 'extract').resolve()):
        raise ValueError('output must be under ignored work/build or work/extract')
    if out.exists():
        raise ValueError('output exists; choose a fresh directory')
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent, prefix='.es-graphics-') as tmp:
        stage = Path(tmp)
        current = graphics_current(args.cn_rom, args.us_rom, stage / 'generated-en')
        original = m.load_rom(args.cn_rom)
        baseline, donor = m.load_rom(args.baseline_rom), m.load_rom(args.source_rom)
        members, codes, archives = plan(policy, original, baseline, donor, current, m.load_rom(args.spanish_rom))
        extra = []
        for group in policy['archives']:
            fs = m.Narc.parse(m.get_file(current, group['narc'])).files
            for screen in group.get('additional_screens', []):
                extra.append(dict(narc=group['narc'], **screen, baseline_tile_ceiling=max(e & 1023 for e in gfx.NSCR(fs[screen['screen']]).ents)))
        for index, row in enumerate(members + codes):
            row['asset'] = f'assets/{index:04d}.bin'
            p = stage / row['asset']; p.parent.mkdir(exist_ok=True)
            p.write_bytes(row.pop('data'))
        receipt = dict(schema=2, locale='es', policy_sha256=file_sha(args.policy),
                       fallback_policy=mode, fallbacks=policy.get('fallbacks', []),
                       known_fallbacks_remaining=bool(policy.get('fallbacks')),
                       inputs=policy['inputs'], members=members, code_ranges=codes, archives=archives,
                       additional_screens=extra, runtime_verified=False,
                       exclusions=policy['exclusions'], notes=policy['notes'])
        # Captures exact checkout recipes without treating them as a complete ROM build key.
        recipe_paths = [Path(__file__), WORK/'tools/gfx.py', WORK/'graphics/layout_checks.json']
        recipe_paths += sorted((WORK/'patches').glob('gfx-*/fix.toml'))
        receipt['recipe_hashes'] = {str(p.relative_to(WORK)):file_sha(p) for p in recipe_paths}
        (stage/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
        apply_prepared(lambda p:m.get_file(current,p),lambda p,b:m.set_file(current,p,b),gfx.CodeView(current),stage)
        for row in members:
            actual=m.Narc.parse(m.get_file(current,row['narc'])).files[row['member']]
            require_hash(actual,row['after_sha256'],'readback')
        for row in codes:
            actual=gfx.CodeView(current).get(row['file'])[row['offset']:row['offset']+row['length']]
            require_hash(actual,row['after_sha256'],'code readback')
        shutil.rmtree(stage/'generated-en')
        stage.rename(out)
    print(json.dumps(dict(output=str(out), members=len(members), archives=len(archives), code_ranges=len(codes), runtime_verified=False,
                          fallback_policy=mode, fallbacks=[dict(id=r['id'],label=r['label']) for r in policy.get('fallbacks',[])])))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['prepare'])
    parser.add_argument('--fallback-policy', choices=['allow-listed', 'error'],
                        help='allow only hash-checked listed gaps (default), or reject all fallbacks')
    parser.add_argument('--policy',type=Path,default=POLICY)
    for option in ('cn-rom','us-rom','source-rom','baseline-rom','spanish-rom','out'):
        parser.add_argument('--'+option,type=Path,required=True)
    prepare(parser.parse_args())


if __name__=='__main__':
    main()
