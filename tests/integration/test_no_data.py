from pathlib import Path

from click.testing import CliRunner

from claude_wrapped.cli import main


def test_empty_home_exits_zero_with_friendly_message(tmp_path: Path, monkeypatch):
    # Empty fake home: no ~/.claude at all.
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    runner = CliRunner()
    result = runner.invoke(main, ["--year", "2026"])

    assert result.exit_code == 0
    assert "No Claude Code history found" in result.output
    assert "Traceback" not in result.output
