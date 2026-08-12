export interface GoldfishSession {
  id: number;
  deck_id: number;
  opponent_deck_id: number | null;
  user_id: number;
  name: string;
  created_at: string;
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
