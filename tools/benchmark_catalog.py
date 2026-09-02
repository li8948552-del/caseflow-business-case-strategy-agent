#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "benchmarks" / "deck_catalog.json"
ALLOWED_SPLITS = {"reference", "calibration", "holdout", "challenge"}
REQUIRED_FIELDS = {
    "id",
    "competition",
    "year",
    "case_company",
    "industry",
    "placement",
    "placement_verified",
    "split",
    "case_url",
    "deck_url",
    "archive_url",
    "rights",
    "learning_focus",
}
BLIND_FIELDS = {"placement", "placement_verified", "team", "learning_focus"}


def load_catalog(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("decks"), list):
        raise ValueError("Catalog root must be an object containing a decks list")
    return data


def validate_catalog(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_decks: set[str] = set()

    for index, deck in enumerate(data["decks"]):
        label = f"decks[{index}]"
        if not isinstance(deck, dict):
            errors.append(f"{label}: must be an object")
            continue
        missing = REQUIRED_FIELDS - deck.keys()
        if missing:
            errors.append(f"{label}: missing fields {sorted(missing)}")
            continue

        deck_id = deck["id"]
        if not isinstance(deck_id, str) or not deck_id:
            errors.append(f"{label}: id must be a non-empty string")
        elif deck_id in seen_ids:
            errors.append(f"{label}: duplicate id {deck_id}")
        seen_ids.add(deck_id)

        if deck["split"] not in ALLOWED_SPLITS:
            errors.append(f"{deck_id}: invalid split {deck['split']!r}")
        if not isinstance(deck["year"], int) or not 2000 <= deck["year"] <= 2100:
            errors.append(f"{deck_id}: invalid year")
        if deck["placement"] not in {1, 2, 3}:
            errors.append(f"{deck_id}: placement must be 1, 2, or 3")
        if deck["placement_verified"] is not True:
            errors.append(f"{deck_id}: only verified placements belong in this catalog")
        if not isinstance(deck["industry"], list) or not deck["industry"]:
            errors.append(f"{deck_id}: industry must be a non-empty list")
        if not isinstance(deck["learning_focus"], list) or not deck["learning_focus"]:
            errors.append(f"{deck_id}: learning_focus must be a non-empty list")
        if deck["rights"] != "external-link-only":
            errors.append(f"{deck_id}: rights must remain external-link-only")

        for field in ("case_url", "deck_url", "archive_url"):
            parsed = urlparse(deck[field])
            if parsed.scheme != "https" or not parsed.netloc:
                errors.append(f"{deck_id}: {field} must be an absolute HTTPS URL")

        deck_url = deck["deck_url"]
        if deck_url in seen_decks:
            errors.append(f"{deck_id}: duplicate deck_url")
        seen_decks.add(deck_url)

    return errors


def select(data: dict[str, Any], split: str | None) -> list[dict[str, Any]]:
    decks = cast(list[dict[str, Any]], data["decks"])
    if split is None:
        return decks
    return [deck for deck in decks if deck["split"] == split]


def command_validate(data: dict[str, Any]) -> int:
    errors = validate_catalog(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    counts = {split: len(select(data, split)) for split in sorted(ALLOWED_SPLITS)}
    print(f"Catalog valid: {len(data['decks'])} decks; splits={counts}")
    return 0


def command_list(data: dict[str, Any], split: str | None) -> int:
    decks = select(data, split)
    for deck in decks:
        print(
            f"{deck['id']}: {deck['case_company']} ({deck['year']}), "
            f"place={deck['placement']}, split={deck['split']}"
        )
    print(f"Total: {len(decks)}")
    return 0


def command_export_blind(
    data: dict[str, Any], split: str, output: Path
) -> int:
    decks = select(data, split)
    blinded = [
        {key: value for key, value in deck.items() if key not in BLIND_FIELDS}
        for deck in decks
    ]
    payload = {
        "schema_version": data["schema_version"],
        "blind": True,
        "split": split,
        "decks": blinded,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(blinded)} blinded records to {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and inspect the CaseFlow deck catalog")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--split", choices=sorted(ALLOWED_SPLITS))

    export_parser = subparsers.add_parser("export-blind")
    export_parser.add_argument(
        "--split",
        choices=["calibration", "holdout", "challenge"],
        required=True,
    )
    export_parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        data = load_catalog(args.catalog)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.command == "validate":
        return command_validate(data)
    if args.command == "list":
        return command_list(data, args.split)
    return command_export_blind(data, args.split, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
