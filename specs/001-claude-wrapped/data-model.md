# Phase 1 Data Model — Claude Wrapped

All entities are in-memory Python dataclasses populated by `parser.py`
and consumed by `aggregator.py` and `renderer.py`. No persistence layer.

## Entity: `Session`

A contiguous Claude Code conversation.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `id` | `str` | JSONL file stem | Stable, unique per conversation. |
| `project_id` | `str` | derived from parent path | Joins to `Project.id`. |
| `started_at` | `datetime` (UTC) | first message timestamp | Required. |
| `ended_at` | `datetime` (UTC) | last message timestamp | Required. |
| `message_count` | `int` | count of `type=message` records | ≥ 0. |
| `tool_call_count` | `int` | count of `type=tool_use` records | ≥ 0. |
| `tool_calls` | `list[ToolCall]` | each `tool_use` record | Ordered by time. |
| `tokens_input` | `int` | sum of `usage.input_tokens` | ≥ 0. |
| `tokens_output` | `int` | sum of `usage.output_tokens` | ≥ 0. |
| `tokens_cache_read` | `int` | sum of `usage.cache_read_input_tokens` | ≥ 0. |
| `tokens_cache_create` | `int` | sum of `usage.cache_creation_input_tokens` | ≥ 0. |
| `model` | `str` | model id on assistant messages | Most-recent non-null wins if mixed. |

**Validation**: `started_at ≤ ended_at`; `message_count` and
`tool_call_count` must match the lengths of the underlying event
streams.

**State transitions**: none — a Session is fully built before it leaves
the parser.

## Entity: `ToolCall`

A single invocation of a tool inside a session.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `session_id` | `str` | parent Session | FK. |
| `tool_name` | `str` | `name` field on `tool_use` record | Required. |
| `timestamp` | `datetime` (UTC) | record timestamp | Required. |
| `subagent` | `str \| None` | present only for Task/Agent invocations | Powers the "top subagents" metric. |

**Validation**: `tool_name` non-empty. `timestamp` within parent
session's [`started_at`, `ended_at`] window — if outside, the aggregator
clamps to the session window and emits a warning (counted toward the
skip total).

## Entity: `Project`

A workspace a session belongs to.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `id` | `str` | normalized path (slashes → dashes) | Stable across renames. |
| `display_name` | `str` | `~/.claude.json` projects map, else basename | Fallback handles deleted paths. |
| `first_seen` | `datetime` (UTC) | earliest session in selected window | Populated by aggregator. |
| `last_seen` | `datetime` (UTC) | latest session in selected window | Populated by aggregator. |
| `session_count` | `int` | derived | ≥ 1 (unless filtered). |

**Validation**: `first_seen ≤ last_seen`.

## Entity: `Metric`

A single aggregated number presented in the report.

| Field | Type | Notes |
|-------|------|-------|
| `label` | `str` | Human-readable name ("Total sessions"). |
| `value` | `int \| float \| str` | Numeric or formatted. |
| `unit` | `str \| None` | "sessions", "tokens", "USD", etc. |
| `rank` | `int \| None` | Position within a top-N group (None for scalars). |
| `group` | `str \| None` | "totals", "top_tools", "top_projects", etc. |

**Validation**: `rank` is only set when `group` denotes a ranked list.
`unit` is required for numeric values so the JSON export
(`--json`/FR-009) is self-describing.

## Relationships

```
Project 1 ──< many Session 1 ──< many ToolCall
                     │
                     └──< 0..n tokens_* counters (scalar fields)
```

- A Session belongs to exactly one Project (by `project_id`).
- A ToolCall belongs to exactly one Session (by `session_id`).
- Metrics have no persistent relation to the raw entities — they're
  computed from them and then rendered.

## Computed metrics (derived, not stored)

- **Totals**: sessions, messages, tool calls, tokens (4 categories),
  active days.
- **Top 5**: tools (by `ToolCall` count), projects (by `Session` count),
  subagents (by `ToolCall.subagent` count where non-null).
- **Time**: busiest hour (mode of `Session.started_at` hour in local TZ),
  busiest weekday (mode of local weekday), longest session (max
  `ended_at − started_at`).
- **Models**: percentage mix of `Session.model` rolled into
  Opus/Sonnet/Haiku families by prefix match.
- **Cost** (opt-in): per-category tokens × `pricing.py` table, summed.

## Invariants (enforced in tests; Constitution IV)

1. `sum(session.message_count for session in sessions) == totals.messages`.
2. `sum(session.tool_call_count for session in sessions) == totals.tool_calls`.
3. Every `ToolCall.timestamp` falls inside its session's window (after
   the clamp logic described on `ToolCall`).
4. The JSON export contains a key for every number visible in the
   human report (SC-003).
