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
      sx={{ p: 2, mb: 2, bgcolor: "primary.50", borderColor: "primary.200" }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
        <LightbulbIcon color="primary" fontSize="small" />
        <Typography variant="subtitle1" fontWeight="800" color="primary.main">
          Deck Construction Guide
        </Typography>
      </Box>

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
            <CircularProgress size={20} />
        </Box>
      ) : (
        <>
          <Grid container spacing={2} sx={{ mb: 1.5 }}>
            {/* Total Cards */}
            <Grid size={{ xs: 4, sm: 2 }}>
              <Box textAlign="center">
                <Typography variant="h6" fontWeight="900" color="primary.main">
                  {totalCards}
                </Typography>
                <Typography variant="caption" color="text.secondary" fontWeight="bold" sx={{ fontSize: '0.65rem', display: 'block' }}>
                  TOTAL
                </Typography>
              </Box>
            </Grid>

            {/* Lands (Current / Recommended) */}
            <Grid size={{ xs: 4, sm: 3 }} sx={{ display: 'flex', justifyContent: 'center' }}>
               <Box textAlign="center">
                <Typography variant="h6" fontWeight="900" color="secondary.main">
                  {totalLands}
                  {serverStats && (
                    <Typography component="span" variant="body2" color="text.secondary" sx={{ opacity: 0.7, fontWeight: 700 }}>
                      /{serverStats.recommendations.land_count}
                    </Typography>
                  )}
                </Typography>
                <Typography variant="caption" color="text.secondary" fontWeight="bold" sx={{ fontSize: '0.65rem', display: 'block' }}>
                  LANDS
                </Typography>
              </Box>
            </Grid>

            {/* Non-Lands */}
            <Grid size={{ xs: 4, sm: 2 }}>
               <Box textAlign="center">
                <Typography variant="h6" fontWeight="900" color="info.main">
                   {totalCards - totalLands}
                </Typography>
                <Typography variant="caption" color="text.secondary" fontWeight="bold" sx={{ fontSize: '0.65rem', display: 'block' }}>
                  SPELLS
                </Typography>
              </Box>
            </Grid>
            
            {serverStats && (
              <>
                 {/* CMC */}
                <Grid size={{ xs: 4, sm: 2 }}>
                  <Box textAlign="center">
                    <Typography variant="h6" fontWeight="900" color="text.primary">
                      {serverStats.average_cmc}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" fontWeight="bold" sx={{ fontSize: '0.65rem', display: 'block' }}>
                      CMC
                    </Typography>
                  </Box>
                </Grid>

                {/* Ramp */}
                <Grid size={{ xs: 4, sm: 1.5 }}>
                  <Box textAlign="center">
                    <Typography variant="h6" fontWeight="900" color="text.primary">
                       {serverStats.recommendations.ramp_count}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" fontWeight="bold" sx={{ fontSize: '0.65rem', display: 'block' }}>
                      RAMP
                    </Typography>
                  </Box>
                </Grid>

                {/* Draw */}
                <Grid size={{ xs: 4, sm: 1.5 }}>
                   <Box textAlign="center">
                    <Typography variant="h6" fontWeight="900" color="text.primary">
                       {serverStats.recommendations.cantrip_count}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" fontWeight="bold" sx={{ fontSize: '0.65rem', display: 'block' }}>
                      DRAW
                    </Typography>
                  </Box>
                </Grid>
              </>
            )}
          </Grid>
          
          {serverStats ? (
             <Box sx={{ borderTop: 1, borderColor: 'primary.100', pt: 1 }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', lineHeight: 1.3 }}>
                   {serverStats.recommendations.reasoning}
                </Typography>
             </Box>
          ) : (
            <Box sx={{ borderTop: 1, borderColor: 'primary.100', pt: 1, fontStyle: 'italic' }}>
               <Typography variant="caption" color="text.secondary">
                  Save deck to unlock recommendations.
               </Typography>
            </Box>
          )}
        </>
      )}
    </Paper>
  );
};
