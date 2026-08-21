import std/[os, strutils, unittest]

import ../scripts/starintel_transport


suite "StarIntel Nim transport discovery":
  test "only canonical packet-root transports are discovered":
    let root = getTempDir() / ("starintel-transport-test-" & $getCurrentProcessId())
    if dirExists(root):
      removeDir(root)
    defer:
      if dirExists(root):
        removeDir(root)

    let packet = root / "gop" / "run-1"
    let shard = packet / "part-00"
    createDir(shard)
    writeFile(packet / "starintel-documents.jsonl", "{\"_id\":\"canonical\"}\n")
    writeFile(shard / "starintel-documents.jsonl", "{\"_id\":\"shard\"}\n")

    let found = packetFiles(root)
    check found.len == 1
    check found[0].target == "gop"
    check found[0].run == "run-1"
    check found[0].path.endsWith("gop" / "run-1" / "starintel-documents.jsonl")

  test "plain transport wins over encoded alternatives":
    let root = getTempDir() / ("starintel-transport-priority-" & $getCurrentProcessId())
    if dirExists(root):
      removeDir(root)
    defer:
      if dirExists(root):
        removeDir(root)

    let packet = root / "gop" / "run-2"
    createDir(packet)
    writeFile(packet / "starintel-documents.jsonl.gz.b64", "unused")
    writeFile(packet / "starintel-documents.jsonl", "{\"_id\":\"plain\"}\n")

    let found = packetFiles(root)
    check found.len == 1
    check lastPathPart(found[0].path) == "starintel-documents.jsonl"
