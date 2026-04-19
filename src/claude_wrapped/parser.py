from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .models import Project, Session, ToolCall


@dataclass(slots=True)
class ParseResult:
    sessions: list[Session]
    projects: dict[str, Project]
    skipped_records: int
    warnings: list[str]


def _parse_ts(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        return datetime.fromisoformat(raw).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _display_name(project_id: str, registry: dict[str, dict]) -> str:
    for path in registry:
        if _encode_path(path) == project_id:
            return Path(path).name or project_id
    # Fallback: treat the encoding as path-like and take the last segment.
    last = project_id.rsplit("-", 1)[-1]
    return last or project_id


def _encode_path(path: str) -> str:
    # Claude Code encodes project paths as '-'.join(path.split('/')).
    return path.replace("/", "-")


def parse_records(
    records: Iterable[tuple[str, dict | None, Path]],
    registry: dict[str, dict] | None = None,
) -> ParseResult:
    registry = registry or {}
    sessions: dict[str, Session] = {}
    skipped = 0
    warnings: list[str] = []
    project_firstseen: dict[str, datetime] = {}
    project_lastseen: dict[str, datetime] = {}

    for project_id, record, _path in records:
        if record is None:
            skipped += 1
            continue

        rtype = record.get("type")
        session_id = record.get("sessionId")
        ts = _parse_ts(record.get("timestamp"))

        if rtype not in ("user", "assistant"):
            # Known system events (permission-mode, file-history-snapshot, etc.)
            # and future unknown types: both ignored for metrics. We don't
            # count system events as "skipped" — only malformed or
            # shape-broken records count.
            continue

        if not session_id or ts is None:
            skipped += 1
            continue

        message = record.get("message")
        if not isinstance(message, dict):
            skipped += 1
            continue

        session = sessions.get(session_id)
        if session is None:
            session = Session(
                id=session_id,
                project_id=project_id,
                started_at=ts,
                ended_at=ts,
            )
            sessions[session_id] = session
        else:
            if ts < session.started_at:
                session.started_at = ts
            if ts > session.ended_at:
                session.ended_at = ts

        session.message_count += 1

        # Per-project window tracking.
        if project_id not in project_firstseen or ts < project_firstseen[project_id]:
            project_firstseen[project_id] = ts
        if project_id not in project_lastseen or ts > project_lastseen[project_id]:
            project_lastseen[project_id] = ts

        if rtype == "assistant":
            model = message.get("model")
            if isinstance(model, str) and model and model != "<synthetic>":
                session.model = model
            usage = message.get("usage") or {}
            if isinstance(usage, dict):
                session.tokens_input += int(usage.get("input_tokens") or 0)
                session.tokens_output += int(usage.get("output_tokens") or 0)
                session.tokens_cache_read += int(
                    usage.get("cache_read_input_tokens") or 0
                )
                session.tokens_cache_create += int(
                    usage.get("cache_creation_input_tokens") or 0
                )
            content = message.get("content")
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "tool_use":
                        continue
                    name = block.get("name")
                    if not isinstance(name, str) or not name:
                        continue
                    subagent = None
                    if name == "Task":
                        inp = block.get("input") or {}
                        if isinstance(inp, dict):
                            st = inp.get("subagent_type")
                            if isinstance(st, str) and st:
                                subagent = st
                    session.tool_calls.append(
                        ToolCall(
                            session_id=session_id,
                            tool_name=name,
                            timestamp=ts,
                            subagent=subagent,
                        )
                    )
                    session.tool_call_count += 1

    # Clamp any tool-call timestamps that fall outside the session window —
    # in practice they share the parent message timestamp, so this is a
    # belt-and-braces guard against records with a divergent ``timestamp``
    # added in future versions of the JSONL format.
    for s in sessions.values():
        for tc in s.tool_calls:
            if tc.timestamp < s.started_at:
                tc.timestamp = s.started_at
                warnings.append(
                    f"tool-call in session {s.id} clamped to session start"
                )
            elif tc.timestamp > s.ended_at:
                tc.timestamp = s.ended_at
                warnings.append(
                    f"tool-call in session {s.id} clamped to session end"
                )

    project_session_counts: dict[str, int] = {}
    for s in sessions.values():
        project_session_counts[s.project_id] = (
            project_session_counts.get(s.project_id, 0) + 1
        )

    projects: dict[str, Project] = {}
    for pid in project_session_counts:
        projects[pid] = Project(
            id=pid,
            display_name=_display_name(pid, registry),
            first_seen=project_firstseen.get(pid),
            last_seen=project_lastseen.get(pid),
            session_count=project_session_counts[pid],
        )

    return ParseResult(
        sessions=list(sessions.values()),
        projects=projects,
        skipped_records=skipped,
        warnings=warnings,
    )
