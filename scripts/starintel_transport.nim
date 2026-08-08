import std/[algorithm, base64, os, osproc, streams, strutils, tables]


type PacketFile* = ref object
  target*: string
  run*: string
  path*: string


type LineVisitor* = proc(line: string; lineNumber: int) {.closure.}


proc transportPriority(path: string): int =
  let name = lastPathPart(path)
  if name == "starintel-documents.jsonl":
    return 0
  if name == "starintel-documents.jsonl.gz.b64":
    return 1
  if name == "starintel-documents.jsonl.gz.b64.parts":
    return 2
  99


proc isTransport*(path: string): bool =
  transportPriority(path) < 99


proc shellQuote(value: string): string =
  "'" & value.replace("'", "'\"'\"'") & "'"


proc gunzip(data: string): string =
  let temp = getTempDir() / ("starintel-transport-" & $getCurrentProcessId() & ".gz")
  writeFile(temp, data)
  defer:
    if fileExists(temp):
      removeFile(temp)
  result = execProcess("gzip", args = ["-dc", temp], options = {poUsePath})


proc readTransport*(path: string): string =
  if path.endsWith(".parts"):
    var encoded = newStringOfCap(64 * 1024 * 1024)
    for rawName in readFile(path).splitLines:
      let name = rawName.strip()
      if name.len == 0:
        continue
      encoded.add(readFile(parentDir(path) / name).strip())
    return gunzip(decode(encoded))
  if path.endsWith(".gz.b64"):
    return gunzip(decode(readFile(path)))
  readFile(path)


proc forEachTransportLine*(path: string; visitor: LineVisitor) =
  if lastPathPart(path) == "starintel-documents.jsonl":
    var input = open(path, fmRead)
    defer:
      input.close()
    var line: string
    var lineNumber = 0
    while input.readLine(line):
      inc lineNumber
      visitor(line, lineNumber)
    return

  var command = ""
  if path.endsWith(".parts"):
    var parts: seq[string]
    for rawName in readFile(path).splitLines:
      let name = rawName.strip()
      if name.len > 0:
        parts.add(shellQuote(parentDir(path) / name))
    if parts.len == 0:
      raise newException(IOError, path & ": transport manifest contains no parts")
    command = "cat " & parts.join(" ") & " | base64 -d | gzip -dc"
  elif path.endsWith(".gz.b64"):
    command = "base64 -d " & shellQuote(path) & " | gzip -dc"
  else:
    raise newException(ValueError, "unsupported StarIntel transport: " & path)

  let process = startProcess("sh", args = ["-c", command], options = {poUsePath})
  let stream = process.outputStream
  var line: string
  var lineNumber = 0
  while stream.readLine(line):
    inc lineNumber
    visitor(line, lineNumber)
  let code = process.waitForExit()
  process.close()
  if code != 0:
    raise newException(IOError, path & ": transport decode command failed with exit code " & $code)


proc packetFiles*(root: string): seq[PacketFile] =
  if not dirExists(root):
    return

  var selected = initTable[string, string]()
  for path in walkDirRec(root):
    let rel = relativePath(path, root)
    let parts = rel.split(DirSep)
    # Canonical packets live exactly at root/<target>/<run>/starintel-documents.*.
    # Generated partition shards are intentionally deeper and must never be
    # treated as independent packets.
    if parts.len != 3 or not isTransport(path):
      continue
    let packetKey = parts[0] & "\x1f" & parts[1]
    if not selected.hasKey(packetKey) or transportPriority(path) < transportPriority(selected[packetKey]):
      selected[packetKey] = path

  var paths: seq[string]
  for path in selected.values:
    paths.add(path)
  paths.sort()

  for path in paths:
    let rel = relativePath(path, root)
    let parts = rel.split(DirSep)
    result.add(PacketFile(target: parts[0], run: parts[1], path: path))


proc dbFiles*(root: string): seq[string] =
  if not dirExists(root):
    return
  for path in walkDirRec(root):
    if path.endsWith(".ndjson"):
      result.add(path)
  result.sort()
