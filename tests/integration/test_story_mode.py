from pathlib import Path

from click.testing import CliRunner

from claude_wrapped.cli import main


def _seed(tmp_path: Path) -> Path:
    root = tmp_path / ".claude" / "projects"
    project = root / "-home-user-project-foo"
    project.mkdir(parents=True)
    fixture = (
        Path(__file__).resolve().parent.parent / "fixtures" / "sample_session.jsonl"
    ).read_text()
    (project / "fixture-session.jsonl").write_text(fixture)
    return tmp_path


def test_story_mode_completes(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_WRAPPED_STORY_DWELL", "0.01")
    home = _seed(tmp_path)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    result = CliRunner().invoke(main, ["--year", "2026", "--story"])
    assert result.exit_code == 0
    # rich.live only flushes the final frame to the captured buffer.
    assert "wrap" in result.output.lower()


def test_story_mode_rejects_json(tmp_path, monkeypatch):
    home = _seed(tmp_path)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    result = CliRunner().invoke(main, ["--story", "--json"])
    assert result.exit_code == 2
