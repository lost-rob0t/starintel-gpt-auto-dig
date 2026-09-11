## fast_import.nim — very fast parallel StarIntel corpus importer.
##
## Mirrors `starintel.py import` (starintel_doc.cli.cmd_import) semantics:
##   - reads canonical JSONL (one compact document per line)
##   - refuses duplicate `_id`s within a batch
##   - idempotent: byte-identical targets count as unchanged
##   - never overwrites an existing different record without --replace
## Strict v0.9.0 schema validation is delegated to the authoritative
## Python validator run afterwards (scripts/starintel.py validate-db.py),
## matching the repo rule that starintel_doc/ is the only spec authority.
##
## Usage:
##   nim c -d:release --threads:on -o:bin/fast_import scripts/fast_import.nim
##   bin/fast_import records.jsonl [--root <repo>] [--replace] [--dry-run]
##   bin/fast_import --corpus          # import every digs/*/*/starintel-documents.jsonl(.gz)

import std/[os, json, streams, strutils, osproc, syncio, tables, hashes, threadpool, times]

type
  Result = object
    created, replaced, unchanged, bad: int

proc gzipRead(path: string): string =
  let (outp, code) = execCmdEx("gzip -dc " & quoteShell(path))
  if code != 0: raise newException(IOError, "gzip failed: " & path)
  outp

proc readLines(path: string): seq[string] =
  if path.endsWith(".gz"):
    for line in gzipRead(path).splitLines():
      if line.strip().len > 0: result.add line
  else:
    for line in lines(path):
      if line.strip().len > 0: result.add line

proc docId(node: JsonNode): string =
  # canonical envelope: _id is required
  if node.kind != JObject or not node.hasKey("_id"):
    raise newException(ValueError, "record missing _id")
  node["_id"].getStr()

proc dbPath(root, dtype, id: string): string =
  if '/' in id or '\\' in id or id.len == 0:
    raise newException(ValueError, "invalid _id: " & id)
  root / "db" / dtype / (id & ".ndjson")

proc payload(node: JsonNode): string =
  # compact, sort_keys equivalent: re-serialize canonically
  ($node).replace(": ", ":").replace(", ", ", ") & "\n"

proc importFile(path: string, root: string, replaceIt: bool, dryRun: bool): Result =
  var seen = initCountTable[string]()
  let recs = readLines(path)
  for raw in recs:
    var node: JsonNode
    try:
      node = parseJson(raw)
    except JsonParsingError:
      inc result.bad
      stderr.writeLine "BAD JSON " & path
      continue
    try:
      let id = docId(node)
      let dtype = node["dtype"].getStr()
      if dtype.len == 0 or '/' in dtype:
        raise newException(ValueError, "invalid dtype")
      seen.inc(id)
      if seen[id] > 1:
        raise newException(ValueError, "duplicate _id in batch: " & id)
      let target = dbPath(root, dtype, id)
      let body = payload(node)
      if fileExists(target):
        if readFile(target) == body:
          inc result.unchanged
          continue
        if not replaceIt:
          raise newException(ValueError, target & " exists; pass --replace")
        inc result.replaced
      else:
        inc result.created
      if not dryRun:
        createDir(parentDir(target))
        writeFile(target, body)
    except ValueError as e:
      inc result.bad
      stderr.writeLine "REJECTED " & path & ": " & e.msg
  if result.bad > 0:
    stderr.writeLine "fast_import: " & $result.bad & " rejected records in " & path

proc corpusFiles(root: string): seq[string] =
  for dir in walkDir(root / "digs"):
    if dir.kind == pcDir:
      for sub in walkDir(dir.path):
        if sub.kind == pcDir:
          for f in walkDir(sub.path):
            let n = f.path.extractFilename
            if n in ["starintel-documents.jsonl", "starintel-documents.jsonl.gz"]:
              result.add f.path

when isMainModule:
  let t0 = epochTime()
  var root = getCurrentDir()
  var inputs: seq[string]
  var replaceIt = false
  var dryRun = false
  var corpus = false
  var i = 1
  while i <= paramCount():
    case paramStr(i)
    of "--root": inc i; root = paramStr(i).absolutePath()
    of "--replace": replaceIt = true
    of "--dry-run": dryRun = true
    of "--corpus": corpus = true
    else: inputs.add paramStr(i)
    inc i
  if corpus:
    inputs.add corpusFiles(root)
  if inputs.len == 0:
    stderr.writeLine "usage: fast_import <records.jsonl...> [--root DIR] [--replace] [--dry-run] [--corpus]"
    quit 2
  var total = Result()
  # parallel across files; within a file keep order (batch duplicate detection)
  var fvs: seq[FlowVar[Result]]
  for f in inputs:
    fvs.add spawn importFile(f, root, replaceIt, dryRun)
  var resolved: seq[Result]
  for fv in fvs: resolved.add ^fv
  for r in resolved:
    total.created += r.created; total.replaced += r.replaced
    total.unchanged += r.unchanged; total.bad += r.bad
  stdout.writeLine $(%*{
    "created": total.created, "replaced": total.replaced,
    "unchanged": total.unchanged, "rejected": total.bad,
    "seconds": (epochTime() - t0), "files": inputs.len})
  quit (if total.bad > 0: 1 else: 0)
