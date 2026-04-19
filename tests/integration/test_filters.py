from pathlib import Path

from click.testing import CliRunner

from claude_wrapped.cli import main


def _seed(tmp_path: Path) -> Path:
    root = tmp_path / ".claude" / "projects"
    a = root / "-home-user-project-alpha"
    b = root / "-home-user-project-beta"
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    fixture = (
        Path(__file__).resolve().parent.parent / "fixtures" / "sample_session.jsonl"
    ).read_text()
    # Two projects, distinct sessionId values so they do not merge.
    (a / "fixture-a.jsonl").write_text(fixture.replace("fixture-session-1", "sess-a"))
    (b / "fixture-b.jsonl").write_text(fixture.replace("fixture-session-1", "sess-b"))
    return tmp_path


def _run(home: Path, monkeypatch, *args):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    return CliRunner().invoke(main, list(args))


def test_year_filter_includes_only_target_year(tmp_path, monkeypatch):
    home = _seed(tmp_path)
    result = _run(home, monkeypatch, "--year", "2020")
    assert result.exit_code == 0
    assert "No Claude Code history found" in result.output


def test_since_until_narrows_window(tmp_path, monkeypatch):
    home = _seed(tmp_path)
    result = _run(
        home,
        monkeypatch,
        "--since",
        "2026-03-15",
        "--until",
        "2026-03-15",
    )
    assert result.exit_code == 0
    assert "Sessions" in result.output


def test_year_and_since_are_mutually_exclusive(tmp_path, monkeypatch):
    home = _seed(tmp_path)
    result = _run(
        home,
        monkeypatch,
        "--year",
        "2026",
        "--since",
        "2026-01-01",
    )
    assert result.exit_code == 2
    assert "mutually exclusive" in (result.output + (result.stderr_bytes or b"").decode())


def test_project_filter_limits_to_one(tmp_path, monkeypatch):
    home = _seed(tmp_path)
    result = _run(home, monkeypatch, "--year", "2026", "--project", "alpha")
    assert result.exit_code == 0
    assert "project=alpha" in result.output


def test_unknown_project_returns_empty(tmp_path, monkeypatch):
    home = _seed(tmp_path)
    result = _run(home, monkeypatch, "--year", "2026", "--project", "nonexistent")
    assert result.exit_code == 0
    assert "No Claude Code history found" in result.output
