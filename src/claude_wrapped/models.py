from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class ToolCall:
    session_id: str
    tool_name: str
    timestamp: datetime
    subagent: str | None = None


@dataclass(slots=True)
class Session:
    id: str
    project_id: str
    started_at: datetime
    ended_at: datetime
    message_count: int = 0
    tool_call_count: int = 0
    tool_calls: list[ToolCall] = field(default_factory=list)
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_cache_read: int = 0
    tokens_cache_create: int = 0
    model: str | None = None


@dataclass(slots=True)
class Project:
    id: str
    display_name: str
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    session_count: int = 0


@dataclass(slots=True)
class Metric:
    label: str
    value: int | float | str
    unit: str | None = None
    rank: int | None = None
    group: str | None = None
