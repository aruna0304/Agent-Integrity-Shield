"""Normalize the official ToolEmu test-case benchmark into AIS JSONL.

ToolEmu publishes risk scenarios, not recorded tool-execution trajectories. This
adapter preserves that distinction: it emits an empty actions list instead of
fabricating calls, inputs, outputs, or observed failures.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_CASES = PROJECT_ROOT / "data" / "raw" / "toolemu" / "all_cases.json"
SCHEMA_FILE = PROJECT_ROOT / "schema" / "trajectory_schema.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "toolemu_normalized.jsonl"
sys.path.insert(0, str(PROJECT_ROOT / "schema"))
from validate_trajectory import load_schema, validate_record  # noqa: E402

# This first AIS slice intentionally includes only the three requested domains.
# Toolkits not listed here are reported as skipped rather than guessed.
TOOLKIT_DOMAINS = {
    "Terminal": "file_operations",
    "Dropbox": "file_operations",
    "EvernoteManager": "file_operations",
    "BankManager": "financial_transactions",
    "Venmo": "financial_transactions",
    "EthereumManager": "financial_transactions",
    "Binance": "financial_transactions",
    "TDAmeritrade": "financial_transactions",
    "InvestmentManager": "financial_transactions",
    "Gmail": "communication",
    "TwitterManager": "communication",
    "FacebookManager": "communication",
    "Slack": "communication",
    "Twilio": "communication",
}


def print_raw_structure_evidence(cases: list[dict]) -> None:
    """Show why this source cannot populate observed calls or verdict fields.

    ToolEmu's released benchmark is made of pre-execution risk scenarios. This
    explicit preflight output prevents a future reader from mistaking absent
    trace/label data for a mapping defect in this adapter.
    """
    example = next((case for case in cases if case.get("name") == "official_1"), cases[0])
    keys = sorted(example.keys())
    expected_trace_fields = {"trajectory", "actions", "tool_calls", "tool_use_trace"}
    expected_label_fields = {
        "label", "verdict", "safety_label", "evaluator_output", "severity", "risk_level"
    }
    present_trace_fields = sorted(expected_trace_fields.intersection(example))
    present_label_fields = sorted(expected_label_fields.intersection(example))
    print(f"Raw structure check ({example.get('name', 'first case')}): keys only = {keys}")
    print("  Trace fields present: " + (", ".join(present_trace_fields) if present_trace_fields else "none"))
    print("  Verdict/label fields present: " + (", ".join(present_label_fields) if present_label_fields else "none"))


def choose_domain(toolkits: list[str]) -> tuple[str | None, str | None]:
    """Return a domain or a clear skip reason for unsupported/ambiguous cases."""
    mapped = {TOOLKIT_DOMAINS[name] for name in toolkits if name in TOOLKIT_DOMAINS}
    unknown = [name for name in toolkits if name not in TOOLKIT_DOMAINS]
    if unknown:
        return None, f"toolkit(s) outside today's three-domain mapping: {', '.join(unknown)}"
    if len(mapped) != 1:
        return None, f"toolkits map to multiple domains: {', '.join(toolkits)}"
    return mapped.pop(), None


def convert_case(case: dict, sequence_number: int) -> tuple[dict | None, str | None]:
    toolkits = case.get("Toolkits", [])
    if not isinstance(toolkits, list) or not toolkits:
        return None, "missing or empty Toolkits"
    task = case.get("User Instruction")
    if not isinstance(task, str):
        return None, "missing User Instruction"
    domain, reason = choose_domain(toolkits)
    if reason:
        return None, reason

    record = {
        "trajectory_id": f"toolemu_{sequence_number:04d}",
        "source_dataset": "ToolEmu",
        "status": "scenario_only",
        "task_context": task,
        "domain": domain,
        # TODO: When ToolEmu emulator trace exports are added, map each observed
        # call here and default lifecycle_stage to "execution" if unspecified.
        "actions": [],
        "risk_taxonomy": {
            "potential_risky_actions": case.get("Potential Risky Actions", []),
            "potential_risky_outcomes": case.get("Potential Risky Outcomes", []),
        },
        "expected_achievements": case.get("Expected Achievements", []),
        "underspecifications": case.get("Underspecifications", {}),
        "ground_truth_label": {
            "is_failure": None,
            "failure_category": None,
            "severity": None,
            "source_annotation": "ToolEmu case-bank risk scenario; no observed evaluator verdict in all_cases.json.",
            "note": "ToolEmu case files do not contain a pre-computed verdict. Run the LM-emulated sandbox and its evaluator to obtain an observed failure label.",
        },
        "raw_source_ref": f"all_cases.json#{case.get('name', f'array_index_{sequence_number - 1}')}",
    }
    return record, None


def main() -> int:
    cases = json.loads(RAW_CASES.read_text(encoding="utf-8"))
    schema = load_schema(SCHEMA_FILE)
    converted, skipped, domain_counts, outcome_counts = [], [], Counter(), Counter()

    # Print this before conversion so the source interpretation is inspectable.
    print_raw_structure_evidence(cases)

    for raw_index, case in enumerate(cases):
        record, reason = convert_case(case, raw_index + 1)
        case_ref = case.get("name", f"array_index_{raw_index}") if isinstance(case, dict) else f"array_index_{raw_index}"
        if reason:
            skipped.append((case_ref, reason))
            continue
        errors = validate_record(record, schema)
        if errors:
            skipped.append((case_ref, "schema validation failed: " + "; ".join(errors)))
            continue
        converted.append(record)
        domain_counts[record["domain"]] += 1
        label = record["ground_truth_label"]["is_failure"]
        outcome_counts["failures" if label is True else "non_failures" if label is False else "unknown"] += 1

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as handle:
        for record in converted:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("ToolEmu normalization summary")
    print(f"  Total raw cases found: {len(cases)}")
    print(f"  Successfully converted: {len(converted)}")
    print(f"  Skipped/failed: {len(skipped)}")
    print("  Per domain: " + ", ".join(f"{name}={domain_counts[name]}" for name in sorted(domain_counts)))
    print(
        "  Failures vs non-failures: "
        f"failures={outcome_counts['failures']}, non_failures={outcome_counts['non_failures']}, "
        f"unknown={outcome_counts['unknown']}"
    )
    if skipped:
        print("  Skipped records:")
        for case_ref, reason in skipped:
            print(f"    - {case_ref}: {reason}")
    print("\nFirst 3 converted records:")
    for record in converted[:3]:
        print(json.dumps(record, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
