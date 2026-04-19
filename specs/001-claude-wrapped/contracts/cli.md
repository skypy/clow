# CLI Contract — `claude-wrapped`

This is the public interface users and scripts depend on. Changes to
exit codes, flag names, or JSON schema fields are breaking and require
a MAJOR version bump per Constitution V.

## Invocation

```text
claude-wrapped [OPTIONS]
claude-wrapped tools [OPTIONS]
```

### Top-level command: `claude-wrapped`

Produces the full year-in-review report.

| Flag | Type | Default | Notes |
|------|------|---------|-------|
| `--year` | int | current calendar year | Selects Jan 1 → Dec 31 of YEAR. |
| `--since` | ISO date | — | Overrides `--year`. Inclusive. |
| `--until` | ISO date | today | Used with `--since`. Inclusive. |
| `--project` | string | — | Display name or ID; scopes all metrics. |
| `--story` | flag | off | Animated slideshow mode (`rich.live`). |
| `--json` | flag | off | Emits JSON to stdout; no ANSI. |
| `--cost` | flag | off | Include token-cost estimate (opt-in). |
| `--dry-run` | flag | off | Print files that would be scanned, exit 0. |
| `--verbose` | flag | off | Print per-file skip counts. |
| `--version` | flag | off | Print version, exit 0. |
| `--help` | flag | off | Standard click help. |

**Mutually exclusive groups**: `--year` vs `(--since, --until)`; `--story`
vs `--json`.

### Subcommand: `claude-wrapped tools`

Standalone tool-usage heatmap (tool × weekday).

| Flag | Type | Default | Notes |
|------|------|---------|-------|
| `--year` / `--since` / `--until` / `--project` / `--json` | — | — | Same semantics as above. |

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success (report printed, or dry-run list printed). |
| `2` | User error (unknown flag, invalid date, mutually-exclusive conflict). |
| `1` | Internal error (I/O failure, unexpected exception). |

Per Constitution II: no crash traceback reaches the user by default;
tracebacks only appear under `--verbose`.

## stdout vs stderr

- **stdout**: the report (human or JSON).
- **stderr**: warnings, skip counts, any diagnostic. Empty on the happy
  path unless `--verbose`.

## `--json` output schema (v1)

```json
{
  "window": {
    "since": "2026-01-01",
    "until": "2026-04-19",
    "project": null
  },
  "totals": {
    "sessions": 0,
    "messages": 0,
    "tool_calls": 0,
    "tokens": {
      "input": 0,
      "output": 0,
      "cache_read": 0,
      "cache_create": 0
    },
    "active_days": 0
  },
  "top_tools": [
    { "rank": 1, "name": "Read", "count": 0 }
  ],
  "top_projects": [
    { "rank": 1, "id": "home-user-project-foo", "name": "foo", "sessions": 0 }
  ],
  "top_subagents": [
    { "rank": 1, "name": "Explore", "count": 0 }
  ],
  "time": {
    "busiest_hour_local": 0,
    "busiest_weekday_local": "Mon",
    "longest_session_seconds": 0
  },
  "models": {
    "opus_pct": 0.0,
    "sonnet_pct": 0.0,
    "haiku_pct": 0.0
  },
  "cost_estimate_usd": null,
  "skipped_records": 0,
  "warnings": []
}
```

Every field present here MUST be present in the JSON output even when
the value is zero or empty — stable shape beats conditional keys for
downstream scripts.

## Error output shape

On user error (exit code 2), stderr contains a single line of the form:

```
Error: <short reason>. Try --help.
```

On internal error (exit code 1) with `--verbose`, the full traceback is
printed to stderr. Without `--verbose`, stderr shows only:

```
Error: something went wrong while reading <file>. Re-run with --verbose for details.
```

## Backwards-compatibility policy

- Adding a flag, subcommand, or JSON field: MINOR bump.
- Renaming or removing a flag, subcommand, or JSON field: MAJOR bump.
- Changing exit-code meaning: MAJOR bump.
- Changing wording of human-readable text: PATCH bump.
