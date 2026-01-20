import React from "react";
import { Box, Typography, Paper, Grid, Stack } from "@mui/material";
import type { DeckStatsResponse } from "../../types/mtg";

interface DrawProbabilityStatsProps {
  drawOdds: DeckStatsResponse["draw_odds"];
}

export const DrawProbabilityStats: React.FC<DrawProbabilityStatsProps> = ({
  drawOdds,
}) => {
  if (!drawOdds) return null;

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h6" gutterBottom fontWeight="bold">
        Draw Probability
      </Typography>
      <Grid container spacing={2}>
        {/* Opening Hand */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography
              variant="subtitle2"
              color="text.secondary"
              gutterBottom
              fontWeight="bold"
            >
              OPENING HAND (7 Cards)
            </Typography>
            <Stack spacing={1}>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="body2">At least 2 Lands</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {(drawOdds.opening_hand.lands_at_least_2 * 100).toFixed(1)}%
                </Typography>
              </Box>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="body2">At least 3 Lands</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {(drawOdds.opening_hand.lands_at_least_3 * 100).toFixed(1)}%
                </Typography>
              </Box>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="body2">At least 4 Lands</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {(drawOdds.opening_hand.lands_at_least_4 * 100).toFixed(1)}%
                </Typography>
              </Box>
            </Stack>
          </Paper>
        </Grid>
        {/* On Curve */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography
              variant="subtitle2"
              color="text.secondary"
              gutterBottom
              fontWeight="bold"
            >
              ON CURVE
            </Typography>
            <Stack spacing={1}>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="body2">Turn 3 Land Drop</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {(drawOdds.on_curve.turn_3_land_drop * 100).toFixed(1)}%
                </Typography>
              </Box>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="body2">Turn 4 Land Drop</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {(drawOdds.on_curve.turn_4_land_drop * 100).toFixed(1)}%
                </Typography>
              </Box>
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};
