import React from "react";
import { Box, Typography, Paper, Grid, Stack, CircularProgress } from "@mui/material";
import LightbulbIcon from "@mui/icons-material/Lightbulb";
import type { DeckStatsResponse } from "../../types/mtg";

interface DeckConstructionGuideProps {
  serverStats?: DeckStatsResponse;
  totalCards: number;
  totalLands: number;
  isLoading: boolean;
}

export const DeckConstructionGuide: React.FC<DeckConstructionGuideProps> = ({
  serverStats,
  totalCards,
  totalLands,
  isLoading,
}) => {
  return (
    <Paper
      elevation={0}
      variant="outlined"
      sx={{ p: 3, mb: 4, bgcolor: "primary.50", borderColor: "primary.200" }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
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
            <Typography
              variant="subtitle2"
              fontWeight="700"
              color="text.secondary"
              gutterBottom
            >
              RECOMMENDED LANDS
            </Typography>
            <Stack direction="row" alignItems="baseline" spacing={1}>
              <Typography variant="h3" fontWeight="900" color="primary.main">
                {serverStats.recommendations.land_count}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                / {totalCards} cards
              </Typography>
            </Stack>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Current: <strong>{totalLands}</strong>
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Typography
              variant="subtitle2"
              fontWeight="700"
              color="text.secondary"
              gutterBottom
            >
              ANALYSIS
            </Typography>
            <Typography variant="body1">
              {serverStats.recommendations.reasoning}
            </Typography>
            <Stack direction="row" spacing={3} sx={{ mt: 2 }}>
              <Box>
                <Typography variant="caption" fontWeight="bold" display="block">
                  AVG CMC
                </Typography>
                <Typography variant="h6">{serverStats.average_cmc}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" fontWeight="bold" display="block">
                  RAMP
                </Typography>
                <Typography variant="h6">
                  {serverStats.recommendations.ramp_count}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" fontWeight="bold" display="block">
                  CANTRIPS
                </Typography>
                <Typography variant="h6">
                  {serverStats.recommendations.cantrip_count}
                </Typography>
              </Box>
            </Stack>
          </Grid>
        </Grid>
      ) : (
        <Typography color="text.secondary">
          Save the deck to get specific recommendations based on Commander/Standard math.
        </Typography>
      )}
    </Paper>
  );
};
