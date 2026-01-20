import React from "react";
import { Box, Typography } from "@mui/material";

interface ManaCurveChartProps {
  curve: number[];
}

export const ManaCurveChart: React.FC<ManaCurveChartProps> = ({ curve }) => {
  const maxCurve = Math.max(...curve, 1);

  return (
    <>
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
        {curve.map((count, i) => {
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
    </>
  );
};
