import std/[json, os, osproc, strformat, strutils, tables]


const PagesContentBudgetBytes = 700_000_000'i64


type Options = object
  buildSite: bool
  skipGitDiff: bool
  requireSources: bool
  minimums: Table[string, int]


type SiteSizeReport = object
  totalBytes: int64
  fileCount: int64
  htmlBytes: int64
  jsonBytes: int64
  jsonlBytes: int64
  orgBytes: int64
  assetsBytes: int64
  quasarBytes: int64
  downloadBytes: int64
  largestFile: string
  largestFileBytes: int64
  largestDirectory: string
  largestDirectoryBytes: int64


type BulkReport = object
  totalBytes: int64
  fileCount: int64
  canonicalCorpusBytes: int64
  shardCount: int64
  membershipCount: int64


proc run(command: string; args: seq[string] = @[]) =
  echo "+ ", command, " ", args.join(" ")
  let process = startProcess(command, args = args, options = {poParentStreams, poUsePath})
  let code = process.waitForExit()
  process.close()
  if code != 0:
    raise newException(OSError, &"{command} failed with exit code {code}")


proc slug(value: string): string =
  var previousDash = false
  for ch in value.toLowerAscii().strip():
    if ch in {'a'..'z', '0'..'9'}:
      result.add(ch)
      previousDash = false
    elif result.len > 0 and not previousDash:
      result.add('-')
      previousDash = true
  result = result.strip(chars = {'-'})


proc parseMinimum(raw: string): tuple[topic: string, count: int] =
  let separator = raw.find('=')
  if separator <= 0 or separator == raw.high:
    raise newException(ValueError, "invalid --topic-minimum; expected TOPIC=COUNT")
  result.topic = slug(raw[0 ..< separator])
  if result.topic.len == 0:
    raise newException(ValueError, "invalid empty topic in --topic-minimum")
  try:
    result.count = parseInt(raw[separator + 1 .. ^1])
  except ValueError:
    raise newException(ValueError, "invalid count in --topic-minimum: " & raw)
  if result.count < 0:
    raise newException(ValueError, "topic minimum must be nonnegative")


proc parseOptions(): Options =
  result.minimums = initTable[string, int]()
  var index = 1
  while index <= paramCount():
    let arg = paramStr(index)
    case arg
    of "--site": result.buildSite = true
    of "--skip-git-diff-check": result.skipGitDiff = true
    of "--require-sources": result.requireSources = true
    of "--topic-minimum":
      inc index
      if index > paramCount():
        raise newException(ValueError, "missing value for --topic-minimum")
      let parsed = parseMinimum(paramStr(index))
      if result.minimums.hasKey(parsed.topic) and result.minimums[parsed.topic] != parsed.count:
        raise newException(ValueError, "conflicting minimum for topic " & parsed.topic)
      result.minimums[parsed.topic] = parsed.count
    of "-h", "--help":
      echo "usage: validate-for-merge [--site] [--topic-minimum TOPIC=COUNT] [--require-sources] [--skip-git-diff-check]"
      quit(0)
    else:
      raise newException(ValueError, "unknown argument: " & arg)
    inc index
  if result.minimums.len > 0 and not result.buildSite:
    raise newException(ValueError, "--topic-minimum requires --site")


proc executable(name: string): string =
  let local = "bin" / name
  if fileExists(local): return local
  let found = findExe(name)
  if found.len > 0: return found
  raise newException(IOError, "missing compiled binary: " & name)


proc validateJavascript() =
  let node = findExe("node")
  if node.len == 0: return
  if dirExists("site-assets"):
    for path in walkDirRec("site-assets"):
      if path.endsWith(".mjs") or path.endsWith(".js"):
        run(node, @["--check", path])
  if fileExists("tests/test_graph_pathfinding.mjs"):
    run(node, @["tests/test_graph_pathfinding.mjs"])


proc validateTopics(site: string; minimums: Table[string, int]) =
  for topic, minimum in minimums.pairs:
    let path = site / ("dataset-" & topic) / "downloads" / "topic-manifest.json"
    if not fileExists(path):
      raise newException(IOError, "required topic dataset is missing: dataset-" & topic)
    let manifest = parseFile(path)
    if not manifest.hasKey("record_count") or manifest["record_count"].kind != JInt:
      raise newException(ValueError, path & ": missing integer record_count")
    let actual = manifest["record_count"].getInt()
    echo &"topic_dataset={topic} records={actual} minimum={minimum}"
    if actual < minimum:
      raise newException(ValueError, &"dataset-{topic} has {actual} records, below minimum {minimum}")


proc siteSizeReport(path: string): SiteSizeReport =
  if not dirExists(path): return
  var topLevelBytes = initTable[string, int64]()
  for item in walkDirRec(path):
    if not fileExists(item): continue
    let bytes = getFileSize(item).int64
    let rel = relativePath(item, path).replace('\\', '/')
    let topLevel = rel.split('/')[0]
    result.totalBytes += bytes
    inc result.fileCount
    topLevelBytes[topLevel] = topLevelBytes.getOrDefault(topLevel) + bytes
    if rel.endsWith(".html"): result.htmlBytes += bytes
    elif rel.endsWith(".jsonl"): result.jsonlBytes += bytes
    elif rel.endsWith(".json"): result.jsonBytes += bytes
    elif rel.endsWith(".org"): result.orgBytes += bytes
    if rel.startsWith("assets/"): result.assetsBytes += bytes
    if rel.startsWith("quasar/"): result.quasarBytes += bytes
    if rel.startsWith("downloads/") or rel.contains("/downloads/"): result.downloadBytes += bytes
    if bytes > result.largestFileBytes:
      result.largestFileBytes = bytes
      result.largestFile = rel
  for directory, bytes in topLevelBytes.pairs:
    if bytes > result.largestDirectoryBytes:
      result.largestDirectoryBytes = bytes
      result.largestDirectory = directory


proc bulkReport(path: string): BulkReport =
  if not dirExists(path): return
  for item in walkDirRec(path):
    if not fileExists(item): continue
    let bytes = getFileSize(item).int64
    let rel = relativePath(item, path).replace('\\', '/')
    result.totalBytes += bytes
    inc result.fileCount
    if rel == "starintel-complete-corpus.jsonl": result.canonicalCorpusBytes = bytes
    if rel.startsWith("corpus/") and rel.endsWith(".jsonl"): inc result.shardCount
    if rel.startsWith("memberships/") and rel.endsWith(".ids"): inc result.membershipCount


proc printReports(site: SiteSizeReport; bulk: BulkReport) =
  echo "SITE SIZE REPORT"
  echo &"total_bytes={site.totalBytes}"
  echo &"file_count={site.fileCount}"
  echo &"html_bytes={site.htmlBytes}"
  echo &"json_bytes={site.jsonBytes}"
  echo &"jsonl_bytes={site.jsonlBytes}"
  echo &"org_bytes={site.orgBytes}"
  echo &"assets_bytes={site.assetsBytes}"
  echo &"quasar_bytes={site.quasarBytes}"
  echo &"download_bytes={site.downloadBytes}"
  echo &"largest_file={site.largestFile}"
  echo &"largest_file_bytes={site.largestFileBytes}"
  echo &"largest_directory={site.largestDirectory}"
  echo &"largest_directory_bytes={site.largestDirectoryBytes}"
  echo &"canonical_corpus_bytes={bulk.canonicalCorpusBytes}"
  if bulk.canonicalCorpusBytes > 0:
    echo &"site_amplification_ratio={site.totalBytes.float / bulk.canonicalCorpusBytes.float:.4f}"
  else:
    echo "site_amplification_ratio=unavailable"
  echo &"bulk_build_bytes={bulk.totalBytes}"
  echo &"bulk_file_count={bulk.fileCount}"
  echo &"bulk_shard_count={bulk.shardCount}"
  echo &"membership_file_count={bulk.membershipCount}"
  echo &"budget={PagesContentBudgetBytes}"


proc validateSite(options: Options) =
  let site = ".generated/merge-site"
  let org = ".generated/merge-org"
  let bulk = ".generated/merge-bulk"
  for path in [site, org, bulk]:
    if dirExists(path): removeDir(path)
  createDir(".generated")
  defer:
    for path in [site, org, bulk]:
      if dirExists(path): removeDir(path)

  run(executable("starintel-site"), @[
    "--input", "digs",
    "--db", "db",
    "--output", site,
    "--org-output", org,
    "--bulk-output", bulk,
    "--bulk-base-url", "https://github.com/lost-rob0t/starintel-gpt-auto-dig/releases/download/ci"
  ])

  for required in [
    site / "index.html",
    site / "search-index.json",
    site / "indexes" / "search" / "manifest.json",
    site / "indexes" / "records" / "manifest.json",
    site / "downloads" / "starintel-complete-corpus.manifest.json",
    bulk / "starintel-complete-corpus.jsonl"
  ]:
    if not fileExists(required) or getFileSize(required) <= 0:
      raise newException(IOError, "site validation failed; missing artifact: " & required)
  if dirExists(site / "org"):
    raise newException(ValueError, "public Org tree must not be materialized inside Pages")
  for path in walkDirRec(site):
    if path.endsWith("starintel-documents.jsonl"):
      raise newException(ValueError, "duplicate per-view raw JSONL leaked into Pages: " & path)

  validateTopics(site, options.minimums)
  let siteReport = siteSizeReport(site)
  let bulkStats = bulkReport(bulk)
  printReports(siteReport, bulkStats)
  if bulkStats.shardCount < 1:
    raise newException(ValueError, "bulk corpus did not produce deterministic shards")
  if bulkStats.membershipCount < 1:
    raise newException(ValueError, "dataset membership references were not produced")
  if siteReport.totalBytes >= PagesContentBudgetBytes:
    raise newException(ValueError, &"generated site is too large for safe Pages budget: {siteReport.totalBytes} bytes")


proc main(): int =
  let options = parseOptions()
  var validateArgs = @["--root", "."]
  if options.requireSources: validateArgs.add("--require-sources")
  run(executable("starintel-validate"), validateArgs)
  validateJavascript()
  if options.buildSite: validateSite(options)
  if not options.skipGitDiff and dirExists(".git"):
    run("git", @["diff", "--check"])
  echo "MERGE GATE: PASS"
  0


when isMainModule:
  try:
    quit(main())
  except CatchableError as exc:
    stderr.writeLine("MERGE GATE: FAIL: " & exc.msg)
    quit(1)
