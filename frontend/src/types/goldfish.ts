export interface GoldfishSession {
  id: number;
  deck_id: number;
  opponent_deck_id: number | null;
  user_id: number;
  name: string;
  created_at: string;
  // Manual, session-level, freely-editable outcome (Phase 7) — null means
  // "not recorded." Not tied to any specific tree branch/node.
  outcome: "win" | "loss" | "draw" | null;
}

export interface GoldfishAnalytics {
  session_count: number;
  sessions_with_outcome: number;
  wins: number;
  losses: number;
  draws: number;
  // None/null when their denominator is zero/undefined — never coerced to 0.
  win_rate: number | null;
  average_max_turn: number | null;
  two_deck_session_ratio: number | null;
}

export interface Zones {
  library: string[];
  hand: string[];
  battlefield: string[];
  graveyard: string[];
  exile: string[];
}

export interface GameState extends Zones {
  life_total: number;
  opponent_life_total: number;
  // Typed as always-present (matching every node created from Phase 3d
  // onward, where `.model_dump()` always includes an explicit `opponent_zones:
  // null`) even though it's genuinely absent (not `null`) on nodes created
  // before this phase, since `state` is stored as raw JSON and never
  // re-validated through GameState on read. `Zones | null` still handles both
  // cases fine as long as nothing does a strict `=== null`/`=== undefined`
  // check against this field.
  opponent_zones: Zones | null;
  // Phase 8 mana-spent tracker (backend-computed, sum of cast mana values).
  // Typed as always-present, matching `opponent_zones` above, even though
  // it's genuinely absent (not `0`) on nodes created before this phase,
  // since `state` is stored as raw JSON and never re-validated through
  // GameState on read. Default to 0 defensively on read.
  mana_spent: number;
  opponent_mana_spent: number;
}

export type GoldfishZone = "library" | "hand" | "battlefield" | "graveyard" | "exile";

export interface GoldfishAction {
  type:
    | "draw"
    | "play_land"
    | "cast"
    | "move_zone"
    | "set_life"
    | "shuffle"
    | "next_turn";
  card_id?: string;
  from_zone?: GoldfishZone;
  to_zone?: GoldfishZone;
  life_total?: number;
  target?: "self" | "opponent";
}

export interface GoldfishNode {
  id: number;
  session_id: number;
  parent_id: number | null;
  label: string;
  turn_number: number | null;
  order_index: number;
  // Generic named-counter snapshot at this node (life, poison, storm count,
  // whatever) - an opaque key->value map, not a fixed set of fields.
  trackers: Record<string, number> | null;
  // Phase 3b game-state snapshot (library/hand/battlefield/graveyard/exile +
  // life_total). Null for plain 3a free-text sessions/notes.
  state: GameState | null;
  created_at: string;
}

export interface GoldfishSessionTree {
  session: GoldfishSession;
  nodes: GoldfishNode[];
}
