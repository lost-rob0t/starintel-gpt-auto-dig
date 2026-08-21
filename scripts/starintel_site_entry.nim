import std/[algorithm, json, os, osproc, sets, strutils, tables, uri]


type
  PersonAgg = ref object
    name: string
    connections: int
    datasets: HashSet[string]
    predicates: Table[string, int]

  DatasetAgg = ref object
    name: string
    recordCount: int
    peopleCount: int
    organizationCount: int
    relationCount: int
    sources: HashSet[string]
    dayCounts: Table[string, int]
    latestDay: string
    updatedThrough: string

  Finding = object
    id: string
    title: string
    summary: string
    dtype: string
    score: float
    reason: string

  Activity = object
    id: string
    title: string
    dtype: string
    updated: string


const
  ReviewedTokens = [
    "reviewed", "verified", "validated", "confirmed", "corroborated",
    "source-backed", "source backed", "resolved"
  ]
  UnreviewedTokens = [
    "unreviewed", "unverified", "pending", "draft", "queued", "unknown",
    "unclassified", "needs-review", "needs review", "not-reviewed",
    "not reviewed", "proposed"
  ]


proc text(node: JsonNode; key: string; fallback = ""): string =
  if node != nil and node.kind == JObject and node.hasKey(key) and node[key].kind == JString:
    return node[key].getStr()
  fallback


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
  if result.len == 0:
    result = "dataset"


proc commas(value: int): string =
  let raw = $value
  var reverse = newStringOfCap(raw.len + raw.len div 3)
  var digits = 0
  for index in countdown(raw.high, 0):
    if digits > 0 and digits mod 3 == 0:
      reverse.add(',')
    reverse.add(raw[index])
    inc digits
  for index in countdown(reverse.high, 0):
    result.add(reverse[index])


proc datePrefix(value: string): string =
  if value.len >= 10:
    return value[0 .. 9]
  ""


proc dayNumber(value: string): int =
  if value.len < 10:
    return low(int)
  try:
    var year = parseInt(value[0 .. 3])
    let month = parseInt(value[5 .. 6])
    let day = parseInt(value[8 .. 9])
    if month < 1 or month > 12 or day < 1 or day > 31:
      return low(int)
    if month <= 2:
      dec year
    let era = (if year >= 0: year else: year - 399) div 400
    let yearOfEra = year - era * 400
    let shiftedMonth = month + (if month > 2: -3 else: 9)
    let dayOfYear = (153 * shiftedMonth + 2) div 5 + day - 1
    let dayOfEra = yearOfEra * 365 + yearOfEra div 4 - yearOfEra div 100 + dayOfYear
    result = era * 146097 + dayOfEra
  except ValueError:
    result = low(int)


proc sourceKey(source: JsonNode): string =
  case source.kind
  of JString:
    result = source.getStr().strip()
  of JObject:
    for key in ["source_id", "url", "uri", "title"]:
      let value = text(source, key)
      if value.len > 0:
        return value.strip()
    result = $source
  else:
    result = $source


proc sourceDomain(value: string): string =
  var host = value.strip().toLowerAscii()
  let scheme = host.find("://")
  if scheme >= 0:
    host = host[scheme + 3 .. ^1]
  let slash = host.find('/')
  if slash >= 0:
    host = host[0 ..< slash]
  let query = host.find('?')
  if query >= 0:
    host = host[0 ..< query]
  let hash = host.find('#')
  if hash >= 0:
    host = host[0 ..< hash]
  let port = host.rfind(':')
  if port > 0 and host.find(':') == port:
    host = host[0 ..< port]
  if host.startsWith("www."):
    host = host[4 .. ^1]
  if host.len == 0 or not host.contains('.'):
    result = "other"
  else:
    result = host


proc reviewStatus(document: JsonNode): string =
  var raw = ""
  if document.hasKey("verification") and document["verification"].kind == JObject:
    raw = text(document["verification"], "status")
  if raw.len == 0 and document.hasKey("workflow") and document["workflow"].kind == JObject:
    raw = text(document["workflow"], "review_status", text(document["workflow"], "status"))
  if raw.len == 0:
    raw = text(document, "status")
  let status = raw.strip().toLowerAscii().replace("_", "-")
  for token in UnreviewedTokens:
    if status.contains(token):
      return "unreviewed"
  for token in ReviewedTokens:
    if status.contains(token):
      return "reviewed"
  "unreviewed"


proc endpointIds(value: JsonNode): seq[string] =
  case value.kind
  of JString:
    result.add(value.getStr())
  of JObject:
    let id = text(value, "id")
    if id.len > 0:
      result.add(id)
  of JArray:
    for item in value.items:
      result.add(endpointIds(item))
  else:
    discard


proc documentTitle(document: JsonNode): string =
  result = text(document, "title")
  if result.len == 0 and document.hasKey("data") and document["data"].kind == JObject:
    for key in ["display_name", "name", "full_name", "claim"]:
      result = text(document["data"], key)
      if result.len > 0:
        break
  if result.len == 0:
    result = text(document, "_id")


proc documentSummary(document: JsonNode): string =
  result = text(document, "summary", text(document, "description"))
  if result.len == 0 and document.hasKey("data") and document["data"].kind == JObject:
    for key in ["description", "definition", "claim", "bio", "business", "mission"]:
      result = text(document["data"], key)
      if result.len > 0:
        break
  if result.len > 280:
    result = result[0 ..< 280] & "…"


proc newPerson(): PersonAgg =
  PersonAgg(datasets: initHashSet[string](), predicates: initTable[string, int]())


proc getPerson(people: var Table[string, PersonAgg]; id: string): PersonAgg =
  if not people.hasKey(id):
    people[id] = newPerson()
  people[id]


proc newDataset(name: string): DatasetAgg =
  DatasetAgg(
    name: name,
    sources: initHashSet[string](),
    dayCounts: initTable[string, int]()
  )


proc getDataset(datasets: var Table[string, DatasetAgg]; name: string): DatasetAgg =
  if not datasets.hasKey(name):
    datasets[name] = newDataset(name)
  datasets[name]


proc confidence(document: JsonNode): float =
  if not document.hasKey("assessment") or document["assessment"].kind != JObject:
    return 0.0
  let assessment = document["assessment"]
  if not assessment.hasKey("confidence"):
    return 0.0
  let node = assessment["confidence"]
  case node.kind
  of JInt:
    result = node.getInt().float
  of JFloat:
    result = node.getFloat()
  else:
    return 0.0
  if result > 1.0:
    result = result / 100.0
  result = max(0.0, min(1.0, result))


proc keepFinding(rows: var seq[Finding]; candidate: Finding) =
  if rows.len < 8:
    rows.add(candidate)
    return
  var weakest = 0
  for index in 1 ..< rows.len:
    if rows[index].score < rows[weakest].score:
      weakest = index
  if candidate.score > rows[weakest].score:
    rows[weakest] = candidate


proc keepActivity(rows: var seq[Activity]; candidate: Activity) =
  if rows.len < 10:
    rows.add(candidate)
    return
  var oldest = 0
  for index in 1 ..< rows.len:
    if rows[index].updated & rows[index].id < rows[oldest].updated & rows[oldest].id:
      oldest = index
  if candidate.updated & candidate.id > rows[oldest].updated & rows[oldest].id:
    rows[oldest] = candidate


proc metric(value: int; label: string): string =
  "<div class=\"corpus-metric\"><strong>" & commas(value) & "</strong><span>" & htmlEscape(label) & "</span></div>"


proc fallbackTable(rows: JsonNode; labelKey = "label"): string =
  result = "<div class=\"chart-fallback\"><table><thead><tr><th>Category</th><th>Count</th></tr></thead><tbody>"
  var count = 0
  for row in rows.items:
    if count >= 16:
      break
    result.add("<tr><td>" & htmlEscape(text(row, labelKey)) & "</td><td>" & commas(row["count"].getInt()) & "</td></tr>")
    inc count
  result.add("</tbody></table></div>")


proc pageShell(title, body: string): string =
  "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>" & htmlEscape(title) & "</title>" &
  "<link rel=\"stylesheet\" href=\"assets/style.css\"><link rel=\"stylesheet\" href=\"assets/explorer.css\"><link rel=\"stylesheet\" href=\"assets/adar-dashboard.css\"></head><body>" &
  "<header><a class=\"brand\" href=\"index.html\">StarIntel GPT Auto Dig</a><nav></nav></header><main>" & body & "</main>" &
  "<script src=\"assets/theme.js\"></script><script defer src=\"assets/adar-shell.js\"></script><script defer src=\"assets/corpus-dashboard.js\"></script></body></html>"


proc personRow(row: JsonNode; rank: int): string =
  let url = text(row, "url")
  let name = htmlEscape(text(row, "name"))
  let title = if url.len > 0: "<a href=\"" & htmlEscape(url) & "\">" & name & "</a>" else: name
  var relations: seq[string]
  if row.hasKey("relations"):
    for item in row["relations"].items:
      relations.add(text(item, "label") & " " & $item["count"].getInt())
  "<li><span class=\"rank-number\">" & align($rank, 2, '0') & "</span><div><strong>" & title & "</strong><small>" & htmlEscape(relations.join(", ")) & "</small></div><b>" & commas(row["connections"].getInt()) & "</b></li>"


proc findingRow(row: JsonNode; rank: int): string =
  let url = text(row, "url")
  let label = htmlEscape(text(row, "title"))
  let title = if url.len > 0: "<a href=\"" & htmlEscape(url) & "\">" & label & "</a>" else: label
  "<li><span class=\"rank-number\">" & align($rank, 2, '0') & "</span><div><strong>" & title & "</strong><small>" & htmlEscape(text(row, "reason")) & "</small><p>" & htmlEscape(text(row, "summary")) & "</p></div></li>"


proc datasetRow(row: JsonNode): string =
  let url = htmlEscape(text(row, "url"))
  "<li><div><strong><a href=\"" & url & "\">" & htmlEscape(text(row, "title", text(row, "dataset"))) & "</a></strong><small>" & htmlEscape(text(row, "kind")) & " · +" & commas(row["added_30d"].getInt()) & " / 30d</small></div><b>" & commas(row["record_count"].getInt()) & "</b></li>"


proc activityRow(row: JsonNode): string =
  let url = text(row, "url")
  let label = htmlEscape(text(row, "title"))
  let title = if url.len > 0: "<a href=\"" & htmlEscape(url) & "\">" & label & "</a>" else: label
  "<li><time>" & htmlEscape(datePrefix(text(row, "updated"))) & "</time><div><strong>" & title & "</strong><small>" & htmlEscape(text(row, "dtype", "record")) & "</small></div></li>"


proc dashboardHtml(data: JsonNode; siteTitle: string): string =
  let summary = data["summary"]
  var domains = ""
  for row in data["source_domains"].items:
    domains.add("<li><span>" & htmlEscape(text(row, "label")) & "</span><strong>" & commas(row["count"].getInt()) & "</strong></li>")
  var people = ""
  var rank = 1
  for row in data["top_connected_people"].items:
    people.add(personRow(row, rank))
    inc rank
  if people.len == 0:
    people = "<li>No reviewed person relations yet.</li>"
  var findings = ""
  rank = 1
  for row in data["top_findings"].items:
    findings.add(findingRow(row, rank))
    inc rank
  if findings.len == 0:
    findings = "<li>No reviewed findings met the ranking threshold.</li>"
  var active = ""
  for row in data["active_datasets"].items:
    active.add(datasetRow(row))
  var activity = ""
  for row in data["latest_activity"].items:
    activity.add(activityRow(row))

  let body = "<div id=\"corpus-dashboard\" class=\"corpus-dashboard\" data-dashboard=\"dashboard-data.json\">" &
    "<section class=\"corpus-hero\"><div><span class=\"eyebrow\">StarIntel corpus / live projection</span><h1>Follow the evidence.<br>See the network move.</h1><p class=\"lede\">A source-backed view across the public StarIntel corpus. Start with the pulse, drill into the datasets, then go as deep as the graph.</p></div>" &
    "<div class=\"corpus-status\"><span>Updated through</span><strong>" & htmlEscape(datePrefix(text(summary, "updated_through"))) & "</strong><a href=\"downloads/starintel-complete-corpus.manifest.json\">Download corpus manifest ↘</a></div></section>" &
    "<section class=\"corpus-metrics\" aria-label=\"Corpus totals\">" & metric(summary["documents"].getInt(), "records") & metric(summary["people"].getInt(), "people") & metric(summary["organizations"].getInt(), "organizations") & metric(summary["relations"].getInt(), "relations") & metric(summary["datasets"].getInt(), "datasets") & metric(summary["sources"].getInt(), "sources") & "</section>" &
    "<section class=\"dashboard-primary-grid\"><article class=\"chart-surface chart-surface-wide\"><div class=\"section-head\"><div><span class=\"eyebrow\">Corpus pulse</span><h2>Documents added by day</h2></div><div class=\"range-switch\" role=\"group\" aria-label=\"Chart date range\"><button data-range=\"30\">30d</button><button data-range=\"90\" class=\"active\">90d</button><button data-range=\"365\">1y</button><button data-range=\"all\">All</button></div></div><div id=\"documents-by-day-chart\" class=\"chart-frame\" aria-label=\"Documents added by day chart\"></div>" & fallbackTable(data["documents_by_day"], "date") & "</article>" &
    "<aside class=\"corpus-sidecar\"><span class=\"eyebrow\">Evidence base</span><strong>" & commas(summary["sources"].getInt()) & "</strong><h2>unique sources</h2><ol class=\"domain-list\">" & domains & "</ol></aside></section>" &
    "<section class=\"dashboard-chart-grid\"><article class=\"chart-surface\"><span class=\"eyebrow\">Corpus composition</span><h2>Document types</h2><p>Relations are intentionally excluded.</p><div id=\"document-types-chart\" class=\"chart-frame chart-frame-square\"></div>" & fallbackTable(data["document_types"]) & "</article><article class=\"chart-surface\"><span class=\"eyebrow\">Network grammar</span><h2>Relation types</h2><p>The connection types shaping the graph.</p><div id=\"relation-types-chart\" class=\"chart-frame\"></div>" & fallbackTable(data["relation_types"]) & "</article></section>" &
    "<section class=\"dashboard-rank-grid\"><article><div class=\"section-head\"><div><span class=\"eyebrow\">Reviewed graph</span><h2>Top connected people</h2></div><a href=\"datasets.html\">Browse datasets →</a></div><ol class=\"people-rank\">" & people & "</ol></article><article><div class=\"section-head\"><div><span class=\"eyebrow\">Evidence-backed</span><h2>Top findings</h2></div></div><ol class=\"finding-rank\">" & findings & "</ol></article></section>" &
    "<section class=\"dashboard-rank-grid dashboard-lower\"><article><div class=\"section-head\"><div><span class=\"eyebrow\">Growing now</span><h2>Active datasets</h2></div><a class=\"primary-action\" href=\"datasets.html\">All datasets →</a></div><ol class=\"dataset-rank\">" & active & "</ol></article><article><div class=\"section-head\"><div><span class=\"eyebrow\">Fresh evidence</span><h2>Latest activity</h2></div></div><ol class=\"activity-rank\">" & activity & "</ol></article></section></div>"
  pageShell(siteTitle, body)


proc datasetsHtml(catalog: JsonNode; siteTitle: string): string =
  var topicCount = 0
  var sourceCount = 0
  for row in catalog.items:
    if text(row, "kind") == "topic": inc topicCount
    elif text(row, "kind") == "source": inc sourceCount
  let body = "<div id=\"dataset-browser\" class=\"dataset-browser\" data-catalog=\"dataset-catalog.json\">" &
    "<section class=\"dataset-hero\"><div><span class=\"eyebrow\">Corpus catalog</span><h1>Datasets</h1><p class=\"lede\">Every generated topic dataset and source dataset in one place. Filter it, sort it, then open the dataset view you need.</p></div><div class=\"dataset-totals\"><strong>" & commas(catalog.len) & "</strong><span>datasets</span><small>" & commas(topicCount) & " topic · " & commas(sourceCount) & " source</small></div></section>" &
    "<section class=\"dataset-toolbar\" aria-label=\"Dataset controls\"><input id=\"dataset-search\" type=\"search\" placeholder=\"Search datasets or research targets…\" autocomplete=\"off\"><div class=\"segmented\" role=\"group\" aria-label=\"Dataset class\"><button type=\"button\" class=\"active\" data-kind=\"all\" aria-pressed=\"true\">All</button><button type=\"button\" data-kind=\"topic\" aria-pressed=\"false\">Topic</button><button type=\"button\" data-kind=\"source\" aria-pressed=\"false\">Source</button></div><select id=\"dataset-sort\" aria-label=\"Sort datasets\"><option value=\"activity\">Recent growth</option><option value=\"records\">Record count</option><option value=\"sources\">Source count</option><option value=\"updated\">Recently updated</option><option value=\"name\">Name</option></select><div class=\"segmented dataset-view-switch\" role=\"group\" aria-label=\"Dataset view\"><button type=\"button\" class=\"active\" data-view=\"cards\" aria-pressed=\"true\">Cards</button><button type=\"button\" data-view=\"table\" aria-pressed=\"false\">Table</button></div></section>" &
    "<div id=\"dataset-summary\" class=\"dataset-summary\">Loading datasets…</div><section id=\"dataset-card-grid\" class=\"dataset-card-grid\"></section><div id=\"dataset-table-wrap\" class=\"dataset-table-wrap\" hidden><table class=\"dataset-table\"><thead><tr><th>Dataset</th><th>Kind</th><th>Records</th><th>People</th><th>Orgs</th><th>Relations</th><th>Sources</th><th>+30d</th><th>Updated</th><th>Open</th></tr></thead><tbody id=\"dataset-table-body\"></tbody></table></div></div>"
  pageShell(siteTitle & " datasets", body)


proc buildProjection(corpusPath, output, siteTitle: string): tuple[data, catalog: JsonNode] =
  var total = 0
  var peopleCount = 0
  var organizationCount = 0
  var relationCount = 0
  var updatedThrough = ""
  var byDay = initTable[string, int]()
  var dtypes = initTable[string, int]()
  var relationTypes = initTable[string, int]()
  var globalSources = initHashSet[string]()
  var domains = initTable[string, int]()
  var people = initTable[string, PersonAgg]()
  var datasets = initTable[string, DatasetAgg]()
  var findings: seq[Finding]
  var activity: seq[Activity]

  if not fileExists(corpusPath):
    raise newException(IOError, "dashboard restore missing canonical corpus: " & corpusPath)

  for raw in lines(corpusPath):
    if raw.strip().len == 0:
      continue
    let document = parseJson(raw)
    if document.kind != JObject:
      continue
    inc total
    let id = text(document, "_id")
    let dtype = text(document, "dtype", "unknown")
    let datasetName = text(document, "dataset", "unknown")
    let added = datePrefix(text(document, "date_added"))
    let updated = text(document, "date_updated")
    let reviewed = reviewStatus(document) == "reviewed"
    let dataset = getDataset(datasets, datasetName)
    inc dataset.recordCount
    if updated > dataset.updatedThrough:
      dataset.updatedThrough = updated
    if added.len > 0:
      dataset.dayCounts[added] = dataset.dayCounts.getOrDefault(added) + 1
      if added > dataset.latestDay:
        dataset.latestDay = added
      byDay[added] = byDay.getOrDefault(added) + 1
    if updated > updatedThrough:
      updatedThrough = updated

    case dtype
    of "person":
      inc peopleCount
      inc dataset.peopleCount
      let person = getPerson(people, id)
      person.name = documentTitle(document)
    of "org":
      inc organizationCount
      inc dataset.organizationCount
    of "relation":
      inc relationCount
      inc dataset.relationCount
    else:
      dtypes[dtype] = dtypes.getOrDefault(dtype) + 1

    if document.hasKey("sources") and document["sources"].kind == JArray:
      for source in document["sources"].items:
        let key = sourceKey(source)
        if key.len == 0:
          continue
        dataset.sources.incl(key)
        if key notin globalSources:
          globalSources.incl(key)
          let domain = sourceDomain(key)
          domains[domain] = domains.getOrDefault(domain) + 1

    if dtype == "relation" and document.hasKey("data") and document["data"].kind == JObject:
      let data = document["data"]
      let predicate = text(data, "predicate", "related to").replace("_", " ")
      relationTypes[predicate] = relationTypes.getOrDefault(predicate) + 1
      if reviewed and data.hasKey("subject") and data.hasKey("object"):
        var endpoints = initHashSet[string]()
        for endpoint in endpointIds(data["subject"]): endpoints.incl(endpoint)
        for endpoint in endpointIds(data["object"]): endpoints.incl(endpoint)
        for endpoint in endpoints:
          let person = getPerson(people, endpoint)
          person.connections += max(1, endpoints.len - 1)
          person.datasets.incl(datasetName)
          person.predicates[predicate] = person.predicates.getOrDefault(predicate) + 1

    if reviewed and dtype in ["claim", "analysis", "research-pass"]:
      let evidenceCount = if document.hasKey("evidence") and document["evidence"].kind == JArray: document["evidence"].len else: 0
      let sourceCount = if document.hasKey("sources") and document["sources"].kind == JArray: document["sources"].len else: 0
      let relatedCount = if document.hasKey("related_ids") and document["related_ids"].kind == JArray: document["related_ids"].len else: 0
      let conf = confidence(document)
      let score = evidenceCount.float * 4.0 + sourceCount.float * 3.0 + conf * 10.0 + min(relatedCount, 10).float
      if score > 0:
        var reasons: seq[string]
        if evidenceCount > 0: reasons.add($evidenceCount & " evidence")
        if sourceCount > 0: reasons.add($sourceCount & " sources")
        if conf > 0: reasons.add($(int(conf * 100.0)) & "% confidence")
        if relatedCount > 0: reasons.add($relatedCount & " linked records")
        keepFinding(findings, Finding(id: id, title: documentTitle(document), summary: documentSummary(document), dtype: dtype, score: score, reason: reasons.join(" · ")))

    if reviewed:
      keepActivity(activity, Activity(id: id, title: documentTitle(document), dtype: dtype, updated: updated))

  var dayKeys: seq[string]
  for key in byDay.keys: dayKeys.add(key)
  dayKeys.sort()
  var daily = newJArray()
  for key in dayKeys:
    daily.add(%*{"date": key, "count": byDay[key]})

  var dtypePairs: seq[(string, int)]
  for key, value in dtypes.pairs: dtypePairs.add((key, value))
  dtypePairs.sort(proc(a, b: (string, int)): int = cmp(b[1], a[1]))
  var dtypeRows = newJArray()
  for row in dtypePairs: dtypeRows.add(%*{"label": row[0], "count": row[1]})

  var relationPairs: seq[(string, int)]
  for key, value in relationTypes.pairs: relationPairs.add((key, value))
  relationPairs.sort(proc(a, b: (string, int)): int = cmp(b[1], a[1]))
  var relationRows = newJArray()
  for row in relationPairs: relationRows.add(%*{"label": row[0], "count": row[1]})

  var domainPairs: seq[(string, int)]
  for key, value in domains.pairs: domainPairs.add((key, value))
  domainPairs.sort(proc(a, b: (string, int)): int = cmp(b[1], a[1]))
  var domainRows = newJArray()
  for index in 0 ..< min(domainPairs.len, 8):
    domainRows.add(%*{"label": domainPairs[index][0], "count": domainPairs[index][1]})

  var personPairs: seq[(string, PersonAgg)]
  for id, person in people.pairs:
    if person.name.len > 0 and person.connections > 0:
      personPairs.add((id, person))
  personPairs.sort(proc(a, b: (string, PersonAgg)): int = cmp(b[1].connections, a[1].connections))
  var personRows = newJArray()
  for index in 0 ..< min(personPairs.len, 12):
    let id = personPairs[index][0]
    let person = personPairs[index][1]
    var predicatePairs: seq[(string, int)]
    for label, count in person.predicates.pairs: predicatePairs.add((label, count))
    predicatePairs.sort(proc(a, b: (string, int)): int = cmp(b[1], a[1]))
    var predicates = newJArray()
    for p in 0 ..< min(predicatePairs.len, 3):
      predicates.add(%*{"label": predicatePairs[p][0], "count": predicatePairs[p][1]})
    personRows.add(%*{
      "id": id,
      "name": person.name,
      "connections": person.connections,
      "dataset_count": person.datasets.len,
      "relations": predicates,
      "url": "search.html?id=" & encodeUrl(id)
    })

  findings.sort(proc(a, b: Finding): int = cmp(b.score, a.score))
  var findingRows = newJArray()
  for finding in findings:
    findingRows.add(%*{
      "id": finding.id,
      "title": finding.title,
      "summary": finding.summary,
      "dtype": finding.dtype,
      "score": finding.score,
      "reason": finding.reason,
      "url": "search.html?id=" & encodeUrl(finding.id)
    })

  activity.sort(proc(a, b: Activity): int = cmp(b.updated & b.id, a.updated & a.id))
  var activityRows = newJArray()
  for row in activity:
    activityRows.add(%*{
      "id": row.id,
      "title": row.title,
      "dtype": row.dtype,
      "updated": row.updated,
      "url": "search.html?id=" & encodeUrl(row.id)
    })

  var catalogByKey = initTable[string, JsonNode]()
  for name, dataset in datasets.pairs:
    var added30d = 0
    let latestNumber = dayNumber(dataset.latestDay)
    if latestNumber != low(int):
      for day, count in dataset.dayCounts.pairs:
        let number = dayNumber(day)
        if number != low(int) and latestNumber - number <= 29:
          added30d += count
    let row = %*{
      "id": "source-" & slug(name),
      "dataset": name,
      "title": name,
      "kind": "source",
      "record_count": dataset.recordCount,
      "people_count": dataset.peopleCount,
      "organization_count": dataset.organizationCount,
      "relation_count": dataset.relationCount,
      "source_count": dataset.sources.len,
      "added_30d": added30d,
      "updated_through": dataset.updatedThrough,
      "url": "search.html?dataset=" & encodeUrl(name),
      "download": ""
    }
    catalogByKey[slug(name)] = row

  let topicsPath = output / "topic-datasets.json"
  if fileExists(topicsPath):
    let topics = parseFile(topicsPath)
    if topics.kind == JArray:
      for source in topics.items:
        let name = text(source, "dataset", text(source, "title"))
        let row = %*{
          "id": "topic-" & slug(name),
          "dataset": name,
          "title": text(source, "title", name),
          "kind": "topic",
          "record_count": (if source.hasKey("record_count"): source["record_count"].getInt() else: 0),
          "people_count": 0,
          "organization_count": 0,
          "relation_count": 0,
          "source_count": (if source.hasKey("source_dataset_count"): source["source_dataset_count"].getInt() else: 0),
          "added_30d": 0,
          "updated_through": updatedThrough,
          "url": text(source, "url", "dataset-" & slug(name) & "/index.html"),
          "download": text(source, "download")
        }
        catalogByKey[slug(name)] = row

  var catalogRows: seq[JsonNode]
  for row in catalogByKey.values: catalogRows.add(row)
  catalogRows.sort(proc(a, b: JsonNode): int =
    let countCmp = cmp(b["record_count"].getInt(), a["record_count"].getInt())
    if countCmp != 0: countCmp else: cmp(text(a, "title"), text(b, "title"))
  )
  var catalog = newJArray()
  for row in catalogRows: catalog.add(row)

  var activeRows = catalogRows
  activeRows.sort(proc(a, b: JsonNode): int =
    let growthCmp = cmp(b["added_30d"].getInt(), a["added_30d"].getInt())
    if growthCmp != 0: growthCmp else: cmp(b["record_count"].getInt(), a["record_count"].getInt())
  )
  var active = newJArray()
  for index in 0 ..< min(activeRows.len, 8): active.add(activeRows[index])

  let data = %*{
    "version": 2,
    "generated_at": updatedThrough,
    "summary": {
      "documents": total,
      "people": peopleCount,
      "organizations": organizationCount,
      "relations": relationCount,
      "datasets": catalog.len,
      "sources": globalSources.len,
      "updated_through": updatedThrough
    },
    "documents_by_day": daily,
    "document_types": dtypeRows,
    "relation_types": relationRows,
    "top_connected_people": personRows,
    "top_findings": findingRows,
    "source_domains": domainRows,
    "active_datasets": active,
    "latest_activity": activityRows
  }
  result = (data, catalog)


proc optionValue(args: seq[string]; name, fallback: string): string =
  for index in 0 ..< args.len:
    if args[index] == name and index + 1 < args.len:
      return args[index + 1]
  fallback


proc siteTitle(configPath: string): string =
  result = "StarIntel GPT Auto Dig"
  if not fileExists(configPath):
    return
  try:
    let config = parseFile(configPath)
    result = text(config, "site_title", result)
  except CatchableError:
    discard


proc runCore(args: seq[string]): int =
  let core = getAppDir() / "starintel-site-core"
  if not fileExists(core):
    stderr.writeLine("missing canonical site core: " & core)
    return 1
  let process = startProcess(core, args = args, options = {poParentStreams})
  result = process.waitForExit()
  process.close()


proc main(): int =
  let args = commandLineParams()
  let code = runCore(args)
  if code != 0:
    return code
  if "--help" in args or "-h" in args:
    return 0
  let output = optionValue(args, "--output", "_site")
  let bulk = optionValue(args, "--bulk-output", ".generated/bulk")
  let config = optionValue(args, "--config", "site-config.json")
  let title = siteTitle(config)
  let projection = buildProjection(bulk / "starintel-complete-corpus.jsonl", output, title)
  writeFile(output / "dashboard-data.json", projection.data.pretty() & "\n")
  writeFile(output / "dataset-catalog.json", projection.catalog.pretty() & "\n")
  writeFile(output / "index.html", dashboardHtml(projection.data, title))
  writeFile(output / "datasets.html", datasetsHtml(projection.catalog, title))
  echo "restored_adar_dashboard=PASS records=", projection.data["summary"]["documents"].getInt(), " datasets=", projection.catalog.len
  0


when isMainModule:
  try:
    quit(main())
  except CatchableError as exc:
    stderr.writeLine("starintel-site dashboard restore failed: " & exc.msg)
    quit(1)
