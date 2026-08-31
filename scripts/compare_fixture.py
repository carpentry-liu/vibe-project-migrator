#!/usr/bin/env python3
"""对仓库内的可复现迁移样例执行前后只读对比。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from audit_project import audit_project, configure_utf8_stdio


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = REPOSITORY_ROOT / "examples" / "python-cli-migration"
BASELINE_SIGNAL_KEYS = (
    "ai_entrypoints",
    "ai_collaboration_rules",
    "contribution_guides",
    "pull_request_templates",
    "change_templates",
    "docs_indexes",
    "security_policies",
    "ci_workflows",
)


def file_snapshot(root: Path) -> list[dict[str, object]]:
    """Hash fixture files without following links or exposing their contents."""
    resolved = root.resolve()
    entries: list[dict[str, object]] = []
    for current, directories, filenames in os.walk(resolved, followlinks=False):
        current_path = Path(current)
        kept_directories = []
        for directory in directories:
            child = current_path / directory
            if child.is_symlink():
                target = os.readlink(child)
                entries.append(
                    {
                        "path": child.relative_to(resolved).as_posix(),
                        "kind": "symlink",
                        "sha256": hashlib.sha256(target.encode("utf-8")).hexdigest(),
                    }
                )
            else:
                kept_directories.append(directory)
        directories[:] = kept_directories
        for filename in filenames:
            path = current_path / filename
            relative = path.relative_to(resolved).as_posix()
            if path.is_symlink():
                target = os.readlink(path)
                entries.append(
                    {
                        "path": relative,
                        "kind": "symlink",
                        "sha256": hashlib.sha256(target.encode("utf-8")).hexdigest(),
                    }
                )
                continue
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(64 * 1024), b""):
                    digest.update(block)
            entries.append(
                {
                    "path": relative,
                    "kind": "file",
                    "size": path.stat().st_size,
                    "sha256": digest.hexdigest(),
                }
            )
    return sorted(entries, key=lambda entry: str(entry["path"]))


def audit_with_snapshot(root: Path) -> tuple[dict[str, object], dict[str, object]]:
    snapshot_before = file_snapshot(root)
    report = audit_project(root)
    snapshot_after = file_snapshot(root)
    before_by_path = {str(entry["path"]): entry for entry in snapshot_before}
    after_by_path = {str(entry["path"]): entry for entry in snapshot_after}
    changed_paths = sorted(
        path
        for path in before_by_path.keys() | after_by_path.keys()
        if before_by_path.get(path) != after_by_path.get(path)
    )
    return report, {
        "unchanged": not changed_paths,
        "changed_paths": changed_paths,
        "snapshot_before": snapshot_before,
        "snapshot_after": snapshot_after,
    }


def compare_fixture(fixture: Path = DEFAULT_FIXTURE) -> dict[str, object]:
    before, before_integrity = audit_with_snapshot(fixture / "before")
    after, after_integrity = audit_with_snapshot(fixture / "after")

    def metrics(report: dict[str, object], integrity: dict[str, object]) -> dict[str, object]:
        governance = report["governance"]
        return {
            "files_seen": report["scan"]["files_seen"],
            "technologies": report["technologies"],
            "path_signal_groups_present": sum(bool(governance[key]) for key in BASELINE_SIGNAL_KEYS),
            "path_signal_groups_total": len(BASELINE_SIGNAL_KEYS),
            "migration_candidates": len(report["migration_candidates"]),
            "audit_integrity": integrity,
        }

    return {
        "fixture": "合成的 Python CLI 示例，不代表真实团队成效",
        "before": metrics(before, before_integrity),
        "after": metrics(after, after_integrity),
        "interpretation": "候选项和路径信号只反映文件路径是否存在，不验证文件内容质量，也不是效率或合规评分。",
    }


def markdown_report(comparison: dict[str, object]) -> str:
    before = comparison["before"]
    after = comparison["after"]
    lines = [
        "# 可复现迁移样例对比",
        "",
        f"> {comparison['fixture']}。",
        "",
        "| 可观察指标 | 迁移前 | 迁移后 |",
        "|---|---:|---:|",
        f"| 已枚举文件 | {before['files_seen']} | {after['files_seen']} |",
        f"| 已有路径信号组 | {before['path_signal_groups_present']}/{before['path_signal_groups_total']} | {after['path_signal_groups_present']}/{after['path_signal_groups_total']} |",
        f"| 待确认迁移项 | {before['migration_candidates']} | {after['migration_candidates']} |",
        f"| 审计前后 SHA-256 快照一致 | {'是' if before['audit_integrity']['unchanged'] else '否'} | {'是' if after['audit_integrity']['unchanged'] else '否'} |",
        "",
        f"> {comparison['interpretation']}",
        "",
        "## 零写入快照证据",
        "",
        "> 下列哈希由案例对比器读取合成 fixture 后计算；只读审计器本身仍不读取目标文件内容。",
    ]
    for label, item in (("迁移前 fixture", before), ("迁移后 fixture", after)):
        integrity = item["audit_integrity"]
        snapshot_before = {str(entry["path"]): entry for entry in integrity["snapshot_before"]}
        snapshot_after = {str(entry["path"]): entry for entry in integrity["snapshot_after"]}
        lines.extend(
            [
                "",
                f"### {label}",
                "",
                f"- 结果：{'审计前后完全一致' if integrity['unchanged'] else '检测到变化'}",
                "",
                "| 相对路径 | 审计前 SHA-256 | 审计后 SHA-256 | 对比 |",
                "|---|---|---|---|",
            ]
        )
        for path in sorted(snapshot_before.keys() | snapshot_after.keys()):
            before_hash = snapshot_before.get(path, {}).get("sha256", "（不存在）")
            after_hash = snapshot_after.get(path, {}).get("sha256", "（不存在）")
            status = "一致" if snapshot_before.get(path) == snapshot_after.get(path) else "变化"
            lines.append(f"| `{path}` | `{before_hash}` | `{after_hash}` | {status} |")
        if integrity["changed_paths"]:
            lines.extend(["", "- 变化路径：" + "、".join(integrity["changed_paths"])])
    return "\n".join(lines) + "\n"


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE, help="包含 before/after 的样例目录。")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = parser.parse_args()
    comparison = compare_fixture(args.fixture.resolve())
    if args.format == "json":
        print(json.dumps(comparison, ensure_ascii=False, indent=2))
    else:
        print(markdown_report(comparison), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
