# Auto-Dig pause control

Auto-Dig execution is governed by `config/auto-dig-control.json`.

All workers and executable entrypoints must fail closed when the file is missing, invalid, disabled, or paused.

Paused state:

```json
{"schema":"auto-dig-control.v1","enabled":false,"state":"paused"}
```

Running state after an explicit operator resume:

```json
{"schema":"auto-dig-control.v1","enabled":true,"state":"running"}
```

Changing backlog, schedules, issue labels, CI state, recursive research frontiers, or existing draft PRs does not implicitly resume Auto-Dig.

Current authoritative pause issue: `#2616`.
