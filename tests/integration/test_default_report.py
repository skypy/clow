from pathlib import Path

from click.testing import CliRunner

from claude_wrapped.cli import main
from claude_wrapped.loader import default_projects_root  # noqa: F401


def _seed_fixture_tree(tmp_path: Path):
    projects_root = tmp_path / ".claude" / "projects"
    project = projects_root / "-home-user-project-foo"
    project.mkdir(parents=True)
    src = Path(__file__).resolve().parent.parent / "fixtures" / "sample_session.jsonl"
    (project / "fixture-session-1.jsonl").write_text(src.read_text())
    return tmp_path


def test_default_invocation_prints_report(tmp_path: Path, monkeypatch):
    home = _seed_fixture_tree(tmp_path)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))

    runner = CliRunner()
    result = runner.invoke(main, ["--year", "2026"])

    assert result.exit_code == 0, result.output
    assert "Totals" in result.output
    assert "Top 5 tools" in result.output
    assert "Top 5 projects" in result.output
    assert "Time" in result.output
    assert "Models" in result.output


def test_report_shows_skipped_record_count(tmp_path: Path, monkeypatch):
    home = _seed_fixture_tree(tmp_path)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))

    runner = CliRunner()
    result = runner.invoke(main, ["--year", "2026"])
    assert "skipped" in result.output.lower()
