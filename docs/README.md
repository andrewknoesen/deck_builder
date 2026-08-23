# deck_builder docs index

Also published as a hosted site via [mkdocs](https://www.mkdocs.org/) + Material
(`mkdocs.yml` at the repo root, deployed by `.github/workflows/docs.yml` on every push to `main`
that touches `docs/**`) — this file is that site's homepage either way, so reading it here or on
the hosted site is the same content.

This is the central entry point for every doc in this repo — agents and developers alike should
be able to find what they need starting here, without already knowing a file exists. If you add a
new persistent doc anywhere in the repo (`docs/*.md`, a new subdirectory `README.md`, a new
`.claude/agents/*.md`), link it from here as part of that phase's Concrete Steps — see
`CLAUDE.md`'s `## Documentation` section.

## Start here

1. **Read root [`CLAUDE.md`](https://github.com/andrewknoesen/deck_builder/blob/main/CLAUDE.md)
   first.** Agents already do this automatically (it's
   loaded into every session and subagent) — human developers should read it manually, since it
   holds the project overview, directory tree, dev setup, and key conventions that everything else
   here assumes.
2. **Then this page** for everything CLAUDE.md doesn't hold: architecture detail, subsystem design
   docs, and how decisions actually get made on this project.

## How this project makes decisions

`PLAN.md` is the live planning tool and single source of truth for project status — what's
shipped, what's in progress, what's deferred, and why. It is **not summarized here on purpose**:
`PLAN.md`'s own Status section explicitly refuses to characterize or summarize its own history,
because every attempt at that has itself introduced drift or overclaiming. Read `PLAN.md` directly
— start with its Status section at the top, then follow its pointer into
[`MEMORY.md`](https://github.com/andrewknoesen/deck_builder/blob/main/MEMORY.md) for the phase you
care about. `PLAN.md` deliberately stays lean (current summary + what's still actionable);
`MEMORY.md` holds the full per-phase history (Why/Ground truth/Design/Interview outcome/Concrete
steps/Shipped writeups) so `PLAN.md` doesn't have to.

The short version of the process, if you're about to start new work: anything crossing more than
one layer (backend+frontend, or a new backend subsystem) gets a design pass from `mtg-architect`
first, real open questions get resolved via a product-owner interview before any code is written,
and every shipped phase gets a "Shipped" writeup in `MEMORY.md` recording what actually happened
(including deviations from the plan) — not just a checkbox.

## Architecture and current API/data-model shape

- **[`ARCHITECTURE.md`](ARCHITECTURE.md)** — the real, current shape: layer overview, the full API
  table (every router/endpoint), auth status, and an explicit "what's not built yet" list kept
  current on purpose. Start here for "how does this actually work today."
- **[`backend/app/ai/README.md`](https://github.com/andrewknoesen/deck_builder/blob/main/backend/app/ai/README.md)**
  — the AI/agent layer in detail: directory structure, each agent, each tool, RAG modules,
  ingestion scripts, and the MCP server.
- **[`frontend/README.md`](https://github.com/andrewknoesen/deck_builder/blob/main/frontend/README.md)**
  / **[`backend/README.md`](https://github.com/andrewknoesen/deck_builder/blob/main/backend/README.md)**
  — per-package dev notes.

## Subsystem design docs

Each of these is a point-in-time design or audit document, not a live reference — check its status
banner before trusting its details over the actual code:

| Doc | Status |
|---|---|
| [`mcp_server.md`](mcp_server.md) | Current — matches the shipped Phase 9 implementation. |
| [`DECK_IMPORT_DESIGN.md`](DECK_IMPORT_DESIGN.md) | Implemented, with one noted refinement. |
| [`deck_statistics_spec.md`](deck_statistics_spec.md) | Implemented — treat as the math reference. |
| [`auth_specs.md`](auth_specs.md) | Not implemented — describes the intended design only. |
| [`design_rulings_agent.md`](design_rulings_agent.md) | Superseded — kept for historical context. |
| [`rules_ingestion_pipeline.md`](rules_ingestion_pipeline.md) | Directionally accurate, some details drifted. |
| [`rules_ingestion_guide.md`](rules_ingestion_guide.md) | Directionally accurate, some details drifted. |
| [`UI_DEGENERIC_DESIGN.md`](UI_DEGENERIC_DESIGN.md) | Fully implemented — all 4 findings fixed. |

## Exploring the codebase structurally

For "what connects to what" questions (god nodes, community structure, cross-file relationships),
use `graphify` rather than raw grepping — it returns a scoped subgraph, usually much smaller than
reading source directly:

- `graphify query "<question>"`, `graphify path "<A>" "<B>"`, `graphify explain "<concept>"` —
  the fastest way to answer a specific structural question.
- `graphify-out/wiki/index.md` (local path, not a link here — it's gitignored, regenerated
  locally, not checked into the repo or this hosted site) — a generated wiki (one article per
  detected community) for broad navigation, if you're exploring rather than asking a specific
  question. If it's missing, run `graphify update .` then `graphify export wiki`.
- [`graphify-out/GRAPH_REPORT.md`](https://github.com/andrewknoesen/deck_builder/blob/main/graphify-out/GRAPH_REPORT.md)
  — broad architecture review, for when query/path/explain don't surface enough context.
- After modifying code, run `graphify update .` to keep the graph current.

See `CLAUDE.md`'s `## graphify` section for the full rules.

## The subagent team

`.claude/agents/*.md` defines this project's specialist subagents (backend, frontend, AI, devops,
integrations, maths, QA, UX, EM, architect) — Claude dispatches to the right one(s) automatically.
See `CLAUDE.md`'s "Subagent roster" section for the current list and each agent's scope; see the
individual `.claude/agents/<name>.md` file for that agent's actual grounding and standards.

## Expanding this project

This is the actual answer to "how do I add something new here":

1. Read `PLAN.md`'s Status section to see what's already shipped, in progress, or deliberately
   deferred — don't duplicate or conflict with something already decided. Follow into `MEMORY.md`
   for the full reasoning behind any past decision that's relevant to what you're about to build.
2. If the change crosses more than one layer, or isn't obviously a one-file change, start with a
   design pass from `mtg-architect` (read-only — it hands off implementation, doesn't do it).
3. Resolve any real open questions via a product-owner interview before writing code — this
   project's convention is to decide ambiguity explicitly, not guess and hope.
4. Route implementation to the specialist(s) whose scope matches the change (see "The subagent
   team" above).
5. Once shipped: add a "Shipped" writeup to `MEMORY.md` (what was built, any deviation from the
   plan, how it was verified), a one-paragraph pointer to it in `PLAN.md`'s Status section, and
   link any new persistent doc file from this page.
