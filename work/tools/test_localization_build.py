import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import localization as loc
import localization_build as lb


class LocaleBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.locale_root = self.root / "locales"
        self.stage_root = lb.ROOT / "work/build/locales/test-localization-build"
        self.sources = {
            "a027/0000#0": {"text": "中文文本", "source_sha256": "a" * 64,
                            "source_bank_sha256": "bank-a", "source_path": "synthetic"},
            "a027/0000#1": {"text": "！？……", "source_sha256": "b" * 64,
                            "source_bank_sha256": "bank-a", "source_path": "synthetic"},
            "a027/0793#0": {"text": "外国文字", "source_sha256": "c" * 64,
                            "source_bank_sha256": "bank-b", "source_path": "synthetic"},
        }
        self.patches = [
            patch.object(loc, "LOCALES", self.locale_root),
            patch.object(lb, "BUILD_ROOT", self.stage_root),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(lambda: shutil.rmtree(self.stage_root, ignore_errors=True))
        self.locale_dir = self.locale_root / "fr"
        self.locale_dir.mkdir(parents=True)
        (self.locale_dir / "locale.json").write_text(json.dumps({"locale": "fr", "glossary": "glossary.json",
            "voices": "voices.json", "decisions": "decisions.jsonl", "build_resources": {}}), encoding="utf-8")
        (self.locale_dir / "glossary.json").write_text('{"Pokémon":"Pokémon"}', encoding="utf-8")
        (self.locale_dir / "voices.json").write_text('{"speaker":"voice"}', encoding="utf-8")
        (self.locale_dir / "decisions.jsonl").write_text("", encoding="utf-8")

    def set_record(self, *, status="reviewed", source_hash="a" * 64, text="Texte français"):
        path = loc.bank_path("fr", "a027", 0)
        bank = loc.empty_locale_bank("fr", "a027", 0, "bank-a")
        bank["strings"] = [{"ref": "a027/0000#0", "source_sha256": source_hash, "text": text,
                            "status": status, "provenance": {"kind": "local"},
                            "alignment": {"state": "direct_source_ref"}}]
        loc.atomic_json(path, bank)

    def test_partial_imported_and_stale_catalogues_do_not_stage(self):
        self.set_record(status="imported")
        with self.assertRaises(lb.LocaleBuildError):
            lb.prepare("fr", self.sources)
        self.set_record(status="reviewed", source_hash="old")
        with self.assertRaises(lb.LocaleBuildError):
            lb.prepare("fr", self.sources)

    def test_complete_catalogue_stages_with_exact_copies_and_isolated_reproducible_path(self):
        self.set_record()
        result1 = lb.prepare("fr", self.sources)
        result2 = lb.prepare("fr", self.sources)
        self.assertEqual(result1["stage"], result2["stage"])
        stage = Path(result1["stage"])
        if not stage.is_absolute():
            stage = lb.ROOT / stage
        manifest = json.loads((stage / "manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["compile_ready"])
        self.assertEqual(manifest["resource_states"], {"graphics": "unverified", "hardcoded_strings": "unverified",
                                                       "font": "unverified", "grammar_audit": "unverified"})
        staged = json.loads((stage / "workspace/a027/0000.json").read_text(encoding="utf-8"))
        self.assertEqual(staged["strings"][0]["en"], "Texte français")
        self.assertEqual(staged["strings"][1]["en"], "！？……")
        self.assertEqual(staged["strings"][1]["origin"], "copy")
        self.assertEqual(staged["strings"][1]["status"], "reviewed")
        self.assertEqual(staged["strings"][1]["en"], staged["strings"][1]["zh"])
        passthrough = json.loads((stage / "workspace/a027/0793.json").read_text(encoding="utf-8"))
        self.assertEqual(passthrough["strings"][0]["en"], "外国文字")
        self.assertFalse((stage / "workspace/a027/0000.json").is_symlink())

    def test_empty_reviewed_text_is_not_stageable(self):
        self.set_record(text="")
        self.assertFalse(loc.readiness("fr", self.sources)["catalogue_ready"])
        with self.assertRaises(lb.LocaleBuildError):
            lb.prepare("fr", self.sources)

    def test_matrix_exposes_locale_asset_blockers_and_keeps_english_default(self):
        self.set_record()
        data = lb.matrix(self.sources)
        by_locale = {row["locale"]: row for row in data["locales"]}
        self.assertFalse(by_locale["en"]["build_ready"])
        self.assertEqual(by_locale["en"]["build_path"], "legacy-default")
        self.assertFalse(by_locale["fr"]["build_ready"])
        self.assertTrue(any("graphics locale resource is unverified" in b for b in by_locale["fr"]["blockers"]))

    def test_fingerprint_changes_when_target_changes(self):
        self.set_record(text="Texte A")
        a = lb.prepare("fr", self.sources)["manifest"]["fingerprint"]
        self.set_record(text="Texte B")
        b = lb.prepare("fr", self.sources)["manifest"]["fingerprint"]
        self.assertNotEqual(a, b)

    def test_empty_sources_cannot_stage(self):
        with self.assertRaises(lb.LocaleBuildError):
            lb.prepare("fr", {})

    def test_cached_stage_rejects_unmanifested_files_or_modified_content(self):
        self.set_record()
        result = lb.prepare("fr", self.sources)
        stage = lb.ROOT / result["stage"]
        extra = stage / "workspace/a027/9999.json"
        extra.write_text("{}")
        with self.assertRaisesRegex(lb.LocaleBuildError, "cached stage differs"):
            lb.prepare("fr", self.sources)
        extra.unlink()
        (stage / "workspace/a027/0000.json").write_text("{}")
        with self.assertRaisesRegex(lb.LocaleBuildError, "cached stage differs"):
            lb.prepare("fr", self.sources)

    def test_cached_stage_symlink_cannot_escape(self):
        self.set_record()
        result = lb.prepare("fr", self.sources)
        stage = lb.ROOT / result["stage"]
        external = self.root / "outside"
        external.mkdir()
        (stage / "escape").symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(lb.LocaleBuildError, "symlink"):
            lb.prepare("fr", self.sources)
        self.assertEqual(list(external.iterdir()), [])

    def test_build_outputs_cannot_traverse_shared_symlinks_or_parent_segments(self):
        external = self.root / "outside"
        external.mkdir()
        shared = self.stage_root / "shared"
        shared.parent.mkdir(parents=True, exist_ok=True)
        shared.symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            loc.safe_build_output(shared / "output.json")
        with self.assertRaises(ValueError):
            loc.safe_build_output(lb.ROOT / "work/build/../../outside.json")


    def test_full_display_plan_uses_target_names_and_keeps_compilation_disabled(self):
        self.set_record()
        ref = "a027/0719#17"
        self.sources[ref] = {"text": "中文组名", "source_sha256": "d" * 64,
                             "source_bank_sha256": "bank-c", "source_path": "synthetic"}
        path = loc.bank_path("fr", "a027", 719)
        bank = loc.empty_locale_bank("fr", "a027", 719, "bank-c")
        bank["strings"] = [{"ref": ref, "source_sha256": "d" * 64,
                            "text": "Groupe complet", "status": "reviewed",
                            "provenance": {"kind": "local"},
                            "alignment": {"state": "direct_source_ref"}}]
        loc.atomic_json(path, bank)
        first = lb.prepare("fr", self.sources)
        self.assertFalse(first["manifest"]["compile_ready"])
        self.assertEqual(first["manifest"]["trainer_display"]["aliases"], {17: "Groupe complet"})
        self.assertTrue(first["manifest"]["trainer_display"]["runtime_required"])
        bank["strings"][0]["text"] = "Autre groupe"
        loc.atomic_json(path, bank)
        second = lb.prepare("fr", self.sources)
        self.assertNotEqual(first["stage"], second["stage"])
        self.assertNotEqual(first["manifest"]["trainer_display"]["alias_sha256"],
                            second["manifest"]["trainer_display"]["alias_sha256"])


if __name__ == "__main__":
    unittest.main()
