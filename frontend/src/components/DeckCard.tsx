import React from 'react';
import {
  Card,
  CardMedia,
  Box,
  Typography,
  IconButton,
  Menu,
  MenuItem,
} from "@mui/material";
import RemoveIcon from "@mui/icons-material/Remove";
import AddIcon from "@mui/icons-material/Add";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import DeleteIcon from "@mui/icons-material/Delete";
import type { DeckCard as DeckCardType } from "../types/mtg";

import { useCardHover } from "../context/CardHoverContext";

interface DeckCardProps {
  deckCard: DeckCardType;
  onUpdateQuantity: (cardId: string, delta: number) => void;
  onRemove: (cardId: string) => void;
  onMoveCard?: (cardId: string, fromBoard: string, toBoard: string, quantity?: number) => void;
  isCommanderFormat?: boolean;
  limit?: number;
  isIllegal?: boolean;
  canBeCommander?: boolean;
  currentTotalQuantity?: number;
}

export const DeckCard = React.memo<DeckCardProps>(
  ({
    deckCard,
    onUpdateQuantity,
    onRemove,
    onMoveCard,
    isCommanderFormat,
    limit = 4,
    isIllegal = false,
    canBeCommander = true,
    currentTotalQuantity,
  }) => {
    const isOverLimit = (currentTotalQuantity ?? deckCard.quantity) > limit;
    const { setHoveredCard } = useCardHover();

    // Menu State
    const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
    const openMenu = Boolean(anchorEl);

    const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
      event.stopPropagation();
      setAnchorEl(event.currentTarget);
    };

    const handleMenuClose = (e?: React.MouseEvent) => {
      if (e) e.stopPropagation();
      setAnchorEl(null);
    };

    const handleMove = (targetBoard: string, quantity: number = 1) => {
      if (onMoveCard) {
        onMoveCard(deckCard.card_id, deckCard.board, targetBoard, quantity);
      }
      handleMenuClose();
    };

    const handleMoveAll = (targetBoard: string) => {
        handleMove(targetBoard, deckCard.quantity);
    };

    return (
      <Box
        sx={{ position: "relative", width: "100%", aspectRatio: "2.5/3.5" }}
        onMouseEnter={() => deckCard.card && setHoveredCard(deckCard.card)}
        onMouseLeave={() => setHoveredCard(null)}
      >
        {/* Illegality Badge */}
        {isIllegal && (
          <Box
            sx={{
              position: "absolute",
              top: 8,
              left: 8,
              zIndex: 20,
              bgcolor: "error.main",
              color: "white",
              px: 1,
              py: 0.5,
              borderRadius: 1,
              fontSize: "0.6rem",
              fontWeight: 900,
              boxShadow: 4,
              pointerEvents: "none",
            }}
          >
            ILLEGAL
          </Box>
        )}
        {/* Quantity Badge (Always Visible initially, hidden on hover via CSS) */}
        <Box
          sx={{
            position: "absolute",
            top: -8,
            right: -8,
            width: 28,
            height: 28,
            bgcolor:
              isOverLimit || isIllegal ? "error.main" : "background.paper",
            color: isOverLimit || isIllegal ? "white" : "text.primary",
            border: 1,
            borderColor: isOverLimit || isIllegal ? "error.main" : "divider",
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
              isOverLimit || isIllegal
                ? "error.main"
                : deckCard.board === "commander"
                  ? "warning.main"
                  : "divider",
            borderWidth:
              isOverLimit || isIllegal || deckCard.board === "commander"
                ? 2
                : 1,
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
              filter: isIllegal ? "grayscale(100%)" : "none",
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

              {/* Actions Row */}
              <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
                {/* Board Menu */}
                {onMoveCard && (
                  <>
                    <IconButton
                      size="small"
                      onClick={handleMenuClick}
                      sx={{
                        bgcolor: "background.paper",
                        color: "text.secondary",
                        "&:hover": { bgcolor: "primary.main", color: "white" },
                      }}
                    >
                      <MoreVertIcon fontSize="small" />
                    </IconButton>
                    <Menu
                      anchorEl={anchorEl}
                      open={openMenu}
                      onClose={() => handleMenuClose()}
                      anchorOrigin={{
                        vertical: "bottom",
                        horizontal: "center",
                      }}
                      transformOrigin={{
                        vertical: "top",
                        horizontal: "center",
                      }}
                      PaperProps={{ sx: { minWidth: 160 } }}
                    >
                      {deckCard.board !== "main" && (
                        deckCard.quantity > 1 ? [
                            <MenuItem key="move-one-main" onClick={() => handleMove("main", 1)}>
                                Move One to Main
                            </MenuItem>,
                            <MenuItem key="move-all-main" onClick={() => handleMoveAll("main")}>
                                Move All to Main
                            </MenuItem>
                        ] : (
                            <MenuItem onClick={() => handleMove("main")}>
                                Move to Mainboard
                            </MenuItem>
                        )
                      )}
                      {deckCard.board !== "side" && (
                        deckCard.quantity > 1 ? [
                            <MenuItem key="move-one-side" onClick={() => handleMove("side", 1)}>
                                Move One to Side
                            </MenuItem>,
                            <MenuItem key="move-all-side" onClick={() => handleMoveAll("side")}>
                                Move All to Side
                            </MenuItem>
                        ] : (
                            <MenuItem onClick={() => handleMove("side")}>
                                Move to Sideboard
                            </MenuItem>
                        )
                      )}
                      {deckCard.board !== "maybe" && (
                         deckCard.quantity > 1 ? [
                            <MenuItem key="move-one-maybe" onClick={() => handleMove("maybe", 1)}>
                                Move One to Maybe
                            </MenuItem>,
                            <MenuItem key="move-all-maybe" onClick={() => handleMoveAll("maybe")}>
                                Move All to Maybe
                            </MenuItem>
                         ] : (
                            <MenuItem onClick={() => handleMove("maybe")}>
                                Move to Maybeboard
                            </MenuItem>
                         )
                      )}
                      {isCommanderFormat &&
                        canBeCommander &&
                        deckCard.board !== "commander" && (
                          <MenuItem onClick={() => handleMove("commander", 1)}>
                            Set as Commander
                          </MenuItem>
                        )}
                    </Menu>
                  </>
                )}

                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemove(deckCard.card_id);
                  }}
                  sx={{
                    bgcolor: "background.paper",
                    color: "error.main",
                    "&:hover": { bgcolor: "error.main", color: "white" },
                  }}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Box>
            </Box>
          </Box>
        </Card>
      </Box>
    );
  }
);
