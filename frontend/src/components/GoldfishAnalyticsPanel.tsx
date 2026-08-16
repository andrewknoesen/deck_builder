import React from "react";
import { Box, Typography, Paper, Grid, Tooltip } from "@mui/material";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import type { GoldfishAnalytics } from "../types/goldfish";

interface GoldfishAnalyticsPanelProps {
  deckId: number;
}

const Stat: React.FC<{
  label: React.ReactNode;
  value: React.ReactNode;
}> = ({ label, value }) => (
  <Grid size={{ xs: 6, sm: 3 }}>
    <Typography variant="caption" color="text.secondary" component="div">
      {label}
    </Typography>
    <Typography variant="h6" fontWeight="700">
      {value}
    </Typography>
  </Grid>
);

const formatPercent = (value: number | null) =>
  value === null ? "—" : `${(value * 100).toFixed(0)}%`;

export const GoldfishAnalyticsPanel: React.FC<GoldfishAnalyticsPanelProps> = ({
  deckId,
}) => {
  const { data, isLoading } = useQuery({
    queryKey: ["goldfishAnalytics", deckId],
    queryFn: async () => {
      const res = await apiClient.get("/goldfish/analytics", {
        params: { deck_id: deckId },
      });
      return res.data as GoldfishAnalytics;
    },
  });

  if (isLoading || !data) {
    return null;
  }

  if (data.session_count === 0) {
    return (
      <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
        <Typography variant="body2" color="text.secondary">
          No practice sessions yet — analytics will appear once you've played
          a few.
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
      <Typography variant="overline" color="text.secondary">
        Analytics
      </Typography>
      <Grid container spacing={2} sx={{ mt: 0.5 }}>
        <Stat label="Sessions" value={data.session_count} />
        <Stat
          label={`Win rate${data.sessions_with_outcome === 0 ? "" : ` (${data.sessions_with_outcome} recorded)`}`}
          value={formatPercent(data.win_rate)}
        />
        <Stat
          label={
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              Avg. max turn
              <Tooltip title="The longest branch explored per session, not necessarily the line actually played.">
                <InfoOutlinedIcon sx={{ fontSize: 14 }} />
              </Tooltip>
            </Box>
          }
          value={
            data.average_max_turn === null
              ? "—"
              : data.average_max_turn.toFixed(1)
          }
        />
        <Stat
          label="Two-deck sessions"
          value={formatPercent(data.two_deck_session_ratio)}
        />
      </Grid>
      {data.sessions_with_outcome > 0 && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1.5, display: "block" }}>
          {data.wins}W / {data.losses}L / {data.draws}D
        </Typography>
      )}
    </Paper>
  );
};
