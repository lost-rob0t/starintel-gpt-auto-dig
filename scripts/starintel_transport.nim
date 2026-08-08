import std/[base64, os, osproc, strutils, tables, algorithm]


type PacketFile* = object
  target*: string
  run*: string
  path*: string


proc transportPriority(path: string): int =
  if path.endsWith("starintel-documents.jsonl"):
    return 0
  if path.endsWith("starintel-documents.jsonl.gz.b64"):
    return 1
  if path.endsWith("starintel-documents.jsonl.gz.b64.parts"):
    return 2
  99


proc isTransport*(path: string): bool =
  transportPriority(path) < 99


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


proc packetFiles*(root: string): seq[PacketFile] =
  if not dirExists(root):
    return

  var selected = initTable[string, string]()
  for path in walkDirRec(root):
    if not isTransport(path):
      continue
    let directory = parentDir(path)
    if not selected.hasKey(directory) or transportPriority(path) < transportPriority(selected[directory]):
      selected[directory] = path

  var paths = newSeq[string]()
  for path in selected.values:
    paths.add(path)
  paths.sort()

  for path in paths:
    let rel = relativePath(path, root)
    let parts = rel.split(DirSep)
    if parts.len < 3:
      continue
    result.add(PacketFile(target: parts[0], run: parts[1], path: path))


proc dbFiles*(root: string): seq[string] =
  if not dirExists(root):
    return
  for path in walkDirRec(root):
    if path.endsWith(".ndjson"):
      result.add(path)
  result.sort()
