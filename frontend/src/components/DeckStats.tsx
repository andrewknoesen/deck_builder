import React, { useMemo } from "react";
import { Box, Typography, Paper, Grid, Stack, CircularProgress } from "@mui/material";
import type { DeckCard, DeckStatsResponse } from "../types/mtg";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import LightbulbIcon from '@mui/icons-material/Lightbulb';

interface DeckStatsProps {
  cards: DeckCard[];
  deckId?: number;
}

interface StatsData {
  curve: number[];
  colors: Record<string, { pips: number; sources: number; recommended_sources: number }>;
  manaProduction: Record<string, number>;
  totalCards: number;
  totalLands: number;
}

export const DeckStats: React.FC<DeckStatsProps> = ({ cards, deckId }) => {
  // Fetch server-side stats for recommendations
  const { data: serverStats, isLoading } = useQuery<DeckStatsResponse>({
      queryKey: ['deckStats', deckId],
      queryFn: async () => {
          if (!deckId) return null;
          const res = await apiClient.get(`/decks/${deckId}/stats`);
          return res.data;
      },
      enabled: !!deckId
  });

  const stats = useMemo<StatsData>(() => {
    // If server stats are available and contain color stats, use them for the colors portion
    // But we still need curve and totals
    const curve = Array(8).fill(0);
    const colors: Record<string, { pips: number; sources: number; recommended_sources: number }> = {
      W: { pips: 0, sources: 0, recommended_sources: 0 },
      U: { pips: 0, sources: 0, recommended_sources: 0 },
      B: { pips: 0, sources: 0, recommended_sources: 0 },
      R: { pips: 0, sources: 0, recommended_sources: 0 },
      G: { pips: 0, sources: 0, recommended_sources: 0 },
      C: { pips: 0, sources: 0, recommended_sources: 0 },
    };
    
    // Legacy support for simple production view if needed, but 'colors' handles it now
    const manaProduction: Record<string, number> = {}; 

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
            pipsMatch.forEach(pip => {
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
        Object.keys(colors).forEach(c => {
            if (serverStats.color_stats && serverStats.color_stats[c]) {
                colors[c] = serverStats.color_stats[c];
            }
        });
    }

    return { curve, colors, manaProduction, totalCards, totalLands };
  }, [cards, serverStats]);

  const maxCurve = Math.max(...stats.curve, 1);

  return (
    <Box sx={{ p: 3 }}>
        {/* Recommendation Guide */}
        <Paper elevation={0} variant="outlined" sx={{ p: 3, mb: 4, bgcolor: 'primary.50', borderColor: 'primary.200' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <LightbulbIcon color="primary" />
                <Typography variant="h6" fontWeight="800" color="primary.main">
                    Deck Construction Guide
                </Typography>
            </Box>
            
            {isLoading ? (
                 <CircularProgress size={24} />
            ) : serverStats ? (
                <Grid container spacing={3}>
                    <Grid size={{ xs: 12, md: 6 }}>
                        <Typography variant="subtitle2" fontWeight="700" color="text.secondary" gutterBottom>
                            RECOMMENDED LANDS
                        </Typography>
                        <Stack direction="row" alignItems="baseline" spacing={1}>
                            <Typography variant="h3" fontWeight="900" color="primary.main">
                                {serverStats.recommendations.land_count}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                / {stats.totalCards} cards
                            </Typography>
                        </Stack>
                         <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                            Current: <strong>{stats.totalLands}</strong>
                        </Typography>
                    </Grid>
                     <Grid size={{ xs: 12, md: 6 }}>
                        <Typography variant="subtitle2" fontWeight="700" color="text.secondary" gutterBottom>
                            ANALYSIS
                        </Typography>
                        <Typography variant="body1">
                            {serverStats.recommendations.reasoning}
                        </Typography>
                        <Stack direction="row" spacing={3} sx={{ mt: 2 }}>
                            <Box>
                                <Typography variant="caption" fontWeight="bold" display="block">AVG CMC</Typography>
                                <Typography variant="h6">{serverStats.average_cmc}</Typography>
                            </Box>
                            <Box>
                                <Typography variant="caption" fontWeight="bold" display="block">RAMP</Typography>
                                <Typography variant="h6">{serverStats.recommendations.ramp_count}</Typography>
                            </Box>
                            <Box>
                                <Typography variant="caption" fontWeight="bold" display="block">CANTRIPS</Typography>
                                <Typography variant="h6">{serverStats.recommendations.cantrip_count}</Typography>
                            </Box>
                        </Stack>
                    </Grid>
                </Grid>
            ) : (
                <Typography color="text.secondary">Save the deck to get specific recommendations based on Commander/Standard math.</Typography>
            )}
        </Paper>

      <Typography variant="h6" gutterBottom fontWeight="bold">
        Mana Curve
      </Typography>
      <Box
        sx={{
          display: "flex",
          alignItems: "stretch", 
          height: 180, 
          gap: 1,
          mb: 4,
          borderBottom: 1,
          borderColor: "divider",
          pb: 1,
        }}
      >
        {stats.curve.map((count, i) => {
          const maxBarHeight = 120;
          const barHeight = maxCurve > 0 ? (count / maxCurve) * maxBarHeight : 0;
          
          return (
            <Box
              key={i}
              sx={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "flex-end", // Align content to bottom
                gap: 0.5,
              }}
            >
              {count > 0 && (
                <Typography variant="caption" fontWeight="bold">
                  {count}
                </Typography>
              )}
              <Box
                sx={{
                  width: "100%",
                  bgcolor: "primary.main",
                  borderRadius: "4px 4px 0 0",
                  height: barHeight, 
                  minHeight: count > 0 ? 4 : 0,
                  transition: "height 0.3s ease",
                  opacity: 0.8,
                  "&:hover": { opacity: 1 },
                }}
              />
              <Typography variant="caption" color="text.secondary">
                {i === 7 ? "7+" : i}
              </Typography>
            </Box>
          );
        })}
      </Box>

      <Typography variant="h6" gutterBottom fontWeight="bold">
        Mana Analysis
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Colors required (Pips) vs Sources provided vs Recommended sources (Frank Karsten method)
      </Typography>
      
      <Stack spacing={2}>
          {Object.entries(stats.colors).map(([color, data]) => {
              if (data.pips === 0 && data.sources === 0) return null;
              
              const colorMap: Record<string, string> = {
                  W: "#F0E6BC",
                  U: "#0E68AB",
                  B: "#150B00",
                  R: "#D3202A",
                  G: "#00733E",
                  C: "#999999",
              };
              
              // Status check
              const isLow = data.sources < data.recommended_sources;
              const isGood = data.sources >= data.recommended_sources;

              return (
                  <Box key={color} p={2} border={1} borderColor="divider" borderRadius={2}>
                       <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                           <Box sx={{ width: 24, height: 24, borderRadius: '50%', bgcolor: colorMap[color], border: 1, borderColor: 'divider' }} />
                           <Typography variant="subtitle1" fontWeight="bold">{color}</Typography>
                           {isLow && data.recommended_sources > 0 && (
                               <Typography variant="caption" color="error.main" fontWeight="bold" sx={{ ml: 'auto' }}>
                                   Low Sources!
                               </Typography>
                           )}
                           {isGood && data.recommended_sources > 0 && (
                               <Typography variant="caption" color="success.main" fontWeight="bold" sx={{ ml: 'auto' }}>
                                   Good
                               </Typography>
                           )}
                       </Box>
                       
                       <Grid container spacing={2}>
                           <Grid size={{ xs: 4 }} textAlign="center">
                               <Typography variant="caption" color="text.secondary">PIPS</Typography>
                               <Typography variant="h6">{data.pips}</Typography>
                           </Grid>
                           <Grid size={{ xs: 4 }} textAlign="center">
                               <Typography variant="caption" color="text.secondary">SOURCES</Typography>
                               <Typography variant="h6" color={isLow ? "error.main" : "text.primary"}>
                                   {data.sources}
                               </Typography>
                           </Grid>
                           <Grid size={{ xs: 4 }} textAlign="center">
                               <Typography variant="caption" color="text.secondary">RECOMMENDED</Typography>
                               <Typography variant="h6">
                                   {data.recommended_sources > 0 ? data.recommended_sources : "-"}
                               </Typography>
                           </Grid>
                       </Grid>
                  </Box>
              )
          })}
      </Stack>
      
       <Box sx={{ mt: 4, p: 2, bgcolor: 'background.paper', borderRadius: 2 }}>
           <Grid container spacing={2} textAlign="center">
               <Grid size={{ xs: 6 }}>
                   <Typography variant="h4" fontWeight="900" color="primary">{stats.totalCards}</Typography>
                   <Typography variant="caption" color="text.secondary">TOTAL CARDS</Typography>
               </Grid>
               <Grid size={{ xs: 6 }}>
                   <Typography variant="h4" fontWeight="900" color="secondary">{stats.totalLands}</Typography>
                   <Typography variant="caption" color="text.secondary">LANDS</Typography>
               </Grid>
           </Grid>
       </Box>
    </Box>
  );
};
