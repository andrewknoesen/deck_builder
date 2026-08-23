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
container, run by hand until there's a real deployment target.

**Phase 3d (Two-deck goldfishing) — planned, not started, 2026-08-09.** Picked up next, ahead of
Phase 3c — user-requested, small/well-scoped extension of already-shipped 3b infrastructure
(manual dual-piloting of a second deck, still no rules checking), versus 3c's still-unscoped
multi-month "rules-aware simulator" undertaking. Independent of whether 3c ever gets built. Both
opening hands auto-deal at session start (product owner decision, 2026-08-09). See Phase 3d below
for the full design.

Under review, per the product owner's explicit "any gate finding sends the whole plan through
every agent again, no exceptions" process: all five specialists (`mtg-architect`, `mtg-backend`,
`mtg-frontend`, `mtg-qa`, `mtg-ux`) review their own portion, `mtg-em` gates last, any gate finding
restarts the full cycle. Multiple rounds completed; fixes are cited inline where they landed in the
section body below, most tagged with round and/or reviewer — that inline record is authoritative
over anything this paragraph might claim about it, and round 8's `mtg-architect` pass caught this
sentence itself overclaiming "every fix... tagged with which round" when several inline citations
name only a reviewer, no round number. Not backfilling those individually here for the same reason
the round-summary attempt below was abandoned: chasing completeness in prose invites the next
overclaim rather than fixing the actual problem. **This paragraph deliberately does not summarize
or categorize the rounds** (e.g.
"rounds X-Y were only textual" / "round Z had more substance than round W") — every attempt at that
kind of characterization has itself been a source of gate findings (an inaccurate summary is just
another thing that can go stale or overclaim), so the fix is to stop attempting it here rather than
keep re-deriving a correct version. If you want to know what a given round found, read that round's
inline citations in the body, not a paraphrase of them.

**Review complete, 2026-08-10.** Round 10's `mtg-em` gate pass found nothing, across all five
specialists plus the gate itself, the first fully clean round of the ten this plan went through.
Ten rounds caught real, fixed issues throughout — not just in the early rounds: the last
substantive (non-textual) finding landed in round 10 itself (`mtg-qa`'s untested opponent-side
empty-library `draw` case), so "converging" held all the way to the actual end rather than tailing
off earlier than it looked.

**Post-review interview held, 2026-08-10, per this file's per-phase convention.** One item the
review process had settled by agent judgment rather than actually asking the product owner:
mixed-format life totals. Resolved by actually asking — **opponent deck selection is now
restricted to the same format as the primary deck**, a real new requirement (400 on mismatch), not
just documentation of the prior behavior; see the "Same-format restriction" note under Design
below for the full reasoning and the explicitly-deferred future relaxation. Folded into Design,
Concrete Steps, and Verify.

**Phase 3d shipped, 2026-08-11.** Routed to `mtg-backend` (Concrete Steps 1-2) then `mtg-frontend`
(Steps 3-4), in that order since the frontend's opponent board renders against the backend's real
response shape. See "Shipped" under Phase 3d below for the full record, including the one
deviation from the plan (a synchronous double-submit guard, needed to actually satisfy the plan's
own rapid-double-click Verify requirement) and the live verification actually performed.

**Phase 3c parked, 2026-08-12 (user decision).** Not deleted from this file, not "revisit after
3a/3b" anymore either — explicitly on hold with no next-pick-up trigger, superseded by Phase 5
below as the thing actually being worked on next. Revisit only if the user brings it back up.

**Phase 5 (AI-assisted card search for deck building) — picked up next, 2026-08-12.** User-
requested: a conversational agent on the deck-building page for synergy-style card discovery
("cards that benefit from artifacts leaving the battlefield," "cards that deal damage when an
artifact enters") — a fundamentally different query shape than Scryfall's keyword/operator search
or `deck_advisor_agent`'s existing `search_cards` tool, closer to semantic/vector search over card
oracle text. User's own opening framing: a SQL + vector-DB hybrid. Routed to `mtg-architect` first
for a design pass before any interview or implementation, per this file's own convention for
anything crossing backend AI layer + data pipeline + frontend. See Phase 5 below once that lands.

**Phase 5 shipped, 2026-08-12.** `search_cards_semantic`/`CardRAG` over a new `mtg_cards` Chroma
collection, a shared sentence-transformer embedder between `RulesRAG` and `CardRAG`, and a manual
`card_embedding_ingestion.py` script. Live-verified end-to-end against the real stack. See Phase 5
below for the full record.

**Phase 6 (Per-card synergy lookup) and Phase 7 (Goldfish session analytics) — picked up next,
2026-08-15.** Both user-requested in the same brainstorming session, in this stated priority order
(synergy lookup first). Both routed to `mtg-architect` for a design pass before any interview or
implementation, run in parallel since the two are independent of each other (different subsystems:
AI/deck-building vs. goldfishing). Design passes and product-owner interviews both complete for
each — every open question resolved to the blueprint's own recommended default, no deviation.
**Phase 7 shipped, 2026-08-15** (backend then frontend, no scope deviation, live-verified against
the real docker stack). **Phase 6 shipped, 2026-08-16** (frontend-only as designed, live-verified
against the real docker stack after isolating one transient Gemini-API blip from the actual code).
See Phase 6 and Phase 7 below.

**Phase 8 (Total mana spent tracker) and Phase 9 (Expose deck_builder's tools via MCP) — routed to
`mtg-architect`, 2026-08-23.** Both design passes complete, run in parallel since the two are
independent (goldfish gameplay tracking vs. a new MCP server subsystem). Phase 8: recommends
extracting the existing `stats.py` CMC parser into a shared module rather than adding a stored
`cmc` column, and storing the running total as a first-class `GameState` field rather than deriving
it on read — two open questions (tree-view surfacing, bundling a pre-existing parser bug fix)
flagged for interview. Phase 9: recommends a `FastMCP`-based server in new `backend/app/mcp/`
exposing all five existing read-only ADK tools over **stdio only** for v1 — explicitly not
HTTP/SSE, which the design treats as a hard blocker on real auth landing first, not a "later"
item. Both interviews complete, 2026-08-23: Phase 8 took the *non*-default on both its questions
(tree view included, not deferred; the pre-existing `{X}` CMC-parser bug gets fixed now, not left
alone) — Phase 9 confirmed every recommended default with no deviation.

**Phase 8 shipped, 2026-08-23** (backend then frontend, no scope deviation from the interview
outcome). See "Shipped" under Phase 8 below for the full record, including the corrected `{X}`
mana-value numbers and both the playmat and tree-node surfaces live-verified against the real
docker stack, single-deck and two-deck.

**Phase 9 shipped, 2026-08-23** (backend-only, matching the design — no frontend surface for an
MCP server). One dependency-version deviation (`mcp<2`, pinned against a same-day `2.0.0` release
that renamed the API this design was built against) and one real bug found and fixed during live
verification (stdout logging corrupting the stdio JSON-RPC stream). See "Shipped" under Phase 9
below for the full record, including the genuine MCP wire-protocol client verification performed.

**Phase 10 (Central project wiki) shipped, 2026-08-23** — user-requested same day, design pass
(`mtg-architect`) then scope review (`mtg-em`) before implementation, all three interview
questions resolved (refresh stale docs now, generate the previously-aspirational
`graphify-out/wiki/`, route through `mtg-em` before writing). `docs/README.md` is now the central
routing index for both agents and human developers, also published as a hosted mkdocs site at
`https://andrewknoesen.github.io/deck_builder/` (a same-day follow-up — GitHub Pages + a new,
narrowly path-filtered GitHub Actions workflow, the first CI in this repo). Two more same-day
follow-ups: two dead links found on the live site got fixed, and `docs/UI_DEGENERIC_DESIGN.md`'s
own status banner turned out to be wrong (3 of 4 findings were already fixed back in
2026-08-06, just never linked back) — corrected. See "Shipped" and the follow-up entries under
Phase 10 below for the full record.

**Phase 11 (De-genericize the rest of the app) shipped, 2026-08-23** — the one item Phase 10's
correction found genuinely still open: `DeckBuilder`/`Collection`/`DeckList` now reuse the landing
page's bespoke MTG glyph icons instead of stock Material icons, closing out
`docs/UI_DEGENERIC_DESIGN.md` entirely. See Phase 11 below for the full record.

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

### Phase 3d — Two-deck goldfishing (planned, not started)

**Not a step toward 3c.** 3c is about rules automation (legality/stack/targeting) on top of one
player's state. This is a different, smaller extension of 3b: a second player's board, still
fully manual, still no rules checking. Independent of whether 3c ever gets built.

#### Why this one, and why now

Raised directly by the user: goldfishing today only tests a deck against itself (draws, curve,
own lines). "Test the specific lines I would play against other decks" needs an actual opponent
board — real cards they might have, not an abstract life counter — so the user can manually pilot
*both* decks and see how a line holds up against real answers/threats, not just an empty board.

**Interview outcome (resolved via conversation before writing this section, per-phase process):**
manual dual-piloting, not an AI opponent. The user drives every action on both sides, same as
today's single-deck philosophy (no legality checking, no automation) just doubled. `next_turn`
stays a single shared counter and does **not** auto-draw for the opponent — auto-drawing would
mean guessing when the opponent-side "would" draw, which is exactly the kind of implicit rules
logic this system has deliberately avoided everywhere else. The opponent's hand is fully visible
in the UI (not hidden) — there's no real hidden information here, one user is piloting both sides.

**Resolved (product owner, 2026-08-09): auto-deal both opening hands.** Session creation deals 7
cards to the opponent's `opponent_zones.hand` the same way it already does for the player's own —
consistent with 3b's existing framing of the opening draw as pre-game setup, not "automation."
Implementation-wise: this is **one** combined node, not two — drawing both starting hands is
simultaneous pre-game setup, not a turn exchange, so it doesn't fit this system's "every
meaningful *action*" node-per-event convention the way an actual turn does.

`draw_opening_hand` does **not** take a second `Zones` argument — a second-round `mtg-architect`
pass caught that the Actions section below already establishes the convention of reading
`state.opponent_zones` directly rather than passing it around separately, and by the time
`draw_opening_hand` runs in `create_session`, `build_initial_state` has already populated
`state.opponent_zones` (it runs first). So `draw_opening_hand(state)` should internally check
`if state.opponent_zones is not None:` and draw up to 7 into it in place, matching how every other
zone-mutating function in this section already resolves the target. Producing a second, separately
sourced `Zones` object would be redundant with data already on `state` and a real drift risk if a
future call site ever passed something that wasn't actually `state.opponent_zones`.

The resulting single node's label generalizes today's `"Drew opening hand (N cards)"` to also name
the opponent's draw when present — see "Opening-hand label wording, pinned down" under Design
below for the exact strings (round 6's `mtg-architect` pass caught this pointer saying "Concrete
Steps" when the paragraph actually lives in Design — fixed), the single canonical statement of
this wording (an earlier draft
of this paragraph restated a vaguer version inline, which `mtg-em`'s gate review caught as drift
between two parts of the same document — don't reintroduce a second copy here). Unchanged wording
for single-deck sessions, where `state.opponent_zones` is `None` and the second draw never happens.

`create_session`'s existing opening-hand node-creation guard (`if opening_state.hand:`,
`backend/app/api/routes/goldfish.py:91`) also needs updating — this was independently caught in
round 2 by both the `mtg-architect` and `mtg-backend` review passes, a strong signal it's real
(round tag added in round 7, per `mtg-architect`'s pass flagging this citation as missing one). As
written
today the guard is self-hand-only: for a two-deck session where the primary deck's library is
empty (or too small to draw anything) but the opponent's deck has cards, a literal port would
silently skip creating the combined node entirely, dropping the opponent's dealt hand along with
it even though it was computed. Needs to become something like `if opening_state.hand or
(opening_state.opponent_zones and opening_state.opponent_zones.hand):`.

#### Ground truth this plan is built on

Verified directly against the current code (not just described) by two `mtg-architect` review
passes plus dedicated `mtg-backend`/`mtg-frontend`/`mtg-qa`/`mtg-ux` review passes on their
respective portions, all before any implementation — corrections from all of them are folded in
below and throughout this section, not left as separate review notes, since this section should
reflect what's actually true, not what the first draft assumed. `mtg-backend` additionally
confirmed the core `Zones`/`GameState` split empirically (built and round-tripped the exact model
below), not just by reading it.

- `GoldfishSession` (`backend/app/models/goldfish.py:50-68`) has a single `deck_id`. No opponent
  concept at all beyond `GameState.opponent_life_total` (a bare int, added in 3b's usability
  follow-up) — no opponent library/hand/battlefield.
- `GameState` (`goldfish.py:17-36`) is a flat pydantic model: `library`/`hand`/`battlefield`/
  `graveyard`/`exile`/`life_total`/`opponent_life_total`, stored whole as JSON on
  `GoldfishNode.state` (no per-node diffing, established in 3b and still the right call here —
  doubling the state size for a ~60-100 card deck across ~10-20 turn branches is still
  negligible). Critically: `GoldfishNodePublic.state` (`backend/app/models/goldfish.py:91`, via
  `GoldfishNodeBase`) is typed `Optional[Dict]`, **not** `GameState` — FastAPI's `response_model`
  never re-validates or
  reshapes it, so the only place `GameState`'s exact shape matters at all is
  `GameState(**parent_node.state)` in the route (`backend/app/api/routes/goldfish.py:187`). This is why
  the "zero migration" claim below is actually true, not just hoped-for — confirmed by grepping
  the whole repo for other `GoldfishNode.state` consumers; there are none outside the goldfish
  model/service/route/tests.
- `GoldfishActionIn` (`goldfish.py:39-47`) **already has** a `target: Literal["self","opponent"] =
  "self"` field — added in 3b for `set_life` specifically. This plan generalizes it to every
  zone-mutating action type instead of adding a parallel field, since it's already the exact right
  shape. `next_turn` is handled in the route, not `apply_action`, and per the interview outcome
  doesn't touch the opponent at all — `target` is simply inert for it.
- `apply_action`/`draw_card`/`draw_opening_hand` (`backend/app/services/goldfish.py`) are all
  written directly against a flat `GameState`'s top-level zone fields — every zone-mutating
  function needs to become target-aware, not just `set_life`.
- `build_initial_state(deck)` (`goldfish.py:10-26`) builds one player's shuffled library from one
  `Deck`. Needs an optional second `Deck` argument.
- `create_session` (`backend/app/api/routes/goldfish.py:66-67`) already 403s if the primary
  deck's `user_id` doesn't match the current user. No equivalent check exists for a second deck
  yet, since there is no second deck yet — this needs to be added new, not "extended," for
  whichever deck ends up in the `opponent_deck_id` slot.
- Card-name lookup for auto-labels (`backend/app/api/routes/goldfish.py:203-215`) is **already
  deck-agnostic** — one query against the deck-independent `Card` table over whatever `card_id`s
  appear in `all_card_ids`, built from the current state's zones. It does not build a per-deck map
  today and doesn't need to; it just needs `opponent_zones`' five lists folded into the same
  `all_card_ids` set before that one query runs. That fold must be null-guarded
  (`{*state.opponent_zones.library, ...} if state.opponent_zones else set()`) — `mtg-backend`
  flagged that a plain single-deck session issuing `set_life(target=opponent)` still reaches this
  code path (it's excluded only from the zone-mutation dispatch, not from label generation), and an
  unconditional `state.opponent_zones.library` access there would `AttributeError` on exactly the
  regression case this plan is most worried about protecting.
- The existing test helpers `_make_deck_with_cards`/`_make_deck_with_many_cards`
  (`backend/app/tests/api/routes/test_goldfish_actions.py`) each create a **new** `User` bundled
  with every deck (unique `email`/`google_sub`, enforced at the DB level —
  `backend/app/models/user.py`). `mtg-backend` confirmed calling either twice to get "two decks,
  one owner" fails on that unique constraint — a new helper taking an existing `User` and creating
  only the deck is needed before Step 1's test list is actually writable, not just reworded.
- The two prior goldfish migrations (`2040f7f42c18`, `97dfa370d0ca`) were each a single
  `op.add_column(..., sa.JSON())` with no constraint. The original table-creation migration
  (`957916eed363`) already has four foreign keys, so `opponent_deck_id` isn't "the first
  foreign-key-adding migration" outright (round 5's `mtg-architect` pass caught that overclaim) —
  it's the **first FK added via `ALTER TABLE` to an already-existing table**, since
  `957916eed363`'s four FKs were all inline `sa.ForeignKeyConstraint`s on `op.create_table(...)`.
  On Postgres that's `op.add_column(...)` plus a separate `op.create_foreign_key(...)` (and the
  matching `downgrade()` needs `op.drop_constraint(...)` before `op.drop_column(...)`), not the
  one-line shape either prior migration used. `mtg-backend` flagged this as worth being explicit
  about since it's a new pattern for this file, on top of the already-noted Alembic-autogenerate
  caution below.
- Frontend: `GoldfishPlaymat.tsx` renders one `GameState` directly. Today's single shared row
  (`GoldfishPlaymat.tsx:194-291`) mixes concepts that the interview outcome splits apart: the Turn
  chip and Next Turn button are genuinely shared (one turn counter, confirmed by the interview),
  but Draw, Shuffle, the library/graveyard/exile zone chips, and both `LifeCounter`s ("Life" and
  "Opp") are all **self-scoped** today, not shared — under dual-piloting, the opponent side needs
  its own Draw/Shuffle/zone-chips/life-counter too, not just its own hand/battlefield. `LifeCounter`
  (`GoldfishPlaymat.tsx:61`) is a module-private sub-component, not exported.
  `GoldfishSessionPage.tsx` fetches exactly one `deck` for the whole page and builds one
  `cardById` map from it, used by both the deck-list sidebar and the playmat.
- `Goldfish.tsx`'s new-session dialog takes only a name; deck is chosen on the page before that.

#### Design

**Data model — additive, not restructured, specifically to avoid migrating existing sessions'
JSON:**

```python
class Zones(BaseModel):
    library: List[str] = []
    hand: List[str] = []
    battlefield: List[str] = []
    graveyard: List[str] = []
    exile: List[str] = []

    def zone(self, name: str) -> List[str]: ...  # unchanged from today's GameState.zone

class GameState(Zones):
    life_total: int = 20
    opponent_life_total: int = 20
    opponent_zones: Optional[Zones] = None   # NEW — None for every existing session
```

`GameState` inherits `Zones` rather than composing it, so the top-level JSON shape for a
single-deck session's own state is byte-for-byte unchanged (`library`, `hand`, etc. stay at the
top level) — every existing stored `GoldfishNode.state` blob parses into this exactly as before,
`opponent_zones` just defaults to `None` on load. Zero Alembic migration for the JSON itself (it's
already an untyped JSON column, and — per the Ground Truth note above — nothing outside the
`GameState(**parent_node.state)` call site depends on its exact shape). This is a deliberate asymmetry —
self stays flattened on `GameState`, opponent is nested under `opponent_zones` — traded for
genuinely zero migration risk on every session created before this phase, matching this file's own
precedent (e.g. 3b's `opponent_life_total` addition needing no migration either, same reasoning).
`mtg-architect` reviewed this specific tradeoff against the real code and confirmed it holds.

`GoldfishSession` gets one new nullable column: `opponent_deck_id: Optional[int] =
Field(default=None, foreign_key="deck.id", index=True)` — `index=True` per round 5's `mtg-backend`
pass, matching every other FK field on this model (`deck_id`/`user_id` on `GoldfishSessionBase`,
`session_id`/`parent_id` on `GoldfishNodeBase` all declare it; nothing currently queries by
`opponent_deck_id` directly, so this is a convention-consistency fix, not a correctness one).
Three schema classes end up with the field, but it only needs to be **written in two places** —
`GoldfishSessionBase` (from which
`GoldfishSession`/`GoldfishSessionPublic` both inherit it automatically) *and*
`GoldfishSessionCreate`, which does not inherit `GoldfishSessionBase` and redeclares its own
fields fresh (`goldfish.py:61-64`). Missing `GoldfishSessionCreate` means the field would silently
never reach the DB from the request — an easy miss, called out explicitly so it isn't. Nullable
throughout, so every existing session (and every new single-deck session) is completely
unaffected — this phase is opt-in per session.

**Actions** — `GoldfishActionIn.target` already exists; extend `apply_action` (and `draw_card`,
which currently takes a `GameState` and needs to instead take a `Zones`) to resolve which `Zones`
object a **zone-mutating** action mutates (`draw`, `play_land`, `cast`, `move_zone`, `shuffle`):

```python
next_state = state.model_copy(deep=True)  # apply_action already does this today
target_zones = next_state if action.target == "self" else next_state.opponent_zones
if target_zones is None:
    raise ValueError("This session has no opponent deck")
```

then mutate `target_zones` and reassign: `next_state` (self case, same as today, valid Liskov
substitution since `GameState` *is* a `Zones`) or `next_state.opponent_zones = <mutated copy>`
(opponent case, a genuinely new `Zones` object that must be explicitly reassigned back).

`set_life` is explicitly **excluded** from the "no opponent deck → error" behavior above — it's
already target-aware today via the separate `opponent_life_total` field (outside `Zones` on both
sides, no duplication with a nested `opponent_zones.life_total`), and a single-deck session's
`set_life(target=opponent)` is existing, shipped behavior (the bare opponent-life-counter feature
from 3b's follow-up) that must keep working with no `opponent_deck_id` at all. Getting this wrong
would be a real regression, not just a missed edge case — worth double-checking directly in
review, not just in the plan.

**Session creation**: `build_initial_state(deck, opponent_deck=None)` — shuffles the opponent's
mainboard into `opponent_zones` when given, exactly like the player's own. The route needs to
fetch both decks (`selectinload` on each) before calling it, **and must 403 if the opponent
deck's `user_id` doesn't match the current user**, mirroring the existing check on the primary
deck (`goldfish.py:66-67`) — without this, a user could pass another user's `opponent_deck_id` and
read that deck's card list into their own session. No change needed to card-name lookup for
labels beyond folding `opponent_zones`' five lists into the existing `all_card_ids` set (see
Ground Truth above) — it's already one deck-agnostic query, not something that needs a second
per-deck map.

One deliberate non-restriction worth recording rather than leaving ambiguous, per `mtg-backend`'s
review: `opponent_deck_id == deck_id` (piloting a deck against a copy of itself) is not blocked —
legitimate mirror-match use case, and mechanically safe since `build_initial_state` independently
shuffles two separate `list[str]` copies of the same card pool with no shared mutable state.

**Same-format restriction (product owner decision, 2026-08-10, resolved at interview — not an
agent judgment call like the item above).** The review process's original framing of the
mixed-format life-total question ("not worth the complexity, both sides just use the primary
deck's total") was an engineering judgment call made without actually asking the product owner.
Asked directly: **opponent deck selection must be restricted to the same format as the primary
deck.** `create_session` needs a new check alongside the existing ownership check — reject with a
400 if `opponent_deck.format != deck.format` (plain equality; two decks with no format set, i.e.
both `None`, are treated as matching, same as any other equal-value case — no special-casing
needed). This makes the life-total question moot rather than solved: `build_initial_state`'s
existing Commander-like-format heuristic, unchanged, now always agrees with itself on both sides
since the formats are guaranteed equal by the time it runs. **Explicitly deferred, not forgotten**:
relaxing this to support genuinely mixed-format pairing (each side computing its own life total
independently) is a real future enhancement, not implemented now — if it's ever wanted, it needs
its own design pass (at minimum: does `GameState.life_total`/`opponent_life_total`'s shared
Commander-format-derived-from-one-deck assumption need to become two independently-derived values,
and what should Practice Mode's UI say about starting life differing between two boards).

**Node labels**: keep today's unprefixed labels for `target == "self"` (zero diff for the common
case). Add an `"Opponent: "` prefix only for the **zone-mutating** action labels
(`draw`/`play_land`/`cast`/`move_zone`/`shuffle`) when `target == "opponent"` — e.g.
`"Opponent: Cast Counterspell"`. `set_life` must **not** get this generic prefix: it already
produces its own self-describing wording (`"Opponent life: 20 → 17"`,
`goldfish.py:112`) — applying the generic prefix on top would double up into `"Opponent: Opponent
life: 20 → 17"`. `next_turn`'s label is unaffected either way since `target` doesn't apply to it.

**Frontend**:
- `Goldfish.tsx`: new-session dialog gets an optional second deck picker ("Playing against",
  defaulting to none — today's single-deck flow unchanged when left empty).
- `GoldfishSessionPage.tsx`: fetch `opponentDeck` alongside `deck` when
  `data.session.opponent_deck_id` is set. Build **one** merged `cardById` map from both decks'
  cards (card identity doesn't depend on which deck it came from, no meaningful collision risk) —
  used by both boards in the playmat. Keep the two decks' card *lists* separate only for the
  deck-list sidebar, which shows both as two collapsible sections (not a mode toggle — you want to
  reference either deck while planning a line without losing your place).
- `GoldfishPlaymat.tsx`: extract a `GoldfishPlayerBoard` sub-component covering everything that's
  actually self-scoped today — hand, battlefield, zone chips, Draw, Shuffle, and the life counter
  (not just hand/battlefield) — parameterized by `zones: Zones`, `cardById`, `lifeTotal`,
  `onLifeChange`, an `onAction` that already carries the right `target`, an `ownerLabel: string`
  prop (see below), and **`disabled: boolean`** (round 9's `mtg-frontend` pass caught this was
  missing from an otherwise-presented-as-exhaustive list — today's single shared row threads
  `disabled={addNode.isPending}` through Shuffle, Draw, every hand card's Cast/Play button, every
  battlefield card's GY/Hand/Exile buttons, and both `LifeCounter`s, guarding against double-
  submitting while a mutation is in flight; dropping it silently regresses that guard on both
  boards, which is exactly what Step 3's own "behaves identically" bar exists to catch). Only the
  Turn chip and Next Turn button stay outside it, genuinely shared. Keep
  `GoldfishPlayerBoard` **in the same file** as the existing private helpers (`LifeCounter`,
  `ZoneCountChip`, `CardThumb`) rather than a new file — `LifeCounter` isn't exported today, and
  moving it would mean either exporting it or duplicating it for no reason. `GoldfishPlaymat` itself
  becomes a thin wrapper: the existing single-board case becomes the *one* `GoldfishPlayerBoard`
  call (not a separate old code path kept alongside a new component — that would just be two
  implementations to drift apart), with a second conditional call when `state.opponent_zones` is
  present.
  - **Regression risk caught by `mtg-frontend` in round 2, fixed here**: today's bare "Opp" `LifeCounter`
    (tracking `opponent_life_total` with no opponent deck at all — the shipped 3b follow-up
    feature) must **not** get swallowed into a `GoldfishPlayerBoard` that only renders when
    `opponent_zones` exists. The wrapper keeps rendering a standalone `LifeCounter` for
    `opponent_life_total` outside any board whenever `!state.opponent_zones` (today's exact single-
    counter-row behavior, unchanged), and only stops once a real second `GoldfishPlayerBoard`
    exists to carry it instead.
  - **Board-identification gap, independently caught by both `mtg-ux` and `mtg-frontend` in round
    2, extended in rounds 6 and 7 (see below)**: with
    identical MUI styling on both boards and no distinguishing label, a user can't reliably tell
    which board is theirs — and because this feature has zero rules enforcement by design, acting
    on the wrong board fails silently rather than erroring, directly undermining the point of
    testing a specific line. This is functional, not cosmetic, so it's in initial scope (unlike the
    deferred visual-polish pass in Step 5 below): `GoldfishPlayerBoard` takes an `ownerLabel: string`
    prop, rendered as a small heading consistent with the existing `overline` zone headers — `"You"`
    for the self board, the opponent deck's title, **trimmed, falling back to `"Opponent"` when
    that trimmed result is empty** (round 9's `mtg-ux` pass caught that a whitespace-only title,
    e.g. `"   "`, is truthy pre-trim so a naive falsy-check fallback wouldn't catch it — `deck.title`
    has no length/non-empty validation anywhere in the backend model or the `DeckBuilder.tsx` title
    field, confirmed reachable via ordinary use: backspace the title to nothing or a single space
    and wait for autosave. A blank `ownerLabel` reproduces the exact "fails silently" failure mode
    this whole fix exists to prevent, just via an unguarded edge case instead of the pronoun one
    below — trimming before the emptiness check, not just before the pronoun check, closes both
    with the one `.trim()` call rather than two separate guards) for the second — **also falling
    back to `"Opponent"` whenever that same trimmed, case-insensitive title matches any of
    `{"you", "your", "yours"}`** (round 7's `mtg-em` gate caught that a deck
    genuinely titled "You" would otherwise reproduce the exact "You's Hand (N)" bug the two-template
    fix below exists to eliminate, just via user-supplied deck-naming instead of the self-board
    hardcoding that originally caused it — deck titles are free text everywhere else in this
    codebase, nothing stops it, and `Deck.title` has no whitespace-stripping anywhere in the model.
    Round 8's `mtg-architect` pass then caught that a single-string `"you"` comparison didn't close
    the class it claimed to: a deck titled **"Your"** would pass that narrower guard unchanged and
    render `"Your's Hand (N)"` — worse than the original bug, since it's now one apostrophe away
    from the self board's actual `"Your Hand (N)"` text, the exact confusability this whole fix
    exists to prevent. The three-string, case-insensitive, trimmed match is the closed set of
    second-person-pronoun forms that actually violates the "always a proper noun" invariant this
    template depends on — not deliberately narrowed further, since first/third-person pronouns like
    "my"/"our"/"their" produce odd-but-not-confusable-with-anything-else possessives, a lesser,
    purely cosmetic version of the same issue that doesn't carry the same board-identification risk).
    **A single heading at the top of the board isn't enough on its own** — round 6's `mtg-ux` pass
    pointed out each board can grow well past a screen's height once hand/battlefield card grids
    wrap onto multiple rows (`GoldfishPlaymat.tsx:293-384`), so a user scrolled into the middle of a
    board would lose the one identifying label while still looking at unlabeled action buttons —
    exactly the "fails silently" failure mode this fix exists to prevent, not merely a polish gap.
    Fold `ownerLabel` into the `Hand (N)`/`Battlefield (N)` `overline` sub-headers too, so the
    identification signal reappears at every point a user is actually clicking, not just once above
    the fold — **two explicit templates, not one possessive template applied to both** (round 7's
    `mtg-ux` and `mtg-frontend` passes independently caught the same bug: a single `` "{ownerLabel}'s
    Hand (N)" `` template renders as the self board's literal `ownerLabel` value, `"You"`, producing
    ungrammatical `"You's Hand (N)"` — this ships immediately in Step 3, not deferred, since Step 3
    hardcodes `ownerLabel` to `"You"` from the start). Self board: hardcoded `"Your Hand (N)"` /
    `"Your Battlefield (N)"` (the adjective form, independent of `ownerLabel`'s literal string value
    — not derived from it). Opponent board: `` "{ownerLabel}'s Hand (N)" `` / `` "{ownerLabel}'s
    Battlefield (N)" `` (the possessive-noun form, correct as originally written for that case, since
    `ownerLabel` there is always a proper noun — a deck name or the literal `"Opponent"` — never a
    pronoun).
- `types/goldfish.ts`: needs more than originally scoped, per `mtg-frontend`'s review —
  - `GoldfishSession` (`types/goldfish.ts:1-7`) is missing `opponent_deck_id` entirely; add
    `opponent_deck_id: number | null` — **not** `opponent_deck_id?:`. Round 5's `mtg-frontend` pass
    caught that this is the `parent_id`/`turn_number`-style case (a real, always-present, typed
    pydantic field with a default — FastAPI always includes it in the response, just `null` when
    unset), not the `opponent_zones`-style case two bullets below (a genuinely-absent key on
    pre-existing rows, because `state` bypasses model validation). Every other nullable field in
    this file already uses `| null` on an always-present key, never `?:`; this should match.
  - There is **no `Zones` type in this file today** — `GameState` declares the five zone fields
    inline (`types/goldfish.ts:9-17`). `Zones` needs to actually be extracted as its own interface
    that `GameState` extends (mirroring the backend split), not assumed to already exist.
  - `opponent_zones: Zones | null` (not `Zones | undefined`/`opponent_zones?:`) — for any node
    *created from this phase onward*, `.model_dump()` always includes an explicit `opponent_zones:
    null`, so the stricter type reflects the common case accurately. Correction from round 4
    (`mtg-frontend` caught this overclaiming the general case): a session's *pre-existing, untouched*
    nodes (root, opening-hand, anything never followed by a post-3d action) genuinely have the key
    **absent**, not `null`, on read — `GET /sessions/{id}` returns each node's `state` verbatim from
    the DB with no re-validation through `GameState` (see the `GoldfishNodePublic.state: Optional[
    Dict]` note in Ground Truth above), which is exactly the shape the backward-compat test further
    below is built to simulate. Doesn't change the chosen type or any code in Steps 3/4 — `Zones |
    null` still handles both cases fine since nothing does a strict `=== null`/`=== undefined`
    check — it was purely the justifying sentence that overclaimed.

**Opening-hand label wording, pinned down** (was left vague as "or naming an uneven count" before
`mtg-qa`'s review pointed out that's not something a test can assert against): both sides drawing
exactly 7 keeps the shorthand `"Drew opening hands (7 cards each)"`; any other combination
(opponent's library ran out early, or vice versa) uses `"Drew opening hands ({self} card{s};
opponent drew {opp} card{s})"` — e.g. self=7/opponent=4 renders `"Drew opening hands (7 cards;
opponent drew 4 cards)"` (the template's own `{opp} card{s}` clause always keeps the noun — an
earlier draft's worked example dropped it, "opponent drew 4", which `mtg-architect`'s round-3 pass
caught as the template and its own example disagreeing; this is the one corrected, literal string,
not a second competing version). A single-deck session (`state.opponent_zones is None`) keeps
today's exact `"Drew opening hand (N cards)"` wording, untouched.

#### Concrete steps

1. **Test scaffolding first.** Add a `_make_deck_for_user(client, db_session, user, title, cards)`
   helper to `test_goldfish_actions.py` that takes an existing `User` and creates only a deck —
   `mtg-backend` confirmed the existing `_make_deck_with_cards`/`_make_deck_with_many_cards`
   helpers each create a *new* `User` with a unique email/sub, so getting "two decks, one owner" or
   "two decks, different owners" for this phase's tests isn't possible without it. This blocks
   writing any of Step 2's tests, so it comes first.
2. **Backend foundation.** `Zones`/`GameState` split; `opponent_deck_id` added to
   `GoldfishSessionBase` **and** `GoldfishSessionCreate` (see Design above, `index=True` included)
   plus its migration (first FK added via `ALTER TABLE` to an already-existing table in this
   model's history — `add_column` + a separate `create_foreign_key`, see Ground Truth above for
   why that's the precise framing, not "first FK-adding migration" outright; not the
   single-`add_column` shape its predecessors used); `build_initial_state` opponent support;
   session-creation route update including the opponent-deck ownership check, **the same-format
   restriction (product owner decision — see Design above)**, and the combined
   opening-hand deal (one node, both
   players, updated node-creation guard, pinned-down label wording — all per the resolved decision
   above); target-aware `apply_action`/`draw_card` for zone-mutating actions only (`set_life`
   explicitly unaffected); `all_card_ids` extended for labels with the required null-guard on
   `opponent_zones`.

   New tests, incorporating specific gaps `mtg-backend`/`mtg-qa` both caught in the original test
   list rather than the vaguer "opponent-target draw/cast/move_zone/shuffle" it started as:
   - Creating a 2-deck session: the ownership-check rejection case (403); the **format-mismatch
     rejection case (400)** — primary deck and opponent deck with different `format` values,
     confirm the session is *not* created (product owner decision at interview, see Design above —
     new requirement, not present in earlier rounds' review); a same-format pair with both formats
     `None` succeeds (confirms the plain-equality check doesn't special-case unset formats out of
     matching); both hands land with 7 cards each *and* the opponent's library composition matches
     `sorted(deck.cards)` (not just a count — mirrors the existing
     `test_session_auto_shuffles_mainboard_only` pattern, catches a self/opponent deck mix-up
     specifically) *and* the node's label is the exact happy-path string `"Drew opening hands (7
     cards each)"` (round 3's `mtg-qa` pass caught that only the asymmetric cases below had an
     explicit label assertion — the common case needs one too);
     `opponent_deck_id == deck_id` (mirror-match, deliberately unrestricted per the Design note
     above) is covered by **one** test, not the two rounds 4-5 iterated toward — round 6's
     `mtg-backend` pass found that round 5's proposed unit test
     (`assert initial_state.library is not initial_state.opponent_zones.library`) is itself vacuous:
     Pydantic v2 always allocates a fresh list when validating a `List[str]` field, so that
     assertion is `True` unconditionally, for *any* implementation of `build_initial_state`
     — including a hypothetical buggy one that deliberately reused one already-shuffled list for
     both sides before constructing the two `Zones`. By the time you have a constructed `GameState`,
     Pydantic has already decoupled the two lists regardless of what happened before validation, so
     no test at the `GameState`/`Zones` object boundary can actually distinguish a correct
     implementation from an aliased one. The underlying conclusion, once traced this far: the "no
     shared mutable state" risk the Design note originally worried about isn't a risk `build_
     initial_state` could introduce in the first place — it's structurally prevented by Pydantic's
     own validation semantics, not by anything the implementation needs to get right. There's
     nothing to regression-test here, so there's no test for it. What *is* real and worth testing is
     the separate, correctly-scoped claim from round 5: that `target: "self"` action dispatch never
     touches `opponent_zones`, even in the mirror-match case — create the session, `target: "self"`
     draw/shuffle, assert `opponent_zones.library` unchanged from a pre-action snapshot. That's the
     one test this bullet keeps.
   - Opponent-target **draw, play_land, cast, move_zone, shuffle** (all five zone-mutating types,
     not a subset) each asserting the **exact label string**, not just the resulting state — e.g.
     `"Opponent: Cast Card A"` with the real card name resolved, not a raw `card_id` leaking
     through a missed `all_card_ids` fold. For at least one of the five (round 7's `mtg-qa` pass
     caught this was missing, mirroring the same bug class the mirror-match and `next_turn` tests
     already guard against): also confirm the **self side's own zones** (`library`/`hand`/
     `battlefield`/`graveyard`/`exile`) are unchanged from a pre-action snapshot — checking only
     that the opponent side gained the change isn't enough to catch a bug that builds `target_zones`
     from `next_state` instead of `next_state.opponent_zones` (see the reassignment note in Design
     above), which could still produce a correct-looking label while mutating the wrong side. One
     matching self-target assertion *in a session that has `opponent_zones` set* proving the label
     stays unprefixed (the existing suite can't exercise this today since no existing session has
     `opponent_zones`).
   - Opponent-target `draw` against an **empty** `opponent_zones.library` — round 10's `mtg-qa` pass
     caught this was the one edge case with dedicated self-side coverage
     (`test_draw_with_empty_library_does_not_crash`) but no opponent-side equivalent, even though
     `draw_card`'s signature is changing in this exact phase (`GameState` → `Zones`, see Design
     above) and its empty-input path is a distinct success case, not generic validation shared
     across all five action types the way the others' failure paths are. Confirm no crash,
     `opponent_zones.hand` unchanged, and the label reads `"Opponent: Tried to draw with an empty
     library"` (prefixed, not a raw crash).
   - `set_life(target=opponent)` on a plain single-deck session (no `opponent_deck_id` at all)
     still works exactly as today, wording included (`"Opponent life: 20 → 17"`, proving no
     double-prefix).
   - A zone-mutating opponent-target action against a session with no `opponent_deck_id` returns
     400 with the exact `detail` (`"This session has no opponent deck"`), explicitly *not* tested
     for `set_life`.
   - Opening-hand asymmetry, three cases, each asserting the exact pinned-down label wording above
     (`draw_opening_hand` draws each side independently and isn't symmetric by construction):
     opponent deck with an empty mainboard (0 cards — confirm no crash, `opponent_zones.hand ==
     []`); **both** decks' libraries at exactly 1 card, not just the opponent's — round 8's `mtg-qa`
     pass caught that the pinned label template has two independent singular/plural branches
     (`{self} card{s}` and `{opp} card{s}`), picked 1 for the opponent side only, and round 8's
     `mtg-em` gate then caught that self never hits exactly 1 across any of the three cases (7 in
     cases 1-2, 0 in case 3) — a template that always rendered the plural form on the self side
     specifically would still pass every test undetected, same bug class as the self/opponent
     zone-mutation asymmetry already fixed in rounds 6-7, just for a string-formatting branch
     instead. One case with both sides at exactly 1 forces both singular branches at once
     (`"Drew opening hands (1 card; opponent drew 1 card)"`), tighter than a fourth case per this
     doc's own YAGNI convention; and — pinned specifically, not just "the
     player's library small," per round 3's `mtg-qa` pass — the **primary deck's library empty
     (0 cards) with the opponent's full**, since that's the exact scenario the updated
     node-creation guard (`if opening_state.hand or (opening_state.opponent_zones and
     opening_state.opponent_zones.hand):`, see "Why this one, and why now" above — round 6's
     `mtg-architect` pass caught this pointer saying "Design" when the guard is actually defined
     there, not in Design) exists to handle: under the old
     self-hand-only guard this would have produced zero nodes and silently dropped the opponent's
     dealt hand entirely, same failure mode as `test_get_session_tree_starts_with_auto_created_root`
     documents for the pre-3d single-deck empty-library case.
   - A single-deck session's opening-hand node label is unchanged character-for-character from
     today's wording.
   - **Backward-compatibility proof, not just inference**: one test manually constructs a
     `GoldfishNode` with a hand-built `state` dict that's missing the `opponent_zones` key
     entirely (simulating a genuinely pre-3d row, which no test creating a fresh session can
     produce) and confirms an action against it still succeeds and stores `opponent_zones: null`.
     Also one test asserting `set(root["state"].keys())` for a plain single-deck session equals
     exactly `{"library", "hand", "battlefield", "graveyard", "exile", "life_total",
     "opponent_life_total", "opponent_zones"}` — **eight** keys, including `opponent_zones` itself
     (round 6's `mtg-qa` pass caught that leaving this unpinned invited writing the test against the
     old seven-key set instead: `.model_dump()` has no `exclude_none` anywhere in `goldfish.py`, so
     it always includes `opponent_zones: None` for any node created post-3d, single-deck or not —
     same fact the backward-compat bullet just above already states correctly). "Byte-for-byte
     unchanged" describes the *seven pre-existing* fields staying flat and identically shaped, not
     the total key count staying at seven — this is the one assertion that actually operationalizes
     that claim, rather than leaving it as an inference from unrelated field checks continuing to
     pass.
   - **`next_turn` never touches the opponent side in a 2-deck session** — round 6's `mtg-qa` pass
     caught that this is a headline, explicitly-resolved interview decision (see "Why this one, and
     why now" above: "`next_turn` stays a single shared counter and does **not** auto-draw for the
     opponent") with no test locking it in, unlike nearly every other stated behavioral guarantee in
     this list. True "for free" today since the route's `next_turn` branch only ever calls
     `draw_card` on the self side — but exactly the kind of implicit guarantee a later "helpful"
     symmetry-driven change could silently break without a test to catch it. One test: in a 2-deck
     session, `next_turn`, assert `opponent_zones` is byte-for-byte unchanged from before the action.
   - Full existing suite must stay green with zero changes.

   Per Phase 3a's own recorded experience, Alembic autogenerate hasn't worked directly against this
   environment's real Postgres — expect to hand-write the migration and verify via `alembic
   upgrade head` / `downgrade -1` inside the running backend container, not autogenerate-and-trust.
3. **Frontend, part one — refactor only, one deliberate visible exception.** Extract
   `GoldfishPlayerBoard` out of `GoldfishPlaymat.tsx` as described above (including the
   standalone-opponent-`LifeCounter` preservation for the no-opponent-deck case) and confirm the
   existing single-deck goldfish UI behaves identically before adding anything new — isolates "did
   the extraction break the working case" from "does the new case work," rather than shipping both
   changes at once. Round 6's `mtg-ux` pass caught that "renders... identically" overstated this:
   the always-on `"You"`/`"Your Hand (N)"`/`"Your Battlefield (N)"` labels (grammar corrected per
   round 7, see Design above) are a real, new, user-visible addition to every existing single-deck
   session's playmat, not a no-diff refactor — correct as the wording now stands ("behaves
   identically," not "renders"), and it's fine for this one labeling change to ship alongside the
   refactor rather than waiting for Step 4, since it's static
   text with no interactive/functional difference to isolate a regression in. Extract the `Zones`
   type in `types/goldfish.ts` as part of this step (needed by `GoldfishPlayerBoard`'s props
   regardless of whether an opponent exists yet); `GoldfishPlayerBoard` takes its `ownerLabel` prop
   from the start, hardcoded to `"You"` on the only board that exists at
   this point.
4. **Frontend, part two — new feature.** Add `opponent_deck_id` to the `GoldfishSession` type
   **and `opponent_zones: Zones | null` to `GameState`** (round 10's `mtg-frontend` pass caught that
   Design lists three `types/goldfish.ts` changes but only two — the `Zones` extraction in Step 3,
   `opponent_deck_id` here — were ever assigned to a specific step; this one was never explicitly
   placed anywhere despite this same step's next clause requiring `state.opponent_zones` to already
   exist as a typed field); opponent deck picker on session creation; `GoldfishSessionPage.tsx`
   fetching/merging both decks into one `cardById`; second `GoldfishPlayerBoard` render when
   `opponent_zones` is present, with
   its real `ownerLabel` (the opponent deck's title, falling back to `"Opponent"`, and to the
   pronoun-collision fallback per the Design section above — round 8's `mtg-frontend` pass noted
   Step 3's cross-references its own round-7 fix inline and this step should do the same for the
   guard, since it's the step that actually wires in a real deck-derived `ownerLabel` value for the
   first time); two-section deck list sidebar.
5. **Polish.** Verify tree labels read cleanly with both sides acting, specifically eyeballing a
   long opponent label alongside a tracker summary in `GoldfishTree.tsx` — `mtg-frontend` noted its
   `LEVEL_HEIGHT` row spacing is a fixed constant independent of actual rendered text height, so a
   long wrapped label could visually crowd the row below it; not a code change unless it's actually
   a problem in practice. Beyond the `ownerLabel` fix already folded into Steps 3-4, a dedicated
   `mtg-ux` visual-design pass on the two-board layout (spacing, dividers, responsive stacking) is
   deliberately *not* in this step's initial scope — `mtg-ux`'s review confirmed the deferral holds
   for everything except the board-identification gap already addressed above. Every prior
   sub-phase here (3a, 3b) shipped a plain first cut and iterated on real friction from actually
   using it; revisit only if real usage surfaces an actual layout problem.

#### Verify (once built)

Live against the docker stack: attempt creating a 2-deck session with mismatched-format decks and
confirm it's rejected (product owner requirement, added at interview), then create a real
same-format 2-deck session, confirm both opening hands deal per the
pinned-down wording above, draw/cast/move/shuffle on both sides, confirm the board-identification
labels ("You" / opponent's deck title) actually make it obvious which board is which — including
one run where the opponent deck is named/renamed to `"You"` (or `"your"`/`"yours"`), confirming the
header and `Hand (N)`/`Battlefield (N)` sub-headers fall back to `"Opponent"` rather than rendering
the confusable `"You's Hand (N)"`/`"Your's Hand (N)"` (round 8's `mtg-ux` pass caught this case had
no automated coverage possible — no frontend test infra exists for this phase per the note below —
and no manual check called for it either, the only safety net that could have caught the guard
being silently dropped during implementation), and a second run where the opponent deck's title is
renamed to whitespace-only (e.g. a single space), confirming the header **and** `Hand (N)`/
`Battlefield (N)` sub-headers all fall back to `"Opponent"` rather than a blank heading/sub-header
at any of the three (round 10's `mtg-ux` pass caught that this sentence had quietly dropped the
explicit three-site enumeration its pronoun-case sibling above uses, in favor of a vaguer "a blank
heading/sub-header" that a check could satisfy by looking at only one of the three sites — same
underlying rationale as the pronoun case though: no automated coverage, so a missed implementation
of the trim-then-check fix would otherwise ship unnoticed) —
confirm `set_life(target=opponent)` still works on an existing plain single-deck session, confirm
tree labels distinguish self vs. `"Opponent: "` actions without double-prefixing `set_life`,
confirm an existing single-deck session (created before this phase) still opens and plays exactly
as before, prune a node in a 2-deck session and confirm cascade-delete still works (`mtg-qa`
confirmed this needs no new backend logic — `delete_node` only walks `parent_id`/`id`, never
inspects `state` JSON content — but worth one live click-through since it's new UI surface), and —
round 10's `mtg-architect` pass caught this was the one Design-flagged, automated-coverage-
impossible risk that hadn't gotten a matching Verify bullet yet, the same category as the two
`ownerLabel` fixes above — rapidly double-click Draw (or Shuffle, or a hand card's Cast button) on
the **opponent** board specifically while a request is in flight, confirming the controls disable
on both boards during the pending window and only one node gets created, not just that the action
eventually succeeds (the `disabled` prop is wired via a separate `GoldfishPlayerBoard` call site
for the opponent board, Step 4, distinct from the self board's — exactly where dropping the prop on
only one of the two instantiations would be easy to miss and impossible to catch without a live
check, per the same reasoning as the two fixes above it).

No frontend automated test coverage is planned for this phase (`mtg-qa` noted this is a
pre-existing gap across the whole frontend, not something newly introduced here) — Steps 3-4 are
verified by this manual pass, same as every prior frontend change in this codebase.

### Shipped, 2026-08-11: as designed, one scope expansion found during Verify

Built exactly as designed above, routed `mtg-backend` (Steps 1-2) then `mtg-frontend` (Steps 3-4),
sequenced that way since the frontend's opponent board needs the backend's real response shape to
verify against live, not just to compile against a written-down type. `cd backend && uv run pytest`
(104 passed, zero regressions) and `uv run ruff check .` clean; `npx tsc -b` and `npx eslint .`
clean on the frontend. Migration (`1d1448d72c58`) verified against the running
`deck_builder-backend-1`/`deck_builder-db-1` containers — `\d goldfishsession` confirmed the
nullable `opponent_deck_id` column, its index, and `fk_goldfishsession_opponent_deck_id_deck`, all
matching the hand-written `add_column` + `create_foreign_key` shape the Ground Truth section called
for (not autogenerate, per Phase 3a's own precedent).

**One deviation, a real scope expansion, not a plan miss**: the plan's own Verify section requires
rapid-double-click-while-pending to produce exactly one node. Testing that live surfaced a genuine
pre-existing race — `disabled={addNode.isPending}` only takes effect once React re-renders with the
mutation's updated `isPending`, and a fast enough double-click fires both POSTs before that commits.
Confirmed via network logs this reproduces identically on the untouched single-board case, so it
predates this phase and isn't something the `GoldfishPlayerBoard` split introduced. Since the plan's
own Verify bar named this scenario explicitly, fixed it rather than shipping a phase that fails its
own stated check: `GoldfishSessionPage.tsx` gained a synchronous `submittingRef` guard around
`addNode.mutate`, checked at the moment of submission rather than relying on render timing. Re-
verified after the fix: exactly one POST per double-click on both the self and opponent boards.

**Live-verified against the docker stack** (`deck_builder-frontend-1`/`-backend-1`/`-db-1`,
confirmed separately from the implementing agent's own report): opened a real 2-deck session
(`lathril` vs. a same-format second deck) — both boards render (`YOU` / the opponent deck's actual
title), the tree shows `"Opponent: Cast Sol Ring"` correctly prefixed alongside unprefixed self-side
labels, and the asymmetric opening-hand node reads the exact pinned wording,
`"Drew opening hands (7 cards; opponent drew 1 card)"`. Mismatched-format creation, the `"You"`/
whitespace-only opponent-title fallback (all three label sites), an untouched pre-3d single-deck
session, and cascade-delete pruning were all exercised by the implementing agent and are recorded in
its own report; the render/label/tree checks above were independently re-confirmed rather than taken
on trust.

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

## Phase 5 — AI-assisted card search for deck building (planned, not started)

### Why this one, and why now

Raised directly by the user, picked up ahead of Phase 3c (explicitly parked — see Status above) as
the thing actually being worked on next. Today's card discovery on the deck-building page is
Scryfall keyword/operator search (`search_cards`, `DeckBuilderSearch.tsx`) — exact-text and
structured-field matching only. The user wants to ask synergy-style natural-language questions a
keyword search can't answer: "cards that benefit from artifacts leaving the battlefield," "cards
that deal damage when an artifact enters the battlefield" — queries about what a card *does*
semantically, not what text it contains literally (neither example phrase need appear verbatim in
matching cards' oracle text). User's own opening framing for how to build this: a combination of
SQL search and a vector DB of the MTG cards.

### Status

Design pass complete (`mtg-architect`, 2026-08-12). Two questions below are flagged for the
product-owner interview before implementation starts — everything else is a decided
recommendation, not a menu of options.

### Ground truth this plan is built on

Corrections/refinements against the framing this design pass was handed, checked against actual
code, not assumed:

- `deck_advisor_agent` (`backend/app/ai/agents/deck_advisor/deck_advisor_agent.py`) is a `make_agent`
  call with exactly one tool, `search_cards`. Its prompt already establishes the discipline this
  phase reuses: never cite a card `search_cards` didn't actually return, pass the deck's format to
  `search_cards` for legality, don't re-look-up cards already given in context.
- `search_cards` (`backend/app/ai/tools/cards.py:54-88`) already **is** the "SQL search" half of
  the user's own framing, not something new to build: plain-name queries hit the local `Card`
  table (`ILIKE`, `_search_local`, line 30) first, and anything using Scryfall's `key:value`
  operator syntax (`t:creature c:red pow>=5`, ...) — itself a structured/filtered query — falls
  back to live Scryfall. `_format_card` (line 38) already formats a plain dict (`name`,
  `mana_cost`, `type_line`, `oracle_text`, optional `legalities`) into the tool's return text —
  reusable as-is for the new semantic tool's output, just called with `format=None` since Chroma
  metadata won't carry legality (see below).
- `Card` (`backend/app/models/card.py:4-22`) has no `keywords` field — the original framing's
  "oracle text + type line + keywords" isn't buildable as written. Not a real gap: Scryfall's
  `oracle_text` already spells out keyword ability names inline for the overwhelming majority of
  cards (e.g. a flier's oracle text literally starts `"Flying"`), so `name + type_line +
  oracle_text` (all three already populated by Phase 4's ingestion) is sufficient embedding input
  without adding a new column.
- `rag/rules.py`'s `RulesRAG` (`backend/app/ai/rag/rules.py`) is the only existing `RAGService`
  implementation and the direct precedent for a card-oracle-text RAG: it constructs its own
  `SentenceTransformerEmbedder()` and a `ChromaVectorStore(embedding_model=self.embedder)`
  (default `collection_name="mtg_rules"`), and is exposed as a bare module-level singleton
  (`rules_rag = RulesRAG()`), not a class instantiated per-call. `ChromaVectorStore.__init__`
  (`backend/app/ai/vector_store/chroma.py:13-19`) already takes `collection_name` as a constructor
  arg — standing up a second collection needs zero changes to that class, just a different name.
- **Resource note the original framing didn't raise, worth flagging now rather than after two
  full model loads ship**: `SentenceTransformerEmbedder()` (`backend/app/ai/vector_store/
  embedding.py`) loads a real ~440MB sentence-transformer model (`BAAI/bge-base-en-v1.5`) into
  memory on construction. `RulesRAG.__init__` constructs its own instance today; a naive `CardRAG`
  built the same way would load a **second, fully redundant copy of the same model** into the same
  process. This is the same shape of duplication that triggered `make_agent`'s extraction in Phase
  1 (two call sites, real repeated cost, not speculative) — see Design below for the fix.
- `run_ingestion()` in `backend/app/ai/ingestion/scryfall_ingestion.py:103-122` is a fast,
  Postgres-only bulk upsert (44s for 116,568 rows per Phase 4's live run) with **no ML inference in
  it at all**. `rules_ingestion.py` is already a fully separate script from it, populating a
  different Chroma collection — this phase's ingestion is the same shape of "separate concern,"
  not a new pattern.
- `api/routes/cards.py`'s `local_search_cards` (lines 34-64) already has the exact dedup-by-name
  query this phase needs for embedding: `select(func.min(Card.id)).where(...).group_by(col(Card.name))`
  collapses ~116k printings down to one row per unique card name, "matching Scryfall's own default
  `unique=cards` search behavior" (its own docstring). Embedding every printing individually would
  be ~4x more embedding work for zero search-quality benefit (near-duplicate oracle text crowding
  results) — reuse this exact grouping, don't re-derive it.
- `api/routes/ai.py`'s `/suggest` handler (line 68) and `_build_deck_context` (line 24) already do
  everything a synergy-search request needs: ownership check, `Deck` fetch, format threaded into
  context. No new route is needed for this phase — see Design below, this is a correction to the
  original framing's assumption that a new `/api/ai/...` route was required.
- Frontend: `DeckBuilder.tsx`'s right pane (`rightPaneTab`, line 95; tab buttons, lines 626-644)
  already toggles between `DeckStats` and `DeckAdvisor` (`backend` confirms this is the Phase 1 tab,
  not `AgentChat.tsx`). `DeckAdvisor.tsx` posts `{deck_id, query}` to `/ai/suggest` and renders a
  plain chat thread (`ChatBubble`/`ChatInput`) — no structured/clickable card results exist
  anywhere in this codebase's chat UI today; `DeckBuilderSearch.tsx`'s Autocomplete-with-click-to-add
  is a completely separate component/interaction pattern used only for exact-name search.

### Design

**Recommendation on the core question (agent/tool shape): extend `deck_advisor_agent` with one new
tool. Do not create a new agent, route, schema, or frontend tab.**

Reasoning: the only real argument for a second agent is that a synergy question ("cards that deal
damage when an artifact enters") isn't "improve this deck," it's open card discovery — a
plausibly different *intent*. But `rules_agent` already sets the precedent that one agent can juggle
several distinct tools/query shapes under one prompt (rules lookup vs. card rulings vs. glossary
terms, three different tools, one agent, one prompt-level dispatch) — nothing here is architecturally
different from that. `deck_advisor_agent`'s existing **Suggestions**/**Cuts**/**Summary** format
isn't a hard schema, it's prompt guidance; a synergy answer fits naturally under **Suggestions**
("matching cards"). A second agent would mean a new subfolder, a new route, new schemas, and either
a new frontend tab or awkwardly hiding it behind the existing one — real new surface area for a
capability that's still fundamentally "help me with the deck I have open," not a distinct product
concern. This is the direct YAGNI call per this repo's own convention (a new agent needs a concrete
reason it can't share, not just response-format taste) — same bar the `make_agent` factory's own
history in this file already established.

**Two tools, LLM combines them itself** (the user's "SQL + vector DB" framing, realized literally):
`deck_advisor_agent.tools` becomes `[search_cards, search_cards_semantic]`. `search_cards` is
already the SQL/structured half (unchanged). `search_cards_semantic` (new,
`backend/app/ai/tools/cards.py`, alongside `search_cards`) is the vector half:

```python
async def search_cards_semantic(query: str, k: int = 10) -> str:
    """
    Finds cards by what they DO semantically -- synergy, mechanics, effects --
    rather than exact oracle-text wording. Use for questions a name/text
    substring search can't answer (e.g. "cards that benefit when an artifact
    leaves the battlefield"). Does NOT return legality -- verify a candidate's
    format legality via 'search_cards' (passing the deck's format) before
    recommending it.
    """
    docs = card_rag.query(query, k=k)
    ...  # format each result via the existing _format_card(card, format=None)
```

Prompt addition to `deck_advisor_agent`'s `PROMPT`: a new instruction telling it to use
`search_cards_semantic` instead of `search_cards` for synergy/mechanic-style questions where the
exact phrase isn't expected to appear verbatim in a matching card's text, and — critically, to keep
this phase's citation discipline intact — to still verify a semantic hit's exact name/cost/legality
via `search_cards` before citing it, since `search_cards_semantic` can't carry legality data (see
below). This is additive to the existing prompt, not a rewrite.

**No new route, no new schema.** `POST /ai/suggest` (`SuggestCardRequest{deck_id, query}` /
`SuggestCardResponse{response}`) is reused as-is — the route doesn't know or care which tools the
agent decides to call. `_build_deck_context`'s existing stats/curve computation is harmless overhead
on a pure discovery question (already in-memory, no extra I/O), not worth special-casing out.

**No new frontend surface required.** `DeckAdvisor.tsx`'s existing chat tab already sends arbitrary
natural-language `query` text to `/ai/suggest` — a user can ask a synergy question in the exact same
box they use today for "what should I add," no new tab/component/route wiring needed. The one
plausible copy tweak (mentioning synergy questions in the placeholder/intro text,
`DeckAdvisor.tsx:31`/`:101`) is small enough to leave to whoever implements this, not something this
blueprint needs to pin down. **This is the one place worth flagging for the interview anyway** — see
Open questions below — because "keep reusing free text" vs. "build a structured, click-to-add result
list" is a real product/UX tradeoff this blueprint can't resolve unilaterally even though it can
recommend a default.

**Vector collection**: a second `ChromaVectorStore` collection, `mtg_cards`, alongside the existing
`mtg_rules` one — zero changes needed to `ChromaVectorStore` itself, just a different
`collection_name`. New `backend/app/ai/rag/cards.py`:

```python
class CardRAG(RAGService):
    def __init__(self, embedder: Optional[EmbeddingModel] = None):
        self.embedder = embedder or SentenceTransformerEmbedder()
        self.store = ChromaVectorStore(embedding_model=self.embedder, collection_name="mtg_cards")

    def query(self, text: str, k: int = 5) -> List[str]: ...  # same shape as RulesRAG.query

card_rag = CardRAG(embedder=shared_embedder)
```

**Shared embedder, fixing the redundant-model-load issue flagged in Ground Truth above**: add a
module-level `shared_embedder = SentenceTransformerEmbedder()` to `backend/app/ai/vector_store/
embedding.py`, and change `RulesRAG.__init__` to accept an optional injected `embedder` (defaulting
to constructing its own, so nothing breaks if called standalone) the same way `CardRAG` does above.
`rag/rules.py`'s `rules_rag = RulesRAG(embedder=shared_embedder)` and `rag/cards.py`'s `card_rag =
CardRAG(embedder=shared_embedder)` then both point at the one loaded model instead of two. This is a
small, in-scope fix (a few lines), not a speculative refactor — it's the actual second call site
that makes the duplication real, same trigger condition as the `make_agent` extraction.

**Embedding source and ID**: per card *name* (not per printing) — `name + "\n" + type_line + "\n" +
oracle_text` as the embedded text, using the same `func.min(Card.id)`-grouped-by-name query
`local_search_cards` already uses (see Ground Truth). Use the **card's name itself as the Chroma
document ID**, not the representative row's Scryfall UUID — Chroma IDs are opaque strings with no
format requirement, and a name-keyed ID makes re-embedding idempotent regardless of which specific
printing happens to be selected as "representative" on a given run (new printings, or a different
`min(id)` winner, just overwrite the same vector on the next embedding pass — no drift, no
duplicate vectors accumulating across runs).

**Pipeline hook: a separate, manual ingestion script, not bolted onto `scryfall_ingestion.py`.**
New `backend/app/ai/ingestion/card_embedding_ingestion.py`: reads from the already-refreshed local
`Card` table (not Scryfall directly — `scryfall_ingestion.py` is already the source of truth once
it's run), groups by name, builds one `ProcessedChunk` per unique card, embeds via
`shared_embedder`, upserts in batches into the `mtg_cards` collection via `ChromaVectorStore`. Entry
point `uv run python -m app.ai.ingestion.card_embedding_ingestion`, run by hand, same "no scheduling
infra" decision Phase 4's interview already settled — this phase doesn't reopen that, it inherits
it. Deliberately **not** folded into `scryfall_ingestion.py`'s `run_ingestion()`: that function is a
fast, pure-DB upsert (44s for 116k rows against a live run); embedding tens of thousands of card
texts through a local sentence-transformer model is a materially slower, CPU/MPS-bound step, and
silently making every future `Card`-table refresh also pay that cost would be a real, easy-to-miss
regression to the workflow Phase 4 optimized for. Keeping them as two explicit, separately-run
scripts mirrors the existing `rules_ingestion.py` vs. `scryfall_ingestion.py` separation exactly —
not a new pattern.

**Staleness/re-sync**: same manual cadence as Phase 4 — re-run `card_embedding_ingestion.py` by hand
after `scryfall_ingestion.py` whenever the card data's been refreshed and the vector index should
catch up. Idempotent by construction (name-keyed upsert, see above), so re-running it is always
safe, same as `upsert_cards`' own idempotency. No new scheduling question to resolve here — Phase
4's interview outcome already covers this; this phase just adds a second manual script to the same
already-accepted "run by hand" workflow.

**Legality**: deliberately **not** stored in Chroma metadata (it would go stale independently of the
`Card` table's own refresh cadence, and duplicate data already served correctly by `search_cards`).
`search_cards_semantic` returns name/type/oracle-text only; the updated prompt instructs the agent
to verify any semantic-search candidate's legality via `search_cards` (which already does this
correctly) before citing it — composing the two tools is exactly the point, not a limitation to
route around.

### Open questions for the product-owner interview

1. **Result presentation: reuse the existing free-text advisor chat, or build a structured,
   click-to-add result list?** Recommended default: reuse `DeckAdvisor.tsx`'s existing chat UI
   as-is (zero new frontend surface, ships as a backend+prompt+ingestion change only). The
   alternative — matching results rendered as clickable cards (closer to `DeckBuilderSearch.tsx`'s
   Autocomplete, one-click add-to-deck) — is a real, meaningfully bigger lift: `search_cards_semantic`
   would need to return structured data, not formatted text, `/ai/suggest`'s response shape would
   need to change (or a second endpoint added after all), and a new result-list component would be
   needed. Worth asking directly rather than assuming free text is "good enough" — this is a genuine
   product/UX call, not a technical one.
2. **Ingestion scope: embed literally everything in the local `Card` table (tokens, Un-set/silver-
   border joke cards, art-series cards, memorabilia — whatever Scryfall's `default_cards` bulk file
   contains and Phase 4 already ingested unfiltered), or filter down to "real," tournament-legal-set
   cards only?** Recommended default: unfiltered, matching the local `Card` table's own existing
   scope — nothing in this codebase filters by `set_type` today (confirmed: no such field even
   exists on `Card`), so an unfiltered card-vector index is the *consistent* choice, not a new
   problem this phase introduces. Filtering would require adding a new `Card.set_type` field
   upstream in Phase 4's ingestion first — worth asking only if joke/promo-card pollution in
   synergy-search results turns out to bother the user in practice; not a blocker for v1.

### Interview outcome (resolved before writing code, per-phase process)

Both open questions above resolved by interview, 2026-08-12 — both took the blueprint's own
recommended default, no deviation:

1. **Result presentation: reuse the existing free-text advisor chat.** No new frontend surface —
   `DeckAdvisor.tsx`'s chat tab is unchanged; synergy questions just work in the same input as
   today's "what should I add" queries. If free-text answers turn out to feel insufficient once
   this ships (e.g. the user wants one-click add-to-deck on a synergy hit), the structured
   click-to-add list from the Design section's alternative is the fallback, not designed further
   now.
2. **Ingestion scope: unfiltered**, matching the local `Card` table's existing scope exactly. No
   new `Card.set_type` field, no filtering logic in `card_embedding_ingestion.py`.

Implementation now proceeds per the Design section above: `search_cards_semantic` tool, `CardRAG`/
`mtg_cards` collection, shared embedder fix, `card_embedding_ingestion.py`, and the
`deck_advisor_agent` prompt update — no route/schema/frontend changes.

### Shipped: built exactly per Design, one real bug caught on the live run

Built per the Design section above, no deviation on the architecture. `backend/app/ai/vector_store/
embedding.py` gained the module-level `shared_embedder` singleton; `RulesRAG.__init__`
(`backend/app/ai/rag/rules.py`) now accepts an optional injected `embedder`, and its own module-level
`rules_rag` singleton passes `shared_embedder` — one loaded sentence-transformer model shared by both
RAG services, not two. New `backend/app/ai/rag/cards.py`'s `CardRAG` is the same shape, pointed at a
second `mtg_cards` Chroma collection, exposed as `card_rag = CardRAG(embedder=shared_embedder)`. New
`search_cards_semantic` (`backend/app/ai/tools/cards.py`) queries `card_rag` and reuses the existing
`_format_card(card, format=None)` helper — a small `_doc_to_card()` parses the embedded
`name\ntype_line\noracle_text` document back into the dict shape `_format_card` expects, since
`CardRAG.query()` returns plain text (same shape as `RulesRAG.query`), not structured metadata.
`deck_advisor_agent` (`backend/app/ai/agents/deck_advisor/deck_advisor_agent.py`) now registers both
`search_cards` and `search_cards_semantic`, with an additive prompt instruction (point 6) telling it
when to reach for the semantic tool and to still verify any hit's legality via `search_cards` before
citing it — the existing citation-discipline instructions (points 1-5) are untouched.

New `backend/app/ai/ingestion/card_embedding_ingestion.py` mirrors `rules_ingestion.py`'s shape as a
separate manual script (`uv run python -m app.ai.ingestion.card_embedding_ingestion`), not folded
into `scryfall_ingestion.py`. `fetch_unique_cards()` reuses `local_search_cards`'s exact
`func.min(Card.id)`-grouped-by-name query; `_chunk_for_card()` embeds `name + "\n" + type_line + "\n"
+ oracle_text` keyed by the card's name (not its Scryfall UUID) for idempotent re-runs;
`embed_and_upsert()` batches (500/batch) through `shared_embedder` into `card_rag`'s store. Unfiltered,
per the interview outcome — no set_type/token/joke-card filtering.

One real bug the unit tests (mocked embedder/store) couldn't catch, only surfaced by running against
the live stack: `ChromaVectorStore.upsert` passes each `ProcessedChunk.metadata` straight through to
Chroma, and Chroma's `upsert` **rejects an empty metadata dict outright**
(`ValueError: Expected metadata to be a non-empty dict, got 0 metadata attributes`) — the first live
run died on batch 1. `ProcessedChunk.metadata` defaults to `{}` and `_chunk_for_card()` wasn't setting
it. Fixed by giving each chunk `metadata={"name": card.name}` (not otherwise used today, just enough
to be non-empty) and added a unit test asserting `chunk.metadata` is truthy so this can't silently
regress. Also caught along the way: a first pass tried validating retrieval with a raw `chromadb`
client's `collection.query(query_texts=...)`, which used Chroma's own default embedding function
(384-dim MiniLM) instead of the app's `bge-base-en-v1.5` (768-dim) — `InvalidArgumentError: Collection
expecting embedding with dimension of 768, got 384`. Not a bug in the shipped code (confirms the
stored vectors are the correct 768-dim shape); just the wrong way to spot-check retrieval outside the
app's own `CardRAG`/`search_cards_semantic` code path, corrected by testing through
`search_cards_semantic` directly instead.

**Live-verified against the real stack** (`deck_builder-backend-1`/`mtg-chromadb`/`deck_builder-db-1`,
2026-08-12): the local `Card` table already held 116,694 rows (from a prior `scryfall_ingestion.py`
run) across 36,063 unique names. Ran `card_embedding_ingestion.py` inside the backend container
against real Postgres and real Chroma — completed in ~74 minutes on CPU (this container has no
GPU/MPS, unlike local dev), logging `Card embedding ingestion complete: 36063 cards upserted`.
Confirmed the `mtg_cards` collection's count (`36063`) matches the unique-name count exactly — no
duplicate vectors. Called `search_cards_semantic` directly (through the real tool, not mocked) for
both of the user's own example queries ("cards that deal damage when an artifact enters the
battlefield", "cards that benefit from artifacts leaving the battlefield") — both returned real,
plausible artifact-synergy cards (e.g. *Letter Bomb*, *Wake the Past*, *Portcullis*) with no crash and
no legality field, confirming the full pipeline (embed → store → query → format) works end-to-end
against live data, not just mocks.

Test coverage added: `search_cards_semantic` formatting/no-results (`test_cards_tool.py`),
`card_embedding_ingestion.py`'s dedup-by-name query, chunk-building, and batched embed/upsert logic
against a mocked embedder/store (new `test_card_embedding_ingestion.py`), and a small
`test_deck_advisor_agent.py` confirming the agent registers both tools and the prompt mentions
verifying semantic hits. `cd backend && uv run pytest` (112 passed) and `uv run ruff check .` both
clean on every file this phase touched (two pre-existing, unrelated files already needed
`ruff format` before this phase started — left alone, out of scope).

No deviation from the Design section's route/schema/frontend scope: `POST /ai/suggest`,
`SuggestCardRequest`/`SuggestCardResponse`, and `DeckAdvisor.tsx` are all untouched, exactly as
decided.

---

## Phase 6 — Per-card synergy lookup (shipped, 2026-08-16)

### Why this one, and why now

Second-order follow-up to Phase 5, raised directly by the user in a 2026-08-15 brainstorming
session as the first of two features to build next (Phase 7 below is the second). Phase 5 shipped
`search_cards_semantic`/`CardRAG` and wired synergy-style questions into `deck_advisor_agent`'s
free-text chat — but only reachable by typing a question. This phase adds a lower-friction trigger:
click a card already in the deck and get synergy suggestions seeded from that specific card,
without typing anything.

### Status

Design pass complete (`mtg-architect`, 2026-08-15). One open question flagged for the
product-owner interview before implementation — everything else is a decided recommendation.

### Ground truth this plan is built on

- **Correction to the original framing**: `frontend/src/components/DeckListItem.tsx` is *not* the
  per-card row inside a deck — it's the per-*deck* row on the deck list page (`DeckListItem.tsx:29-
  132`, props `{deck: Deck, onDelete}`, navigates to `/decks/:id`). The actual per-card row inside
  deck-building is `DeckCard.tsx`, rendered as `DeckCardComponent` in `DeckBuilder.tsx:596-611`.
  This design is built against `DeckCard.tsx`.
- `DeckCard.tsx` already has the exact trigger surface this needs: a hover-revealed Actions Row
  (`DeckCard.tsx:246-343`) with icon-button callbacks (quantity, board-move menu, delete), each
  `e.stopPropagation()`-guarded. A new "find synergies" icon button fits this existing idiom
  directly — no new interaction paradigm.
- `DeckBuilder.tsx` already has a two-tab right pane (`rightPaneTab: "stats" | "advisor"`, state at
  line 95, tabs at lines 626-644) and an established "disabled until deck is saved" convention for
  deck-scoped actions (the goldfish practice-mode button, lines 486-504: `disabled={!deck?.id}` +
  explanatory `Tooltip`). Both reusable as-is.
- `DeckAdvisor.tsx` posts `{deck_id, query}` to `/ai/suggest` via `useMutation` (lines 40-60) and
  appends both sides of the exchange as chat bubbles via `handleSend` (lines 62-65). `ChatInput.tsx`
  owns its own uncontrolled input state and only exposes `onSend(message: string)` — there's no
  existing way to pre-fill it from a parent, so a card-triggered query means calling `handleSend`
  directly, not touching `ChatInput.tsx`.
- `POST /ai/suggest` (`ai.py:68-104`) and `_build_deck_context` (`ai.py:24-65`) already do
  everything a synergy query needs: ownership check, `Deck` fetch, stats, and a context string of
  every mainboard card. `deck_advisor_agent`'s prompt (instruction 6) already tells it to reach for
  `search_cards_semantic` on synergy-style questions and verify legality via `search_cards` before
  citing — this phase's job is producing a query and sending it through this already-working
  pipeline, not building new agent capability.
- **Real gap found while grounding this**: `_build_deck_context` only includes `board == "main"`
  cards (`ai.py:25`) — a synergy click on a sideboard/maybeboard/commander card wouldn't have its
  oracle text in the agent's context, only its bare name. Fix: build the query **client-side** with
  the card's own oracle text/type baked in (`DeckCard.tsx`'s `deckCard.card` is already a full
  `ScryfallCard`), which is board-agnostic and also matches what `search_cards_semantic` actually
  embeds (`name\ntype_line\noracle_text`) — better than a bare name for vector search quality too.
- `SuggestCardRequest{deck_id, query}` / `SuggestCardResponse{response}` already have everything
  needed — no new schema field.

### Design

**Central question, resolved: route through the full `deck_advisor_agent` turn via the existing
`POST /ai/suggest`. No new endpoint, no new schema, no bypass of the agent.**

A per-card click is a new *trigger* for a query shape Phase 5 already built and already verified
end-to-end, not a new query shape. A bypass route calling `card_rag`/`search_cards_semantic`
directly would mean re-implementing legality filtering in Python (duplicating what `_format_card`
already does inside the tool), losing the agent's prose reasoning tied to the deck's actual stats,
and standing up new route/schema/rendering surface for zero new capability — the same YAGNI bar
this file already applies elsewhere (`make_agent`'s own precedent, Phase 5's "don't build a second
agent" reasoning).

**Trigger and query construction:**
- `DeckCard.tsx` gains an optional `onFindSynergies?: (deckCard: DeckCardType) => void` prop,
  rendered as a new `IconButton` in the existing Actions Row, shown only when the prop is passed
  (same idiom as the existing `onMoveCard` guard) and disabled if `!deckCard.card`.
- `DeckBuilder.tsx` passes `onFindSynergies={deck?.id ? handleFindSynergies : undefined}` (same
  "disabled until saved" convention as the practice-mode button). `handleFindSynergies(dc)`:
  1. builds the query client-side, e.g. ``What cards would synergize well with `${card.name}`
     (${card.type_line})? Its text: "${card.oracle_text}"``;
  2. switches `rightPaneTab` to `"advisor"`;
  3. passes the query to `DeckAdvisor` via a new prop, e.g. `synergySeed: { query: string; nonce:
     number } | null` — the `nonce` (e.g. `Date.now()`) exists so clicking the *same* card twice in
     a row still fires, even though the query string alone would be unchanged.
- `DeckAdvisor.tsx` accepts `synergySeed` and adds a `useEffect` keyed on `synergySeed?.nonce` that
  calls the existing `handleSend(synergySeed.query)` directly — no change to `ChatInput.tsx`. Guard
  against firing a second send while one is in flight, same precedent as Phase 3d's synchronous
  double-submit guard.

**Results render in the existing `DeckAdvisor` chat pane** — not a new popover/panel. `DeckBuilder`'s
right pane is already dual-purpose (stats/advisor tabs) and already has a separate hover-preview
overlay; stacking a third UI paradigm (a click-anchored popover) on top would be real new surface
area for no gain, and would contradict Phase 5's own already-shipped interview decision to keep
synergy answers as chat prose rather than a structured list. Switching tabs + auto-sending into the
same pane is the smallest diff that satisfies the ask.

**Backend: no changes required.** `POST /ai/suggest`, its schemas, and `deck_advisor_agent`'s
tools/prompt are already correctly shaped — this phase is frontend-only (a new prop on
`DeckCard.tsx`, a handler + prop-threading in `DeckBuilder.tsx`, a seed-effect in `DeckAdvisor.tsx`).

### Files touched (if the recommended default is confirmed)

- `frontend/src/components/DeckCard.tsx` — new `onFindSynergies?` prop, new conditional
  `IconButton` in the Actions Row.
- `frontend/src/pages/DeckBuilder.tsx` — new `synergySeed` state, `handleFindSynergies` handler,
  prop-threading into `DeckCardComponent` and `DeckAdvisor`.
- `frontend/src/components/DeckAdvisor.tsx` — new `synergySeed?` prop, a `useEffect` calling the
  existing `handleSend`, an in-flight guard against double-firing.
- No backend files change under the recommended default. If the interview instead picks the bypass
  fallback below: new `backend/app/api/routes/ai.py` endpoint + `backend/app/schemas/ai.py`
  addition, reusing `card_rag`/`_card_to_dict`/`_format_card` rather than duplicating them.

### Open question for the product-owner interview

**Is a full agent turn per click acceptable, or does the lower-friction trigger (a click vs. typing
a chat message) change the cost/latency calculus enough to want a cheaper bypass for this specific
interaction?**

Recommended default (above): route through the full agent turn, reusing `/ai/suggest` as-is —
zero backend changes, reuses Phase 5's already-verified citation/legality discipline, keeps the
agent's prose "why this synergizes" explanation.

The real tension: Phase 1's own measured numbers put a `/ai/suggest` call at roughly 15-90 seconds
depending on how many `search_cards` verifications the agent needs — a cost the user already
accepts for a deliberately-typed chat question. A one-click button invites much higher-frequency,
lower-intent use (clicking through several cards in a row just to browse), the same operation paid
for more often. If that tradeoff turns out to matter, the fallback is a lightweight variant that
skips the LLM turn entirely: a new endpoint calling `card_rag.query(...)` directly, filtering
results against the local `Card` table's `legalities` in code (deterministic, no LLM needed —
`_card_to_dict`/`_format_card` already do this lookup), rendering either as a single chat-style
message in the same pane (cheap, but loses the agent's synthesized reasoning) or a genuinely new
structured/click-to-add result list (real new surface area, reopening Phase 5's own already-
answered interview question about that exact fallback). Worth asking directly rather than assuming
the existing chat latency is "fine" just because it was fine for typed queries.

### Interview outcome (resolved before writing code, per-phase process)

Resolved by interview, 2026-08-15 — took the blueprint's recommended default, no deviation: **route
through the full `deck_advisor_agent` turn via the existing `POST /ai/suggest`.** No bypass
endpoint, no new backend surface. Implementation proceeds per the Design section above:
`onFindSynergies` prop on `DeckCard.tsx`, `handleFindSynergies` + `synergySeed` state in
`DeckBuilder.tsx`, seed-effect in `DeckAdvisor.tsx` calling `handleSend` directly.

### Shipped: built exactly per Design, no deviation

Routed to `mtg-frontend`, frontend-only as planned. `DeckCard.tsx` gained the `onFindSynergies?`
prop and a new `AutoAwesomeIcon` button in the Actions Row, tooltipped "Find synergies," rendered
only when the deck card has resolved card data. `DeckBuilder.tsx`'s `handleFindSynergies` builds the
query client-side from the clicked card's own name/type/oracle text, switches `rightPaneTab` to
`"advisor"`, and sets a `{ query, nonce }` seed. `DeckAdvisor.tsx`'s seed-effect calls `handleSend`
directly — a `lastSeedNonceRef` (not just `mutation.isPending`) tracks the last-processed nonce, a
deliberate choice to survive React StrictMode's dev-only double-invoke of effects, which fires
synchronously before a first call's pending state would be reflected in a re-render.

**Live-verified against the real docker stack**, not just typechecked, after a first pass surfaced
two things worth recording (neither a defect in the shipped code):

1. The first click's real network call failed with a genuine `ServerDisconnectedError` from the
   Gemini API — an infrastructure blip, confirmed via `docker logs` and reproduced as unrelated to
   this phase's code (a direct `curl` to `/ai/suggest` minutes later, no code changes in between,
   succeeded in 33s with a normal response). Nothing to fix; the existing "Sorry, I couldn't get a
   suggestion" error bubble (Phase 1's own error handling) rendered correctly when it happened.
2. A second verification pass, after a fresh page load, clicked "Find synergies" on a non-commander
   creature (Arbor Elf) and got a real, on-topic synergy answer (leading with **Utopia Sprawl**) —
   confirming the full path (button → query construction → tab switch → `/ai/suggest` → agent
   response) end to end, not just the click-and-switch-tabs part.

`npx tsc -b` and `npx eslint .` both clean. No backend files changed, matching the Design section's
scope exactly.

---

## Phase 7 — Goldfish session analytics (shipped, 2026-08-15)

### Why this one, and why now

Second of two features raised in the same 2026-08-15 brainstorming session (Phase 6 above is the
first, picked up ahead of this one per stated priority). Three full phases of investment in
goldfishing (3a branching tree, 3b assisted simulator, 3d two-deck goldfishing) and today every
session is viewable only in isolation — `GoldfishTree.tsx` renders one session's tree,
`GoldfishSessionPage.tsx` is scoped to one session at a time. Nothing aggregates across sessions.
User asked for an aggregate analytics view (win rate, average game length, mulligan/mana-screw
frequency raised as illustrative examples, not a fixed spec).

### Status

Design pass complete (`mtg-architect`, 2026-08-15). Four open questions flagged for the
product-owner interview before implementation — the first blocks everything else in this phase.

### Ground truth this plan is built on

Checked directly against current code, not assumed:

- `GoldfishSession` (`backend/app/models/goldfish.py:63-74`) has exactly `deck_id`, `user_id`,
  `name`, `opponent_deck_id`, `created_at`. **No outcome/result field of any kind exists.** No
  win/loss/draw concept, no "session ended" event, no "session complete" flag anywhere.
- `GoldfishNode` (`goldfish.py:88-113`) has `turn_number: Optional[int]` (bumped only by an
  explicit `next_turn` action), `trackers: Optional[Dict[str, int]]` (opaque, freeform), and
  `state: Optional[Dict]` (a `GameState` snapshot: zones, `life_total`, `opponent_life_total`,
  `opponent_zones`).
- **Sessions are trees, not linear logs** — a second load-bearing constraint alongside the missing
  outcome field. A session can have multiple sibling branches (`parent_id`, `order_index`)
  representing alternate hypothetical lines, with no server-side concept of which branch "actually
  happened." `selectedNodeId` in `GoldfishSessionPage.tsx:48` is frontend-only, ephemeral, never
  persisted. "How did the game end" and "how long did it go" are both ambiguous at the tree level,
  not just unrecorded — there's no canonical path to read them off even in principle.
- The action vocabulary (`GoldfishActionIn.type`) is `draw`, `play_land`, `cast`, `move_zone`,
  `set_life`, `shuffle`, `next_turn`. **No `mulligan` action exists.** A user could simulate one via
  `move_zone` + `shuffle` + `draw`, but nothing tags it as a mulligan — indistinguishable in the log
  from an unrelated shuffle. Mulligan frequency is not inferable from existing data at all.
- Mana screw/flood *is* theoretically derivable (cross-reference `state.hand`/`state.battlefield`
  against `Card.type_line` containing `"Land"` at each turn boundary) but needs its own threshold
  design and is the most expensive candidate metric to compute (per-turn, per-node, joined against
  `Card`). A scope/cost question, not a schema gap.
- `backend/app/services/goldfish.py` is pure state-transform functions, no aggregation logic.
  `stats.py`'s `calculate_stats(deck)` is the existing "service function computes, thin route calls
  it" precedent — but it's deck-*composition* math, a different domain (per the subagent roster,
  `mtg-maths` owns mana curve/draw odds/color balance, not gameplay-history aggregation). This
  phase's aggregation doesn't belong folded into `stats.py`.
- `goldfish.py`'s `list_sessions` already filters by `deck_id` **and** `user_id` — the exact
  `?deck_id=` scoping precedent this phase should reuse. `_get_owned_session` is the reusable
  per-session ownership-check pattern for a new outcome-update endpoint.
- Frontend: `Goldfish.tsx` is the deck-picker → session-list page; once a deck is selected it
  already fetches sessions scoped to that `deck_id` — the natural, already-deck-scoped surface for
  an aggregate view, no new page/route needed. `types/goldfish.ts`'s `GoldfishSession` interface
  uses `| null` on always-present keys (`opponent_deck_id: number | null`), never `?:` — the
  convention to match if `outcome` is added.
- `backend/app/api/api.py:12` already registers `goldfish.router` at `/goldfish` — a new `GET
  /goldfish/analytics` route is a same-router addition, not new registration wiring.

### Design

**Central decision this phase has to make before any metric is buildable: how does a session's
outcome get recorded.** No candidate answer is already implied by existing code — genuinely new
ground. Recommendation, offered as an interview starting point, not a silent pick:

- **Manual only** — matches this system's established philosophy (3d's interview: "manual
  dual-piloting... no automation"; no rules engine exists, and life-total-hits-zero win detection
  wouldn't be reliable anyway since users may never touch life total if only testing draws/curve).
- **Session-level, not node/branch-level.** A new nullable `GoldfishSession.outcome:
  Optional[Literal["win", "loss", "draw"]]`, set via a small control on `GoldfishSessionPage.tsx`,
  not tied to any specific tree node — sidesteps the branch-ambiguity problem above entirely by
  recording "how this practice session went" as one whole-session judgment call.
- **Freely editable, not a one-way "end session" action.** Nothing else in this system treats a
  session as "closed" — a locking/finalization step would be new, unrequested ceremony. A
  dropdown/toggle the user can set or change at any time is the smaller, more consistent design.
- New endpoint: `PATCH /goldfish/sessions/{id}` (schema `GoldfishSessionOutcomeUpdate {outcome:
  Literal["win","loss","draw"] | None}`), reusing `_get_owned_session` like every other
  session-scoped route.
- Migration: single nullable `op.add_column`, no FK — matches the shape of the two simple prior
  goldfish migrations, not 3d's heavier FK-adding one.

**Analytics aggregation — a new module, not folded into `stats.py`.** New
`backend/app/services/goldfish_analytics.py`, following the existing "service function computes,
route stays thin" pattern. One function, `async def compute_deck_analytics(db, deck_id, user_id) ->
GoldfishAnalyticsPublic`, deck-scoped (matching `list_sessions`'s `?deck_id=` convention — no
cross-deck rollup in v1, trivially addable later). New schema in `backend/app/schemas/goldfish.py`:

```python
class GoldfishAnalyticsPublic(BaseModel):
    session_count: int
    sessions_with_outcome: int
    wins: int
    losses: int
    draws: int
    win_rate: Optional[float]          # None when sessions_with_outcome == 0
    average_max_turn: Optional[float]  # None when no session has any turn_number set
    two_deck_session_ratio: Optional[float]  # None when session_count == 0
```

New route `GET /goldfish/analytics?deck_id=`, same file, same auth/ownership shape as
`list_sessions`.

**v1 metric set — only what's soundly computable today, nothing assumed into existence:**

1. `win_rate` = wins / sessions_with_outcome (excludes sessions with no recorded outcome from the
   denominator; `sessions_with_outcome` reported alongside so "0 sessions marked" reads distinctly
   from "0% win rate"). Entirely contingent on the outcome-recording mechanism shipping first.
2. `wins`/`losses`/`draws` breakdown.
3. `session_count`, `sessions_with_outcome` — a completion-rate signal on its own.
4. `average_max_turn` — for each session, `MAX(turn_number)` across every node in that session's
   *whole tree* (not one branch — there is no canonical branch to prefer per Ground Truth),
   averaged across sessions. Caveat for the UI copy: this can overcount vs. "how long the game
   actually went" if the user explored a longer hypothetical branch than the line they actually
   played — a known, stated limitation, not silently hidden.
5. `two_deck_session_ratio` — fraction of sessions with `opponent_deck_id` set, i.e. real
   opponent-board testing vs. solo goldfishing.

**Explicitly not in v1, with reasons:**

- **Mulligan frequency** — not inferable from the current action vocabulary at all; would need a
  new explicit `mulligan` action type first, a real vocabulary change, not an analytics-layer
  add-on. Separate open question below.
- **Mana screw/flood frequency** — theoretically derivable but needs its own threshold design and
  is the most expensive metric to compute. Matches this codebase's repeated pattern (3a/3b) of
  shipping a plain first cut and iterating only once real usage surfaces friction. Separate open
  question below.
- **Wall-clock session duration** — cheap to add later (`created_at` delta, root to latest node)
  but conflates thinking/pause time with game length; lower value than turn-count, addable
  independently at any time without touching the outcome-recording work.

**Frontend:** new `GoldfishAnalyticsPanel.tsx` (`frontend/src/components/`), rendered inside
`Goldfish.tsx`'s deck-selected view above/beside the existing session `List` — reuses the page's
existing `selectedDeckId` scoping, no new route/page. `useQuery(["goldfishAnalytics",
selectedDeckId], ...)` against `GET /goldfish/analytics?deck_id=`, rendered as a small stat-row
(session count, win rate, avg turns reached, two-deck ratio) — matches the "tab/section beside
existing content" precedent from Phase 1 (advisor tab next to Deck Statistics) rather than a new
page. Outcome-recording control (a small `Win / Loss / Draw / —` toggle) lives on
`GoldfishSessionPage.tsx`'s header, next to the existing tree/deck-list toggles. `types/goldfish.ts`'s
`GoldfishSession` gains `outcome: "win" | "loss" | "draw" | null`, matching the established
`| null`-on-always-present-key convention.

### Concrete steps (once the interview below resolves)

1. **Outcome-recording foundation** (backend): `outcome` column + migration on `GoldfishSession`,
   `GoldfishSessionOutcomeUpdate` schema, `PATCH /goldfish/sessions/{id}` reusing
   `_get_owned_session`. Tests: set/clear/update outcome, ownership check (403 on someone else's
   session), invalid literal value rejected.
2. **Outcome-recording UI** (frontend): small control on `GoldfishSessionPage.tsx`, wired to the
   new `PATCH`, `outcome` added to `types/goldfish.ts`.
3. **Analytics service + endpoint** (backend): `goldfish_analytics.py`, `GoldfishAnalyticsPublic`
   schema, `GET /goldfish/analytics?deck_id=`. Tests: zero-session deck (all-None/zero response),
   mixed win/loss/draw + unrecorded sessions (win_rate denominator excludes unrecorded),
   `average_max_turn` against a small multi-branch fixture tree (confirms whole-tree max, not
   first-branch), two-deck ratio, ownership (deck not owned by requester → 403/404 matching
   existing deck-route pattern).
4. **Analytics UI** (frontend): `GoldfishAnalyticsPanel.tsx` wired into `Goldfish.tsx`.

### Verify (once built)

`cd backend && uv run pytest` covers the new endpoints, not just structural typing. Manually
against the docker stack: record win/loss/draw on a few real sessions for one deck, confirm the
analytics panel's win rate and counts match by hand-count; confirm a deck with zero sessions
renders a sane empty state (not a crash/NaN%); confirm `average_max_turn` reflects a session with a
longer abandoned branch than its "real" line, and that this is visibly explained in the UI copy,
not silently misleading.

### Open questions for the product-owner interview

1. **(Central, blocks everything else) How should a session's outcome be recorded — mechanism,
   granularity, and mutability?** The recommendation above (manual button, session-level not
   per-branch, freely editable, no "end session" lock) is a starting point, not a decision. Needs
   an actual answer before Step 1 can be written.
2. **Should outcome-recording (and therefore win-rate) apply to single-deck sessions too, or only
   two-deck (Phase 3d) sessions?** A single-deck session has no in-app opponent board — "win/loss"
   there would describe a match played elsewhere (paper/MTGO) while goldfishing draws in this app.
   Both are plausible; changes what "win rate" even means and whether the control should be
   conditionally hidden.
3. **Is mana screw/flood detection wanted for v1**, despite the added threshold-design and compute
   cost, or deferred until real usage of the simpler metrics surfaces demand (matching 3a/3b's
   "ship plain, iterate on friction" precedent)?
4. **Is mulligan frequency wanted badly enough to justify adding a new `mulligan` action type
   first** (a real change to the existing action vocabulary, not just an analytics addition), or
   deferred?

### Interview outcome (resolved before writing code, per-phase process)

All four questions resolved by interview, 2026-08-15 — all took the blueprint's recommended
default, no deviation:

1. **Outcome recording: manual toggle, session-level, freely editable, no lock/finalize concept.**
2. **Scope: both single-deck and two-deck sessions** can record an outcome — a single-deck
   session's win/loss describes a match played elsewhere while goldfishing draws in-app, still a
   meaningful signal.
3. **Mana screw/flood detection: not in v1**, deferred until the core metric set surfaces real
   demand.
4. **Mulligan frequency: not in v1**, deferred — no new `mulligan` action type added at this time.

Implementation proceeds per the Design and Concrete Steps sections above, in order: outcome-
recording foundation (backend) → outcome-recording UI (frontend) → analytics service + endpoint
(backend) → analytics UI (frontend).

### Shipped: backend then frontend, no deviation on scope

Routed to `mtg-backend` (Concrete Steps 1 and 3) then `mtg-frontend` (Steps 2 and 4), same
sequencing precedent as Phase 3d. Backend: `GoldfishSession` gained a nullable
`outcome: Optional[Literal["win","loss","draw"]]` on `GoldfishSessionBase` (inherited by
`GoldfishSession`/`GoldfishSessionPublic`, deliberately **not** added to `GoldfishSessionCreate` — a
session never starts with an outcome), needing an explicit `sa_column=Column(String)` since SQLModel
can't auto-derive a column type from `Optional[Literal[...]]` (a real `TypeError` on import caught
this before it shipped, not inspection). New migration `9ebb5d15bcf9` — single nullable
`op.add_column`, matching the two simplest prior goldfish migrations, not 3d's heavier FK-adding
one. `PATCH /goldfish/sessions/{id}` (body `{"outcome": "win"|"loss"|"draw"|null}`, reuses
`_get_owned_session`) and `GET /goldfish/analytics?deck_id=` (new `goldfish_analytics.py`'s
`compute_deck_analytics`, one flat query for `average_max_turn` across each session's *whole* tree,
not one branch — no per-branch traversal) both shipped as specified, no scope deviation (no
mana-screw/mulligan metrics, applies to both single- and two-deck sessions).

One real bug the implementer's own tests caught, not inspection: two test files had
`app.dependency_overrides.clear()` fired mid-test with a DB call still to come after it — the exact
`dependency_overrides.clear()` footgun Phase 3b's section of this file already documents. Surfaced
as a real Postgres-connection-attempt failure while running the suite; fixed both to use
`del app.dependency_overrides[get_current_user]` instead, matching the already-documented fix.

Frontend: a `ToggleButtonGroup` (Win/Loss/Draw/—) on `GoldfishSessionPage.tsx`'s header wired to the
new `PATCH`, invalidating both the session-tree query and `["goldfishAnalytics"]` on success so the
analytics panel can't go stale from a stale outcome. New `GoldfishAnalyticsPanel.tsx` (a `Paper`
stat row: sessions / win rate / avg. max turn / two-deck ratio) wired into `Goldfish.tsx` above the
existing session list, rendering a distinct empty state at zero sessions and `—` per-field for any
null optional rather than `NaN%`. `average_max_turn`'s label carries a tooltip stating it reflects
the longest explored branch, not necessarily the line actually played, per this section's own
Design-stage caveat. `types/goldfish.ts` gained `outcome: "win"|"loss"|"draw"|null` on
`GoldfishSession` (the file's established `| null`-on-always-present-key convention) and a new
`GoldfishAnalytics` interface mirroring `GoldfishAnalyticsPublic`. `ToggleButtonGroup` is a
genuinely new MUI component in this codebase (no prior usage to match) — flagged by the implementer
as a judgment call, not hidden.

**Live-verified against the real docker stack**, not just typechecked: confirmed the migration
applied via container logs; toggled a session's outcome to Win, reloaded, confirmed it persisted;
set a second session to Loss; confirmed the deck's analytics panel read `Sessions: 3`,
`Win rate (2 recorded): 50%`, `1W / 1L / 0D`, `Avg. max turn: —` (correctly null — no node in those
sessions has `turn_number` set), `Two-deck sessions: 0%` — matched hand-counting exactly. Confirmed
the pre-outcome empty/unrecorded state renders sanely (no NaN/crash). No console/network errors on
any goldfish route. `cd backend && uv run pytest` (120 passed), `uv run ruff check .` clean on every
file this phase touched (one pre-existing, unrelated `F401` in `scryfall.py` confirmed untouched by
this phase via `git diff HEAD` — left alone, out of scope). `npx tsc -b` and `npx eslint .` both
clean on the frontend.

---

## Phase 8 — Total mana spent tracker (shipped, 2026-08-23)

### Why this one, and why now

User-requested, 2026-08-16: surface a running "total mana spent so far" figure in a goldfish
session's game history, alongside the life total and other trackers already shown during play.

### Status

Design pass complete (`mtg-architect`, 2026-08-23). Two open questions flagged for the
product-owner interview before implementation — everything else is a decided recommendation.

### Ground truth this plan is built on

Re-verified directly against current code, not the earlier backlog stub's partial pass — several
details there were stale (line numbers had moved, and it missed the `self`/`opponent` target
dimension entirely, added by Phase 3d after the stub was written):

- `GoldfishActionIn` (`backend/app/models/goldfish.py:52-60`) has `type: Literal["draw","play_land",
  "cast","move_zone","set_life","shuffle","next_turn"]` and a `target: Literal["self","opponent"] =
  "self"` field. `apply_action`'s `play_land`/`cast` branch (`backend/app/services/goldfish.py:149-
  159`) is shared code for both types — it moves a card from hand to the *target's* battlefield
  (self or opponent) and generates a label. **No mana value is looked up or stored anywhere today.**
- `Card` (`backend/app/models/card.py:4-19`) has `mana_cost: Optional[str]` (Scryfall's raw string,
  e.g. `"{2}{G}"`), no numeric `cmc` column. Confirmed via a repo-wide grep: no `cmc` field exists
  anywhere in `models/`, `scryfall_ingestion.py`, or `services/scryfall.py` — Scryfall's numeric
  `cmc` is not fetched or persisted at all today, not a "fetched but unused" situation.
- **A correct CMC-from-string parser already exists and is shipped**: `backend/app/services/
  stats.py:97-115` (`_calculate_cmc`), used today for the deck-stats mana curve and color-source
  recommendations. It strips `{\d+}` generic-mana symbols and sums their values, then counts every
  *remaining* `{...}` symbol as 1 — mana-value-correct for hybrid (`{G/U}`), Phyrexian (`{G/P}`), and
  colored-pip symbols alike (each contributes exactly 1 regardless of what's inside the braces).
  **One real pre-existing bug, not introduced by this phase**: `{X}` also matches "non-numeric
  bracket content" and is counted as 1 rather than X's off-stack value of 0 — `{X}{R}` computes as
  mana value 2 instead of 1. Already affects the shipped mana-curve/avg-CMC stat today; called out
  below as an explicit choice, not silently inherited.
- **The frontend has its own, weaker, parallel parser**: `frontend/src/components/DeckStats.tsx:77-
  90` — uses `.match()` without the global flag (only ever reads the *first* `{\d+}` occurrence) and
  only matches single-letter pips, missing hybrid/Phyrexian entirely. Not something to reuse here —
  a separate latent bug in the existing mana-curve card, out of scope for this phase.
- `apply_action` already takes a `card_names: Dict[str, str]` (id→name) lookup, built in the route
  (`backend/app/api/routes/goldfish.py:291-296`) via `select(Card.id, Card.name).where(Card.id.
  in_(all_card_ids))` over every card_id in the parent state's zones (self + opponent, null-guarded).
  This is the exact seam a mana-cost lookup slots into — same query, one more column.
- `GoldfishNode.state` is an untyped JSON column (`backend/app/models/goldfish.py:116`); `GameState
  (**parent_node.state)` backfills pydantic defaults for any field missing from an older stored
  blob — already the zero-migration mechanism Phase 3b (`opponent_life_total`) and Phase 3d
  (`opponent_zones`) both used, confirmed still true, no new migration needed for a new field.
- Frontend: `GoldfishPlaymat.tsx`'s `GoldfishPlayerBoard` (`frontend/src/components/
  GoldfishPlaymat.tsx:187-295`) is instantiated twice (self, opponent) with per-player `zones`/
  `lifeTotal`/`onLifeChange` props — the one place both boards' UI is defined, so a per-player
  counter added there renders for both sides for free. `LifeCounter` sits in an `ml: "auto"` box at
  line 292-294. The standalone bare "Opp" life counter (rendered only when `!state.opponent_zones`,
  i.e. no real opponent board) is structurally incompatible with a mana-spent counter — there's no
  opponent hand to cast from in that mode, so opponent mana spent can't ever be nonzero there.

### Design

**1. What counts as "mana spent": `cast` only.** `play_land` never has a cost (`mana_cost` is empty
for every land, so including it would always be a no-op), and no action in today's vocabulary
represents activated abilities or other costs — out of scope because the vocabulary has nothing to
represent them with, not a gap this phase should try to paper over.

**2. Numeric source: parse `Card.mana_cost`, don't add a stored `cmc` column.** Extract `stats.py`'s
existing `_calculate_cmc` into a small shared module, `backend/app/services/mana.py` (public
`calculate_cmc(mana_cost: str) -> float`), and have `stats.py` import it (one-line change, nothing
else in that file touched). `goldfish.py`'s service imports it directly. This is a real-duplication
extraction (two independent services now need identical parsing logic), not a speculative one — the
same bar this codebase already applies to `make_agent` (Phase 1). A stored `cmc` column would mean a
migration, a backfill of every already-cached `Card` row, and threading `cmc` through three separate
card-persistence call sites (`decks.py:89`, `collection.py:54`, `scryfall_ingestion.py:56`) — real
new surface for a number the existing string parser already produces correctly for every symbol type
that matters here.
   - **Explicit, deliberately out-of-scope note**: the parser's pre-existing `{X}` mishandling is not
     being fixed as part of this phase — fixing it would silently change the already-shipped
     mana-curve/avg-CMC numbers for any deck containing X spells, a behavior change with a blast
     radius outside this feature. Flagged for interview confirmation only in case the product owner
     wants it bundled — default is: leave it, file separately.

**3. Derived-on-read vs. stored-on-node: stored, as a first-class `GameState` field, computed by the
backend at write time.** Mirrors 3b's own `life_total` decision (stays first-class on `state`, not
folded into `trackers`) for the same reason, plus one the life_total precedent didn't have to deal
with: a pure read-time derivation genuinely isn't reconstructable from what's stored today. Nodes
don't record which action created them — only the resulting `label` (free text) and `state` (a
snapshot). Diffing a node's battlefield against its parent's to guess "a card was cast here" is
unreliable, because `move_zone` is a fully generic action that can also move a card onto the
battlefield (e.g. reanimation-style hand/graveyard→battlefield) with an identical resulting-state
shape to a `cast` — there is no way to tell them apart after the fact without storing more than just
the number. Add:
```python
class GameState(Zones):
    ...
    mana_spent: int = 0
    opponent_mana_spent: int = 0
```
Both default to `0` and ride along for free on every action that isn't a self/opponent `cast` —
`apply_action` already does `next_state = state.model_copy(deep=True)` at the top of every branch, so
untouched fields are preserved automatically, exactly like every other carry-forward field already
works. Only the `cast` branch needs new code: look up the cast card's `mana_cost` from a new
`card_mana_costs: Dict[str, str]` parameter (built the same way `card_names` already is, one extra
column on the same query), run it through `calculate_cmc`, and add it to `next_state.mana_spent`
(target `self`) or `next_state.opponent_mana_spent` (target `opponent`). Symmetric self/opponent
tracking follows the exact precedent `target` already established for `cast`/`set_life` in Phase 3d.
   - Genuinely zero migration: `state` is a JSON column; both new fields backfill to `0` via pydantic
     default for every pre-existing stored node, same mechanism Phase 3b/3d already relied on.
   - `trackers` is explicitly the wrong home for this, on the existing precedent's own terms: 3a's
     own reasoning for `trackers` is "the backend does zero inheritance logic — trackers is just
     whatever the request provides." Mana spent needs real backend-computed inheritance logic
     (increment on `cast`, carry forward otherwise) — the opposite of that design intent.

**4. Frontend surface: `GoldfishPlaymat.tsx`'s `GoldfishPlayerBoard`, next to each side's
`LifeCounter`.** Add a `manaSpent: number` prop to `GoldfishPlayerBoardProps`, rendered as a plain
read-only label (not editable like `LifeCounter` — this number is never user-set, only
backend-computed) in the same `ml: "auto"` box as the existing `LifeCounter`. Threaded from the
parent exactly like `lifeTotal` already is: `state.mana_spent` for the self board,
`state.opponent_mana_spent` for the opponent board. Because `GoldfishPlayerBoard` is one shared
component instantiated for both sides, this single edit site covers both self and two-deck-opponent
rendering — the bare fallback "Opp" life counter is correctly left untouched.

### Open questions for the product-owner interview

1. **Does the game-history tree (`GoldfishTree.tsx`) also need this, or is the live playmat counter
   enough?** The user's phrasing ("in a goldfish session's game history... alongside the life total
   and other trackers already shown during play") plausibly means either "the playmat, which is
   what's live during play" or "the tree, which is literally the history." `GoldfishTree.tsx` already
   renders a per-node `trackers` summary line (`GoldfishTree.tsx:74-87`) reading `n.trackers`;
   extending that line to also read `n.state?.mana_spent`/`opponent_mana_spent` when present is cheap
   and additive, but it's a second UI surface the Design above doesn't strictly require. Recommended
   default: ship the playmat counter first (unambiguously "alongside the life total... during play");
   add the tree-node line as a fast follow-up if wanted, rather than building both on a guess.
2. **Bundle the pre-existing `{X}` CMC-parser bug fix, or leave it out of scope?** Recommended
   default: leave it — it would silently change the shipped mana-curve stat for X-spell decks, an
   unrelated behavior change. Confirm before Concrete Step 1 in case both should ship together.

Everything else above (cast-only scope, string-parsing over a stored `cmc` column, stored-not-derived,
`GameState`-field placement, symmetric self/opponent tracking, playmat-component placement) follows
directly from existing codebase convention with no live product ambiguity — decided, not reopened.

### Interview outcome (resolved before writing code, per-phase process)

Both questions resolved by interview, 2026-08-23 — **both went against the blueprint's own
recommended default**, unlike Phase 5/6/7's interviews:

1. **Tree view: yes, both surfaces.** The playmat counter ships as designed, *and*
   `GoldfishTree.tsx`'s per-node summary line gets extended to also show mana spent at each node —
   not deferred as a "fast follow-up."
2. **CMC parser `{X}` bug: fix it now, as part of this phase**, accepting that this changes the
   already-shipped mana-curve/avg-CMC numbers for any deck containing `{X}` spells. This is a
   deliberate, informed behavior change to existing stats, not an accidental side effect — worth
   this note existing so a future reader doesn't mistake the shifted mana-curve numbers for a
   regression.

### Concrete steps (per the interview outcome above)

1. **`backend/app/services/mana.py`** (new) — `calculate_cmc(mana_cost: str) -> float`, body moved
   from `stats.py:97-115`, **fixing the `{X}` bug in the same move**: an `{X}` symbol must contribute
   `0` to the total, not `1` like every other non-numeric `{...}` symbol. `stats.py` imports it as
   `_calculate_cmc` in place of the local def (one-line change, everything else in that file
   untouched) — its own existing mana-curve/avg-CMC tests are expected to need updating for any
   fixture deck containing `{X}` costs, per the interview outcome's accepted tradeoff, not a
   regression to chase down.
2. **`backend/app/models/goldfish.py`** — add `mana_spent: int = 0` and `opponent_mana_spent: int =
   0` to `GameState`. No migration.
3. **`backend/app/services/goldfish.py`** — `apply_action` gains a `card_mana_costs: Dict[str, str]`
   parameter (alongside `card_names`); in the `cast` branch only, compute
   `calculate_cmc(card_mana_costs.get(action.card_id, ""))` and add it to `next_state.mana_spent` or
   `next_state.opponent_mana_spent` depending on `action.target`.
4. **`backend/app/api/routes/goldfish.py`** — extend the existing card-lookup query (line ~294) to
   also select `Card.mana_cost`, build the second `card_mana_costs` dict, pass it into `apply_action`.
5. **Tests**: extend `backend/app/tests/api/routes/test_goldfish_actions.py` — cast increments
   `mana_spent`/`opponent_mana_spent` correctly for generic/colored/hybrid/Phyrexian/`{X}` costs,
   `play_land` leaves it unchanged, every other action type carries the value forward unchanged, and
   a `GameState(**old_state_dict)` missing the new keys entirely still backfills to `0`. Add unit
   tests for `mana.py`'s extracted `calculate_cmc` directly (including the fixed `{X}` = 0 case),
   update `stats.py`'s existing mana-curve tests for the corrected numbers on any `{X}`-cost fixture.
6. **Frontend**: add `mana_spent`/`opponent_mana_spent: number` to `GameState` in `frontend/src/
   types/goldfish.ts` (same "typed as always-present, may be absent on older nodes" caveat comment as
   `opponent_zones`); add `manaSpent: number` to `GoldfishPlayerBoardProps` and render it next to
   `LifeCounter` in `GoldfishPlaymat.tsx`, reading `state.mana_spent ?? 0` / `state.
   opponent_mana_spent ?? 0` defensively for pre-existing sessions.
7. **`GoldfishTree.tsx`**: extend the existing per-node tracker-summary line (`GoldfishTree.tsx:74-
   87`) to append `n.state?.mana_spent` (and `n.state?.opponent_mana_spent` when
   `n.state?.opponent_zones` is set) after the existing `trackers` summary, defensively defaulting
   missing values to `0` for pre-existing nodes.

### Verify (once built)

`cd backend && uv run pytest` covers the new `cast`-branch behavior, the extracted `calculate_cmc`,
and the old-state-backfill case. Manually against the docker stack: drive a single-deck session,
cast spells of different cost shapes (generic, colored, hybrid), confirm the counter increments
correctly and other actions (play_land, draw, move_zone, next_turn) don't change it; repeat against a
two-deck session casting from both sides, confirming the two counters track independently. `npx tsc
-b` / `npx eslint .` clean on the frontend files touched.

### Shipped: as designed, no scope deviation

Built exactly per the Concrete Steps above, backend then frontend (frontend renders the backend's
real `mana_spent`/`opponent_mana_spent` response fields, same ordering rationale as Phase 3d).

**Backend**: `backend/app/services/mana.py` (new) holds `calculate_cmc`, moved out of `stats.py`
with the `{X}` fix landed in the same move (`{X}` now contributes `0`, not `1`); `stats.py` imports
it as a one-line change. `GameState` gained `mana_spent`/`opponent_mana_spent: int = 0` — no
migration, backfilled by pydantic for every pre-existing stored node. `apply_action` gained a
`card_mana_costs` parameter alongside the existing `card_names`, used only in the `cast` branch;
`goldfish.py`'s route extended its existing card-lookup query to also select `Card.mana_cost`.
137 backend tests pass, including new coverage for every cost shape (generic/colored/hybrid/
Phyrexian/`{X}`) on both `self`/`opponent` targets, every non-`cast` action carrying the fields
forward unchanged, and the old-state-backfill case. `test_stats.py` gained a regression test
proving `{X}{R}` now computes as mana value 1, confirming the accepted, deliberate shift in the
already-shipped mana-curve numbers per the interview outcome — no prior fixture contained `{X}`, so
no existing expected numbers needed updating.

**Frontend**: `GoldfishPlaymat.tsx`'s shared `GoldfishPlayerBoard` gained a read-only "Mana Spent"
label next to each side's `LifeCounter` (self and opponent both, single edit site per the Design's
own reasoning); the single-deck fallback bare "Opp" life counter was correctly left without one.
`GoldfishTree.tsx`'s per-node summary line now appends `Mana: n` (nonzero only) and, for two-deck
sessions only, `Opp Mana: n`, matching the existing `trackers` chip-list formatting. `npx tsc -b`
and `npx eslint .` both clean.

**Live-verified** against the real docker stack, not just unit tests: a single-deck session
(`pauper test`) — cast two spells, playmat counter went 0 → 3 → 5 correctly, `play_land` left it
unchanged, tree nodes showed the matching `Mana: n` labels; a two-deck session (`pauper test` vs.
`pauper test`) — self and opponent counters tracked independently (2 vs. 3), tree node showed both
`Mana:`/`Opp Mana:` figures together on the same line. No console errors, all goldfish API calls
200 OK throughout.

---

## Phase 9 — Expose deck_builder's tools via MCP (shipped, 2026-08-23)

### Why this one, and why now

User-requested, 2026-08-16: make this app's tools/capabilities usable by **external** agents (not
just its own `rules_agent`/`deck_advisor_agent`), by standing up an MCP *server* so an outside MCP
client (Claude Desktop, another agent) can call in — the reverse direction of how MCP is normally
discussed for this codebase (an ADK agent *consuming* external MCP tools via `MCPToolset`). That
client-consumption direction is well-trodden in ADK's own docs and irrelevant here; this phase is
unambiguously the server direction, confirmed by both the user's own framing ("external agents can
use my tools") and the research below.

### Status

**Shipped** (`mtg-backend`, 2026-08-23). `backend/app/mcp/server.py` builds a `FastMCP("deck_builder")`
instance and registers all five tools via `add_tool(fn)`, imported unwrapped from `app.ai.tools.*`;
entry point `uv run python -m app.mcp.server` (stdio only), matching the design exactly. One
implementation-time finding not anticipated by the design: `app.ai.rag`/`app.ai.vector_store` use
raw `print()` (plus the shared `app.core.logging` logger's stdout handler) for status/error
messages, which corrupts the stdio JSON-RPC stream if left alone — mitigated inside `server.py`
(redirect stdout to stderr around the tool-module imports, repoint the shared logger's handler
stream to stderr in-process) without touching `app/ai/*` itself, since that's `mtg-ai-engineer`'s
scope; the residual gap (rare, error-path-only `print()` calls inside `app/ai/rag`/
`app/ai/vector_store` that would still leak to stdout on a RAG exception mid-session) is flagged for
`mtg-ai-engineer` to clean up (swap those `print()`s for `logger` calls), not fixed here. New
dependency: `mcp<2` (pinned below the SDK's brand-new 2.0 release, which renamed `FastMCP` to
`MCPServer` and moved its module path — 1.29.0 is what the design's `FastMCP`/`add_tool`/
`list_tools` API surface was actually verified against). Verified live: full MCP stdio handshake via
the `mcp` SDK's own client (`ClientSession`/`stdio_client`) against the running docker-compose
stack (Postgres, ChromaDB) — `list_tools()` returned all five names, `call_tool()` round-tripped
real Postgres-backed card data (`search_cards`) and real live-Scryfall rulings
(`lookup_card_rulings`) over the actual wire protocol, not just an in-process shortcut. Docs:
`docs/mcp_server.md`. Four open questions flagged for the product-owner interview before
implementation — the first (terminology) and third (transport) are the ones that most change the
shape of everything else.

### Ground truth this plan is built on

Re-verified directly against the repo and the actual `mcp`/ADK docs, not assumed from the earlier
backlog stub's partial pass:

- **Candidate tools, all plain, stateless, self-contained async/sync functions** already registered
  on ADK `Agent`s via `make_agent` (`backend/app/ai/agents/factory.py:8-23`): `search_cards(query,
  format=None)` and `search_cards_semantic(query, k=10)` (`backend/app/ai/tools/cards.py:55`,
  `:101`), `query_comprehensive_rules(query)` and `lookup_glossary_term(term)`
  (`backend/app/ai/tools/rules.py:6`, `:21`), `lookup_card_rulings(card_names)`
  (`backend/app/ai/tools/scryfall.py:52`). **All five are read-only** — nothing in this codebase's
  ADK tool layer mutates state today; deck/collection/goldfish mutation only ever happens through
  the REST routes, never through an agent tool. Directly relevant to the scope question below.
- All five are already portable outside the FastAPI process: `search_cards` opens its own DB
  session via `get_tool_session()` (`backend/app/ai/tools/db.py:19` — a directly-importable
  `async_sessionmaker` bound to the same `engine`, built specifically because "ADK calls tool
  functions directly — there's no FastAPI request/route cycle"), `search_cards_semantic`/
  `query_comprehensive_rules`/`lookup_glossary_term` import module-level `card_rag`/`rules_rag`
  singletons (`backend/app/ai/rag/cards.py:10-29`, no dependency on the FastAPI `app` instance or
  its `lifespan`), and `lookup_card_rulings` opens its own `httpx.AsyncClient` per call. None of the
  five reach into `app.state`. **This means the MCP server can be a genuinely separate process that
  never boots the FastAPI app at all** — it only needs `app.core.config.settings`-driven env vars
  (DB URL, Chroma host, Scryfall base URL), same as every ingestion script already requires.
- **No `mcp` package dependency exists anywhere in this project today** — confirmed directly in
  `backend/uv.lock`: no package named `mcp` appears as a top-level or transitive dependency,
  specifically checked against `google-adk`'s own resolved entry (`uv.lock:739-767`, pinned at
  `2.4.0`). Despite ADK's own docs saying it "uses FastMCP to handle MCP protocol details" for its
  `MCPToolset` client path, that isn't a hard dependency pulled in at this pinned version — `mcp` is
  a genuinely new dependency this phase would add (`uv add mcp`).
- **`backend/app/main.py`** is a single flat `FastAPI()` instance: CORS middleware, one
  `include_router` (`backend/app/api/api.py:1-13`, six routers), a `lifespan` that only manages a
  shared Scryfall `httpx.AsyncClient`, three bare routes. **No `app.mount(...)` anywhere** — no
  existing precedent for mounting a second ASGI app, which is what an HTTP/SSE MCP server embedded
  in-process would require. A mounted-route approach would be new infrastructure, not a small
  addition to something already there.
- **`backend/app/api/deps.py`'s `get_current_user`** is a genuine stub: ignores any bearer token
  entirely, always returns (or lazily creates) the first `User` row. Confirms this file's own
  "Deferred" section verbatim (see "Real auth" under Deferred below) — single-tenant today, by
  explicit product-owner choice gated on "complete and finished," not an oversight. Any transport
  that's network-reachable inherits this gap directly and materially changes its blast radius
  (arbitrary internet/agent traffic vs. the developer's own browser).
- **`.claude/` (agents, commands, `settings.json`, `launch.json`)** is entirely Claude-Code-
  development-time tooling. None of it is imported by, referenced from, or has any runtime existence
  inside `backend/app` or `frontend/src`. It cannot be "exposed" by an MCP server because it isn't a
  capability the deployed app serves — it's a way of working *on* this repo inside Claude Code. This
  settles the terminology question technically; which one the user meant is still the right thing to
  ask (Open Question 1), since "skills" is a real, different, reasonable thing to want exposed for a
  *different* purpose — just not something this phase's MCP server can serve at all, by construction.
- **Existing manual-entry-point precedent**: every one-off backend script (`scryfall_ingestion.py`,
  `rules_ingestion.py`, `card_embedding_ingestion.py`) is invoked as `uv run python -m
  app.ai.ingestion.<module>`, run by hand, deliberately not wired into `docker-compose.yml` or any
  scheduler. This is the exact precedent to follow for an MCP server's entry point.

### Research: how an MCP server actually gets built, and what ADK offers

- **The official `mcp` Python SDK (PyPI: `mcp`) now ships `FastMCP` directly** as
  `mcp.server.fastmcp.FastMCP` — the standalone `fastmcp` project's 1.0 API was folded into the
  official SDK; `pip install mcp` is sufficient. Declaring a tool is `@mcp.tool()` on a plain
  function (or `mcp.add_tool(fn)` programmatically) — the JSON schema and description are
  auto-derived from type hints and the docstring, and the framework supports `stdio`, `http`, and
  `sse` transports out of the box. This is directly usable against this codebase's existing tool
  functions with **zero wrapping** — they're already plain typed functions with docstrings, exactly
  the shape both ADK's own tool convention (CLAUDE.md: "Agent tools are plain async functions") and
  `FastMCP`'s tool convention want.
- **Google ADK does document a server-direction path**, but it is *not* a one-line "expose my Agent
  as a server" helper — it's a lower-level pattern: wrap each ADK-registered tool via
  `google.adk.tools.mcp_tool.conversion_utils.adk_to_mcp_tool_type`, then hand-roll `@app.
  list_tools()`/`@app.call_tool()` handlers on `mcp.server.lowlevel.Server`, then serve over
  `mcp.server.stdio.stdio_server()`. This requires first wrapping the plain functions in ADK's
  `FunctionTool` machinery purely to satisfy that lower-level API's shape — machinery this codebase
  doesn't otherwise need, and which the plain-function tools were deliberately kept clear of (Phase
  1's "tools stay stateless" decision). Given YAGNI: **bypass ADK entirely on the server side.** ADK
  is irrelevant to serving MCP — it only matters that Phase 1's original "tools are plain,
  DB-session-self-managed functions" choice happens to make them directly portable to `FastMCP`'s
  high-level API with no adapter layer at all.
- One more option, explicitly **not recommended for v1**: `FastMCP.from_fastapi(app=api_app)` can
  auto-generate an MCP server that exposes an existing FastAPI app's *REST routes* as MCP tools,
  including its middleware/auth/schemas. Real and well-documented, but the wrong shape for this
  phase's actual ask — the user asked for this app's AI *tools*, not its REST CRUD surface, and
  blanket-exposing every `/api/v1/...` route (including deck-mutating ones, protected only by the
  `get_current_user` stub) as MCP tools would silently and drastically expand scope past what was
  asked, reintroducing exactly the auth/mutation exposure this design deliberately keeps out of v1.
  Worth remembering as a natural next step *if* a future phase decides deck-mutating capabilities
  should also be MCP-exposed — not this phase's design.

### Design

**1. Scope: all five existing tools, v1.** Because every existing ADK tool in this codebase is
already read-only, "all of them" and "a conservative read-only subset" are the same set — no actual
tradeoff to litigate, unlike a codebase where some tools mutate state. Recommend exposing all five:
`search_cards`, `search_cards_semantic`, `query_comprehensive_rules`, `lookup_glossary_term`,
`lookup_card_rulings`. No deck/collection/goldfish mutation tool exists to accidentally expose. A
future MCP tool that mutates a deck (e.g. "add this card to my deck" from an external agent) is a
materially different design problem — it would need to decide *whose* deck an anonymous external
caller is mutating, entangled with the auth gap in a way today's read-only tools aren't. Flagged as
future scope, not this phase's.

**2. Transport: stdio for v1, HTTP/SSE explicitly deferred and gated.** The MCP client (Claude
Desktop, another local agent) spawns the server as a subprocess via a configured command (e.g. `uv
run --project /path/to/backend python -m app.mcp.server`) and talks over stdin/stdout — no network
socket, no listener, nothing internet-reachable. Matches the existing ingestion-script precedent of
a manually-invoked local process, and sidesteps the auth gap *by construction*, not by omission:
whoever can run that command already has full local access to `backend/.env`, the DB, and Scryfall
credentials — the same trust boundary as running any other script in this repo today.

**HTTP/SSE is explicitly not v1**, and — unlike CI/deployment in this file's existing Deferred
list — this is a **hard blocker on real auth landing first**, not a "revisit later at our leisure"
item. Everything else in Deferred is unreachable by anyone but the developer's own browser
regardless of the gap; a network-reachable MCP endpoint is by definition reachable by whatever the
operator points at it, and `get_current_user`'s current behavior would hand any caller full access
to that single tenant's data through the tool layer's DB-backed paths — this would be the first
network-facing surface in the app with zero auth check at all, including the placebo bearer-token
acceptance the REST routes at least go through the motions of. Do not build this path until real
auth is either in place or the product owner explicitly, knowingly accepts the risk for a specific
narrow reason.

**3. Module placement and architecture.** New package **`backend/app/mcp/`** — a sibling of
`app/ai/`, `app/api/`, `app/services/`, since this is a genuinely new kind of thing (a server entry
point, not a tool implementation, not a route, not a service class).
- **`backend/app/mcp/server.py`** (new) — builds a `FastMCP` instance (name e.g. `"deck_builder"`),
  registers the five existing tool functions directly via `mcp.add_tool(fn)` (imported straight
  from `app.ai.tools.cards`/`rules`/`scryfall` — **no thin wrappers needed**, their existing
  signatures and docstrings are already exactly what `FastMCP` derives schema/description from), and
  under `if __name__ == "__main__":` calls `mcp.run(transport="stdio")`. Entry point: `uv run python
  -m app.mcp.server`, matching the ingestion-script precedent exactly.
- **No FastAPI involvement at all** — this process never imports or boots `app.main:app`. Only
  needs `app.core.config.settings` (same env-driven config every other script already uses) plus the
  tool modules themselves. A deliberate architectural payoff of Phase 1's original "tools stay
  stateless, own their DB session" decision — worth citing back to explicitly since it's what makes
  this phase cheap.
- **No `docker-compose.yml` change for v1** — a manually-run local process on the operator's own
  machine, not a service the docker-compose stack needs to host. If it later needs to run *inside*
  the docker network (e.g. Chroma/Postgres only reachable there), that's a straightforward addition
  then, not now.
- **New dependency**: `mcp` added to `backend/pyproject.toml`'s `dependencies` (not
  `dependency-groups.dev` — a real runtime capability of the shipped backend package, even though
  it's invoked manually) via `uv add mcp`. Not added yet, pending the interview.
- Explicit registration mechanism: **five explicit imports and `add_tool` calls**
  (`from app.ai.tools.cards import search_cards, search_cards_semantic`, etc.), not an "auto-
  discover everything in `app.ai.tools`" mechanism — a short, fixed, deliberately-curated list (see
  Scope above), and auto-discovery would be exactly the kind of speculative generality this file's
  own YAGNI convention argues against for a five-item list not expected to grow quickly.

**4. Auth stance for v1.** **Not a blocker for the stdio path**: the trust boundary for v1 is "can
this OS user run this command on this machine," identical to running `scryfall_ingestion.py` or `uv
run pytest` today. This is not "auth is fine" — it's "auth is orthogonal to a transport that never
leaves the local process boundary," and that reasoning stops applying the instant HTTP/SSE enters
the picture. **Is a hard blocker for any future HTTP/SSE exposure** — that expansion should not ship
until either real auth lands (gated on the product owner's own "complete and finished" judgment,
per this file's existing Deferred entry) or the product owner explicitly, knowingly accepts running
a fully open, single-tenant, unauthenticated network endpoint for a specific narrow reason.

### Open questions for the product-owner interview

1. **Terminology, needs a real answer, not a guess**: does "tools and skills" mean (a) this app's
   existing ADK tool functions — the only thing an MCP server built against this backend *can*
   expose — or (b) also/instead the `.claude/` Claude Code skills? Those have zero runtime presence
   in the deployed app and cannot be served by any MCP server this phase could build. If the actual
   want is "let another Claude Code session reuse this repo's dev conventions," that's a completely
   different, unrelated ask (e.g. publishing `.claude/agents/*.md` as shareable skill files) and
   should be scoped as its own item, not folded into this phase.
2. **Scope confirmation**: all five existing read-only tools, as recommended — or a narrower/
   different starting set (e.g. just card search, holding rules lookup back)? None of the five
   mutate anything, so there's no safety-driven reason to narrow further unless there's a product
   reason (e.g. `search_cards_semantic` runs a local sentence-transformer model per call — the
   heaviest of the five, worth knowing before external callers can trigger it freely).
3. **Transport confirmation**: stdio-only, local-process v1, as recommended — specifically, does
   "external agents" mean "another agent/tool the user runs on their own machine" (what stdio
   covers) or "an agent running somewhere else that needs to reach this over a network" (what stdio
   does *not* cover, forcing the HTTP/SSE-plus-real-auth conversation immediately)? The single most
   important thing to pin down before any code gets written — it changes both the transport and the
   auth answer.
4. **Deliverable shape**: does "shipped" for this phase include a short setup doc (e.g. `docs/
   mcp_server.md` or a `backend/README.md` section) walking through pointing an MCP client at the
   resulting `uv run python -m app.mcp.server` command, matching this repo's own convention of
   updating docs when a gap they mention gets closed? Recommended default: yes, but confirm rather
   than assume.

### Interview outcome (resolved before writing code, per-phase process)

All four questions resolved by interview, 2026-08-23 — all took the blueprint's own recommended
default, no deviation:

1. **Terminology: the app's own AI tools** (`search_cards`, `search_cards_semantic`,
   `query_comprehensive_rules`, `lookup_glossary_term`, `lookup_card_rulings`), not the `.claude/`
   Claude Code skills — confirmed those are out of scope for this phase entirely, not just
   deprioritized.
2. **Transport: stdio, local-process only.** No HTTP/SSE — confirmed "external agents" means the
   user's own other agents/tools on their own machine, not a network-reachable endpoint. The
   real-auth-first gate on any future HTTP/SSE exposure stands as designed.
3. **Scope: all five existing read-only tools**, no narrowing.
4. **Docs: yes**, a short setup doc ships as part of this phase.

Implementation proceeds per the Design and Concrete Steps sections above, exactly as designed.

### Concrete steps (once the interview above resolves)

1. `uv add mcp` in `backend/` (new runtime dependency, `pyproject.toml` + `uv.lock`).
2. New `backend/app/mcp/__init__.py` and `backend/app/mcp/server.py`: `FastMCP("deck_builder")`
   instance, `add_tool(...)` for each of the five tools imported directly from their existing
   modules, `mcp.run(transport="stdio")` under `if __name__ == "__main__":`.
3. Manually verify by pointing an actual MCP client (e.g. Claude Desktop's
   `claude_desktop_config.json`, `"command": "uv", "args": ["run", "--project", "<path>/backend",
   "python", "-m", "app.mcp.server"]`) at it, confirm all five tools appear with correct
   auto-derived schemas, and exercise at least one end-to-end call per tool against the live local
   stack (Chroma/Postgres up via `docker compose up`, since the tool functions still reach into
   those) — this repo's own "verify against the live stack before calling work done" convention,
   adapted to an MCP client instead of a browser.
4. Tests: a focused pytest module (e.g. `backend/app/tests/mcp/test_server.py`) asserting the five
   tools are registered on the `FastMCP` instance with the expected names — a smoke-level test, not
   a reimplementation of each tool's own existing test coverage (confirm exact existing-test
   location before writing this, don't assume).
5. Docs: whatever Open Question 4 resolves — likely a short new `docs/mcp_server.md` or a
   `backend/README.md` section with the exact client-config snippet used in step 3.
6. Update this file's own Status paragraph once shipped, per every other phase's convention.

### Shipped: as designed, one version pin and one real bug found live

Built per the Concrete Steps above: `backend/app/mcp/server.py` (new) builds a `FastMCP
("deck_builder")` instance and registers all five tools — `search_cards`, `search_cards_semantic`
(`app.ai.tools.cards`), `query_comprehensive_rules`, `lookup_glossary_term` (`app.ai.tools.rules`),
`lookup_card_rulings` (`app.ai.tools.scryfall`) — via `mcp.add_tool(fn)` with zero wrapping, no
FastAPI import anywhere in the module. `docs/mcp_server.md` (new) has the entry-point command and a
`claude_desktop_config.json` snippet. `backend/app/tests/mcp/test_server.py` (new) smoke-tests tool
registration. 138 backend tests pass; ruff clean on everything touched.

**Dependency deviation, not a design change**: the design cited `mcp.server.fastmcp.FastMCP`, but
`mcp` shipped a `2.0.0` release the same day that renamed `FastMCP` → `MCPServer` and moved its
module path. Pinned `mcp<2` (resolved to `1.29.0`), which has exactly the `FastMCP`/`add_tool`/
`list_tools`/`run(transport="stdio")` surface the design was actually verified against — confirmed
by directly importing and inspecting both versions, not guessed.

**Real bug found during live verification, fixed in-scope**: `app.ai.rag`/`app.ai.vector_store`'s
`print()` calls and the shared `app.core.logging` logger (both writing to stdout) corrupt the stdio
transport's JSON-RPC stream — a real MCP client hit `Failed to parse JSONRPC message from server`
before the fix. Fixed entirely inside `server.py` (`redirect_stdout(sys.stderr)` around the
tool-module imports, repointing `logging.getLogger("app")`'s handler to stderr in-process) rather
than touching `app/ai/*` itself, which is `mtg-ai-engineer` territory. **Residual gap, not fixed
here**: rare error-path `print()` calls inside `app/ai/rag`/`app/ai/vector_store` would still leak
to stdout if a RAG call raises mid-session — worth a small follow-up swapping those for `logger`
calls, flagged for `mtg-ai-engineer`, not blocking this phase.

**Live verification actually performed, not just claimed**: brought up `docker compose up -d db
chromadb backend`, confirmed the server module imports/builds without ever touching `app.main`,
connects to real ChromaDB. Drove a genuine MCP stdio wire-protocol handshake using the `mcp` SDK's
own client (`ClientSession` + `stdio_client`, spawning `uv run python -m app.mcp.server` as a real
subprocess): `initialize()`, `list_tools()` (all 5 names over the wire), and `call_tool()` for
`search_cards` (real Postgres-backed data) and `lookup_card_rulings` (real live Scryfall data) —
clean, no protocol errors, confirming the stdout-pollution fix actually worked end-to-end. The
other three tools were exercised via direct `mcp.call_tool()` rather than over the wire and
returned empty results — not a bug, the local rules/card RAG collections aren't fully populated in
this dev environment (a separate, orthogonal ingestion-pipeline concern). Not verified: an actual
Claude Desktop handshake (not installed in this environment) — the SDK's own client library
exercises the identical wire protocol, the closest achievable substitute here.

---

## Phase 10 — Central project wiki (shipped, 2026-08-23)

### Why this one, and why now

User-requested directly, same day as Phase 8/9 shipping: a central docs entry point for both AI
agents and human developers, specifically for "how to expand on this project" — not end-user
docs. It must be **the** place both audiences find everything without already knowing a file
exists — no separate digging required.

### Status

Design pass complete (`mtg-architect`), scope/routing review complete (`mtg-em`), both before any
implementation — matching this file's own per-phase process. All three interview questions
resolved, then implemented directly by the orchestrating session (no specialist in the roster
owns cross-cutting root-level documentation).

### Ground truth this plan is built on

Verified directly, not assumed — full detail in the `mtg-architect` design pass and the
`mtg-em` scope review that followed it:

- Nine `docs/*.md` files, three `README.md` files (root, `backend/`, `backend/app/ai/`), 2800+
  lines of `PLAN.md`, and ten `.claude/agents/*.md` files existed with no single routing point.
- `CLAUDE.md` already referenced `graphify-out/wiki/index.md` for code-structure navigation, but
  it had never actually been generated — only `GRAPH_REPORT.md`/`graph.json`/etc existed, and the
  graph itself was stale (last built 2026-08-04, before Phases 5-9).
- `docs/ARCHITECTURE.md` and `backend/app/ai/README.md` had both drifted — missing `CardRAG`/
  `search_cards_semantic` (Phase 5), the `make_agent` factory (Phase 1), the goldfish `PATCH
  /sessions/{id}`/`GET /analytics` routes (Phase 7), two-deck goldfishing (Phase 3d), the mana
  tracker (Phase 8), and the MCP server (Phase 9) entirely. Root `README.md` wrongly claimed
  SQLite persistence (it's Postgres in prod) and called shipped AI features "experimental."
  `mtg-em`'s scope review spot-checked the remaining `docs/*.md` files against Phase 0's own
  2026-07-08 doc audit and found **4 of the 5 files the design pass flagged for a new status
  banner already had one** — only `docs/UI_DEGENERIC_DESIGN.md` genuinely lacked one. This
  correction was applied before writing anything.
- `PLAN.md`'s own Status section explicitly refuses to summarize itself (see the paragraph above
  Phase 1) — a load-bearing precedent this phase's index respects: it links to `PLAN.md`, never
  paraphrases it.
- No CI runs in this repo today (`Deferred` below) — any enforcement mechanism had to be process,
  not tooling.

### Design

**Format: in-repo markdown, no new tooling.** Rejected a GitHub Wiki (not reachable by file tools,
not co-versioned with code) and a generated static site (new build/hosting burden, no CI to run
it against). Chosen: **`docs/README.md`** as the central routing index — matches this repo's
existing `README.md` naming convention (`backend/README.md`, `frontend/README.md`) and
auto-renders as `docs/`'s GitHub landing page.

**Structure: a routing index, not a content migration.** No existing file moved. `docs/README.md`
links to everything in place: `CLAUDE.md` first (always-loaded for agents, stated explicitly for
human devs), `PLAN.md`'s Status section (link only), `docs/ARCHITECTURE.md`, `backend/app/ai/
README.md`, `frontend/README.md`, a status table over the remaining `docs/*.md` files, graphify's
code-structure navigation, the subagent roster, and an "Expanding this project" section that's the
actual answer to the user's stated goal.

**Enforcement: a new `## Documentation` section in `CLAUDE.md`** (not a bullet buried in "Key
Conventions" — `mtg-em`'s recommendation, since this is a standing process obligation, not a
one-line style rule) stating the convention: any new persistent doc file must be linked from
`docs/README.md` as part of that phase's Concrete Steps. Process-only, no CI dependency.

### Interview outcome (resolved before writing code, per-phase process)

All three questions resolved by interview, 2026-08-23:

1. **Staleness: refresh the content now**, not just flag it — `docs/ARCHITECTURE.md`,
   `backend/app/ai/README.md`, and root `README.md`'s stale claims all get fixed as part of this
   phase, not deferred to a follow-up.
2. **Generate `graphify-out/wiki/`**: yes — makes `CLAUDE.md`'s existing (previously aspirational)
   reference to it actually true.
3. **Who implements**: route through `mtg-em` for a scope/routing review first (the non-default
   option — the design pass's own recommendation was to skip straight to direct implementation),
   then the orchestrating session writes the content directly.

### Concrete steps (as implemented)

1. **`docs/README.md`** (new) — the central index, per Design above.
2. **`CLAUDE.md`** — new `## Documentation` section (enforcement convention + pointer).
3. **`docs/ARCHITECTURE.md`** — refreshed: AI/Agent layer bullet gained `CardRAG`/
   `search_cards_semantic` and an MCP server pointer; API table's `goldfish` row gained
   `opponent_deck_id`, `PATCH /sessions/{id}`, `GET /analytics`, and the `mana_spent`/`target`
   action fields; "what's not built yet" gained the MCP HTTP/SSE gate and an explicit "3c parked"
   note; added a dated status banner.
4. **`backend/app/ai/README.md`** — refreshed: `ingestion/`/`rag/` sections gained
   `card_embedding_ingestion.py`/`CardRAG`; `agents/` section gained `deck_advisor_agent` and the
   `factory.py`/`make_agent` extraction; `tools/` section gained `cards.py`/`db.py`; new section
   pointing at `backend/app/mcp/` with a cross-link to `docs/mcp_server.md` rather than
   duplicating it; added a dated status banner.
5. **Root `README.md`** — fixed the SQLite→Postgres claim, replaced the "experimental" AI framing
   with the actual shipped feature list (deck advisor, semantic search, goldfishing, MCP server),
   added a `docs/README.md` pointer under "Project Structure."
6. **`docs/UI_DEGENERIC_DESIGN.md`** — added the one genuinely-missing status banner (an
   unactioned audit/backlog item, not tracked as a `PLAN.md` phase).
7. **`graphify-out/wiki/`** — generated via `graphify update .` (incremental, AST-only, no LLM
   cost — the lighter path this repo's own `CLAUDE.md` convention already establishes, used
   instead of a full corpus re-extraction) then `graphify export wiki` (154 articles +
   `index.md`). Linked from `docs/README.md`. Gitignored (regenerated locally, same treatment as
   `graph.json`/`graph.html`) — `.gitignore` gained a pattern for it and for graphify's own dated
   auto-backup dirs, alongside its existing generated-artifact entries.

### Verify

Read `docs/README.md` start-to-finish and confirmed every link resolves to a real file or repo
path. Confirmed `docs/ARCHITECTURE.md`'s API table matches the actual registered routes
(`grep "@router\." backend/app/api/routes/ai.py backend/app/api/routes/goldfish.py`) rather than
trusting the design pass's citations blindly. Confirmed `graphify-out/wiki/index.md` was generated
and non-empty (172-line index, 154 community articles). No code paths touched — nothing to run
`pytest`/`tsc`/`eslint` against; this phase is docs and one gitignore change only.

### Follow-up, same day: pivot to an actual hosted mkdocs wiki

User follow-up, same day: the in-repo `docs/README.md` routing index wasn't enough — wanted a
real hosted site. Two product-owner decisions needed first (both asked directly, smaller in scope
than a full `mtg-architect` design pass): **hosting target** (GitHub Pages, the recommended
default — free, no new account, matches the repo's own GitHub location) and **deploy mechanism**,
since this repo has deliberately had no CI at all until now (see Deferred below) — the
**non-default** choice was taken here: a GitHub Actions workflow auto-deploying on every push to
`main` that touches `docs/**`/`mkdocs.yml`/`requirements-docs.txt`, rather than a manual
`mkdocs gh-deploy` run by hand matching this repo's existing manual-script convention.

**Built**: `mkdocs.yml` (Material theme, explicit `nav` so `docs/README.md` — not the mkdocs
convention `index.md` — is the site homepage, no file rename needed since GitHub's own folder
auto-render also depends on the `README.md` name); `requirements-docs.txt` (`mkdocs`,
`mkdocs-material`, pinned to major version); `.github/workflows/docs.yml` (path-filtered, `pip
install -r requirements-docs.txt && mkdocs gh-deploy --force`, `permissions: contents: write` for
the `gh-pages` branch push).

**Real problem caught before shipping, not after**: mkdocs' `docs_dir` is `docs/` only — every
outbound link in `docs/README.md` pointing *outside* that folder (`../CLAUDE.md`,
`../backend/app/ai/README.md`, `../frontend/README.md`, `../backend/README.md`,
`../graphify-out/GRAPH_REPORT.md`) would 404 on the built site, since those files never get copied
into it. Considered a plugin (`mkdocs-same-dir`) to widen `docs_dir` to the repo root; rejected as
new complexity for what a link-format change solves for free. **Fix**: those specific links
became full `https://github.com/andrewknoesen/deck_builder/blob/main/...` URLs instead of relative
paths — resolves correctly both on the hosted site and on GitHub's own file browser, and these
files are genuinely "go look at the source repo" pointers regardless of which surface is reading
them. `graphify-out/wiki/index.md` (gitignored, never committed) was left as a plain local-path
mention rather than a link of either kind, since neither surface can serve a file that was never
pushed. Content links *within* `docs/` were left as plain relative paths — unaffected, both
audiences resolve those correctly.

**Verified**: built with a scratch venv (`mkdocs build --strict`) — clean, exit 0, only three
non-blocking `INFO`-level notes (an unrelated external commit link, two intra-page anchors in
`auth_specs.md`/`UI_DEGENERIC_DESIGN.md` that reference the subagent roster's names as prose, not
real page anchors — harmless). Served it locally (`mkdocs serve`) and drove it in the actual
browser: Home and Architecture pages both rendered correctly with the Material theme, dark mode,
and working nav. Scratch venv and build output deleted after — nothing left behind, `/site` was
already gitignored beforehand.

**Manual step resolved same day**: GitHub Pages wasn't enabled on the repo yet (confirmed via
`gh api repos/andrewknoesen/deck_builder/pages` → 404) when this was built — a repo-settings
change outside git, correctly not done silently. Asked the product owner explicitly; they said
yes, enabled via `gh api -X POST repos/andrewknoesen/deck_builder/pages` pointing at the
`gh-pages` branch. Confirmed live: the site is public and reachable at
`https://andrewknoesen.github.io/deck_builder/` — the repo itself is public, so the docs site
inherits that (no login, no access restriction; discussed explicitly with the product owner, who
confirmed public is fine for this content).

### Follow-up, same day: two dead links found on the live site

User reported "strange formatting" under Workflow Assignments on the hosted `auth_specs.md` page.
Root cause: three links to `#mtg-integrations`/`#mtg-backend`/`#mtg-frontend` anchors that don't
exist on the page, using the retired `/mtg-*` manual-slash-command style CLAUDE.md's roster
section already documents as replaced by automatic dispatch. Fixed to plain `mtg-integrations`/
`mtg-backend`/`mtg-frontend` references. Also fixed a second dead link caught by the same
`mkdocs build --strict` pass in `UI_DEGENERIC_DESIGN.md` (a relative path resolving above the
repo root) — converted to a real GitHub commit URL. Re-ran `mkdocs build --strict` clean before
pushing.

### Follow-up, same day: UI_DEGENERIC_DESIGN.md's own status banner was wrong

User asked whether the open items in `UI_DEGENERIC_DESIGN.md` were still real. They weren't —
checking git history for `frontend/src/pages/LandingPage.tsx` specifically (not just `PLAN.md` and
a general `git log`, which is what the original Phase 10 banner-writing pass had checked) found
[`0b8f770`](https://github.com/andrewknoesen/deck_builder/commit/0b8f770) (2026-08-06, reviewed by
`mtg-ux`/`mtg-em`, two rounds) had already fixed items 1-3 (font, layout, copy) one day after the
audit — it just never linked back to the doc or became a tracked `PLAN.md` phase, which is exactly
why the earlier check missed it. Item 4 (spot-checking `DeckBuilder`/`AgentChat`/`Collection`/
`DeckList` for the same generic-icon pattern) was confirmed genuinely still open — those pages
still used stock `@mui/icons-material` icons, not the bespoke glyph set. Corrected the doc's status
banner and per-item markers accordingly. See Phase 11 below for item 4 itself shipping the same
day.

### Follow-up, same day: mermaid architecture diagram

User-requested: a mermaid diagram of the architecture in the wiki. Added `pymdownx.superfences`
with the custom `mermaid` fence config to `mkdocs.yml`'s `markdown_extensions` (Material's native
Mermaid rendering — no extra JS needed, bundled by the theme) and a `graph TB` diagram at the top
of `docs/ARCHITECTURE.md`, right after the status banner: frontend → REST API → DB/Scryfall, the
`/ai` routes → ADK agent layer → Gemini + AI tools, the AI tools' fan-out to Postgres/Chroma/
Scryfall, and the MCP server's separate stdio process calling the same tools directly (bypassing
ADK, per Phase 9's own design) for an external MCP client. Also fixed a stale nav label in
`mkdocs.yml` ("UI de-genericizing (open backlog)" → "(implemented)") caught while in the file for
this change.

Verified before pushing, not assumed: `mkdocs build --strict` clean, then actually served the site
locally and screenshotted the rendered page in the browser — all subgraphs, labels, and arrows
render correctly. Renders on GitHub's own file view too (native Mermaid support), so the diagram
works whether read via the hosted site or the raw repo.

---

## Phase 11 — De-genericize the rest of the app (item 4 of docs/UI_DEGENERIC_DESIGN.md) (shipped, 2026-08-23)

### Why this one, and why now

Item 4 from `docs/UI_DEGENERIC_DESIGN.md`'s original "Suggested order of work" — spot-check
`DeckBuilder`/`AgentChat`/`Collection`/`DeckList` for the same generic-icon pattern the landing
page had, now that Phase 10's follow-up correctly identified it as the one genuinely open item
from that audit (see the Phase 10 follow-up above). User-requested directly: "Have mtg-frontend
fix item 4."

### Ground truth this plan is built on

Grepped every `@mui/icons-material` import across the four named pages and mapped each to its
actual usage context before dispatching, rather than guessing which were "feature/concept" icons
(the actual tell) versus conventional UI chrome (not the tell, per the doc's own "What generic is
not, here" section):

- `frontend/src/components/icons/` already had five bespoke glyph components from the Phase-10-
  adjacent landing-page redesign (`0b8f770`): `CardGlyphIcon`, `ManaCurveGlyphIcon`,
  `CardStackGlyphIcon`, `BinderGlyphIcon`, `BranchGlyphIcon` — each a small `SvgIcon`-based
  component with a doc comment naming the generic icon it replaces and why.
- Clear semantic matches existed for most of the stock icons in scope: `BarChartIcon` (Deck Stats
  tab) ↔ `ManaCurveGlyphIcon`, `SportsEsportsIcon` (Practice Mode button) ↔ `BranchGlyphIcon`,
  `CollectionsIcon` (Collection header + empty state) ↔ `BinderGlyphIcon`, `AutoStoriesIcon`/
  `LayersIcon` (deck-list title + empty state) ↔ `CardStackGlyphIcon`.
- Some icons in scope are conventional interaction chrome, not concept icons — `ArrowBackIcon`,
  `AddIcon`, `UploadFileIcon`, `ChevronRightIcon` — and swapping those would be exactly the
  over-application the doc's own "What generic is not, here" section warns against.
- `SmartToyIcon` (DeckBuilder's AI Advisor tab, AgentChat's page title/avatar) doesn't clearly fall
  into either bucket — a robot icon is an accurate literal label for "AI feature," not obviously a
  lazy generic default, so it was flagged as the implementer's judgment call rather than mapped.

### Concrete steps (as implemented)

Routed directly to `mtg-frontend` per the user's explicit instruction (not `mtg-ux` first, unlike
the original landing-page redesign) — reasonable given the visual language was already established
and this was applying an existing pattern consistently, not designing something new.

1. `DeckBuilder.tsx`: `BarChartIcon`→`ManaCurveGlyphIcon` (Stats tab), `SportsEsportsIcon`→
   `BranchGlyphIcon` (Practice Mode button), `GridViewIcon`→`CardStackGlyphIcon` (empty-deck
   state — chosen over `CardGlyphIcon` since `CardStackGlyphIcon` is already the established
   "Your Decks" glyph and reads better for "no cards yet").
2. `Collection.tsx`: `CollectionsIcon`→`BinderGlyphIcon`, both the header title and the empty
   state.
3. `DeckList.tsx`: `AutoStoriesIcon`→`CardStackGlyphIcon` (page title), `LayersIcon`→
   `CardStackGlyphIcon` (empty state — reused rather than picking a distinct glyph, consistent
   with the title).
4. Left alone as designed: `ArrowBackIcon`, `AddIcon`, `UploadFileIcon`, `ChevronRightIcon`
   (conventional chrome) and `SmartToyIcon` in both files (judgment call — no new glyph created,
   none required).
5. No new glyph components created — all five existing ones covered the actual need.

### Verify

`npx tsc -b` / `npx eslint .` in `frontend/` both clean (confirmed independently, not just taking
the implementer's word). Live-verified against the docker stack: `DeckList` (header + empty
state), `DeckBuilder` (stats-tab icon, practice-mode button, empty-deck state), `Collection`
(header + empty state), and `AgentChat` (spot-checked as a no-change control) — all rendered
correctly in the app's dark-slate theme, no console errors beyond two pre-existing startup-timing
`ERR_CONNECTION_RESET` entries unrelated to this change, all API calls 200. `git diff` confirmed
exactly the three files in scope changed, unused icon imports cleanly removed.

`docs/UI_DEGENERIC_DESIGN.md` updated: all four findings now marked done, status banner corrected
to "fully implemented," no open items remain from that audit. `docs/README.md`'s status table
updated to match.

---

## Deferred (explicit choice, not an oversight)

Production-readiness was considered and deliberately deprioritized behind feature work. Recorded
here so it isn't forgotten, not because it's next:

- **Real auth**: `POST /auth/login` is a placeholder; `get_current_user`
  (`backend/app/api/deps.py`) ignores any bearer token entirely and always returns the first `User`
  row in the DB (auto-creating one if none exists). The frontend's "Sign In" button
  (`MainLayout.tsx`) calls `login("mock-jwt-token")` — a hardcoded string, no real Google OAuth
  flow exists yet. Net effect: **the app is currently single-tenant** — every browser/session
  shares the same one user's decks/collection/goldfish data, not just "auth is unverified."
  `docs/auth_specs.md` has the unimplemented design. **Explicitly gated on the user's own
  judgment**, confirmed 2026-08-04: release to friends/family happens whenever they personally deem
  the app "complete and finished," not on a fixed date — real auth is a pre-release blocker at that
  point, not something to build proactively before then.
- **CI**: Renovate (dependency bumps) and, as of Phase 10's mkdocs follow-up, a narrowly
  path-filtered docs-deploy workflow (`.github/workflows/docs.yml`, builds/deploys the mkdocs
  site on `docs/**` changes only) are the only workflows in `.github/workflows/`. Nothing runs
  `pytest`/`ruff`/`eslint` on PRs. The pytest-collection break fixed in Phase 0 could sit
  undetected indefinitely under this setup.
- **Deployment target**: no `fly.toml`/`render.yaml`/Procfile/etc. anywhere — `docker-compose.yml`
  is local-dev only. Nothing to change until there's a decision on where this actually runs.
- **Stored `cmc` column on `Card`**: raised 2026-08-23 during Phase 8 review — Phase 8 deliberately
  kept mana value as parsed-on-write from `Card.mana_cost` (via `calculate_cmc`) rather than adding
  a stored numeric column, since a migration + backfill + threading `cmc` through three
  card-persistence call sites (`decks.py`, `collection.py`, `scryfall_ingestion.py`) wasn't worth it
  just to save a cheap string parse done once per `cast` action. User flagged a real future reason
  this calculus could change: a stored `cmc` is something **agents would want to reference directly**
  once the app starts using agents to build/suggest decks (cheaper for an agent to filter/sort/reason
  over than re-parsing `mana_cost` per candidate card). Not needed yet — no such agent capability
  exists today. Revisit if/when an agent-driven deck-building feature is actually scoped, not before.

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
