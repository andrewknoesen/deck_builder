import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useNavigate, Link as RouterLink } from "react-router-dom";
import {
  Box,
  TextField,
  Typography,
  Button,
  IconButton,
  Grid,
  Paper,
  InputAdornment,
  Divider,
  Stack,
  CircularProgress,
  Tabs,
  Tab,
  Alert,
  Collapse,
} from "@mui/material";
import { validateDeckSize } from "../utils/deckValidation";
import BarChartIcon from "@mui/icons-material/BarChart";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import SearchIcon from "@mui/icons-material/Search";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import GridViewIcon from "@mui/icons-material/GridView";
import { apiClient } from "../api/client";
import type { ScryfallCard, Deck, DeckCard } from "../types/mtg";
import { useAuth } from "../context/AuthContext";
import { SearchCard } from "../components/SearchCard";
import { DeckCard as DeckCardComponent } from "../components/DeckCard";
import { DeckStats } from "../components/DeckStats";
import { useDebounce } from "../hooks/useDebounce";

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

  // Search State
  const [rightTab, setRightTab] = useState(0);
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<ScryfallCard[]>([]);
  const [searching, setSearching] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;
    setSearching(true);
    try {
      const res = await apiClient.get(`/cards/search`, {
        params: { q: query },
      });
      setSearchResults(res.data.data || []);
    } catch (err) {
      console.error("Search failed", err);
    } finally {
      setSearching(false);
    }
  };

  const addCard = useCallback((card: ScryfallCard) => {
    setDeckCards((prev) => {
      const existing = prev.find((dc) => dc.card_id === card.id);
      if (existing) {
        return prev.map((dc) =>
          dc.card_id === card.id ? { ...dc, quantity: dc.quantity + 1 } : dc,
        );
      }
      return [...prev, { card_id: card.id, quantity: 1, board: "main", card }];
    });
  }, []);

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
        <Box
          sx={{
            p: 3,
            borderBottom: 1,
            borderColor: "divider",
            bgcolor: "rgba(15, 23, 42, 0.8)",
            backdropFilter: "blur(12px)",
            position: "sticky",
            top: 0,
            zIndex: 20,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
            <IconButton
              component={RouterLink}
              to="/decks"
              size="small"
              sx={{ border: 1, borderColor: "divider", borderRadius: 2 }}
            >
              <ArrowBackIcon fontSize="small" />
            </IconButton>
            <Box
              sx={{ flex: 1, display: "flex", flexDirection: "column", gap: 1 }}
            >
              <Box sx={{ display: "flex", gap: 2, alignItems: "flex-start" }}>
                <TextField
                  fullWidth
                  variant="standard"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Deck Title"
                  InputProps={{
                    disableUnderline: true,
                    sx: { fontSize: "1.5rem", fontWeight: 900 },
                  }}
                />
                <TextField
                  select
                  value={format}
                  onChange={(e) => setFormat(e.target.value)}
                  variant="outlined"
                  size="small"
                  SelectProps={{ native: true }}
                  sx={{ width: 220 }}
                >
                  {FORMATS.map((fmt) => (
                    <option key={fmt} value={fmt}>
                      {fmt}
                    </option>
                  ))}
                </TextField>
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

            {/* Status Indicator */}
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}></Box>
          </Box>

          <Collapse in={!validation.valid}>
            {validation.message && (
              <Alert
                severity={validation.severity === "error" ? "error" : "warning"}
                sx={{
                  mx: 3,
                  mb: 2,
                  borderRadius: 2,
                  fontWeight: 500,
                  "& .MuiAlert-icon": { alignItems: "center" },
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
                        <DeckCardComponent
                          deckCard={dc}
                          onUpdateQuantity={updateQuantity}
                          onRemove={removeCard}
                          onMoveToBoard={handleMoveToBoard}
                          isCommanderFormat={
                            format === "Commander" || format === "Brawl"
                          }
                        />
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              ))}
            </Stack>
          )}
        </Box>
      </Paper>

      {/* Right Column: Search + Stats */}
      <Box
        sx={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          bgcolor: "background.default",
          minWidth: 0,
        }}
      >
        <Box
          sx={{
            px: 2,
            pt: 2,
            zIndex: 10,
            bgcolor: "background.default",
            borderBottom: 1,
            borderColor: "divider",
          }}
        >
          <Tabs value={rightTab} onChange={(_, v) => setRightTab(v)}>
            <Tab
              icon={<SearchIcon />}
              label="Search Cards"
              iconPosition="start"
              sx={{ minHeight: 64 }}
            />
            <Tab
              icon={<BarChartIcon />}
              label="Deck Stats"
              iconPosition="start"
              sx={{ minHeight: 64 }}
            />
          </Tabs>

          {rightTab === 0 && (
            <Box
              component="form"
              onSubmit={handleSearch}
              sx={{ position: "relative", my: 2 }}
            >
              <TextField
                fullWidth
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search by name, type, or color..."
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon color="action" />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <Button
                        type="submit"
                        variant="contained"
                        disabled={searching}
                        sx={{ minWidth: 80, borderRadius: 2 }}
                      >
                        {searching ? (
                          <CircularProgress size={20} color="inherit" />
                        ) : (
                          "Find"
                        )}
                      </Button>
                    </InputAdornment>
                  ),
                  sx: {
                    borderRadius: 4,
                    bgcolor: "background.paper",
                    boxShadow: 2,
                    pl: 2,
                    pr: 1,
                    py: 1,
                    "& fieldset": { border: "none" },
                  },
                }}
              />
            </Box>
          )}
        </Box>

        <Box sx={{ flex: 1, overflowY: "auto", p: rightTab === 0 ? 4 : 0 }}>
          {rightTab === 0 ? (
            <>
              {searching ? (
                <Grid container spacing={2}>
                  {[...Array(10)].map((_, i) => (
                    <Grid size={{ xs: 6, sm: 4, md: 3 }} key={i}>
                      <Box
                        sx={{
                          aspectRatio: "2.5/3.5",
                          bgcolor: "action.hover",
                          borderRadius: 3,
                          animation: "pulse 1.5s infinite opacity",
                        }}
                      />
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Grid container spacing={3}>
                  {searchResults.map((card) => (
                    <Grid size={{ xs: 6, sm: 4, md: 3 }} key={card.id}>
                      <SearchCard card={card} onAdd={addCard} />
                    </Grid>
                  ))}
                  {searchResults.length === 0 && !searching && (
                    <Box
                      sx={{
                        gridColumn: "1 / -1",
                        py: 10,
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        opacity: 0.3,
                        gap: 2,
                      }}
                    >
                      <AutoAwesomeIcon sx={{ fontSize: 60 }} />
                      <Typography variant="h5" fontWeight="700">
                        Search the multiverse
                      </Typography>
                    </Box>
                  )}
                </Grid>
              )}
            </>
          ) : (
            <DeckStats
              cards={deckCards}
              deckId={deck ? deck.id : undefined}
              format={format}
            />
          )}
        </Box>
      </Box>
    </Box>
  );
};
