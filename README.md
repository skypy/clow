# claude-wrapped

A personal year-in-review for your Claude Code history, rendered in the
terminal. Reads your local `~/.claude/projects/*.jsonl` logs, computes
totals + top-lists + time metrics + model mix, and prints a rich report.
No network, no telemetry, no cloud anything.

## Install

```bash
pipx install claude-wrapped
```

`pipx` keeps the tool isolated from your system Python. If you don't
have it yet:

```bash
python -m pip install --user pipx
python -m pipx ensurepath
```

## Run

```bash
# The full year-in-review for the current calendar year
claude-wrapped

# A past year
claude-wrapped --year 2025

# Custom date window
claude-wrapped --since 2026-01-01 --until 2026-03-31

# Just one project (match by display name or encoded id)
claude-wrapped --project my-api

# Machine-readable output for piping into other tools
claude-wrapped --json | jq .top_tools

# Animated slideshow
claude-wrapped --story

# Opt-in approximate cost estimate
claude-wrapped --cost

# Standalone tool-usage heatmap (tool × weekday)
claude-wrapped tools
claude-wrapped tools --json

# Audit what the tool would read, without processing
claude-wrapped --dry-run

# Show per-file warnings on stderr; surface full tracebacks on errors
claude-wrapped --verbose
```

Global flags can appear before or after the `tools` subcommand:
`claude-wrapped --json tools` and `claude-wrapped tools --json` both work.

## What you'll see

- **Totals** — sessions, messages, tool calls, tokens (input, output,
  cache read, cache write), active days
- **Top 5 tools** — most-used tools over the selected window
- **Top 5 projects** — busiest projects
- **Top subagents** — subagents invoked via the `Task` tool, if any
- **Time** — busiest hour and weekday in your local timezone, longest
  single session
- **Models** — Opus / Sonnet / Haiku / Other mix as percentages
- **Cost** — only when `--cost` is passed, clearly labelled approximate

Empty datasets print a friendly "no history found" and exit `0` (never
a traceback).

## JSON schema (stable v1)

```jsonc
{
  "window":  { "since": "...", "until": "...", "project": null },
  "totals":  { "sessions": 0, "messages": 0, "tool_calls": 0,
               "tokens": { "input": 0, "output": 0,
                           "cache_read": 0, "cache_create": 0 },
               "active_days": 0 },
  "top_tools":     [ { "rank": 1, "name": "...", "count": 0 } ],
  "top_projects":  [ { "rank": 1, "id": "...", "name": "...", "sessions": 0 } ],
  "top_subagents": [ { "rank": 1, "name": "...", "count": 0 } ],
  "time":   { "busiest_hour_local": 0, "busiest_weekday_local": "Mon",
              "longest_session_seconds": 0 },
  "models": { "opus_pct": 0.0, "sonnet_pct": 0.0, "haiku_pct": 0.0 },
  "cost_estimate_usd": null,
  "skipped_records": 0,
  "warnings": []
}
```

Every key is always present — stable shape beats conditional keys for
downstream scripts.

## Troubleshooting

- **"No Claude Code history found"** but you know you have history —
  run `claude-wrapped --dry-run` to see which files were discovered.
  The tool reads from `~/.claude/projects/*/*.jsonl`.
- **Skipped records shown at the bottom of the report** — expected;
  the Claude Code JSONL format drifts between releases. Re-run with
  `--verbose` to see which events were rejected.
- **Report looks cramped** — widen your terminal. Rich wraps at the
  current width rather than forcing a minimum.
- **"Longest session" looks absurdly large** — Claude Code sometimes
  resumes old sessions, so `started_at` and `ended_at` can legitimately
  span days or weeks in the raw logs. This is real data, not a bug.

## Non-goals (v1)

- HTML / web output
- Cloud sync or sharing links
- Multi-user accounts
- Real-time dashboards
- Editing any local file

See [`specs/001-claude-wrapped/spec.md`](specs/001-claude-wrapped/spec.md)
for the feature spec and
[`specs/001-claude-wrapped/plan.md`](specs/001-claude-wrapped/plan.md)
for the implementation plan.

## Local development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
```

All tests run against anonymized JSONL fixtures at
`tests/fixtures/sample_session.jsonl` — no network, no dependency on
your own Claude Code history.

## License

MIT.
