
export interface ValidationResult {
  valid: boolean;
  message?: string;
  severity: "success" | "warning" | "error" | "info";
}

export const validateDeckSize = (
  format: string = "Commander",
  totalCards: number
): ValidationResult => {
  const f = format.toLowerCase();

  if (f === "commander" || f === "edh") {
    if (totalCards === 100) {
      return { valid: true, severity: "success", message: "Deck size is legal." };
    }
    const diff = 100 - totalCards;
    return {
      valid: false,
      severity: "error",
      message:
        diff > 0
          ? `Commander decks must have exactly 100 cards. Add ${diff} more.`
          : `Commander decks must have exactly 100 cards. Remove ${Math.abs(diff)}.`,
    };
  }

  if (f === "brawl" || f === "oathbreaker") {
    if (totalCards === 60) {
      return { valid: true, severity: "success", message: "Deck size is legal." };
    }
    const diff = 60 - totalCards;
    return {
      valid: false,
      severity: "error",
      message:
        diff > 0
          ? `${format} decks must have exactly 60 cards. Add ${diff} more.`
          : `${format} decks must have exactly 60 cards. Remove ${Math.abs(diff)}.`,
    };
  }

  if (f === "limited" || f === "draft" || f === "sealed") {
    if (totalCards >= 40) {
      return { valid: true, severity: "success", message: "Deck size is legal." };
    }
    return {
      valid: false,
      severity: "warning",
      message: `Limited decks require at least 40 cards. Add ${40 - totalCards} more.`,
    };
  }

  // Standard, Modern, Pioneer, Legacy, Vintage, etc.
  if (totalCards >= 60) {
    return { valid: true, severity: "success", message: "Deck size is legal." };
  }
  return {
    valid: false,
    severity: "warning",
    message: `${format} decks usually require at least 60 cards.`,
  };
};
