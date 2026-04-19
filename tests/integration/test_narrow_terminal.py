from pathlib import Path

from click.testing import CliRunner

from claude_wrapped.cli import main


def test_narrow_terminal_renders_without_crash(tmp_path, monkeypatch):
    root = tmp_path / ".claude" / "projects" / "-home-user-project-foo"
    root.mkdir(parents=True)
    fixture = (
        Path(__file__).resolve().parent.parent / "fixtures" / "sample_session.jsonl"
    ).read_text()
    (root / "s.jsonl").write_text(fixture)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setenv("COLUMNS", "60")
    result = CliRunner().invoke(main, ["--year", "2026"])
    assert result.exit_code == 0, result.output
    assert "Totals" in result.output
    # No line should be dramatically wider than the budget (rich wraps at
    # COLUMNS, but with borders/padding a couple of chars over is OK).
    for line in result.output.splitlines():
        assert len(line) <= 80, line


def test_dry_run_prints_discovered_files(tmp_path, monkeypatch):
    root = tmp_path / ".claude" / "projects" / "-home-user-project-foo"
    root.mkdir(parents=True)
    (root / "a.jsonl").write_text("")
    (root / "b.jsonl").write_text("")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    result = CliRunner().invoke(main, ["--dry-run"])
    assert result.exit_code == 0
    assert "a.jsonl" in result.output
    assert "b.jsonl" in result.output
