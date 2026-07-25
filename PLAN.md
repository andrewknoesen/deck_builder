# Repo Cleanup Plan

Working guide from a 2026-07-08 audit of `feature/agent_factory` (built with `graphify`, git branch
diffs, and an actual `pytest` run — not just reading docs). Goal: fix what's actively broken or
misleading, clear out clutter, and decide the fate of unfinished scaffolding. Work top to bottom;
check items off as they land. Re-run the verification command for each item before checking it off.

---

## P0 — Actually broken

### [ ] Fix `pytest` collection failure
`cd backend && uv run pytest` — the command in `backend/README.md` and `CLAUDE.md` — currently
**fails at collection**, not just at runtime.

- **Cause**: `backend/scripts/test_agent_logging.py:9` does
  `from app.ai.agents.rules.rules_agent import RulesAgent`. That class was removed when
  `rules_agent.py` was refactored to export a bare ADK `Agent` instance named `rules_agent`
  instead of a `RulesAgent` class.
- **Also check**: `backend/scripts/test_rules_agent.py` for the same stale import pattern —
  didn't fully audit this one.
- **Fix options** (pick one):
  1. Update `test_agent_logging.py` (and `test_rules_agent.py` if affected) to use the current
     `rules_agent` instance instead of the old class.
  2. If these scripts are manual/debug scripts rather than real tests, move them out of
     `backend/scripts/` (or rename off the `test_*.py` pattern) so pytest doesn't try to collect
     them, and/or add `testpaths = ["app"]` under `[tool.pytest.ini_options]` in
     `backend/pyproject.toml` so collection is scoped intentionally instead of implicitly.
- **Verify**: `cd backend && uv run pytest` passes with no `--ignore` flag needed.

### [ ] Fill in missing AI env vars in `.env.example`
`backend/app/core/config.py` defines `GOOGLE_API_KEY`, `GOOGLE_PROJECT_ID`, `GOOGLE_LOCATION`,
`CHROMA_HOST`, `CHROMA_PORT`, `AI_MODEL_NAME` — none of these appear in `.env.example`. A fresh
clone following the example file gets a silently non-functional AI layer.

- **Fix**: add all six vars to `.env.example` with sane defaults/placeholders (mirroring the
  defaults already in `config.py` where non-secret, empty string for `GOOGLE_API_KEY`).
- **Verify**: diff the fields in `config.py`'s `Settings` class against `.env.example` — every
  field should have a line (or a documented reason it's intentionally omitted, e.g. it's
  optional and fine to default).

---

## P1 — Docs that actively mislead

### [ ] Rewrite `backend/app/ai/README.md`
Still describes the pre-ADK API: `agents/rules.py` with a `RulesAgent` class and a
`get_rules_agent()` factory function, and `rag/rules.py`'s usage sample similarly. Actual current
shape:
- `backend/app/ai/agents/rules/rules_agent.py` — module-level `rules_agent = Agent(...)` (ADK).
- `backend/app/ai/agents/core/base.py` — `BaseAgent`/`BaseTool` ABCs (currently unused — see P2).

Rewrite the "5. `agents/`" section (and check "4. `rag/`" for the same drift) to match actual
current imports and usage.

- **Verify**: every code sample/import path in the file actually works if pasted into a REPL
  (`uv run python -c "..."` from `backend/`).

### [ ] Delete and rewrite `docs/ARCHITECTURE.md` and `docs/AI_ARCHITECTURE.md`
Both are pre-implementation planning docs (checkbox task lists, dated Jan/Mar) describing things
that were never built as specified — a `DeckAdvisorAgent` with `search_cards`/`get_deck_stats`
tools, a chat widget UI, an `/ai/chat` deck-context endpoint. What actually exists is a single
rules-judge agent (`rules_agent`) with rules/glossary/ruling lookup tools. These docs will
actively misdirect anyone (including future-us) trying to understand current architecture.

- **Decision**: delete both, write one short `docs/ARCHITECTURE.md` reflecting what's actually
  built today (can mostly lift from CLAUDE.md's Architecture section + this repo's actual
  routes/models). No archive — the checkbox/planning-doc format isn't worth preserving.
- **Also audit** (not yet deep-checked, same stale dates, likely same problem):
  - `docs/DECK_IMPORT_DESIGN.md`
  - `docs/auth_specs.md`
  - `docs/deck_statistics_spec.md`
  - `docs/design_rulings_agent.md`
  - `docs/rules_ingestion_guide.md`
  - `docs/rules_ingestion_pipeline.md`

  For each: read it, compare against the actual current implementation (e.g. does
  `backend/app/services/stats.py` match `deck_statistics_spec.md`? does the real ingestion
  pipeline in `backend/app/ai/ingestion/` match `rules_ingestion_pipeline.md`?), then either
  update it or move/flag it as historical.

- **Verify**: `docs/` contains nothing that describes a component, endpoint, or class that
  doesn't exist in the current tree.

### [ ] Replace `frontend/README.md` boilerplate
Still the untouched default Vite template — no mention of this actually being the MTG Deck
Builder frontend, no dev instructions specific to this project.

- **Fix**: replace with a short project-specific README (dev server command, key dirs, where
  API base URL is configured), consistent in tone with `backend/README.md`.

### [ ] Update CLAUDE.md's frontend directory tree
Missing `frontend/src/context/`, `frontend/src/styles/`, `frontend/src/utils/`,
`frontend/src/assets/`, which all exist.

- **Verify**: `find frontend/src -maxdepth 1 -type d` matches what CLAUDE.md's tree diagram
  lists.

---

## P2 — Dead scaffolding: resolved

### [ ] Delete `BaseAgent`/`BaseTool` in `backend/app/ai/agents/core/base.py`
CLAUDE.md states "New agents extend `BaseAgent` from `core/base.py`" — but nothing in the
codebase imports or subclasses it (`grep -rn "agents.core\|BaseAgent\|BaseTool" backend/app`
only matches the definition file itself). The one real agent (`rules_agent`) is a plain ADK
`Agent` instance built in 29 lines: prompt + list of plain-function tools + `Agent(...)`.
`BaseTool` requires wrapping every tool in a class with a `context: ToolContext` and a `run()`
method — a heavier pattern that `tools/rules.py` already sidesteps entirely by using plain async
functions (per CLAUDE.md's own convention). The abstraction was never actually adopted.

- **Decision**: delete `core/base.py` and the `agents/core/` package, and remove the CLAUDE.md
  line claiming new agents extend `BaseAgent`. ADK's `Agent` class already handles the model
  loop, tool dispatch, and function-schema generation — the class-hierarchy abstraction doesn't
  match how ADK wants to be used and isn't earning its keep.
- **Revisit later, not now**: if a second/third agent lands and real duplication shows up (most
  likely candidate: repeating `model=settings.AI_MODEL_NAME` and similar boilerplate across
  `Agent(...)` calls), extract a thin **factory function** at that point — not a class hierarchy:
  ```python
  def make_agent(name: str, description: str, prompt: str, tools: list) -> Agent:
      return Agent(name=name, model=settings.AI_MODEL_NAME, description=description,
                   instruction=prompt, tools=tools)
  ```
  Don't build this until agent #2 actually exists and the duplication is real, not hypothetical.
- **Verify**: `grep -rn "agents.core\|BaseAgent\|BaseTool" backend/app` returns nothing;
  `uv run pytest` still passes (nothing depended on it).

---

## P3 — Housekeeping (low risk, mechanical)

### [ ] Delete fully-merged stale branches
Confirmed via `git log main..<branch>` (0 unique commits on all of these) and the same check
against `origin/main` — all fully merged, safe to delete both locally and on `origin`:

- `feature/deck_card_count_limit`
- `feature/deck_import`
- `feature/init`
- `feature/rules_agent`
- `feature/ui`
- `feature/ui-landing-page`
- `feature/google_adk_rules_agent`

**Decision**: delete both local and remote (confirmed) — all seven are fully merged with 0
unique commits on both `main` and `origin/main`.

```bash
# local
git branch -d feature/deck_card_count_limit feature/deck_import feature/init \
  feature/rules_agent feature/ui feature/ui-landing-page feature/google_adk_rules_agent

# remote
git push origin --delete feature/deck_card_count_limit feature/deck_import feature/init \
  feature/rules_agent feature/ui feature/ui-landing-page feature/google_adk_rules_agent
```

- **Verify**: `git branch -a` only shows `main` and active work branches.

### [ ] Stop committing `graphify-out/` generated artifacts
`graphify-out/graph.json` (~608KB, ~19.5k lines) and `graphify-out/graph.html` (~594KB) are
tracked in git. Both regenerate via `graphify update .` and will drift on every code change,
bloating diffs and clone size for no lasting benefit.

- **Fix**: add `graphify-out/graph.json`, `graphify-out/graph.html`, and `graphify-out/manifest.json`
  to `.gitignore` (keep `GRAPH_REPORT.md` tracked if you want the summary reviewable in PRs —
  it's small and human-readable). Then `git rm --cached` the generated files.
- **Verify**: `git status` after running `graphify update .` shows no diff in the newly-ignored
  files.

### [ ] Remove `references/` from git tracking
`references/MagicCompRules 20260116.txt` (954KB) and
`references/Screenshot 2026-01-18 at 21.33.24.png` (2.7MB) are committed. For a repo headed
toward public SaaS, permanently carrying a 2.7MB screenshot and a large rules dump in git
history isn't worth it.

- **Decision**: remove from git tracking.
- **Fix**:
  1. `git rm --cached "references/MagicCompRules 20260116.txt" "references/Screenshot 2026-01-18 at 21.33.24.png"`
     (leave `deck_import.txt` if it's small/genuinely useful notes — re-check its size/content;
     otherwise remove it too).
  2. Add `references/` (or the specific large files) to `.gitignore`.
  3. Document in `README.md` or `docs/rules_ingestion_pipeline.md` how to (re)fetch the
     comprehensive rules text — it's a real ingestion input, just shouldn't live in git history.
     Check whether `backend/app/ai/ingestion/rules_ingestion.py` already downloads this from a
     URL at runtime; if so, the checked-in copy may be fully redundant.
- **Note**: removing from tracking doesn't purge existing git history/blob size — that would
  need a history rewrite (`git filter-repo` or similar), which is a separate, more invasive step
  worth doing only if repo size actually becomes a problem. Not in scope for this pass.

### [ ] Clean up loose root-level clutter
- `test.db` — untracked, already gitignored via `*.db`, harmless but sitting on disk. Safe to
  `rm` locally.
- `backups/` — empty directory. Either start using it or remove it; an empty dir with no
  `.gitkeep` isn't tracked anyway.

---

## Suggested order of attack

All open decisions are now resolved (see below) — the whole list is mechanical execution at this
point.

1. P0 items first — they're actively broken and cheap to fix (couple hours combined).
2. P3 branch deletion, `graphify-out/` gitignore, `references/` untracking — mechanical, do
   anytime.
3. P2 (`BaseAgent`/`BaseTool` deletion) — mechanical now that it's decided; do alongside P3.
4. P1 doc rewrites last — write them to describe the *fixed* state (post P0/P2 cleanup), not a
   moving target.

## Decisions log

- **Agent abstraction**: delete `core/base.py` now; ADK's `Agent` already minimizes boilerplate
  for a single agent. Revisit with a thin factory *function* (not a class hierarchy) once a
  second agent exists and real duplication appears.
- **`docs/ARCHITECTURE.md` / `AI_ARCHITECTURE.md`**: delete and rewrite fresh, no archiving.
- **`references/`**: remove from git tracking, gitignore, document how to re-fetch.
- **Stale branches**: delete both local and remote for all seven confirmed-merged branches.
- **uv workspace**: collapsed. See below — root `pyproject.toml` was a single-member uv
  workspace with no reason to exist as one; it caused a real, reproducible bug, not just clutter.

---

## P4 — Collapse the single-member uv workspace (found mid-cleanup, not in original scope)

While verifying the P0/P3 fixes, `uv sync`/`uv run pytest` on the host repeatedly failed with
`error: failed to remove directory '.venv/lib': Directory not empty` and the venv's Python
symlink kept flipping between a macOS interpreter and a **Linux** one
(`/python/cpython-3.13.9-linux-aarch64-gnu/...`). Root cause, confirmed via `lsof` + `docker
logs`:

- Root `pyproject.toml` declared a uv **workspace** (`[tool.uv.workspace] members = ["backend"]`)
  with exactly one member. Workspaces put `.venv`/`uv.lock` at the workspace *root*, not per
  member — so `cd backend && uv sync` was silently managing a venv one directory above where you
  ran the command.
- `docker-compose.yml`'s `backend` service mounted the **entire repo root** (`.:/app`) instead of
  just `./backend:/app` — required because `uv run` from `/app/backend` needed to see the
  workspace root's `pyproject.toml`/`uv.lock` to resolve anything.
- That means the container's `/app/.venv` *was* the host's `.venv` — same directory, live, via
  the bind mount. The container runs `--reload` (watches the whole `/app` tree, including
  `.venv`) and its startup command re-runs `uv sync`. Any host-side `uv sync` and the container's
  own `uv sync` were writing into the same directory from two different OSes at the same time —
  hence the churn and the Linux/macOS symlink flapping.
- Confirming this wasn't just Docker-adjacent noise: the root `pyproject.toml`'s
  `[project.dependencies]` list (`aiosqlite`, `alembic`, `google-adk`, `greenlet`, `httpx`,
  `pydantic-settings`, `ruff`, `sqlmodel`) was **100% duplicated** in `backend/pyproject.toml` —
  there's no code at the repo root that could ever import them. Almost certainly `uv add X` run
  from the repo root by mistake at some point. A one-member workspace makes that mistake easy and
  gives none of the workspace's actual benefit (sharing code across multiple local packages —
  there is no second Python package; `frontend/` is npm, not part of this workspace at all).

### [x] Strip root `pyproject.toml` to editor-only config
Removed `[project]`, dependencies, and `[tool.uv.workspace]`. Kept only `[tool.pyright]` /
`[tool.mypy]` (`extraPaths`/`mypy_path = ["backend"]`) so editors opened at the repo root still
resolve `backend`'s modules — this doesn't require a uv project, just a `pyproject.toml` with
tool sections. Root `uv.lock` and root `.dockerignore` removed (the latter is dead — nothing
builds from root context anymore).

### [x] Make `backend/` a fully standalone uv project
`backend/pyproject.toml` needed no changes (it never declared the workspace membership — the
root did). Ran `cd backend && uv lock && uv sync` to generate `backend/uv.lock` and
`backend/.venv`. Verified standalone: `uv run pytest` (27 passed) and `uv run ruff check .` (all
checks passed) from `backend/` alone, no root `pyproject.toml`/`uv.lock` involved.

### [x] Rewrite `backend/Dockerfile` and `docker-compose.yml` for a scoped build context
- `docker-compose.yml`: backend service now builds with `context: ./backend` (not `.`),
  `working_dir: /app`, `volumes: [./backend:/app, /app/.venv]`. The `/app/.venv` anonymous volume
  shadows the bind mount at that path only — the container gets its own private venv, source
  stays hot-reloadable. Applied the same fix to `frontend` (`/app/node_modules`) since it has the
  identical exposure (`./frontend:/app` bind mount + `npm install` on every container start).
- `backend/Dockerfile`: dropped `--package=mtg-deck-builder-backend` (workspace-only flag, no
  longer applicable), `COPY . .` instead of `COPY backend ./backend` (context is already
  `backend/`). This also resolved a comment in the old Dockerfile flagging uncertainty about
  whether `WORKDIR` should be `/app` or `/app/backend` — with the scoped context, `/app` *is*
  the backend root, unambiguously.
- Added `backend/.dockerignore` (Docker's default lookup is `<context>/.dockerignore`, so the
  root one stopped applying the moment the context changed).

### [x] Consolidate duplicate `.env.example`
Found `backend/.env.example` (the one `docker-compose.yml`'s `env_file: backend/.env` and
`config.py`'s `env_file=".env"` actually read) had silently diverged from the root
`.env.example` — missing `PROJECT_NAME`, `SCRYFALL_BASE_URL`, `CHROMA_HOST`/`CHROMA_PORT`, and a
stale `AI_MODEL_NAME=gemini-2.0-flash-exp` default (real default is `gemini-2.5-flash`). Same
class of bug as the workspace: two copies of something that should have one source of truth.
Consolidated into `backend/.env.example`, deleted the root copy.

### [x] Fix `bin/dev.sh`
Used workspace-only flags (`uv sync --all-groups --all-packages`, `cd backend && uv lock
--frozen`). Simplified to `(cd backend && uv sync)`.

- **Verify**: `docker compose build backend` succeeds; `docker compose up -d backend` reports
  `healthy`; `cd backend && uv run pytest` and `uv run ruff check .` pass standalone from a fresh
  clone with no root-level Python config involved.
