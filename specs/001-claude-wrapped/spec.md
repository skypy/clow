# Feature Specification: Claude Wrapped

**Feature Branch**: `001-claude-wrapped`
**Created**: 2026-04-19
**Status**: Draft
**Input**: User description: "Parse local Claude Code data → render a personal year-in-review in the terminal."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See my yearly summary at a glance (Priority: P1)

A Claude Code user runs a single command in their terminal and sees a
concise, visually rich summary of how they used Claude Code over the
past year: total sessions, messages, tools used, which projects and
models dominated their time, and when they worked. The output feels
like a celebration of their year, similar in spirit to a music-streaming
year-in-review.

**Why this priority**: This is the core value proposition — the reason
the tool exists. Without it, nothing else matters.

**Independent Test**: Run the tool with no flags on a machine that has
local Claude Code history. Verify it prints a single, complete report
containing totals, top tools, top projects, busiest day/hour, and
model mix, all derived from the user's real data.

**Acceptance Scenarios**:

1. **Given** a user with at least one Claude Code session in the current
   calendar year, **When** they run the tool with default options,
   **Then** a report displays totals, top 5 tools, top 5 projects,
   busiest hour and weekday, and model mix.
2. **Given** a user with no Claude Code history for the selected year,
   **When** they run the tool, **Then** they receive a friendly message
   explaining no data was found, not an error stack trace.
3. **Given** a user whose log files contain events the tool does not
   recognize, **When** they run the tool, **Then** the report still
   completes and a warning footer states how many records were skipped.

---

### User Story 2 - Drill into a single project or time window (Priority: P2)

A user wants the same summary narrowed to a specific project or date
range — e.g., "show me only my work in the `acme-api` repo," or
"just the first quarter."

**Why this priority**: Power-user refinement; valuable but non-essential
for the first usable release.

**Independent Test**: Run the tool with a project filter and a date
range on the same dataset and verify the numbers sum to a subset of the
full-year totals.

**Acceptance Scenarios**:

1. **Given** a user with sessions spanning multiple projects, **When**
   they pass a project filter, **Then** only sessions attributed to
   that project appear in the totals and top-lists.
2. **Given** a user who supplies a date window, **When** they run the
   tool, **Then** only sessions whose timestamps fall within the window
   are included, and the report header names the window.

---

### User Story 3 - Experience the year as a story (Priority: P3)

A user wants a slideshow-style presentation that walks through their
year one metric at a time, with pacing and polish, not a single static
page. They can watch it or skip between slides.

**Why this priority**: Delight feature; increases shareability but not
required for the utility of the tool.

**Independent Test**: Invoke the story mode flag and confirm the
terminal advances through multiple screens, each showing one metric,
and that the final screen matches the static report's key numbers.

**Acceptance Scenarios**:

1. **Given** the user passes the story-mode flag, **When** the tool
   runs, **Then** screens display sequentially and advance either
   automatically or on a key press.
2. **Given** the story is running, **When** the user presses a key to
   exit, **Then** the terminal returns to a clean prompt with no
   visual artifacts.

---

### User Story 4 - Export raw numbers for my own scripts (Priority: P3)

A user wants the same metrics in machine-readable form so they can
pipe the output into another tool, post it to Slack, or build their
own chart.

**Why this priority**: Unlocks composability with the wider shell
ecosystem; small effort once metrics are already computed.

**Independent Test**: Run the tool with the JSON output flag, parse
the result with any JSON tool, and confirm every number shown in the
human report is present as a field in the JSON.

**Acceptance Scenarios**:

1. **Given** the user passes the machine-readable output flag,
   **When** the tool runs, **Then** stdout contains a single valid
   JSON document and no human-formatted text.

---

### Edge Cases

- A project directory referenced in history has since been deleted or
  renamed — the tool must still attribute past sessions to a stable
  identifier rather than crashing on a missing path.
- Log files are empty, zero-byte, or truncated mid-record — skip the
  offending record, log a warning, continue processing.
- The user's terminal is very narrow (e.g., 60 columns) — the report
  must still be readable; wide tables wrap or truncate cleanly.
- Two sessions have identical timestamps — both must be counted; no
  silent deduplication.
- The user's system clock is in a non-UTC timezone — "busiest hour"
  and "busiest weekday" must reflect the user's local time, not UTC.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST discover all Claude Code log files
  belonging to the current user without requiring the user to pass
  any paths.
- **FR-002**: The system MUST parse session transcripts and extract,
  for each session: start timestamp, end timestamp, message count,
  tool-use count, tokens consumed per category (input, output, cache),
  model identifier, and associated project.
- **FR-003**: The system MUST aggregate per-session data into totals
  for: sessions, messages, tool calls, tokens (broken out by category),
  and active days.
- **FR-004**: The system MUST compute and display the top 5 most-used
  tools, top 5 most-active projects, and top 5 most-invoked subagents
  over the selected window.
- **FR-005**: The system MUST compute and display the busiest hour of
  day, busiest day of week, and longest single session.
- **FR-006**: The system MUST compute the percentage mix of each model
  family used (for example Opus / Sonnet / Haiku).
- **FR-007**: The system MUST default the reporting window to the
  current calendar year (Jan 1 → today) and MUST accept explicit
  alternative windows (year, since/until bounds).
- **FR-008**: The system MUST accept an optional filter that scopes
  the report to a single project.
- **FR-009**: The system MUST produce a machine-readable output mode
  (one structured document on stdout) in addition to the default
  human-readable mode.
- **FR-010**: The system MUST provide a "what would be scanned" mode
  that lists the files the tool would read without processing them,
  so users can audit the tool's footprint before running it for real.
- **FR-011**: The system MUST skip and count records whose schema is
  unrecognized, and MUST NOT abort processing on a single malformed
  record.
- **FR-012**: The system MUST exit with a clear, user-friendly
  message (not a stack trace) when no data is found for the selected
  window.
- **FR-013**: The system MUST NOT make outbound network calls during
  report generation.
- **FR-014**: The system MUST offer an opt-in cost estimate that
  multiplies token totals by a documented, in-repo rate table; the
  estimate MUST be clearly labeled as approximate.
- **FR-015**: The system MUST offer a slideshow presentation mode
  that displays metrics sequentially and can be exited cleanly at any
  time.

### Key Entities

- **Session**: A contiguous Claude Code conversation. Attributes:
  start time, end time, project, model, message count, tool-call
  count, token totals by category.
- **Tool Call**: A single invocation of a tool inside a session.
  Attributes: tool name, timestamp, owning session.
- **Project**: A workspace a session belongs to. Attributes: stable
  identifier, display name (best-known label), earliest and latest
  session dates.
- **Metric**: A single aggregated number presented in the report.
  Attributes: label, value, unit, optional rank within a group.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user who has used Claude Code during the target year
  sees a complete report within 5 seconds on a dataset representing
  one typical year of usage.
- **SC-002**: On a dataset containing at least one record the tool
  does not recognize, the report completes successfully and the skip
  count is reported to the user.
- **SC-003**: Every number visible in the human-readable report is
  also present, under a discoverable name, in the machine-readable
  output for the same invocation.
- **SC-004**: Per-session totals, when summed, equal the grand totals
  shown in the report — verified on the fixture test dataset.
- **SC-005**: On a fresh machine with no prior Claude Code data, the
  tool exits in under 1 second with a message the user understands
  and no error traceback.
- **SC-006**: The tool can be installed and produce its first report
  in under 2 minutes, starting from the install instruction in the
  README.

## Assumptions

- The user has already used Claude Code enough to have accumulated
  at least a few sessions; the tool is not responsible for generating
  synthetic data.
- Claude Code stores its conversation and project data in the
  user-owned locations documented by Claude Code itself; the tool
  reads those files in place and never writes to them.
- Timestamps in local log files are in a canonical, parseable format;
  the tool normalises them to the user's local timezone for
  hour-of-day and weekday calculations.
- The Claude Code log schema is not a stable public contract; the
  tool treats unknown fields as optional and unknown event types as
  skip-and-continue.
- Cost estimation is inherently approximate because published rates
  drift over time; this is a user-facing caveat, not a defect.
- The primary user is the owner of the machine; no multi-user account
  model, permissions system, or sharing flow is in scope for v1.
