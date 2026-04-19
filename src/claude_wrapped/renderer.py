from __future__ import annotations

import os
import sys
import time
from collections import Counter
from datetime import datetime

import orjson
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from .aggregator import Report, WEEKDAYS, filter_project, filter_window
from .models import Project, Session


def _format_duration(seconds: int) -> str:
    if seconds <= 0:
        return "0s"
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)


def _totals_panel(report: Report) -> Panel:
    t = report.totals
    table = Table.grid(padding=(0, 2))
    table.add_column(style="cyan", no_wrap=True)
    table.add_column()
    table.add_row("Sessions", str(t.sessions))
    table.add_row("Messages", str(t.messages))
    table.add_row("Tool calls", str(t.tool_calls))
    table.add_row("Active days", str(t.active_days))
    table.add_row(
        "Tokens (in / out / cache read / cache write)",
        f"{t.tokens_input} / {t.tokens_output} / "
        f"{t.tokens_cache_read} / {t.tokens_cache_create}",
    )
    return Panel(
        table,
        title=f"Totals ({report.window.since.date()} → {report.window.until.date()})",
        border_style="cyan",
    )


def _ranked_panel(title: str, items, cols: list[tuple[str, str]]) -> Panel:
    table = Table(show_header=True, header_style="bold")
    for label, _attr in cols:
        table.add_column(label)
    for item in items:
        row = [str(getattr(item, attr)) for _label, attr in cols]
        table.add_row(*row)
    if not items:
        table.add_row(*["—" for _ in cols])
    return Panel(table, title=title, border_style="magenta")


def _time_panel(report: Report) -> Panel:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="cyan", no_wrap=True)
    table.add_column()
    bh = report.time.busiest_hour_local
    bw = report.time.busiest_weekday_local or "—"
    table.add_row("Busiest hour", f"{bh:02d}:00" if bh is not None else "—")
    table.add_row("Busiest weekday", bw)
    table.add_row(
        "Longest session", _format_duration(report.time.longest_session_seconds)
    )
    return Panel(table, title="Time", border_style="yellow")


def _models_panel(report: Report) -> Panel:
    m = report.models
    table = Table.grid(padding=(0, 2))
    table.add_column(style="cyan", no_wrap=True)
    table.add_column()
    table.add_row("Opus", f"{m.opus_pct:.1f}%")
    table.add_row("Sonnet", f"{m.sonnet_pct:.1f}%")
    table.add_row("Haiku", f"{m.haiku_pct:.1f}%")
    if m.other_pct > 0:
        table.add_row("Other", f"{m.other_pct:.1f}%")
    return Panel(table, title="Models", border_style="green")


def _cost_panel(cost_usd: float) -> Panel:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="cyan", no_wrap=True)
    table.add_column()
    table.add_row("Estimate", f"~${cost_usd:,.2f} (approximate)")
    return Panel(table, title="Cost", border_style="red")


def render_report(
    report: Report, console: Console | None = None, cost_usd: float | None = None
) -> None:
    console = console or Console()
    scope = (
        f"project={report.window.project}"
        if report.window.project
        else "all projects"
    )
    console.print(f"[bold]Claude Wrapped[/bold] — {scope}")
    console.print(_totals_panel(report))
    console.print(
        _ranked_panel(
            "Top 5 tools",
            report.top_tools,
            [("#", "rank"), ("Tool", "name"), ("Count", "count")],
        )
    )
    console.print(
        _ranked_panel(
            "Top 5 projects",
            report.top_projects,
            [("#", "rank"), ("Project", "name"), ("Sessions", "sessions")],
        )
    )
    if report.top_subagents:
        console.print(
            _ranked_panel(
                "Top subagents",
                report.top_subagents,
                [("#", "rank"), ("Subagent", "name"), ("Count", "count")],
            )
        )
    console.print(_time_panel(report))
    console.print(_models_panel(report))
    if cost_usd is not None:
        console.print(_cost_panel(cost_usd))
    if report.skipped_records:
        console.print(
            f"[dim]Note: skipped {report.skipped_records} malformed record(s).[/dim]"
        )


def render_empty_message(year: int, console: Console | None = None) -> None:
    console = console or Console()
    console.print(
        f"No Claude Code history found for {year}. "
        "Run [bold]claude-wrapped --dry-run[/bold] to see which files were scanned."
    )


def report_to_dict(report: Report, cost_usd: float | None = None) -> dict:
    return {
        "window": {
            "since": report.window.since.date().isoformat(),
            "until": report.window.until.date().isoformat(),
            "project": report.window.project,
        },
        "totals": {
            "sessions": report.totals.sessions,
            "messages": report.totals.messages,
            "tool_calls": report.totals.tool_calls,
            "tokens": {
                "input": report.totals.tokens_input,
                "output": report.totals.tokens_output,
                "cache_read": report.totals.tokens_cache_read,
                "cache_create": report.totals.tokens_cache_create,
            },
            "active_days": report.totals.active_days,
        },
        "top_tools": [
            {"rank": t.rank, "name": t.name, "count": t.count}
            for t in report.top_tools
        ],
        "top_projects": [
            {"rank": p.rank, "id": p.id, "name": p.name, "sessions": p.sessions}
            for p in report.top_projects
        ],
        "top_subagents": [
            {"rank": s.rank, "name": s.name, "count": s.count}
            for s in report.top_subagents
        ],
        "time": {
            "busiest_hour_local": report.time.busiest_hour_local,
            "busiest_weekday_local": report.time.busiest_weekday_local,
            "longest_session_seconds": report.time.longest_session_seconds,
        },
        "models": {
            "opus_pct": report.models.opus_pct,
            "sonnet_pct": report.models.sonnet_pct,
            "haiku_pct": report.models.haiku_pct,
        },
        "cost_estimate_usd": cost_usd,
        "skipped_records": report.skipped_records,
        "warnings": list(report.warnings),
    }


def render_json(report: Report, cost_usd: float | None = None) -> None:
    payload = report_to_dict(report, cost_usd)
    sys.stdout.write(orjson.dumps(payload).decode())
    sys.stdout.write("\n")


def _story_frames(report: Report) -> list[Panel]:
    """Build the slideshow frames in presentation order."""
    intro = Panel.fit(
        "[bold magenta]✨ Your Claude Wrapped ✨[/bold magenta]\n"
        f"[dim]{report.window.since.date()} → {report.window.until.date()}[/dim]",
        border_style="magenta",
    )
    frames: list[Panel] = [intro, _totals_panel(report)]
    frames.append(
        _ranked_panel(
            "Top 5 tools",
            report.top_tools,
            [("#", "rank"), ("Tool", "name"), ("Count", "count")],
        )
    )
    frames.append(
        _ranked_panel(
            "Top 5 projects",
            report.top_projects,
            [("#", "rank"), ("Project", "name"), ("Sessions", "sessions")],
        )
    )
    frames.append(_time_panel(report))
    frames.append(_models_panel(report))
    frames.append(
        Panel.fit(
            "[bold]That's a wrap.[/bold] 🎬",
            border_style="magenta",
        )
    )
    return frames


def render_story(report: Report, console: Console | None = None) -> None:
    console = console or Console()
    dwell = float(os.environ.get("CLAUDE_WRAPPED_STORY_DWELL", "2.0"))
    frames = _story_frames(report)
    try:
        with Live(frames[0], console=console, refresh_per_second=8, screen=False) as live:
            for frame in frames[1:]:
                time.sleep(dwell)
                live.update(frame)
            time.sleep(dwell)
    except KeyboardInterrupt:
        console.print()  # Ensure cursor lands on a fresh line.


def render_tools_heatmap(
    sessions: list[Session],
    since: datetime,
    until: datetime,
    project_ref: str | None,
    projects: dict[str, Project],
    console: Console | None = None,
) -> None:
    console = console or Console()
    scoped = filter_window(sessions, since, until)
    if project_ref:
        scoped = filter_project(scoped, projects, project_ref)

    counts: dict[str, Counter] = {}
    tool_names: Counter = Counter()
    for s in scoped:
        for tc in s.tool_calls:
            weekday = WEEKDAYS[tc.timestamp.astimezone().weekday()]
            counts.setdefault(tc.tool_name, Counter())[weekday] += 1
            tool_names[tc.tool_name] += 1

    table = Table(title="Tool × Weekday", show_header=True, header_style="bold")
    table.add_column("Tool")
    for day in WEEKDAYS:
        table.add_column(day, justify="right")
    for name, _total in tool_names.most_common():
        row = [name] + [str(counts[name].get(day, 0)) for day in WEEKDAYS]
        table.add_row(*row)
    if not tool_names:
        table.add_row("—", *(["0"] * len(WEEKDAYS)))
    console.print(table)


def render_tools_heatmap_json(
    sessions: list[Session],
    since: datetime,
    until: datetime,
    project_ref: str | None,
    projects: dict[str, Project],
) -> None:
    scoped = filter_window(sessions, since, until)
    if project_ref:
        scoped = filter_project(scoped, projects, project_ref)
    heat: Counter = Counter()
    for s in scoped:
        for tc in s.tool_calls:
            weekday = WEEKDAYS[tc.timestamp.astimezone().weekday()]
            heat[(tc.tool_name, weekday)] += 1
    payload = [
        {"tool": tool, "weekday": wd, "count": c}
        for (tool, wd), c in heat.items()
    ]
    sys.stdout.write(orjson.dumps(payload).decode())
    sys.stdout.write("\n")
