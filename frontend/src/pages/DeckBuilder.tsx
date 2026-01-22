import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useNavigate, Link as RouterLink } from "react-router-dom";
import {
  Box,
  TextField,
  Typography,
  IconButton,
  Grid,
  Paper,
  Divider,
  Stack,
  CircularProgress,
  Alert,
  Collapse,
} from "@mui/material";
import {
  validateDeckSize,
  getCardLimit,
  isCardLegal,
  isValidCommander,
} from "../utils/deckValidation";
import BarChartIcon from "@mui/icons-material/BarChart";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import GridViewIcon from "@mui/icons-material/GridView";
import { apiClient } from "../api/client";
import type { ScryfallCard, Deck, DeckCard } from "../types/mtg";
import { useAuth } from "../context/AuthContext";
import { DeckCard as DeckCardComponent } from "../components/DeckCard";
import { DeckStats } from "../components/DeckStats";
import { DeckBuilderSearch } from "../components/DeckBuilderSearch";
import { useDebounce } from "../hooks/useDebounce";
import { useCardHover } from "../context/CardHoverContext";
import { Card, CardMedia } from "@mui/material";

// Helper to determine primary type for grouping
const getCardType = (typeLine?: string): string => {
  if (!typeLine) return "Unknown";
  const lower = typeLine.toLowerCase();
  if (lower.includes("creature")) return "Creatures";
  if (lower.includes("planeswalker")) return "Planeswalkers";
  if (lower.includes("instant")) return "Instants";
  if (lower.includes("sorcery")) return "Sorceries";
  if (lower.includes("artifact")) return "Artifacts";
  if (lower.includes("enchantment")) return "Enchantments";
  if (lower.includes("land")) return "Lands";
  return "Other";
};

const TYPE_ORDER = [
  "Creatures",
  "Planeswalkers",
  "Instants",
  "Sorceries",
  "Artifacts",
  "Enchantments",
  "Lands",
  "Other",
  "Unknown",
];

const FORMATS = [
  "Commander",
  "Standard",
  "Modern",
  "Pioneer",
  "Legacy",
  "Vintage",
  "Pauper",
  "Oathbreaker",
  "Brawl",
  "Limited",
];

export const DeckBuilder: React.FC = () => {
  const { deckId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { hoveredCard } = useCardHover();

  const isNew = !deckId || deckId === "new";

  // State
  const [title, setTitle] = useState("New Deck");
  const [format, setFormat] = useState("Commander");
  const [deckCards, setDeckCards] = useState<DeckCard[]>([]);
  const [saveStatus, setSaveStatus] = useState<"saved" | "saving" | "unsaved">(
    "saved",
  );
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  // Debounce critical state for auto-save
  const debouncedTitle = useDebounce(title, 1000);
  const debouncedFormat = useDebounce(format, 1000);
  const debouncedCards = useDebounce(deckCards, 1000);

  // Fetch deck data
  const { data: deck, isLoading: loadingDecks } = useQuery({
    queryKey: ["deck", deckId],
    queryFn: async () => {
      if (isNew) return null;
      const res = await apiClient.get(`/decks/${deckId}`);
      return res.data as Deck;
    },
    enabled: !isNew,
  });

  // Sync remote data to local state when loaded
  // Sync remote data to local state ONLY on initial load
  useEffect(() => {
    if (deck && isInitialLoad) {
      setTitle(deck.title);
      setFormat(deck.format || "Commander");
      setDeckCards(deck.cards || []);
      setIsInitialLoad(false);
    } else if (isNew) {
      setIsInitialLoad(false);
    }
  }, [deck, isNew, isInitialLoad]);

  // Track if we have unsaved changes locally
  useEffect(() => {
    if (!isInitialLoad) {
      // Check if current state differs from debounced (roughly implies typing)
      // Or simpler: just set to unsaved on any change, and let debounce effect handle save
      setSaveStatus("unsaved");
    }
  }, [title, format, deckCards, isInitialLoad]);

  // Auto-save Effect
  useEffect(() => {
    // Don't save on initial load or if nothing changed (conceptually)
    if (isInitialLoad) return;

    const saveDeck = async () => {
      setSaveStatus("saving");
      try {
        const deckData = {
          title: debouncedTitle,
          format: debouncedFormat,
          user_id: user?.id || 1,
          cards: debouncedCards.map(({ card_id, quantity, board }) => ({
            card_id,
            quantity,
            board,
          })),
        };

        if (isNew) {
          const res = await apiClient.post("/decks/", deckData);
          queryClient.invalidateQueries({ queryKey: ["decks"] });
          // Navigate to the new URL silently/replace
          navigate(`/decks/${res.data.id}`, { replace: true });
        } else {
          await apiClient.put(`/decks/${deckId}`, deckData);
          queryClient.invalidateQueries({ queryKey: ["decks"] });
          queryClient.invalidateQueries({ queryKey: ["deck", deckId] });
        }
        setSaveStatus("saved");
      } catch (err) {
        console.error("Auto-save failed", err);
        setSaveStatus("unsaved"); // keep unsaved status if failed
      }
    };

    // Only save if we are actually 'unsaved'.
    if (saveStatus === "unsaved") {
      saveDeck();
    }
  }, [debouncedTitle, debouncedFormat, debouncedCards]);

  // Search State removed (now handled by DeckBuilderSearch)

  const addCard = useCallback(
    (card: ScryfallCard) => {
      setDeckCards((prev) => {
        const existing = prev.find((dc) => dc.card_id === card.id);

        if (existing) {
          // Allow exceeding limit (visual warning handled in DeckCard)
          return prev.map((dc) =>
            dc.card_id === card.id ? { ...dc, quantity: dc.quantity + 1 } : dc,
          );
        }
        return [
          ...prev,
          { card_id: card.id, quantity: 1, board: "main", card },
        ];
      });
    },
    [format],
  );

  const updateQuantity = useCallback((cardId: string, delta: number) => {
    setDeckCards((prev) =>
      prev
        .map((dc) => {
          if (dc.card_id === cardId) {
            const newQty = Math.max(0, dc.quantity + delta);
            return { ...dc, quantity: newQty };
          }
          return dc;
        })
        .filter((dc) => dc.quantity > 0),
    );
  }, []);

  const removeCard = useCallback((cardId: string) => {
    setDeckCards((prev) => prev.filter((dc) => dc.card_id !== cardId));
  }, []);

  const handleMoveToBoard = useCallback((cardId: string, newBoard: string) => {
    setDeckCards((prev) =>
      prev.map((dc) => {
        if (dc.card_id === cardId) {
          if (newBoard === "commander" && !isValidCommander(dc.card)) {
            return dc; // Prevent illegal commander
          }
          // If moving to commander, quantity max 1
          const quantity = newBoard === "commander" ? 1 : dc.quantity;
          return { ...dc, board: newBoard, quantity };
        }
        return dc;
      }),
    );
  }, []);

  // Group cards
  const groupedCards = useMemo(() => {
    const groups: Record<string, DeckCard[]> = {};
    deckCards.forEach((dc) => {
      // Logic for grouping:
      // 1. If board is commander, group is "Commander"
      // 2. Else group by type
      let groupKey = getCardType(dc.card?.type_line);
      if (dc.board === "commander") {
        groupKey = "Commander";
      }

      if (!groups[groupKey]) groups[groupKey] = [];
      groups[groupKey].push(dc);
    });
    return groups;
  }, [deckCards]);

  const sortedGroups = useMemo(() => {
    const customOrder = ["Commander", ...TYPE_ORDER];
    return Object.keys(groupedCards).sort((a, b) => {
      return customOrder.indexOf(a) - customOrder.indexOf(b);
    });
  }, [groupedCards]);

  const totalCards = useMemo(
    () => deckCards.reduce((acc, curr) => acc + curr.quantity, 0),
    [deckCards],
  );

  const validation = useMemo(
    () => validateDeckSize(format, totalCards),
    [format, totalCards],
  );

  if (loadingDecks) {
    return (
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "calc(100vh - 64px)",
          gap: 2,
        }}
      >
        <CircularProgress size={48} color="primary" />
        <Typography variant="body1" color="text.secondary">
          Conjuring your deck...
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{ display: "flex", height: "calc(100vh - 64px)", overflow: "hidden" }}
    >
      {/* Left Column: Deck Inventory (Expanded to 65%) */}
      <Paper
        square
        elevation={0}
        sx={{
          width: "65%", // Expanded from 45%
          borderRight: 1,
          borderColor: "divider",
          display: "flex",
          flexDirection: "column",
          bgcolor: "background.paper",
          zIndex: 10,
        }}
      >
        {/* Header */}
        {/* Header */}
        <Box
          sx={{
            py: 1.5,
            px: 2,
            borderBottom: 1,
            borderColor: "divider",
            bgcolor: "rgba(15, 23, 42, 0.8)",
            backdropFilter: "blur(12px)",
            position: "sticky",
            top: 0,
            zIndex: 20,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <IconButton
              component={RouterLink}
              to="/decks"
              size="small"
              sx={{ border: 1, borderColor: "divider", borderRadius: 2 }}
            >
              <ArrowBackIcon fontSize="small" />
            </IconButton>

            {/* Title & Format Row */}
            <Box
              sx={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                gap: 2,
                minWidth: 0,
              }}
            >
              <TextField
                fullWidth
                variant="standard"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Deck Title"
                InputProps={{
                  disableUnderline: true,
                  sx: { fontSize: "1.25rem", fontWeight: 800 },
                }}
              />
              <TextField
                select
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                variant="outlined"
                size="small"
                SelectProps={{ native: true }}
                sx={{ width: 140, "& .MuiInputBase-input": { py: 0.5 } }}
              >
                {FORMATS.map((fmt) => (
                  <option key={fmt} value={fmt}>
                    {fmt}
                  </option>
                ))}
              </TextField>
            </Box>
          </Box>

          {/* Search Row */}
          <Box
            sx={{
              mt: 1.5,
              display: "flex",
              alignItems: "center",
              gap: 2,
              justifyContent: "space-between",
            }}
          >
            <Box sx={{ flex: 1, maxWidth: 600 }}>
              <DeckBuilderSearch onAddCard={addCard} />
            </Box>
            <Typography
              variant="caption"
              fontWeight="700"
              color="text.secondary"
              sx={{ textTransform: "uppercase", letterSpacing: 1 }}
            >
              {totalCards} Cards
            </Typography>
          </Box>

          <Collapse in={!validation.valid}>
            {validation.message && (
              <Alert
                severity={validation.severity === "error" ? "error" : "warning"}
                sx={{
                  mt: 1,
                  py: 0,
                  borderRadius: 2,
                  fontWeight: 500,
                  "& .MuiAlert-icon": { alignItems: "center", py: 0 },
                  "& .MuiAlert-message": { py: 0.5 },
                }}
              >
                {validation.message}
              </Alert>
            )}
          </Collapse>
        </Box>

        {/* Deck Content */}
        <Box sx={{ flex: 1, overflowY: "auto", p: 3, pb: 10 }}>
          {deckCards.length === 0 ? (
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                height: "100%",
                opacity: 0.5,
                textAlign: "center",
                gap: 2,
              }}
            >
              <Box
                sx={{
                  width: 80,
                  height: 80,
                  borderRadius: "50%",
                  bgcolor: "action.hover",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <GridViewIcon sx={{ fontSize: 40, color: "text.secondary" }} />
              </Box>
              <Box>
                <Typography variant="h5" fontWeight="800" color="text.primary">
                  Start Building
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Search for cards on the right to add them to your masterpiece.
                </Typography>
              </Box>
            </Box>
          ) : (
            <Stack spacing={4}>
              {sortedGroups.map((type) => (
                <Box key={type}>
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      mb: 2,
                    }}
                  >
                    <Typography
                      variant="subtitle2"
                      fontWeight="900"
                      color="text.secondary"
                      sx={{ textTransform: "uppercase", letterSpacing: 1 }}
                    >
                      {type}
                    </Typography>
                    <Box
                      sx={{
                        px: 1,
                        py: 0.5,
                        bgcolor: "action.selected",
                        borderRadius: 1,
                        fontSize: "0.7rem",
                        fontWeight: 700,
                        color: "text.primary",
                      }}
                    >
                      {groupedCards[type].reduce((a, c) => a + c.quantity, 0)}
                    </Box>
                    <Divider sx={{ flex: 1 }} />
                  </Box>
                  <Grid container spacing={2}>
                    {groupedCards[type].map((dc) => (
                      <Grid size={{ xs: 3, lg: 2 }} key={dc.card_id}>
                        {(() => {
                          const isCommanderLike =
                            format === "Commander" ||
                            format === "Brawl" ||
                            format === "Oathbreaker";
                          const isIllegalPlacement =
                            dc.board === "commander" && !isCommanderLike;
                          return (
                            <DeckCardComponent
                              deckCard={dc}
                              onUpdateQuantity={updateQuantity}
                              onRemove={removeCard}
                              onMoveToBoard={handleMoveToBoard}
                              limit={getCardLimit(format, dc.card)}
                              isCommanderFormat={isCommanderLike}
                              isIllegal={
                                !isCardLegal(format, dc.card) ||
                                isIllegalPlacement
                              }
                              canBeCommander={isValidCommander(dc.card)}
                            />
                          );
                        })()}
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              ))}
            </Stack>
          )}
        </Box>
      </Paper>

      {/* Right Column: Stats (Blurred) or Card Preview */}
      <Box
        sx={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          bgcolor: "background.default",
          minWidth: 0,
          borderLeft: 1,
          borderColor: "divider",
          position: "relative", // For overlay
        }}
      >
        {/* Main Content (Stats) - active when NO hover */}
        <Box
          sx={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden", // Fixes scrolling issue
            transition: "filter 0.2s, opacity 0.2s",
            filter: hoveredCard ? "blur(8px)" : "none",
            opacity: hoveredCard ? 0.3 : 1,
            pointerEvents: hoveredCard ? "none" : "auto",
          }}
        >
          <Box
            sx={{
              p: 2,
              borderBottom: 1,
              borderColor: "divider",
              display: "flex",
              alignItems: "center",
              gap: 1,
            }}
          >
            <BarChartIcon color="primary" />
            <Typography variant="h6" fontWeight="700">
              Deck Statistics
            </Typography>
          </Box>

          <Box sx={{ flex: 1, overflowY: "auto" }}>
            <DeckStats
              cards={deckCards}
              deckId={deck ? deck.id : undefined}
              format={format}
            />
          </Box>
        </Box>

        {/* Hover Overlay */}
        {hoveredCard && (
          <Box
            sx={{
              position: "absolute",
              inset: 0,
              zIndex: 20,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center", // Center vertically
              p: 2,
              gap: 2,
              overflow: "hidden", // Prevent overlay itself from scrolling
            }}
          >
            <Card
              sx={{
                width: "auto",
                height: "auto",
                maxHeight: "55%", // Limit height to avoid cutoff
                aspectRatio: "2.5/3.5",
                bgcolor: "transparent",
                borderRadius: "4.5% / 3.5%",
                boxShadow: 24,
                overflow: "hidden",
                transform: "perspective(1000px) rotateY(5deg)",
                flexShrink: 1, // Allow shrinking if needed
              }}
            >
              {hoveredCard.image_uris?.normal ? (
                <CardMedia
                  component="img"
                  image={hoveredCard.image_uris.normal}
                  alt={hoveredCard.name}
                  sx={{ width: "100%", height: "100%", objectFit: "cover" }}
                />
              ) : (
                <Box
                  sx={{
                    width: "100%",
                    height: "100%",
                    bgcolor: "background.paper",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    p: 4,
                    textAlign: "center",
                  }}
                >
                  <Typography variant="h5" fontWeight="700">
                    {hoveredCard.name}
                  </Typography>
                </Box>
              )}
            </Card>

            {/* Info Panel */}
            <Paper
              sx={{
                width: "100%",
                maxWidth: 400,
                p: 2,
                borderRadius: 1, // Reduced radius
                bgcolor: "background.paper",
                backdropFilter: "blur(20px)",
                border: 1,
                borderColor: "divider",
                display: "flex",
                flexDirection: "column",
                maxHeight: "40%", // Leave room for card
                overflowY: "auto", // Scroll if text is long
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  mb: 1,
                  flexShrink: 0,
                }}
              >
                <Typography variant="h6" fontWeight="900" lineHeight={1.1}>
                  {hoveredCard.name}
                </Typography>
                <Typography
                  variant="subtitle2"
                  sx={{
                    bgcolor: "action.hover",
                    px: 1,
                    py: 0.5,
                    borderRadius: 1,
                    fontFamily: "monospace",
                    flexShrink: 0,
                  }}
                >
                  {hoveredCard.mana_cost}
                </Typography>
              </Box>
              <Typography
                variant="subtitle2"
                color="primary.main"
                fontWeight="700"
                gutterBottom
                sx={{ flexShrink: 0 }}
              >
                {hoveredCard.type_line}
              </Typography>
              <Divider sx={{ my: 1.5, flexShrink: 0 }} />
              <Typography
                variant="body2"
                sx={{
                  whiteSpace: "pre-wrap",
                  lineHeight: 1.6,
                  color: "text.primary",
                }}
              >
                {hoveredCard.oracle_text}
              </Typography>
            </Paper>
          </Box>
        )}
      </Box>
    </Box>
  );
};;
