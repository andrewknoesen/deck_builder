# deck_builder — Plan

## Status

**Phase 0 (repo cleanup) — done, 2026-07-08.** Fixed a broken test suite, stale/misleading docs,
dead scaffolding, and a real structural bug (a single-member uv workspace that put the host and
Docker's backend container in a file-system race over the same `.venv`). See the archive at the
bottom of this file for the full record, or `git log` — it landed as 9 commits on
`feature/agent_factory`, most recently `refactor: collapse single-member uv workspace`.

**Phase 2 (Deck Import) — done, 2026-07-08.** Built ahead of Phase 1 (AI advisor) — goldfishing
(Phase 3) needs decks easily importable to test against, and there was no reason to block that on
the advisor shipping first. `POST /decks/import` + `DeckImportModal`, best-effort resolution with
an inline search-to-replace path for unresolved cards. See Phase 2 below for the full record.

**Phase 1 (AI Deck Advisor) — not started, up next.** Feature completeness chosen over
production-readiness (auth/CI/deploy explicitly deferred, see "Deferred" below). Detailed below.

**Every phase gets an interview before implementation** — a short round of clarifying questions
on the genuinely open design decisions, resolved and recorded before any code is written. Applied
to Phase 2 already; apply to Phase 1 and Phase 3 the same way when they're picked up.

---

## Phase 1 — AI Deck Advisor

### Why this one, and why now

`POST /api/v1/ai/suggest` is currently a placeholder (`backend/app/api/routes/ai.py:18-23`) that
returns `{"message": "AI suggestion placeholder", "query": request.query}`. The only real agent
in the codebase is `rules_agent` — a rules-lookup judge, not a deck advisor. Frontend evidence
this was already anticipated and stalled: `AgentChat.tsx:52` has `context_cards: [], // Can be
populated later`.

This is also the natural point to revisit the agent-abstraction decision from Phase 0. When
`core/base.py` (`BaseAgent`/`BaseTool`) was deleted, the call was: ADK's `Agent` class already
minimizes boilerplate for *one* agent, and a shared factory function should wait until a second
agent exists and shows real duplication. This feature adds that second agent — the plan below
includes checking that assumption for real, not just building the feature.

### Ground truth this plan is built on

Checked before writing anything below, so this reflects actual code shapes, not invented ones:

- `backend/app/services/scryfall.py`'s `ScryfallService` already has `search_cards(query)`,
  `get_card_by_id(id)`, `get_cards_by_ids(ids)`, `get_card_rulings(id)` — all async, all it takes
  to build a card-search tool.
- `backend/app/services/stats.py`'s `calculate_stats(deck: Deck) -> Dict` already computes mana
  curve, color pips/sources (Karsten's heuristic), and draw odds — exactly what a deck advisor
  needs as context, already built for the `/decks/{id}/stats` endpoint.
- `backend/app/schemas/ai.py` has `ChatRequest.context_cards: Optional[List[str]] = []` — the
  wiring for deck-context chat already exists in the schema, just unused. `ai.py`'s
  `SuggestCardRequest` has `deck_context: List[str]` and `query: str`.
- Legality is **not** a separate backend concept — Scryfall's card objects carry a `legalities`
  dict directly (confirmed via `test_legalities.py`'s mocks), matching the repo's "Card data =
  Scryfall only" convention. No new legality service needed.
- **No tool in this codebase is DB-aware.** `query_comprehensive_rules`, `lookup_glossary_term`,
  `lookup_card_rulings` all hit Chroma/Scryfall directly, stateless, no request-scoped
  dependency injection exists for ADK tools anywhere. This matters for the design decision below.
- The real invocation pattern (`backend/app/api/routes/ai.py:26-46`, already working for `/chat`):
  `InMemoryRunner(agent=...)` → `create_session` → `run_async` → read `event.content.parts[0].text`
  off the final event.
- `test_ai_suggest` (`backend/app/tests/api/routes/test_ai.py`) currently only asserts the
  placeholder shape (`"message" in response.json()`) — it will need to become a real behavioral
  test, not just get updated in place.

### Key design decision: tools stay stateless, deck context goes in the prompt

Two ways to give the agent deck awareness:

1. **Request-scoped DB-aware tool** (e.g. `get_deck_stats(deck_id)` that opens its own DB
   session) — more flexible (agent decides when to look things up), but this pattern doesn't
   exist anywhere in the codebase yet and would be new infrastructure to design and get right.
2. **Pre-compute, pass as context** — the API route fetches the `Deck` (same ownership check
   `decks.py` already does via `get_current_user`), calls the existing `calculate_stats`, and
   folds the deck list + stats into the initial message sent to the agent. The agent gets one new
   *stateless* tool (`search_cards`) for looking up candidate cards, matching every existing tool.

**Decision: option 2.** It reuses `calculate_stats` outright, keeps `tools/` consistent with the
existing plain-function convention, and doesn't invent DB-aware-tool infrastructure for a single
call site. Revisit only if a later feature genuinely needs the agent to fetch arbitrary decks
mid-conversation (not needed for "suggest cards for the deck I'm looking at").

### Concrete steps

1. **`backend/app/ai/tools/cards.py`** (new) — `async def search_cards(query: str, format:
   str | None = None) -> str`, mirroring `tools/scryfall.py`'s existing pattern (own
   `httpx.AsyncClient` + `ScryfallService` per call, since ADK tools have no DI). Returns
   formatted results: name, mana cost, type line, oracle text snippet, and — if `format` given —
   `legalities[format]`, so the agent can self-filter instead of the tool doing it.

2. **`backend/app/ai/agents/deck_advisor/deck_advisor_agent.py`** (new) — plain ADK `Agent`
   instance, same shape as `rules_agent.py`. Prompt instructs it to: suggest additions/cuts with
   reasoning, cite only cards returned by `search_cards` (never invent a name/cost — same
   discipline as `rules_agent`'s "never rely on internal memory for rule numbers"), reference the
   mana curve/color stats given in context, and respect the deck's format legality.
   - **While writing this**: check whether `model=settings.AI_MODEL_NAME` (and any other
     boilerplate) is now duplicated between `rules_agent.py` and this file. If it is, extract the
     thin factory function sketched in the Phase 0 decision log (`make_agent(name, description,
     prompt, tools)`) — this is the actual trigger condition that was deferred, don't skip
     re-checking it just because the feature works without it.

3. **Extend the request schema.** `SuggestCardRequest` needs a `deck_id: int` (or reuse
   `ChatRequest`'s existing but unused `context_cards`/add `deck_id` there too — decide once
   writing the route which schema this should actually live under; `/suggest` is the more
   semantically correct endpoint name for this feature than repurposing `/chat`).

4. **Update `backend/app/api/routes/ai.py`'s `/suggest` handler**: fetch the `Deck` (ownership
   check like `decks.py:151` `GET /{deck_id}`), call `calculate_stats`, build a context string,
   invoke `deck_advisor_agent` via `InMemoryRunner` — same pattern already working in `/chat`,
   don't invent a new invocation style.

5. **Tests**: replace `test_ai_suggest`'s placeholder assertion with real coverage — mock
   Scryfall the same way `test_stats.py`/`test_legalities.py` already do (`AsyncMock` on
   `get_scryfall_service`), and mock `InMemoryRunner.run_async` the same way `test_ai_chat`
   already does. Cover: suggestion respects format legality, cites a real card from the mocked
   search result (not a hallucinated one), handles a deck the requesting user doesn't own (403,
   matching `decks.py`'s existing pattern).

6. **Frontend**: `AgentChat.tsx`'s `context_cards: []` stub needs real deck context threaded in —
   check whether this page should gain a "which deck" selector, or whether the natural home is
   actually inside `DeckBuilder.tsx` (advisor scoped to the deck you're already editing, which
   avoids needing a deck picker at all). Decide this by looking at `DeckBuilder.tsx`'s existing
   layout before building UI — don't assume `AgentChat.tsx` is the right page.

### Verify

- `cd backend && uv run pytest` covers the new behavior, not just the placeholder.
- Manually drive it in the browser per this repo's own convention (CLAUDE.md: "verify in the
  browser before calling work done") — add a card via search, confirm the suggestion is a real
  Scryfall card, confirm it respects the deck's format.
- `docs/ARCHITECTURE.md`'s "What's not built yet" section currently lists this exact gap —
  update it once this ships, so that doc doesn't silently go stale the way its predecessor did.

---

## Phase 2 — Deck Import (done, 2026-07-08)

`docs/DECK_IMPORT_DESIGN.md` already had a full design (MTGA/simple text paste, regex-based
parsing, Scryfall resolution by set+collector-number or fuzzy name) — marked "not implemented"
during Phase 0's doc audit. No AI involved; straightforward parsing + Scryfall resolution + a
frontend modal.

### Interview outcome (decided before writing code, per-phase process going forward)

The design doc left its own transactionality question open ("Best Effort"? — marked with a
question mark). Resolved:

1. **Partial failures: best-effort, with a replace path** — the deck is created with everything
   that resolves; lines that don't resolve (typo, not found, ambiguous) are reported as warnings,
   *and* each warning gets an inline "search for a replacement" affordance rather than just being
   silently listed.
2. **No new reconciliation screen** — that "search for a replacement" affordance reuses
   `DeckBuilderSearch.tsx` (already takes a simple `onAddCard: (card: ScryfallCard) => void`
   prop), rendered per failed line. This satisfies both "best-effort with replacement" and
   "plain warning list, not a whole new UI" at once — no new search/picker component needed.
3. **Entry point: `DeckList.tsx` only**, matching the design doc exactly — an "Import Deck"
   button opening a paste-text modal. Not also adding an entry point in `DeckBuilder.tsx` for v1.

### Ground truth this plan is built on

- `backend/app/api/routes/decks.py`'s existing `POST /` (`create_deck`) already does 90% of what
  import needs downstream of parsing: it calls a local helper `sync_cards(db, card_ids,
  scryfall)` (`decks.py:24`) to ensure resolved Scryfall IDs exist in the local `Card` table,
  builds `Deck`/`DeckCard` rows, and returns a `DeckPublic`. The import endpoint's job is
  specifically: parse text → resolve names to Scryfall IDs → then do what `create_deck` already
  does. Reuse `sync_cards` directly rather than re-implementing card persistence.
- `DeckCard`'s `board` field already supports `"main" | "side" | "maybe" | "commander"`
  (`backend/app/models/deck.py:8`) — the design doc's `Deck`/`Commander`/`Sideboard` header
  parsing maps directly onto this, no model changes needed.
- `references/deck_import.txt` (gitignored-large-files pass didn't remove this one — it's small,
  useful) has a real sample decklist in the MTGA-ish format to test the parser against.

### Concrete steps

1. **Re-read `docs/DECK_IMPORT_DESIGN.md` in full before coding** — it predates everything else
   in this plan and has the actual regex/parsing-state-machine design (zone-header switching,
   `^(\d+)\s+(.+?)(?:\s+\((\w+)\)\s+(\d+))?\s*$` pattern for qty/name/set/collector-number).
2. **Backend**: new `backend/app/schemas/deck_import.py` (`DeckImportRequest {text: str, name:
   str | None}`, `DeckImportResponse {id, name, missing_cards: List[str]}`); parsing logic in a
   new `backend/app/services/deck_import.py` (keep it out of the route file, matching how
   `stats.py`/`scryfall.py` are separate services, not inline in routes); new
   `POST /decks/import` in `decks.py` wired to `get_current_user` ownership like every other
   deck route.
3. **Resolution**: set+collector-number lines resolve via a specific-printing Scryfall lookup;
   name-only lines via Scryfall's named-fuzzy search. Anything that 404s or is ambiguous goes in
   `missing_cards`, not into the deck.
4. **Frontend**: `DeckImportModal.tsx` (new, in `frontend/src/components/`) — textarea + optional
   name override + submit, triggered from an "Import Deck" button in `DeckList.tsx`. On success,
   navigate to the new deck in `DeckBuilder.tsx` (matching the doc's original UX flow). If
   `missing_cards` is non-empty, show them with the `DeckBuilderSearch`-based replace affordance
   from the interview outcome above.
5. **Tests**: parser unit tests (simple list, MTGA export, mixed zones, malformed lines) +
   route test mocking Scryfall the same way `test_stats.py`/`test_legalities.py` already do,
   covering: full success, partial success (missing_cards populated, deck still created with the
   valid subset), and ownership (imported deck belongs to the requesting user).

### Verify

- `cd backend && uv run pytest` covers parser edge cases and the route, not just the happy path.
- Manually import `references/deck_import.txt` through the UI, confirm the deck lands correctly
  and any intentionally-broken line in a test paste shows up as a fixable warning.
- Update `docs/ARCHITECTURE.md`'s "what's not built yet" list once this ships.

### Bug found post-ship: rate limit crash on real decklists

First real-world test (a 21-line, 75-card decklist) 500'd entirely — not a parsing bug, a design
flaw: `resolve_entries` made one `search_cards` HTTP call *per line*. 21 sequential Scryfall
requests was enough to trip their rate limit before `sync_cards`'s own batch call even ran,
raising an uncaught `429 Too Many Requests` (confirmed via `docker logs`, not guessed).

**Fix**: rewrote resolution to use Scryfall's `/cards/collection` endpoint (added
`ScryfallService.get_collection`), which accepts up to 75 identifiers (by name or by
set+collector-number) in a single request — collapsing 21+ sequential calls into one. Matches
returned cards back to entries by name/printing (grouped, so the same name appearing in multiple
zones — e.g. a sideboard card also in the maindeck — still resolves both). A 429/500 on the
collection call itself now degrades to "everything in that chunk is missing" rather than
crashing the whole import.

Re-verified against the exact decklist that failed: `POST /decks/import` now returns 200 with
`missing_cards: []`, single `get_collection` call, correct quantities/boards for all 21 lines.
Added a regression test (`test_import_deck_batches_resolution_into_one_scryfall_request`)
asserting exactly one `get_collection` call regardless of decklist size, plus one for the
collection-call-itself-fails path, so this can't silently regress back to N sequential requests.

---

## Phase 3 — Practice Mode: branching action tree for goldfishing (after Phase 2)

### Vision and why it's phased this way

Goal: a tree view of a solo practice ("goldfishing") session — the sequence of actions taken each
turn, with the ability to rewind to any earlier point and try a different line, keeping both the
original and the new attempt as sibling branches (like a chess analysis tree or a git branch
graph, not a linear log).

End state is a **full rules-aware simulator** (validates legal plays, resolves triggered
abilities, understands the stack/targeting). That's out of reach as a single next-step — it's
closer to building a partial MTG rules engine. So this is deliberately staged in three sub-phases,
each one's infrastructure becoming a prerequisite for the next, rather than trying to design the
end-state data model upfront:

- **3a — Manual action log**: no game-state tracking at all, just a tree of free-text/lightly
  structured notes. Builds and validates the actual hard part first — the branching tree data
  model and its visualization — without also having to get a game-state model right at the same
  time.
- **3b — Assisted simulator**: adds real library/hand/battlefield/graveyard tracking and virtual
  shuffling, reusing the tree infrastructure from 3a unchanged (nodes just start carrying a real
  state snapshot instead of free text). Still no rules validation — the user manually drives
  every action.
- **3c — Full rules-aware simulator**: adds legality validation and effect resolution on top of
  3b's state model. Deliberately not designed in detail yet — what's learned building 3a/3b (what
  the tree UI actually needs, how much manual bookkeeping users tolerate before wanting
  automation) should inform this, not the other way around.

Requires **Phase 2 (Deck Import)** first — goldfishing needs an easy way to get a deck's 60-100
cards into the app to test against, and building a session around a deck the user had to
manually add one card at a time via search would be needlessly painful.

### Ground truth this plan is built on

- `backend/app/models/deck.py`: `Deck` has a `cards: List[DeckCard]` relationship;
  `DeckCard` is `(deck_id, card_id, quantity, board)`. This is the source a virtual library gets
  built from in 3b (expand each `DeckCard` by `quantity`, filter `board == "main"`, shuffle).
  Nothing new needed here for 3a/3b to reference an existing deck.
- Card image rendering already exists twice (`SearchCard.tsx`, `CardHoverPreview.tsx`), both
  using MUI `CardMedia` off `card.image_uris.normal`. Reuse this directly for hand/battlefield
  rendering in 3b rather than building new card-display components.
- **No graph/tree visualization library is installed** (`frontend/package.json` has none). This
  needs to be picked before 3a's UI can be built — see recommendation below.
- No session/game-log concept exists anywhere in the backend today — `models/`, `schemas/`,
  `api/routes/` all need new files, not extensions of existing ones (unlike Phase 1, which reuses
  `stats.py`/`scryfall.py` heavily).

### Phase 3a — Manual action log + branching tree

**Data model** (new — `backend/app/models/goldfish.py`):
- `GoldfishSession`: `id`, `user_id` (FK, ownership matches `decks.py`'s pattern), `deck_id` (FK),
  `name`, `created_at`.
- `GoldfishNode`: `id`, `session_id` (FK), `parent_id` (FK to `GoldfishNode`, nullable — null means
  root), `label` (free text, e.g. "Turn 2: cast Llanowar Elves"), `turn_number` (nullable int,
  purely informational), `order_index` (int, for ordering sibling branches left-to-right in the
  UI), `created_at`. A session's tree is just all nodes with that `session_id`, connected via
  `parent_id`.

**Backend** (new `backend/app/schemas/goldfish.py`, `backend/app/api/routes/goldfish.py`,
registered in `backend/app/api/api.py` alongside the existing routers):
- `POST /goldfish/sessions` — create a session for a deck.
- `GET /goldfish/sessions?deck_id=` — list sessions for a deck.
- `GET /goldfish/sessions/{id}` — full tree for a session (all nodes, client reconstructs the
  tree from `parent_id`s — don't build nested-JSON serialization for this, flat list + client-side
  tree build is simpler and matches how the frontend already handles `Deck.cards` as a flat list).
- `POST /goldfish/sessions/{id}/nodes` — add a node under a given `parent_id` (omitting
  `parent_id` targets the root). This is the operation that creates a branch: adding a second
  child under a node that already has one child is exactly "an alternate line."
- `DELETE /goldfish/nodes/{id}` — prune a branch (cascade-delete descendants).

**Frontend**:
- New page `frontend/src/pages/Goldfish.tsx`: pick a deck (reuse the existing deck-list picker
  pattern from `DeckList.tsx`), list/create sessions for it, open a session into the tree view.
- New component `GoldfishTree.tsx` — the actual tree/graph visualization. **Recommend
  `@xyflow/react`** (React Flow) for this: handles node/edge layout, zoom/pan, and click
  interaction out of the box, avoids hand-rolling SVG tree-layout math, and is the standard choice
  for exactly this kind of node-graph UI in React. This is the one new frontend dependency this
  phase needs.
- Interaction: click a node to select it as "current," a button/input to add a new action as a
  child of the selected node. If the selected node already has a child, this visibly creates a
  second branch rather than silently overwriting — that's the whole point of the feature, make it
  visually obvious in the tree (e.g. sibling branches rendered side by side, not stacked).

### Phase 3b — Assisted simulator

Builds on 3a's tree unchanged; nodes now carry real state instead of free text.

- **Game state**: recommend storing a full **state snapshot as JSON on each node**
  (`GoldfishNode.state: dict` — library as an ordered list of card IDs, hand, battlefield,
  graveyard, exile as lists, plus `life_total`), rather than storing per-node diffs that need to
  be replayed to reconstruct a point in the tree. Decks are small (~60-100 cards) and a goldfish
  line is short (maybe 10-20 turns per branch) — storage cost is negligible, and "what was the
  state at this exact node" being a direct read instead of a replay is worth it for both the UI
  and for debugging. Revisit only if sessions turn out to have far more branches than expected.
- **Virtual shuffle/draw**: build the virtual library from the deck's actual `DeckCard` rows
  (expand by `quantity`, `board == "main"` only) using a Fisher-Yates shuffle at session start.
  "Draw" moves the top library entry to hand and creates a new tree node with the updated
  snapshot.
- **Actions become structured**, not free text: a fixed vocabulary (`draw`, `play_land(card_id)`,
  `cast(card_id)`, `move_zone(card_id, from, to)`, `set_life(n)`, etc.) — still no legality
  checking, the user picks the action and the app just applies the zone/life change and snapshots
  the result.
- **UI**: needs an actual mini-playmat — hand (row of card images, reusing the existing
  `CardMedia` pattern), battlefield area, library/graveyard/exile as counts (with a
  click-to-expand list), life total. This is the meaningfully bigger lift in this sub-phase, not
  the tree itself (that's already built in 3a).

### Phase 3c — Full rules-aware simulator

Deliberately not detailed here yet — this is the point where the project would need real design
work on: parsing enough of a card's oracle text to know what it does, a stack/priority model,
targeting, triggered/replacement effects, and continuous-effect layers. That's a multi-month
undertaking on its own and should get its own dedicated planning pass once 3a/3b have shipped and
it's clear the tree/session infrastructure they build is actually being used and is the right
foundation. Revisit this section then, don't try to design it in advance.

---

## Deferred (explicit choice, not an oversight)

Production-readiness was considered and deliberately deprioritized behind feature work. Recorded
here so it isn't forgotten, not because it's next:

- **Real auth**: `POST /auth/login` is a placeholder; `get_current_user`
  (`backend/app/api/deps.py`) auto-creates/returns a dev user for every request, no Google ID
  token verification. `docs/auth_specs.md` has the design. Fine for local/dev use; would need to
  happen before any real user ever hits this.
- **CI**: only Renovate (dependency bumps) runs in `.github/workflows/` — nothing runs
  `pytest`/`ruff`/`eslint` on PRs. The pytest-collection break fixed in Phase 0 could sit
  undetected indefinitely under this setup.
- **Deployment target**: no `fly.toml`/`render.yaml`/Procfile/etc. anywhere — `docker-compose.yml`
  is local-dev only. Nothing to change until there's a decision on where this actually runs.
- **`mtg-chromadb` container reporting `unhealthy`**: predates Phase 0's changes, unrelated to
  anything done there, still unresolved. Worth a look before it's load-bearing for a public
  feature.

---

<details>
<summary><strong>Archive: Phase 0 repo cleanup (completed 2026-07-08, click to expand)</strong></summary>

Working guide from a 2026-07-08 audit of `feature/agent_factory` (built with `graphify`, git branch
diffs, and an actual `pytest` run — not just reading docs). Goal: fix what's actively broken or
misleading, clear out clutter, and decide the fate of unfinished scaffolding.

## P0 — Actually broken

### [x] Fix `pytest` collection failure
`cd backend && uv run pytest` — the command in `backend/README.md` and `CLAUDE.md` — was
**failing at collection**, not just at runtime.

- **Cause**: `backend/scripts/test_agent_logging.py:9` did
  `from app.ai.agents.rules.rules_agent import RulesAgent`. That class was removed when
  `rules_agent.py` was refactored to export a bare ADK `Agent` instance named `rules_agent`
  instead of a `RulesAgent` class.
- **Fix**: updated both scripts to invoke the agent via ADK's `InMemoryRunner` (matching
  `backend/app/api/routes/ai.py`'s working pattern), and scoped pytest's `testpaths` to
  `app/tests`/`tests` so `backend/scripts/` isn't collected implicitly.

### [x] Fill in missing AI env vars in `.env.example`
`backend/app/core/config.py` defines `GOOGLE_API_KEY`, `GOOGLE_PROJECT_ID`, `GOOGLE_LOCATION`,
`CHROMA_HOST`, `CHROMA_PORT`, `AI_MODEL_NAME` — none appeared in `.env.example`.

- **Fix**: added all six (later consolidated into `backend/.env.example` — see Phase 0's uv
  workspace collapse below, which found a second, drifted copy of this same file).

## P1 — Docs that actively mislead

### [x] Rewrite `backend/app/ai/README.md`
Described the pre-ADK API (`RulesAgent` class, `get_rules_agent()`). Rewritten to match the
current ADK `Agent` + `InMemoryRunner` pattern.

### [x] Delete and rewrite `docs/ARCHITECTURE.md` and `docs/AI_ARCHITECTURE.md`
Both were pre-implementation planning docs describing a `DeckAdvisorAgent`/chat widget that was
never built. Deleted, replaced with one doc reflecting actual current implementation, including
an explicit "what's not built yet" section (which is what fed Phase 1 above).

Audited the rest of `docs/`:
- `docs/DECK_IMPORT_DESIGN.md`, `docs/auth_specs.md` — describe unbuilt features, marked
  "not implemented" (fed the Deferred/Phase 2 sections above).
- `docs/design_rulings_agent.md` — proposed an in-memory FAISS/numpy index, abandoned in favor
  of the ChromaDB approach actually shipped — marked superseded.
- `docs/rules_ingestion_pipeline.md`/`_guide.md`, `docs/deck_statistics_spec.md` — directionally
  accurate, minor naming drift noted, not rewritten.

### [x] Replace `frontend/README.md` boilerplate
Was still the untouched Vite template. Replaced with real project dev instructions.

### [x] Update CLAUDE.md's frontend directory tree
Was missing `context/`, `styles/`, `utils/`, `assets/`.

## P2 — Dead scaffolding: resolved

### [x] Delete `BaseAgent`/`BaseTool` in `backend/app/ai/agents/core/base.py`
Nothing imported or subclassed it; the one real agent bypassed it entirely with a plain ADK
`Agent`. Deleted. **Decision, now being tested for real in Phase 1**: revisit a thin factory
*function* (not a class hierarchy) once a second agent exists and shows real duplication.

## P3 — Housekeeping

### [x] Delete fully-merged stale branches
`feature/deck_card_count_limit`, `feature/deck_import`, `feature/init`, `feature/rules_agent`,
`feature/ui`, `feature/ui-landing-page`, `feature/google_adk_rules_agent` — all fully merged (0
unique commits vs. both `main` and `origin/main`). Deleted locally and on `origin`.

### [x] Stop committing `graphify-out/` generated artifacts
`graph.json`/`graph.html`/`manifest.json`/`.graphify_labels.json` regenerate via
`graphify update .`. Gitignored, untracked (kept `GRAPH_REPORT.md` tracked).

### [x] Remove `references/` from git tracking
`MagicCompRules 20260116.txt` (954KB) and a 2.7MB screenshot were committed for no ongoing
reason — the rules text is fetched at runtime by `rules_ingestion.py`. Untracked, gitignored,
kept on disk locally.

### [x] Clean up loose root-level clutter
Removed untracked `test.db` and empty `backups/`.

## P4 — Collapse the single-member uv workspace (found mid-cleanup, not in original scope)

While verifying the P0/P3 fixes, `uv sync`/`uv run pytest` on the host repeatedly failed with
`error: failed to remove directory '.venv/lib': Directory not empty` and the venv's Python
symlink kept flipping between a macOS interpreter and a **Linux** one. Root cause, confirmed via
`lsof` + `docker logs`:

- Root `pyproject.toml` declared a uv **workspace** (`[tool.uv.workspace] members = ["backend"]`)
  with exactly one member. Workspaces put `.venv`/`uv.lock` at the workspace *root*, not per
  member — so `cd backend && uv sync` was silently managing a venv one directory above where the
  command ran.
- `docker-compose.yml`'s `backend` service mounted the **entire repo root** (`.:/app`) instead of
  just `./backend:/app` — required because `uv run` from `/app/backend` needed to see the
  workspace root's `pyproject.toml`/`uv.lock`.
- That meant the container's `/app/.venv` *was* the host's `.venv` — same directory, live, via
  the bind mount. The container runs `--reload` (watches the whole `/app` tree, including
  `.venv`) and re-runs `uv sync` on restart. Host-side `uv sync` and the container's own were
  writing into the same directory from two different OSes at once — hence the churn and symlink
  flapping.
- Confirming this wasn't just Docker noise: root `pyproject.toml`'s dependency list was **100%
  duplicated** in `backend/pyproject.toml` — no code at the repo root could ever import them.
  Almost certainly `uv add X` run from the repo root by mistake. A one-member workspace makes
  that mistake easy and provides none of a workspace's actual benefit (there's no second Python
  package — `frontend/` is npm, not a workspace member).

### [x] Strip root `pyproject.toml` to editor-only config
Removed `[project]`, dependencies, `[tool.uv.workspace]`. Kept only `[tool.pyright]`/`[tool.mypy]`
so editors opened at the repo root still resolve `backend`'s modules. Root `uv.lock` and root
`.dockerignore` removed (dead — nothing builds from root context anymore).

### [x] Make `backend/` a fully standalone uv project
Generated `backend/uv.lock` and `backend/.venv` via `cd backend && uv lock && uv sync`. Verified
standalone: `uv run pytest` (27 passed) and `uv run ruff check .` (clean), zero root-level Python
config involved.

### [x] Rewrite `backend/Dockerfile` and `docker-compose.yml` for a scoped build context
`docker-compose.yml`: backend builds with `context: ./backend`, mounts only `./backend:/app` plus
an `/app/.venv` anonymous-volume shadow (container gets its own private venv — verified: host
venv points at a macOS interpreter, container venv at a Linux one, fully independent). Same fix
applied to `frontend` (`/app/node_modules`). `backend/Dockerfile`: dropped the workspace-only
`--package=` flag; added `backend/.dockerignore` (Docker's default lookup changes with context).

### [x] Consolidate duplicate `.env.example`
`backend/.env.example` (the one actually read by `docker-compose.yml`/`config.py`) had silently
diverged from the root copy. Consolidated into `backend/.env.example`, deleted the root one.

### [x] Fix `bin/dev.sh`
Used workspace-only flags (`--all-groups --all-packages`). Simplified to `(cd backend && uv sync)`.

**Verified**: `docker compose build backend` succeeds, `docker compose up -d` reports `healthy`,
`cd backend && uv run pytest`/`uv run ruff check .` pass standalone.

</details>
