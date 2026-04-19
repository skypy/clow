from pathlib import Path

from claude_wrapped.loader import stream_records
from claude_wrapped.parser import parse_records

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def _records_from_fixture(tmp_path: Path, project_dir: str = "-home-user-project-foo"):
    project = tmp_path / project_dir
    project.mkdir()
    src = FIXTURES / "sample_session.jsonl"
    dest = project / "fixture-session-1.jsonl"
    dest.write_text(src.read_text())
    return list(stream_records([dest]))


def test_parser_builds_one_session(tmp_path: Path):
    result = parse_records(_records_from_fixture(tmp_path))
    assert len(result.sessions) == 1
    s = result.sessions[0]
    assert s.id == "fixture-session-1"
    assert s.message_count == 5  # 2 user + 3 assistant messages in fixture
    assert s.tool_call_count == 3  # Read + Bash + Task


def test_parser_counts_malformed_lines_as_skipped(tmp_path: Path):
    result = parse_records(_records_from_fixture(tmp_path))
    # Fixture includes one deliberately broken JSON line.
    assert result.skipped_records >= 1


def test_parser_ignores_unknown_type_without_counting_it(tmp_path: Path):
    # The fixture includes a 'future-event-we-dont-know' record and a
    # 'permission-mode' record; neither is malformed so neither should
    # inflate skipped_records beyond the broken line above.
    result = parse_records(_records_from_fixture(tmp_path))
    assert result.skipped_records == 1


def test_parser_captures_tokens(tmp_path: Path):
    result = parse_records(_records_from_fixture(tmp_path))
    s = result.sessions[0]
    assert s.tokens_input == 10 + 5 + 3
    assert s.tokens_output == 20 + 15 + 7
    assert s.tokens_cache_read == 5 + 0 + 1
    assert s.tokens_cache_create == 0 + 0 + 2


def test_parser_detects_subagent(tmp_path: Path):
    result = parse_records(_records_from_fixture(tmp_path))
    subagents = [tc.subagent for tc in result.sessions[0].tool_calls if tc.subagent]
    assert subagents == ["Explore"]


def test_parser_uses_last_real_model(tmp_path: Path):
    result = parse_records(_records_from_fixture(tmp_path))
    # Last assistant message in fixture uses claude-sonnet-4-6.
    assert result.sessions[0].model == "claude-sonnet-4-6"


def test_parser_populates_project(tmp_path: Path):
    result = parse_records(_records_from_fixture(tmp_path))
    assert "-home-user-project-foo" in result.projects
    p = result.projects["-home-user-project-foo"]
    assert p.session_count == 1
    assert p.display_name == "foo"
