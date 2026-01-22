import React from "react";
import { Box, Card, CardMedia, Fade, Typography, Stack, Divider } from "@mui/material";
import { useCardHover } from "../context/CardHoverContext";
import { useLocation } from "react-router-dom";

export const CardHoverPreview: React.FC = () => {
  const { hoveredCard } = useCardHover();
  const location = useLocation();

  // Hide global preview on DeckBuilder page
  if (location.pathname.startsWith("/decks/") && location.pathname !== "/decks") {
      return null;
  }

  return (
    <Fade in={!!hoveredCard} timeout={200}>
      <Box
        sx={{
          position: "fixed",
          bottom: 24,
          right: 24,
          zIndex: 9999,
          pointerEvents: "none",
          display: "flex",
          alignItems: "flex-end",
          gap: 2,
        }}
      >
        {/* Info Card (Left of Image) */}
        <Card
          sx={{
            width: 300,
            p: 2,
            bgcolor: "background.paper",
            borderRadius: 2,
            boxShadow: 8,
            border: 1,
            borderColor: "divider",
          }}
        >
          <Stack spacing={1}>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <Typography variant="subtitle1" fontWeight="700" lineHeight={1.2}>
                {hoveredCard?.name}
              </Typography>
              <Typography variant="caption" sx={{ bgcolor: "action.hover", px: 0.5, borderRadius: 0.5 }}>
                {hoveredCard?.mana_cost}
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary" fontWeight="700">
              {hoveredCard?.type_line}
            </Typography>
            <Divider />
            <Typography
              variant="body2"
              sx={{
                whiteSpace: "pre-wrap",
                fontSize: "0.8rem",
                color: "text.primary",
                py: 0.5,
              }}
            >
              {hoveredCard?.oracle_text}
            </Typography>
          </Stack>
        </Card>

        {/* Card Image */}
        <Card
          sx={{
            width: 300,
            aspectRatio: "2.5/3.5",
            bgcolor: "transparent",
            borderRadius: "4.5% / 3.5%",
            overflow: "hidden",
            boxShadow: 12,
          }}
        >
          {hoveredCard?.image_uris?.normal && (
            <CardMedia
              component="img"
              image={hoveredCard.image_uris.normal}
              alt={hoveredCard.name}
              sx={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          )}
        </Card>
      </Box>
    </Fade>
  );
};
