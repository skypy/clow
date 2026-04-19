from __future__ import annotations

import sys
from datetime import datetime, timezone

import click

from . import __version__
from .aggregator import aggregate
from .loader import discover_jsonl_files, load_project_registry, stream_records
from .parser import parse_records
from .pricing import estimate_cost
from .renderer import (
    render_empty_message,
    render_json,
    render_report,
    render_story,
    render_tools_heatmap,
    render_tools_heatmap_json,
    report_to_dict,
)


def _resolve_window(year, since, until):
    if year is not None and (since is not None or until is not None):
        raise click.UsageError("--year is mutually exclusive with --since/--until")
    if since is not None or until is not None:
        start = (
            since.replace(tzinfo=timezone.utc)
            if since
            else datetime(1970, 1, 1, tzinfo=timezone.utc)
        )
        end = (
            until.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
            if until
            else datetime.now(timezone.utc)
        )
        return start, end
    year = year or datetime.now(timezone.utc).year
    return (
        datetime(year, 1, 1, tzinfo=timezone.utc),
        datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
    )


def _build(since, until, project_filter):
    files = discover_jsonl_files()
    registry = load_project_registry()
    parsed = parse_records(stream_records(files), registry=registry)
    report = aggregate(
        sessions=parsed.sessions,
        projects=parsed.projects,
        since=since,
        until=until,
        project_filter=project_filter,
        skipped_records=parsed.skipped_records,
    )
    return report, parsed, files


def _empty_report_dict(since, until, project_filter):
    return {
        "window": {
            "since": since.date().isoformat(),
            "until": until.date().isoformat(),
            "project": project_filter,
        },
        "totals": {
            "sessions": 0,
            "messages": 0,
            "tool_calls": 0,
            "tokens": {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0},
            "active_days": 0,
        },
        "top_tools": [],
        "top_projects": [],
        "top_subagents": [],
        "time": {
            "busiest_hour_local": None,
            "busiest_weekday_local": None,
            "longest_session_seconds": 0,
        },
        "models": {"opus_pct": 0.0, "sonnet_pct": 0.0, "haiku_pct": 0.0},
        "cost_estimate_usd": None,
        "skipped_records": 0,
        "warnings": [],
    }


@click.group(
    invoke_without_command=True,
    help="Render a personal year-in-review from local Claude Code data.",
)
@click.option("--year", type=int, default=None, help="Calendar year (default: current).")
@click.option("--since", type=click.DateTime(["%Y-%m-%d"]), default=None)
@click.option("--until", type=click.DateTime(["%Y-%m-%d"]), default=None)
@click.option("--project", type=str, default=None, help="Scope to one project (name or id).")
@click.option("--story", is_flag=True, default=False, help="Animated slideshow mode.")
@click.option("--json", "json_out", is_flag=True, default=False, help="Emit JSON to stdout.")
@click.option("--cost", is_flag=True, default=False, help="Include approximate token-cost estimate.")
@click.option("--dry-run", is_flag=True, default=False, help="List files that would be scanned, then exit.")
@click.option("--verbose", is_flag=True, default=False, help="Show per-file warnings on stderr.")
@click.version_option(__version__)
@click.pass_context
def main(
    ctx: click.Context,
    year: int | None,
    since,
    until,
    project: str | None,
    story: bool,
    json_out: bool,
    cost: bool,
    dry_run: bool,
    verbose: bool,
) -> None:
    ctx.ensure_object(dict)
    ctx.obj.update(
        year=year,
        since=since,
        until=until,
        project=project,
        json_out=json_out,
        dry_run=dry_run,
        verbose=verbose,
    )
    if ctx.invoked_subcommand is not None:
        return

    try:
        if story and json_out:
            raise click.UsageError("--story cannot be combined with --json")

        since_dt, until_dt = _resolve_window(year, since, until)

        if dry_run:
            for path in discover_jsonl_files():
                click.echo(str(path))
            sys.exit(0)

        report, parsed, _files = _build(since_dt, until_dt, project)

        if verbose:
            for warning in parsed.warnings:
                click.echo(warning, err=True)

        cost_usd = estimate_cost(report.totals, report.models) if cost else None

        if report.totals.sessions == 0:
            if json_out:
                import orjson
                sys.stdout.write(
                    orjson.dumps(_empty_report_dict(since_dt, until_dt, project)).decode()
                )
                sys.stdout.write("\n")
            else:
                render_empty_message(since_dt.year)
            sys.exit(0)

        if json_out:
            render_json(report, cost_usd=cost_usd)
        elif story:
            render_story(report)
        else:
            render_report(report, cost_usd=cost_usd)
    except click.UsageError:
        raise
    except Exception as exc:  # noqa: BLE001 — unknown runtime failures
        if verbose:
            raise
        click.echo(
            f"Error: {exc}. Re-run with --verbose for details.", err=True
        )
        sys.exit(1)


@main.command("tools", help="Show a tool × weekday heatmap.")
@click.option("--year", type=int, default=None)
@click.option("--since", type=click.DateTime(["%Y-%m-%d"]), default=None)
@click.option("--until", type=click.DateTime(["%Y-%m-%d"]), default=None)
@click.option("--project", type=str, default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--verbose", is_flag=True, default=False)
@click.pass_context
def tools_cmd(
    ctx: click.Context,
    year,
    since,
    until,
    project,
    json_out,
    dry_run,
    verbose,
) -> None:
    obj = ctx.obj or {}
    # Subcommand-local flags override anything inherited from the group.
    year = year if year is not None else obj.get("year")
    since = since if since is not None else obj.get("since")
    until = until if until is not None else obj.get("until")
    project = project if project is not None else obj.get("project")
    json_out = json_out or obj.get("json_out", False)
    dry_run = dry_run or obj.get("dry_run", False)
    verbose = verbose or obj.get("verbose", False)

    try:
        since_dt, until_dt = _resolve_window(year, since, until)
        if dry_run:
            for path in discover_jsonl_files():
                click.echo(str(path))
            sys.exit(0)
        _report, parsed, _files = _build(since_dt, until_dt, project)
        if verbose:
            for warning in parsed.warnings:
                click.echo(warning, err=True)
        if json_out:
            render_tools_heatmap_json(
                parsed.sessions, since_dt, until_dt, project, parsed.projects
            )
        else:
            render_tools_heatmap(
                parsed.sessions, since_dt, until_dt, project, parsed.projects
            )
    except click.UsageError:
        raise
    except Exception as exc:  # noqa: BLE001
        if verbose:
            raise
        click.echo(
            f"Error: {exc}. Re-run with --verbose for details.", err=True
        )
        sys.exit(1)


# Silence a lint warning about unused imports in type-narrow branches above.
_ = report_to_dict
