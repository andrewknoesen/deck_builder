import React from "react";
import { Box, Typography, Grid } from "@mui/material";

interface DeckSummaryProps {
  totalCards: number;
  totalLands: number;
}

export const DeckSummary: React.FC<DeckSummaryProps> = ({
  totalCards,
  totalLands,
}) => {
  return (
    <Box sx={{ mt: 4, p: 2, bgcolor: "background.paper", borderRadius: 2 }}>
      <Grid container spacing={2} textAlign="center">
        <Grid size={{ xs: 6 }}>
          <Typography variant="h4" fontWeight="900" color="primary">
            {totalCards}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            TOTAL CARDS
          </Typography>
        </Grid>
        <Grid size={{ xs: 6 }}>
          <Typography variant="h4" fontWeight="900" color="secondary">
            {totalLands}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            LANDS
          </Typography>
        </Grid>
      </Grid>
    </Box>
  );
};
