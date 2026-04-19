from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator


def default_projects_root() -> Path:
    return Path.home() / ".claude" / "projects"


def default_registry_path() -> Path:
    return Path.home() / ".claude.json"


def discover_jsonl_files(root: Path | None = None) -> list[Path]:
    root = root or default_projects_root()
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*.jsonl") if p.is_file())


def load_project_registry(path: Path | None = None) -> dict[str, dict]:
    path = path or default_registry_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    projects = data.get("projects")
    return projects if isinstance(projects, dict) else {}


def stream_records(
    files: list[Path],
) -> Iterator[tuple[str, dict | None, Path]]:
    """Yield (project_id, record_dict_or_None, file_path) for every line.

    A None record signals a malformed JSON line so the parser can count it.
    The project_id is derived from the parent directory name under the
    projects root, which is the canonical encoded-path identifier Claude
    Code uses (e.g. ``-home-user-project-foo``).
    """
    import orjson  # imported here so tests without orjson can import module

    for path in files:
        project_id = path.parent.name
        try:
            with path.open("rb") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = orjson.loads(line)
                    except orjson.JSONDecodeError:
                        yield project_id, None, path
                        continue
                    if isinstance(record, dict):
                        yield project_id, record, path
                    else:
                        yield project_id, None, path
        except OSError:
            continue
