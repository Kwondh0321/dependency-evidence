import json
import tempfile
import unittest
from pathlib import Path

from depevidence.cli import main
from depevidence.core import build_report


class DependencyEvidenceTests(unittest.TestCase):
    def test_parses_python_requirements(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "requirements.txt").write_text(
                "requests==2.32.3\nflask>=3\n", encoding="utf-8"
            )
            report = build_report(root)
            by_name = {item["name"]: item for item in report["dependencies"]}
            self.assertEqual("2.32.3", by_name["requests"]["version"])
            self.assertIn("unpinned-version", by_name["flask"]["findings"])

    def test_parses_npm_lock_license_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lock = {
                "lockfileVersion": 3,
                "packages": {
                    "": {"dependencies": {"pkg": "1.0.0"}},
                    "node_modules/pkg": {
                        "name": "pkg",
                        "version": "1.0.0",
                        "license": "MIT",
                    },
                },
            }
            (root / "package-lock.json").write_text(json.dumps(lock), encoding="utf-8")
            report = build_report(root)
            self.assertEqual("MIT", report["dependencies"][0]["license"])
            self.assertNotIn("license-unknown", report["dependencies"][0]["findings"])

    def test_cli_can_fail_on_unpinned(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "requirements.txt").write_text("flask>=3\n", encoding="utf-8")
            self.assertEqual(1, main([str(root), "--fail-on", "unpinned"]))

    def test_parses_pep508_direct_reference_and_uses_portable_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "requirements.txt").write_text(
                "demo @ https://example.org/demo.whl\n", encoding="utf-8"
            )
            report = build_report(root)
            dependency = report["dependencies"][0]
            self.assertEqual("demo", dependency["name"])
            self.assertEqual("https://example.org/demo.whl", dependency["source"])
            self.assertIn("mutable-or-insecure-source", dependency["findings"])
            self.assertEqual(".", report["repository"])

    def test_rejects_missing_repository(self):
        with tempfile.TemporaryDirectory() as temporary, self.assertRaises(ValueError):
            build_report(Path(temporary) / "missing")


if __name__ == "__main__":
    unittest.main()
