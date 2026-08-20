import std/json


const LegacyFileFormatNote* = "normalized legacy source data.file_format to data.medium"


proc normalizeLegacyDocument*(document: JsonNode): string =
  if document.kind != JObject or
     not document.hasKey("dtype") or
     document["dtype"].kind != JString or
     document["dtype"].getStr != "source" or
     not document.hasKey("data") or
     document["data"].kind != JObject or
     not document["data"].hasKey("file_format"):
    return ""

  let data = document["data"]
  let legacyValue = data["file_format"]
  if data.hasKey("medium") and data["medium"] != legacyValue:
    return "$.data: conflicting legacy 'file_format' and canonical 'medium' values"

  data["medium"] = legacyValue
  data.delete("file_format")

  if not document.hasKey("lineage"):
    document["lineage"] = newJObject()
  elif document["lineage"].kind != JObject:
    return "$.lineage: expected object while recording legacy normalization"

  let lineage = document["lineage"]
  if not lineage.hasKey("migration_notes"):
    lineage["migration_notes"] = newJArray()
  elif lineage["migration_notes"].kind != JArray:
    return "$.lineage.migration_notes: expected array while recording legacy normalization"

  lineage["migration_notes"].add(%LegacyFileFormatNote)
  ""
