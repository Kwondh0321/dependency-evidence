import json
import tempfile
import unittest
from pathlib import Path

from depevidence.cli import main
from depevidence.core import build_report, discover_manifests


class DependencyEvidenceTests(unittest.TestCase):
    def test_parses_python_requirements(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "requirements.txt").write_text("requests==2.32.3\nflask>=3\n", encoding="utf-8")
            report = build_report(root)
            by_name = {item["name"]: item for item in report["dependencies"]}
            self.assertEqual("2.32.3", by_name["requests"]["version"])
            self.assertIn("unpinned-version", by_name["flask"]["findings"])

    def test_parses_npm_lock_license_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lock = {"lockfileVersion": 3, "packages": {"": {"dependencies": {"pkg": "1.0.0"}}, "node_modules/pkg": {"name": "pkg", "version": "1.0.0", "license": "MIT"}}}
            (root / "package-lock.json").write_text(json.dumps(lock), encoding="utf-8")
            report = build_report(root)
            self.assertEqual("MIT", report["dependencies"][0]["license"])
            self.assertNotIn("license-unknown", report["dependencies"][0]["findings"])

    def test_cli_can_fail_on_unpinned(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "requirements.txt").write_text("flask>=3\n", encoding="utf-8")
            self.assertEqual(1, main([str(root), "--fail-on", "unpinned"]))


if __name__ == "__main__":
    unittest.main()

