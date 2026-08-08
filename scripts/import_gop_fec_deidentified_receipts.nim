import std/[algorithm, base64, httpclient, json, os, osproc, sets, streams, strformat, strutils]


const
  Dataset = "gop"
  RncId = "starintel:org:republican-national-committee"
  CommitteeId = "C00003418"
  DefaultCycle = 2026
  DefaultGeneratedAt = "2026-08-08T21:50:00Z"
  DescriptionUrl = "https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/"
  PartSize = 30_000_000
  ReadChunk = 3 * 1024 * 1024
  MaxUniqueRows = 1_500_000


type ReceiptRow = object
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


type Options = object
  cycle: int
  committeeId: string
  output: string
  offlineZip: string
  generatedAt: string


proc bulkUrl(cycle: int): string =
  &"https://www.fec.gov/files/bulk-downloads/{cycle}/indiv{($cycle)[^2 .. ^1]}.zip"


proc sourceId(cycle: int; committeeId: string): string =
  &"starintel:source:fec-individual-contributions-{cycle}-gop-{committeeId.toLowerAscii()}"


proc setField(row: var ReceiptRow; index: int; value: string) =
  case index
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
  var i = start
  while i <= line.len:
    if i == line.len or line[i] == '|':
      if field <= 20:
        setField(row, field, line[start ..< i])
      inc field
      start = i + 1
    inc i

  if field < 21:
    raise newException(ValueError, &"unexpected FEC row width: only {field} fields")
  true


proc isoDate(value: string): JsonNode =
  let raw = value.strip()
  if raw.len == 0:
    return newJNull()
  if raw.len == 8 and raw.allCharsInSet({'0'..'9'}):
    return %(&"{raw[4..7]}-{raw[0..1]}-{raw[2..3]}T00:00:00Z")
  if raw.len == 10 and raw[2] == '/' and raw[5] == '/':
    return %(&"{raw[6..9]}-{raw[0..1]}-{raw[3..4]}T00:00:00Z")
  raise newException(ValueError, "invalid FEC date: " & raw)


proc amount(value: string): float =
  try:
    parseFloat(value.strip())
  except ValueError as exc:
    raise newException(ValueError, "invalid FEC amount " & value & ": " & exc.msg)


proc safeMetadata(row: ReceiptRow; committeeId: string): JsonNode =
  result = newJObject()
  template addIf(name: string; value: string) =
    if value.len > 0:
      result[name] = %value
  addIf("cmte_id", committeeId)
  addIf("amndt_ind", row.amendment)
  addIf("rpt_tp", row.reportType)
  addIf("transaction_pgi", row.primaryGeneral)
  addIf("image_num", row.imageNumber)
  addIf("transaction_tp", row.transactionType)
  addIf("entity_tp", row.entityType)
  addIf("transaction_dt", row.transactionDate)
  addIf("transaction_amt", row.transactionAmount)
  addIf("other_id", row.otherId)
  addIf("tran_id", row.transactionId)
  addIf("file_num", row.fileNumber)
  addIf("memo_cd", row.memoCode)
  addIf("sub_id", row.subId)


proc identifiers(row: ReceiptRow): JsonNode =
  result = newJArray()
  result.add(%*{
    "scheme": "fec_sub_id",
    "value": row.subId,
    "issuer": "Federal Election Commission",
    "canonical": true
  })
  template addIdentifier(schemeName: string; value: string) =
    if value.len > 0:
      result.add(%*{
        "scheme": schemeName,
        "value": value,
        "issuer": "Federal Election Commission",
        "canonical": false
      })
  addIdentifier("fec_file_num", row.fileNumber)
  addIdentifier("fec_transaction_id", row.transactionId)
  addIdentifier("fec_image_num", row.imageNumber)


proc sourceDocument(cycle: int; committeeId, when: string): JsonNode =
  %*{
    "_id": sourceId(cycle, committeeId),
    "data": {
      "accessed_at": when,
      "credibility": 0.99,
      "kind": "official_fec_bulk_file",
      "publisher": "Federal Election Commission",
      "uri": bulkUrl(cycle)
    },
    "dataset": Dataset,
    "date_added": when,
    "date_updated": when,
    "dtype": "source",
    "evidence": [],
    "extensions": {
      "privacy_transform": {
        "description_uri": DescriptionUrl,
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
    "summary": "Official FEC individual-contribution bulk source filtered to the Republican National Committee; published StarIntel records intentionally omit contributor identity and employment/location fields.",
    "tags": ["gop", "fec", "official-source", "individual-contribution", "deidentified"],
    "title": &"FEC {cycle} de-identified RNC individual-receipt source",
    "verification": {
      "last_reviewed_at": when,
      "status": "official-fec-record",
      "verified": true
    },
    "version": 1
  }


proc financeDocument(row: ReceiptRow; cycle: int; committeeId, when, source: string): JsonNode =
  let value = amount(row.transactionAmount)
  let date = isoDate(row.transactionDate)
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
      "committee_id": committeeId,
      "contribution_type": (if row.transactionType.len > 0: row.transactionType else: "reported_receipt"),
      "counterparty_ids": [RncId],
      "currency": "USD",
      "election_cycle": $cycle,
      "filing_id": row.fileNumber,
      "methodology": "Direct row import from the official FEC individual-contributions bulk file with contributor identity fields omitted.",
      "observation_type": "reported_itemized_contribution",
      "period_end": date,
      "period_start": date,
      "qualifications": qualifications,
      "recipient_id": RncId,
      "reported_at": newJNull(),
      "value_type": "reported_transaction_amount"
    },
    "dataset": Dataset,
    "date_added": when,
    "date_updated": when,
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
      "source_id": source,
      "locator": "SUB_ID " & row.subId,
      "metadata": safeMetadata(row, committeeId)
    }],
    "status": "recorded",
    "summary": &"Official FEC row reports ${value} as an itemized contribution or related receipt record to the Republican National Committee; contributor identity is intentionally omitted.",
    "tags": ["gop", "fec", "individual-contribution", "campaign-finance", "deidentified"],
    "title": "FEC contribution " & row.subId,
    "verification": {
      "last_reviewed_at": when,
      "status": "official-filing-record",
      "verified": true
    },
    "version": 1
  }


proc dataMembers(zipPath: string): seq[string] =
  let output = execProcess("unzip", args = ["-Z1", zipPath], options = {poUsePath})
  for raw in output.splitLines:
    let name = raw.strip()
    let lower = name.toLowerAscii()
    if name.len > 0 and (lower.endsWith(".txt") or lower.endsWith(".csv")):
      result.add(name)
  result.sort()
  if result.len == 0:
    raise newException(ValueError, "FEC ZIP contains no text data files")


proc hashFile(path: string): string =
  let output = execProcess("sha256sum", args = [path], options = {poUsePath}).strip()
  let pieces = output.splitWhitespace()
  if pieces.len == 0:
    raise newException(IOError, "sha256sum produced no digest for " & path)
  pieces[0]


proc compress(path, gzipPath: string) =
  let command = "gzip -9 -n -c " & quoteShell(path) & " > " & quoteShell(gzipPath)
  let code = execShellCmd(command)
  if code != 0:
    raise newException(IOError, "gzip failed with exit code " & $code)


proc encodeParts(gzipPath, output: string): seq[string] =
  let base = output / "starintel-documents.jsonl.gz.b64"
  let manifest = base & ".parts"
  for path in walkFiles(base & ".part-*"):
    removeFile(path)
  if fileExists(manifest):
    removeFile(manifest)

  var input = open(gzipPath, fmRead)
  defer: input.close()
  var part: File
  var partOpen = false
  var partBytes = 0
  var partIndex = 0
  var names: seq[string]

  proc openPart() =
    let name = lastPathPart(base) & &".part-{partIndex:04d}"
    part = open(output / name, fmWrite)
    partOpen = true
    partBytes = 0
    names.add(name)
    inc partIndex

  proc closePart() =
    if partOpen:
      part.write("\n")
      part.close()
      partOpen = false

  var buffer = newString(ReadChunk)
  while true:
    let read = input.readBuffer(addr buffer[0], buffer.len)
    if read <= 0:
      break
    buffer.setLen(read)
    let encoded = encode(buffer)
    var offset = 0
    while offset < encoded.len:
      if not partOpen:
        openPart()
      let room = PartSize - partBytes
      let take = min(room, encoded.len - offset)
      part.write(encoded[offset ..< offset + take])
      partBytes += take
      offset += take
      if partBytes >= PartSize:
        closePart()
    buffer.setLen(ReadChunk)
  closePart()

  if names.len == 0:
    raise newException(IOError, "no encoded document parts were produced")
  writeFile(manifest, names.join("\n") & "\n")
  names


proc download(url, destination: string) =
  var client = newHttpClient(userAgent = "StarIntel-AutoDig/0.9 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)")
  defer: client.close()
  client.downloadFile(url, destination)


proc parseOptions(): Options =
  result = Options(
    cycle: DefaultCycle,
    committeeId: CommitteeId,
    output: "digs/gop/2026-08-08-fec-individual-contributions-2026",
    generatedAt: DefaultGeneratedAt
  )
  var index = 1
  while index <= paramCount():
    let arg = paramStr(index)
    template nextValue(): string =
      inc index
      if index > paramCount():
        raise newException(ValueError, "missing value for " & arg)
      paramStr(index)
    case arg
    of "--cycle": result.cycle = parseInt(nextValue())
    of "--committee-id": result.committeeId = nextValue().toUpperAscii()
    of "--output": result.output = nextValue()
    of "--offline-zip": result.offlineZip = nextValue()
    of "--generated-at": result.generatedAt = nextValue()
    else: raise newException(ValueError, "unknown argument: " & arg)
    inc index


proc generate(zipPath: string; options: Options): JsonNode =
  if dirExists(options.output):
    removeDir(options.output)
  createDir(options.output)

  let members = dataMembers(zipPath)
  let source = sourceId(options.cycle, options.committeeId)
  let tempJsonl = getTempDir() / ("gop-rnc-receipts-" & $getCurrentProcessId() & ".jsonl")
  let tempGzip = tempJsonl & ".gz"
  defer:
    if fileExists(tempJsonl): removeFile(tempJsonl)
    if fileExists(tempGzip): removeFile(tempGzip)

  var output = open(tempJsonl, fmWrite)
  defer:
    if output != nil:
      output.close()

  output.write($sourceDocument(options.cycle, options.committeeId, options.generatedAt) & "\n")

  var seen = initHashSet[string](1 shl 20)
  var rawMatchingRows = 0
  var duplicateRows = 0

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
        raise newException(ValueError, &"matching FEC row {member}:{lineNumber} lacks SUB_ID")
      if row.subId in seen:
        inc duplicateRows
        continue
      seen.incl(row.subId)
      if seen.len > MaxUniqueRows:
        process.terminate()
        process.close()
        raise newException(ValueError, &"unique RNC FEC receipt rows exceed safety cap {MaxUniqueRows}")
      output.write($financeDocument(row, options.cycle, options.committeeId, options.generatedAt, source) & "\n")
    let code = process.waitForExit()
    process.close()
    if code != 0:
      raise newException(IOError, &"unzip failed for {member} with exit code {code}")

  output.close()
  output = nil
  if seen.len == 0:
    raise newException(ValueError, "no individual-contribution rows found for " & options.committeeId)

  let documentSha = hashFile(tempJsonl)
  compress(tempJsonl, tempGzip)
  let parts = encodeParts(tempGzip, options.output)
  let zipSha = hashFile(zipPath)

  result = %*{
    "committee_id": options.committeeId,
    "contributor_employment_emitted": false,
    "contributor_identity_emitted": false,
    "contributor_location_emitted": false,
    "counts": {
      "campaign-finance": seen.len,
      "source": 1
    },
    "cycle": options.cycle,
    "dataset": Dataset,
    "document_part_count": parts.len,
    "document_sha256": documentSha,
    "duplicate_sub_id_rows": duplicateRows,
    "generated_at": options.generatedAt,
    "privacy_transform": "deidentified-fec-receipt-ledger-v3-nim-streaming",
    "raw_matching_rows": rawMatchingRows,
    "raw_source_members": members,
    "raw_source_rows_embedded": false,
    "raw_source_zip_sha256": zipSha,
    "reconciliation": "duplicate SUB_ID rows skipped; amendment and memo rows with distinct SUB_IDs preserved",
    "schema_version": "0.9.0",
    "total_documents": seen.len + 1,
    "unique_fec_sub_ids": seen.len
  }
  writeFile(options.output / "manifest.json", result.pretty() & "\n")
  writeFile(options.output / "README.md", &"""# GOP FEC de-identified individual-receipt ledger — {options.cycle} cycle

Official FEC rows filtered to `{options.committeeId}` by the Nim streaming importer.

- raw matching FEC rows: {rawMatchingRows}
- duplicate `SUB_ID` rows skipped: {duplicateRows}
- unique FEC receipt rows: {seen.len}
- published StarIntel documents: {seen.len + 1}
- contributor names emitted: no
- contributor locations emitted: no
- contributor employers/occupations emitted: no
- raw contributor rows embedded: no

The importer rejects irrelevant rows after reading only the committee-ID field, then parses only the non-PII columns needed for the public ledger.

```bash
nim c -d:release --out:bin/import-gop-receipts scripts/import_gop_fec_deidentified_receipts.nim
bin/import-gop-receipts
```
""")


proc main(): int =
  let options = parseOptions()
  if options.cycle mod 2 != 0:
    raise newException(ValueError, "FEC cycle must be an even-numbered election cycle")
  if options.committeeId != CommitteeId:
    raise newException(ValueError, "this privacy-preserving importer is intentionally scoped to RNC committee " & CommitteeId)

  let temporary = getTempDir() / ("gop-fec-rnc-" & $getCurrentProcessId())
  if dirExists(temporary): removeDir(temporary)
  createDir(temporary)
  defer: removeDir(temporary)
  let zipPath = temporary / &"indiv{($options.cycle)[^2 .. ^1]}.zip"
  if options.offlineZip.len > 0:
    copyFile(options.offlineZip, zipPath)
  else:
    download(bulkUrl(options.cycle), zipPath)

  let manifest = generate(zipPath, options)
  echo $(%*{
    "documents": manifest["total_documents"],
    "duplicate_rows": manifest["duplicate_sub_id_rows"],
    "output": options.output,
    "raw_rows": manifest["raw_matching_rows"],
    "unique_rows": manifest["unique_fec_sub_ids"]
  })
  0


when isMainModule:
  try:
    quit(main())
  except CatchableError as exc:
    stderr.writeLine("error: " & exc.msg)
    quit(1)
