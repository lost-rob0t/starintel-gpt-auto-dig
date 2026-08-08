import std/[algorithm, json, os, sequtils, strutils, tables]

type
  GroupKey = tuple[target: string, dataset: string]

proc fail(message: string): void =
  stderr.writeLine("error: " & message)
  quit(1)

proc slug(value: string): string =
  var text = value.strip.toLowerAscii
  if text.startsWith("starintel:"):
    text = text[10 .. ^1]

  var dashPending = false
  for ch in text:
    if ch in {'a' .. 'z', '0' .. '9'}:
      if dashPending and result.len > 0:
        result.add('-')
      result.add(ch)
      dashPending = false
    elif result.len > 0:
      dashPending = true

  if result.len == 0:
    result = "record"

proc isYearSuffix(value: string, start: int): bool =
  start >= 0 and
    start + 4 == value.len and
    value[start] == '2' and value[start + 1] == '0' and
    value[start + 2] in {'0' .. '9'} and value[start + 3] in {'0' .. '9'}

proc twoDigits(value: string, start: int): bool =
  start >= 0 and start + 1 < value.len and
    value[start] in {'0' .. '9'} and value[start + 1] in {'0' .. '9'}

proc stripDateSuffix(value: string): string =
  if value.len >= 11:
    let start = value.len - 10
    if value[start - 1] == '-' and
       isYearSuffix(value[start ..< start + 4], 0) and
       value[start + 4] == '-' and twoDigits(value, start + 5) and
       value[start + 7] == '-' and twoDigits(value, start + 8):
      return value[0 ..< start - 1]

  if value.len >= 5:
    let start = value.len - 4
    if value[start - 1] == '-' and isYearSuffix(value[start .. ^1], 0):
      return value[0 ..< start - 1]

  value

proc loadMappings(configPath: string): Table[string, string] =
  result = initTable[string, string]()
  if not fileExists(configPath):
    return

  let config = parseFile(configPath)
  if config.kind != JObject or not config.hasKey("database_targets"):
    return

  let mappings = config["database_targets"]
  if mappings.kind != JObject:
    fail("site-config.json: database_targets must be an object")

  for key, value in mappings.pairs:
    if value.kind != JString:
      fail("site-config.json: database_targets values must be strings")
    result[key] = value.getStr

proc inferTarget(dataset: string, mappings: Table[string, string]): string =
  if mappings.hasKey(dataset):
    return slug(mappings[dataset])
  result = slug(stripDateSuffix(slug(dataset)))

proc readDocument(path: string): JsonNode =
  var record = ""
  for candidate in readFile(path).splitLines:
    if candidate.strip.len == 0:
      continue
    if record.len > 0:
      fail(path & ": expected exactly one non-empty NDJSON line")
    record = candidate

  if record.len == 0:
    fail(path & ": empty NDJSON record")

  try:
    result = parseJson(record)
  except JsonParsingError as error:
    fail(path & ": invalid JSON: " & error.msg)

  if result.kind != JObject:
    fail(path & ": expected JSON object")
  if not result.hasKey("_id") or result["_id"].kind != JString:
    fail(path & ": missing string _id")

proc datasetOf(document: JsonNode): string =
  if document.hasKey("dataset") and document["dataset"].kind == JString:
    let value = document["dataset"].getStr
    if value.len > 0:
      return value
  "database"

proc parseArgs(): tuple[dbRoot, workspace, configPath: string] =
  result = ("db", ".generated/site-input", "site-config.json")
  var index = 1
  while index <= paramCount():
    let argument = paramStr(index)
    if argument notin ["--db", "--workspace", "--config"]:
      fail("unknown argument: " & argument)
    if index == paramCount():
      fail("missing value for " & argument)
    inc index
    let value = paramStr(index)
    case argument
    of "--db": result.dbRoot = value
    of "--workspace": result.workspace = value
    of "--config": result.configPath = value
    else: discard
    inc index

proc main() =
  let args = parseArgs()
  let mappings = loadMappings(args.configPath)
  var grouped = initTable[GroupKey, seq[JsonNode]]()
  var documents = 0

  if dirExists(args.dbRoot):
    for path in walkDirRec(args.dbRoot):
      if not path.endsWith(".ndjson"):
        continue
      let document = readDocument(path)
      let dataset = datasetOf(document)
      let key = (inferTarget(dataset, mappings), slug(dataset))
      if not grouped.hasKey(key):
        grouped[key] = @[]
      grouped[key].add(document)
      inc documents

  var keys = toSeq(grouped.keys)
  keys.sort(proc(a, b: GroupKey): int =
    let targetOrder = cmp(a.target, b.target)
    if targetOrder != 0: targetOrder else: cmp(a.dataset, b.dataset)
  )

  for key in keys:
    var records = grouped[key]
    records.sort(proc(a, b: JsonNode): int = cmp(a["_id"].getStr, b["_id"].getStr))
    let directory = args.workspace / key.target / ("db-" & key.dataset)
    createDir(directory)
    let packet = directory / "starintel-documents.jsonl"
    var output = open(packet, fmWrite)
    try:
      for document in records:
        output.write($document)
        output.write('\n')
    finally:
      output.close()

  stdout.writeLine("nim-site-materializer documents=" & $documents & " groups=" & $grouped.len)

when isMainModule:
  main()
