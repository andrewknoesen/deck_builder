import React, { useMemo } from "react";
import { Box } from "@mui/material";
import type { DeckCard, DeckStatsResponse } from "../types/mtg";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { DeckConstructionGuide } from "./DeckStats/DeckConstructionGuide";
import { DrawProbabilityStats } from "./DeckStats/DrawProbabilityStats";
import { ManaCurveChart } from "./DeckStats/ManaCurveChart";
import { ManaColorAnalysis } from "./DeckStats/ManaColorAnalysis";
import { DeckSummary } from "./DeckStats/DeckSummary";

interface DeckStatsProps {
  cards: DeckCard[];
  deckId?: number;
}

interface StatsData {
  curve: number[];
  colors: Record<
    string,
    { pips: number; sources: number; recommended_sources: number }
  >;
  totalCards: number;
  totalLands: number;
}

export const DeckStats: React.FC<DeckStatsProps> = ({ cards, deckId }) => {
  // Fetch server-side stats for recommendations
  const { data: serverStats, isLoading } = useQuery<DeckStatsResponse>({
    queryKey: ["deckStats", deckId],
    queryFn: async () => {
      if (!deckId) return null;
      const res = await apiClient.get(`/decks/${deckId}/stats`);
      return res.data;
    },
    enabled: !!deckId,
  });

  const stats = useMemo<StatsData>(() => {
    // If server stats are available and contain color stats, use them for the colors portion
    // But we still need curve and totals
    const curve = Array(8).fill(0);
    const colors: Record<
      string,
      { pips: number; sources: number; recommended_sources: number }
    > = {
      W: { pips: 0, sources: 0, recommended_sources: 0 },
      U: { pips: 0, sources: 0, recommended_sources: 0 },
      B: { pips: 0, sources: 0, recommended_sources: 0 },
      R: { pips: 0, sources: 0, recommended_sources: 0 },
      G: { pips: 0, sources: 0, recommended_sources: 0 },
      C: { pips: 0, sources: 0, recommended_sources: 0 },
    };

    let totalCards = 0;
    let totalLands = 0;

    cards.forEach((dc) => {
      if (!dc.card) return;
      const qty = dc.quantity;
      totalCards += qty;

      // Mana Curve
      if ((dc.card.type_line || "").includes("Land")) {
        totalLands += qty;

        // Count Sources (Client-side fallback)
        const produced = dc.card.produced_mana || [];
        produced.forEach((c) => {
          if (colors[c]) colors[c].sources += qty;
        });
      } else {
        const cost = dc.card.mana_cost || "";
        let calculatedCmc = 0;
        const numbers = cost.match(/\{(\d+)\}/);
        if (numbers) calculatedCmc += parseInt(numbers[1]);
        const pipsMatch = cost.match(/\{([WUBRG])\}/g);

        // Count Pips (Client-side fallback)
        if (pipsMatch) {
          calculatedCmc += pipsMatch.length;
          pipsMatch.forEach((pip) => {
            const colorChar = pip.replace(/{|}/g, "");
            if (colors[colorChar]) colors[colorChar].pips += qty;
          });
        }

        const bucket = Math.min(calculatedCmc, 7);
        curve[bucket] += qty;
      }
    });

    // If server provides richer stats (specifically recommended sources), merge them in
    if (serverStats?.color_stats) {
      Object.keys(colors).forEach((c) => {
        if (serverStats.color_stats && serverStats.color_stats[c]) {
          colors[c] = serverStats.color_stats[c];
        }
      });
    }

    return {
      curve,
      colors,
      totalCards,
      totalLands,
    };
  }, [cards, serverStats]);

  return (
    <Box sx={{ p: 3 }}>
      <DeckConstructionGuide
        serverStats={serverStats}
        totalCards={stats.totalCards}
        totalLands={stats.totalLands}
        isLoading={isLoading}
      />

      {serverStats?.draw_odds && (
        <DrawProbabilityStats drawOdds={serverStats.draw_odds} />
      )}

      <ManaCurveChart curve={stats.curve} />

      <ManaColorAnalysis colors={stats.colors} />

      <DeckSummary
        totalCards={stats.totalCards}
        totalLands={stats.totalLands}
      />
    </Box>
  );
};
