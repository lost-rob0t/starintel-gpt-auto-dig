#!/usr/bin/env python3
"""Transactional canonical writer; historical local research writes are explicit."""
import argparse
import json
import runpy
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if len(sys.argv) > 1 and sys.argv[1] == "--legacy-research-profile":
    del sys.argv[1]
    runpy.run_path(str(ROOT / "scripts/create-db-document-legacy.py"), run_name="__main__")
    raise SystemExit(0)
from starintel_doc.canonical import DOCUMENT_TYPES, SPEC_VERSION, validate_document
from starintel_doc.writer import write_db_document
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("dtype", choices=sorted(DOCUMENT_TYPES))
parser.add_argument("--dataset", required=True)
parser.add_argument("--id", required=True)
parser.add_argument("--fields", default="{}", help="Flat generated fields as JSON or @path")
parser.add_argument("--root", type=Path, default=ROOT)
parser.add_argument("--replace", action="store_true")
args = parser.parse_args()
fields = json.loads(Path(args.fields[1:]).read_text() if args.fields.startswith("@") else args.fields)
document = {**fields, "id": args.id, "dataset": args.dataset, "dtype": args.dtype, "schemaVersion": SPEC_VERSION}
validate_document(document)
path = write_db_document(args.root, document, replace=args.replace)
print(path.relative_to(args.root.resolve()))
