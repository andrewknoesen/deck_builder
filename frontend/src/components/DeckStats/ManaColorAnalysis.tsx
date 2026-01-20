import React from "react";
import { Box, Typography, Stack, Grid } from "@mui/material";

interface ColorStats {
  pips: number;
  sources: number;
  recommended_sources: number;
}

interface ManaColorAnalysisProps {
  colors: Record<string, ColorStats>;
}

export const ManaColorAnalysis: React.FC<ManaColorAnalysisProps> = ({ colors }) => {
  return (
    <>
      <Typography variant="h6" gutterBottom fontWeight="bold">
        Mana Analysis
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Colors required (Pips) vs Sources provided vs Recommended sources (Frank
        Karsten method)
      </Typography>

      <Stack spacing={2}>
        {Object.entries(colors).map(([color, data]) => {
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
            <Box
              key={color}
              p={2}
              border={1}
              borderColor="divider"
              borderRadius={2}
            >
              <Box
                sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1 }}
              >
                <Box
                  sx={{
                    width: 24,
                    height: 24,
                    borderRadius: "50%",
                    bgcolor: colorMap[color],
                    border: 1,
                    borderColor: "divider",
                  }}
                />
                <Typography variant="subtitle1" fontWeight="bold">
                  {color}
                </Typography>
                {isLow && data.recommended_sources > 0 && (
                  <Typography
                    variant="caption"
                    color="error.main"
                    fontWeight="bold"
                    sx={{ ml: "auto" }}
                  >
                    Low Sources!
                  </Typography>
                )}
                {isGood && data.recommended_sources > 0 && (
                  <Typography
                    variant="caption"
                    color="success.main"
                    fontWeight="bold"
                    sx={{ ml: "auto" }}
                  >
                    Good
                  </Typography>
                )}
              </Box>

              <Grid container spacing={2}>
                <Grid size={{ xs: 4 }} textAlign="center">
                  <Typography variant="caption" color="text.secondary">
                    PIPS
                  </Typography>
                  <Typography variant="h6">{data.pips}</Typography>
                </Grid>
                <Grid size={{ xs: 4 }} textAlign="center">
                  <Typography variant="caption" color="text.secondary">
                    SOURCES
                  </Typography>
                  <Typography
                    variant="h6"
                    color={isLow ? "error.main" : "text.primary"}
                  >
                    {data.sources}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 4 }} textAlign="center">
                  <Typography variant="caption" color="text.secondary">
                    RECOMMENDED
                  </Typography>
                  <Typography variant="h6">
                    {data.recommended_sources > 0
                      ? data.recommended_sources
                      : "-"}
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          );
        })}
      </Stack>
    </>
  );
};
