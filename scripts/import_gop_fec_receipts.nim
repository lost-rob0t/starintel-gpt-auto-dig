import std/[base64, json, os, osproc, sets, streams, strformat, strutils]

const
  Dataset = "gop"
  RncId = "starintel:org:republican-national-committee"
  DefaultCommitteeId = "C00003418"
  DefaultCycle = 2026
  DefaultGeneratedAt = "2026-08-08T21:50:00Z"
  PartSize = 30_000_000
  ReadChunk = 3 * 1024 * 1024
  MaxUniqueRows = 1_500_000


type
  Options = object
    cycle: int
    committeeId: string
    output: string
    offlineZip: string
    generatedAt: string

  ReceiptRow = object
    amendment: string
    reportType: string
    primaryGeneral: string
    imageNumber: string
    transactionType: string
    entityType: string
    transactionDate: string
    transactionAmount: string
    otherId: string
    transactionId: string
    fileNumber: string
    memoCode: string
    subId: string


proc jsonStrings(values: seq[string]): JsonNode =
  result = newJArray()
  for value in values:
    result.add(%value)


proc shellQuote(value: string): string =
  result = "'" & value.replace("'", "'\"'\"'") & "'"


proc bulkUrl(cycle: int): string =
  let year = $cycle
  result = &"https://www.fec.gov/files/bulk-downloads/{cycle}/indiv{year[^2 .. ^1]}.zip"


proc sourceId(cycle: int; committeeId: string): string =
  result = &"starintel:source:fec-individual-contributions-{cycle}-gop-{committeeId.toLowerAscii()}"


proc setField(row: var ReceiptRow; field: int; value: string) =
  case field
  of 1: row.amendment = value
  of 2: row.reportType = value
  of 3: row.primaryGeneral = value
  of 4: row.imageNumber = value
  of 5: row.transactionType = value
  of 6: row.entityType = value
  of 13: row.transactionDate = value
  of 14: row.transactionAmount = value
  of 15: row.otherId = value
  of 16: row.transactionId = value
  of 17: row.fileNumber = value
  of 18: row.memoCode = value
  of 20: row.subId = value
  else: discard


proc parseMatchingReceipt(line, committeeId: string; row: var ReceiptRow): bool =
  let first = line.find('|')
  if first < 0:
    raise newException(ValueError, "FEC row contains no field separator")
  if first != committeeId.len or line[0 ..< first] != committeeId:
    return false

  var field = 1
  var start = first + 1
  var cursor = start
  while cursor <= line.len:
    if cursor == line.len or line[cursor] == '|':
      if field <= 20:
        setField(row, field, line[start ..< cursor])
      inc field
      start = cursor + 1
    inc cursor

  if field < 21:
    raise newException(ValueError, &"unexpected FEC row width: {field}")
  result = true


proc dateNode(value: string): JsonNode =
  let raw = value.strip()
  if raw.len == 0:
    return newJNull()
  if raw.len == 8:
    return %(&"{raw[4..7]}-{raw[0..1]}-{raw[2..3]}T00:00:00Z")
  if raw.len == 10 and raw[2] == '/' and raw[5] == '/':
    return %(&"{raw[6..9]}-{raw[0..1]}-{raw[3..4]}T00:00:00Z")
  raise newException(ValueError, "invalid FEC date: " & raw)


proc amount(value: string): float =
  try:
    result = parseFloat(value.strip())
  except ValueError as exc:
    raise newException(ValueError, "invalid FEC amount " & value & ": " & exc.msg)


proc metadata(row: ReceiptRow; committeeId: string): JsonNode =
  result = newJObject()
  template put(key: string; value: string) =
    if value.len > 0:
      result[key] = %value
  put("cmte_id", committeeId)
  put("amndt_ind", row.amendment)
  put("rpt_tp", row.reportType)
  put("transaction_pgi", row.primaryGeneral)
  put("image_num", row.imageNumber)
  put("transaction_tp", row.transactionType)
  put("entity_tp", row.entityType)
  put("transaction_dt", row.transactionDate)
  put("transaction_amt", row.transactionAmount)
  put("other_id", row.otherId)
  put("tran_id", row.transactionId)
  put("file_num", row.fileNumber)
  put("memo_cd", row.memoCode)
  put("sub_id", row.subId)


proc identifiers(row: ReceiptRow): JsonNode =
  result = newJArray()
  result.add(%*{
    "scheme": "fec_sub_id",
    "value": row.subId,
    "issuer": "Federal Election Commission",
    "canonical": true
  })
  template addId(scheme: string; value: string) =
    if value.len > 0:
      result.add(%*{
        "scheme": scheme,
        "value": value,
        "issuer": "Federal Election Commission",
        "canonical": false
      })
  addId("fec_file_num", row.fileNumber)
  addId("fec_transaction_id", row.transactionId)
  addId("fec_image_num", row.imageNumber)


proc sourceDocument(options: Options): JsonNode =
  result = %*{
    "_id": sourceId(options.cycle, options.committeeId),
    "data": {
      "accessed_at": options.generatedAt,
      "credibility": 0.99,
      "kind": "official_fec_bulk_file",
      "publisher": "Federal Election Commission",
      "uri": bulkUrl(options.cycle)
    },
    "dataset": Dataset,
    "date_added": options.generatedAt,
    "date_updated": options.generatedAt,
    "dtype": "source",
    "evidence": [],
    "extensions": {
      "privacy_transform": {
        "contributor_identity_emitted": false,
        "contributor_location_emitted": false,
        "contributor_employment_emitted": false,
        "raw_source_rows_embedded": false
      }
    },
    "handling": {
      "handling": "public-source-only",
      "pii": false,
      "sensitive": false,
      "visibility": "public"
    },
    "schema_version": "0.9.0",
    "sources": [],
    "status": "recorded",
    "summary": "Official FEC individual-contribution bulk source filtered to the Republican National Committee; contributor identity and employment/location fields are intentionally omitted.",
    "tags": ["gop", "fec", "official-source", "individual-contribution", "deidentified"],
    "title": &"FEC {options.cycle} de-identified RNC individual-receipt source",
    "verification": {
      "last_reviewed_at": options.generatedAt,
      "status": "official-fec-record",
      "verified": true
    },
    "version": 1
  }


proc financeDocument(row: ReceiptRow; options: Options; sid: string): JsonNode =
  let value = amount(row.transactionAmount)
  let txDate = dateNode(row.transactionDate)
  var qualifications = newJArray()
  qualifications.add(%"Raw FEC bulk row; amendments, memo entries, reattributions, refunds, and conduit records are preserved and not netted.")
  if row.amendment == "A":
    qualifications.add(%"This row was reported in an amended filing.")
  if row.memoCode == "X":
    qualifications.add(%"FEC memo code X is preserved; this record is not treated as a net-new contribution.")

  result = %*{
    "_id": "starintel:campaign-finance:fec-individual-" & row.subId,
    "data": {
      "amount": value,
      "committee_id": options.committeeId,
      "contribution_type": (if row.transactionType.len > 0: row.transactionType else: "reported_receipt"),
      "counterparty_ids": [RncId],
      "currency": "USD",
      "election_cycle": $options.cycle,
      "filing_id": row.fileNumber,
      "methodology": "Direct row import from the official FEC individual-contributions bulk file with contributor identity fields omitted.",
      "observation_type": "reported_itemized_contribution",
      "period_end": txDate,
      "period_start": txDate,
      "qualifications": qualifications,
      "recipient_id": RncId,
      "reported_at": newJNull(),
      "value_type": "reported_transaction_amount"
    },
    "dataset": Dataset,
    "date_added": options.generatedAt,
    "date_updated": options.generatedAt,
    "dtype": "campaign-finance",
    "evidence": [],
    "handling": {
      "handling": "public-source-only",
      "pii": false,
      "sensitive": false,
      "visibility": "public"
    },
    "identifiers": identifiers(row),
    "schema_version": "0.9.0",
    "sources": [{
      "source_id": sid,
      "locator": "SUB_ID " & row.subId,
      "metadata": metadata(row, options.committeeId)
    }],
    "status": "recorded",
    "summary": &"Official FEC row reports ${value} as an itemized contribution or related receipt record to the Republican National Committee; contributor identity is intentionally omitted.",
    "tags": ["gop", "fec", "individual-contribution", "campaign-finance", "deidentified"],
    "title": "FEC contribution " & row.subId,
    "verification": {
      "last_reviewed_at": options.generatedAt,
      "status": "official-filing-record",
      "verified": true
    },
    "version": 1
  }


proc listMembers(zipPath: string): seq[string] =
  let output = execProcess("unzip", args = ["-Z1", zipPath], options = {poUsePath})
  for raw in output.splitLines:
    let name = raw.strip()
    let lower = name.toLowerAscii()
    if name.len > 0 and (lower.endsWith(".txt") or lower.endsWith(".csv")):
      result.add(name)
  if result.len == 0:
    raise newException(IOError, "FEC ZIP contains no text data members")


proc sha256(path: string): string =
  let output = execProcess("sha256sum", args = [path], options = {poUsePath}).splitWhitespace()
  if output.len == 0:
    raise newException(IOError, "sha256sum returned no digest")
  result = output[0]


proc gzipFile(inputPath, outputPath: string) =
  let command = "gzip -9 -n -c " & shellQuote(inputPath) & " > " & shellQuote(outputPath)
  let process = startProcess("sh", args = ["-c", command], options = {poUsePath})
  let code = process.waitForExit()
  process.close()
  if code != 0:
    raise newException(IOError, &"gzip failed with exit code {code}")


proc encodeParts(gzipPath, outputDir: string): seq[string] =
  let baseName = "starintel-documents.jsonl.gz.b64"
  let manifest = outputDir / (baseName & ".parts")
  for old in walkFiles(outputDir / (baseName & ".part-*")):
    removeFile(old)

  var input = open(gzipPath, fmRead)
  defer: input.close()
  var part: File
  var partOpen = false
  var partBytes = 0
  var partIndex = 0
  var buffer = newString(ReadChunk)

  while true:
    let count = input.readBuffer(addr buffer[0], buffer.len)
    if count <= 0:
      break
    buffer.setLen(count)
    let encoded = encode(buffer)
    var offset = 0
    while offset < encoded.len:
      if not partOpen:
        let name = baseName & &".part-{partIndex:04d}"
        part = open(outputDir / name, fmWrite)
        result.add(name)
        partOpen = true
        partBytes = 0
        inc partIndex
      let take = min(PartSize - partBytes, encoded.len - offset)
      part.write(encoded[offset ..< offset + take])
      partBytes += take
      offset += take
      if partBytes == PartSize:
        part.write("\n")
        part.close()
        partOpen = false
    buffer.setLen(ReadChunk)

  if partOpen:
    part.write("\n")
    part.close()
  if result.len == 0:
    raise newException(IOError, "no encoded transport parts produced")
  writeFile(manifest, result.join("\n") & "\n")


proc obtainZip(options: Options; destination: string) =
  if options.offlineZip.len > 0:
    copyFile(options.offlineZip, destination)
    return
  let process = startProcess(
    "curl",
    args = [
      "--fail", "--location", "--retry", "3",
      "--output", destination,
      bulkUrl(options.cycle)
    ],
    options = {poUsePath, poParentStreams}
  )
  let code = process.waitForExit()
  process.close()
  if code != 0:
    raise newException(IOError, &"curl failed with exit code {code}")


proc parseOptions(): Options =
  result = Options(
    cycle: DefaultCycle,
    committeeId: DefaultCommitteeId,
    output: "digs/gop/2026-08-08-fec-individual-contributions-2026",
    generatedAt: DefaultGeneratedAt
  )
  var index = 1
  while index <= paramCount():
    let arg = paramStr(index)
    template take(): string =
      inc index
      if index > paramCount():
        raise newException(ValueError, "missing value for " & arg)
      paramStr(index)
    case arg
    of "--cycle": result.cycle = parseInt(take())
    of "--committee-id": result.committeeId = take().toUpperAscii()
    of "--output": result.output = take()
    of "--offline-zip": result.offlineZip = take()
    of "--generated-at": result.generatedAt = take()
    else: raise newException(ValueError, "unknown argument: " & arg)
    inc index


proc generate(zipPath: string; options: Options): JsonNode =
  if dirExists(options.output):
    removeDir(options.output)
  createDir(options.output)

  let tempJsonl = getTempDir() / ("starintel-rnc-" & $getCurrentProcessId() & ".jsonl")
  let tempGzip = tempJsonl & ".gz"
  defer:
    if fileExists(tempJsonl): removeFile(tempJsonl)
    if fileExists(tempGzip): removeFile(tempGzip)

  let sid = sourceId(options.cycle, options.committeeId)
  var output = open(tempJsonl, fmWrite)
  output.write($sourceDocument(options) & "\n")

  var seen = initHashSet[string]()
  var rawMatchingRows = 0
  var duplicateRows = 0
  let members = listMembers(zipPath)

  for member in members:
    let process = startProcess("unzip", args = ["-p", zipPath, member], options = {poUsePath})
    let stream = process.outputStream
    var line: string
    var lineNumber = 0
    while stream.readLine(line):
      inc lineNumber
      var row: ReceiptRow
      if not parseMatchingReceipt(line, options.committeeId, row):
        continue
      inc rawMatchingRows
      row.subId = row.subId.strip()
      if row.subId.len == 0:
        process.terminate()
        process.close()
        output.close()
        raise newException(ValueError, &"matching FEC row {member}:{lineNumber} lacks SUB_ID")
      if row.subId in seen:
        inc duplicateRows
        continue
      seen.incl(row.subId)
      if seen.len > MaxUniqueRows:
        process.terminate()
        process.close()
        output.close()
        raise newException(ValueError, &"unique rows exceed safety cap {MaxUniqueRows}")
      output.write($financeDocument(row, options, sid) & "\n")
    let code = process.waitForExit()
    process.close()
    if code != 0:
      output.close()
      raise newException(IOError, &"unzip failed for {member} with exit code {code}")

  output.close()
  if seen.len == 0:
    raise newException(ValueError, "no RNC receipt rows found")

  let documentSha = sha256(tempJsonl)
  gzipFile(tempJsonl, tempGzip)
  let parts = encodeParts(tempGzip, options.output)
  let sourceSha = sha256(zipPath)

  result = %*{
    "committee_id": options.committeeId,
    "contributor_employment_emitted": false,
    "contributor_identity_emitted": false,
    "contributor_location_emitted": false,
    "counts": {"campaign-finance": seen.len, "source": 1},
    "cycle": options.cycle,
    "dataset": Dataset,
    "document_part_count": parts.len,
    "document_sha256": documentSha,
    "duplicate_sub_id_rows": duplicateRows,
    "generated_at": options.generatedAt,
    "privacy_transform": "deidentified-fec-receipt-ledger-v4-nim-streaming",
    "raw_matching_rows": rawMatchingRows,
    "raw_source_members": jsonStrings(members),
    "raw_source_rows_embedded": false,
    "raw_source_zip_sha256": sourceSha,
    "reconciliation": "duplicate SUB_ID rows skipped; distinct amendment and memo rows preserved",
    "schema_version": "0.9.0",
    "total_documents": seen.len + 1,
    "unique_fec_sub_ids": seen.len
  }
  writeFile(options.output / "manifest.json", result.pretty() & "\n")
  writeFile(options.output / "README.md", &"""# GOP FEC de-identified individual-receipt ledger — {options.cycle}

Generated by the streaming Nim importer for `{options.committeeId}`.

- raw matching rows: {rawMatchingRows}
- duplicate SUB_ID rows skipped: {duplicateRows}
- unique receipt rows: {seen.len}
- published documents: {seen.len + 1}
- contributor identity/location/employment fields emitted: no
- raw contributor rows embedded: no
""")


proc main(): int =
  let options = parseOptions()
  if options.cycle mod 2 != 0:
    raise newException(ValueError, "cycle must be an even election year")
  if options.committeeId != DefaultCommitteeId:
    raise newException(ValueError, "privacy-preserving importer is scoped to " & DefaultCommitteeId)

  let tempDir = getTempDir() / ("starintel-fec-" & $getCurrentProcessId())
  if dirExists(tempDir): removeDir(tempDir)
  createDir(tempDir)
  defer: removeDir(tempDir)
  let year = $options.cycle
  let zipPath = tempDir / ("indiv" & year[^2 .. ^1] & ".zip")
  obtainZip(options, zipPath)
  let manifest = generate(zipPath, options)
  echo $(%*{
    "documents": manifest["total_documents"],
    "duplicate_rows": manifest["duplicate_sub_id_rows"],
    "output": options.output,
    "raw_rows": manifest["raw_matching_rows"],
    "unique_rows": manifest["unique_fec_sub_ids"]
  })
  result = 0


when isMainModule:
  try:
    quit(main())
  except CatchableError as exc:
    stderr.writeLine("error: " & exc.msg)
    quit(1)
