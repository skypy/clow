from datetime import datetime, timezone
from pathlib import Path

from claude_wrapped.aggregator import aggregate
from claude_wrapped.loader import stream_records
from claude_wrapped.parser import parse_records

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def _parsed(tmp_path: Path):
    project = tmp_path / "-home-user-project-foo"
    project.mkdir()
    src = FIXTURES / "sample_session.jsonl"
    dest = project / "fixture-session-1.jsonl"
    dest.write_text(src.read_text())
    return parse_records(stream_records([dest]))


def _report_for_window(tmp_path: Path):
    parsed = _parsed(tmp_path)
    return aggregate(
        sessions=parsed.sessions,
        projects=parsed.projects,
        since=datetime(2026, 1, 1, tzinfo=timezone.utc),
        until=datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        project_filter=None,
        skipped_records=parsed.skipped_records,
    )


def test_totals_sum_matches_per_session(tmp_path: Path):
    parsed = _parsed(tmp_path)
    report = aggregate(
        sessions=parsed.sessions,
        projects=parsed.projects,
        since=datetime(2026, 1, 1, tzinfo=timezone.utc),
        until=datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        project_filter=None,
        skipped_records=0,
    )
    assert report.totals.messages == sum(s.message_count for s in parsed.sessions)
    assert report.totals.tool_calls == sum(s.tool_call_count for s in parsed.sessions)


def test_top_tools_ordering(tmp_path: Path):
    report = _report_for_window(tmp_path)
    names = [t.name for t in report.top_tools]
    # All three tools appear exactly once in the fixture; ordering should be
    # stable by insertion (Counter.most_common breaks ties by insertion order).
    assert set(names) == {"Read", "Bash", "Task"}
    for idx, item in enumerate(report.top_tools):
        assert item.rank == idx + 1


def test_window_excludes_out_of_range_sessions(tmp_path: Path):
    parsed = _parsed(tmp_path)
    report = aggregate(
        sessions=parsed.sessions,
        projects=parsed.projects,
        since=datetime(2020, 1, 1, tzinfo=timezone.utc),
        until=datetime(2020, 12, 31, tzinfo=timezone.utc),
        project_filter=None,
        skipped_records=0,
    )
    assert report.totals.sessions == 0
    assert report.totals.messages == 0


def test_model_mix_reflects_family_prefix(tmp_path: Path):
    report = _report_for_window(tmp_path)
    # Fixture's last assistant model is sonnet → session.model == sonnet.
    assert report.models.sonnet_pct == 100.0
    assert report.models.opus_pct == 0.0


def test_top_subagents_captures_task_invocations(tmp_path: Path):
    report = _report_for_window(tmp_path)
    assert report.top_subagents
    assert report.top_subagents[0].name == "Explore"


def test_longest_session_duration_is_nonnegative(tmp_path: Path):
    report = _report_for_window(tmp_path)
    assert report.time.longest_session_seconds >= 0
