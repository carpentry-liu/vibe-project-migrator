#!/usr/bin/env python3
"""Vibe Project Migrator 的只读仓库画像工具。"""

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

PROFILE_HINT_LABELS = {
    "baseline-profile-candidate": "可考虑 Baseline（基础）层级",
    "standard-profile-candidate": "可考虑 Standard（标准）层级",
    "review-layered-instructions": "复核是否需要 Layered（分层）规则",
    "review-docs-index-and-repository-map": "复核文档索引与仓库地图",
    "human-risk-classification-required": "风险级别仍需人工判断",
}


def configure_utf8_stdio() -> None:
    """Make CLI output deterministic UTF-8 without requiring shell variables."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            # Embedded hosts and test doubles may expose a non-reconfigurable stream.
            continue


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
        ("ai-entrypoint", "ai_entrypoints", "新增或整合仓库级 AI 协作入口。"),
        ("ai-collaboration", "ai_collaboration_rules", "确认是否已说明人类与 AI 的职责、风险分级和证据要求；缺失时再补充。"),
        ("contribution-guide", "contribution_guides", "确认并记录可直接执行的贡献与验证命令。"),
        ("pull-request-evidence", "pull_request_templates", "确认评审入口是否覆盖范围、风险、真实证据与 AI 参与范围。"),
        ("change-proposal", "change_templates", "确认有风险的改动是否具备轻量变更提案路径。"),
        ("docs-index", "docs_indexes", "确认现有文档规模是否需要按读者意图组织的索引。"),
        ("security-reporting", "security_policies", "确认是否需要私密的安全问题报告渠道。"),
        ("continuous-integration", "ci_workflows", "确认是否已有可重复的自动验证；若没有，记录原因。"),
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
        raise ValueError(f"仓库根目录不存在或不是目录：{resolved_root}")

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
            "仓库画像是只读迁移线索，不构成合规结论或评分。",
            "编辑前仍需从仓库权威材料确认命令、风险和事实。",
        ],
    }


def markdown_report(report: dict[str, object]) -> str:
    scan = report["scan"]
    repository = report["repository"]
    governance = report["governance"]
    lines = [
        "# 仓库迁移画像",
        "",
        f"- 根目录：`{report['root']}`",
        f"- 已检查文件：{scan['files_seen']}" + ("（达到上限，结果已截断）" if scan["truncated"] else ""),
        f"- Git 仓库：{'是' if repository.get('is_repository') else '否'}",
        f"- 技术栈：{', '.join(report['technologies']) or '未从文件标记识别'}",
        f"- 迁移层级线索：{'; '.join(PROFILE_HINT_LABELS.get(item, item) for item in report['profile_hints'])}",
        "",
        "## 协作治理信号",
        "",
    ]
    for key, matches in governance.items():
        lines.append(f"- `{key}`：{len(matches)}")
        for match in matches[:8]:
            lines.append(f"  - `{match}`")
        if len(matches) > 8:
            lines.append(f"  - ……另有 {len(matches) - 8} 项")
    lines.extend(["", "## 待确认的迁移项", ""])
    for candidate in report["migration_candidates"]:
        lines.append(f"- **{candidate['code']}**: {candidate['recommendation']}")
    if not report["migration_candidates"]:
        lines.append("- 未检测到缺失的基础信号；仍需人工检查内容质量与一致性。")
    lines.extend(["", "> 本画像只提供迁移线索，不是合规评分。"])
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="要检查的仓库根目录，默认为当前目录。")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown", help="输出格式，默认为 markdown。")
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES, help="最多枚举的文件数。")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    args = parse_args(argv or sys.argv[1:])
    if args.max_files < 1:
        print("--max-files 必须是正整数", file=sys.stderr)
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
