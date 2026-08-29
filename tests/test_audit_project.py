from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from audit_project import audit_project, markdown_report  # noqa: E402


class AuditProjectTests(unittest.TestCase):
    def write(self, root: Path, relative: str, contents: str = "") -> None:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(contents, encoding="utf-8")

    def test_detects_technology_and_governance_signals(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "Cargo.toml", "[package]\nname = 'demo'\n")
            self.write(root, "src/main.rs", "fn main() {}\n")
            self.write(root, "AGENTS.md", "# Rules\n")
            self.write(root, "CONTRIBUTING.md", "# Contributing\n")
            self.write(root, "docs/ai-collaboration.md", "# AI\n")
            self.write(root, ".github/workflows/ci.yml", "name: CI\n")
            self.write(root, ".github/pull_request_template.md", "# Review\n")

            report = audit_project(root)

            self.assertEqual(report["technologies"], ["Rust"])
            governance = report["governance"]
            self.assertEqual(governance["ai_entrypoints"], ["AGENTS.md"])
            self.assertEqual(governance["contribution_guides"], ["CONTRIBUTING.md"])
            self.assertEqual(governance["ci_workflows"], [".github/workflows/ci.yml"])
            candidate_codes = {item["code"] for item in report["migration_candidates"]}
            self.assertNotIn("ai-entrypoint", candidate_codes)
            self.assertNotIn("pull-request-evidence", candidate_codes)

    def test_prunes_generated_and_dependency_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "src/app.py", "print('ok')\n")
            self.write(root, "target/generated.rs", "generated\n")
            self.write(root, "node_modules/pkg/package.json", "{}\n")
            self.write(root, "vendor/library/go.mod", "module vendor\n")
            self.write(root, ".agents/skills/example/package.json", "{}\n")

            report = audit_project(root)

            self.assertEqual(report["scan"]["files_seen"], 1)
            self.assertEqual(report["technologies"], [])
            self.assertEqual(
                set(report["scan"]["excluded_directories_seen"]),
                {"node_modules", "skills", "target", "vendor"},
            )

    def test_truncation_and_markdown_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in range(5):
                self.write(root, f"docs/{index}.md", f"# {index}\n")

            report = audit_project(root, max_files=3)
            rendered = markdown_report(report)

            self.assertTrue(report["scan"]["truncated"])
            self.assertIn("Files inspected: 3 (truncated)", rendered)
            self.assertIn("not a compliance score", rendered)

    def test_cli_emits_valid_json_without_writing_to_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "pyproject.toml", "[project]\nname = 'demo'\n")
            before = sorted(path.relative_to(root) for path in root.rglob("*"))

            result = subprocess.run(
                [
                    sys.executable,
                    str(REPOSITORY_ROOT / "scripts" / "audit_project.py"),
                    "--root",
                    str(root),
                    "--format",
                    "json",
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            report = json.loads(result.stdout)
            after = sorted(path.relative_to(root) for path in root.rglob("*"))

            self.assertEqual(report["technologies"], ["Python"])
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
