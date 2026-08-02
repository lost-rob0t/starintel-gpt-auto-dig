#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import shutil
from pathlib import Path
from urllib.parse import quote

HOST_SCRIPT = Path(__file__).with_name("auto_dig_quasar_host.js")


def shell_html(*, correction_repository: str, versions: dict[str, str]) -> str:
    version_json = json.dumps(versions, ensure_ascii=False)
    repository = html.escape(correction_repository, quote=True)
    return f"""<!doctype html>
<html lang="en" data-correction-repository="{repository}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Auto-Dig · Quasar graph editor</title>
<style>
html,body{{width:100%;height:100%;margin:0;overflow:hidden;background:#090b10}}
iframe{{display:block;width:100%;height:100%;border:0;background:#090b10}}
</style>
<script>window.AUTO_DIG_QUASAR_VERSIONS={version_json}</script>
</head>
<body>
<iframe id="quasar-frame" title="Quasar graph editor" data-src="app/index.html?host=auto-dig" sandbox="allow-scripts allow-same-origin allow-forms allow-downloads allow-popups"></iframe>
<script src="host.js"></script>
</body>
</html>"""


def graph_redirect_html(target: str) -> str:
    escaped = html.escape(target, quote=True)
    target_json = json.dumps(target)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="0;url={escaped}">
<title>Opening Quasar graph editor</title>
<script>location.replace({target_json});</script>
</head>
<body><a href="{escaped}">Open the Quasar graph editor</a></body>
</html>"""


def dataset_id_for_graph(site: Path, graph_page: Path) -> str:
    relative = graph_page.relative_to(site)
    if len(relative.parts) == 1:
        return "complete-corpus"
    return relative.parts[0]


def patch_graph_entrypoints(site: Path) -> list[Path]:
    patched: list[Path] = []
    for graph_page in site.rglob("graph.html"):
        if "quasar" in graph_page.relative_to(site).parts:
            continue
        dataset_id = dataset_id_for_graph(site, graph_page)
        shell = site / "quasar" / "index.html"
        relative_shell = os.path.relpath(shell, graph_page.parent).replace(os.sep, "/")
        target = f"{relative_shell}?dataset={quote(dataset_id, safe='._-')}"
        graph_page.write_text(graph_redirect_html(target), encoding="utf-8")
        patched.append(graph_page)
    return patched


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
        "quasar_commit": args.quasar_commit,
        "quasar_ui_commit": args.quasar_ui_commit,
        "starintel_schema_version": args.starintel_schema_version,
    }
    (output / "index.html").write_text(
        shell_html(
            correction_repository=args.correction_repository,
            versions=versions,
        ),
        encoding="utf-8",
    )
    (output / "version.json").write_text(
        json.dumps(versions, indent=2) + "\n",
        encoding="utf-8",
    )
    patch_graph_entrypoints(site)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto-dig-root", required=True)
    parser.add_argument("--quasar-dist", required=True)
    parser.add_argument("--site-dir")
    parser.add_argument("--quasar-commit", required=True)
    parser.add_argument("--quasar-ui-commit", required=True)
    parser.add_argument("--auto-dig-version", default="0.9.0")
    parser.add_argument("--starintel-schema-version", default="0.9.0")
    parser.add_argument(
        "--correction-repository",
        default="lost-rob0t/starintel-gpt-auto-dig",
    )
    return parser.parse_args()


if __name__ == "__main__":
    print(build(parse_args()))
