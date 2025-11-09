"""Command line interface for interacting with Airtable."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .airtable import AirtableClient
from .config import load_config


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Interact with Airtable data")
    parser.add_argument(
        "command",
        choices={"list", "get"},
        help="Operation to perform",
    )
    parser.add_argument(
        "identifier",
        nargs="?",
        help="Table name for 'list' or record id for 'get'",
    )
    parser.add_argument(
        "--view",
        help="View to use when fetching records",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        help="Maximum number of records to return",
    )
    parser.add_argument(
        "--filter",
        dest="filter_formula",
        help="Airtable filter formula",
    )
    parser.add_argument(
        "--fields",
        nargs="*",
        help="Subset of fields to return",
    )
    return parser


def _print_json(data: Any) -> None:
    json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    config = load_config()
    client = AirtableClient(config)

    if args.command == "list":
        table = args.identifier
        records = client.list_records(
            table=table,
            view=args.view,
            filter_formula=args.filter_formula,
            fields=args.fields,
            max_records=args.max_records,
        )
        _print_json(records)
        return 0

    if args.command == "get":
        if not args.identifier:
            parser.error("A record id must be provided for the 'get' command")
        record = client.get_record(args.identifier)
        _print_json(record)
        return 0

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
