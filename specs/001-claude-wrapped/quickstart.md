# Quickstart — Claude Wrapped

## Install

```bash
pipx install claude-wrapped
```

`pipx` isolates the tool from your system Python. If you don't have it:
`python -m pip install --user pipx && python -m pipx ensurepath`.

## Run

```bash
# Full year-in-review for the current calendar year
claude-wrapped

# A specific past year
claude-wrapped --year 2025

# Just one project
claude-wrapped --project my-api

# Animated slideshow
claude-wrapped --story

# Machine-readable output for piping into other tools
claude-wrapped --json | jq .top_tools

# Cost estimate (opt-in, approximate)
claude-wrapped --cost

# Audit what the tool would read, without actually processing
claude-wrapped --dry-run
```

## What you should see

A panel-style terminal report containing:

- **Totals** — sessions, messages, tool calls, tokens (4 categories),
  active days
- **Top 5 tools** — most-used tools over the window
- **Top 5 projects** — busiest projects over the window
- **Top 5 subagents** — (if you used any)
- **Time** — busiest hour and weekday in your local time, longest session
- **Models** — Opus/Sonnet/Haiku percentage mix
- **Cost** — only when `--cost` is passed; clearly labelled approximate

Empty-dataset runs print a friendly "no Claude Code history found for
this window" and exit 0.

## Verifying it worked

A quick sanity check that maps to Constitution IV and SC-003:

```bash
# Human and JSON outputs should report the same grand totals.
claude-wrapped            > /tmp/report.txt
claude-wrapped --json     > /tmp/report.json

jq '.totals.sessions' /tmp/report.json
grep -E 'sessions\s*[|:]\s*[0-9]+' /tmp/report.txt
```

## Troubleshooting

- **"No data found"** but you know you've used Claude Code — confirm
  your history lives under `~/.claude/projects/`. Run with `--dry-run`
  to see which files the tool discovers.
- **Skipped records shown at the bottom of the report** — expected; the
  Claude Code JSONL format drifts between releases. If the count is
  large, re-run with `--verbose` to see which files and events are
  being skipped.
- **Report looks cramped** — widen your terminal. The tool wraps tables
  at your current width rather than forcing a minimum.

## What's out of scope (v1)

- HTML / web output
- Cloud sync or sharing links
- Multi-user accounts
- Real-time / live dashboards
- Editing any local file

These are intentional non-goals per Constitution V and the feature spec.
