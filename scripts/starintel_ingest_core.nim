## Threaded StarIntel bulk ingest core.
##
## Reads canonical StarIntel documents as JSONL from stdin and submits bounded
## /documents/bulk jobs in parallel. Network workers are Nim threadpool workers;
## each worker owns its HTTP requests and no credential is passed on the command
## line. POST retries are deliberately conservative: without a server-side
## idempotency key, an ambiguous retry can publish the same batch twice.

import std/[cpuinfo, httpclient, json, os, strutils, threadpool, times]

const
  DefaultServerUrl = "https://ingest.starintel.actor"
  DefaultBatchSize = 500
  MaxBatchSize = 500
  # starintel-server currently permits four pending bulk jobs per principal.
  # Auto mode therefore uses every useful core without creating guaranteed 429s.
  DefaultServerPrincipalConcurrency = 4
  DefaultTimeoutMs = 30_000
  DefaultPollIntervalMs = 200
  DefaultPollTimeoutMs = 180_000
  DefaultRetries = 6


type
  Options = object
    serverUrl: string
    batchSize: int
    workers: int
    timeoutMs: int
    pollTimeoutMs: int
    retries: int

  UploadResult = object
    ok: bool
    batchNo: int
    documents: int
    status: string
    error: string

  TerminalRequestError = object of CatchableError


proc fail(message: string): void =
  stderr.writeLine(message)
  quit(QuitFailure)


proc parseIntOption(value, name: string; minimum, maximum: int): int =
  try:
    result = parseInt(value)
  except ValueError:
    fail(name & " must be an integer")
  if result < minimum or result > maximum:
    fail(name & " must be between " & $minimum & " and " & $maximum)


proc parseArgs(): Options =
  result.serverUrl = getEnv("STAR_INGEST_URL", DefaultServerUrl)
  result.batchSize = DefaultBatchSize
  result.workers = 0
  result.timeoutMs = DefaultTimeoutMs
  result.pollTimeoutMs = DefaultPollTimeoutMs
  result.retries = DefaultRetries

  let args = commandLineParams()
  var i = 0
  while i < args.len:
    let arg = args[i]
    template requireValue(): string =
      if i + 1 >= args.len:
        fail(arg & " requires a value")
      inc i
      args[i]

    case arg
    of "--server-url":
      result.serverUrl = requireValue()
    of "--batch-size":
      result.batchSize = parseIntOption(requireValue(), "--batch-size", 1, MaxBatchSize)
    of "--workers":
      result.workers = parseIntOption(requireValue(), "--workers", 0, MaxThreadPoolSize)
    of "--timeout-ms":
      result.timeoutMs = parseIntOption(requireValue(), "--timeout-ms", 1, 3_600_000)
    of "--poll-timeout-ms":
      result.pollTimeoutMs = parseIntOption(requireValue(), "--poll-timeout-ms", 1, 3_600_000)
    of "--retries":
      result.retries = parseIntOption(requireValue(), "--retries", 0, 20)
    of "--help", "-h":
      stdout.writeLine("Usage: starintel-ingest-core [options] < documents.jsonl")
      stdout.writeLine("  --server-url URL       StarIntel ingest base URL")
      stdout.writeLine("  --batch-size N         documents/request (1-500, default 500)")
      stdout.writeLine("  --workers N            concurrent Nim workers; 0=auto")
      stdout.writeLine("  --timeout-ms N         HTTP socket timeout")
      stdout.writeLine("  --poll-timeout-ms N    async bulk-job deadline")
      stdout.writeLine("  --retries N            safe transient retries")
      quit(QuitSuccess)
    else:
      fail("unknown argument: " & arg)
    inc i

  if result.serverUrl.len == 0:
    fail("--server-url may not be empty")


proc trimTrailingSlashes(value: string): string =
  result = value
  while result.len > 0 and result[^1] == '/':
    result.setLen(result.len - 1)


proc resolveUrl(baseUrl, path: string): string =
  if path.startsWith("http://") or path.startsWith("https://"):
    return path
  let base = trimTrailingSlashes(baseUrl)
  if path.startsWith("/"):
    return base & path
  base & "/" & path


proc jsonString(node: JsonNode; key: string): string =
  if node.kind == JObject and node.hasKey(key) and node[key].kind == JString:
    return node[key].getStr()
  ""


proc jsonInt(node: JsonNode; key: string): int =
  if node.kind == JObject and node.hasKey(key) and node[key].kind == JInt:
    return int(node[key].getInt())
  0


proc requireJsonInt(node: JsonNode; key: string): int =
  if node.kind != JObject or not node.hasKey(key) or node[key].kind != JInt:
    raise newException(TerminalRequestError, "bulk ingest response is missing integer " & key)
  int(node[key].getInt())


proc transientStatus(code: int): bool =
  case code
  of 429, 502, 503, 504:
    true
  else:
    false


proc safeToRetryResponse(httpMethod: HttpMethod; code: int): bool =
  # A returned 429 means the server rejected this submission before accepting a
  # bulk job, so retrying the POST is safe. Gateway/server failures for POST are
  # ambiguous: the server may already have accepted the job.
  code == 429 or (httpMethod == HttpGet and transientStatus(code))


proc retryDelayMs(attempt: int): int =
  min(8_000, 250 * (1 shl min(attempt, 5)))


proc requestJson(
    httpMethod: HttpMethod,
    url, apiKey, body: string,
    timeoutMs, retries: int
): JsonNode =
  var attempt = 0
  while true:
    var client: HttpClient = nil
    try:
      let headers = newHttpHeaders({
        "Accept": "application/json",
        "Authorization": "Bearer " & apiKey,
        "User-Agent": "starintel-auto-dig-ingest/2",
        "Content-Type": "application/json",
      })
      client = newHttpClient(timeout = timeoutMs, headers = headers)
      let response = client.request(url, httpMethod = httpMethod, body = body)
      let code = int(response.code)
      let raw = response.body

      if code >= 200 and code < 300:
        if raw.strip().len == 0:
          return newJObject()
        try:
          let parsed = parseJson(raw)
          if parsed.kind != JObject:
            raise newException(
              TerminalRequestError,
              $httpMethod & " " & url & " returned non-object JSON",
            )
          return parsed
        except JsonParsingError as exc:
          raise newException(
            TerminalRequestError,
            $httpMethod & " " & url & " returned invalid JSON: " & exc.msg,
          )

      if safeToRetryResponse(httpMethod, code) and attempt < retries:
        sleep(retryDelayMs(attempt))
        inc attempt
        continue

      let detail = if raw.len > 1000: raw[0 ..< 1000] else: raw
      let retryNote =
        if httpMethod == HttpPost and transientStatus(code) and code != 429:
          " (POST not retried because acceptance is ambiguous without idempotency)"
        else:
          ""
      raise newException(
        TerminalRequestError,
        $httpMethod & " " & url & " failed with HTTP " & $code & ": " & detail & retryNote,
      )
    except TerminalRequestError:
      raise
    except CatchableError as exc:
      if httpMethod == HttpPost:
        raise newException(
          IOError,
          $httpMethod & " " & url & " failed ambiguously and was not retried to avoid duplicate ingestion: " & exc.msg,
        )
      if attempt >= retries:
        raise newException(IOError, $httpMethod & " " & url & " failed: " & exc.msg)
      sleep(retryDelayMs(attempt))
      inc attempt
    finally:
      if client != nil:
        client.close()


proc waitForJob(
    serverUrl, apiKey, statusUrl: string,
    timeoutMs, pollTimeoutMs, retries: int
): JsonNode =
  let deadline = epochTime() + (float(pollTimeoutMs) / 1000.0)
  let url = resolveUrl(serverUrl, statusUrl)

  while true:
    let response = requestJson(HttpGet, url, apiKey, "", timeoutMs, retries)
    let status = jsonString(response, "status").toLowerAscii()
    if status == "completed" or status == "completed-with-errors" or status == "failed":
      let failed = jsonInt(response, "failed")
      if status != "completed" or failed != 0:
        raise newException(TerminalRequestError, "bulk ingest job failed: " & $response)
      return response

    if epochTime() >= deadline:
      raise newException(TerminalRequestError, "timed out waiting for bulk ingest job " & statusUrl)
    sleep(DefaultPollIntervalMs)


proc validateCompletedBatch(response: JsonNode; expectedDocuments: int): string =
  let status = jsonString(response, "status").toLowerAscii()
  if status == "failed" or status == "completed-with-errors" or status == "accepted":
    raise newException(TerminalRequestError, "bulk ingest did not complete successfully: " & $response)
  if status.len > 0 and status != "completed":
    raise newException(TerminalRequestError, "unexpected bulk ingest status " & status & ": " & $response)

  let total = requireJsonInt(response, "total")
  let succeeded = requireJsonInt(response, "succeeded")
  let failed = requireJsonInt(response, "failed")
  if total != expectedDocuments:
    raise newException(
      TerminalRequestError,
      "bulk ingest total mismatch: expected " & $expectedDocuments & ", got " & $total,
    )
  if failed != 0 or succeeded != expectedDocuments:
    raise newException(TerminalRequestError, "bulk ingest reported incomplete success: " & $response)

  if status.len > 0: status else: "inline"


proc uploadBatch(
    batchNo, documentCount: int,
    payload, serverUrl, apiKey: string,
    timeoutMs, pollTimeoutMs, retries: int
): UploadResult {.gcsafe.} =
  {.cast(gcsafe).}:
    result.batchNo = batchNo
    result.documents = documentCount
    try:
      let response = requestJson(
        HttpPost,
        resolveUrl(serverUrl, "/documents/bulk"),
        apiKey,
        payload,
        timeoutMs,
        retries,
      )
      let status = jsonString(response, "status").toLowerAscii()
      let statusUrl = jsonString(response, "status_url")
      var completed = response
      if status == "accepted":
        if statusUrl.len == 0:
          raise newException(
            TerminalRequestError,
            "bulk ingest was accepted without status_url; refusing to resubmit an ambiguous batch",
          )
        completed = waitForJob(
          serverUrl,
          apiKey,
          statusUrl,
          timeoutMs,
          pollTimeoutMs,
          retries,
        )

      result.status = validateCompletedBatch(completed, documentCount)
      result.ok = true
    except CatchableError as exc:
      result.ok = false
      result.error = exc.msg


proc readDocuments(): seq[string] =
  var lineNo = 0
  for rawLine in stdin.lines:
    inc lineNo
    let line = rawLine.strip()
    if line.len == 0:
      continue
    try:
      let node = parseJson(line)
      if node.kind != JObject:
        fail("stdin:" & $lineNo & ": document must be a JSON object")
      if not node.hasKey("_id") or node["_id"].kind != JString or node["_id"].getStr().len == 0:
        fail("stdin:" & $lineNo & ": document is missing non-empty _id")
      if not node.hasKey("dtype") or node["dtype"].kind != JString or node["dtype"].getStr().len == 0:
        fail("stdin:" & $lineNo & ": document is missing dtype")
    except JsonParsingError as exc:
      fail("stdin:" & $lineNo & ": invalid JSON: " & exc.msg)
    result.add(line)


proc makePayload(documents: seq[string]; first, pastLast: int): string =
  result = "["
  for i in first ..< pastLast:
    if i > first:
      result.add(',')
    result.add(documents[i])
  result.add(']')


proc main(): int =
  let options = parseArgs()
  let documents = readDocuments()
  if documents.len == 0:
    stdout.writeLine($( %*{
      "status": "completed",
      "documents": 0,
      "batches": 0,
      "workers": 0,
    }))
    return 0

  let apiKey = getEnv("STAR_SERVER_API_KEY")
  if apiKey.len == 0:
    stderr.writeLine("STAR_SERVER_API_KEY is required")
    return 2

  var payloads: seq[tuple[documents: int, payload: string]]
  var first = 0
  while first < documents.len:
    let pastLast = min(first + options.batchSize, documents.len)
    payloads.add((pastLast - first, makePayload(documents, first, pastLast)))
    first = pastLast

  let cores = max(1, countProcessors())
  var workers = options.workers
  if workers == 0:
    workers = min(cores, DefaultServerPrincipalConcurrency)
  workers = max(1, min(workers, payloads.len))

  setMinPoolSize(workers)
  setMaxPoolSize(workers)

  stdout.writeLine($( %*{
    "status": "starting",
    "documents": documents.len,
    "batches": payloads.len,
    "logical_cores": cores,
    "workers": workers,
    "batch_size": options.batchSize,
    "server_url": options.serverUrl,
  }))

  let started = epochTime()
  var futures: seq[FlowVar[UploadResult]]
  for index, batch in payloads:
    futures.add(spawn uploadBatch(
      index + 1,
      batch.documents,
      batch.payload,
      options.serverUrl,
      apiKey,
      options.timeoutMs,
      options.pollTimeoutMs,
      options.retries,
    ))

  var failures = 0
  var uploaded = 0
  for future in futures:
    let batch = ^future
    if batch.ok:
      uploaded += batch.documents
      stdout.writeLine($( %*{
        "status": "batch-completed",
        "batch": batch.batchNo,
        "batch_documents": batch.documents,
        "server_status": batch.status,
        "uploaded": uploaded,
        "total": documents.len,
      }))
    else:
      inc failures
      stderr.writeLine($( %*{
        "status": "batch-failed",
        "batch": batch.batchNo,
        "batch_documents": batch.documents,
        "error": batch.error,
      }))

  sync()
  let elapsed = max(0.001, epochTime() - started)
  stdout.writeLine($( %*{
    "status": (if failures == 0: "completed" else: "failed"),
    "documents": documents.len,
    "uploaded": uploaded,
    "batches": payloads.len,
    "failed_batches": failures,
    "workers": workers,
    "elapsed_seconds": elapsed,
    "documents_per_second": float(uploaded) / elapsed,
  }))

  if failures == 0: 0 else: 1


when isMainModule:
  quit(main())
