# Package
version = "0.1.0"
author = "StarIntel"
description = "Nim-first StarIntel AutoDig validation, FEC ingest, and static-site pipeline"
license = "GPL-3.0-or-later"

requires "nim >= 2.2.0"

const nimFlags = "-d:release --opt:speed --mm:orc --path:scripts"
const runtimePath = ".starintel-doc-nim/src"

task buildFast, "Build speed-critical StarIntel binaries":
  exec "mkdir -p bin"
  exec "nim c " & nimFlags & " --path:" & runtimePath & " --out:bin/starintel-validate scripts/starintel_validate.nim"
  exec "nim c " & nimFlags & " --out:bin/starintel-site scripts/starintel_site.nim"
  exec "nim c " & nimFlags & " --out:bin/validate-for-merge scripts/validate-for-merge.nim"
  exec "nim c " & nimFlags & " -d:ssl --out:bin/import-gop-receipts scripts/import_gop_fec_deidentified_receipts.nim"

task validate, "Validate corpus and emit ./unverifed source audit":
  exec "nimble buildFast"
  exec "bin/validate-for-merge"

task validateSite, "Run the complete Nim merge gate including site generation":
  exec "nimble buildFast"
  exec "bin/validate-for-merge --site"

task site, "Build the research site with the Nim generator":
  exec "nimble buildFast"
  exec "bin/starintel-site --input digs --db db --output _site --org-output .generated/org"
