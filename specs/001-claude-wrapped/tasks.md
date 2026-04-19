# Tasks: Claude Wrapped

**Input**: Design documents in `specs/001-claude-wrapped/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Included. Constitution IV (Fixture-Driven Testing) makes
unit and integration tests against anonymized JSONL fixtures mandatory.

**Organization**: Grouped by user story so each is independently
deliverable. US1 alone is the MVP.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: Which user story this task belongs to (US1…US4)
- Paths assume the single-package layout from `plan.md`

## Path Conventions

- Source: `src/claude_wrapped/` at repo root
- Tests: `tests/` at repo root, with `tests/fixtures/`, `tests/unit/`, `tests/integration/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project scaffolding; no metric logic yet.

- [X] T001 Create package and test layout: `src/claude_wrapped/__init__.py`, `tests/__init__.py`, `tests/fixtures/`, `tests/unit/`, `tests/integration/`
- [X] T002 Initialize `pyproject.toml` with Python 3.11+, runtime deps `click`, `rich`, `orjson`, `platformdirs`; dev deps `pytest`, `pytest-cov`, `ruff`, `black`; declare `[project.scripts] claude-wrapped = "claude_wrapped.cli:main"`
- [X] T003 [P] Configure `ruff` + `black` in `pyproject.toml` (line length 88, target-version py311)
- [X] T004 [P] Add `pytest` configuration in `pyproject.toml` (testpaths=`["tests"]`, `--strict-markers`)
- [X] T005 [P] Create anonymized JSONL sample at `tests/fixtures/sample_session.jsonl` (≥1 user message, ≥1 assistant message with usage, ≥1 tool_use, ≥1 unknown event type for skip-coverage)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The data pipeline backbone — models, loader, parser. Every user story depends on these.

**⚠️ CRITICAL**: No user story phase may begin until this phase is green.

- [X] T006 Define dataclasses `Session`, `ToolCall`, `Project`, `Metric` per `data-model.md` in `src/claude_wrapped/models.py`
- [X] T007 Implement file discovery + line-streaming in `src/claude_wrapped/loader.py` (uses `platformdirs` to resolve `~/.claude/projects/`, reads `~/.claude.json` project registry, yields `(project_id, raw_record)` tuples via `orjson`)
- [X] T008 Implement event normalization in `src/claude_wrapped/parser.py` (maps raw JSONL records → `Session`/`ToolCall` instances, skips unknown `type` values while incrementing a `skipped_records` counter, clamps ToolCall timestamps to session window)
- [X] T009 [P] Skeleton click entrypoint in `src/claude_wrapped/cli.py` — just `--version`, `--help`, and the `main()` function registered in `pyproject.toml`
- [X] T010 [P] Unit tests for `loader.py` in `tests/unit/test_loader.py` (discovery finds the fixture, empty directory returns no records, zero-byte file is skipped not fatal)
- [X] T011 [P] Unit tests for `parser.py` in `tests/unit/test_parser.py` (normal record → typed instance, unknown `type` → skip + count, malformed JSON line → skip + count, timestamp outside session clamps and warns)

**Checkpoint**: Data pipeline is loaded and tested. User stories can now branch in parallel.

---

## Phase 3: User Story 1 — See yearly summary (Priority: P1) 🎯 MVP

**Goal**: A user runs `claude-wrapped` with no arguments and sees the full default report on their real data.

**Independent Test**: On the fixture dataset, `claude-wrapped` prints a report containing Totals, Top 5 Tools, Top 5 Projects, Top 5 Subagents, Busiest Hour/Weekday, Longest Session, and Model Mix. Every number in the report matches values derivable by hand from the fixture.

- [X] T012 [US1] Implement grand totals in `src/claude_wrapped/aggregator.py` (sessions, messages, tool_calls, tokens 4-way split, active days)
- [X] T013 [US1] Add Top-N helpers in `src/claude_wrapped/aggregator.py` (top-5 tools by `ToolCall.tool_name`, top-5 projects by session count, top-5 subagents by `ToolCall.subagent` where non-null)
- [X] T014 [US1] Add time-based metrics in `src/claude_wrapped/aggregator.py` (busiest hour and weekday in local TZ, longest session duration)
- [X] T015 [US1] Add model mix computation in `src/claude_wrapped/aggregator.py` (group by prefix → Opus/Sonnet/Haiku percentages)
- [X] T016 [US1] Implement static-report rendering in `src/claude_wrapped/renderer.py` using `rich.Table` and `rich.Panel` (one panel per metric group, totals header with window label, skipped-records footer)
- [X] T017 [US1] Wire default invocation in `src/claude_wrapped/cli.py` — current calendar year, read all projects, call aggregator, hand result to renderer, exit 0
- [X] T018 [P] [US1] Unit tests for aggregator in `tests/unit/test_aggregator.py` (invariant: sum of per-session `message_count` equals totals.messages; same for tool_calls; top-N stable ordering on ties)
- [X] T019 [P] [US1] Integration test in `tests/integration/test_default_report.py` — run CLI on fixture, capture stdout, assert expected totals and top-lists appear
- [X] T020 [P] [US1] Integration test in `tests/integration/test_no_data.py` — empty fixture directory, assert exit 0 and friendly message to stdout, no traceback on stderr

---

## Phase 4: User Story 2 — Drill into project or time window (Priority: P2)

**Goal**: User can scope the same report to one project or a custom date range.

**Independent Test**: Run `claude-wrapped --project foo` and `claude-wrapped --since 2026-01-01 --until 2026-03-31`; each narrows metrics to a subset of US1's grand totals.

- [X] T021 [US2] Add `--year`, `--since`, `--until`, `--project` options to `src/claude_wrapped/cli.py` with mutual exclusion between `--year` and the `--since`/`--until` pair
- [X] T022 [US2] Add `filter_window(sessions, since, until)` to `src/claude_wrapped/aggregator.py` (inclusive bounds; empty window returns no sessions without error)
- [X] T023 [US2] Add `filter_project(sessions, project_ref)` to `src/claude_wrapped/aggregator.py` (resolves `project_ref` against `Project.display_name` first, then `Project.id`)
- [X] T024 [P] [US2] Integration tests in `tests/integration/test_filters.py` (year filter matches a known subset, since/until filter matches a known subset, project filter matches a known subset, filter header appears in report output)

---

## Phase 5: User Story 3 — Story-mode slideshow (Priority: P3)

**Goal**: Animated, pacing-controlled slideshow presentation of the same metrics.

**Independent Test**: Invoke `claude-wrapped --story`; multiple screens advance sequentially; pressing a key exits cleanly; final screen's numbers match the static report.

- [X] T025 [US3] Implement slideshow presenter using `rich.live.Live` in `src/claude_wrapped/renderer.py` (slide sequence: title → totals → top tools → top projects → time → models → farewell; configurable dwell)
- [X] T026 [US3] Add `--story` flag to `src/claude_wrapped/cli.py` with mutual exclusion vs `--json`; on story exit, ensure terminal restore (no lingering cursor/color artifacts)
- [X] T027 [P] [US3] Integration test in `tests/integration/test_story_mode.py` — run with `--story` + auto-advance, capture final buffer, assert the last slide's numbers equal the `--json` output's totals

---

## Phase 6: User Story 4 — JSON export (Priority: P3)

**Goal**: Machine-readable output for piping into other tools.

**Independent Test**: Run `claude-wrapped --json`; pipe to `jq`; every field named in `contracts/cli.md` §`--json output schema (v1)` is present.

- [X] T028 [US4] Implement JSON serializer in `src/claude_wrapped/renderer.py` matching `contracts/cli.md` §`--json output schema (v1)` exactly (stable key order, zero/empty defaults for unused sections)
- [X] T029 [US4] Add `--json` flag to `src/claude_wrapped/cli.py` (suppresses all human rendering, writes JSON to stdout, keeps diagnostics on stderr)
- [X] T030 [P] [US4] Integration test in `tests/integration/test_json_export.py` — run with `--json`, parse stdout as JSON, assert every key from `contracts/cli.md` schema is present and numeric fields cross-check against the human report

---

## Phase 7: Polish & Cross-Cutting

**Purpose**: FR-010, FR-011, FR-014, exit codes, docs — everything that makes the tool production-quality without belonging to any single user story.

- [X] T031 [P] Implement `--cost` opt-in in `src/claude_wrapped/cli.py` and rate table in `src/claude_wrapped/pricing.py` (per-model input/output/cache rates, clearly labelled "approximate" in both human and JSON output)
- [X] T032 [P] Implement `--dry-run` in `src/claude_wrapped/cli.py` (print discovered file paths to stdout, exit 0 without touching aggregator/renderer)
- [X] T033 [P] Implement `--verbose` in `src/claude_wrapped/cli.py` (per-file skip counts to stderr, full traceback on internal errors)
- [X] T034 [P] Exit-code mapping per `contracts/cli.md` in `src/claude_wrapped/cli.py` (0 success, 1 internal, 2 user error); replace uncaught exceptions with a clean `click.UsageError`/`click.ClickException`
- [X] T035 [P] `tools` subcommand in `src/claude_wrapped/cli.py` delegating to a new `render_tools_heatmap()` in `src/claude_wrapped/renderer.py`
- [X] T036 [P] Schema-drift regression test in `tests/integration/test_schema_drift.py` — fixture with deliberately unknown event types; report must still complete and `skipped_records` count must be non-zero and surfaced
- [X] T037 [P] Narrow-terminal rendering check in `tests/integration/test_narrow_terminal.py` (force `COLUMNS=60`; no output line overflows; no crash)
- [X] T038 [P] Write `README.md` at repo root with install + quickstart content from `specs/001-claude-wrapped/quickstart.md`, plus a screenshot/asciicast placeholder

---

## Dependencies

```
Phase 1 (Setup)
   ↓
Phase 2 (Foundational: models + loader + parser)
   ↓
Phase 3 (US1)  ← MVP
   ↓
   ├── Phase 4 (US2: filters) — extends aggregator from US1
   ├── Phase 5 (US3: story)   — extends renderer from US1
   └── Phase 6 (US4: JSON)    — extends renderer from US1
   ↓
Phase 7 (Polish) — can start once Phase 3 is done; individual tasks parallel
```

- **US2, US3, US4 are independent of each other** — they each extend a different face of the core (aggregator, renderer, renderer respectively) but don't depend on each other's completion. A team could ship US1 and any subset of US2–US4 in any order.
- **Phase 7 tasks are independent of each other** and mostly independent of US2–US4. `--cost`, `--dry-run`, `--verbose`, exit-code hardening, `tools` subcommand, schema-drift test, narrow-terminal test, and README can each be a separate PR.

## Parallel opportunities

- **Within Phase 1**: T003, T004, T005 can run in parallel after T001/T002 create the files they configure.
- **Within Phase 2**: T009, T010, T011 can run in parallel once T006–T008 land (skeleton CLI and the two test files touch different files).
- **Within Phase 3 (US1)**: T018, T019, T020 can run in parallel after T012–T017 (all three tests write to different files).
- **Within Phase 4 (US2)**: T024 is independent of T021–T023 until those land.
- **Within Phase 7**: every task is marked `[P]` — eight parallel lanes.

## Implementation strategy

1. **Ship US1 as MVP** (Phases 1 + 2 + 3). At that point you have a functional `claude-wrapped` with real numbers on real data — enough to validate the entire architecture against your own history.
2. **Add US2** next because `--year`/`--project` filters are the highest-impact refinements and share the aggregator surface with US1.
3. **Add US4 (JSON export)** before US3 (story mode); JSON is a small-surface high-value addition that unblocks any scripting use case.
4. **Add US3 (story mode)** last of the user stories — it's pure polish.
5. **Fold Phase 7 in opportunistically** — pick up individual tasks between user stories rather than saving them all for the end.

## Format validation

All tasks above use the required `- [ ] [TaskID] [P?] [Story?] Description with file path` format. Setup, Foundational, and Polish phase tasks deliberately omit the `[Story]` label; Phases 3–6 tasks all carry their `[US#]` label. Every task names at least one concrete file path.
