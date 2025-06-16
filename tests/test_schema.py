"""
Validate the generated JSON against schema.json
"""
from jsonschema import validate, ValidationError


def test_output_matches_schema(output_json, schema):
    try:
        validate(instance=output_json, schema=schema)
    except ValidationError as e:  # pragma: no cover
        # Re-raise with a shorter message so pytest output is readable
        raise AssertionError(f"Schema validation failed → {e.message}") from None