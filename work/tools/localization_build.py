#!/usr/bin/env python3
"""Plan and stage locale catalogues without invoking the ROM compiler.

Run from the repository root. Prepared workspaces are isolated below
work/build/locales/<locale>/<fingerprint>/ and are EN-shaped only at the
existing compiler boundary. Every target row must be current and reviewed;
there is no fallback to English or Chinese for a missing target.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import shutil
import tempfile
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[1]
WORK = ROOT / "work"
BUILD_ROOT = WORK / "build" / "locales"
sys.path.insert(0, str(TOOLS))

import localization as loc  # noqa: E402
import qa  # noqa: E402
import trainer_display  # noqa: E402

LOCALE_CODES = ("en", "fr", "it", "de", "es")
BUILD_INPUTS = (
    "work/tools/localization_build.py", "work/tools/localization.py", "work/tools/ws.py",
    "work/tools/trainer_display.py", "work/tools/artifact_check.py", "work/tools/text_speed_patch.py", "work/tools/qa.py", "work/tools/textmetrics.py", "work/tools/msgtool.py",
    "work/tools/build.py", "work/tools/gfx.py", "work/tools/asmpatch.py",
    "work/tools/narcpatch.py", "work/tools/fixes.py", "work/tools/qa_config.json",
)


class LocaleBuildError(ValueError):
    pass


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def locale_records(locale: str) -> dict[str, dict[str, Any]]:
    if locale == "en":
        raise LocaleBuildError("English is read from the legacy adapter and is not staged here")
    root = loc.locale_file(locale)
    records: dict[str, dict[str, Any]] = {}
    if not root.exists():
        return records
    for path in sorted(root.rglob("*.json")):
        # Only bank catalogue files belong to this index; locale resources live beside banks.
        if path.parent == root or "reference" in path.parts:
            continue
        data = loc.load(path)
        if not isinstance(data, dict) or not isinstance(data.get("strings"), list):
            raise LocaleBuildError(f"invalid target bank: {path}")
        for row in data["strings"]:
            if not isinstance(row, dict):
                raise LocaleBuildError(f"invalid target row in {path}")
            ref = row.get("ref")
            if ref in records:
                raise LocaleBuildError(f"duplicate locale record: {ref}")
            records[ref] = row
    return records


def target_snapshot(locale: str, records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    config_path = loc.LOCALES / locale / "locale.json"
    config = loc.load(config_path) if config_path.exists() else {}
    resource_files: dict[str, str] = {}
    for key in ("glossary", "voices", "decisions"):
        value = config.get(key)
        if isinstance(value, str):
            path = loc.locale_resource_path(locale, key)
            identity = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else f"locale-resource:{locale}/{value}"
            resource_files[identity] = file_hash(path) if path.is_file() else "missing"
    # Explicitly declared resource assets participate in the key whether ready or not.
    declared = config.get("build_resources", {})
    if isinstance(declared, dict):
        for name, item in sorted(declared.items()):
            for evidence in item.get("files", []) if isinstance(item, dict) else []:
                if not isinstance(evidence, dict) or not isinstance(evidence.get("path"), str):
                    continue
                base = (loc.LOCALES / locale).resolve()
                path = (base / evidence["path"]).resolve()
                if not path.is_relative_to(base):
                    raise LocaleBuildError(f"{locale} {name} resource path escapes its locale directory")
                identity = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else f"locale-resource:{locale}/{evidence['path']}"
                resource_files[identity] = file_hash(path) if path.is_file() else "missing"
    return {"config": config, "resources": resource_files,
            "records": {ref: records[ref] for ref in sorted(records)}}


def build_input_snapshot(locale: str, target: dict[str, Any], sources: dict[str, dict[str, Any]]) -> dict[str, Any]:
    inputs: dict[str, str] = {}
    for relative in BUILD_INPUTS:
        path = ROOT / relative
        inputs[relative] = file_hash(path) if path.is_file() else "missing"
    for directory in ("work/patches", "work/tools/charmaps", "work/fonts"):
        root = ROOT / directory
        for path in sorted(root.rglob("*")) if root.exists() else []:
            if path.is_file():
                inputs[str(path.relative_to(ROOT))] = file_hash(path)
    for path in sorted((ROOT / "work/tools").glob("charmap*.tsv")):
        inputs[str(path.relative_to(ROOT))] = file_hash(path)
    # Include existing generated/source graphic assets in the key. These are ignored
    # build inputs and are read only; no shared graphics generator is run here.
    graphics = ROOT / "work/graphics"
    if graphics.exists():
        for path in sorted(p for p in graphics.rglob("*") if p.is_file()):
            inputs[str(path.relative_to(ROOT))] = file_hash(path)
    source = {ref: {"source_sha256": row["source_sha256"],
                    "source_bank_sha256": row.get("source_bank_sha256")}
              for ref, row in sorted(sources.items())}
    return {"locale": locale, "source": source,
            "source_bank_inventory": getattr(sources, "bank_inventory", {}),
            "target": target, "inputs": inputs}


def structural_audit(locale: str, sources: dict[str, dict[str, Any]], records: dict[str, dict[str, Any]]) -> list[str]:
    problems: list[str] = []
    for ref, src in sources.items():
        narc, bank, _sid = loc.parse_ref(ref)
        if f"{narc}/{bank:04d}" in loc.PASSTHROUGH or not loc.is_required(src["text"]):
            continue
        row = records.get(ref)
        if not row or not isinstance(row.get("text"), str):
            continue
        findings = []
        qa.check_tags(src["text"], row["text"], lambda severity, code, detail, **kw: findings.append((severity, code, detail)))
        problems.extend(f"{ref}: {code}: {detail}" for severity, code, detail in findings if severity == "error")
    return problems


def blockers(locale: str, readiness: dict[str, Any], structural: list[str]) -> list[str]:
    out = []
    if readiness.get("missing_or_unreviewed"):
        out.append(f"{readiness['missing_or_unreviewed']} required rows are missing or unreviewed")
    if readiness.get("stale"):
        out.append(f"{readiness['stale']} rows have stale source hashes")
    if readiness.get("duplicate_refs"):
        out.append(f"{len(readiness['duplicate_refs'])} duplicate refs")
    if readiness.get("catalogue_errors"):
        out.extend(readiness["catalogue_errors"][:5])
    out.extend(structural[:10])
    if locale != "en":
        for name, state in readiness.get("resources", {}).items():
            if name != "decisions.jsonl" and state != "configured":
                out.append(f"{name} locale editorial resource is {state}")
        for name, state in readiness.get("build_resources", {}).items():
            if state != "integrated":
                out.append(f"{name} locale resource is {state}")
        out.append("encoding/glyph/buffer/pixel-fit QA is not implemented for target locales")
        out.append("locale compiler integration is not implemented")
    return out


def matrix(sources: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for locale in LOCALE_CODES:
        readiness = loc.readiness(locale, sources)
        records = loc.english_adapter(sources) if locale == "en" else locale_records(locale)
        audit = structural_audit(locale, sources, records) if locale != "en" else []
        # The existing English build remains its own default path.
        is_english = locale == "en"
        rows.append({"locale": locale, "coverage": loc.coverage(locale, sources),
                     "catalogue_ready": readiness.get("catalogue_ready", readiness["ready"]),
                     "build_ready": False,
                     "build_path": "legacy-default" if is_english else "locale-staging",
                     "build_resources": readiness.get("build_resources", {}),
                     "qa_scope": {"control_tags": "legacy English pipeline" if is_english else "locale-neutral structural check",
                                  "encoding_glyph_buffer_pixel_fit": "not evaluated by this matrix"},
                     "blockers": (["matrix does not verify the English build output; existing build QA/release gates apply"]
                                  if is_english else blockers(locale, readiness, audit))})
    return {"schema_version": 1, "locales": rows}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def prepared_banks(locale: str, sources: dict[str, dict[str, Any]],
                   records: dict[str, dict[str, Any]]) -> dict[tuple[str, int], dict[str, Any]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = {
        loc.parse_ref(ref + "#0")[:2]: [] for ref in getattr(sources, "bank_inventory", {})}
    for ref, src in sources.items():
        narc, bank, sid = loc.parse_ref(ref)
        passthrough = f"{narc}/{bank:04d}" in loc.PASSTHROUGH
        required = not passthrough and loc.is_required(src["text"])
        row = records.get(ref)
        if required and (row is None or row.get("status") != "reviewed" or row.get("source_sha256") != src["source_sha256"]):
            raise LocaleBuildError(f"cannot stage {locale}: target is missing, unreviewed, or stale at {ref}")
        text = row.get("text") if required else src["text"]
        if not isinstance(text, str):
            raise LocaleBuildError(f"cannot stage {locale}: target text is empty at {ref}")
        if not required and text != src["text"]:
            raise LocaleBuildError(f"cannot stage {locale}: nonlinguistic/passthrough row must be copied exactly at {ref}")
        findings = []
        if required:
            qa.check_tags(src["text"], text, lambda severity, code, detail, **kw: findings.append((severity, code, detail)))
        errors = [x for x in findings if x[0] == "error"]
        if errors:
            raise LocaleBuildError(f"structural QA failed at {ref}: {errors[0][1]}: {errors[0][2]}")
        origin = "copy" if not required else row.get("provenance", {}).get("kind", "locale")
        grouped.setdefault((narc, bank), []).append({"id": sid, "zh": src["text"], "en": text,
                                                       "status": "reviewed", "origin": origin,
                                                       "notes": ""})
    return {key: {"narc": key[0], "bank": key[1], "strings": sorted(rows, key=lambda x: x["id"])}
            for key, rows in grouped.items()}


def prepare(locale: str, sources: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if locale not in ("fr", "it", "de", "es"):
        raise LocaleBuildError("prepare supports target locales fr, it, de, es")
    readiness = loc.readiness(locale, sources)
    records = locale_records(locale)
    audit = structural_audit(locale, sources, records)
    # Preparation needs a complete reviewed catalogue. Locale resources separately
    # gate compilation, so reviewers can inspect a deterministic staged workspace.
    if (not readiness.get("catalogue_ready", readiness["ready"]) or audit):
        raise LocaleBuildError("catalogue is not stageable: " + "; ".join(blockers(locale, readiness, audit)[:10]))
    banks = prepared_banks(locale, sources, records)
    display_aliases = trainer_display.plan_rows(banks.get(("a027", 719), {}).get("strings", []))
    target = target_snapshot(locale, records)
    fingerprint = canonical_hash(build_input_snapshot(locale, target, sources))
    stage = BUILD_ROOT / locale / fingerprint
    loc.safe_build_output(stage)
    build_blockers = blockers(locale, readiness, audit)
    manifest = {"schema_version": 1, "locale": locale, "fingerprint": fingerprint,
                "workspace": "workspace", "catalogue_ready": True,
                "trainer_display": {"state": "planned" if display_aliases else "unused",
                                    "aliases": display_aliases, "alias_sha256": trainer_display.digest(display_aliases),
                                    "runtime_required": bool(display_aliases)},
                "compile_ready": False,
                "compile_blockers": build_blockers,
                "qa_scope": {"control_tags": "checked against source",
                             "encoding_glyph_buffer_pixel_fit": "not evaluated; locale assets/tooling are not integrated"},
                "prepared_banks": len(banks), "prepared_strings": sum(len(b["strings"]) for b in banks.values()),
                "source_catalogue_sha256": canonical_hash({r: s["source_sha256"] for r, s in sorted(sources.items())}),
                "target_catalogue_sha256": canonical_hash(target["records"]),
                "resource_states": readiness.get("build_resources", {}),
                "source_bank_inventory": getattr(sources, "bank_inventory", {}),
                "fingerprint_scope": "text staging inputs and enumerated resource snapshots; not a complete ROM build dependency key"}
    # Build an exact fresh tree; cached trees must match byte-for-byte and contain no extra files.
    stage.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".prepare-", dir=stage.parent))
    try:
        for (narc, bank), data in sorted(banks.items()):
            write_json(temporary / "workspace" / narc / f"{bank:04d}.json", data)
        manifest["files"] = {str(path.relative_to(temporary)): file_hash(path)
                             for path in sorted(temporary.rglob("*")) if path.is_file()}
        write_json(temporary / "manifest.json", manifest)
        if stage.exists():
            expected = {str(path.relative_to(temporary)): file_hash(path)
                        for path in temporary.rglob("*") if path.is_file()}
            existing = {}
            for path in stage.rglob("*"):
                if path.is_symlink():
                    raise LocaleBuildError(f"cached stage contains a symlink: {path}")
                if path.is_file():
                    existing[str(path.relative_to(stage))] = file_hash(path)
            if existing != expected:
                raise LocaleBuildError("cached stage differs from its fingerprint; remove the stale stage and prepare again")
        else:
            os.replace(temporary, stage)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return {"stage": str(stage.relative_to(ROOT)), "manifest": manifest}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("matrix", help="show coverage, readiness and blockers for each locale")
    p_prepare = sub.add_parser("prepare", help="strictly stage a complete locale catalogue for review")
    p_prepare.add_argument("locale", choices=("fr", "it", "de", "es"))
    args = parser.parse_args(argv)
    try:
        sources = loc.source_entries()
        result = matrix(sources) if args.command == "matrix" else prepare(args.locale, sources)
    except (LocaleBuildError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"localization build: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
