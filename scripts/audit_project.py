#!/usr/bin/env python3
"""Read-only repository inventory for the vibe-project-migrator skill."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


SCHEMA_VERSION = 1
DEFAULT_MAX_FILES = 50_000
EXCLUDED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".validation-deps",
    ".idea",
    ".vscode",
    "__pycache__",
    "build",
    "build-debug",
    "build-release",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
    "vendor",
    "vendors",
    "venv",
    ".venv",
}

EXCLUDED_RELATIVE_PREFIXES = {
    ".agents/skills",
    ".claude/worktrees",
    ".codex/skills",
}

TECHNOLOGY_MARKERS = {
    "Rust": {"cargo.toml"},
    "Node.js / JavaScript / TypeScript": {
        "package.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "bun.lock",
        "bun.lockb",
    },
    "Python": {
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
        "setup.cfg",
        "pipfile",
        "poetry.lock",
    },
    "Go": {"go.mod"},
    "Java / Kotlin": {
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle",
        "settings.gradle.kts",
    },
    ".NET": {"global.json", "directory.build.props", "directory.build.targets"},
    "C / C++": {"cmakelists.txt", "meson.build", "configure.ac"},
    "Ruby": {"gemfile"},
    "PHP": {"composer.json"},
    "Swift": {"package.swift"},
    "Dart / Flutter": {"pubspec.yaml"},
}

SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".dart",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".swift",
    ".ts",
    ".tsx",
}


def relative_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def inventory_files(root: Path, max_files: int) -> tuple[list[str], bool, list[str]]:
    files: list[str] = []
    excluded_seen: set[str] = set()
    truncated = False

    for current, directories, filenames in os.walk(root, followlinks=False):
        current_path = Path(current)
        kept_directories = []
        for directory in directories:
            child = current_path / directory
            child_relative = relative_posix(child, root).lower()
            excluded_prefix = any(
                child_relative == prefix or child_relative.startswith(f"{prefix}/")
                for prefix in EXCLUDED_RELATIVE_PREFIXES
            )
            if directory.lower() in EXCLUDED_DIRECTORIES or excluded_prefix or child.is_symlink():
                excluded_seen.add(directory)
            else:
                kept_directories.append(directory)
        directories[:] = kept_directories

        for filename in filenames:
            candidate = current_path / filename
            if candidate.is_symlink():
                continue
            files.append(relative_posix(candidate, root))
            if len(files) >= max_files:
                truncated = True
                return sorted(files), truncated, sorted(excluded_seen)

    return sorted(files), truncated, sorted(excluded_seen)


def matches_any(paths: Iterable[str], predicate) -> list[str]:
    return sorted(path for path in paths if predicate(path.lower()))


def detect_technologies(paths: list[str]) -> list[str]:
    basenames = {Path(path).name.lower() for path in paths}
    technologies = [
        technology
        for technology, markers in TECHNOLOGY_MARKERS.items()
        if basenames.intersection(markers)
    ]
    if any(path.lower().endswith((".sln", ".csproj", ".fsproj", ".vbproj")) for path in paths):
        technologies.append(".NET")
    if any(path.lower().endswith(("makefile", ".mk")) for path in paths):
        technologies.append("C / C++")
    return sorted(set(technologies))


def run_git(root: Path, *arguments: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""
    return result.returncode == 0, result.stdout.strip()


def git_summary(root: Path) -> dict[str, object]:
    inside, top_level = run_git(root, "rev-parse", "--show-toplevel")
    if not inside:
        return {"is_repository": False}

    branch_ok, branch = run_git(root, "branch", "--show-current")
    status_ok, status = run_git(root, "status", "--short", "--untracked-files=all")
    remotes_ok, remotes = run_git(root, "remote")
    status_lines = status.splitlines() if status_ok and status else []
    untracked = sum(1 for line in status_lines if line.startswith("??"))
    tracked = len(status_lines) - untracked

    return {
        "is_repository": True,
        "top_level_matches_root": Path(top_level).resolve() == root,
        "branch": branch if branch_ok and branch else None,
        "dirty": {
            "total": len(status_lines),
            "tracked": tracked,
            "untracked": untracked,
        },
        "remote_count": len(remotes.splitlines()) if remotes_ok and remotes else 0,
    }


def governance_signals(paths: list[str]) -> dict[str, list[str]]:
    def name_is(*names: str):
        expected = {name.lower() for name in names}
        return lambda path: Path(path).name.lower() in expected

    return {
        "ai_entrypoints": matches_any(
            paths,
            lambda path: Path(path).name.lower()
            in {"agents.md", "claude.md", "gemini.md", "copilot-instructions.md"}
            or path.startswith(".cursor/rules/"),
        ),
        "ai_collaboration_rules": matches_any(
            paths,
            lambda path: any(token in path for token in ("ai-collaboration", "ai_assisted", "ai-assisted", "vibe")),
        ),
        "contribution_guides": matches_any(paths, name_is("contributing.md", "contributing.rst")),
        "security_policies": matches_any(paths, name_is("security.md")),
        "codes_of_conduct": matches_any(paths, name_is("code_of_conduct.md", "code-of-conduct.md")),
        "changelogs": matches_any(paths, name_is("changelog.md", "changes.md", "history.md")),
        "docs_indexes": matches_any(
            paths,
            lambda path: path in {"docs/readme.md", "docs/index.md", "documentation/readme.md"}
            or path.endswith("/docs/index.md"),
        ),
        "architecture_docs": matches_any(
            paths,
            lambda path: "architecture" in path or "architectural" in path or "/adr/" in f"/{path}/",
        ),
        "change_templates": matches_any(
            paths,
            lambda path: "template" in path
            and any(token in path for token in ("change", "feature", "refactor", "rfc", "proposal")),
        ),
        "pull_request_templates": matches_any(
            paths,
            lambda path: "pull_request_template" in path or "merge_request_template" in path,
        ),
        "issue_templates": matches_any(paths, lambda path: "issue_template/" in path),
        "ci_workflows": matches_any(
            paths,
            lambda path: path.startswith(".github/workflows/")
            or path in {".gitlab-ci.yml", "azure-pipelines.yml", "jenkinsfile"}
            or path.startswith(".circleci/"),
        ),
    }


def migration_candidates(signals: dict[str, list[str]]) -> list[dict[str, str]]:
    candidates = []
    checks = [
        ("ai-entrypoint", "ai_entrypoints", "Add or consolidate a repository-level AI instruction entrypoint."),
        ("ai-collaboration", "ai_collaboration_rules", "Confirm whether human/AI roles, risk tiers, and evidence rules are already covered; document them if absent."),
        ("contribution-guide", "contribution_guides", "Confirm and document executable contributor and validation commands."),
        ("pull-request-evidence", "pull_request_templates", "Confirm review intake covers scope, risk, actual evidence, and AI coverage."),
        ("change-proposal", "change_templates", "Confirm risk-bearing changes have a lightweight proposal path."),
        ("docs-index", "docs_indexes", "Confirm whether the documentation set warrants an intent-oriented index."),
        ("security-reporting", "security_policies", "Confirm whether a private security-reporting path is needed."),
        ("continuous-integration", "ci_workflows", "Confirm repeatable automated validation or document why it is absent."),
    ]
    for code, key, recommendation in checks:
        if not signals[key]:
            candidates.append({"code": code, "recommendation": recommendation})
    return candidates


def profile_hints(paths: list[str], technologies: list[str], signals: dict[str, list[str]]) -> list[str]:
    top_level_directories = {path.split("/", 1)[0] for path in paths if "/" in path}
    source_roots = {
        path.split("/", 1)[0]
        for path in paths
        if Path(path).suffix.lower() in SOURCE_SUFFIXES and "/" in path
    }
    hints = []
    if len(paths) <= 200 and len(technologies) <= 2:
        hints.append("baseline-profile-candidate")
    else:
        hints.append("standard-profile-candidate")
    if len(source_roots) >= 4 or len(technologies) >= 4 or len(signals["ai_entrypoints"]) >= 3:
        hints.append("review-layered-instructions")
    if len(top_level_directories) >= 12:
        hints.append("review-docs-index-and-repository-map")
    hints.append("human-risk-classification-required")
    return hints


def audit_project(root: Path, max_files: int = DEFAULT_MAX_FILES) -> dict[str, object]:
    resolved_root = root.expanduser().resolve()
    if not resolved_root.is_dir():
        raise ValueError(f"Repository root is not a directory: {resolved_root}")

    paths, truncated, excluded = inventory_files(resolved_root, max_files)
    technologies = detect_technologies(paths)
    signals = governance_signals(paths)
    suffix_counts = Counter(Path(path).suffix.lower() or "<none>" for path in paths)
    top_suffixes = [
        {"suffix": suffix, "files": count}
        for suffix, count in suffix_counts.most_common(12)
    ]
    top_level = sorted({path.split("/", 1)[0] for path in paths})

    return {
        "schema_version": SCHEMA_VERSION,
        "root": str(resolved_root),
        "scan": {
            "files_seen": len(paths),
            "truncated": truncated,
            "max_files": max_files,
            "excluded_directories_seen": excluded,
            "top_level_entries": top_level,
            "top_file_suffixes": top_suffixes,
        },
        "repository": git_summary(resolved_root),
        "technologies": technologies,
        "governance": signals,
        "profile_hints": profile_hints(paths, technologies, signals),
        "migration_candidates": migration_candidates(signals),
        "notes": [
            "Inventory is read-only and does not establish compliance.",
            "Confirm commands, risks, and authoritative documents from repository contents before editing.",
        ],
    }


def markdown_report(report: dict[str, object]) -> str:
    scan = report["scan"]
    repository = report["repository"]
    governance = report["governance"]
    lines = [
        "# Repository migration inventory",
        "",
        f"- Root: `{report['root']}`",
        f"- Files inspected: {scan['files_seen']}" + (" (truncated)" if scan["truncated"] else ""),
        f"- Git repository: {'yes' if repository.get('is_repository') else 'no'}",
        f"- Technologies: {', '.join(report['technologies']) or 'not detected from markers'}",
        f"- Profile hints: {', '.join(report['profile_hints'])}",
        "",
        "## Governance signals",
        "",
    ]
    for key, matches in governance.items():
        lines.append(f"- {key.replace('_', ' ')}: {len(matches)}")
        for match in matches[:8]:
            lines.append(f"  - `{match}`")
        if len(matches) > 8:
            lines.append(f"  - … {len(matches) - 8} more")
    lines.extend(["", "## Migration candidates", ""])
    for candidate in report["migration_candidates"]:
        lines.append(f"- **{candidate['code']}**: {candidate['recommendation']}")
    if not report["migration_candidates"]:
        lines.append("- No missing baseline signals were detected; review quality and consistency manually.")
    lines.extend(["", "> This inventory provides signals, not a compliance score."])
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root to inspect.")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.max_files < 1:
        print("--max-files must be positive", file=sys.stderr)
        return 2
    try:
        report = audit_project(args.root, args.max_files)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    if args.format == "json":
        json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(markdown_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
