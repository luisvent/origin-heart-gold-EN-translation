import json
import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import localization as loc


class LocaleCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.locale_root = self.root / "locales"
        self.es_extract = self.root / "es"
        self.en_root = self.root / "en"
        self.locale_root.mkdir()
        self.es_extract.mkdir()
        self.sources = {
            "a027/0000#0": {"text": "中文源文", "source_sha256": "a" * 64,
                            "source_bank_sha256": "cn-bank", "source_path": "synthetic"},
            "a027/0000#1": {"text": "English leftover", "source_sha256": "b" * 64,
                            "source_bank_sha256": "cn-bank", "source_path": "synthetic"},
            "a027/0793#0": {"text": "外国文字", "source_sha256": "c" * 64,
                            "source_bank_sha256": "cn-bank", "source_path": "synthetic"},
        }
        self.patcher = patch.multiple(loc, LOCALES=self.locale_root, ES_EXTRACT=self.es_extract,
                                      EN_BANKS=self.en_root)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.addCleanup(self.temp.cleanup)

    def write_mappings(self, rows):
        by_bank = {}
        for row in rows:
            by_bank.setdefault((row["narc"], row["es_bank"]), {})[row["es_id"]] = row["es_text"]
        for (narc, bank), replacements in by_bank.items():
            count = sum(1 for ref in self.sources if loc.parse_ref(ref)[:2] == (narc, 0))
            payload = {"bank": bank, "strings": [{"id": i, "text": replacements.get(i, f"unused {i}")}
                                                     for i in range(count)]}
            json_path = self.es_extract / narc / f"{bank:04d}.json"
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            raw_path = self.es_extract / "raw" / narc / f"{bank:04d}.bin"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            import msgtool

            raw_path.write_bytes(msgtool.json_to_bank(dict(payload, seed=123), loc.source_charmap()))
            for row in rows:
                if row["narc"] == narc and row["es_bank"] == bank:
                    row["es_bank_sha256"] = loc.file_sha256(raw_path)
        (self.es_extract / "mappings.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")

    def mapping(self, *, es_bank=0, es_id=0, cn_id=0, candidates=None, status="candidate_same_index_equal_count_unreviewed",
                equal=True, cn_hash="cn-bank", es_text="synthetic Spanish", compatible=True):
        return {"narc": "a027", "es_bank": es_bank, "es_id": es_id, "es_text": es_text,
                "es_bank_sha256": "es-bank", "cn_bank": 0,
                "cn_candidate_ids": [cn_id] if candidates is None else candidates,
                "cn_bank_sha256": cn_hash, "mapping_status": status,
                "review_status": "unreviewed_third_party_reference", "bank_counts_equal": equal,
                "control_signature_compatible": compatible,
                "control_signature": [],
                "candidate_basis": "synthetic structural candidate"}

    def test_locale_initialization_preserves_existing_target_and_stale_source(self):
        path = loc.bank_path("fr", "a027", 0)
        path.parent.mkdir(parents=True)
        bank = loc.empty_locale_bank("fr", "a027", 0)
        bank["strings"] = [{"ref": "a027/0000#0", "source_sha256": "old", "text": "local draft",
                            "status": "reviewed", "provenance": {"kind": "local"}, "alignment": {"state": "direct"}}]
        loc.atomic_json(path, bank)
        counts = loc.init_target("fr", self.sources)
        rows = loc.index_records(loc.load(path))
        self.assertEqual(rows["a027/0000#0"]["text"], "local draft")
        self.assertEqual(rows["a027/0000#0"]["status"], "reviewed")
        self.assertEqual(rows["a027/0000#0"]["staleness"]["state"], "stale")
        self.assertEqual(counts["stale"], 1)
        self.assertNotIn("a027/0793#0", rows)

    def test_spanish_import_is_idempotent_and_does_not_overwrite_local_text(self):
        self.write_mappings([self.mapping()])
        first = loc.import_es(self.sources, extract_root=self.es_extract)
        path = loc.bank_path("es", "a027", 0)
        row = loc.index_records(loc.load(path))["a027/0000#0"]
        self.assertEqual(row["text"], "synthetic Spanish")
        self.assertEqual(row["status"], "imported")
        row.update(text="reviewer-owned text", status="reviewed")
        bank = loc.load(path)
        bank["strings"] = [row]
        loc.atomic_json(path, bank)
        second = loc.import_es(self.sources, extract_root=self.es_extract)
        after = loc.index_records(loc.load(path))["a027/0000#0"]
        self.assertEqual(after["text"], "reviewer-owned text")
        self.assertEqual(after["status"], "reviewed")
        self.assertEqual(first["imported"], 1)
        self.assertEqual(second["existing_preserved"], 1)

    def test_spanish_import_rejects_stale_source_without_replacing_local_review(self):
        self.write_mappings([self.mapping()])
        path = loc.bank_path("es", "a027", 0)
        path.parent.mkdir(parents=True)
        bank = loc.empty_locale_bank("es", "a027", 0, "cn-bank")
        bank["strings"] = [{"ref": "a027/0000#0", "source_sha256": "old", "text": "kept review",
                            "status": "reviewed", "provenance": {"kind": "local"}, "alignment": {"state": "reviewed"}}]
        loc.atomic_json(path, bank)
        counts = loc.import_es(self.sources, extract_root=self.es_extract)
        row = loc.index_records(loc.load(path))["a027/0000#0"]
        self.assertEqual(counts["stale_preserved"], 1)
        self.assertEqual(row["text"], "kept review")
        self.assertEqual(row["status"], "reviewed")
        self.assertEqual(row["staleness"]["state"], "stale")

    def test_import_fills_pristine_target_initialized_todo_record(self):
        loc.init_target("es", self.sources)
        self.write_mappings([self.mapping()])
        counts = loc.import_es(self.sources, extract_root=self.es_extract)
        row = loc.index_records(loc.load(loc.bank_path("es", "a027", 0)))["a027/0000#0"]
        self.assertEqual(counts["filled_todo"], 1)
        self.assertEqual(row["text"], "synthetic Spanish")
        self.assertEqual(row["status"], "imported")

    def test_ambiguous_stale_unknown_and_colliding_candidates_are_quarantined(self):
        self.write_mappings([
            self.mapping(es_id=0, cn_id=0),
            self.mapping(es_bank=0, es_id=0, cn_id=0),
            self.mapping(es_bank=2, es_id=1, candidates=[0, 1], status="candidate_expanded_bank_unreviewed", equal=False),
            self.mapping(es_bank=3, es_id=1, cn_id=88),
            self.mapping(es_bank=0, es_id=1, cn_id=1, cn_hash="wrong-bank"),
        ])
        counts = loc.import_es(self.sources, extract_root=self.es_extract)
        self.assertEqual(counts.get("imported", 0), 0)  # duplicate ref candidates are both rejected
        quarantine = loc.LOCALES / "es/reference/quarantine.jsonl"
        rows = [json.loads(x) for x in quarantine.read_text(encoding="utf-8").splitlines()]
        reasons = {r["reason"] for r in rows}
        self.assertIn("conflicting_es_candidates_for_source_ref", reasons)
        self.assertIn("ambiguous_or_expanded_bank_mapping", reasons)
        self.assertNotIn("unknown_source_ref", reasons)  # invalid same-index mapping is quarantined earlier
        self.assertIn("stale_or_mismatched_cn_bank_fingerprint", reasons)
        self.assertFalse(loc.bank_path("es", "a027", 0).exists())

    def test_coverage_includes_english_leftovers_and_excludes_passthrough_banks(self):
        stats = loc.coverage("fr", self.sources)
        self.assertEqual(stats["required"], 2)
        self.assertEqual(stats["passthrough_excluded"], 1)
        self.assertEqual(stats["todo"], 2)
        self.assertFalse(loc.is_required("！？……"))

    def test_readiness_reports_duplicate_refs_and_empty_resources(self):
        path = loc.bank_path("fr", "a027", 0)
        path.parent.mkdir(parents=True)
        bank = loc.empty_locale_bank("fr", "a027", 0)
        row = {"ref": "a027/0000#0", "source_sha256": "a" * 64, "text": "x", "status": "reviewed",
               "provenance": {}, "alignment": {}}
        bank["strings"] = [row, dict(row)]
        loc.atomic_json(path, bank)
        result = loc.readiness("fr", self.sources)
        self.assertEqual(result["duplicate_refs"], ["a027/0000#0"])
        self.assertFalse(result["resources_ready"])
        self.assertFalse(result["ready"])

    def test_readiness_scans_unreferenced_banks_and_wrong_bank_metadata(self):
        row = {"ref": "a027/0000#0", "source_sha256": "a" * 64, "text": "x", "status": "reviewed",
               "provenance": {}, "alignment": {"state": "unreviewed"}}
        for bank_no in (0, 1):
            path = loc.bank_path("fr", "a027", bank_no)
            path.parent.mkdir(parents=True, exist_ok=True)
            bank = loc.empty_locale_bank("fr", "a027", bank_no)
            bank["strings"] = [dict(row)]
            loc.atomic_json(path, bank)
        result = loc.readiness("fr", self.sources)
        self.assertIn("a027/0000#0", result["duplicate_refs"])
        self.assertTrue(any("wrong bank" in issue for issue in result["catalogue_errors"]))

    def test_readiness_rejects_unknown_source_refs_in_any_catalogue_file(self):
        path = loc.bank_path("fr", "a027", 1)
        path.parent.mkdir(parents=True)
        bank = loc.empty_locale_bank("fr", "a027", 1)
        bank["strings"] = [{"ref": "a027/0001#9", "source_sha256": "a" * 64, "text": "x", "status": "reviewed",
                            "provenance": {}, "alignment": {"state": "reviewed"}}]
        loc.atomic_json(path, bank)
        result = loc.readiness("fr", self.sources)
        self.assertTrue(any("unknown source ref" in issue for issue in result["catalogue_errors"]))

    def test_init_locales_preserves_custom_resource_paths(self):
        path = self.locale_root / "es/locale.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"locale": "es", "glossary": "custom-glossary.json", "custom": True}), encoding="utf-8")
        loc.init_locales()
        config = loc.load(path)
        self.assertEqual(config["glossary"], "custom-glossary.json")
        self.assertTrue(config["custom"])
        self.assertEqual(config["voices"], "voices.json")

    def test_unknown_reference_and_duplicate_catalogue_refs_are_rejected(self):
        with self.assertRaises(ValueError):
            loc.parse_ref("a027/0000#nope")
        with self.assertRaises(ValueError):
            loc.index_records({"strings": [{"ref": "a027/0000#0"}, {"ref": "a027/0000#0"}]})

    def test_raw_decoding_rejects_json_and_mapping_changed_together(self):
        self.write_mappings([self.mapping()])
        bank_path = self.es_extract / "a027/0000.json"
        data = loc.load(bank_path)
        data["strings"][0]["text"] = "mutated candidate"
        loc.atomic_json(bank_path, data)
        rows = loc.es_mappings(self.es_extract)
        rows[0]["es_text"] = "mutated candidate"
        (self.es_extract / "mappings.jsonl").write_text(json.dumps(rows[0]) + "\n")
        result = loc.import_es(self.sources, extract_root=self.es_extract)
        self.assertEqual(result["quarantined"], 1)
        self.assertFalse(loc.bank_path("es", "a027", 0).exists())
        quarantined = json.loads((loc.LOCALES / "es/reference/quarantine.jsonl").read_text())
        self.assertEqual(quarantined["reason"], "stale_or_mismatched_es_decoded_bank")

    def test_mutated_raw_fingerprint_is_rejected_against_manifest(self):
        self.write_mappings([self.mapping()])
        manifest = {"summary": {"a027": {"banks": [{"bank": 0, "es_member_sha256": "old"}]}}}
        loc.atomic_json(self.es_extract / "manifest.json", manifest)
        with patch.object(loc, "ES_EXTRACT", self.root / "default-es"):
            result = loc.import_es(self.sources, extract_root=self.es_extract)
        self.assertEqual(result["quarantined"], 1)
        quarantined = json.loads((loc.LOCALES / "es/reference/quarantine.jsonl").read_text())
        self.assertEqual(quarantined["reason"], "stale_or_mismatched_es_manifest_fingerprint")

    def test_malformed_target_shapes_and_schema_never_become_ready(self):
        path = loc.bank_path("fr", "a027", 0)
        examples = [[], {"schema_version": 9, "locale": "fr", "narc": "a027", "bank": 0,
            "strings": [42, {"ref": "a027/0000#0", "source_sha256": "a" * 64,
                         "text": [], "status": "reviewed", "alignment": None, "provenance": []}]}]
        for data in examples:
            with self.subTest(data=data):
                loc.atomic_json(path, data)
                result = loc.readiness("fr", self.sources)
                self.assertFalse(result["catalogue_ready"])
                self.assertTrue(result["catalogue_errors"])

    def test_unknown_locales_and_escaping_resource_paths_are_rejected(self):
        with self.assertRaises(ValueError):
            loc.readiness("xx", self.sources)
        path = self.locale_root / "fr/locale.json"
        loc.atomic_json(path, {"locale": "fr", "glossary": "../foreign.json"})
        with self.assertRaises(ValueError):
            loc.locale_resource_path("fr", "glossary")
        loc.atomic_json(path, {"locale": "es"})
        with self.assertRaises(ValueError):
            loc.locale_resource_path("fr", "glossary")

    def test_custom_resources_are_initialized_and_validated(self):
        path = self.locale_root / "fr/locale.json"
        loc.atomic_json(path, {"locale": "fr", "glossary": "custom/terms.json", "voices": "custom/voices.json",
                              "decisions": "custom/decisions.jsonl"})
        loc.init_locales()
        self.assertTrue((path.parent / "custom/terms.json").exists())
        loc.atomic_json(path.parent / "custom/terms.json", ["arbitrary nonempty data"])
        result = loc.readiness("fr", self.sources)
        self.assertEqual(result["resources"]["glossary.json"], "invalid")

    def test_lyric_context_hides_source_and_target_and_reports_truncation(self):
        ref = "a027/0000#0"
        source = self.sources[ref]["text"]
        legacy = {"strings": [{"id": 0, "zh": loc.zh_redact.marker(source), "en": "known substitute", "status": "reviewed"}]}
        loc.atomic_json(self.en_root / "a027/0000.json", legacy)
        bank = loc.empty_locale_bank("fr", "a027", 0)
        bank["strings"] = [{"ref": ref, "text": "synthetic lyric candidate", "status": "imported"}]
        loc.atomic_json(loc.bank_path("fr", "a027", 0), bank)
        decisions = self.locale_root / "fr/decisions.jsonl"
        decisions.write_text("".join(json.dumps({"id": f"Q-{i}", "type": "question", "refs": [ref]}) + "\n" for i in range(22)))
        with patch("scene.load_cache", return_value={}), patch("scene.show", return_value="no script path found " + source):
            result = loc.context_package(ref, self.sources, "fr", en_root=self.en_root)
        serialized = json.dumps(result, ensure_ascii=False)
        self.assertNotIn(source, serialized)
        self.assertNotIn("synthetic lyric candidate", serialized)
        self.assertEqual(result["source"]["sha256"], "a" * 64)
        self.assertEqual(result["content_decision"], "D-0368")
        self.assertEqual(result["uncertainty"]["omitted"], 2)
        self.assertEqual(result["locale_resources"]["decisions_omitted"], 2)
        self.assertFalse(result["context"]["script_order_claimed"])

    def test_default_source_fails_closed_on_missing_bank(self):
        import msgtool
        from types import SimpleNamespace

        source = self.root / "work/extract/v4"
        (source / "a027").mkdir(parents=True)
        cn_rom = self.root / "work/rom/origin_v4.0.3_cn.nds"
        cn_rom.parent.mkdir(parents=True)
        cn_rom.write_bytes(b"synthetic ROM")
        cm = loc.source_charmap()
        raw = msgtool.json_to_bank({"bank": 0, "seed": 123, "strings": [{"id": 0, "text": "synthetic source"}]}, cm)
        with patch.object(loc, "ROOT", self.root), patch.object(loc, "SOURCE", source), \
             patch.object(loc, "source_charmap", return_value=cm), \
             patch.object(msgtool, "load_rom", return_value=object()), \
             patch.object(msgtool, "_msg_narc", return_value=SimpleNamespace(files=[raw])):
            with self.assertRaisesRegex(ValueError, "incomplete Chinese source inventory"):
                loc.source_entries(source)

    def test_source_rejects_empty_raw_only_and_duplicate_id_banks(self):
        source = self.root / "source/a027"
        source.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "empty"):
            loc.source_entries(source.parent)
        for data in ({"bank": 0, "raw_bank_hex": "00"},
                     {"bank": 0, "strings": [{"id": 0, "text": "x"}, {"id": 0, "text": "y"}]}):
            loc.atomic_json(source / "0000.json", data)
            with self.assertRaises(ValueError):
                loc.source_entries(source.parent)


if __name__ == "__main__":
    unittest.main()
