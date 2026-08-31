from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from audit_project import audit_project, markdown_report  # noqa: E402
import compare_fixture as compare_fixture_module  # noqa: E402
from compare_fixture import compare_fixture  # noqa: E402


def subprocess_environment_without_encoding_overrides() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("PYTHONIOENCODING", None)
    environment.pop("PYTHONUTF8", None)
    return environment


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
            self.assertIn("已检查文件：3（达到上限，结果已截断）", rendered)
            self.assertIn("不是合规评分", rendered)

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
                env=subprocess_environment_without_encoding_overrides(),
            )
            report = json.loads(result.stdout.decode("utf-8"))
            after = sorted(path.relative_to(root) for path in root.rglob("*"))

            self.assertEqual(report["technologies"], ["Python"])
            self.assertEqual(before, after)

    def test_cli_help_and_markdown_are_chinese_friendly(self) -> None:
        help_result = subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "scripts" / "audit_project.py"), "--help"],
            check=True,
            capture_output=True,
            env=subprocess_environment_without_encoding_overrides(),
        )
        self.assertIn("要检查的仓库根目录", help_result.stdout.decode("utf-8"))

        error_result = subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "scripts" / "audit_project.py"), "--max-files", "0"],
            check=False,
            capture_output=True,
            env=subprocess_environment_without_encoding_overrides(),
        )
        self.assertEqual(error_result.returncode, 2)
        self.assertIn("必须是正整数", error_result.stderr.decode("utf-8"))

    def test_does_not_echo_file_contents_or_secret_like_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            secret = "ghp_DO_NOT_ECHO_THIS_FIXTURE_VALUE"
            self.write(root, "src/settings.py", f"TOKEN = '{secret}'\n")
            rendered = json.dumps(audit_project(root), ensure_ascii=False)
            self.assertNotIn(secret, rendered)

    def test_inventory_never_reads_target_file_contents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "src/app.py", "print('private fixture contents')\n")
            with patch("pathlib.Path.read_text", side_effect=AssertionError("target content read")):
                report = audit_project(root)
            self.assertEqual(report["scan"]["files_seen"], 1)

    def test_reproducible_migration_fixture_has_observable_delta(self) -> None:
        fixture = REPOSITORY_ROOT / "examples" / "python-cli-migration"
        comparison = compare_fixture(fixture)
        self.assertEqual(comparison["before"]["migration_candidates"], 8)
        self.assertEqual(comparison["after"]["migration_candidates"], 0)
        self.assertTrue(comparison["before"]["audit_integrity"]["unchanged"])
        self.assertTrue(comparison["after"]["audit_integrity"]["unchanged"])
        self.assertEqual(comparison["before"]["audit_integrity"]["changed_paths"], [])
        self.assertEqual(comparison["after"]["path_signal_groups_present"], 8)
        self.assertEqual(comparison["after"]["path_signal_groups_total"], 8)
        for stage in ("before", "after"):
            integrity = comparison[stage]["audit_integrity"]
            self.assertEqual(integrity["snapshot_before"], integrity["snapshot_after"])
            self.assertTrue(integrity["snapshot_before"])
            self.assertTrue(all(len(entry["sha256"]) == 64 for entry in integrity["snapshot_before"]))

        rendered = compare_fixture_module.markdown_report(comparison)
        self.assertIn("审计前 SHA-256", rendered)
        self.assertIn("审计后 SHA-256", rendered)

    def test_fixture_snapshot_detects_a_write_instead_of_assuming_zero(self) -> None:
        source = REPOSITORY_ROOT / "examples" / "python-cli-migration"
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "fixture"
            shutil.copytree(source, fixture)
            real_audit = compare_fixture_module.audit_project

            def mutating_audit(root: Path) -> dict[str, object]:
                report = real_audit(root)
                (root / "unexpected-write.tmp").write_text("changed", encoding="utf-8")
                return report

            with patch.object(compare_fixture_module, "audit_project", side_effect=mutating_audit):
                comparison = compare_fixture_module.compare_fixture(fixture)

        self.assertFalse(comparison["before"]["audit_integrity"]["unchanged"])
        self.assertIn("unexpected-write.tmp", comparison["before"]["audit_integrity"]["changed_paths"])

    def test_fixture_preserves_product_files_byte_for_byte(self) -> None:
        fixture = REPOSITORY_ROOT / "examples" / "python-cli-migration"
        for relative in ("pyproject.toml", "src/hello.py", "tests/test_hello.py"):
            self.assertEqual((fixture / "before" / relative).read_bytes(), (fixture / "after" / relative).read_bytes())


if __name__ == "__main__":
    unittest.main()
