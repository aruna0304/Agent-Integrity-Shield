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
    # bool is a Python int subclass, but it is not a JSON Schema integer.
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
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
    if isinstance(value, int) and not isinstance(value, bool) and value < rule.get("minimum", value):
        errors.append(f"{location}: must be at least {rule['minimum']}")
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
