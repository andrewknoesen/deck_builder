# MTG Deck Builder — Frontend

React 18 + TypeScript + Vite frontend for the MTG Deck Builder app. Tailwind + MUI for UI,
`react-query` for API state.

## Dev Setup

```bash
npm install
npm run dev      # http://localhost:5173, proxies API calls to the backend
```

Other scripts: `npm run build`, `npm run lint`.

The API base URL is read from `VITE_API_URL` (see `src/api/client.ts`); it defaults to `/api/v1`
if unset, which works out of the box with the Docker Compose dev stack.

## Structure

- `src/pages/` — top-level routes (`AgentChat`, `DeckBuilder`, `DeckList`, `Collection`, `LandingPage`, ...)
- `src/components/` — shared UI components
- `src/api/` — API client layer
- `src/context/` — React context providers (e.g. auth)
- `src/hooks/` — custom hooks
- `src/types/` — shared TypeScript types
- `src/utils/`, `src/styles/`, `src/assets/` — helpers, global styles, static assets

See the root [`CLAUDE.md`](../CLAUDE.md) for overall project architecture and conventions.
