# Implementation Plan: Claude Wrapped

**Branch**: `001-claude-wrapped` | **Date**: 2026-04-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-claude-wrapped/spec.md`

## Summary

Parse locally stored Claude Code data (`~/.claude/projects/*.jsonl`,
`~/.claude.json`, `~/.claude/todos/*.json`) and render a personal
year-in-review in the terminal. v1 ships a static report plus optional
slideshow and JSON export modes, all on-disk, no network.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `click` (CLI), `rich` (rendering + live slides),
`orjson` (fast JSONL parsing), `platformdirs` (resolve Claude data paths)
**Storage**: Read-only access to user's local Claude Code JSONL files and
`~/.claude.json`. No persistence of its own.
**Testing**: `pytest` with anonymized JSONL fixtures derived from real
Claude Code output (per Constitution IV)
**Target Platform**: macOS + Linux terminals; installable via `pipx`
**Project Type**: Single-package CLI tool
**Performance Goals**: Full-year report in ≤5s on one year of typical
usage (SC-001). Graceful on narrow terminals (≥60 cols).
**Constraints**: No outbound network calls (Constitution I). No config
files, no daemon, no cache (Constitution V). Unknown JSONL events must
be skipped and counted, not fatal (Constitution III).
**Scale/Scope**: Personal-scale. A year of heavy use is O(10k) sessions,
O(100k) messages, O(10M) JSONL lines across dozens of project files.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against `.specify/memory/constitution.md` v1.0.0:

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Local-First, No Network | ✅ PASS | FR-013 forbids outbound calls. Cost estimate uses an in-repo rate table, not a remote lookup. |
| II. CLI Text Protocol | ✅ PASS | FR-009 mandates machine-readable output alongside human output. `click` gives stdin/args → stdout, errors → stderr for free. |
| III. Graceful Schema Degradation | ✅ PASS | FR-011 requires skip-and-count on unknown records; edge cases enumerate empty, truncated, and malformed files. |
| IV. Fixture-Driven Testing | ✅ PASS | Testing plan uses anonymized real JSONL fixtures; SC-004 validates per-session totals sum to grand totals. |
| V. Simplicity (YAGNI) | ✅ PASS | Single pipx binary; no config file, no plugin system. Subagents listed as a metric, not as a plugin surface. |

**Gates**: All pass. No Complexity Tracking entries required.

## Project Structure

### Documentation (this feature)

```text
specs/001-claude-wrapped/
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output — CLI command schema
│   └── cli.md
└── tasks.md             # Phase 2 output (/speckit-tasks; NOT created here)
```

### Source Code (repository root)

```text
src/claude_wrapped/
├── __init__.py
├── cli.py           # click entrypoint + subcommands
├── loader.py        # discover + stream JSONL files
├── parser.py        # normalize JSONL events into typed records
├── aggregator.py    # compute metrics over normalized records
├── renderer.py      # rich tables/panels + story-mode live view
├── models.py        # Session, ToolCall, Metric, Project dataclasses
└── pricing.py       # per-model token rates (opt-in cost mode)

tests/
├── fixtures/        # anonymized JSONL snippets
├── unit/            # parser, aggregator, pricing
└── integration/     # cli end-to-end on fixture data

pyproject.toml       # pipx install claude-wrapped
README.md            # install + quickstart
```

**Structure Decision**: Single-package layout (Option 1). No backend/frontend
split; this is a terminal tool. Module boundaries mirror the data-flow
pipeline: `loader → parser → aggregator → renderer`, with `models.py`
shared and `pricing.py` an orthogonal opt-in add-on.

## Complexity Tracking

> No constitution violations; table intentionally omitted.
