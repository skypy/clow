<!--
Sync Impact Report
==================
Version change: (unversioned template) → 1.0.0
Bump rationale: Initial ratification — template placeholders replaced with concrete principles.

Modified principles:
  - [PRINCIPLE_1_NAME] → Local-First, No Network
  - [PRINCIPLE_2_NAME] → CLI Text Protocol
  - [PRINCIPLE_3_NAME] → Graceful Schema Degradation
  - [PRINCIPLE_4_NAME] → Fixture-Driven Testing
  - [PRINCIPLE_5_NAME] → Simplicity (YAGNI)

Added sections:
  - Technical Constraints (previously [SECTION_2_NAME])
  - Development Workflow (previously [SECTION_3_NAME])

Removed sections: none

Templates requiring updates:
  - .specify/templates/plan-template.md — Constitution Check section references these gates (⚠ pending concrete wiring when `/speckit-plan` is next run)
  - .specify/templates/spec-template.md — no changes required (✅)
  - .specify/templates/tasks-template.md — no changes required (✅)

Follow-up TODOs: none
-->

# Claude Wrapped Constitution

## Core Principles

### I. Local-First, No Network
All processing MUST run on the user's machine against files they already own
(`~/.claude/projects/*.jsonl`, `~/.claude.json`, `~/.claude/todos/*.json`). The
tool MUST NOT emit telemetry, sync state to a server, or make outbound network
calls during normal operation. Rationale: conversation logs are sensitive — the
user is the sole audience and sole custodian.

### II. CLI Text Protocol
Every command MUST follow the UNIX text protocol: stdin/args in, stdout for
results, stderr for diagnostics. Human-readable output is the default; a
`--json` flag MUST produce machine-readable output for every command that emits
data. Exit codes MUST distinguish success (0), user error (2), and internal
error (1). Rationale: composability with shell pipelines and scripting is a
first-class use case.

### III. Graceful Schema Degradation
The Claude Code JSONL format is not a public API and can change between
releases. Parsers MUST skip unknown event types and tolerate missing optional
fields without crashing. Unrecognized or malformed records MUST be counted and
reported (via `--verbose` or a warning footer), never silently dropped.
Rationale: version drift is the single most likely failure mode in production.

### IV. Fixture-Driven Testing
Unit and integration tests MUST run against anonymized JSONL fixtures derived
from real Claude Code output, not hand-written mocks. Any new parser or
aggregator change MUST ship with a fixture that exercises the new behavior.
Per-session totals in tests MUST sum to the reported grand total.
Rationale: mock-based tests silently diverge from reality; fixtures preserve
the shape and edge cases of actual user data.

### V. Simplicity (YAGNI)
One pipx-installable binary. No config file, no daemon, no background cache, no
plugin system. Features MUST be listed in the current plan's Metrics section
before being implemented. New abstractions (base classes, registries, plugin
APIs) require explicit justification in the plan. Rationale: this is a
personal-scale tool; complexity added "just in case" is a net liability.

## Technical Constraints

- **Runtime**: Python 3.11+, installable via `pipx install claude-wrapped`.
- **Primary dependencies**: `click` (CLI), `rich` (rendering), `orjson`
  (JSONL parsing), `platformdirs` (path resolution). Additions require a
  line item in the plan.
- **Non-goals** (from plan.md): HTML/web output, cloud sync, multi-user
  accounts, real-time dashboards, editing local files.
- **Cost estimation**: off by default; rate tables documented in-repo and
  versioned alongside code.

## Development Workflow

- **Spec-driven**: every substantive change flows through `/speckit-specify`
  → `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`. Direct commits
  outside this flow are reserved for typo/tooling fixes.
- **Versioning**: MAJOR.MINOR.PATCH. Removing or renaming a CLI flag or
  subcommand is MAJOR. Adding a flag, subcommand, or metric is MINOR.
  Bug fixes and wording changes are PATCH.
- **Compliance review**: every PR description MUST state which principles
  the change touches and, for any that appear relaxed, provide justification
  that survives this constitution's next amendment cycle.

## Governance

This constitution supersedes ad-hoc conventions. Amendments MUST be proposed
via a PR that updates `.specify/memory/constitution.md`, bumps the version per
the rules in Principle V and the Versioning section above, and updates the
Sync Impact Report at the top of this file. Amendments take effect on merge.
All reviewers MUST verify compliance with the Core Principles before approving.
Complexity or deviations MUST be justified in the PR description, not in code
comments.

**Version**: 1.0.0 | **Ratified**: 2026-04-19 | **Last Amended**: 2026-04-19
