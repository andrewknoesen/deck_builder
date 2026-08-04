import React, { useState, type ReactNode } from "react";
import type { ScryfallCard } from "../types/mtg";
import { CardHoverContext } from "./useCardHover";

export const CardHoverProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [hoveredCard, setHoveredCard] = useState<ScryfallCard | null>(null);

  return (
    <CardHoverContext.Provider value={{ hoveredCard, setHoveredCard }}>
      {children}
    </CardHoverContext.Provider>
  );
};
