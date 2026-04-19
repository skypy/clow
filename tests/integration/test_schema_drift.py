from pathlib import Path

from click.testing import CliRunner

from claude_wrapped.cli import main


def test_completes_with_skip_count_when_records_are_unknown(tmp_path, monkeypatch):
    root = tmp_path / ".claude" / "projects" / "-home-user-project-foo"
    root.mkdir(parents=True)
    # A mix of one recognised message, two unknown-but-valid events, and one
    # malformed line. The report must still render and report skipped=1.
    (root / "drift.jsonl").write_text(
        '{"type":"tomorrows-future-event","sessionId":"s1"}\n'
        '{"type":"user","message":{"role":"user","content":"hi"},"uuid":"u1",'
        '"timestamp":"2026-02-01T10:00:00.000Z","sessionId":"s1"}\n'
        '{"type":"assistant","uuid":"a1","timestamp":"2026-02-01T10:00:01.000Z",'
        '"message":{"model":"claude-opus-4-7","role":"assistant","type":"message",'
        '"usage":{"input_tokens":1,"output_tokens":1,'
        '"cache_creation_input_tokens":0,"cache_read_input_tokens":0},'
        '"content":[{"type":"text","text":"hi"}]},"sessionId":"s1"}\n'
        '{"malformed line that will not parse\n'
    )
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    result = CliRunner().invoke(main, ["--year", "2026"])
    assert result.exit_code == 0, result.output
    assert "skipped 1" in result.output.lower()
