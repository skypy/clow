# Phase 0 Research — Claude Wrapped

No `[NEEDS CLARIFICATION]` markers remain in Technical Context; research
below documents the decisions that closed them and the alternatives
evaluated.

## Decision: Python 3.11 + click + rich + orjson + platformdirs

**Rationale**:

- **Python 3.11+** — matches the language of the upstream Claude Code
  ecosystem's tooling, gives fast JSON via `orjson`, and `pipx` is the
  canonical single-user install story for Python CLIs.
- **click** — handles argument parsing, subcommands, option groups, and
  stdin/out conventions that Constitution II requires, with minimal
  boilerplate.
- **rich** — terminal tables, panels, and `rich.live` for the story-mode
  slideshow (FR-015). Handles narrow-terminal wrapping for free, which
  closes the narrow-terminal edge case.
- **orjson** — JSONL lines are small but numerous; `orjson` is
  consistently 2–5× faster than the stdlib `json` module on line-oriented
  loads, which keeps SC-001 (5s full-year report) achievable.
- **platformdirs** — resolves `~/.claude/` and `~/.claude.json` in a way
  that works across macOS and Linux without hardcoding paths.

**Alternatives considered**:

- **Rust / Go** — faster, but distribution to non-developer users is
  harder and the performance budget isn't tight enough to justify it.
- **argparse** (stdlib) — works, but click's declarative subcommand and
  option composition makes the CLI surface (10+ flags + subcommand) much
  cleaner.
- **textual** (richer TUI framework) — overkill for a report + optional
  slideshow; keeps surface area larger than Principle V allows.
- **stdlib json** — simpler but slower; fails SC-001 on large datasets.

## Decision: read-only access; no config file; no cache

**Rationale**: Constitution V (Simplicity/YAGNI) and FR-013 (no network)
together argue for zero persistent state. Reading files fresh on every
invocation avoids cache-invalidation bugs and makes the tool safe to
run at any time. Five seconds on a year of data is fast enough that a
cache is premature optimization.

**Alternatives considered**:

- **SQLite cache** — would speed up repeated runs, but invalidation is
  a whole class of bugs we'd own, and users run Wrapped rarely (once
  at year-end). Cost outweighs benefit.
- **YAML/TOML config file** — users would need to manage another file.
  CLI flags cover every documented option. Revisit only if we add
  options that need defaults-per-project.

## Decision: graceful-skip on unknown JSONL event types

**Rationale**: Constitution III is explicit about this. The Claude Code
JSONL format is not a public API — fields and event types have already
changed across releases. The tool reports skipped counts (FR-011) so
users can tell the difference between "no data" and "schema drift
dropped my data."

**Alternatives considered**:

- **Strict schema validation** — e.g., `pydantic` with `extra="forbid"`.
  Would catch drift early but hard-fail every user immediately after
  any upstream change. Hostile default for a personal tool.
- **Best-effort only, no report** — silent data loss violates FR-011
  and SC-002.

## Decision: cost estimation opt-in, rates in-repo

**Rationale**: Published token rates drift over time. Baking them into
a mandatory code path creates a silent-staleness bug (numbers look
authoritative but aren't). Opt-in with a visible "approximate" label
(FR-014) keeps the headline metrics trustworthy and pushes the caveat
onto the user who explicitly asked for the estimate.

**Alternatives considered**:

- **Live price lookup** — violates Constitution I (no network).
- **Always-on estimate** — invites angry bug reports whenever Anthropic
  changes pricing.
- **Omit cost entirely** — popular with some users; the opt-in compromise
  serves both camps.

## Decision: identify projects by stable path-derived ID, fall back to last-seen name from `~/.claude.json`

**Rationale**: Closes the "deleted/renamed project" edge case. A project's
on-disk path can disappear, but its normalized ID (derived once, stored
nowhere) remains stable across the dataset. `~/.claude.json` carries a
project registry that's our fallback source of truth for human-readable
display names.

**Alternatives considered**:

- **First-seen path as display name** — breaks when a project was
  renamed mid-year; the report would show the stale name.
- **Require project to exist on disk** — would erase history for any
  work in a repo the user has since deleted, which is exactly the
  history Wrapped is supposed to celebrate.

## Decision: local timezone for hour-of-day/weekday metrics; UTC for all other timestamps

**Rationale**: "Busiest hour" only makes sense to the user in their own
time. Everything else (session start/end, durations) is tz-agnostic once
the time-of-day metrics are computed, so we normalize to UTC at the
parser boundary and convert at the aggregator boundary only for the
hour/weekday rollups. Closes the non-UTC-clock edge case.

**Alternatives considered**:

- **Everything in UTC** — "busiest hour = 03:00" is unintuitive for a
  user whose local time that night was 19:00.
- **Everything in local** — DST transitions and users who change
  timezones mid-year produce off-by-one weirdness that's hard to
  explain.
