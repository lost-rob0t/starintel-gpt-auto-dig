"""Default StarLang wire tooling; historical research commands require an explicit flag."""
import argparse
import json
import sys
from pathlib import Path
from .canonical import DOCUMENT_TYPES, SPEC_VERSION, load_schema, validate_document
from .writer import write_db_document


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--legacy-research-profile":
        from .cli_legacy import main as legacy_main
        return legacy_main(argv[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("types")
    schema = sub.add_parser("schema")
    schema.add_argument("--dtype", choices=sorted(DOCUMENT_TYPES))
    schema.add_argument("--output")
    create = sub.add_parser("create")
    create.add_argument("dtype", choices=sorted(DOCUMENT_TYPES))
    create.add_argument("--dataset", required=True)
    create.add_argument("--id", required=True)
    create.add_argument("--fields", default="{}", help="Flat generated fields as JSON or @path")
    create.add_argument("--output")
    create.add_argument("--pretty", action="store_true")
    ingest = sub.add_parser("import")
    ingest.add_argument("source", type=Path)
    ingest.add_argument("--root", type=Path, default=Path.cwd())
    ingest.add_argument("--replace", action="store_true")
    for name in ("search", "validate"):
        sub.add_parser(name, add_help=False)
    args, remaining = parser.parse_known_args(argv)
    if args.command in {"search", "validate"}:
        from .cli_legacy import main as legacy_main
        return legacy_main(argv)
    if remaining:
        parser.error("unrecognized arguments: " + " ".join(remaining))
    if args.command == "types":
        print("\n".join(sorted(DOCUMENT_TYPES)))
        return 0
    if args.command == "schema":
        value = load_schema()
        if args.dtype:
            value["$ref"] = "#/$defs/" + DOCUMENT_TYPES[args.dtype]
    elif args.command == "create":
        fields = json.loads(Path(args.fields[1:]).read_text() if args.fields.startswith("@") else args.fields)
        value = {**fields, "id": args.id, "dataset": args.dataset, "dtype": args.dtype, "schemaVersion": SPEC_VERSION}
        validate_document(value)
        if args.output and "db" in Path(args.output).parts:
            parser.error("normalized DB writes must use the transactional import/writer")
    elif args.command == "import":
        documents = [json.loads(raw) for raw in args.source.read_text().splitlines() if raw.strip()]
        for document in documents:
            validate_document(document)
        for document in documents:
            write_db_document(args.root, document, replace=args.replace)
        print(json.dumps({"imported": len(documents)}))
        return 0
    payload = json.dumps(value, indent=2 if args.command == "schema" or args.pretty else None) + "\n"
    if args.output:
        Path(args.output).write_text(payload)
    else:
        print(payload, end="")
    return 0
