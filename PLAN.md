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

**Phase 1 (AI Deck Advisor) — done, 2026-07-26.** `POST /ai/suggest` wired to a new
`deck_advisor_agent` (stateless `search_cards` tool, deck stats/list folded into prompt context).
Second agent existing triggered the deferred factory-function check from Phase 0 — real
duplication showed up, so `make_agent` was extracted and both agents now use it. UI lives inside
`DeckBuilder.tsx` as a tab next to Deck Statistics (not `AgentChat.tsx` — scoped to the deck
already open, no deck picker needed). Feature completeness chosen over production-readiness
(auth/CI/deploy explicitly deferred, see "Deferred" below).

**Phase 3a (Manual action log + branching tree) — done, 2026-07-26.** `GoldfishSession`/
`GoldfishNode` models (flat table, `parent_id` self-FK), full CRUD under `/goldfish`, and a new
`/goldfish` + `/goldfish/:sessionId` frontend flow: deck picker → session list → a `@xyflow/react`
tree view where clicking a node selects it as "current" and adding a second action under an
already-answered node visibly branches (siblings side by side). Verified end-to-end in the browser
against the live docker stack: created a session, added a root + child, branched a second child
off the root, and pruned one branch back out — cascade-delete confirmed working. Interview
resolved the one open design decision (tree viz library: went with the plan's `@xyflow/react`
recommendation over hand-rolling).

**Phase 3b (Assisted simulator) — done, 2026-07-26.** `GoldfishNode.state` (JSON: library/hand/
battlefield/graveyard/exile + `life_total`) alongside 3a's `trackers` — kept deliberately separate
per an explicit decision: life stays a first-class field on the structured game state, not folded
into the generic tracker map. Sessions auto-create a shuffled "Game start" root node
(`build_initial_state`, Fisher-Yates via stdlib `random.shuffle`); structured actions (`draw`,
`play_land`, `cast`, `move_zone`, `set_life`) apply against the parent node's state and
auto-generate the node's label server-side. `GoldfishPlaymat.tsx` (new) renders hand/battlefield
as card images with per-card action buttons, library/graveyard/exile as click-to-expand counts,
and an editable life total. Verified end-to-end against the live docker stack: drew a card, played
it, adjusted life, moved it to the graveyard, and retrieved it back to hand via the graveyard
popover — full chain rendered correctly in the tree with auto-generated labels throughout.

**Phase 4 (Scryfall bulk-data ingestion) — partially done, 2026-07-27.** Picked up ahead of
Phase 3c (deliberately deferred, still a multi-month undertaking not ready to design) since Phase 4
was already independent and had a concrete design sketched. `run_ingestion()` refreshes the local
`Card` table from Scryfall's bulk `default_cards` file; `search_cards` now checks that cache first
for plain-name queries via a new tool-side DB session, falling back to live Scryfall on a cache
miss or Scryfall operator syntax. **Scheduling deliberately left manual** — no cron/loop/new
container, run by hand until there's a real deployment target. **Phase 3c is still next** after
this, whenever picked up.

**Every phase gets an interview before implementation** — a short round of clarifying questions
on the genuinely open design decisions, resolved and recorded before any code is written. Applied
to Phase 2 already; apply to Phase 1 and Phase 3 the same way when they're picked up.

---

## Phase 1 — AI Deck Advisor (done, 2026-07-26)

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

### Shipped: as designed, one perf caveat found in manual testing

Built as planned above — `make_agent` factory extracted (step 2's trigger condition fired for
real: `deck_advisor_agent` duplicated `rules_agent`'s `model=settings.AI_MODEL_NAME` boilerplate
exactly), advisor UI landed inside `DeckBuilder.tsx` as a tab next to Deck Statistics per step 6's
decision. Verified against the live docker-stack deck `pauper test` (60 cards): a real `/suggest`
call returned a suggestion citing `search_cards` results, correctly flagged the deck's own cards
as illegal for Pauper, and rendered in the chat UI.

**Perf issue found in that manual run, since fixed**: the agent was calling `search_cards` once
per *existing* deck card, sequentially — for a 60-card deck this took ~60-90 seconds end to end,
just re-verifying cards it had already been told about. Fix: `_build_deck_context`
(`backend/app/api/routes/ai.py`) now includes each existing card's mana cost/type/format legality
directly (data already loaded in memory, zero extra queries), and the prompt tells the agent not
to call `search_cards` for cards already in that list — only for new candidates. Cut the same
manual test to ~15-20s and 2-3 `search_cards` calls (only for genuinely new suggestions).
Considered making `search_cards` itself DB-backed for that remaining case too (a real local card
copy would still be faster/more scalable than live Scryfall for new-candidate searches) but hit a
real architectural blocker doing it as a quick add-on — see Phase 4 below, which is the properly
scoped version of that idea.

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

### Phase 3a — Manual action log + branching tree (done, 2026-07-26)

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

### Shipped: as designed, one implementation note and one real bug fixed

Built as planned above. One deviation worth recording: `DELETE /goldfish/nodes/{id}` cascades via
an application-level BFS over an in-memory `session_id`-scoped node list rather than a DB-level
`ON DELETE CASCADE` — simpler to reason about and test consistently across SQLite (tests) and
Postgres (real deployment) than relying on FK-cascade behavior that SQLite doesn't enforce by
default. The alembic migration was hand-written rather than autogenerated (host couldn't reach the
configured Postgres instance directly; verified instead by running `alembic upgrade head` and
`downgrade -1` inside the running `deck_builder-backend-1` container and diffing the resulting
schema with `psql \d`).

**Real bug caught during manual browser verification, not by tests**: `GoldfishSession`/
`GoldfishNode.created_at` used `datetime.now(timezone.utc)` (tz-aware) as its default, but the
migration's columns are `TIMESTAMP WITHOUT TIME ZONE` — asyncpg rejected the insert
(`can't subtract offset-naive and offset-aware datetimes`) the first time a session was actually
created against real Postgres. SQLite (what the test suite runs against) doesn't enforce this
distinction, so all tests passed despite the bug — this only surfaced hitting the live docker
stack. Fixed by generating a naive UTC datetime instead (`datetime.now(timezone.utc).replace
(tzinfo=None)`, not the deprecated `datetime.utcnow()`). Worth remembering for any future model
with a `datetime` column: SQLite-backed tests can't catch tz-awareness mismatches against Postgres.

### Phase 3a follow-up: usability feedback from actually using it

Real usage of the shipped 3a surfaced four gaps, all fixed:

1. **No entry point on the homepage.** `LandingPage.tsx`'s feature grid only had Decks/Brewing/
   Collection. Added a fourth `Practice Mode` tile (`/goldfish`), regrid to 4 even columns
   (`md: 3` instead of `md: 4`).
2. **No entry point from the deck itself** — had to go to Practice Mode and re-pick the same
   deck from a list. Added a gamepad icon button in `DeckBuilder.tsx`'s header (next to the
   format selector) linking to `/goldfish?deckId={id}`, disabled until the deck is saved.
   `Goldfish.tsx` now reads a `deckId` query param (`useSearchParams`) and pre-selects it,
   skipping the picker straight to that deck's session list.
3. **Deck list was text-only, no way to actually see a card.** Added card thumbnails
   (`image_uris.small`) to each deck-list row in `GoldfishSessionPage.tsx`, and wired
   `onMouseEnter`/`onMouseLeave` to the existing global `useCardHover` context — the same
   `CardHoverPreview` overlay `SearchCard.tsx` already uses elsewhere, no new preview component
   needed (this page isn't in `CardHoverPreview`'s DeckBuilder/Collection exclusion list, so it
   renders automatically).
4. **No way to track life total or anything else per node.** Added a genuinely generic
   `trackers: Optional[Dict[str, int]]` JSON column on `GoldfishNode` (migration
   `2040f7f42c18`) — an opaque name->value map, not a hardcoded `life_total` field, per the
   explicit ask for "a generic way." Each node stores its own full snapshot (not a diff),
   consistent with the snapshot approach Phase 3b below already commits to. The backend does zero
   inheritance logic — `trackers` is just whatever the request provides (`{}` if omitted).
   `NodeTrackerEditor.tsx` (new) is a small chip-list editor: existing tracker values are
   editable, new named trackers can be added inline. The frontend owns the "carry forward"
   behavior: selecting a node re-seeds the draft from that node's own `trackers`, so life (or
   anything else) persists turn-to-turn until edited. Node boxes in `GoldfishTree.tsx` now show
   a compact `Name: value` summary line under the label.

### Phase 3b — Assisted simulator (done, 2026-07-26)

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

### Shipped: as designed, plus one interview decision worth recording

Built as planned above, with one deliberate deviation from this section's original sketch: an
interview before starting resolved that `life_total` stays a first-class field on `state` (not
folded into 3a's generic `trackers` map) — trackers remain for arbitrary freeform counters, `state`
is specifically the structured game snapshot. Also: `action` is accepted on the *same*
`POST /goldfish/sessions/{id}/nodes` endpoint 3a already uses (an optional field, not a parallel
API) — when given, the backend applies it against the parent's state and auto-generates the
node's label; when omitted, the existing free-text/`trackers` path is unchanged, and a freeform
note under a 3b node now carries the parent's state forward unchanged (nothing happened to the
game, so nothing should be lost). Every session auto-creates a shuffled "Game start" root node at
creation time, so there's always a valid state to act against — the frontend auto-selects it on
load so a fresh session is immediately playable with no extra click.

Caught a real bug while writing the dedicated 3b test file, not from the app itself: a test helper
called `app.dependency_overrides.clear()` after a scoped `get_scryfall_service` override, which
also wiped the `client` fixture's `get_db` override — every DB call after that point in the test
tried to hit real Postgres. Fixed by deleting only the specific override key. Worth remembering:
`dependency_overrides.clear()` in a test is only safe as the very last override-touching statement
in that test, never mid-test with more DB-dependent calls still to come.

**Follow-up, same day**: two usability requests after trying the assisted simulator live —
- **Opponent life**: `GameState` gained `opponent_life_total` (default same as `life_total`,
  following the same Commander-format-aware starting value). `set_life` takes a `target: "self" |
  "opponent"` field (defaults to `"self"`, so the existing self-life call sites didn't need
  updating). `GoldfishPlaymat.tsx`'s life counter was extracted into a reusable `LifeCounter`
  sub-component so both counters (`Life` / `Opp`) share the same -/+/edit behavior. No migration
  needed — `state` is a JSON blob, and pydantic backfills the new field's default for any old
  stored state missing the key.
- **Auto-draw opening hand**: `create_session` now creates a second node (child of "Game start")
  via a new `draw_opening_hand(state, count=7)` service function right after the root, drawing up
  to 7 cards (fewer if the library's smaller, never raises). Kept as a *separate* node rather than
  folding into "Game start" itself — matches this system's own convention that every meaningful
  change gets its own node, and leaves "Game start" as a pure pre-game reference point. Guarded to
  skip creating this node entirely when the library is empty (0 drawn), so the existing
  empty-deck test (`test_get_session_tree_starts_with_auto_created_root`, asserting exactly 1
  node) needed no change.

**Follow-up #2, same day**: shuffle and next-turn buttons.
- **Shuffle**: a new `apply_action` branch (`type: "shuffle"`) that reshuffles `state.library` in
  place via `random.shuffle` and labels the node "Shuffled library" — a pure `GameState` mutation,
  fits the existing action dispatch exactly like `draw`/`move_zone`.
- **Next turn**: architecturally different from the other actions — advancing the turn is a
  `GoldfishNode.turn_number` concern, not a `GameState` mutation, so `"next_turn"` is handled
  directly in the `add_node` route rather than inside `apply_action` (which would have nothing to
  do with it). `turn_number` now inherits from the parent node for *every* node type (actions and
  freeform notes alike) unless a `next_turn` action bumps it or the caller explicitly overrides it
  — same carry-forward philosophy as `state`. Auto-label is `"Turn {n}"`, overridable like every
  other auto-label. `GoldfishTree.tsx` got a small fix alongside this: its existing `"T{n}: "`
  label prefix would otherwise double up with next_turn's own label into "T1: Turn 1" — skipped
  when the label already matches `/^Turn \d+/`.
- **Next turn also auto-draws**, added right after: extracted a shared `draw_card(state)` helper
  (used by the `draw` action, `draw_opening_hand`, and now `next_turn`) so "draw one card" is one
  implementation, not three. Label becomes `"Turn {n}: drew {card}"` (or `"Turn {n} (empty
  library)"` if the library's out) — still overridable via an explicit `label`.

**Bug found immediately after, real UX problem not a transient state issue**: "when I play a card
I can't delete that node." Root cause: `GoldfishSessionPage.tsx`'s footer `Paper` capped itself at
`maxHeight: "50%"` with `overflowY: "auto"` — once the playmat's hand/battlefield sections grew
past that cap, the Add/Prune row got pushed below the fold with no obvious way to scroll to it.
Fixed by the layout restructure requested right after (see next entry) rather than just patching
the height cap — a goldfishing session spends most of its time looking at the playmat, so giving
it the primary flexible area (not a capped footer) fixes the visibility bug and matches actual
usage at the same time.

**Layout restructure**: playmat is now the main view (`flex: 1`, its own `overflowY: auto`, so
Add/Prune can never be pushed off-screen again regardless of hand/battlefield size); the tree
moved to a 380px right-side panel, toggleable via a new `AccountTreeIcon` button next to the
existing deck-list toggle. Verified live: cast a card, confirmed Prune stayed visible and
clickable, confirmed pruning that branch actually worked (tree updated, selection reset to the
parent).

### Phase 3c — Full rules-aware simulator

Deliberately not detailed here yet — this is the point where the project would need real design
work on: parsing enough of a card's oracle text to know what it does, a stack/priority model,
targeting, triggered/replacement effects, and continuous-effect layers. That's a multi-month
undertaking on its own and should get its own dedicated planning pass once 3a/3b have shipped and
it's clear the tree/session infrastructure they build is actually being used and is the right
foundation. Revisit this section then, don't try to design it in advance.

---

## Phase 4 — Scryfall bulk-data ingestion pipeline (partially done, 2026-07-27)

### Why this one, and why now

Every Scryfall-touching code path today either calls Scryfall live per-request
(`search_cards`, `ScryfallService.search_cards`/`get_card_by_id`) or lazily caches into the local
`Card` table only when a card is actually added to a deck (`sync_cards`, `decks.py:26`), and never
refreshes a row once cached (`sync_cards` treats non-`NULL` `produced_mana` as "done forever" —
see `decks.py:33-44`). Two concrete problems this causes:

1. **Staleness**: a card's `legalities` can go stale forever once synced (e.g. a ban).
   `deck_advisor_agent` relies on exactly this data for its legality checks (see Phase 1's
   context-enrichment fix above) — a real correctness risk once this is a public, long-lived app.
2. **Scale**: `search_cards` hitting live Scryfall per call is fine at today's usage but won't
   hold up under concurrent users — Phase 2's post-ship bug (`get_collection` rate-limit crash)
   already showed how quickly Scryfall's rate limits bite even for a single user's request.

Attempted a smaller version of this during Phase 1 (point `search_cards` at the local `Card`
table before falling back to Scryfall) and hit a real blocker worth recording: ADK tool functions
are called by the agent framework with only their declared LLM-facing args (`query`, `format`) —
there's no request-scoped dependency injection like FastAPI's `Depends(get_db)`. Reaching for
`app.core.db`'s module-level `engine`/`SessionLocal` directly from the tool bypasses the test
suite's SQLite override entirely and tries to hit real Postgres — confirmed by a failing test run
(`OSError: Multiple exceptions: ... Connect call failed ... 5432`). Went with a different, safe
Phase 1 fix instead (full card details already in the prompt context, since the deck's cards are
already loaded in memory at the route level — zero extra queries). That fix doesn't help
`search_cards` calls for cards *not* already in the deck (i.e. suggesting something new), which is
the actual remaining gap this phase closes.

### Interview outcome (resolved before writing code, per-phase process)

This phase's Design section (below, written earlier) left two decisions explicitly open ("decide
when this phase is actually picked up"). Both resolved by interview before implementation started:

1. **Ingestion trigger: manual script, no scheduling infra.** Checked ground truth first —
   `rules_ingestion.py`, the pattern this phase's Design section originally said to mirror, turned
   out to *not* actually run as a separate scheduled service; it's bolted into the backend
   container's startup command chain (`docker-compose.yml`), re-running on every container
   restart. Fine for a small rules-text index, but re-fetching and upserting Scryfall's full
   `default_cards` bulk file (tens of thousands of rows, not the ~30k this section originally
   estimated) on every dev restart would make `docker compose up` noticeably slower for no real
   benefit in dev. Decided instead: a plain idempotent script
   (`uv run python -m app.ai.ingestion.scryfall_ingestion`), run by hand. Real recurring scheduling
   (cron, a sleep-loop service, etc.) is deferred until there's an actual deployment target to
   schedule against — see Deferred below — rather than building scheduling infra twice.
2. **Tool DB access: a dedicated direct-session helper, not an internal HTTP endpoint.** Chosen for
   scale/simplicity: a direct DB session reuses the existing connection-pooled async engine with no
   extra hop; an internal HTTP endpoint would add a self-referential network round trip and a new
   internal-only route to secure, for what is really just a local read. New
   `backend/app/ai/tools/db.py` exposes `get_tool_session()` — a plain function (not a FastAPI
   dependency) that tool code calls directly. Tests patch `get_tool_session` itself (via
   `unittest.mock.patch`), since ADK tool functions never go through FastAPI's request cycle and so
   can't be reached by `app.dependency_overrides`.

A third decision surfaced only once implementation started, not anticipated in the original Design
section: `search_cards`'s `query` argument is live Scryfall search syntax (`t:creature c:red`, ...),
and reproducing that whole grammar against Postgres is a real sub-project on its own, not something
to bolt on here. Scoped down safely: the local cache only serves **plain name-substring queries**;
anything containing a Scryfall `key:value` operator skips the cache and goes straight to live
Scryfall, so results stay correct for complex queries at the cost of not caching them. Revisit only
if the operator-query volume turns out to be high enough to matter.

### Design

- **A separate ingestion service/container**, not code bolted onto the API container — mirrors
  the shape `backend/app/ai/ingestion/rules_ingestion.py` already uses for the Chroma rules
  index, just pointed at Scryfall's bulk-data endpoint instead of the comprehensive rules text.
  Runs on a schedule (daily is plenty — Scryfall's own bulk files update daily), pulls the
  `default_cards` bulk-data file (~30k cards, all printings' worth of core fields including
  `legalities`), and upserts into the `Card` table — this is a refresh, not the lazy
  create-once `sync_cards` does today.
- **This is what makes a DB-backed `search_cards` safe to build**: once there's a real,
  continuously-refreshed local copy, `search_cards` can be pointed at it without inventing
  request-scoped DI for ADK tools. Two ways to wire that once ingestion exists, decide when this
  phase is actually picked up: (a) the ingestion service also exposes a small internal read-only
  HTTP search endpoint that the tool calls via its own `httpx.AsyncClient` per call (same
  resource-per-call shape every existing tool already uses, just pointed internally instead of at
  Scryfall), or (b) a dedicated read-only engine/session helper for tool code, separate from
  `app.core.db`'s request-scoped one, that a test fixture can override the same way `db_session`
  overrides `get_db` today.
- **Docker Compose**: new service alongside `backend`/`frontend`/`db`/`chromadb`, own Dockerfile
  or a `command:` override reusing the backend image — decide when this is actually built,
  don't over-design the container shape in advance of writing the ingestion script itself.

### Verify (once built)

- Ingestion run populates/refreshes the `Card` table without touching decks/user data.
- `search_cards` (however it ends up wired) returns current legality data for a card known to
  have had a legality change since the app's last lazy `sync_cards` cache of it.
- Re-run the ingestion container twice in a row — confirm it's a safe upsert (no duplicate rows,
  no FK breakage against existing `DeckCard` references).

### Shipped: ingestion + tool wiring done, scheduling deliberately not

Built per the interview outcome above. `backend/app/ai/ingestion/scryfall_ingestion.py`:
`fetch_bulk_data_uri()` looks up the current `default_cards` download URL from Scryfall's
`/bulk-data` endpoint (rotates daily, so it's always looked up fresh, never hardcoded);
`download_bulk_cards()` fetches and parses it; `upsert_cards()` batches rows (1000/batch), splits
each batch into already-existing IDs (one bulk `UPDATE` via SQLAlchemy's executemany-style
ORM update) vs. new IDs (`session.add_all`) — deliberately plain ORM operations rather than a
Postgres-specific `ON CONFLICT` upsert, so the same code path is exercised by the SQLite test
engine, not just Postgres in production. `run_ingestion()` wires it together; entry point is
`uv run python -m app.ai.ingestion.scryfall_ingestion`, run by hand, not wired into any container
command or scheduler.

`backend/app/ai/tools/db.py` (new) is the tool-side DB session seam from decision 2 above.
`search_cards` (`backend/app/ai/tools/cards.py`) now tries a local `Card.name ILIKE` lookup first
for any query without a Scryfall operator, falling back to live Scryfall on a miss or on operator
syntax — the scope-narrowing decision recorded above. Caught and fixed a real regression while
implementing this: three pre-existing `search_cards` tests didn't patch the new DB seam, so they
started trying to hit real Postgres the moment `search_cards` gained its local-first read path
(same class of failure this phase's own "Why this one" section already predicted from the Phase 1
attempt) — fixed by patching `get_tool_session` in those tests too, using the existing SQLite
`db_session` fixture. `cd backend && uv run pytest` (79 passed) and `uv run ruff check .` both
clean.

**Not done**: the scheduling half of the original two-problem framing ("Staleness"/"Scale" above).
Running `run_ingestion()` once now populates/refreshes the cache, but nothing keeps it refreshed
automatically — by design, per the interview decision, until there's a real deployment target.
Also not done: Docker Compose service shape was never decided because there's no new service to
place — the "manual script" decision made that whole sub-question moot for now.

### Live-verified against the real stack (2026-08-04): one real bug caught, since fixed

The above was only unit-tested (mocked `httpx`/SQLite) until this pass — actually running
`run_ingestion()` against live Scryfall + the docker-stack Postgres surfaced a real bug the mocks
couldn't catch: `fetch_bulk_data_uri()` assumed the bulk-data listing had a `download_uri` field
pointing at a plain JSON array. It doesn't — Scryfall's current API only returns
`jsonl_download_uri`, pointing at a **gzipped JSONL** file (one JSON object per line, gzip-
compressed), not a plain JSON array. First real run `KeyError`'d immediately. Confirmed the actual
shape with a live `GET /bulk-data` call rather than guessing from docs, then fixed both
`fetch_bulk_data_uri()` (read `jsonl_download_uri`) and `download_bulk_cards()` (`gzip.decompress`
+ parse line-by-line) to match. Updated the two unit tests that encoded the wrong assumption
(`test_fetch_bulk_data_uri_finds_default_cards`, `test_download_bulk_cards_returns_parsed_jsonl`)
so this can't silently regress back to the wrong shape.

Re-ran end-to-end after the fix, against `deck_builder-backend-1`/`deck_builder-db-1` (docker
stack): downloaded and parsed 116,568 real card entries, upserted cleanly (`SELECT count(*) FROM
card` → 116568). Ran it a **second** time immediately after (PLAN's own Verify criteria: "re-run
twice, confirm safe upsert") — same 116,568 rows, `count(*) = count(DISTINCT id)`, no duplicates,
44s second run. Also called `search_cards` directly against this live data: a plain-name query
("lightning bolt") returned correct local results (multiple printings, correct modern legality) in
~190ms including Python startup; an operator-syntax query ("t:creature c:red pow>=5") correctly
skipped the local cache and returned live Scryfall results — confirming both branches of the
scope-narrowing decision actually work against real data, not just mocks.

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

### Fixed: `mtg-chromadb` container reporting `unhealthy` (2026-07-30)

Root cause, confirmed via `docker inspect mtg-chromadb`'s health-check log, not guessed: the
`chromadb/chroma` image has no `curl` (or `wget`/`python`) in it at all — `docker-compose.yml`'s
healthcheck (`CMD curl -f http://localhost:8000/api/v2/heartbeat`) failed at the exec step every
time (`exec: "curl": executable file not found in $PATH`), regardless of whether Chroma itself was
actually healthy. The container was serving requests fine the whole time (confirmed: RAG queries
through `rules_agent` worked) — this was purely a broken health probe, not a broken service.

**Fix**: replaced the `curl`-based check with a raw HTTP GET over bash's `/dev/tcp` (bash is
present in the image; nothing else needed to be installed):
```
bash -c 'exec 3<>/dev/tcp/127.0.0.1/8000 && printf "GET /api/v2/heartbeat HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n" >&3 && head -1 <&3 | grep -q 200'
```
Verified: `docker compose up -d chromadb` recreated the container, `docker inspect`'s
`.State.Health.Status` went to `healthy` within one interval and stayed there (`FailingStreak: 0`
after a minute), and the backend's own health endpoint plus a direct heartbeat call from inside the
backend container to `chromadb:8000` both still succeed — the fix only touched the probe, not
connectivity. Backend's own `curl`-based healthcheck (`backend` service, different image, one that
actually has `curl` installed) was unaffected and left as-is.

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
