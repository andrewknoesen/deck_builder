import React, { createContext, useContext, useState, type ReactNode } from "react";
import type { ScryfallCard } from "../types/mtg";

interface CardHoverContextType {
  hoveredCard: ScryfallCard | null;
  setHoveredCard: (card: ScryfallCard | null) => void;
}

const CardHoverContext = createContext<CardHoverContextType | undefined>(undefined);

export const CardHoverProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [hoveredCard, setHoveredCard] = useState<ScryfallCard | null>(null);

  return (
    <CardHoverContext.Provider value={{ hoveredCard, setHoveredCard }}>
      {children}
    </CardHoverContext.Provider>
  );
};

export const useCardHover = () => {
  const context = useContext(CardHoverContext);
  if (!context) {
    throw new Error("useCardHover must be used within a CardHoverProvider");
  }
  return context;
};
