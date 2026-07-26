from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import LANGUAGES, SPEC_VERSION
from .fixtures import all_fixtures, fixture_payload

REPORT_PATH = Path("artifacts/conformance-report.json")
DEFAULT_COMMANDS = {
    "python": f"{shlex.quote(sys.executable)} -m conformance.adapter",
}


@dataclass(frozen=True)
class AdapterResult:
    exit_code: int
    response: dict[str, Any]
    stdout: str
    stderr: str


def type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def semantic_diff(expected: Any, actual: Any, path: str = "$") -> list[dict[str, Any]]:
    expected_type = type_name(expected)
    actual_type = type_name(actual)
    if expected_type != actual_type:
        return [
            {
                "path": path,
                "kind": "type_changed",
                "expected_type": expected_type,
                "actual_type": actual_type,
                "expected": expected,
                "actual": actual,
            }
        ]
    if isinstance(expected, dict):
        changes: list[dict[str, Any]] = []
        expected_keys = set(expected)
        actual_keys = set(actual)
        for key in sorted(expected_keys - actual_keys):
            changes.append({"path": f"{path}.{key}", "kind": "removed", "expected": expected[key]})
        for key in sorted(actual_keys - expected_keys):
            changes.append({"path": f"{path}.{key}", "kind": "added", "actual": actual[key]})
        for key in sorted(expected_keys & actual_keys):
            changes.extend(semantic_diff(expected[key], actual[key], f"{path}.{key}"))
        return changes
    if isinstance(expected, list):
        changes = []
        if len(expected) != len(actual):
            changes.append(
                {
                    "path": path,
                    "kind": "array_length",
                    "expected": len(expected),
                    "actual": len(actual),
                }
            )
        for index, (left, right) in enumerate(zip(expected, actual)):
            changes.extend(semantic_diff(left, right, f"{path}[{index}]"))
        return changes
    if expected != actual:
        return [{"path": path, "kind": "value_changed", "expected": expected, "actual": actual}]
    return []


def parse_adapter_overrides(values: list[str]) -> dict[str, str]:
    commands = dict(DEFAULT_COMMANDS)
    for language in LANGUAGES:
        env_value = os.environ.get(f"STARINTEL_ADAPTER_{language.upper()}")
        if env_value:
            commands[language] = env_value
    for value in values:
        if "=" not in value:
            raise ValueError(f"adapter must use language=command: {value!r}")
        language, command = value.split("=", 1)
        if language not in LANGUAGES:
            raise ValueError(f"unknown language: {language!r}")
        commands[language] = command
    return commands


def call_adapter(command: str, request: dict[str, Any], root: Path) -> AdapterResult:
    completed = subprocess.run(
        shlex.split(command),
        input=json.dumps(request, ensure_ascii=False, separators=(",", ":")),
        text=True,
        capture_output=True,
        env={**os.environ, "STARINTEL_CONFORMANCE_ROOT": str(root)},
        check=False,
    )
    stdout = completed.stdout.strip()
    try:
        response = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        response = {"ok": False, "error": "invalid_adapter_output", "raw": stdout}
    return AdapterResult(completed.returncode, response, stdout, completed.stderr)


def adapter_probe(language: str, command: str, root: Path) -> dict[str, Any]:
    version = call_adapter(command, {"command": "version", "spec_version": SPEC_VERSION}, root)
    capabilities = call_adapter(command, {"command": "capabilities", "spec_version": SPEC_VERSION}, root)
    inventory = call_adapter(command, {"command": "schema-inventory", "spec_version": SPEC_VERSION}, root)
    ok = (
        version.exit_code == 0
        and version.response.get("spec_version") == SPEC_VERSION
        and capabilities.exit_code == 0
        and inventory.exit_code == 0
    )
    return {
        "language": language,
        "ok": ok,
        "version": version.response,
        "capabilities": capabilities.response,
        "inventory": inventory.response.get("inventory", []),
        "diagnostics": [value for value in (version.stderr, capabilities.stderr, inventory.stderr) if value],
    }


def run_suite(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    commands = parse_adapter_overrides(args.adapter)
    producers = [args.producer] if args.producer else list(LANGUAGES)
    consumers = [args.consumer] if args.consumer else list(LANGUAGES)
    required_languages = set(producers) | set(consumers)
    missing = sorted(language for language in required_languages if language not in commands)
    probed_languages = [language for language in LANGUAGES if language in commands]
    probes = {language: adapter_probe(language, commands[language], root) for language in probed_languages}

    fixture_values = all_fixtures()
    if args.fixture:
        fixture_values = [value for value in fixture_values if value["fixture_id"] == args.fixture]
        if not fixture_values:
            raise ValueError(f"fixture not found: {args.fixture}")

    pair_results: list[dict[str, Any]] = []
    for producer in producers:
        for consumer in consumers:
            pair = {"producer": producer, "consumer": consumer, "status": "pass", "failures": []}
            if producer not in commands or consumer not in commands:
                pair["status"] = "not-run"
                pair["failures"].append({"kind": "missing_adapter"})
                pair_results.append(pair)
                continue
            if not probes[producer]["ok"] or not probes[consumer]["ok"]:
                pair["status"] = "fail"
                pair["failures"].append({"kind": "adapter_probe_failed"})
                pair_results.append(pair)
                continue

            for value in fixture_values:
                if not value["expected_valid"]:
                    continue
                request = {
                    "command": "roundtrip",
                    "spec_version": value["spec_version"],
                    "document": value["document"],
                }
                produced = call_adapter(commands[producer], request, root)
                if produced.exit_code != 0 or not produced.response.get("ok"):
                    pair["status"] = "fail"
                    pair["failures"].append(
                        {
                            "fixture_id": value["fixture_id"],
                            "stage": "producer",
                            "exit_code": produced.exit_code,
                            "response": produced.response,
                            "stderr": produced.stderr,
                        }
                    )
                    continue
                consumed = call_adapter(
                    commands[consumer],
                    {**request, "document": produced.response.get("document")},
                    root,
                )
                if consumed.exit_code != 0 or not consumed.response.get("ok"):
                    pair["status"] = "fail"
                    pair["failures"].append(
                        {
                            "fixture_id": value["fixture_id"],
                            "stage": "consumer",
                            "exit_code": consumed.exit_code,
                            "response": consumed.response,
                            "stderr": consumed.stderr,
                        }
                    )
                    continue
                changes = semantic_diff(value["document"], consumed.response.get("document"))
                if changes:
                    pair["status"] = "fail"
                    pair["failures"].append(
                        {
                            "fixture_id": value["fixture_id"],
                            "stage": "compare",
                            "diff": changes,
                            "original": value["document"],
                            "produced": produced.response.get("document"),
                            "consumed": consumed.response.get("document"),
                        }
                    )
            pair_results.append(pair)

    invalid_results: list[dict[str, Any]] = []
    for language in sorted(required_languages):
        item = {"language": language, "status": "pass", "failures": []}
        if language not in commands:
            item["status"] = "not-run"
            item["failures"].append({"kind": "missing_adapter"})
            invalid_results.append(item)
            continue
        for value in fixture_values:
            if value["expected_valid"]:
                continue
            response = call_adapter(
                commands[language],
                {
                    "command": "validate",
                    "spec_version": value["spec_version"],
                    "document": value["document"],
                },
                root,
            )
            expected_exit = 3 if value["expected_error"] == "unsupported_spec_version" else 1
            if response.exit_code != expected_exit or response.response.get("error") != value["expected_error"]:
                item["status"] = "fail"
                item["failures"].append(
                    {
                        "fixture_id": value["fixture_id"],
                        "expected_error": value["expected_error"],
                        "expected_exit": expected_exit,
                        "actual_exit": response.exit_code,
                        "response": response.response,
                        "stderr": response.stderr,
                    }
                )
        invalid_results.append(item)

    inventories = {
        language: probes[language]["inventory"]
        for language in required_languages
        if language in probes and probes[language]["ok"]
    }
    inventory_failures: list[dict[str, Any]] = []
    reference_language = "python" if "python" in inventories else next(iter(sorted(inventories)), None)
    if reference_language is not None:
        reference = inventories[reference_language]
        for language, inventory in inventories.items():
            changes = semantic_diff(reference, inventory)
            if changes:
                inventory_failures.append(
                    {"reference": reference_language, "language": language, "diff": changes}
                )

    required_dtypes = {
        value["object_type"]
        for value in fixture_values
        if value["expected_valid"] and value["fixture_id"].endswith(".minimal.v1")
    }
    coverage_reference = probes.get(reference_language or "", {}).get("capabilities", {})
    coverage_missing = sorted(set(coverage_reference.get("object_types", [])) - required_dtypes)
    required_probes_ok = all(
        language in probes and probes[language]["ok"] for language in required_languages
    )
    ok = (
        not missing
        and required_probes_ok
        and all(pair["status"] == "pass" for pair in pair_results)
        and all(item["status"] == "pass" for item in invalid_results)
        and not inventory_failures
        and not coverage_missing
    )
    report = {
        "ok": ok,
        "spec_version": SPEC_VERSION,
        "languages": list(LANGUAGES),
        "required_languages": sorted(required_languages),
        "missing_adapters": missing,
        "fixtures": {
            "total": len(fixture_values),
            "valid": sum(1 for value in fixture_values if value["expected_valid"]),
            "invalid": sum(1 for value in fixture_values if not value["expected_valid"]),
            "coverage_missing": coverage_missing,
        },
        "probes": probes,
        "matrix": pair_results,
        "invalid": invalid_results,
        "schema_inventory_failures": inventory_failures,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def print_matrix(report: dict[str, Any]) -> None:
    lookup = {(item["producer"], item["consumer"]): item["status"] for item in report["matrix"]}
    print("producer\\consumer " + " ".join(f"{language:>8}" for language in LANGUAGES))
    for producer in LANGUAGES:
        print(
            f"{producer:>17} "
            + " ".join(
                f"{lookup.get((producer, consumer), 'not-run'):>8}" for consumer in LANGUAGES
            )
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="conformance")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("test", "matrix"):
        current = sub.add_parser(name)
        current.add_argument("--adapter", action="append", default=[], help="language=command")
        current.add_argument("--producer", choices=LANGUAGES)
        current.add_argument("--consumer", choices=LANGUAGES)
        current.add_argument("--fixture")
    dump = sub.add_parser("dump-fixtures")
    dump.add_argument("--output")
    report = sub.add_parser("report")
    report.add_argument("--format", choices=("json", "text"), default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "dump-fixtures":
        payload = json.dumps(fixture_payload(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            Path(args.output).write_text(payload, encoding="utf-8")
        else:
            print(payload, end="")
        return 0
    if args.command == "report":
        if not REPORT_PATH.exists():
            print("no conformance report; run `conformance test` first", file=sys.stderr)
            return 2
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        if args.format == "json":
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print_matrix(report)
            print(
                f"ok={str(report['ok']).lower()} spec={report['spec_version']} "
                f"fixtures={report['fixtures']['total']}"
            )
        return 0 if report["ok"] else 1
    report = run_suite(args)
    print_matrix(report)
    print(
        f"ok={str(report['ok']).lower()} spec={report['spec_version']} "
        f"fixtures={report['fixtures']['total']}"
    )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
