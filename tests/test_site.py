import json
from pathlib import Path

from agent_gate.record import build_bundle

ROOT = Path(__file__).resolve().parents[1]


def _js_payload(text: str) -> dict:
    prefix = "window.HL_RUNS = "
    assert text.startswith(prefix)
    body = text[len(prefix) :].strip()
    if body.endswith(";"):
        body = body[:-1]
    return json.loads(body)


def test_committed_recording_matches_a_fresh_run():
    fresh = build_bundle(str(ROOT / "demo" / "data"))
    committed = json.loads((ROOT / "site" / "data" / "runs.json").read_text(encoding="utf-8"))
    script = _js_payload((ROOT / "site" / "data" / "runs.js").read_text(encoding="utf-8"))
    assert committed == fresh
    assert script == fresh
    assert {run["id"] for run in fresh["runs"]} == {
        "refund-stalled",
        "refund-goodwill",
        "email-vendor",
        "dns-cutover",
        "refund-expired",
    }
    stalled = next(run for run in fresh["runs"] if run["id"] == "refund-stalled")
    assert stalled["continuations"]["approve"]["execution_count"] == 1
    assert stalled["continuations"]["approve"]["idempotent_replays"] == 1
    assert stalled["continuations"]["deny"]["execution_count"] == 0
    goodwill = next(run for run in fresh["runs"] if run["id"] == "refund-goodwill")
    assert goodwill["continuations"]["edit"]["result"]["amount_usd"] == "43.20"
    expired = next(run for run in fresh["runs"] if run["id"] == "refund-expired")
    assert expired["continuations"]["late"]["status"] == "expired"
    assert expired["continuations"]["late"]["execution_count"] == 0


def test_static_site_has_no_remote_dependencies():
    html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "site" / "assets" / "site.css").read_text(encoding="utf-8")
    script = (ROOT / "site" / "assets" / "site.js").read_text(encoding="utf-8")
    assert 'src="data/runs.js"' in html
    assert 'src="assets/site.js"' in html
    blob = html + css + script
    assert "fonts.googleapis.com" not in blob
    assert "cdn." not in blob
    assert "btn-approve" in script
    assert "btn-deny" in script


def test_readme_has_diagram_and_screenshots():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "```mermaid" in text
    for name in ("pending-approval.png", "approved-resume.png", "denied-dark.png"):
        path = ROOT / "docs" / "images" / name
        assert f"docs/images/{name}" in text
        assert path.is_file()
        assert path.stat().st_size > 10_000
