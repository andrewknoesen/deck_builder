# deck_builder — Plan

Full per-phase detail (Why/Ground truth/Design/Interview outcome/Concrete steps/Shipped writeups)
lives in [`MEMORY.md`](MEMORY.md), not here — this file keeps only the current summary below and
what's still actionable (`## Deferred`).

## Status

**Phase 0 (repo cleanup) — done, 2026-07-08.** Fixed a broken test suite, stale/misleading docs,
dead scaffolding, and a real structural bug (a single-member uv workspace that put the host and
Docker's backend container in a file-system race over the same `.venv`). See `MEMORY.md`'s Phase 0
archive for the full record, or `git log` — it landed as 9 commits on
`feature/agent_factory`, most recently `refactor: collapse single-member uv workspace`.

**Phase 2 (Deck Import) — done, 2026-07-08.** Built ahead of Phase 1 (AI advisor) — goldfishing
(Phase 3) needs decks easily importable to test against, and there was no reason to block that on
the advisor shipping first. `POST /decks/import` + `DeckImportModal`, best-effort resolution with
an inline search-to-replace path for unresolved cards. See `MEMORY.md`'s Phase 2 for the full record.

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
opening hands auto-deal at session start (product owner decision, 2026-08-09). See `MEMORY.md`'s
Phase 3d for the full design.

Under review, per the product owner's explicit "any gate finding sends the whole plan through
every agent again, no exceptions" process: all five specialists (`mtg-architect`, `mtg-backend`,
`mtg-frontend`, `mtg-qa`, `mtg-ux`) review their own portion, `mtg-em` gates last, any gate finding
restarts the full cycle. Multiple rounds completed; fixes are cited inline where they landed in
`MEMORY.md`'s Phase 3d section, most tagged with round and/or reviewer — that inline record is authoritative
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
just documentation of the prior behavior; see the "Same-format restriction" note under Phase 3d's
Design section in `MEMORY.md` for the full reasoning and the explicitly-deferred future relaxation. Folded into Design,
Concrete Steps, and Verify.

**Phase 3d shipped, 2026-08-11.** Routed to `mtg-backend` (Concrete Steps 1-2) then `mtg-frontend`
(Steps 3-4), in that order since the frontend's opponent board renders against the backend's real
response shape. See "Shipped" under Phase 3d in `MEMORY.md` for the full record, including the one
deviation from the plan (a synchronous double-submit guard, needed to actually satisfy the plan's
own rapid-double-click Verify requirement) and the live verification actually performed.

**Phase 3c parked, 2026-08-12 (user decision).** Not deleted from this file, not "revisit after
3a/3b" anymore either — explicitly on hold with no next-pick-up trigger, superseded by Phase 5
as the thing actually being worked on next. Revisit only if the user brings it back up.

**Phase 5 (AI-assisted card search for deck building) — picked up next, 2026-08-12.** User-
requested: a conversational agent on the deck-building page for synergy-style card discovery
("cards that benefit from artifacts leaving the battlefield," "cards that deal damage when an
artifact enters") — a fundamentally different query shape than Scryfall's keyword/operator search
or `deck_advisor_agent`'s existing `search_cards` tool, closer to semantic/vector search over card
oracle text. User's own opening framing: a SQL + vector-DB hybrid. Routed to `mtg-architect` first
for a design pass before any interview or implementation, per this file's own convention for
anything crossing backend AI layer + data pipeline + frontend. See `MEMORY.md`'s Phase 5 once
that lands.

**Phase 5 shipped, 2026-08-12.** `search_cards_semantic`/`CardRAG` over a new `mtg_cards` Chroma
collection, a shared sentence-transformer embedder between `RulesRAG` and `CardRAG`, and a manual
`card_embedding_ingestion.py` script. Live-verified end-to-end against the real stack. See
`MEMORY.md`'s Phase 5 for the full record.

**Phase 6 (Per-card synergy lookup) and Phase 7 (Goldfish session analytics) — picked up next,
2026-08-15.** Both user-requested in the same brainstorming session, in this stated priority order
(synergy lookup first). Both routed to `mtg-architect` for a design pass before any interview or
implementation, run in parallel since the two are independent of each other (different subsystems:
AI/deck-building vs. goldfishing). Design passes and product-owner interviews both complete for
each — every open question resolved to the blueprint's own recommended default, no deviation.
**Phase 7 shipped, 2026-08-15** (backend then frontend, no scope deviation, live-verified against
the real docker stack). **Phase 6 shipped, 2026-08-16** (frontend-only as designed, live-verified
against the real docker stack after isolating one transient Gemini-API blip from the actual code).
See `MEMORY.md`'s Phase 6 and Phase 7 sections for the full record.

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
outcome). See "Shipped" under Phase 8 in `MEMORY.md` for the full record, including the corrected `{X}`
mana-value numbers and both the playmat and tree-node surfaces live-verified against the real
docker stack, single-deck and two-deck.

**Phase 9 shipped, 2026-08-23** (backend-only, matching the design — no frontend surface for an
MCP server). One dependency-version deviation (`mcp<2`, pinned against a same-day `2.0.0` release
that renamed the API this design was built against) and one real bug found and fixed during live
verification (stdout logging corrupting the stdio JSON-RPC stream). See "Shipped" under Phase 9
in `MEMORY.md` for the full record, including the genuine MCP wire-protocol client verification performed.

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
Phase 10 in `MEMORY.md` for the full record.

**Phase 11 (De-genericize the rest of the app) shipped, 2026-08-23** — the one item Phase 10's
correction found genuinely still open: `DeckBuilder`/`Collection`/`DeckList` now reuse the landing
page's bespoke MTG glyph icons instead of stock Material icons, closing out
`docs/UI_DEGENERIC_DESIGN.md` entirely. See `MEMORY.md`'s Phase 11 for the full record.

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
