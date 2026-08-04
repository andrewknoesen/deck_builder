import { createContext, useContext } from "react";
import type { ScryfallCard } from "../types/mtg";

export interface CardHoverContextType {
  hoveredCard: ScryfallCard | null;
  setHoveredCard: (card: ScryfallCard | null) => void;
}

export const CardHoverContext = createContext<CardHoverContextType | undefined>(undefined);

export const useCardHover = () => {
  const context = useContext(CardHoverContext);
  if (!context) {
    throw new Error("useCardHover must be used within a CardHoverProvider");
  }
  return context;
};
