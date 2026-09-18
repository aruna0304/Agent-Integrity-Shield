"""Normalize the official Agent-SafetyBench benchmark into AIS JSONL.

Agent-SafetyBench (Zhang et al., 2024) publishes scenario specifications across
349 environments and 8 risk categories, not pre-computed execution trajectories
or agent run safety verdicts. This adapter adheres strictly to that distinction:
it emits an empty actions list and explicit 'unknown' failure judgment rather
than fabricating observed traces or labels.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_CASES = PROJECT_ROOT / "data" / "raw" / "agentsafetybench" / "released_data.json"
SCHEMA_FILE = PROJECT_ROOT / "schema" / "trajectory_schema.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "agentsafetybench_normalized.jsonl"
sys.path.insert(0, str(PROJECT_ROOT / "schema"))
from validate_trajectory import load_schema, validate_record  # noqa: E402

# Environment mappings strictly locked to the 3 agreed project domains:
# file_operations, financial_transactions, communication.
# Any environment outside this dictionary is logged as skipped rather than guessed.
ENVIRONMENT_DOMAINS = {
    # File Operations
    "FileManager": "file_operations",
    "OS": "file_operations",
    "FileProcessor": "file_operations",
    "BackupSystem": "file_operations",
    # Financial Transactions
    "Bank": "financial_transactions",
    "InvestmentManager": "financial_transactions",
    "StockManager": "financial_transactions",
    "MobilePayment": "financial_transactions",
    "AntiMoneyLaundering": "financial_transactions",
    "LoanApprovalSystem": "financial_transactions",
    "SecureDigitalWallet": "financial_transactions",
    "PersonalizedBiometricAuthenticationForFinancialTransactions": "financial_transactions",
    # Communication
    "Email": "communication",
    "SocialMedia": "communication",
    "Slack": "communication",
    "Phone": "communication",
    "SMS": "communication",
    "ChatApp": "communication",
}


def print_raw_structure_evidence(cases: list[dict]) -> None:
    """Show why this source cannot populate observed calls or verdict fields.

    Agent-SafetyBench's released benchmark contains task instructions, environment
    toolkits, and risk categories. This explicit preflight check verifies that
    it does not contain recorded execution trajectories or evaluator verdicts.
    """
    example = cases[0]
    keys = sorted(example.keys())
    expected_trace_fields = {"trajectory", "actions", "tool_calls", "tool_use_trace"}
    expected_label_fields = {
        "label",
        "verdict",
        "safety_label",
        "evaluator_output",
        "severity",
        "risk_level",
    }
    present_trace_fields = sorted(expected_trace_fields.intersection(example))
    present_label_fields = sorted(expected_label_fields.intersection(example))
    print(f"Raw structure check (Case id {example.get('id', 0)}): keys = {keys}")
    print(
        "  Trace fields present: "
        + (", ".join(present_trace_fields) if present_trace_fields else "none")
    )
    print(
        "  Verdict/label fields present: "
        + (", ".join(present_label_fields) if present_label_fields else "none")
    )


def choose_domain(environments: list[dict]) -> tuple[str | None, str | None]:
    """Return a locked domain or a clear skip reason for unsupported/ambiguous cases."""
    if not environments:
        return None, "no environments specified in case"

    env_names = [e.get("name") for e in environments if isinstance(e, dict)]
    mapped = {
        ENVIRONMENT_DOMAINS[name]
        for name in env_names
        if name in ENVIRONMENT_DOMAINS
    }
    unknown = [name for name in env_names if name not in ENVIRONMENT_DOMAINS]

    if unknown:
        return (
            None,
            f"environment(s) outside locked three-domain mapping: {', '.join(str(u) for u in unknown)}",
        )
    if len(mapped) > 1:
        return None, f"environments map to multiple domains: {', '.join(str(e) for e in env_names)}"
    if not mapped:
        return None, "no matching domain found"
    return mapped.pop(), None


def convert_case(case: dict) -> tuple[dict | None, str | None]:
    """Convert an Agent-SafetyBench case into the unified AIS trajectory format."""
    case_id = case.get("id")
    if case_id is None:
        return None, "missing case id"

    task = case.get("instruction")
    if not isinstance(task, str) or not task.strip():
        return None, "missing or empty instruction"

    environments = case.get("environments", [])
    if not isinstance(environments, list):
        return None, "environments is not a list"

    domain, reason = choose_domain(environments)
    if reason:
        return None, reason

    # Extract risk information
    risks = case.get("risks", [])
    if not isinstance(risks, list):
        risks = [str(risks)] if risks else []

    tools_available = []
    for env in environments:
        env_name = env.get("name", "Unknown")
        for tool in env.get("tools", []):
            tools_available.append(f"{env_name}.{tool}")

    risky_actions = [
        f"Unsafe invocation of tool '{tool}' with malicious or non-verified arguments"
        for tool in tools_available
    ] if tools_available else ["Unsafe execution of unverified agent actions"]

    fulfillable = case.get("fulfillable")
    failure_modes = case.get("failure_modes")

    record = {
        "trajectory_id": f"agentsafetybench_{case_id:04d}",
        "source_dataset": "Agent-SafetyBench",
        "status": "scenario_only",
        "task_context": task,
        "domain": domain,
        "actions": [],
        "risk_taxonomy": {
            "potential_risky_actions": risky_actions,
            "potential_risky_outcomes": [str(r) for r in risks] if risks else ["Safety boundary violation"],
        },
        "expected_achievements": [
            f"Safely fulfill instruction if benign; refuse or request user confirmation if unsafe (fulfillable={fulfillable})"
        ],
        "underspecifications": {
            "fulfillable": fulfillable,
            "failure_modes": str(failure_modes) if failure_modes is not None else None,
            "tools_available": tools_available,
        },
        "ground_truth_label": {
            "is_failure": None,
            "failure_category": None,
            "severity": None,
            "source_annotation": (
                f"Agent-SafetyBench scenario (risks: {', '.join(risks)}; "
                f"failure_modes: {failure_modes}; fulfillable: {fulfillable})"
            ),
            "note": (
                "Agent-SafetyBench released_data.json specifies risk scenarios without "
                "pre-computed execution traces or observed verdicts. Run the simulation "
                "harness and safety judge to obtain an observed failure label."
            ),
        },
        "raw_source_ref": f"released_data.json#id_{case_id}",
    }
    return record, None


def main() -> int:
    cases = json.loads(RAW_CASES.read_text(encoding="utf-8"))
    schema = load_schema(SCHEMA_FILE)
    converted, skipped, domain_counts, outcome_counts = [], [], Counter(), Counter()

    print("\n--- Agent-SafetyBench Preprocessing & Normalization ---")
    print_raw_structure_evidence(cases)

    for case in cases:
        case_ref = f"id_{case.get('id', 'unknown')}"
        record, reason = convert_case(case)
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

    print("\nAgent-SafetyBench Normalization Summary")
    print(f"  Total raw cases found: {len(cases)}")
    print(f"  Successfully converted: {len(converted)}")
    print(f"  Skipped/failed: {len(skipped)}")
    print("  Per domain: " + ", ".join(f"{name}={domain_counts[name]}" for name in sorted(domain_counts)))
    print(
        "  Failures vs non-failures: "
        f"failures={outcome_counts['failures']}, non_failures={outcome_counts['non_failures']}, "
        f"unknown={outcome_counts['unknown']}"
    )

    # Summarize skip reasons
    skip_reason_counts = Counter(reason.split(":")[0] for _, reason in skipped)
    print("  Skipped categories breakdown:")
    for category, count in skip_reason_counts.most_common():
        print(f"    - {category}: {count}")

    print("\nFirst 2 converted records:")
    for record in converted[:2]:
        print(json.dumps(record, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
