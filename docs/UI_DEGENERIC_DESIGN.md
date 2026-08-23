# De-genericizing the UI: why it still reads "AI-generated"

> **Status: fully implemented (2026-08-23).** Items 1-3 (font, landing-page layout, landing-page
> copy) were fixed in [`0b8f770`](https://github.com/andrewknoesen/deck_builder/commit/0b8f770)
> (2026-08-06, reviewed by `mtg-ux`/`mtg-em`). Item 4 (extending bespoke glyph icons to the rest of
> the app) shipped 2026-08-23 via `mtg-frontend` — see `PLAN.md`'s Phase 11 for the full record.
> All four findings closed; no open items remain from this audit.

Audit date: 2026-08-06. Scope: `frontend/src/pages/LandingPage.tsx` + `frontend/src/theme.ts`,
extrapolated to the rest of the app's component patterns (`DeckBuilder`, `AgentChat`,
`Collection`, `DeckList`). Triggered by
[f4b67ff](https://github.com/andrewknoesen/deck_builder/commit/f4b67ff) (the warm/gold palette
work) — the palette fix was real progress, but it's one of four tells, and the other three are
untouched.

## Why this matters here specifically

The "AI slop" look isn't really about any single choice being *bad* — Inter is a fine font,
gold-on-black is a good palette, three feature bullets is a reasonable IA. It's that every choice
is the **statistically safest default**, so the product reads as *a* SaaS tool rather than *this*
SaaS tool. For an MTG deck builder, that's a wasted opportunity: Magic has 30 years of extremely
specific, recognizable visual language (mana symbols, card frames, set symbols, foil texture,
rarity gems) that no generic AI output would ever reach for on its own, because it isn't in the
median of "landing page" training data. Leaning on that domain vocabulary is the cheapest way to
stop looking generic, because a competitor's AI-assisted clone literally cannot default into it.

## The four tells, and where this codebase has each one

Cross-referenced against multiple 2025–2026 write-ups on why AI-generated UI converges
([SmoothUI](https://smoothui.dev/blog/ai-design-slop),
[925 Studios](https://www.925studios.co/blog/ai-slop-design-tells),
[Superdesign](https://superdesign.dev/blog/why-ai-design-looks-generic),
[BrainGrid](https://www.braingrid.ai/blog/design-system-optimized-for-ai-coding)) — they
converge on the same four fingerprints. Below, each is graded against what's actually in this repo.

### 1. Font — ✅ fixed, 2026-08-06

`theme.ts` now sets `h1`-`h4` to `"Besley", serif`, keeping Inter only for body/UI chrome — exactly
the fix suggested below. Original finding kept for context:

```ts
fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
```
This is the single most-cited tell. Inter is "the most-used interface font in [an LLM's] training
data" — using it undifferentiated, with the stock MUI fallback stack behind it, is the
typographic equivalent of not making a choice at all. The color work in `theme.ts` has a
paragraph of deliberate reasoning behind it (OKLCH, WCAG contrast, "not Tailwind's stock
Slate scale"); the font has zero.

**Fix:** pick a display face for headlines that has actual character — MTG's own branding leans
on serif/slab display faces for card names and set text (think the weight of card-frame
typography, not a SaaS dashboard). Keep Inter or similar for body/UI chrome where legibility at
small sizes matters, but stop using it for `h1`–`h3`. This alone changes the landing page's
silhouette more than any other single fix.

### 2. Layout — ✅ fixed, 2026-08-06 (landing page) + 2026-08-23 (rest of the app, item 4)

The landing page uses an asymmetric primary-feature/paired-row/illustrated-row layout with live
Scryfall card art and five bespoke glyph icons (`CardGlyphIcon`, `ManaCurveGlyphIcon`,
`CardStackGlyphIcon`, `BinderGlyphIcon`, `BranchGlyphIcon`), no sparkle emoji. `DeckBuilder`,
`Collection`, and `DeckList` now reuse those same glyphs for their feature/concept icons instead
of stock Material icons (see item 4 in "Suggested order of work" below for the exact mapping).
Original finding kept for context — this described the pre-fix layout:

`LandingPage.tsx` (rendered, see screenshot evidence below) was, structurally:
- Centered hero: giant bold headline with one word in accent color, one line of gray subtext,
  divider.
- One "hero card": sparkle icon (✨) → bold heading → two lines of gray body copy → pill CTA
  button with a trailing arrow.
- Three feature rows: generic thin-line icon → bold one-line heading → one line of gray
  description → divider. (`Your Decks`, `Collection`, `Practice Mode`.)

This is, near-verbatim, the pattern named in every source above: "three cards, each with an icon,
a heading, and two lines of text," "a bounce on every hover," generic pill CTAs with arrows. It's
implemented as a vertical list instead of a horizontal card row, which hides it at first glance,
but it's the same information architecture.

**Fix:** break the symmetry. Options, roughly in order of effort:
- Give the three features *unequal* visual weight instead of identical icon+heading+line rows —
  e.g. one gets a real screenshot/mini-demo, the other two stay text.
  Asymmetry is called out specifically as the fix for the "three-card" tell.
  - Replace the sparkle emoji with something MTG-specific — a mana symbol, a stylized card
  silhouette, a set-symbol-style glyph. ✨ is itself a cliché "AI magic" signifier and reads as
  doubly generic here.
- Use actual card art (Scryfall images the app already has access to) as background/texture in
  the hero instead of flat `#110c07`. Right now the hero is compositionally identical to any
  B2B SaaS landing page with the copy swapped out.

### 3. Copy — ✅ fixed, 2026-08-06

The landing page headline is now "Goldfish your list before you sleeve it up" with a subhead
citing real, falsifiable mechanics ("hypergeometric draw-odds instead of a rule of thumb") —
almost exactly the fix suggested below, including the MTG-native phrasing example. Original
finding kept for context — this described the pre-fix copy:

"Build decks that actually win." / "Start Brewing" / "no guesswork" / "Instant card search with
live previews." Every one of these lines could be true of a different product with a find-and-replace
of nouns. This is what the SmoothUI/925 Studios pieces call "weightless headline copy" — the tell
isn't grammatical, it's that nothing in the sentence is falsifiable or specific to *this* tool.

**Fix:** replace generic claims with specifics only this app can say — an actual number
(cards indexed, rules ingested, formats supported), a real mechanic ("hypergeometric draw-odds,
not a rule of thumb"), or MTG-native language a player would actually use ("goldfish your list
before you sleeve it up" instead of "stress-test decks"). The existing subhead
("real Scryfall data, real mana-curve math, no guesswork") is already halfway there — "real
Scryfall data" is specific; "no guesswork" is filler. Cut the filler half.

### 4. Color — ✅ deliberately overridden, still not the tell

**Update, 2026-08-06:** the original gold-on-warm-black palette was replaced with a dark slate
theme at the product owner's explicit request (personal preference — the gold/red/green combo
read as "neon," not an AI-slop finding). Current values live in `theme.ts:10-33`: a muted
steel-blue accent (`#5b7fa3`) on cool near-black neutrals (`#12151a`/`#1a1e25`), with desaturated
danger/success colors. This does **not** reopen the color tell. The tell named in the sources
below is specifically *unmodified Tailwind defaults with zero justification* — indigo-to-purple
gradients, raw `indigo-500`, decorative rather than functional color use. A considered, documented,
non-purple, non-gradient accent on neutral slate isn't that, even though the earlier version of
this doc used "slate" as shorthand for the generic case. The things to keep watching for as this
palette gets implemented:
- Don't let the accent drift toward indigo/purple or reintroduce a gradient.
- Keep it non-decorative — accent color still gated to primary actions/selection state only.
- Keep the "why" comment in `theme.ts` current (it already documents this change) — that inline
  justification is the actual anti-generic discipline here, independent of which hue is chosen.

## What "generic" is not, here

Two things worth being explicit about so this doc doesn't get over-applied:
- **Sharp (non-rounded) `MuiCard` panels vs. rounded buttons** (`theme.ts:53,61`) is already a
  deliberate, documented asymmetry — don't "fix" it by rounding everything to match, that would
  be reverting toward the default, not away from it.
- Dark mode + a single accent color is not itself a tell. Purple/indigo specifically is the tell,
  because it's Tailwind's `indigo-500` default. Gold was fine; the current muted steel-blue is
  fine too — see the color update in item 4 above.

## Suggested order of work

1. ✅ **Done, 2026-08-06.** Typography pass (`theme.ts` font stack + a scale that isn't MUI
   defaults) — highest visual impact for the effort, touches every page at once via the theme.
2. ✅ **Done, 2026-08-06.** Landing page hero/feature-section rewrite — asymmetric layout,
   card-art texture, kill the sparkle emoji, MTG-specific iconography.
3. ✅ **Done, 2026-08-06.** Copy pass across `LandingPage.tsx` — can happen in parallel with (2),
   same file.
4. ✅ **Done, 2026-08-23.** Spot-checked `DeckBuilder`, `Collection`, `DeckList` and swapped their
   feature/concept icons for the existing bespoke glyphs: `BarChartIcon`→`ManaCurveGlyphIcon`
   (Stats tab), `SportsEsportsIcon`→`BranchGlyphIcon` (Practice Mode button),
   `GridViewIcon`→`CardStackGlyphIcon` (empty-deck state), `CollectionsIcon`→`BinderGlyphIcon`
   (Collection header + empty state), `AutoStoriesIcon`/`LayersIcon`→`CardStackGlyphIcon` (deck
   list title + empty state). Functional UI chrome (back/add/upload/chevron arrows) was
   deliberately left alone — conventional affordances, not the tell. `SmartToyIcon` (AI
   Advisor/AI Rules Judge, in both `DeckBuilder.tsx` and `AgentChat.tsx`) was also deliberately
   left alone: it's an accurate literal label for "this is an AI feature," not a lazy generic
   default — no MTG-flavored replacement was created for it, and none is required.

Route this to `mtg-ux` for the actual visual/interaction redesign and `mtg-frontend` for
implementation, per the existing subagent split in `CLAUDE.md`.

## Sources

- [AI Design Slop: Why AI-Generated UI Looks Generic — and the Fix (SmoothUI)](https://smoothui.dev/blog/ai-design-slop)
- [AI Slop Fonts and Gradients: The Tells That Give Away AI Design (925 Studios)](https://www.925studios.co/blog/ai-slop-design-tells)
- [Why AI Design Looks Generic (Superdesign)](https://superdesign.dev/blog/why-ai-design-looks-generic)
- [Design Systems for AI Coding: Stop Getting Purple Gradients (BrainGrid)](https://www.braingrid.ai/blog/design-system-optimized-for-ai-coding)
- [Why AI-Generated UI Looks Good But Often Feels Generic (Medium)](https://medium.com/@cssamithpitigala/why-ai-generated-ui-looks-good-but-often-feels-generic-020a9b1b8492)
