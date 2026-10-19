"""Small, dependency-free validator for the AIS trajectory schema.

It implements the Draft-07 keywords used by trajectory_schema.json. Keeping this
local means the first pipeline step can run without installing packages.
"""

import json
from pathlib import Path


def load_schema(schema_path: Path | str) -> dict:
    """Load the versioned JSON Schema definition used by the pipeline."""
    with open(schema_path, encoding="utf-8") as handle:
        return json.load(handle)


def _matches_type(value, expected: str) -> bool:
    # bool is a Python int subclass, but it is not a JSON Schema integer or number.
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": (isinstance(value, (int, float)) and not isinstance(value, bool)),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, False)


def _validate(value, rule: dict, location: str, errors: list[str]) -> None:
    expected = rule.get("type")
    if expected:
        choices = expected if isinstance(expected, list) else [expected]
        if not any(_matches_type(value, choice) for choice in choices):
            errors.append(f"{location}: expected {choices}, got {type(value).__name__}")
            return
    if "enum" in rule and value not in rule["enum"]:
        errors.append(f"{location}: value {value!r} is not an allowed enum value")
    if isinstance(value, str) and len(value) < rule.get("minLength", 0):
        errors.append(f"{location}: must not be empty")
    if (isinstance(value, (int, float)) and not isinstance(value, bool)):
        if "minimum" in rule and value < rule["minimum"]:
            errors.append(f"{location}: must be at least {rule['minimum']}")
        if "maximum" in rule and value > rule["maximum"]:
            errors.append(f"{location}: must be at most {rule['maximum']}")
    if isinstance(value, dict):
        for field in rule.get("required", []):
            if field not in value:
                errors.append(f"{location}: missing required field {field!r}")
        properties = rule.get("properties", {})
        if rule.get("additionalProperties") is False:
            for field in value:
                if field not in properties:
                    errors.append(f"{location}: unexpected field {field!r}")
        for field, nested_rule in properties.items():
            if field in value:
                _validate(value[field], nested_rule, f"{location}.{field}", errors)
    if isinstance(value, list) and "items" in rule:
        for index, item in enumerate(value):
            _validate(item, rule["items"], f"{location}[{index}]", errors)


def validate_record(record: dict, schema: dict) -> list[str]:
    """Return validation messages; an empty list means the record is valid."""
    errors: list[str] = []
    _validate(record, schema, "$", errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    import sys
    args = argv if argv is not None else sys.argv[1:]
    if not args or "-h" in args or "--help" in args:
        print("Usage: python validate_trajectory.py <file1.jsonl> [file2.jsonl ...]")
        return 0 if ("-h" in args or "--help" in args) else 1

    schema_path = Path(__file__).resolve().parent / "trajectory_schema.json"
    if not schema_path.exists():
        print(f"Error: Schema file not found at {schema_path}", file=sys.stderr)
        return 1

    schema = load_schema(schema_path)
    total_error_count = 0

    for arg in args:
        filepath = Path(arg)
        if not filepath.exists():
            print(f"{filepath.name}: File not found", file=sys.stderr)
            total_error_count += 1
            continue

        errors: list[str] = []
        with filepath.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except Exception as e:
                    errors.append(f"Line {line_no}: JSON parse error: {e}")
                    continue

                rec_errors = validate_record(record, schema)
                for err in rec_errors:
                    rec_id = record.get("trajectory_id", f"line_{line_no}")
                    errors.append(f"[{rec_id}] {err}")

        print(f"{filepath.name}: {len(errors)} error(s)")
        if errors:
            total_error_count += len(errors)
            for err in errors[:3]:
                print(f"   - {err}")

    return 1 if total_error_count > 0 else 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
