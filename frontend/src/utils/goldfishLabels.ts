// Second-person-pronoun forms that would otherwise collide with the self
// board's own "You"/"Your ..." labels if a deck were literally titled one of
// these (e.g. a deck named "Your" would render the confusable "Your's Hand
// (N)"). Case-insensitive, matched against the trimmed title.
const PRONOUN_COLLISIONS = new Set(["you", "your", "yours"]);

/**
 * The opponent board's `ownerLabel` for Phase 3d two-deck goldfishing: the
 * opponent deck's title, trimmed, falling back to "Opponent" when that
 * trimmed result is empty (including whitespace-only titles) or collides
 * with a second-person pronoun that would otherwise be confusable with the
 * self board's own "You"/"Your ..." labels.
 */
export function opponentOwnerLabel(deckTitle: string | undefined): string {
  const trimmed = (deckTitle ?? "").trim();
  if (!trimmed || PRONOUN_COLLISIONS.has(trimmed.toLowerCase())) {
    return "Opponent";
  }
  return trimmed;
}
