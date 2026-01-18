export interface ScryfallCard {
    id: string;
    name: string;
    mana_cost?: string;
    type_line?: string;
    oracle_text?: string;
    colors?: string[];
    image_uris?: {
        small: string;
        normal: string;
        large: string;
        png: string;
        art_crop: string;
        border_crop: string;
    };
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
