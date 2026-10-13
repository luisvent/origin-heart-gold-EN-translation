#!/usr/bin/env python3
"""Locale-neutral catalogue adapters and conservative reference import.

Run from the repository root. Source identity is always the Chinese narc/bank/id;
target text lives under work/translate/locales/<locale>/banks and is never written
back into the legacy English workspace.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import zh_redact

ROOT = Path(__file__).resolve().parents[2]
LOCALES = ROOT / "work/translate/locales"
SOURCE = ROOT / "work/extract/v4"
EN_BANKS = ROOT / "work/translate/banks"
ES_EXTRACT = ROOT / "work/extract/es-rc42"
STATUSES = ("todo", "imported", "draft", "reviewed")
LOCALE_CODES = ("en", "fr", "it", "de", "es")
CN_NARC_PATHS = {"a027": "a/0/2/7", "battle_string": "battle/string/battle_string.narc"}


class SourceCatalogue(dict):
    """Text records plus the verified inventory (including empty message banks)."""

    def __init__(self):
        super().__init__()
        self.bank_inventory = {}


def checked_locale_base(locale: str) -> Path:
    if locale not in LOCALE_CODES:
        raise ValueError(f"unsupported locale: {locale}")
    base = (LOCALES / locale).resolve()
    if not base.is_relative_to(LOCALES.resolve()):
        raise ValueError(f"{locale} directory escapes the locale root")
    return base


def locale_config(locale: str) -> dict[str, Any]:
    path = checked_locale_base(locale) / "locale.json"
    config = load(path) if path.exists() else {}
    if not isinstance(config, dict):
        raise ValueError(f"{locale} config must be an object")
    if config.get("locale", locale) != locale or config.get("catalogue_schema", 1) != 1:
        raise ValueError(f"{locale} config identity/schema mismatch")
    return config


def safe_build_output(path: Path) -> Path:
    """Never write through shared build-input symlinks in a worktree."""
    root = ROOT / "work/build"
    candidate = path.absolute()
    if ".." in candidate.parts or not candidate.is_relative_to(root):
        raise ValueError("game-text output must be under work/build/")
    for part in (candidate, *candidate.parents):
        if part == root.parent:
            break
        if part.is_symlink():
            raise ValueError(f"build output traverses a symlink: {part}")
    return candidate

REF_RE = re.compile(r"([a-zA-Z0-9_]+)/([0-9]{4})#([0-9]+)\Z")
PASSTHROUGH = {
    "a027/0793", "a027/0794", "a027/0795", "a027/0796", "a027/0797",
    "a027/0804", "a027/0805", "a027/0806", "a027/0807", "a027/0808", "a027/0809",
    "a027/0810", "a027/0811", "a027/0812", "a027/0813",
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def locale_resource_path(locale: str, key: str) -> Path:
    """Resolve a configured locale resource, rejecting paths outside its locale directory."""
    base = checked_locale_base(locale)
    config = locale_config(locale)
    value = config.get(key, "decisions.jsonl" if key == "decisions" else f"{key}.json")
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError(f"{locale} {key} path must be relative to its locale directory")
    path = (base / value).resolve()
    if not path.is_relative_to(base):
        raise ValueError(f"{locale} {key} path escapes its locale directory")
    return path


def ref_for(narc: str, bank: int, sid: int) -> str:
    return f"{narc}/{bank:04d}#{sid}"


def parse_ref(ref: str) -> tuple[str, int, int]:
    match = REF_RE.fullmatch(ref)
    if not match:
        raise ValueError(f"invalid text ref: {ref}")
    return match[1], int(match[2]), int(match[3])


def source_charmap():
    import msgtool

    return msgtool.Charmap.load([ROOT / "work/tools/charmap_en.tsv",
                                ROOT / "work/tools/charmaps/charmap_zh_xzonn_gen4.tsv"])


def text_rows(bank: Any, bank_no: int) -> list[dict[str, Any]]:
    if not isinstance(bank, dict) or bank.get("bank") != bank_no:
        raise ValueError(f"invalid source bank identity: {bank_no:04d}")
    if "raw_bank_hex" in bank or not isinstance(bank.get("strings"), list):
        raise ValueError(f"unsupported raw/nontext source bank: {bank_no:04d}; preserve and integrate it explicitly")
    rows = bank["strings"]
    if any(not isinstance(r, dict) or type(r.get("id")) is not int
           or r["id"] != i or not isinstance(r.get("text"), str) for i, r in enumerate(rows)):
        raise ValueError(f"invalid or nonsequential source rows: {bank_no:04d}")
    return rows


def source_entries(source_root: Path = SOURCE) -> dict[str, dict[str, Any]]:
    """Fail closed against the CN ROM for the default source; custom roots are test fixtures."""
    out = SourceCatalogue()
    verified_banks = {}
    if source_root.resolve() == SOURCE.resolve():
        import msgtool

        cn_rom = ROOT / "work/rom/origin_v4.0.3_cn.nds"
        if not cn_rom.is_file():
            raise ValueError("Chinese reference ROM is required to verify the default source inventory")
        manifest_path = ES_EXTRACT / "manifest.json"
        if manifest_path.exists():
            expected = load(manifest_path).get("source", {}).get("chinese_reference_sha256")
            if not expected or file_sha256(cn_rom) != expected:
                raise ValueError("Chinese reference ROM fingerprint differs from extraction provenance")
        cm = source_charmap()
        rom = msgtool.load_rom(str(cn_rom))
        for narc, narc_path in CN_NARC_PATHS.items():
            raw_narc = msgtool._msg_narc(rom, narc_path)
            expected_paths = {f"{i:04d}.json" for i in range(len(raw_narc.files))}
            found = {p.name for p in (source_root / narc).glob("[0-9]*.json")}
            if found != expected_paths:
                raise ValueError(f"incomplete Chinese source inventory: {narc}; "
                                 f"missing={sorted(expected_paths-found)[:10]}, extra={sorted(found-expected_paths)[:10]}")
            for bank_no, raw in enumerate(raw_narc.files):
                decoded = msgtool.bank_to_json(bank_no, raw, cm)
                decoded_rows = text_rows(decoded, bank_no)
                extracted = load(source_root / narc / f"{bank_no:04d}.json")
                extracted_rows = text_rows(extracted, bank_no)
                if decoded_rows != extracted_rows:
                    raise ValueError(f"Chinese extract is stale or edited: {narc}/{bank_no:04d}")
                verified_banks[f"{narc}/{bank_no:04d}"] = hashlib.sha256(raw).hexdigest()
    for narc_dir in sorted(p for p in source_root.iterdir() if p.is_dir()):
        paths = sorted(narc_dir.glob("[0-9]*.json"))
        if paths and verified_banks and narc_dir.name not in CN_NARC_PATHS:
            raise ValueError(f"unverified source NARC: {narc_dir.name}")
        for path in paths:
            if not re.fullmatch(r"[0-9]{4}\.json", path.name):
                raise ValueError(f"invalid source bank filename: {path.name}")
            bank_no = int(path.stem)
            rows = text_rows(load(path), bank_no)
            bank_ref = f"{narc_dir.name}/{bank_no:04d}"
            bank_sha = verified_banks.get(bank_ref, file_sha256(path))
            out.bank_inventory[bank_ref] = {"sha256": bank_sha, "strings": len(rows)}
            for row in rows:
                ref = ref_for(narc_dir.name, bank_no, row["id"])
                if ref in out:
                    raise ValueError(f"duplicate source ref: {ref}")
                out[ref] = {"text": row["text"], "source_sha256": sha256_text(row["text"]),
                            "source_bank_sha256": bank_sha,
                            "source_path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)}
    if not out:
        raise ValueError("source catalogue is empty")
    return out


def locale_file(locale: str) -> Path:
    return locale_resource_path(locale, "target_bank_dir") if "target_bank_dir" in locale_config(locale) else checked_locale_base(locale) / "banks"


def bank_path(locale: str, narc: str, bank: int) -> Path:
    if not re.fullmatch(r"[a-zA-Z0-9_]+", narc) or type(bank) is not int or not 0 <= bank <= 9999:
        raise ValueError("invalid bank identity")
    root = locale_file(locale)
    path = root / narc / f"{bank:04d}.json"
    if not path.resolve().is_relative_to(checked_locale_base(locale)):
        raise ValueError("catalogue bank path escapes locale directory")
    return path

def load_locale_bank(locale: str, narc: str, bank: int) -> dict[str, Any] | None:
    path = bank_path(locale, narc, bank)
    return load(path) if path.exists() else None


def index_records(bank: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    if not isinstance(bank, dict) or not isinstance(bank.get("strings"), list):
        raise ValueError("locale bank must be an object with a strings array")
    for row in bank["strings"]:
        ref = row.get("ref") if isinstance(row, dict) else None
        if not isinstance(ref, str) or ref in out:
            raise ValueError(f"duplicate or invalid locale ref: {ref}")
        parse_ref(ref)
        out[ref] = row
    return out


def empty_locale_bank(locale: str, narc: str, bank: int, source_hash: str | None = None) -> dict[str, Any]:
    return {"schema_version": 1, "locale": locale, "narc": narc, "bank": bank,
            "source_bank_sha256": source_hash, "strings": []}


def init_target(locale: str, sources: dict[str, dict[str, Any]], *, exclude_passthrough: bool = True) -> dict[str, int]:
    """Create todo records while preserving existing local text and review fields."""
    if locale == "en":
        raise ValueError("English is an adapter over legacy banks; it is not initialized here")
    grouped: dict[tuple[str, int], list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for ref, src in sources.items():
        narc, bank, _ = parse_ref(ref)
        if exclude_passthrough and f"{narc}/{bank:04d}" in PASSTHROUGH:
            continue
        grouped[(narc, bank)].append((ref, src))
    counts = Counter()
    for (narc, bank), entries in grouped.items():
        path = bank_path(locale, narc, bank)
        old = load(path) if path.exists() else empty_locale_bank(locale, narc, bank)
        if (old.get("schema_version"), old.get("locale"), old.get("narc"), old.get("bank")) != (1, locale, narc, bank):
            raise ValueError(f"existing locale bank identity/schema mismatch: {path}")
        rows = index_records(old)
        if any(parse_ref(ref)[:2] != (narc, bank) for ref in rows):
            raise ValueError(f"existing locale record is stored in the wrong bank: {path}")
        for ref, src in entries:
            current = rows.get(ref)
            if current is None:
                current = {"ref": ref, "source_sha256": src["source_sha256"], "text": None,
                           "status": "todo", "provenance": {"kind": "source_only"},
                           "alignment": {"state": "direct_source_ref"}}
                rows[ref] = current
                counts["created"] += 1
            elif current.get("source_sha256") != src["source_sha256"]:
                current["staleness"] = {"state": "stale", "current_source_sha256": src["source_sha256"]}
                counts["stale"] += 1
            else:
                counts["preserved"] += 1
        old["schema_version"] = 1
        old["locale"] = locale
        old["narc"] = narc
        old["bank"] = bank
        old["source_bank_sha256"] = entries[0][1]["source_bank_sha256"]
        old["strings"] = sorted(rows.values(), key=lambda r: parse_ref(r["ref"])[2])
        atomic_json(path, old)
        counts["banks"] += 1
    return dict(counts)


def english_adapter(sources: dict[str, dict[str, Any]], en_root: Path = EN_BANKS) -> dict[str, dict[str, Any]]:
    """Read legacy EN bank rows as normalized target records; never write them."""
    result = {}
    grouped: dict[tuple[str, int], list[tuple[str, dict[str, Any], int]]] = defaultdict(list)
    for ref, src in sources.items():
        narc, bank, sid = parse_ref(ref)
        grouped[(narc, bank)].append((ref, src, sid))
    for (narc, bank), refs in grouped.items():
        path = en_root / narc / f"{bank:04d}.json"
        rows = {r.get("id"): r for r in load(path).get("strings", [])} if path.exists() else {}
        for ref, src, sid in refs:
            row = rows.get(sid)
            result[ref] = {"ref": ref, "source_sha256": src["source_sha256"],
                           "text": row.get("en") if row else None,
                           "status": row.get("status", "todo") if row else "todo",
                           "provenance": {"kind": row.get("origin") or "legacy_en"} if row else {"kind": "missing"},
                           "alignment": {"state": "direct_source_ref"},
                           "source_state": "current" if not row or zh_redact.matches(row.get("zh"), src["text"]) else "stale"}
    return result


def english_bank_adapter(refs: list[str], sources: dict[str, dict[str, Any]], en_root: Path = EN_BANKS) -> dict[str, dict[str, Any]]:
    """Read one legacy bank for bounded context; avoids loading the full catalogue."""
    if not refs:
        return {}
    narc, bank, _ = parse_ref(refs[0])
    path = en_root / narc / f"{bank:04d}.json"
    rows = {r.get("id"): r for r in load(path).get("strings", [])} if path.exists() else {}
    out = {}
    for ref in refs:
        rnarc, rbank, sid = parse_ref(ref)
        if (rnarc, rbank) != (narc, bank) or ref not in sources:
            continue
        row = rows.get(sid)
        out[ref] = {"ref": ref, "source_sha256": sources[ref]["source_sha256"],
                    "text": row.get("en") if row else None,
                    "status": row.get("status", "todo") if row else "todo",
                    "provenance": {"kind": row.get("origin") or "legacy_en"} if row else {"kind": "missing"},
                    "alignment": {"state": "direct_source_ref"},
                    "source_state": "current" if not row or zh_redact.matches(row.get("zh"), sources[ref]["text"]) else "stale"}
    return out


def es_mappings(extract_root: Path = ES_EXTRACT) -> list[dict[str, Any]]:
    path = extract_root / "mappings.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def control_signature(text: str) -> list[list[Any]]:
    text = re.sub(r"\{VAR:FF00:[^}]*\}", "", text, flags=re.IGNORECASE)
    token = re.compile(r"\{(?:VAR:([0-9A-Fa-f]{4}):([^}]*)|([A-Z]+))\}")
    result = []
    for match in token.finditer(text):
        if match.group(1):
            argc = len(match.group(2).split(",")) if match.group(2) else 0
            result.append(["VAR", match.group(1).upper(), argc])
        else:
            result.append(["TAG", match.group(3)])
    return result


def import_es(sources: dict[str, dict[str, Any]], *, extract_root: Path = ES_EXTRACT) -> dict[str, int]:
    """Import unique equal-count candidates as imported; quarantine every uncertain row."""
    rows = es_mappings(extract_root)
    for row in rows:
        if (not isinstance(row, dict) or not isinstance(row.get("narc"), str)
                or not re.fullmatch(r"[a-zA-Z0-9_]+", row["narc"])
                or type(row.get("es_bank")) is not int or not 0 <= row["es_bank"] <= 9999
                or type(row.get("es_id")) is not int or row["es_id"] < 0
                or not isinstance(row.get("es_text"), str)
                or (row.get("cn_bank") is not None and (type(row["cn_bank"]) is not int or not 0 <= row["cn_bank"] <= 9999))
                or not isinstance(row.get("cn_candidate_ids"), list)
                or any(type(i) is not int or i < 0 for i in row["cn_candidate_ids"])):
            raise ValueError("malformed Spanish mapping row")
    reference_hashes = {}
    manifest_path = extract_root / "manifest.json"
    if manifest_path.exists():
        manifest = load(manifest_path)
        for narc, summary in manifest.get("summary", {}).items():
            for item in summary.get("banks", []):
                reference_hashes[(narc, item["bank"])] = item["es_member_sha256"]
        if not reference_hashes:
            raise ValueError("Spanish extraction manifest has no bank provenance")
        if extract_root.resolve() == ES_EXTRACT.resolve():
            es_rom = extract_root / "origin_v4.0.3_es_rc42.nds"
            expected = manifest.get("source", {}).get("reconstructed_es_rom_sha256")
            if not es_rom.is_file() or file_sha256(es_rom) != expected:
                raise ValueError("Spanish reference ROM fingerprint differs from extraction provenance")
            import msgtool

            rom = msgtool.load_rom(str(es_rom))
            for narc, narc_path in CN_NARC_PATHS.items():
                raw_narc = msgtool._msg_narc(rom, narc_path)
                for bank_no, raw in enumerate(raw_narc.files):
                    if reference_hashes.get((narc, bank_no)) != hashlib.sha256(raw).hexdigest():
                        raise ValueError(f"Spanish manifest bank differs from reference ROM: {narc}/{bank_no:04d}")
    elif extract_root.resolve() == ES_EXTRACT.resolve() and extract_root.resolve() == (ROOT / "work/extract/es-rc42").resolve():
        raise ValueError("Spanish extraction manifest is required for the default reference")
    source_counts = Counter((parse_ref(ref)[0], parse_ref(ref)[1]) for ref in sources)
    es_banks: dict[tuple[str, int], dict[str, Any] | None] = {}
    cm = source_charmap()

    def es_bank(narc: str, bank: int) -> dict[str, Any] | None:
        key = (narc, bank)
        if key in es_banks:
            return es_banks[key]
        raw_path = extract_root / "raw" / narc / f"{bank:04d}.bin"
        json_path = extract_root / narc / f"{bank:04d}.json"
        if not raw_path.exists() or not json_path.exists():
            es_banks[key] = None
            return None
        import msgtool

        data = load(json_path)
        try:
            decoded = msgtool.bank_to_json(bank, raw_path.read_bytes(), cm)
            decoded_rows = text_rows(decoded, bank)
            rows = text_rows(data, bank)
            verified = decoded_rows == rows
        except (ValueError, IndexError, TypeError):
            verified = False
            rows = []
        entries = {str(row["id"]): row["text"] for row in rows}
        es_banks[key] = {"sha256": file_sha256(raw_path), "entries": entries, "count": len(entries),
                         "bank": data.get("bank") if isinstance(data, dict) else None,
                         "decoded_verified": verified}
        return es_banks[key]

    def candidate_ref(row: dict[str, Any]) -> str | None:
        ids = row.get("cn_candidate_ids")
        if row.get("cn_bank") is None or not isinstance(ids, list) or len(ids) != 1:
            return None
        return ref_for(row["narc"], int(row["cn_bank"]), int(ids[0]))

    def invalid_reason(row: dict[str, Any], ref: str | None) -> str | None:
        if (row.get("mapping_status") != "candidate_same_index_equal_count_unreviewed"
                or row.get("bank_counts_equal") is not True
                or row.get("control_signature_compatible") is not True
                or ref is None
                or row.get("es_bank") != row.get("cn_bank")
                or int(row.get("es_id", -1)) != parse_ref(ref)[2]):
            return "ambiguous_or_expanded_bank_mapping"
        es = es_bank(row["narc"], int(row["es_bank"]))
        if es is None:
            return "missing_es_source_bank"
        if reference_hashes and reference_hashes.get((row["narc"], int(row["es_bank"]))) != es["sha256"]:
            return "stale_or_mismatched_es_manifest_fingerprint"
        if not es["decoded_verified"]:
            return "stale_or_mismatched_es_decoded_bank"
        if es["bank"] != int(row["es_bank"]) or es["sha256"] != row.get("es_bank_sha256"):
            return "stale_or_mismatched_es_bank_fingerprint"
        if es["count"] != source_counts[(row["narc"], int(row["cn_bank"]))]:
            return "expanded_or_mismatched_bank_count"
        if es["entries"].get(str(row["es_id"])) != row.get("es_text"):
            return "stale_or_mismatched_es_text"
        if ref not in sources:
            return "unknown_source_ref"
        if row.get("cn_bank_sha256") != sources[ref]["source_bank_sha256"]:
            return "stale_or_mismatched_cn_bank_fingerprint"
        signature = control_signature(row.get("es_text", ""))
        if (signature != control_signature(sources[ref]["text"])
                or signature != row.get("control_signature")):
            return "control_signature_mismatch"
        return None

    candidates: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        ref = candidate_ref(row)
        if not invalid_reason(row, ref) and ref:
            candidates[ref].append(row)
    usable: dict[str, dict[str, Any]] = {}
    quarantined: list[dict[str, Any]] = []
    counts = Counter()
    for row in rows:
        ref = candidate_ref(row)
        reason = invalid_reason(row, ref)
        if reason is None and ref not in candidates:
            reason = "ambiguous_or_expanded_bank_mapping"
        elif reason is None and len(candidates[ref]) != 1:
            reason = "conflicting_es_candidates_for_source_ref"
        if reason:
            quarantined.append({"locale": "es", "es_ref": ref_for(row["narc"], int(row["es_bank"]), int(row["es_id"])),
                                "cn_candidate_refs": [ref_for(row["narc"], int(row["cn_bank"]), int(i)) for i in row.get("cn_candidate_ids", [])] if row.get("cn_bank") is not None else [],
                                "reason": reason, "mapping_status": row.get("mapping_status"),
                                "review_status": row.get("review_status"), "source_mapping": row})
            counts["quarantined"] += 1
            continue
        assert ref is not None
        usable[ref] = row
    grouped: dict[tuple[str, int], list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for ref, row in usable.items():
        narc, bank, _ = parse_ref(ref)
        grouped[(narc, bank)].append((ref, row))
    for (narc, bank), entries in grouped.items():
        path = bank_path("es", narc, bank)
        old = load(path) if path.exists() else empty_locale_bank("es", narc, bank)
        if (old.get("schema_version"), old.get("locale"), old.get("narc"), old.get("bank")) != (1, "es", narc, bank):
            raise ValueError(f"existing Spanish bank identity/schema mismatch: {path}")
        record_map = index_records(old)
        if any(parse_ref(ref)[:2] != (narc, bank) for ref in record_map):
            raise ValueError(f"existing Spanish record is stored in the wrong bank: {path}")
        for ref, row in entries:
            src = sources[ref]
            previous = record_map.get(ref)
            if previous:
                if previous.get("source_sha256") != src["source_sha256"]:
                    previous["staleness"] = {"state": "stale", "current_source_sha256": src["source_sha256"]}
                    counts["stale_preserved"] += 1
                elif previous.get("status") == "todo" and previous.get("text") is None:
                    # `init-target es` may have created an empty shell; the reference is still useful.
                    replacement = imported_record(ref, row, src, extract_root=extract_root)
                    for key in previous.keys() - replacement.keys():
                        replacement[key] = previous[key]
                    record_map[ref] = replacement
                    counts["filled_todo"] += 1
                else:
                    counts["existing_preserved"] += 1
                continue
            record_map[ref] = imported_record(ref, row, src, extract_root=extract_root)
            counts["imported"] += 1
        old.update(schema_version=1, locale="es", narc=narc, bank=bank,
                   source_bank_sha256=entries[0][1]["cn_bank_sha256"],
                   strings=sorted(record_map.values(), key=lambda r: parse_ref(r["ref"])[2]))
        atomic_json(path, old)
        counts["banks_written"] += 1
    quarantine_path = LOCALES / "es/reference/quarantine.jsonl"
    quarantine_path.parent.mkdir(parents=True, exist_ok=True)
    # Preserve reviewed/local quarantine annotations when regenerating, keyed by ES ref.
    prior = {}
    if quarantine_path.exists():
        prior = {r.get("es_ref"): r for r in (json.loads(x) for x in quarantine_path.read_text().splitlines() if x.strip())}
    for q in quarantined:
        old_q = prior.get(q["es_ref"])
        if old_q:
            for key in ("review", "notes", "decision"):
                if key in old_q:
                    q[key] = old_q[key]
    tmp = quarantine_path.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(q, ensure_ascii=False) + "\n" for q in quarantined), encoding="utf-8")
    os.replace(tmp, quarantine_path)
    counts["quarantine_file_rows"] = len(quarantined)
    return dict(counts)


def imported_record(ref: str, row: dict[str, Any], src: dict[str, Any], *, extract_root: Path = ES_EXTRACT) -> dict[str, Any]:
    return {"ref": ref, "source_sha256": src["source_sha256"], "text": row["es_text"], "status": "imported",
            "provenance": {"kind": "third_party_es_reference", "extract": str(extract_root.relative_to(ROOT)) if extract_root.is_relative_to(ROOT) else str(extract_root),
                           "raw_decode_verified": True,
                           "es_ref": ref_for(row["narc"], int(row["es_bank"]), int(row["es_id"])),
                           "es_bank_sha256": row["es_bank_sha256"]},
            "alignment": {"state": "unreviewed_same_index_equal_count_candidate", "confidence": "low",
                          "basis": row.get("candidate_basis")}}


def is_required(source_text: str) -> bool:
    """CJK/full-width source or Latin prose requires a target decision; symbols alone do not."""
    visible = re.sub(r"\{[^}]*\}", "", source_text)
    if re.search(r"[\u3400-\u9fff\uf900-\ufaff\u3040-\u30ff]", visible):
        return True
    if re.search(r"[\uff10-\uff19\uff21-\uff3a\uff41-\uff5a]", visible):
        return True
    return bool(re.search(r"[A-Za-z]{2,}", visible))


def coverage(locale: str, sources: dict[str, dict[str, Any]], *, en_root: Path = EN_BANKS) -> dict[str, int]:
    records = english_adapter(sources, en_root) if locale == "en" else {}
    if locale != "en":
        banks = {(parse_ref(ref)[0], parse_ref(ref)[1]) for ref in sources}
        for narc, bank in banks:
            try:
                data = load_locale_bank(locale, narc, bank)
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict) and isinstance(data.get("strings"), list):
                for row in data["strings"]:
                    ref = row.get("ref") if isinstance(row, dict) else None
                    if isinstance(ref, str):
                        records.setdefault(ref, row)
    counts = Counter()
    for ref, src in sources.items():
        narc, bank, _ = parse_ref(ref)
        if f"{narc}/{bank:04d}" in PASSTHROUGH:
            counts["passthrough_excluded"] += 1
            continue
        if not is_required(src["text"]):
            counts["nonprose_or_punctuation"] += 1
            continue
        counts["required"] += 1
        record = records.get(ref)
        state = record.get("status", "todo") if record else "todo"
        counts[state if state in STATUSES else "other"] += 1
        if record and (record.get("source_sha256") != src["source_sha256"] or record.get("source_state") == "stale"):
            counts["stale"] += 1
    return dict(counts)


def readiness(locale: str, sources: dict[str, dict[str, Any]], *, en_root: Path = EN_BANKS) -> dict[str, Any]:
    """Strict build-planning summary. Imported/draft rows are not build-ready."""
    checked_locale_base(locale)
    stats = coverage(locale, sources, en_root=en_root)
    missing = []
    stale = []
    duplicates = []
    catalogue_errors = [] if sources else ["source catalogue is empty"]
    records = english_adapter(sources, en_root) if locale == "en" else {}
    if locale != "en":
        seen: set[str] = set()
        root = locale_file(locale)
        for path in sorted(root.rglob("*.json")) if root.exists() else []:
            try:
                data = load(path)
            except (OSError, json.JSONDecodeError) as exc:
                catalogue_errors.append(f"invalid JSON {path.relative_to(root)}: {exc}")
                continue
            relative = path.relative_to(root)
            if not path.resolve().is_relative_to(checked_locale_base(locale)):
                catalogue_errors.append(f"catalogue path escapes locale directory: {relative}")
                continue
            if len(relative.parts) != 2 or not re.fullmatch(r"[0-9]{4}", relative.stem):
                catalogue_errors.append(f"unexpected catalogue path: {relative}")
                continue
            expected_narc, expected_bank = relative.parts[0], int(relative.stem)
            if not isinstance(data, dict):
                catalogue_errors.append(f"bank must be an object: {relative}")
                continue
            if data.get("schema_version") != 1:
                catalogue_errors.append(f"unsupported catalogue schema: {relative}")
            if (data.get("locale"), data.get("narc"), data.get("bank")) != (locale, expected_narc, expected_bank):
                catalogue_errors.append(f"catalogue metadata mismatch: {relative}")
            if not isinstance(data.get("strings"), list):
                catalogue_errors.append(f"missing strings array: {relative}")
                continue
            for row in data["strings"]:
                ref = row.get("ref") if isinstance(row, dict) else None
                try:
                    narc, bank, _ = parse_ref(ref)
                except (TypeError, ValueError):
                    catalogue_errors.append(f"invalid ref in {relative}: {ref!r}")
                    continue
                if (narc, bank) != (expected_narc, expected_bank):
                    catalogue_errors.append(f"ref stored in wrong bank: {ref} in {relative}")
                if ref not in sources:
                    catalogue_errors.append(f"unknown source ref: {ref}")
                if ref in seen:
                    duplicates.append(ref)
                seen.add(ref)
                status = row.get("status")
                if status not in STATUSES:
                    catalogue_errors.append(f"invalid record status: {ref}")
                if (not isinstance(row.get("source_sha256"), str)
                        or not re.fullmatch(r"[a-f0-9]{64}", row["source_sha256"])):
                    catalogue_errors.append(f"invalid source hash: {ref}")
                if row.get("text") is not None and not isinstance(row.get("text"), str):
                    catalogue_errors.append(f"non-string target text: {ref}")
                if status == "todo" and row.get("text") is not None:
                    catalogue_errors.append(f"todo record has target text: {ref}")
                for field in ("provenance", "alignment"):
                    if not isinstance(row.get(field), dict):
                        catalogue_errors.append(f"invalid {field}: {ref}")
                if (isinstance(row.get("alignment"), dict)
                        and row["alignment"].get("state") not in ("direct_source_ref", "unreviewed_same_index_equal_count_candidate", "reviewed", "verified")):
                    catalogue_errors.append(f"invalid alignment state: {ref}")
                if "staleness" in row and not isinstance(row["staleness"], dict):
                    catalogue_errors.append(f"invalid staleness: {ref}")
                records[ref] = row
    for ref, src in sources.items():
        narc, bank, _ = parse_ref(ref)
        if f"{narc}/{bank:04d}" in PASSTHROUGH or not is_required(src["text"]):
            continue
        row = records.get(ref)
        if row is None or row.get("text") is None:
            missing.append(ref)
        elif (row.get("source_sha256") != src["source_sha256"] or row.get("source_state") == "stale"
              or not isinstance(row.get("staleness", {}), dict)
              or row.get("staleness", {}).get("state") == "stale"):
            stale.append(ref)
        elif row.get("status") != "reviewed" or not isinstance(row.get("text"), str) or not row.get("text").strip():
            missing.append(ref)
        elif (not isinstance(row.get("alignment"), dict) or row["alignment"].get("state") not in ("reviewed", "verified", "direct_source_ref")):
            catalogue_errors.append(f"unverified alignment for reviewed record: {ref}")
    base = LOCALES / locale
    resources = {}
    for key, name in (("glossary", "glossary.json"), ("voices", "voices.json"), ("decisions", "decisions.jsonl")):
        path = locale_resource_path(locale, key)
        if not path.exists():
            resources[name] = "missing"
        elif name == "decisions.jsonl":
            try:
                decisions = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
                resources[name] = "present" if all(isinstance(d, dict) for d in decisions) else "invalid"
            except (OSError, json.JSONDecodeError):
                resources[name] = "invalid"
        else:
            content = load(path)
            valid = isinstance(content, dict) and all(isinstance(k, str) and k.strip()
                and isinstance(v, str) and v.strip() for k, v in content.items())
            resources[name] = "configured" if valid and content else "empty" if valid else "invalid"
    # Non-English target resources have separate readiness from editorial glossaries.
    # A non-empty glossary cannot establish that graphics, code strings, fonts, or
    # grammar-sensitive UI were reviewed and integrated for that locale.
    asset_resources = {}
    if locale == "en":
        for name in ("graphics", "hardcoded_strings", "font", "grammar_audit"):
            asset_resources[name] = "integrated"
    else:
        config_path = base / "locale.json"
        config = load(config_path) if config_path.exists() else {}
        declared = config.get("build_resources", {}) if isinstance(config, dict) else {}
        for name in ("graphics", "hardcoded_strings", "font", "grammar_audit"):
            item = declared.get(name, {}) if isinstance(declared, dict) else {}
            state = item.get("state", "unverified") if isinstance(item, dict) else "unverified"
            files = item.get("files", []) if isinstance(item, dict) else []
            valid_files = isinstance(files, list) and bool(files)
            for evidence in files if isinstance(files, list) else []:
                if not isinstance(evidence, dict) or not isinstance(evidence.get("path"), str) or not isinstance(evidence.get("sha256"), str):
                    valid_files = False
                    break
                asset_path = (base / evidence["path"]).resolve()
                if (not asset_path.is_relative_to(base.resolve()) or not asset_path.is_file()
                        or file_sha256(asset_path) != evidence["sha256"]):
                    valid_files = False
                    break
            asset_resources[name] = "integrated" if state == "integrated" and valid_files else "unverified"
    resources_ready = (all(resources.get(k) == "configured" for k in ("glossary.json", "voices.json"))
                       and resources.get("decisions.jsonl") == "present")
    assets_ready = all(state == "integrated" for state in asset_resources.values())
    if locale != "en":
        resources_ready = resources_ready and assets_ready
    return {"locale": locale, "required": stats.get("required", 0), "missing_or_unreviewed": len(missing),
            "stale": len(stale), "duplicate_refs": sorted(set(duplicates)),
            "catalogue_errors": catalogue_errors, "resources": resources,
            "build_resources": asset_resources, "resources_ready": resources_ready,
            "catalogue_ready": not missing and not stale and not duplicates and not catalogue_errors,
            "ready": not missing and not stale and not duplicates and not catalogue_errors and resources_ready,
            "examples": {"missing_or_unreviewed": missing[:20], "stale": stale[:20]}}


def context_package(ref: str, sources: dict[str, dict[str, Any]], locale: str = "en", *, neighbors: int = 2,
                    en_root: Path = EN_BANKS) -> dict[str, Any]:
    """Bounded physical-neighbour package. Stored order is explicitly not script order."""
    narc, bank, sid = parse_ref(ref)
    if ref not in sources:
        raise ValueError(f"unknown text ref: {ref}")
    checked_locale_base(locale)
    if not 0 <= neighbors <= 10:
        raise ValueError("neighbors must be from 0 to 10")
    refs = sorted((r for r in sources if parse_ref(r)[:2] == (narc, bank)), key=lambda r: parse_ref(r)[2])
    pos = refs.index(ref)
    picked = refs[max(0, pos-neighbors):pos+neighbors+1]
    en = english_bank_adapter(picked, sources, en_root)
    target = en if locale == "en" else {}
    if locale != "en":
        data = load_locale_bank(locale, narc, bank)
        target = index_records(data) if data else {}
    glossary_path = locale_resource_path(locale, "glossary")
    glossary = load(glossary_path) if glossary_path.exists() else {}
    if not isinstance(glossary, dict):
        raise ValueError("locale glossary must be an object")
    voices_path = locale_resource_path(locale, "voices")
    voices = load(voices_path) if voices_path.exists() else {}
    if not isinstance(voices, dict):
        raise ValueError("locale voices must be an object")
    legacy_path = en_root / narc / f"{bank:04d}.json"
    legacy = load(legacy_path).get("strings", []) if legacy_path.exists() else []
    redacted = {ref_for(narc, bank, r["id"]) for r in legacy if zh_redact.is_marker(r.get("zh"))}
    hidden = "[song lyrics withheld; substitute a hum or description; D-0368]"
    def source_context(r):
        return hidden if r in redacted else sources[r]["text"]
    def target_context(r, record):
        return dict(record, text=hidden, content_decision="D-0368") if r in redacted and record else record
    en = {r: target_context(r, row) for r, row in en.items()}
    target = {r: target_context(r, row) for r, row in target.items()}
    text = source_context(ref)
    terms = {term: value for term, value in glossary.items() if term and term in text}
    uncertainty_rows = []
    locale_decision_rows = []
    decision_path = locale_resource_path(locale, "decisions")
    if decision_path.exists():
        for line in decision_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            decision = json.loads(line)
            refs = decision.get("refs", [])
            relevant = ref in refs or decision.get("scope") == "global"
            compact = {key: decision[key] for key in ("id", "type", "status", "issue", "question", "en", "refs") if key in decision}
            if relevant:
                locale_decision_rows.append(compact)
                if decision.get("type") == "question" or decision.get("status") in ("open", "needs-review"):
                    uncertainty_rows.append(compact)
    scene_excerpt = None
    scene_state = "unavailable"
    scene_error = None
    try:
        import scene

        # Scene indexes are shared read-only inputs in some worktrees. Keep any
        # missing/stale cache rebuild inside mutable locale build output.
        scene_cache = safe_build_output(ROOT / "work/build/locales/scene-context-cache.json")
        cache = scene.load_cache(path=scene_cache)
        scene_excerpt = scene.show(cache, ref, window=2, show_en=True, max_scenes=2)
        for r in redacted:
            if r in sources:
                scene_excerpt = scene_excerpt.replace(sources[r]["text"], hidden)
        scene_state = "no_script_path" if "no script path found" in scene_excerpt else "available"
    except (Exception, SystemExit) as exc:
        scene_error = str(exc) or type(exc).__name__
    evidence_refs = set(re.findall(r"(?:a027/)?([0-9]{4}#[0-9]+)", scene_excerpt or ""))
    scene_refs = sorted({f"{narc}/{item}" for item in evidence_refs})
    relevant_voices = {key: value for key, value in voices.items() if key and key in (scene_excerpt or "")}
    return {"schema_version": 1, "ref": ref, "locale": locale,
            "source": {"text": text, "sha256": sources[ref]["source_sha256"]},
            "translation_policy": {
                "source_fidelity": "Match the Chinese source and preserve ambiguity; record suspected hack errors instead of silently correcting them.",
                "tone": "D-0627: preserve the source strength of swearing, insults, innuendo, sex, violence, dark and political jokes, including adult (21+) content. Do not sanitise or add crudeness.",
                "tone_word_choices": "D-2081: choose tone words for the individual line, scene and speaker; precedents are not global rules.",
                "lyrics": "D-0368: replace song lyrics with a hum or description and record the substitution."},
            "content_decision": "D-0368" if ref in redacted else None,
            "target": target.get(ref), "english_reference": en.get(ref),
            "locale_terms": terms,
            "uncertainty": {"state": "open" if uncertainty_rows else "none recorded for this locale/ref",
                            "items": uncertainty_rows[:20], "total": len(uncertainty_rows),
                            "omitted": max(0, len(uncertainty_rows)-20)},
            "locale_resources": {"glossary_path": str(glossary_path.relative_to(ROOT)) if glossary_path.is_relative_to(ROOT) else str(glossary_path),
                                 "voice_path": str(voices_path.relative_to(ROOT)) if voices_path.is_relative_to(ROOT) else str(voices_path),
                                 "decision_path": str(decision_path.relative_to(ROOT)) if decision_path.is_relative_to(ROOT) else str(decision_path),
                                 "voice_state": "configured" if voices else "empty",
                                 "relevant_voices": relevant_voices,
                                 "relevant_decisions": locale_decision_rows[:20],
                                 "decision_total": len(locale_decision_rows),
                                 "decisions_omitted": max(0, len(locale_decision_rows)-20)},
            "needs_context": True,
            "context_review_required": True,
            "unresolved_context": {"speaker": scene_state == "no_script_path" or scene_state == "unavailable",
                                   "branch": scene_state == "no_script_path" or scene_state == "unavailable",
                                   "script_order": scene_state == "no_script_path" or scene_state == "unavailable"},
            "context_warnings": ["Bounded physical bank neighbours are not script order.",
                                 "Review speaker, branch and script context before target text can be considered reviewed."],
            "scene_evidence": {"state": scene_state, "refs": scene_refs, "excerpt": scene_excerpt,
                               "error": scene_error,
                               "retrieval": f"python3 work/tools/scene.py show {ref} --window 2"},
            "context": {"kind": "bounded physical bank neighbours", "script_order_claimed": False,
                        "items": [{"ref": r, "source": source_context(r),
                                   "english_reference": en.get(r, {}).get("text") if en.get(r) else None,
                                   "locale_text": target.get(r, {}).get("text") if target.get(r) else None}
                                  for r in picked]}}


def init_locales() -> None:
    for code, name in (("en", "English"), ("fr", "French"), ("it", "Italian"), ("de", "German"), ("es", "Spanish")):
        directory = LOCALES / code
        directory.mkdir(parents=True, exist_ok=True)
        config_path = directory / "locale.json"
        config = load(config_path) if config_path.exists() else {}
        if not isinstance(config, dict):
            raise ValueError(f"locale config must be an object: {config_path}")
        defaults = {"locale": code, "name": name, "source_locale": "zh-CN", "catalogue_schema": 1,
                    "glossary": "glossary.json", "decisions": "decisions.jsonl", "voices": "voices.json",
                    "target_bank_dir": "banks", "english_storage": "legacy work/translate/banks adapter" if code == "en" else None}
        for key, value in defaults.items():
            config.setdefault(key, value)
        if code != "en":
            config.setdefault("build_resources", {
                "graphics": {"state": "unverified", "files": []},
                "hardcoded_strings": {"state": "unverified", "files": []},
                "font": {"state": "unverified", "files": []},
                "grammar_audit": {"state": "unverified", "files": []},
            })
        atomic_json(config_path, config)
        for filename, content in (("glossary.json", {}), ("voices.json", {})):
            path = locale_resource_path(code, filename.removesuffix(".json"))
            if not path.exists():
                atomic_json(path, content)
        decisions = locale_resource_path(code, "decisions")
        if not decisions.exists():
            decisions.parent.mkdir(parents=True, exist_ok=True)
            decisions.write_text("", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-locales", help="create locale configs and empty locale resources")
    p_init = sub.add_parser("init-target", help="initialize target-localisation records from Chinese")
    p_init.add_argument("locale", choices=("fr", "it", "de", "es"))
    p_import = sub.add_parser("import-es", help="conservatively import ES references and quarantine candidates")
    p_import.add_argument("--extract", type=Path, default=ES_EXTRACT)
    p_stats = sub.add_parser("stats", help="show coverage and stale counts")
    p_stats.add_argument("locale", choices=("en", "fr", "it", "de", "es"))
    p_ready = sub.add_parser("readiness", help="strict readiness for build planning")
    p_ready.add_argument("locale", choices=("en", "fr", "it", "de", "es"))
    p_context = sub.add_parser("context", help="write one bounded context package under work/build")
    p_context.add_argument("ref")
    p_context.add_argument("--locale", default="en", choices=("en", "fr", "it", "de", "es"))
    p_context.add_argument("--out", type=Path, required=True)
    p_context.add_argument("--neighbors", type=int, default=2)
    args = parser.parse_args(argv)
    if args.command == "init-locales":
        init_locales()
        print("initialized locale configs: en, fr, it, de, es")
    elif args.command == "init-target":
        print(json.dumps(init_target(args.locale, source_entries()), ensure_ascii=False, sort_keys=True))
    elif args.command == "import-es":
        print(json.dumps(import_es(source_entries(), extract_root=args.extract), ensure_ascii=False, sort_keys=True))
    elif args.command == "stats":
        print(json.dumps(coverage(args.locale, source_entries()), ensure_ascii=False, sort_keys=True))
    elif args.command == "readiness":
        print(json.dumps(readiness(args.locale, source_entries()), ensure_ascii=False, sort_keys=True))
    elif args.command == "context":
        output = args.out if args.out.is_absolute() else ROOT / args.out
        try:
            safe_build_output(output)
        except ValueError as exc:
            parser.error(str(exc))
        if args.neighbors < 0 or args.neighbors > 10:
            parser.error("--neighbors must be from 0 to 10")
        atomic_json(output, context_package(args.ref, source_entries(), args.locale, neighbors=args.neighbors))
        print(output.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
