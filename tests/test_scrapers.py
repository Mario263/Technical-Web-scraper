"""
Smoke-test every scraper class independently.

We monkey-patch HTTPClient.get to avoid real network traffic.
"""
import inspect
from pathlib import Path
import types
import pytest
import importlib.util 

# -------- Helpers -------- #

ROOT = Path(__file__).resolve().parents[1]
SCRAPER_DIR = ROOT / "src" / "scrapers"

def _load_scraper(module_path: Path) -> types.ModuleType:
    """Dynamically import a scraper module so the test auto-discovers new scrapers."""
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def _fake_http_get(*_args, **_kwargs):
    """
    A dummy HTTPClient.get returning a hard-coded HTML snippet
    containing a <title> and a <body>.  
    That’s enough for every scraper’s parse() to run.
    """
    return """
        <html>
          <head><title>Dummy Title</title></head>
          <body><p>Dummy content for unit test.</p></body>
        </html>
    """


@pytest.mark.parametrize(
    "scraper_module",
    list(SCRAPER_DIR.glob("*_scraper.py")),
    ids=lambda p: p.stem
)
def test_parse_returns_minimum_fields(monkeypatch, scraper_module):
    """
    For each scraper, ensure .parse() yields a dict with at least
    'title', 'content', and 'content_hash'.
    """
    mod = _load_scraper(scraper_module)
    cls_members = [m for _, m in inspect.getmembers(mod, inspect.isclass) if m.__name__.endswith("Scraper")]
    assert cls_members, f"No scraper class found in {scraper_module.name}"

    ScraperClass = cls_members[0]
    scraper = ScraperClass()

    # Monkey-patch HTTPClient.get so we stay offline
    monkeypatch.setattr(scraper.http_client, "get", _fake_http_get)

    item = scraper.scrape("https://dummy.test/")
    for key in ("title", "content", "content_hash"):
        assert key in item, f"{ScraperClass.__name__} missing '{key}'"