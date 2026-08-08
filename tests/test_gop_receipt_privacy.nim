import std/[json, os, osproc, strutils, unittest]


const PacketRoot = "digs/gop/2026-08-08-fec-individual-contributions-2026"


proc shellQuote(value: string): string =
  "'" & value.replace("'", "'\"'\"'") & "'"


proc hasForbiddenKey(node: JsonNode; forbidden: set[string]): bool =
  case node.kind
  of JObject:
    for key, value in node.pairs:
      if key.toLowerAscii() in forbidden:
        return true
      if hasForbiddenKey(value, forbidden):
        return true
  of JArray:
    for value in node.items:
      if hasForbiddenKey(value, forbidden):
        return true
  else:
    discard
  false


suite "GOP de-identified receipt privacy":
  test "manifest asserts privacy invariants":
    let manifest = parseFile(PacketRoot / "manifest.json")
    check manifest["contributor_identity_emitted"].getBool() == false
    check manifest["contributor_location_emitted"].getBool() == false
    check manifest["contributor_employment_emitted"].getBool() == false
    check manifest["raw_source_rows_embedded"].getBool() == false
    check manifest["unique_fec_sub_ids"].getInt() >= 100_000

  test "sampled canonical documents contain no contributor PII fields":
    let manifestPath = PacketRoot / "starintel-documents.jsonl.gz.b64.parts"
    var parts: seq[string]
    for raw in readFile(manifestPath).splitLines:
      let name = raw.strip()
      if name.len > 0:
        parts.add(shellQuote(PacketRoot / name))
    check parts.len > 0

    let command = "cat " & parts.join(" ") & " | base64 -d | gzip -dc | head -n 32"
    let sample = execProcess("sh", args = ["-c", command], options = {poUsePath})
    var checked = 0
    let forbidden = {
      "name", "city", "state", "zip", "zip_code", "employer", "occupation", "memo_text"
    }
    for raw in sample.splitLines:
      if raw.strip().len == 0:
        continue
      let document = parseJson(raw)
      check not hasForbiddenKey(document, forbidden)
      inc checked
    check checked >= 2
