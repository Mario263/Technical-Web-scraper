"""
Ensure duplicate content_hash values do not appear in the final output.
"""
import pytest


def test_no_duplicate_content_hashes(output_json):
    items = output_json.get("items")
    if items is None:
        # fall back to a one-level nested structure (e.g. {"comprehensive_assignment": {"items": [...]}})
        for value in output_json.values():
            if isinstance(value, dict) and "items" in value:
                items = value["items"]
                break
        else:
            pytest.skip("No 'items' list found in output JSON")
    hashes = [it["content_hash"] for it in items]
    dupes = {h for h in hashes if hashes.count(h) > 1}
    assert not dupes, f"Found duplicate content_hash values: {dupes}"