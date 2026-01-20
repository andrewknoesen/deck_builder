import React from 'react';
import {
  Card,
  CardMedia,
  Box,
  Typography,
  IconButton,
  Button,
  Tooltip,
} from "@mui/material";
import RemoveIcon from '@mui/icons-material/Remove';
import AddIcon from '@mui/icons-material/Add';
import EmojiEventsIcon from "@mui/icons-material/EmojiEvents"; // Crown icon alternative
import StarIcon from "@mui/icons-material/Star";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import type { DeckCard as DeckCardType } from '../types/mtg';

interface DeckCardProps {
  deckCard: DeckCardType;
  onUpdateQuantity: (cardId: string, delta: number) => void;
  onRemove: (cardId: string) => void;
  onMoveToBoard?: (cardId: string, board: string) => void;
  isCommanderFormat?: boolean;
}

export const DeckCard = React.memo<DeckCardProps>(
  ({
    deckCard,
    onUpdateQuantity,
    onRemove,
    onMoveToBoard,
    isCommanderFormat,
  }) => {
    return (
      <Box sx={{ position: "relative", width: "100%", aspectRatio: "2.5/3.5" }}>
        {/* Quantity Badge (Always Visible initially, hidden on hover via CSS) */}
        <Box
          sx={{
            position: "absolute",
            top: -8,
            right: -8,
            width: 28,
            height: 28,
            bgcolor: "background.paper",
            border: 1,
            borderColor: "divider",
            borderRadius: "50%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 20,
            boxShadow: 4,
            fontWeight: 900,
            fontSize: "0.75rem",
            transition: "opacity 0.2s",
            opacity: 1,
            ".parent-card:hover &": { opacity: 0 }, // Hide when hovering the card controller
          }}
        >
          x{deckCard.quantity}
        </Box>

        <Card
          className="parent-card"
          sx={{
            width: "100%",
            height: "100%",
            position: "relative",
            borderRadius: 0,
            border: 1,
            borderColor:
              deckCard.board === "commander" ? "warning.main" : "divider",
            borderWidth: deckCard.board === "commander" ? 2 : 1,
            overflow: "visible", // For scale effect
            "&:hover": { zIndex: 10 },
          }}
        >
          <Box
            sx={{
              position: "relative",
              width: "100%",
              height: "100%",
              borderRadius: 0,
              overflow: "hidden",
              transition: "transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
              "&:hover": { transform: "scale(1.05)", boxShadow: 12 },
            }}
          >
            {deckCard.card?.image_uris?.normal ? (
              <CardMedia
                component="img"
                image={deckCard.card.image_uris.normal}
                alt={deckCard.card.name}
                loading="lazy"
                sx={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            ) : (
              <Box
                sx={{
                  width: "100%",
                  height: "100%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  bgcolor: "background.paper",
                  p: 2,
                  textAlign: "center",
                }}
              >
                <Typography
                  variant="body2"
                  color="text.secondary"
                  fontWeight="700"
                >
                  {deckCard.card?.name}
                </Typography>
              </Box>
            )}

            {/* Overlay */}
            <Box
              sx={{
                position: "absolute",
                inset: 0,
                bgcolor: "rgba(0,0,0,0.7)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: 1.5,
                opacity: 0,
                transition: "opacity 0.2s",
                "&:hover": { opacity: 1 },
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    onUpdateQuantity(deckCard.card_id, -1);
                  }}
                  sx={{
                    bgcolor: "background.paper",
                    "&:hover": { bgcolor: "secondary.main", color: "white" },
                  }}
                >
                  <RemoveIcon fontSize="small" />
                </IconButton>
                <Typography
                  variant="h6"
                  fontWeight="900"
                  sx={{ minWidth: 24, textAlign: "center" }}
                >
                  {deckCard.quantity}
                </Typography>
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    onUpdateQuantity(deckCard.card_id, 1);
                  }}
                  sx={{
                    bgcolor: "background.paper",
                    "&:hover": { bgcolor: "#10b981", color: "white" },
                  }} // Emerald-500 equivalent
                >
                  <AddIcon fontSize="small" />
                </IconButton>
              </Box>

              {/* Commander Actions */}
              {isCommanderFormat && onMoveToBoard && (
                <Box sx={{ display: "flex", gap: 1 }}>
                  {deckCard.board === "commander" ? (
                    <Tooltip title="Move to Main Deck">
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          onMoveToBoard(deckCard.card_id, "main");
                        }}
                        sx={{
                          bgcolor: "background.paper",
                          color: "warning.main",
                          "&:hover": {
                            bgcolor: "background.paper",
                            color: "text.primary",
                          },
                        }}
                      >
                        <ArrowDownwardIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  ) : (
                    <Tooltip title="Set as Commander">
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          onMoveToBoard(deckCard.card_id, "commander");
                        }}
                        sx={{
                          bgcolor: "background.paper",
                          color: "text.secondary",
                          "&:hover": {
                            bgcolor: "warning.main",
                            color: "white",
                          },
                        }}
                      >
                        <EmojiEventsIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                </Box>
              )}

              <Button
                size="small"
                variant="text"
                color="secondary"
                onClick={(e) => {
                  e.stopPropagation();
                  onRemove(deckCard.card_id);
                }}
                sx={{ fontWeight: 800, letterSpacing: 1, fontSize: "0.65rem" }}
              >
                REMOVE
              </Button>
            </Box>
          </Box>
        </Card>
      </Box>
    );
  },
);
