from pathlib import Path

from claude_wrapped.loader import (
    discover_jsonl_files,
    load_project_registry,
    stream_records,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_discover_returns_empty_for_missing_root(tmp_path: Path):
    assert discover_jsonl_files(tmp_path / "does-not-exist") == []


def test_discover_finds_nested_jsonl(tmp_path: Path):
    project = tmp_path / "-home-user-foo"
    project.mkdir()
    f1 = project / "session-a.jsonl"
    f2 = project / "session-b.jsonl"
    f1.write_text("{}\n")
    f2.write_text("{}\n")
    (tmp_path / "not-a-project.txt").write_text("nope")

    found = discover_jsonl_files(tmp_path)
    assert set(found) == {f1, f2}


def test_stream_records_yields_project_id_from_dir(tmp_path: Path):
    project = tmp_path / "-home-user-foo"
    project.mkdir()
    src = FIXTURES / "sample_session.jsonl"
    dest = project / "fixture-session-1.jsonl"
    dest.write_text(src.read_text())

    records = list(stream_records([dest]))
    assert records, "expected at least one record"
    assert all(pid == "-home-user-foo" for pid, _, _ in records)


def test_stream_records_reports_malformed_line(tmp_path: Path):
    path = tmp_path / "bad.jsonl"
    path.write_text('{"good": 1}\n{"broken":\n{"good2": 2}\n')
    records = list(stream_records([path]))
    none_count = sum(1 for _, rec, _ in records if rec is None)
    ok_count = sum(1 for _, rec, _ in records if rec is not None)
    assert none_count == 1
    assert ok_count == 2


def test_stream_records_skips_empty_lines(tmp_path: Path):
    path = tmp_path / "spaced.jsonl"
    path.write_text('\n\n{"type":"user"}\n\n')
    records = list(stream_records([path]))
    assert len(records) == 1


def test_stream_records_handles_zero_byte_file(tmp_path: Path):
    path = tmp_path / "empty.jsonl"
    path.write_text("")
    assert list(stream_records([path])) == []


def test_load_project_registry_missing_returns_empty(tmp_path: Path):
    assert load_project_registry(tmp_path / "missing.json") == {}
