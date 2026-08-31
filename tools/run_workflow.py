#!/usr/bin/env python3
"""Initialize, inspect, gate and validate CaseFlow without third-party packages."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "AGENTS.md",
    "competition/rules.yaml",
    "competition/rubric.yaml",
    "inputs/team-profile.yaml",
    "workspace/01_case_facts.md",
    "workspace/02_issue_tree.md",
    "workspace/03_research_plan.md",
    "workspace/04_evidence_ledger.csv",
    "workspace/05_assumptions.csv",
    "workspace/06_strategy_options.md",
    "workspace/07_financial_model.md",
    "workspace/gates.yaml",
    "workspace/decision_log.md",
    "deliverables/deck_outline.md",
    "deliverables/qa_bank.md",
    "deliverables/rubric_review.md",
    "prompts/phase_prompts.md",
]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def write(relative: str, content: str) -> None:
    (ROOT / relative).write_text(content, encoding="utf-8")


def data_rows(relative: str) -> list[list[str]]:
    with (ROOT / relative).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    return rows[1:]


def init_case(case_name: str) -> int:
    path = "competition/rules.yaml"
    content = read(path)
    safe_name = case_name.replace('"', "'")
    content, changed = re.subn(
        r'^case_name: ".*"$', f'case_name: "{safe_name}"', content, count=1, flags=re.MULTILINE
    )
    if changed != 1:
        print("ERROR: Could not update case_name in competition/rules.yaml", file=sys.stderr)
        return 1
    write(path, content)
    print(f"Initialized: {safe_name}")
    print("Next: add official materials to inputs/case-brief/ and complete rules.yaml")
    return 0


def parse_gate(number: int) -> bool:
    content = read("workspace/gates.yaml")
    pattern = rf"^  {number}:\n(?:    .*\n)*?    approved: (true|false)$"
    match = re.search(pattern, content, re.MULTILINE)
    return bool(match and match.group(1) == "true")


def set_gate(number: int, approved: bool, approved_by: str) -> int:
    path = "workspace/gates.yaml"
    content = read(path)
    block_pattern = re.compile(
        rf"(^  {number}:\n    name: .*\n)"
        r"    approved: .*\n"
        r"    approved_by: .*\n"
        r"    approved_at: .*\n",
        re.MULTILINE,
    )
    now = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    value = "true" if approved else "false"
    replacement = (
        rf'\1    approved: {value}\n'
        f'    approved_by: "{approved_by.replace(chr(34), chr(39))}"\n'
        f'    approved_at: "{now}"\n'
    )
    updated, changed = block_pattern.subn(replacement, content, count=1)
    if changed != 1:
        print(f"ERROR: Gate {number} was not found", file=sys.stderr)
        return 1
    write(path, updated)
    print(f"Gate {number}: {'APPROVED' if approved else 'REOPENED'} by {approved_by}")
    return 0


def status() -> int:
    print("CaseFlow — Business Case Competition Strategy Agent")
    print("=" * 42)
    for relative in REQUIRED:
        print(f"[{'OK' if (ROOT / relative).exists() else 'MISSING':7}] {relative}")
    brief_dir = ROOT / "inputs/case-brief"
    briefs = [p for p in brief_dir.glob("*") if p.name != ".gitkeep"]
    print(f"\nCase materials: {len(briefs)}")
    print(f"Evidence rows: {len(data_rows('workspace/04_evidence_ledger.csv'))}")
    print(f"Assumption rows: {len(data_rows('workspace/05_assumptions.csv'))}")
    for number in (1, 2, 3):
        print(f"Gate {number}: {'APPROVED' if parse_gate(number) else 'PENDING'}")
    return 0


def check() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for relative in REQUIRED:
        if not (ROOT / relative).exists():
            errors.append(f"Missing required file: {relative}")
    if errors:
        for message in errors:
            print(f"ERROR: {message}")
        return 1

    rules = read("competition/rules.yaml")
    policy = re.search(r'^  status: "(.*?)"', rules, re.MULTILINE)
    policy_value = policy.group(1) if policy else "UNKNOWN"
    if policy_value == "UNKNOWN":
        errors.append("AI policy is UNKNOWN. Confirm the official competition rules.")
    elif policy_value == "PROHIBITED":
        errors.append("AI policy is PROHIBITED. Do not use this workflow on competition content.")
    if "TODO" in rules:
        warnings.append("Competition rules still contain TODO fields.")

    brief_dir = ROOT / "inputs/case-brief"
    briefs = [p for p in brief_dir.glob("*") if p.name != ".gitkeep"]
    if not briefs:
        warnings.append("No case material found in inputs/case-brief/.")

    evidence_rows = data_rows("workspace/04_evidence_ledger.csv")
    if not evidence_rows or all("TODO" in row for row in evidence_rows):
        warnings.append("Evidence ledger contains no completed evidence row.")
    else:
        for index, row in enumerate(evidence_rows, start=2):
            if len(row) < 11:
                errors.append(f"Evidence ledger row {index} has missing columns.")
            elif not row[0].startswith("E-"):
                errors.append(f"Evidence ledger row {index} has invalid ID: {row[0]}")
            elif not row[3].strip():
                warnings.append(f"Evidence {row[0]} has no source URL.")

    assumption_rows = data_rows("workspace/05_assumptions.csv")
    if not assumption_rows or all("TODO" in row for row in assumption_rows):
        warnings.append("Assumption ledger contains no completed assumption row.")
    else:
        for index, row in enumerate(assumption_rows, start=2):
            if len(row) < 10:
                errors.append(f"Assumption ledger row {index} has missing columns.")
            elif not row[0].startswith("A-"):
                errors.append(f"Assumption ledger row {index} has invalid ID: {row[0]}")

    financial = read("workspace/07_financial_model.md")
    if "Source / assumption ID" not in financial:
        errors.append("Financial model lacks source/assumption traceability.")

    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARNING: {message}")
    print(f"\nResult: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CaseFlow workflow helper")
    commands = parser.add_subparsers(dest="command", required=True)

    init_parser = commands.add_parser("init", help="Set the active case name")
    init_parser.add_argument("--case-name", required=True)
    commands.add_parser("status", help="Show files, row counts and gates")
    commands.add_parser("check", help="Validate rules and traceability")

    gate_parser = commands.add_parser("gate", help="Approve or reopen a human gate")
    gate_parser.add_argument("number", type=int, choices=(1, 2, 3))
    action = gate_parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--approve", action="store_true")
    action.add_argument("--reopen", action="store_true")
    gate_parser.add_argument("--by", required=True)

    args = parser.parse_args()
    if args.command == "init":
        return init_case(args.case_name)
    if args.command == "status":
        return status()
    if args.command == "check":
        return check()
    return set_gate(args.number, args.approve, args.by)


if __name__ == "__main__":
    raise SystemExit(main())
