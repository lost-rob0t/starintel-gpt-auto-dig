import std/[json, os, strutils]

const Targets = [
  "digs/anarchist-violence/2026-09-08-area-codes-b-253-256-262/starintel-documents.jsonl",
  "digs/anarchist-violence/2026-09-08-area-codes-b-274-283-301/starintel-documents.jsonl",
  "digs/anarchist-violence/2026-09-08-area-codes-b-304-307-310/starintel-documents.jsonl",
  "digs/anarchist-violence/2026-09-08-area-codes-b-304-307-310-freedom-farmers/starintel-documents.jsonl"
]

proc ensureFindings(data: JsonNode): JsonNode =
  if not data.hasKey("findings"):
    data["findings"] = newJArray()
  result = data["findings"]

proc appendFinding(data: JsonNode; kind: string; key: string) =
  if not data.hasKey(key):
    return
  let findings = ensureFindings(data)
  var finding = newJObject()
  finding["kind"] = %kind
  if key in ["codes_attempted", "hit_codes", "unresolved_leads"]:
    finding["items"] = data[key]
  else:
    finding["value"] = data[key]
  findings.add(finding)
  data.delete(key)

proc appendStats(data: JsonNode; key: string) =
  if not data.hasKey(key):
    return
  var finding = data[key]
  if finding.kind == JObject:
    finding["kind"] = %"statistics"
    ensureFindings(data).add(finding)
  data.delete(key)

proc repairPass(doc: JsonNode) =
  if doc{"dtype"}.getStr("") != "research-pass":
    return
  let data = doc["data"]

  if data.hasKey("parent_pass_id"):
    if not data.hasKey("supporting_record_ids"):
      data["supporting_record_ids"] = newJArray()
    data["supporting_record_ids"].add(data["parent_pass_id"])
    data.delete("parent_pass_id")

  appendFinding(data, "codes-attempted", "codes_attempted")
  appendFinding(data, "hit-codes", "hit_codes")
  appendStats(data, "stats")
  appendStats(data, "aggregate_stats")
  appendFinding(data, "unresolved-leads", "unresolved_leads")
  appendFinding(data, "resolution", "resolution")

  if data.hasKey("coverage_state"):
    var finding = newJObject()
    finding["kind"] = %"coverage-state-snapshot"
    finding["value"] = data["coverage_state"]
    ensureFindings(data).add(finding)
    data.delete("coverage_state")

  if data.hasKey("provenance"):
    let provenance = data["provenance"]
    if provenance.kind == JObject:
      if provenance.hasKey("collector") and not data.hasKey("agent_identity"):
        data["agent_identity"] = provenance["collector"]
      if provenance.hasKey("method") and not data.hasKey("narrative_role"):
        data["narrative_role"] = provenance["method"]
    data.delete("provenance")

proc repairFile(path: string) =
  var output: seq[string]
  for raw in lines(path):
    if raw.strip.len == 0:
      continue
    let doc = parseJson(raw)
    repairPass(doc)
    output.add($doc)
  writeFile(path, output.join("\n") & "\n")

when isMainModule:
  for path in Targets:
    if not fileExists(path):
      quit("missing packet: " & path, 2)
    repairFile(path)
