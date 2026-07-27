#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

HOST_SCRIPT = Path(__file__).with_name("auto_dig_quasar_host.js")


def shell_html(*, correction_repository: str, versions: dict[str, str]) -> str:
    version_json = json.dumps(versions, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="en" data-correction-repository="{correction_repository}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Auto-Dig · Quasar</title>
<style>
:root{{color-scheme:dark;background:#090b10;color:#eef1f7;font:15px system-ui,sans-serif}}*{{box-sizing:border-box}}body{{margin:0;display:grid;grid-template-rows:auto 1fr;height:100vh}}header{{display:flex;align-items:center;gap:.6rem;padding:.55rem .8rem;border-bottom:1px solid #29303d;background:#11151d}}header strong{{margin-right:auto}}button,a{{border:1px solid #394253;background:#171d28;color:inherit;border-radius:.5rem;padding:.45rem .7rem;text-decoration:none}}iframe{{width:100%;height:100%;border:0;background:#090b10}}.version{{font-size:.72rem;opacity:.65}}
</style>
<script>window.AUTO_DIG_QUASAR_VERSIONS={version_json}</script>
</head>
<body>
<header>
<strong>Auto-Dig</strong>
<a href="../index.html">Research</a>
<button data-quasar-route="/graph">Graph</button>
<button data-quasar-route="/documents">Documents</button>
<button data-quasar-route="/agents">Actors</button>
<button data-quasar-route="/tipline">Tipline</button>
<span class="version" title="{version_json}">fork {versions['quasar_fork_commit'][:8]} · upstream {versions['quasar_upstream_commit'][:8]}</span>
</header>
<iframe id="quasar-frame" title="Quasar" src="app/index.html" sandbox="allow-scripts allow-same-origin allow-forms allow-downloads allow-popups"></iframe>
<script src="host.js"></script>
</body></html>"""


def patch_navigation(site: Path) -> None:
    marker = '<a data-auto-dig-quasar="true"'
    for page in site.rglob("*.html"):
        if "quasar" in page.relative_to(site).parts:
            continue
        text = page.read_text(encoding="utf-8")
        if marker in text or "</nav>" not in text:
            continue
        relative = page.relative_to(site)
        depth = len(relative.parts) - 1
        prefix = "../" * depth
        dataset = relative.parts[0] if depth else "complete-corpus"
        link = f'{marker} href="{prefix}quasar/index.html?dataset={dataset}">Quasar</a>'
        page.write_text(text.replace("</nav>", link + "</nav>", 1), encoding="utf-8")


def build(args: argparse.Namespace) -> Path:
    root = Path(args.auto_dig_root).resolve()
    site = Path(args.site_dir).resolve() if args.site_dir else root / "site"
    quasar_dist = Path(args.quasar_dist).resolve()
    if not quasar_dist.joinpath("index.html").exists():
        raise SystemExit(f"Quasar dist is missing index.html: {quasar_dist}")
    output = site / "quasar"
    app = output / "app"
    if output.exists():
        shutil.rmtree(output)
    app.mkdir(parents=True)
    shutil.copytree(quasar_dist, app, dirs_exist_ok=True)
    shutil.copy2(HOST_SCRIPT, output / "host.js")
    versions = {
        "auto_dig_version": args.auto_dig_version,
        "quasar_fork_commit": args.quasar_fork_commit,
        "quasar_upstream_commit": args.quasar_upstream_commit,
        "starintel_schema_version": args.starintel_schema_version,
    }
    (output / "index.html").write_text(shell_html(correction_repository=args.correction_repository, versions=versions), encoding="utf-8")
    (output / "version.json").write_text(json.dumps(versions, indent=2) + "\n", encoding="utf-8")
    (root / "quasar-fork.lock.json").write_text(json.dumps(versions, indent=2) + "\n", encoding="utf-8")
    patch_navigation(site)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto-dig-root", required=True)
    parser.add_argument("--quasar-dist", required=True)
    parser.add_argument("--site-dir")
    parser.add_argument("--quasar-fork-commit", required=True)
    parser.add_argument("--quasar-upstream-commit", required=True)
    parser.add_argument("--auto-dig-version", default="0.9.0")
    parser.add_argument("--starintel-schema-version", default="0.9.0")
    parser.add_argument("--correction-repository", default="lost-rob0t/starintel-gpt-auto-dig")
    return parser.parse_args()


if __name__ == "__main__":
    print(build(parse_args()))
