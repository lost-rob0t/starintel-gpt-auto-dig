"""Offline launcher contract plus real canonical builder smoke tests."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="launcher with spaces ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ("scripts", "docs", "config", "bin"):
            (self.root / folder).mkdir()
        for name in ("scripts/opencode-auto-dig.py", "docs/opencode-auto-dig-task.md", "opencode.jsonc"):
            shutil.copyfile(ROOT / name, self.root / name)
        self.control = {"schema": "auto-dig-control.v1", "enabled": True, "state": "running"}
        self.write_control()
        (self.root / "scripts/schema-release.py").write_text(
            "import os,sys\nsys.exit(int(os.environ.get('SCHEMA_EXIT', '0')))\n")
        self.capture = self.root / "capture.json"
        fake = self.root / "bin/opencode"
        fake.write_text(f"#!{sys.executable}\n" +
                       "import json,os,sys\nfrom pathlib import Path\n"
                       "Path(os.environ['CAPTURE']).write_text(json.dumps({'argv':sys.argv[1:], 'cwd':os.getcwd(), 'key_present':bool(os.environ.get('BRAVE_API_KEY'))}))\n"
                       "if os.environ.get('FAKE_SIGNAL'): os.kill(os.getpid(), 15)\n"
                       "sys.exit(int(os.environ.get('FAKE_EXIT', '0')))\n")
        fake.chmod(0o755)
        for name in ("npx", "nimble"):
            (self.root / "bin" / name).symlink_to(fake)
        self.env = {**os.environ, "PATH": str(self.root / "bin"), "BRAVE_API_KEY": "sentinel-secret",
                    "CAPTURE": str(self.capture)}

    def write_control(self):
        (self.root / "config/auto-dig-control.json").write_text(json.dumps(self.control))

    def run_launcher(self, *args):
        return subprocess.run([sys.executable, str(self.root / "scripts/opencode-auto-dig.py"), *args],
                              cwd="/tmp", env=self.env, capture_output=True, text=True)

    def test_dry_run_needs_no_tools_or_credentials_and_does_not_leak(self):
        self.env["PATH"] = ""
        result = self.run_launcher("--task", "Review synthetic fixtures", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(plan["cwd"], str(self.root))
        self.assertFalse(self.capture.exists())
        self.assertNotIn("sentinel-secret", result.stdout + result.stderr)

    def test_task_file_model_cwd_and_shell_metacharacters(self):
        task = self.root / "task file.txt"
        task.write_text("--flag $(touch NEVER) `echo no`\nsecond line")
        result = self.run_launcher("--task-file", str(task), "--model", "provider/model")
        self.assertEqual(result.returncode, 0, result.stderr)
        got = json.loads(self.capture.read_text())
        self.assertEqual(got["argv"][:4], ["run", "--model", "provider/model", "--"])
        self.assertIn(task.read_text(), got["argv"][4])
        self.assertIn("--fields @fields.json", got["argv"][4])
        self.assertIn("bin/validate-for-merge --site", got["argv"][4])
        self.assertEqual(got["cwd"], str(self.root))
        self.assertTrue(got["key_present"])
        self.assertFalse((self.root / "NEVER").exists())

    def test_exit_status_propagates(self):
        self.env["FAKE_EXIT"] = "42"
        self.assertEqual(self.run_launcher("--task", "fixture").returncode, 42)

    def test_signal_exit_propagates(self):
        self.env["FAKE_SIGNAL"] = "1"
        self.assertEqual(self.run_launcher("--task", "fixture").returncode, 143)

    def test_schema_failure_prevents_launch(self):
        self.env["SCHEMA_EXIT"] = "19"
        self.assertEqual(self.run_launcher("--task", "fixture").returncode, 19)
        self.assertFalse(self.capture.exists())

    def test_control_fails_closed_even_with_environment_override(self):
        self.env["AUTO_DIG_CONTROL_FILE"] = "/tmp/not-the-control-file"
        for change in ({"enabled": False}, {"state": "paused"}, {"allow_new_passes": False},
                       {"allow_new_claims": False}, {"enabled": "true"}):
            with self.subTest(change=change):
                original = self.control.copy()
                self.control.update(change)
                self.write_control()
                self.assertEqual(self.run_launcher("--task", "fixture").returncode, 75)
                self.control = original
        for content in ("null", "[]", "{", "{}"):
            (self.root / "config/auto-dig-control.json").write_text(content)
            self.assertEqual(self.run_launcher("--task", "fixture", "--dry-run").returncode, 2)
        (self.root / "config/auto-dig-control.json").unlink()
        self.assertEqual(self.run_launcher("--task", "fixture").returncode, 2)
        self.assertFalse(self.capture.exists())

    def test_missing_prerequisites_and_invalid_task(self):
        self.assertEqual(self.run_launcher("--task", " ").returncode, 2)
        self.assertEqual(self.run_launcher("--task-file", "/does-not-exist").returncode, 2)
        self.assertEqual(self.run_launcher("--task", "x", "--opencode", "not-installed").returncode, 127)
        self.env.pop("BRAVE_API_KEY")
        self.assertEqual(self.run_launcher("--task", "fixture").returncode, 2)
        self.assertFalse(self.capture.exists())


class TargetTests(unittest.TestCase):
    def test_mixed_formats_and_malformed_records(self):
        selector = load_script("random-targets")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            records = [
                {"id": "canonical-open", "schemaVersion": "0.10.1", "dtype": "target", "state": "pending", "target": "synthetic", "targetType": "org"},
                {"id": "canonical-done", "dtype": "target", "state": "completed", "data": {"status": "open"}},
                {"id": "flat-status-done", "dtype": "investigation-target", "status": "DONE"},
                {"_id": "legacy-open", "dtype": "investigation-target", "data": {"status": "open", "research_question": "synthetic question", "target_id": "org-id"}},
                {"_id": "legacy-done", "dtype": "target", "data": {"status": " Resolved "}},
                {"dtype": "target", "data": {}},
                {"id": None, "_id": "do-not-fallback", "dtype": "target"},
                {"_id": "bad-data", "dtype": "target", "data": []},
            ]
            for i, record in enumerate(records):
                path = root / "db" / record["dtype"] / f"{i}.ndjson"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(record))
            for name, raw in (("array", "[]"), ("broken", "{")):
                (root / "db/target" / f"{name}.ndjson").write_text(raw)
            found = {doc["_id"]: doc for doc in selector.iter_unresolved(root)}
            self.assertEqual(set(found), {"canonical-open", "legacy-open"})
            self.assertEqual(found["canonical-open"]["target_type"], "org")
            self.assertEqual(found["legacy-open"]["research_question"], "synthetic question")
            for output in (root / "one/queue.jsonl", root / "two/queue.jsonl"):
                result = subprocess.run([sys.executable, str(ROOT / "scripts/random-targets.py"), "--root", temp,
                                         "--count", "10", "--assign", "2", "--seed", "7", "--output", str(output)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root / "one/queue.jsonl").read_bytes(), (root / "two/queue.jsonl").read_bytes())
            self.assertEqual({d["worker"] for d in map(json.loads, (root / "one/queue.jsonl").read_text().splitlines())}, {1, 2})


class CanonicalBuilderSmokeTests(unittest.TestCase):
    def test_writer_create_import_search_and_completed_target(self):
        from starintel_doc.canonical import validate_document
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fields = root / "fields.json"
            fields.write_text(json.dumps({"actor": "fixture", "target": "synthetic", "state": "completed"}))
            result = subprocess.run([sys.executable, str(ROOT / "scripts/create-db-document.py"), "target",
                                     "--dataset", "launcher-test", "--id", "starintel:target:fixture",
                                     "--fields", "@" + str(fields), "--root", temp], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            document = json.loads((root / "db/target/starintel:target:fixture.ndjson").read_text())
            validate_document(document)
            self.assertNotIn("_id", document)
            self.assertEqual(list(load_script("random-targets").iter_unresolved(root)), [])
            draft = root / "draft.jsonl"
            result = subprocess.run([sys.executable, str(ROOT / "scripts/starintel.py"), "create", "org",
                                     "--dataset", "launcher-test", "--id", "starintel:org:fixture",
                                     "--fields", '{"name":"Synthetic launcher fixture"}', "--output", str(draft)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([sys.executable, str(ROOT / "scripts/starintel.py"), "import", str(draft), "--root", temp], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([sys.executable, str(ROOT / "scripts/starintel.py"), "search", "Synthetic launcher fixture", "--root", temp, "--with-location"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("starintel:org:fixture", result.stdout)


if __name__ == "__main__":
    unittest.main()
