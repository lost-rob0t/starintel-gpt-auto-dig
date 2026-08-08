import std/[algorithm, json, os, osproc, sets, strformat, strutils, tables, uri]

import starintel_transport


const
  GraphDocumentLimit = 50_000
  NodePageLimit = 50_000


type Record = ref object
  # Raw canonical JSON is retained. Parsed trees are deliberately discarded
  # after indexing and recreated only for the small subset rendered as pages.
  raw: string
  target: string
  run: string
  path: string
  id: string
  dtype: string
  dataset: string
  title: string
  summary: string
  updated: string
  schemaVersion: string
  status: string
  sourceKeys: seq[string]


type Bucket = ref object
  docs: Table[string, Record]
  orderedIds: seq[string]
  orderDirty: bool


type TopicRule = object
  id: string
  title: string
  subtitle: string
  targets: seq[string]
  datasets: seq[string]
  terms: seq[string]


type TopicConfig = object
  rules: seq[TopicRule]
  excludedDatasets: HashSet[string]


type SiteConfig = object
  title: string
  excludedIds: HashSet[string]
  databaseTargets: Table[string, string]
  packetTitles: Table[string, string]
  packetSubtitles: Table[string, string]


proc ensureDir(path: string) =
  if not dirExists(path):
    createDir(path)


proc cleanDir(path: string) =
  if dirExists(path):
    removeDir(path)
  createDir(path)


proc slug(value: string): string =
  var source = value.toLowerAscii().strip()
  if source.startsWith("starintel:") and source.len > 10:
    source = source[10 .. ^1]
  var previousDash = false
  for ch in source:
    if ch in {'a'..'z', '0'..'9'}:
      result.add(ch)
      previousDash = false
    elif result.len > 0 and not previousDash:
      result.add('-')
      previousDash = true
  result = result.strip(chars = {'-'})
  if result.len == 0:
    result = "record"


proc htmlEscape(value: string): string =
  result = newStringOfCap(value.len + 16)
  for ch in value:
    case ch
    of '&': result.add("&amp;")
    of '<': result.add("&lt;")
    of '>': result.add("&gt;")
    of '"': result.add("&quot;")
    of '\'': result.add("&#39;")
    else: result.add(ch)


proc jsonText(node: JsonNode; key: string; fallback = ""): string =
  if node != nil and node.kind == JObject and node.hasKey(key) and node[key].kind == JString:
    return node[key].getStr()
  fallback


proc nestedText(node: JsonNode; parent, key: string; fallback = ""): string =
  if node != nil and node.kind == JObject and node.hasKey(parent) and node[parent].kind == JObject:
    return jsonText(node[parent], key, fallback)
  fallback


proc recordSummary(node: JsonNode): string =
  result = jsonText(node, "summary")
  if result.len == 0:
    result = jsonText(node, "description")
  if result.len == 0 and node.hasKey("data") and node["data"].kind == JObject:
    for key in ["description", "definition", "claim", "bio", "business", "mission"]:
      result = jsonText(node["data"], key)
      if result.len > 0:
        break
  if result.len == 0:
    result = jsonText(node, "title", jsonText(node, "_id"))


proc displayTitle(node: JsonNode): string =
  result = jsonText(node, "title")
  if result.len == 0 and node.hasKey("data") and node["data"].kind == JObject:
    for key in ["display_name", "name", "full_name"]:
      result = jsonText(node["data"], key)
      if result.len > 0:
        break
  if result.len == 0:
    result = jsonText(node, "_id")


proc graphEligible(dtype: string): bool =
  dtype in [
    "person", "org", "relation", "event", "claim", "analysis", "concept",
    "education", "employment"
  ]


proc sourceKey(source: JsonNode): string =
  case source.kind
  of JString:
    result = source.getStr().strip()
  of JObject:
    for key in ["source_id", "uri", "url"]:
      if source.hasKey(key) and source[key].kind == JString:
        let value = source[key].getStr().strip()
        if value.len > 0:
          return value
    result = $source
  else:
    result = $source


proc extractSourceKeys(document: JsonNode): seq[string] =
  if not document.hasKey("sources") or document["sources"].kind != JArray:
    return
  for source in document["sources"].items:
    let key = sourceKey(source)
    if key.len > 0 and key notin result:
      result.add(key)


proc newBucket(): Bucket =
  Bucket(
    docs: initTable[string, Record](),
    orderedIds: @[],
    orderDirty: true
  )


proc getBucket(buckets: var Table[string, Bucket]; key: string): Bucket =
  if not buckets.hasKey(key):
    buckets[key] = newBucket()
  buckets[key]


proc putLatest(bucket: Bucket; record: Record) =
  let exists = bucket.docs.hasKey(record.id)
  if not exists or record.updated >= bucket.docs[record.id].updated:
    bucket.docs[record.id] = record
    if not exists:
      bucket.orderDirty = true


proc sortedIds(bucket: Bucket): seq[string] =
  if bucket.orderDirty:
    bucket.orderedIds.setLen(0)
    for id in bucket.docs.keys:
      bucket.orderedIds.add(id)
    bucket.orderedIds.sort()
    bucket.orderDirty = false
  result = bucket.orderedIds


proc sortedSet(values: HashSet[string]): seq[string] =
  for value in values:
    result.add(value)
  result.sort()


proc jsonStrings(values: seq[string]): JsonNode =
  result = newJArray()
  for value in values:
    result.add(%value)


proc stringList(node: JsonNode): seq[string] =
  if node.kind != JArray:
    return
  for item in node.items:
    if item.kind == JString:
      result.add(item.getStr())


proc emptySiteConfig(title = "StarIntel GPT Auto Dig"): SiteConfig =
  result.title = title
  result.excludedIds = initHashSet[string]()
  result.databaseTargets = initTable[string, string]()
  result.packetTitles = initTable[string, string]()
  result.packetSubtitles = initTable[string, string]()


proc topicSiteConfig(target, title, subtitle: string): SiteConfig =
  result = emptySiteConfig(title)
  result.packetTitles[target] = title
  result.packetSubtitles[target] = subtitle


proc loadSiteConfig(path: string): SiteConfig =
  result = emptySiteConfig()
  if not fileExists(path):
    return
  let root = parseFile(path)
  result.title = jsonText(root, "site_title", result.title)
  if root.hasKey("excluded_document_ids") and root["excluded_document_ids"].kind == JArray:
    for item in root["excluded_document_ids"].items:
      if item.kind == JString:
        result.excludedIds.incl(item.getStr())
  if root.hasKey("database_targets") and root["database_targets"].kind == JObject:
    for key, value in root["database_targets"].pairs:
      if value.kind == JString:
        result.databaseTargets[key] = slug(value.getStr())
  if root.hasKey("packets") and root["packets"].kind == JObject:
    for key, value in root["packets"].pairs:
      if value.kind != JObject:
        continue
      result.packetTitles[key] = jsonText(value, "title", key.replace("-", " "))
      result.packetSubtitles[key] = jsonText(value, "subtitle", "StarIntel public-record research")


proc loadTopicConfig(path: string): TopicConfig =
  result.excludedDatasets = initHashSet[string]()
  result.excludedDatasets.incl("daily")
  if not fileExists(path):
    return
  let root = parseFile(path)
  if root.hasKey("excluded_source_datasets"):
    for item in stringList(root["excluded_source_datasets"]):
      result.excludedDatasets.incl(slug(item))
  if not root.hasKey("topics") or root["topics"].kind != JArray:
    return
  for item in root["topics"].items:
    if item.kind != JObject:
      continue
    var rule: TopicRule
    rule.id = slug(jsonText(item, "id"))
    if rule.id.len == 0:
      continue
    rule.title = jsonText(item, "title", rule.id.replace("-", " "))
    rule.subtitle = jsonText(item, "subtitle", "Merged topical dataset for " & rule.id)
    if item.hasKey("match") and item["match"].kind == JObject:
      let matcher = item["match"]
      if matcher.hasKey("targets"):
        for value in stringList(matcher["targets"]):
          rule.targets.add(slug(value))
      if matcher.hasKey("datasets"):
        for value in stringList(matcher["datasets"]):
          rule.datasets.add(slug(value))
      if matcher.hasKey("terms"):
        for value in stringList(matcher["terms"]):
          rule.terms.add(value.toLowerAscii().strip())
    result.rules.add(rule)


proc inferDbTarget(dataset: string; config: SiteConfig): string =
  if config.databaseTargets.hasKey(dataset):
    return config.databaseTargets[dataset]
  result = slug(dataset)


proc makeRecord(document: JsonNode; raw, target, run, path: string): Record =
  let status = nestedText(
    document,
    "verification",
    "status",
    jsonText(document, "status", "recorded")
  )
  Record(
    raw: raw,
    target: target,
    run: run,
    path: path,
    id: jsonText(document, "_id"),
    dtype: jsonText(document, "dtype"),
    dataset: jsonText(document, "dataset"),
    title: displayTitle(document),
    summary: recordSummary(document),
    updated: jsonText(document, "date_updated"),
    schemaVersion: jsonText(document, "schema_version"),
    status: status,
    sourceKeys: extractSourceKeys(document)
  )


proc addRecord(targets: var Table[string, Bucket]; complete: Bucket; record: Record; config: SiteConfig) =
  if record.id.len == 0 or record.id in config.excludedIds:
    return
  putLatest(getBucket(targets, record.target), record)
  putLatest(complete, record)


proc scanCorpus(inputRoot, dbRoot: string; config: SiteConfig): tuple[targets: Table[string, Bucket], complete: Bucket] =
  var targets = initTable[string, Bucket]()
  let complete = newBucket()

  for packet in packetFiles(inputRoot):
    forEachTransportLine(packet.path, proc(raw: string; lineNumber: int) =
      if raw.strip().len == 0:
        return
      let document = parseJson(raw)
      if document.kind != JObject:
        raise newException(ValueError, &"{packet.path}:{lineNumber}: expected JSON object")
      addRecord(
        targets,
        complete,
        makeRecord(document, raw, packet.target, packet.run, packet.path),
        config
      )
    )

  for path in dbFiles(dbRoot):
    var input = open(path, fmRead)
    var raw: string
    var lineNumber = 0
    while input.readLine(raw):
      inc lineNumber
      if raw.strip().len == 0:
        continue
      let document = parseJson(raw)
      if document.kind != JObject:
        input.close()
        raise newException(ValueError, &"{path}:{lineNumber}: expected JSON object")
      let dataset = jsonText(document, "dataset", "database")
      addRecord(
        targets,
        complete,
        makeRecord(document, raw, inferDbTarget(dataset, config), "db", path),
        config
      )
    input.close()

  result = (targets, complete)


proc endpointIds(value: JsonNode): seq[string] =
  case value.kind
  of JString:
    result.add(value.getStr())
  of JObject:
    if value.hasKey("id") and value["id"].kind == JString:
      result.add(value["id"].getStr())
  of JArray:
    for item in value.items:
      result.add(endpointIds(item))
  else:
    discard


proc buildGraph(bucket: Bucket): JsonNode =
  var nodes = newJArray()
  var edges = newJArray()
  var nodeIds = initHashSet[string]()
  var graphRecords: seq[Record]

  for id in sortedIds(bucket):
    let record = bucket.docs[id]
    if graphEligible(record.dtype):
      graphRecords.add(record)
      if graphRecords.len >= GraphDocumentLimit:
        break

  for record in graphRecords:
    if record.dtype == "relation":
      continue
    nodeIds.incl(record.id)
    nodes.add(%*{
      "id": record.id,
      "label": record.title,
      "group": record.dtype,
      "href": "nodes/" & slug(record.id) & ".html",
      "detail": record.summary,
      "dataset": record.dataset,
      "updated": record.updated,
      "reviewed": true,
      "review_status": "reviewed"
    })

  var edgeKeys = initHashSet[string]()
  for record in graphRecords:
    if record.dtype != "relation":
      continue
    let document = parseJson(record.raw)
    if not document.hasKey("data") or document["data"].kind != JObject:
      continue
    let data = document["data"]
    if not data.hasKey("subject") or not data.hasKey("object"):
      continue
    let predicate = jsonText(data, "predicate", "related to").replace("_", " ")
    for source in endpointIds(data["subject"]):
      if source notin nodeIds:
        continue
      for target in endpointIds(data["object"]):
        if target notin nodeIds or target == source:
          continue
        let key = source & "\x1f" & target & "\x1f" & predicate
        if key in edgeKeys:
          continue
        edgeKeys.incl(key)
        edges.add(%*{
          "source": source,
          "target": target,
          "label": predicate,
          "predicate": predicate,
          "reviewed": true
        })

  result = %*{
    "nodes": nodes,
    "edges": edges,
    "meta": {
      "reviewed_nodes": nodes.len,
      "unreviewed_nodes": 0,
      "reviewed_edges": edges.len,
      "unreviewed_edges": 0,
      "graph_document_cap": GraphDocumentLimit
    }
  }


proc page(pageTitle, bodyMarkup, prefix: string): string =
  result = newStringOfCap(bodyMarkup.len + 1024)
  result.add("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">")
  result.add("<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">")
  result.add("<meta name=\"color-scheme\" content=\"dark light\"><title>")
  result.add(htmlEscape(pageTitle))
  result.add("</title><link rel=\"stylesheet\" href=\"")
  result.add(prefix & "assets/style.css\"><link rel=\"stylesheet\" href=\"" & prefix & "assets/explorer.css\"></head><body>")
  result.add("<header><a class=\"brand\" href=\"" & prefix & "index.html\">StarIntel GPT Auto Dig</a></header><main>")
  result.add(bodyMarkup)
  result.add("</main><script src=\"" & prefix & "assets/theme.js\"></script></body></html>")


proc writeJsonArray(path: string; bucket: Bucket; mapper: proc(record: Record): JsonNode {.closure.}) =
  var output = open(path, fmWrite)
  defer:
    output.close()
  output.write("[")
  var first = true
  for id in sortedIds(bucket):
    if not first:
      output.write(",")
    first = false
    output.write($mapper(bucket.docs[id]))
  output.write("]")


proc writeJsonl(path: string; bucket: Bucket) =
  var output = open(path, fmWrite)
  defer:
    output.close()
  for id in sortedIds(bucket):
    output.write(bucket.docs[id].raw)
    output.write("\n")


proc sourceInventory(bucket: Bucket): seq[(string, int)] =
  var counts = initTable[string, int]()
  for record in bucket.docs.values:
    for key in record.sourceKeys:
      counts[key] = counts.getOrDefault(key) + 1
  for key, count in counts.pairs:
    result.add((key, count))
  result.sort(proc(a, b: (string, int)): int =
    result = cmp(b[1], a[1])
    if result == 0:
      result = cmp(a[0], b[0])
  )


proc targetTitle(target: string; config: SiteConfig): string =
  if config.packetTitles.hasKey(target):
    result = config.packetTitles[target]
  else:
    result = target.replace("-", " ")


proc targetSubtitle(target: string; config: SiteConfig): string =
  if config.packetSubtitles.hasKey(target):
    result = config.packetSubtitles[target]
  else:
    result = "StarIntel public-record research"


proc writeTarget(target: string; bucket: Bucket; output, orgOutput: string; config: SiteConfig) =
  let targetOut = output / target
  let nodeOut = targetOut / "nodes"
  let downloads = targetOut / "downloads"
  let publicOrg = output / "org" / target
  let orgOut = orgOutput / target
  for directory in [targetOut, nodeOut, downloads, publicOrg, orgOut]:
    ensureDir(directory)

  let graph = buildGraph(bucket)
  writeFile(targetOut / "graph.json", $graph)
  writeJsonArray(targetOut / "documents.json", bucket, proc(record: Record): JsonNode =
    result = %*{
      "id": record.id,
      "title": record.title,
      "dtype": record.dtype,
      "dataset": record.dataset,
      "summary": record.summary,
      "review": "reviewed",
      "status": record.status,
      "updated": record.updated,
      "url": (if graphEligible(record.dtype): "nodes/" & slug(record.id) & ".html" else: "documents.html?dataset=" & encodeUrl(record.dataset))
    }
  )
  writeJsonl(downloads / "starintel-documents.jsonl", bucket)
  writeFile(downloads / "research-history.json", $(%*[{"target": target, "document_count": bucket.docs.len}]))

  let title = targetTitle(target, config)
  let subtitle = targetSubtitle(target, config)
  let sources = sourceInventory(bucket)
  var sourceMarkup = newStringOfCap(min(1_000_000, sources.len * 96))
  for index in 0 ..< min(sources.len, 5000):
    sourceMarkup.add("<li><strong>" & $sources[index][1] & "</strong> " & htmlEscape(sources[index][0]) & "</li>")

  let dashboard = "<div class=\"dashboard-hero\"><div><span class=\"eyebrow\">StarIntel dashboard</span><h1>" & htmlEscape(title) & "</h1><p class=\"lede\">" & htmlEscape(subtitle) & "</p></div><div class=\"dashboard-actions\"><a class=\"primary-action\" href=\"graph.html\">Open graph</a><a href=\"documents.html\">Browse documents</a><a href=\"sources.html\">Sources</a></div></div><section class=\"stats dashboard-stats\"><div><strong>" & $bucket.docs.len & "</strong><span>canonical records</span></div><div><strong>" & $graph["nodes"].len & "</strong><span>graph nodes</span></div><div><strong>" & $graph["edges"].len & "</strong><span>graph edges</span></div><div><strong>" & $sources.len & "</strong><span>source roots</span></div></section><section class=\"download-strip\"><div><h2>Data exports</h2><p>Bulk observations stay in JSONL instead of exploding into tiny generated files.</p></div><p><a href=\"downloads/starintel-documents.jsonl\">Merged JSONL</a></p></section>"
  writeFile(targetOut / "index.html", page(title, dashboard, "../"))

  let documentsBody = "<div class=\"crumb\"><a href=\"index.html\">← dashboard</a></div><div class=\"documents-heading\"><div><span class=\"eyebrow\">Canonical records</span><h1>Documents</h1><p class=\"lede\">Search the generated document index.</p></div><a class=\"primary-action\" href=\"graph.html\">Open graph</a></div><section class=\"document-controls\"><input id=\"documents-search\" type=\"search\" placeholder=\"Search records…\"><select id=\"documents-type\"><option value=\"\">All record types</option></select><select id=\"documents-review\"><option value=\"\">All review states</option></select></section><div id=\"documents-summary\" class=\"documents-summary\">Loading records…</div><section id=\"documents-grid\" class=\"record-grid document-browser\"></section><nav class=\"document-pages\"><button id=\"documents-prev\">← Previous</button><span id=\"documents-page\"></span><button id=\"documents-next\">Next →</button></nav><script src=\"../assets/dashboard.js\" data-documents=\"documents.json\"></script>"
  writeFile(targetOut / "documents.html", page(title & " documents", documentsBody, "../"))

  let graphBody = "<div class=\"crumb\"><a href=\"index.html\">← dashboard</a></div><h1>" & htmlEscape(title) & " graph</h1><p class=\"lede\">Entity and relation records only; bulk observations are intentionally excluded from graph materialization.</p><div id=\"graph-shell\"><canvas id=\"graph-canvas\"></canvas><aside id=\"graph-detail\">Select a node.</aside></div><script type=\"module\">import { mount } from '../assets/graph-explorer.mjs'; mount({ graphUrl: 'graph.json' });</script>"
  writeFile(targetOut / "graph.html", page(title & " graph", graphBody, "../"))
  writeFile(targetOut / "sources.html", page(title & " sources", "<h1>Sources</h1><p>Source roots are deduplicated by source_id/URI.</p><ol class=\"rank-list\">" & sourceMarkup & "</ol>", "../"))

  var nodeCount = 0
  for id in sortedIds(bucket):
    let record = bucket.docs[id]
    if not graphEligible(record.dtype):
      continue
    inc nodeCount
    if nodeCount > NodePageLimit:
      break
    let document = parseJson(record.raw)
    let pretty = document.pretty()
    let nodeBody = "<div class=\"crumb\"><a href=\"../documents.html\">← documents</a></div><h1>" & htmlEscape(record.title) & "</h1><p class=\"lede\">" & htmlEscape(record.summary) & "</p><pre>" & htmlEscape(pretty) & "</pre>"
    writeFile(nodeOut / (slug(record.id) & ".html"), page(record.title, nodeBody, "../../"))
    let org = "#+title: " & record.title.replace("\n", " ") & "\n#+description: " & record.summary.replace("\n", " ") & "\n\n* Raw StarIntel Document\n\n#+begin_src json\n" & pretty & "\n#+end_src\n"
    writeFile(orgOut / (slug(record.id) & ".org"), org)
    writeFile(publicOrg / (slug(record.id) & ".org"), org)


proc directTopicMatch(rule: TopicRule; record: Record): bool =
  let target = slug(record.target)
  let dataset = slug(record.dataset)
  for value in rule.targets:
    if value.len > 0 and target.contains(value):
      return true
  for value in rule.datasets:
    if value.len > 0 and value == dataset:
      return true
  false


proc termTopicMatch(rule: TopicRule; record: Record): bool =
  if rule.terms.len == 0:
    return false
  let text = (record.target & " " & record.dataset & " " & record.title & " " & record.summary & " " & record.raw).toLowerAscii()
  for term in rule.terms:
    if term.len > 0 and text.contains(term):
      return true
  false


proc topicRulesFor(record: Record; topics: TopicConfig): seq[TopicRule] =
  for rule in topics.rules:
    if directTopicMatch(rule, record):
      result.add(rule)
  if result.len > 0:
    return
  for rule in topics.rules:
    if termTopicMatch(rule, record):
      result.add(rule)
  if result.len == 0:
    result.add(TopicRule(
      id: slug(record.target),
      title: record.target.replace("-", " "),
      subtitle: "Merged dataset for all " & record.target.replace("-", " ") & " research packets"
    ))


proc writeTopicDatasets(targets: Table[string, Bucket]; output, orgOutput: string; topics: TopicConfig): seq[JsonNode] =
  var topicBuckets = initTable[string, Bucket]()
  var topicMeta = initTable[string, TopicRule]()
  var topicTargets = initTable[string, HashSet[string]]()
  var topicDatasets = initTable[string, HashSet[string]]()

  for target, bucket in targets.pairs:
    for record in bucket.docs.values:
      for rule in topicRulesFor(record, topics):
        putLatest(getBucket(topicBuckets, rule.id), record)
        topicMeta[rule.id] = rule
        if not topicTargets.hasKey(rule.id):
          topicTargets[rule.id] = initHashSet[string]()
        topicTargets[rule.id].incl(target)
        if slug(record.dataset) notin topics.excludedDatasets:
          if not topicDatasets.hasKey(rule.id):
            topicDatasets[rule.id] = initHashSet[string]()
          topicDatasets[rule.id].incl(record.dataset)

  var ids: seq[string]
  for id in topicBuckets.keys:
    ids.add(id)
  ids.sort()

  for id in ids:
    let bucket = topicBuckets[id]
    let meta = topicMeta[id]
    let target = "dataset-" & slug(id)
    let targetOut = output / target
    let downloads = targetOut / "downloads"
    ensureDir(targetOut)
    ensureDir(downloads)

    writeTarget(target, bucket, output, orgOutput, topicSiteConfig(target, meta.title, meta.subtitle))
    let sourceTargets = if topicTargets.hasKey(id): sortedSet(topicTargets[id]) else: newSeq[string]()
    let sourceDatasets = if topicDatasets.hasKey(id): sortedSet(topicDatasets[id]) else: newSeq[string]()
    let manifest = %*{
      "topic_dataset": id,
      "title": meta.title,
      "record_count": bucket.docs.len,
      "source_targets": jsonStrings(sourceTargets),
      "source_datasets": jsonStrings(sourceDatasets)
    }
    writeFile(downloads / "topic-manifest.json", manifest.pretty() & "\n")
    writeFile(downloads / "research-history.json", $(%*[manifest]))
    result.add(%*{
      "dataset": id,
      "title": meta.title,
      "record_count": bucket.docs.len,
      "source_target_count": sourceTargets.len,
      "source_dataset_count": sourceDatasets.len,
      "url": target & "/index.html",
      "download": target & "/downloads/starintel-documents.jsonl"
    })


proc writeAssets(assets, output: string) =
  let destination = output / "assets"
  ensureDir(destination)
  if not dirExists(assets):
    return
  for path in walkDirRec(assets):
    if fileExists(path):
      copyFile(path, destination / lastPathPart(path))


proc writeCompleteCorpus(complete: Bucket; output: string) =
  let downloads = output / "downloads"
  ensureDir(downloads)
  let corpus = downloads / "starintel-complete-corpus.jsonl"
  writeJsonl(corpus, complete)
  let digestOutput = execProcess("sha256sum", args = [corpus], options = {poUsePath}).splitWhitespace()
  if digestOutput.len == 0:
    raise newException(IOError, "sha256sum produced no corpus digest")
  let digest = digestOutput[0]

  var counts = initTable[string, int]()
  var updated = ""
  var versions = initHashSet[string]()
  for record in complete.docs.values:
    counts[record.dtype] = counts.getOrDefault(record.dtype) + 1
    if record.updated > updated:
      updated = record.updated
    if record.schemaVersion.len > 0:
      versions.incl(record.schemaVersion)

  var countNode = newJObject()
  for dtype, count in counts.pairs:
    countNode[dtype] = %count

  let manifest = %*{
    "_id": "starintel:dataset-manifest:auto-dig-complete-corpus",
    "dataset": "starintel-auto-dig-complete-corpus",
    "dtype": "dataset-manifest",
    "schema_version": "0.9.0",
    "version": 1,
    "date_added": updated,
    "date_updated": updated,
    "title": "StarIntel Auto Dig complete corpus",
    "sources": [],
    "evidence": [],
    "data": {
      "manifest_type": "dataset",
      "name": "StarIntel Auto Dig complete corpus",
      "counts_by_dtype": countNode,
      "record_count": complete.docs.len,
      "hash_algorithm": "sha256",
      "content_hash": digest,
      "files": [{
        "path": "starintel-complete-corpus.jsonl",
        "media_type": "application/x-ndjson",
        "size_bytes": getFileSize(corpus)
      }],
      "schema_versions": jsonStrings(sortedSet(versions)),
      "generated_at": updated
    }
  }
  writeFile(downloads / "starintel-complete-corpus.manifest.json", manifest.pretty() & "\n")


proc writeRoot(targets: Table[string, Bucket]; complete: Bucket; topicRows: seq[JsonNode]; output: string; config: SiteConfig; topics: TopicConfig) =
  var datasetRows = newJArray()
  var cards = newStringOfCap(targets.len * 256)
  var targetNames: seq[string]
  for target in targets.keys:
    targetNames.add(target)
  targetNames.sort()

  for target in targetNames:
    let bucket = targets[target]
    cards.add("<article><span>" & $bucket.docs.len & " records</span><h2><a href=\"" & target & "/index.html\">" & htmlEscape(targetTitle(target, config)) & "</a></h2><p>" & htmlEscape(targetSubtitle(target, config)) & "</p></article>")
    var byDataset = initTable[string, int]()
    var updatedByDataset = initTable[string, string]()
    for record in bucket.docs.values:
      if slug(record.dataset) in topics.excludedDatasets:
        continue
      byDataset[record.dataset] = byDataset.getOrDefault(record.dataset) + 1
      if record.updated > updatedByDataset.getOrDefault(record.dataset):
        updatedByDataset[record.dataset] = record.updated
    for dataset, count in byDataset.pairs:
      datasetRows.add(%*{
        "dataset": dataset,
        "target": target,
        "target_title": targetTitle(target, config),
        "record_count": count,
        "updated_through": updatedByDataset[dataset],
        "url": target & "/documents.html?dataset=" & encodeUrl(dataset)
      })

  writeFile(output / "datasets.json", $datasetRows)
  var topicsNode = newJArray()
  for row in topicRows:
    topicsNode.add(row)
  writeFile(output / "topic-datasets.json", $topicsNode)
  writeJsonArray(output / "search-index.json", complete, proc(record: Record): JsonNode =
    result = %*{
      "target": record.target,
      "id": record.id,
      "title": record.title,
      "dtype": record.dtype,
      "dataset": record.dataset,
      "summary": record.summary,
      "url": record.target & "/documents.html?dataset=" & encodeUrl(record.dataset)
    }
  )

  var topicCards = newStringOfCap(topicRows.len * 256)
  for row in topicRows:
    topicCards.add("<article><span>" & $row["record_count"].getInt() & " records</span><h2><a href=\"" & htmlEscape(row["url"].getStr()) & "\">" & htmlEscape(row["title"].getStr()) & "</a></h2></article>")
  let body = "<h1>StarIntel GPT Auto Dig</h1><p class=\"lede\">Source-backed research generated by the Nim static-site engine.</p><div class=\"dashboard-actions\"><a class=\"primary-action\" href=\"downloads/starintel-complete-corpus.jsonl\" download>Download complete corpus</a></div><section class=\"stats dashboard-stats\"><div><strong>" & $targets.len & "</strong><span>research targets</span></div><div><strong>" & $topicRows.len & "</strong><span>topic datasets</span></div><div><strong>" & $complete.docs.len & "</strong><span>canonical records</span></div></section><section><h2>Topic datasets</h2><div class=\"packets dataset-catalog\">" & topicCards & "</div></section><section><h2>Research targets</h2><div class=\"packets\">" & cards & "</div></section>"
  writeFile(output / "index.html", page(config.title, body, ""))


proc usage() =
  echo "usage: starintel_site [--input digs] [--db db] [--output _site] [--org-output .generated/org] [--config site-config.json] [--topics manifests/topic-datasets.json] [--assets site-assets]"


proc main(): int =
  var inputRoot = "digs"
  var dbRoot = "db"
  var output = "_site"
  var orgOutput = ".generated/org"
  var configPath = "site-config.json"
  var topicsPath = "manifests/topic-datasets.json"
  var assets = "site-assets"
  var index = 1
  while index <= paramCount():
    let arg = paramStr(index)
    template take(): string =
      inc index
      if index > paramCount():
        raise newException(ValueError, "missing value for " & arg)
      paramStr(index)
    case arg
    of "--input": inputRoot = take()
    of "--db": dbRoot = take()
    of "--output": output = take()
    of "--org-output": orgOutput = take()
    of "--config": configPath = take()
    of "--topics": topicsPath = take()
    of "--assets": assets = take()
    of "-h", "--help":
      usage()
      return 0
    else:
      raise newException(ValueError, "unknown argument: " & arg)
    inc index

  cleanDir(output)
  cleanDir(orgOutput)
  writeAssets(assets, output)
  writeFile(output / ".nojekyll", "")

  let config = loadSiteConfig(configPath)
  let topics = loadTopicConfig(topicsPath)
  let scanned = scanCorpus(inputRoot, dbRoot, config)
  let targets = scanned.targets
  let complete = scanned.complete
  if complete.docs.len == 0:
    raise newException(ValueError, "no canonical StarIntel documents found")

  writeCompleteCorpus(complete, output)
  var names: seq[string]
  for target in targets.keys:
    names.add(target)
  names.sort()
  for target in names:
    writeTarget(target, targets[target], output, orgOutput, config)
  let topicRows = writeTopicDatasets(targets, output, orgOutput, topics)
  writeRoot(targets, complete, topicRows, output, config, topics)

  echo &"site={output} targets={targets.len} topics={topicRows.len} documents={complete.docs.len} engine=nim"
  0


when isMainModule:
  try:
    quit(main())
  except CatchableError as exc:
    stderr.writeLine("error: " & exc.msg)
    quit(1)
