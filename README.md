# claude-wrapped

> Your personal year-in-review for Claude Code, rendered in the terminal.

`claude-wrapped` parses the JSONL logs that Claude Code already writes to
`~/.claude/projects/`, aggregates a year (or any window) of your usage,
and prints a rich report: total sessions, top tools, top projects,
busiest hour and weekday, model-family mix, and an optional approximate
token-cost estimate — all locally, no network, no telemetry.

```text
Claude Wrapped — all projects
╭────────────────────── Totals (2026-01-01 → 2026-12-31) ──────────────────────╮
│ Sessions                                      78                             │
│ Messages                                      31358                          │
│ Tool calls                                    9539                           │
│ Active days                                   35                             │
│ Tokens (in / out / cache read / cache write)  435803 / 4158442 / ...         │
╰──────────────────────────────────────────────────────────────────────────────╯
╭──────────────────────────────── Top 5 tools ─────────────────────────────────╮
│ 1  Bash    2953                                                              │
│ 2  Read    2741                                                              │
│ 3  Grep    1359                                                              │
│ 4  Edit    1327                                                              │
│ 5  Glob    338                                                               │
╰──────────────────────────────────────────────────────────────────────────────╯
╭──────────────────────────────────── Time ────────────────────────────────────╮
│ Busiest hour     18:00                                                       │
│ Busiest weekday  Fri                                                         │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─────────────────────────────────── Models ───────────────────────────────────╮
│ Opus  43.6 %   Sonnet  26.9 %   Haiku  7.7 %   Other  21.8 %                 │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Features

- Full-year summary (default) or any `--since`/`--until`/`--year` window
- Top 5 tools, projects, and subagents
- Busiest hour, busiest weekday, longest session (local timezone)
- Model-family mix across Opus / Sonnet / Haiku
- Optional approximate token-cost estimate (`--cost`)
- Stable JSON export for piping into `jq` or your own scripts (`--json`)
- Animated slideshow mode (`--story`)
- Standalone tool × weekday heatmap (`tools` subcommand)
- Dry-run mode to audit which files would be read (`--dry-run`)
- Graceful handling of JSONL schema drift — skips unknown events and
  reports the count, never crashes

## Requirements

- Python 3.11 or newer
- Claude Code data under `~/.claude/projects/*.jsonl` (the defaults
  Claude Code writes to — no extra config needed)
- A terminal wider than ~60 columns for best rendering

## Install

The tool is not on PyPI yet, so install from source.

### Option 1 — `pipx` (recommended for end users)

```bash
git clone https://github.com/skypy/clow.git
pipx install ./clow
claude-wrapped --help
```

`pipx` puts `claude-wrapped` on your `PATH` in its own managed venv. To
pick up future edits, `pipx reinstall claude-wrapped`.

### Option 2 — virtualenv (recommended for development)

```bash
git clone https://github.com/skypy/clow.git
cd clow
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
claude-wrapped
```

Editable install means edits to `src/claude_wrapped/` take effect
immediately — handy while hacking on the tool. Deactivate with
`deactivate` when you're done.

If you want to call it from any directory without activating the venv,
add this to `~/.bashrc` or `~/.zshrc`:

```bash
alias claude-wrapped='/absolute/path/to/clow/.venv/bin/claude-wrapped'
```

## Usage

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

# Standalone tool × weekday heatmap
claude-wrapped tools
claude-wrapped tools --json

# Audit which files the tool would scan, without processing them
claude-wrapped --dry-run

# Show per-file warnings on stderr; surface full tracebacks on errors
claude-wrapped --verbose
```

Global flags can appear before *or* after the `tools` subcommand —
`claude-wrapped --json tools` and `claude-wrapped tools --json` both
work.

### Exit codes

| Code | Meaning                                        |
|------|-----------------------------------------------|
| 0    | Success (report printed, or dry-run list printed) |
| 2    | User error (unknown flag, invalid date, etc.)  |
| 1    | Internal error (I/O failure, unexpected exception) |

### JSON schema (stable v1)

Every key below is always present — stable shape beats conditional keys
for downstream scripts.

```jsonc
{
  "window":  { "since": "2026-01-01", "until": "2026-12-31", "project": null },
  "totals":  { "sessions": 0, "messages": 0, "tool_calls": 0,
               "tokens": { "input": 0, "output": 0,
                           "cache_read": 0, "cache_create": 0 },
               "active_days": 0 },
  "top_tools":     [ { "rank": 1, "name": "Bash", "count": 0 } ],
  "top_projects":  [ { "rank": 1, "id": "...", "name": "...", "sessions": 0 } ],
  "top_subagents": [ { "rank": 1, "name": "Explore", "count": 0 } ],
  "time":   { "busiest_hour_local": 18, "busiest_weekday_local": "Fri",
              "longest_session_seconds": 0 },
  "models": { "opus_pct": 0.0, "sonnet_pct": 0.0, "haiku_pct": 0.0 },
  "cost_estimate_usd": null,
  "skipped_records": 0,
  "warnings": []
}
```

## Tech stack

- **Language**: Python 3.11+
- **CLI framework**: [`click`](https://click.palletsprojects.com/)
- **Terminal rendering**: [`rich`](https://rich.readthedocs.io/) — tables, panels, and `rich.live` for story mode
- **JSON parsing**: [`orjson`](https://github.com/ijl/orjson) — fast JSONL line parsing at scale
- **Path resolution**: [`platformdirs`](https://platformdirs.readthedocs.io/) — locates the Claude Code data directory across macOS/Linux
- **Packaging**: [`hatchling`](https://hatch.pypa.io/) build backend; single-package wheel installable via `pipx`
- **Testing**: [`pytest`](https://docs.pytest.org/) + anonymized JSONL fixtures (37 tests, ~0.4s end-to-end)
- **Linting / formatting**: `ruff` + `black`
- **Spec-driven development**: [spec-kit](https://github.com/github/spec-kit) — see `specs/001-claude-wrapped/` and `.specify/memory/constitution.md`

## How it works

1. **Discover** all `*.jsonl` files under `~/.claude/projects/`.
2. **Stream** each line via `orjson`; skip malformed lines and count them.
3. **Normalize** each record into typed `Session` / `ToolCall` /
   `Project` dataclasses. Unknown `type` values (future Claude Code
   event schemas) are silently ignored; only *malformed* records are
   counted as skipped.
4. **Aggregate** over a time window: totals, top-5s, busiest hour/weekday,
   longest session, model-family mix.
5. **Render** via `rich` (human report or slideshow) or serialize as JSON
   matching the stable schema above.

See [`specs/001-claude-wrapped/data-model.md`](specs/001-claude-wrapped/data-model.md)
and [`specs/001-claude-wrapped/plan.md`](specs/001-claude-wrapped/plan.md)
for the full design.

## Privacy

- **No network calls.** The tool never contacts any remote server,
  telemetry endpoint, or API.
- **Read-only.** It does not modify your Claude Code data. It only
  reads from `~/.claude/projects/` and `~/.claude.json`.
- **No caches, no config files.** Each invocation reads fresh from disk;
  uninstalling the tool leaves no residue.

## Troubleshooting

- **"No Claude Code history found"** but you know you have history —
  run `claude-wrapped --dry-run` to see which files were discovered.
- **Skipped records shown at the bottom of the report** — expected;
  the Claude Code JSONL format drifts between releases. Re-run with
  `--verbose` to see which records were rejected and in which files.
- **Report looks cramped** — widen your terminal. Rich wraps at the
  current width; there is no minimum.
- **"Longest session" looks absurdly large** — Claude Code sometimes
  resumes old sessions, so `started_at` and `ended_at` can legitimately
  span days or weeks in the raw logs. This is real data, not a bug.
- **`claude-wrapped: command not found`** — if you installed via the
  virtualenv path, the binary lives in `.venv/bin/`. Either activate
  the venv (`. .venv/bin/activate`) or add the alias shown in the
  install section to your shell rc file.

## Non-goals (v1)

- HTML / web dashboards
- Cloud sync or shareable links
- Multi-user accounts or permission systems
- Real-time / live-updating dashboards
- Editing any local file

## Development

```bash
git clone https://github.com/skypy/clow.git
cd clow
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
```

All tests run against anonymized JSONL fixtures at
`tests/fixtures/sample_session.jsonl` — no network, no dependency on
your own Claude Code history, ~0.4s to green.

The project follows a spec-driven workflow:

- `.specify/memory/constitution.md` — principles the code honors
  (local-first, CLI text protocol, graceful schema degradation,
  fixture-driven testing, YAGNI)
- `specs/001-claude-wrapped/` — feature spec, implementation plan,
  research, data model, CLI contract, task list

Contributions are welcome. Open an issue or PR at
<https://github.com/skypy/clow>.

## License

MIT — see [`LICENSE`](LICENSE).
