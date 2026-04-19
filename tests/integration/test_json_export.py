import json
from pathlib import Path

from click.testing import CliRunner

from claude_wrapped.cli import main


REQUIRED_TOP_KEYS = {
    "window",
    "totals",
    "top_tools",
    "top_projects",
    "top_subagents",
    "time",
    "models",
    "cost_estimate_usd",
    "skipped_records",
    "warnings",
}


def _seed(tmp_path: Path) -> Path:
    root = tmp_path / ".claude" / "projects"
    project = root / "-home-user-project-foo"
    project.mkdir(parents=True)
    fixture = (
        Path(__file__).resolve().parent.parent / "fixtures" / "sample_session.jsonl"
    ).read_text()
    (project / "fixture-session.jsonl").write_text(fixture)
    return tmp_path


def test_json_mode_emits_valid_json_with_schema_keys(tmp_path, monkeypatch):
    home = _seed(tmp_path)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    result = CliRunner().invoke(main, ["--year", "2026", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output.strip())
    assert REQUIRED_TOP_KEYS.issubset(set(payload.keys()))
    assert set(payload["totals"]["tokens"]) == {
        "input",
        "output",
        "cache_read",
        "cache_create",
    }


def test_json_numbers_match_human_report(tmp_path, monkeypatch):
    home = _seed(tmp_path)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    json_result = CliRunner().invoke(main, ["--year", "2026", "--json"])
    payload = json.loads(json_result.output.strip())
    human_result = CliRunner().invoke(main, ["--year", "2026"])
    # Cross-check: every totals.tokens value from JSON appears verbatim in human output.
    for value in payload["totals"]["tokens"].values():
        assert str(value) in human_result.output


def test_json_empty_dataset_has_stable_shape(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    result = CliRunner().invoke(main, ["--year", "2026", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output.strip())
    assert REQUIRED_TOP_KEYS.issubset(set(payload.keys()))
    assert payload["totals"]["sessions"] == 0
    assert payload["top_tools"] == []


def test_cost_flag_adds_estimate_to_json(tmp_path, monkeypatch):
    home = _seed(tmp_path)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    result = CliRunner().invoke(main, ["--year", "2026", "--json", "--cost"])
    assert result.exit_code == 0
    payload = json.loads(result.output.strip())
    assert payload["cost_estimate_usd"] is not None
    assert isinstance(payload["cost_estimate_usd"], (int, float))
