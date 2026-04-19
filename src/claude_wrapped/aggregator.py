from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

from .models import Project, Session


@dataclass(slots=True)
class Totals:
    sessions: int = 0
    messages: int = 0
    tool_calls: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_cache_read: int = 0
    tokens_cache_create: int = 0
    active_days: int = 0


@dataclass(slots=True)
class RankedItem:
    rank: int
    name: str
    count: int


@dataclass(slots=True)
class RankedProject:
    rank: int
    id: str
    name: str
    sessions: int


@dataclass(slots=True)
class TimeMetrics:
    busiest_hour_local: int | None = None
    busiest_weekday_local: str | None = None
    longest_session_seconds: int = 0


@dataclass(slots=True)
class ModelMix:
    opus_pct: float = 0.0
    sonnet_pct: float = 0.0
    haiku_pct: float = 0.0
    other_pct: float = 0.0


@dataclass(slots=True)
class Window:
    since: datetime
    until: datetime
    project: str | None = None


@dataclass(slots=True)
class Report:
    window: Window
    totals: Totals
    top_tools: list[RankedItem]
    top_projects: list[RankedProject]
    top_subagents: list[RankedItem]
    time: TimeMetrics
    models: ModelMix
    skipped_records: int
    warnings: list[str] = field(default_factory=list)


WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def filter_window(
    sessions: Iterable[Session], since: datetime, until: datetime
) -> list[Session]:
    return [s for s in sessions if since <= s.started_at <= until]


def filter_project(
    sessions: Iterable[Session],
    projects: dict[str, Project],
    project_ref: str,
) -> list[Session]:
    matches: set[str] = set()
    for pid, p in projects.items():
        if project_ref == pid or project_ref == p.display_name:
            matches.add(pid)
    return [s for s in sessions if s.project_id in matches]


def _top_n(counter: Counter, n: int = 5) -> list[RankedItem]:
    return [
        RankedItem(rank=i + 1, name=name, count=count)
        for i, (name, count) in enumerate(counter.most_common(n))
    ]


def _model_family(model: str | None) -> str:
    if not model:
        return "other"
    lower = model.lower()
    if "opus" in lower:
        return "opus"
    if "sonnet" in lower:
        return "sonnet"
    if "haiku" in lower:
        return "haiku"
    return "other"


def aggregate(
    sessions: list[Session],
    projects: dict[str, Project],
    since: datetime,
    until: datetime,
    project_filter: str | None,
    skipped_records: int,
) -> Report:
    window = Window(since=since, until=until, project=project_filter)
    scoped = filter_window(sessions, since, until)
    if project_filter:
        scoped = filter_project(scoped, projects, project_filter)

    totals = Totals(sessions=len(scoped))
    tool_counter: Counter = Counter()
    subagent_counter: Counter = Counter()
    project_counter: Counter = Counter()
    hour_counter: Counter = Counter()
    weekday_counter: Counter = Counter()
    model_family_counter: Counter = Counter()
    active_days: set = set()
    longest = 0

    for s in scoped:
        totals.messages += s.message_count
        totals.tool_calls += s.tool_call_count
        totals.tokens_input += s.tokens_input
        totals.tokens_output += s.tokens_output
        totals.tokens_cache_read += s.tokens_cache_read
        totals.tokens_cache_create += s.tokens_cache_create
        local_start = s.started_at.astimezone()
        active_days.add(local_start.date())
        hour_counter[local_start.hour] += 1
        weekday_counter[local_start.weekday()] += 1
        project_counter[s.project_id] += 1
        model_family_counter[_model_family(s.model)] += 1
        duration = int((s.ended_at - s.started_at).total_seconds())
        if duration > longest:
            longest = duration
        for tc in s.tool_calls:
            tool_counter[tc.tool_name] += 1
            if tc.subagent:
                subagent_counter[tc.subagent] += 1

    totals.active_days = len(active_days)

    top_tools = _top_n(tool_counter)
    top_subagents = _top_n(subagent_counter)
    ranked_projects: list[RankedProject] = []
    for i, (pid, count) in enumerate(project_counter.most_common(5)):
        display = projects[pid].display_name if pid in projects else pid
        ranked_projects.append(
            RankedProject(rank=i + 1, id=pid, name=display, sessions=count)
        )

    time = TimeMetrics(longest_session_seconds=longest)
    if hour_counter:
        time.busiest_hour_local = hour_counter.most_common(1)[0][0]
    if weekday_counter:
        time.busiest_weekday_local = WEEKDAYS[weekday_counter.most_common(1)[0][0]]

    total_sessions = sum(model_family_counter.values()) or 1
    models = ModelMix(
        opus_pct=round(100 * model_family_counter["opus"] / total_sessions, 1),
        sonnet_pct=round(100 * model_family_counter["sonnet"] / total_sessions, 1),
        haiku_pct=round(100 * model_family_counter["haiku"] / total_sessions, 1),
        other_pct=round(100 * model_family_counter["other"] / total_sessions, 1),
    )

    return Report(
        window=window,
        totals=totals,
        top_tools=top_tools,
        top_projects=ranked_projects,
        top_subagents=top_subagents,
        time=time,
        models=models,
        skipped_records=skipped_records,
    )
