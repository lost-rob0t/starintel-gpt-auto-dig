# Read-only presentation compatibility. This module never rewrites source records.
import std/[json, times, strutils]

proc projectionText*(node: JsonNode; key: string; fallback = ""): string =
  if node != nil and node.kind == JObject and node.hasKey(key) and node[key].kind == JString:
    return node[key].getStr()
  fallback

proc nativeDocument*(node: JsonNode): bool =
  node.kind == JObject and (node.hasKey("schemaVersion") or node.hasKey("id"))

proc documentId*(node: JsonNode): string =
  projectionText(node, if nativeDocument(node): "id" else: "_id")

proc documentVersion*(node: JsonNode): string =
  projectionText(node, if nativeDocument(node): "schemaVersion" else: "schema_version")

proc documentTime*(node: JsonNode; added = false): string =
  if not nativeDocument(node):
    return projectionText(node, if added: "date_added" else: "date_updated")
  let key = if added: "createdAt" else: "updatedAt"
  if node.hasKey(key) and node[key].kind == JInt and node[key].getBiggestInt() >= 0:
    return fromUnix(node[key].getBiggestInt()).utc.format("yyyy-MM-dd'T'HH:mm:ss'Z'")

proc relationPayload*(node: JsonNode): JsonNode =
  if nativeDocument(node): return node
  if node.hasKey("data") and node["data"].kind == JObject: return node["data"]
  newJObject()

proc relationEndpoint*(node: JsonNode; destination = false): JsonNode =
  let key = if nativeDocument(node): (if destination: "destination" else: "source")
            else: (if destination: "object" else: "subject")
  let payload = relationPayload(node)
  if payload.hasKey(key): return payload[key]
  newJNull()

proc emptyPolicy(node: JsonNode): bool =
  node.kind == JNull or (node.kind == JString and node.getStr().len == 0) or
    (node.kind == JObject and node.len == 0)

proc policyKey(key: string): string =
  key.replace("_", "").replace("-", "").toLowerAscii()

proc permissiveHandling(node: JsonNode): bool =
  if node.kind == JNull: return true
  if node.kind == JString:
    return node.getStr().strip().toLowerAscii() in ["public", "public-source-only"]
  if node.kind != JObject: return false
  let explicitPublic = projectionText(node, "visibility") == "public"
  # Newly recognized annotations are compatibility-only. Ambiguous handling
  # marked sensitive remains excluded pending explicit publication review.
  let safeAnnotation = explicitPublic and (not node.hasKey("sensitive") or
    (node["sensitive"].kind == JBool and not node["sensitive"].getBool()))
  for key, flag in node.pairs:
    case policyKey(key)
    of "handling", "legacyhandling":
      if flag.kind == JString and flag.getStr().strip().toLowerAscii() in [
          "public-source only", "public-source-research",
          "public-source-research-no-credentials", "verified-source-evidence",
          "verified-source-artifact"]:
        if not safeAnnotation: return false
      elif not permissiveHandling(flag): return false
    of "public":
      if flag.kind != JBool or not flag.getBool(): return false
    of "visibility", "sensitivity":
      if flag.kind != JString or flag.getStr() != "public": return false
    of "restricted", "confidential", "classified", "deleted":
      if flag.kind != JBool or flag.getBool(): return false
    of "classification":
      if not safeAnnotation or flag.kind != JString or
          flag.getStr().toLowerAscii() notin ["public", "unclassified"]: return false
    of "notes":
      if not safeAnnotation or flag.kind != JString: return false
    of "caveats", "redactions":
      if not safeAnnotation or flag.kind != JArray: return false
      for annotation in flag.items:
        if annotation.kind != JString: return false
    of "sensitive", "pii":
      # Content indicators are not access permissions. Historical public
      # professional/source records may legitimately carry either marker.
      if flag.kind != JBool: return false
    else: return false
  true

proc hasRestriction(node: JsonNode; policyContext = false): bool =
  case node.kind
  of JObject:
    for key, value in node.pairs:
      let normalized = policyKey(key)
      if normalized in ["handling", "legacyhandling"]:
        if not permissiveHandling(value): return true
        # The structured policy was evaluated in its own context. Do not
        # reinterpret public evidence caveats/classification as a second ACL.
        continue
      elif normalized in ["visibility", "sensitivity"]:
        if value.kind != JString or value.getStr() != "public": return true
      elif normalized in ["restricted", "confidential", "classified", "deleted"]:
        if value.kind != JBool or value.getBool(): return true
      elif normalized in ["accesscontrol", "acl", "retentionpolicy", "classification",
                          "dissemination", "embargo"]:
        if not emptyPolicy(value): return true
      # Domain payloads (e.g. assessment.caveats) are evidence, not access
      # policy. Recurse only through policy/metadata containers, then inspect
      # their descendants conservatively.
      if policyContext or normalized in ["metadata", "extensions", "provenance", "lineage"]:
        if hasRestriction(value, true): return true
  of JArray:
    for value in node.items:
      if hasRestriction(value, policyContext): return true
  else: discard

proc publicProjectionAllowed*(node: JsonNode): bool =
  if node.kind != JObject: return false
  if nativeDocument(node) and projectionText(node, "collectionStatus") == "deleted":
    return false
  if nativeDocument(node) and (projectionText(node, "visibility") != "public" or
      projectionText(node, "sensitivity") != "public"):
    return false
  # Inspect retained compatibility metadata too; a public top-level label must
  # not override restrictive source handling. Unspecified historical handling
  # remains readable solely for the established historical public corpus.
  not hasRestriction(node)

proc presentationSources*(node: JsonNode): JsonNode =
  # Direct source URLs are the human-readable projection when supplied;
  # typed source references remain untouched in the canonical bulk payload.
  if nativeDocument(node) and node.hasKey("sourceUrls") and
      node["sourceUrls"].kind == JArray and node["sourceUrls"].len > 0:
    return node["sourceUrls"]
  if node.hasKey("sources") and node["sources"].kind == JArray:
    return node["sources"]
  newJArray()
