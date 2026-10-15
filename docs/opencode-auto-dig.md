# OpenCode Auto-Dig launcher

Run one explicit, bounded task from any working directory:

```sh
python3 /path/to/repo/scripts/opencode-auto-dig.py \
  --task 'Review the public documentation for <subject>; stop after one pass.' --dry-run
python3 /path/to/repo/scripts/opencode-auto-dig.py \
  --task-file /path/to/task.txt --model provider/model
```

`--task` and `--task-file` are mutually exclusive. `--model` is optional;
OpenCode otherwise uses its configured default. `--opencode /path/to/opencode`
selects an executable, never a shell expression. The launcher runs from the
repository root, supplies [current task instructions](opencode-auto-dig-task.md),
and uses the project `opencode.jsonc` for pinned Brave search and fetch MCP tools.
Local corpus search, schema inspection, canonical builders and validation use
OpenCode's ordinary shell tool. No legacy corpus MCP adapter is required.
Relative executable paths resolve against the caller's directory before launch.
The child receives an absolute `--dir` and matching `PWD` so an inherited caller
directory cannot select another OpenCode project. Standard input is closed;
use `--task` or `--task-file` rather than piping additional task content.

## Prerequisites

- Python 3.11+ with this repository's pinned Python dependency from
  `schema/starintel-runtime.lock.json` installed in the active environment.
- The pinned Nim runtime checked out at `.starintel-doc-nim`, Nim 2.2.4 and
  `nimble` on PATH, plus PCRE as in `.github/workflows/validate-db.yml`.
- OpenCode on PATH (or `--opencode`), Node.js/npm with `npx`, and access to the
  pinned MCP packages in `opencode.jsonc`.
- `BRAVE_API_KEY` supplied by the calling environment, and existing OpenCode
  provider authentication or provider environment credentials. The launcher
  neither configures credentials nor prints environment values. Do not put
  secrets in task text, command arguments, or committed files.

The launcher checks control state, executable availability, the Brave key, and
the pinned generated schema/runtime consistency before starting OpenCode. It
uses the invoking Python's directory on the child's PATH so shell commands use
the active Python environment. Provider access and MCP availability are checked
by OpenCode at runtime; no paid model probe or research request is made during
preflight. Existing OpenCode user settings and runtime overrides still apply;
review them before a live task. This wrapper is not a sandbox or an authorization
boundary for agent tools.

Compatibility was checked with OpenCode **1.19.0** using `run --help` and
`debug config` (no model run). The project config follows the current
[MCP server format](https://opencode.ai/docs/mcp-servers/): named entries directly
under `mcp` and numeric timeouts. The invocation uses documented
[`opencode run`](https://opencode.ai/docs/cli/) with a single literal message and
optional `--model`. It does not grant blanket permission overrides.

## Behavior and validation

`--dry-run` prints JSON containing the working directory, literal argument array,
config path, and prerequisite names. It checks the control file and reads task
instructions but starts no subprocess, installs nothing, and writes no files.
It works without OpenCode, API keys, or the schema runtime installed. Task text
appears in the plan, so keep it free of secrets.

Paused control state returns 75. Invalid inputs or missing credentials return 2;
missing executables return 127. Preflight and OpenCode failures propagate their
exit status; a signal exit becomes 128 + signal, and interruption returns 130.
An OpenCode exit of zero alone is not evidence of successful research: inspect
its report and run the full gate before readiness or merge:

```sh
python3 -m unittest tests.test_opencode_launcher -v
nimble buildFast
bin/validate-for-merge --site
```

The launcher does not schedule work, select or claim targets, manage concurrent
writers, publish branches, or merge. Operators must coordinate target ownership.
`scripts/random-targets.py` remains a separate seeded sampler; it reads canonical
flat `id`/`state` and legacy `_id`/`data.status`. Its queue keeps `_id` as the
compatibility key for either source identity and excludes completed/resolved/done
records. Sampling is not a claim and does not change target state.

Canonical wire documents use flat fields and the generated type registry.
`target` is canonical; `investigation-target` and the old recursive selector are
historical research interfaces. Inspect `starintel.py types` and `schema` before
building; do not copy nested examples from older skills. The offline tests use
a fake OpenCode executable and temporary synthetic corpora, including real
canonical create, transactional write/import, search, and target-state checks.
