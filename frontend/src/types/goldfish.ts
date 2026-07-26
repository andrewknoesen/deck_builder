export interface GoldfishSession {
  id: number;
  deck_id: number;
  user_id: number;
  name: string;
  created_at: string;
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
  created_at: string;
}

export interface GoldfishSessionTree {
  session: GoldfishSession;
  nodes: GoldfishNode[];
}
