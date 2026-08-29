from __future__ import annotations

import html
import sys
import tempfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from audit_project import audit_project  # noqa: E402


def build_example_repository(root: Path) -> None:
    markers = {
        "package.json": '{"name":"example-agent-app","private":true}\n',
        "pyproject.toml": '[project]\nname = "example-agent-api"\n',
        "Cargo.toml": '[package]\nname = "example-agent-runtime"\nversion = "0.1.0"\n',
        "go.mod": "module example.com/agent-worker\n",
        "README.md": "# Example Agent App\n",
    }
    for relative, contents in markers.items():
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(contents, encoding="utf-8")

    source_roots = [
        ("apps", ".ts", "export const ready = true;\n"),
        ("services", ".py", "READY = True\n"),
        ("crates", ".rs", "pub const READY: bool = true;\n"),
        ("workers", ".go", "package worker\n"),
    ]
    for folder, suffix, contents in source_roots:
        for index in range(54):
            destination = root / folder / "src" / f"module_{index:02d}{suffix}"
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(contents, encoding="utf-8")


def render_report(report: dict[str, object]) -> str:
    scan = report["scan"]
    candidates = report["migration_candidates"]
    technologies = report["technologies"]
    profile = "Standard + Layered review" if "review-layered-instructions" in report["profile_hints"] else "Baseline"
    chips = "".join(f"<span>{html.escape(item)}</span>" for item in technologies)
    candidate_rows = "".join(
        f"<li><b>{index:02d}</b><span>{html.escape(candidate['code'])}</span><i>REVIEW</i></li>"
        for index, candidate in enumerate(candidates[:6], start=1)
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Vibe Project Migrator · real audit demo</title>
  <style>
    :root {{ --paper:#f3efe4; --ink:#171815; --red:#e3422f; --acid:#d9ff43; --line:#9c988d; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:#171815; color:var(--ink); font-family:"Segoe UI", "Microsoft YaHei", sans-serif; }}
    main {{ width:1440px; height:900px; margin:0 auto; padding:42px 52px; overflow:hidden; background:
      linear-gradient(rgba(23,24,21,.045) 1px, transparent 1px),
      linear-gradient(90deg, rgba(23,24,21,.045) 1px, transparent 1px), var(--paper);
      background-size:28px 28px; position:relative; }}
    main::after {{ content:""; position:absolute; inset:18px; border:2px solid var(--ink); pointer-events:none; }}
    header {{ display:grid; grid-template-columns:1fr auto; align-items:start; border-bottom:4px solid var(--ink); padding-bottom:22px; }}
    .eyebrow {{ font:800 16px/1 "Consolas", monospace; letter-spacing:.16em; color:var(--red); }}
    h1 {{ margin:9px 0 0; font:900 54px/.95 "Microsoft YaHei", sans-serif; letter-spacing:-.055em; }}
    .stamp {{ transform:rotate(2deg); border:3px solid var(--red); color:var(--red); padding:12px 16px; font:900 18px/1.05 "Consolas", monospace; text-align:center; }}
    .grid {{ display:grid; grid-template-columns:1.08fr .92fr; gap:28px; margin-top:28px; }}
    .terminal {{ background:var(--ink); color:#f8f3e7; min-height:225px; padding:22px 24px; box-shadow:10px 10px 0 var(--red); }}
    .dots {{ color:var(--red); letter-spacing:5px; }}
    code {{ display:block; margin-top:24px; font:17px/1.6 "Consolas", monospace; white-space:pre-wrap; }}
    code em {{ color:var(--acid); font-style:normal; }}
    .metrics {{ display:grid; grid-template-columns:repeat(3,1fr); border:2px solid var(--ink); background:rgba(255,255,255,.58); }}
    .metric {{ padding:20px; border-right:2px solid var(--ink); }}
    .metric:last-child {{ border-right:0; }}
    .metric strong {{ display:block; font:900 40px/1 "Consolas", monospace; }}
    .metric small {{ display:block; margin-top:8px; font-weight:700; text-transform:uppercase; letter-spacing:.06em; }}
    h2 {{ margin:28px 0 12px; font-size:20px; text-transform:uppercase; letter-spacing:.08em; }}
    .chips {{ display:flex; flex-wrap:wrap; gap:8px; }}
    .chips span {{ border:1.5px solid var(--ink); padding:7px 10px; background:var(--acid); font:700 13px/1 "Consolas", monospace; }}
    .receipt {{ border:2px solid var(--ink); background:#fffdf7; padding:20px; min-height:435px; }}
    .receipt-head {{ display:flex; justify-content:space-between; align-items:end; border-bottom:2px solid var(--ink); padding-bottom:12px; }}
    .receipt-head b {{ font:900 25px/1 "Microsoft YaHei", sans-serif; }}
    .receipt-head span {{ color:var(--red); font:800 13px/1 "Consolas", monospace; }}
    ul {{ list-style:none; margin:12px 0 0; padding:0; }}
    li {{ display:grid; grid-template-columns:40px 1fr auto; align-items:center; gap:10px; padding:11px 0; border-bottom:1px solid var(--line); font:700 15px/1.1 "Consolas", monospace; }}
    li b {{ color:var(--red); }} li i {{ font-style:normal; font-size:11px; border:1px solid var(--ink); padding:4px 6px; }}
    .route {{ display:flex; align-items:center; justify-content:space-between; margin-top:22px; font:900 14px/1 "Consolas", monospace; }}
    .route b {{ padding:11px 12px; border:2px solid var(--ink); background:var(--paper); }}
    .route span {{ color:var(--red); font-size:24px; }}
    footer {{ position:absolute; left:52px; right:52px; bottom:42px; display:flex; justify-content:space-between; align-items:center; border-top:2px solid var(--ink); padding-top:15px; font:700 13px/1.2 "Consolas", monospace; }}
    footer b {{ background:var(--acid); padding:7px 9px; }}
  </style>
</head>
<body>
<main>
  <header>
    <div><div class="eyebrow">VIBE PROJECT MIGRATOR / REAL RUN</div><h1>把“AI 写了”变成<br>“人类敢合并”</h1></div>
    <div class="stamp">READ-ONLY<br>AUDIT RECEIPT</div>
  </header>
  <section class="grid">
    <div>
      <div class="terminal"><div class="dots">● ● ●</div><code>$ python scripts/audit_project.py \\
  --root example-agent-app --format json

<em>✓ inventory complete</em>
  target writes : 0
  files inspected: {scan['files_seen']}
  profile hint  : {html.escape(profile)}</code></div>
      <h2>Detected stack</h2><div class="chips">{chips}</div>
      <h2>Evidence, not vibes</h2>
      <div class="metrics">
        <div class="metric"><strong>{scan['files_seen']}</strong><small>files read</small></div>
        <div class="metric"><strong>{len(technologies)}</strong><small>stacks</small></div>
        <div class="metric"><strong>{len(candidates)}</strong><small>review leads</small></div>
      </div>
    </div>
    <div class="receipt">
      <div class="receipt-head"><b>迁移线索</b><span>SIGNALS ≠ SCORE</span></div>
      <ul>{candidate_rows}</ul>
      <div class="route"><b>REPOSITORY</b><span>→</span><b>AUDIT</b><span>→</span><b>MINIMUM PROFILE</b><span>→</span><b>RECEIPT</b></div>
    </div>
  </section>
  <footer><span>实际调用仓库内审计代码；示例仓库在临时目录创建并在完成后销毁。</span><b>NO PRODUCT CODE CHANGED</b></footer>
</main>
</body>
</html>"""


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="vibe-migrator-readme-demo-") as directory:
        root = Path(directory) / "example-agent-app"
        build_example_repository(root)
        report = audit_project(root)
    output = Path(__file__).with_name("readme-shot.html")
    output.write_text(render_report(report), encoding="utf-8")
    print(f"Rendered real audit receipt to {output}")


if __name__ == "__main__":
    main()
