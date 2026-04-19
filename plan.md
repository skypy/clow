# Claude Wrapped CLI — Plan

## Spec (1-liner)
Parse local Claude Code data → render a personal year-in-review in the terminal.

## Non-goals
HTML/web output, cloud sync, multi-user, real-time dashboard, editing local files.

## Tech stack
- Python 3.11+
- `click` (CLI), `rich` (tables / panels / live slides), `orjson` (fast JSONL), `platformdirs`
- Distribution: `pipx install claude-wrapped`

## Data sources
- `~/.claude/projects/*/*.jsonl` — messages, tool_use, `usage` tokens, timestamps, model id
- `~/.claude.json` — project registry, permission history
- `~/.claude/todos/*.json` — optional task enrichment

## Architecture
```
src/claude_wrapped/
  cli.py         # click entrypoint
  loader.py      # discover + stream JSONL
  parser.py      # normalize events
  aggregator.py  # compute metrics
  renderer.py    # rich output (report + story modes)
  models.py      # Session, ToolCall, Metric dataclasses
  pricing.py     # per-model token rates
```

## Metrics (v1)
- **Totals**: sessions, messages, tool calls, tokens (input/output/cache), active days
- **Top 5**: tools, projects, subagents
- **Time**: busiest hour, busiest weekday, longest session
- **Models**: % mix across Opus / Sonnet / Haiku
- **Cost estimate**: tokens × rate table (opt-in flag — rates drift)

## CLI surface
- `claude-wrapped` — current-year report
- `--year 2026` | `--since / --until`
- `--project <path>` — scope to one repo
- `--story` — animated slideshow via `rich.live`
- `--json` — machine-readable dump
- `tools` subcommand — standalone tool heatmap
- `--dry-run` — list files that would be scanned

## Phases
1. Loader + parser, tested against anonymized fixtures
2. Aggregator with unit tests
3. Static report renderer
4. `--story` slideshow polish
5. Packaging, README, `pipx` install instructions

## Risks / open questions
- JSONL schema isn't a public API — pin against current Claude Code version, guard with graceful-skip on unknown event types.
- Cost rates drift → default off, document rate table location.
- Deleted/moved projects: dereference paths, fall back to last-seen name from `~/.claude.json`.

## Validation
Fixture tests from your own JSONL (anonymized), `--dry-run` file list, per-session totals must sum to grand total.
