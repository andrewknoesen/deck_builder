export interface ScryfallCard {
    id: string;
    name: string;
    mana_cost?: string;
    type_line?: string;
    oracle_text?: string;
    colors?: string[];
    produced_mana?: string[];
    image_uris?: {
        small: string;
        normal: string;
        large: string;
        png: string;
        art_crop: string;
        border_crop: string;
    };
    legalities?: Record<string, string>;
}

export interface DeckCard {
    card_id: string;
    quantity: number;
    board: string;
    card?: ScryfallCard; // Joined for UI
}

export interface Deck {
    id?: number;
    title: string;
    format?: string;
    user_id: number;
    cards?: DeckCard[];
}

export interface CollectionCard {
    id: number;
    card_id: string;
    quantity: number;
    card?: ScryfallCard;
}

export interface DeckStatsRecommendation {
    land_count: number;
    ramp_count: number;
    cantrip_count: number;
    reasoning: string;
}

export interface DeckStatsDrawOdds {
    opening_hand: {
        lands_at_least_2: number;
        lands_at_least_3: number;
        lands_at_least_4: number;
    };
    on_curve: {
        turn_3_land_drop: number;
        turn_4_land_drop: number;
    };
}

export interface DeckStatsResponse {
    total_cards: number;
    mana_curve: Record<string, number>;
    average_cmc: number;
    recommendations: DeckStatsRecommendation;
    color_stats?: Record<string, { pips: number; sources: number; recommended_sources: number }>;
    draw_odds?: DeckStatsDrawOdds;
}
