"""
Project-wide pytest fixtures
"""
from pathlib import Path
import json
import importlib.util
import pytest
import jsonschema

# ---------- Paths ---------- #

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
SCHEMA_PATH = ROOT / "config" / "schema.json"

@pytest.fixture(scope="session")
def schema():
    """Load the project JSON schema once per test session."""
    with SCHEMA_PATH.open() as f:
        return json.load(f)


@pytest.fixture(scope="session")
def latest_output_file():
    """
    Return the newest *.json file in the output directory
    (e.g. complete_pipeline_output.json, aline_comprehensive_assignment.json …).
    """
    candidates = sorted(OUTPUT_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    assert candidates, "No output JSON files found; run the pipeline first."
    return candidates[0]


@pytest.fixture(scope="session")
def output_json(latest_output_file):
    """Load the newest pipeline output as Python dict."""
    with latest_output_file.open() as f:
        return json.load(f)