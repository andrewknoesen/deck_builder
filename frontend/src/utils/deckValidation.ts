
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

export const getCardLimit = (
  format: string = "Commander",
  card?: { type_line?: string; oracle_text?: string }
): number => {
  if (!card) return 4;

  const f = format.toLowerCase();
  
  // Basic Lands are unlimited (technically 99/60 etc, but effectively unlimited)
  if (card.type_line?.includes("Basic Land")) {
    return 99;
  }

  // Cards that say "A deck can have any number of cards named..."
  if (card.oracle_text?.includes("A deck can have any number of cards named")) {
    return 99;
  }

  // Singleton formats
  if (f === "commander" || f === "edh" || f === "brawl" || f === "oathbreaker") {
    return 1;
  }

  // Limited formats - essentially unlimited pool
  if (f === "limited" || f === "draft" || f === "sealed") {
    return 99;
  }

  // Standard, Modern, Pioneer, etc.
  return 4;
};
