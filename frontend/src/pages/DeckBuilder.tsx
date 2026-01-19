import React, {
  useState,
  useEffect,
  useCallback,
  useMemo,
  useRef,
} from "react";
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
  CircularProgress,
  InputAdornment,
  Divider,
  Stack,
  Chip,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import SearchIcon from "@mui/icons-material/Search";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import GridViewIcon from "@mui/icons-material/GridView";
import { apiClient } from "../api/client";
import type { ScryfallCard, Deck, DeckCard } from "../types/mtg";
import { useAuth } from "../context/AuthContext";
import { SearchCard } from "../components/SearchCard";
import { DeckCard as DeckCardComponent } from "../components/DeckCard";
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

export const DeckBuilder: React.FC = () => {
  const { deckId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const isNew = !deckId || deckId === "new";

  // State
  const [title, setTitle] = useState("New Deck");
  const [deckCards, setDeckCards] = useState<DeckCard[]>([]);
  const [saveStatus, setSaveStatus] = useState<"saved" | "saving" | "unsaved">(
    "saved",
  );
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  // Debounce critical state for auto-save
  const debouncedTitle = useDebounce(title, 1000);
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
  useEffect(() => {
    if (deck) {
      setTitle(deck.title);
      setDeckCards(deck.cards || []);
      setIsInitialLoad(false);
    } else if (isNew) {
      setIsInitialLoad(false);
    }
  }, [deck, isNew]);

  // Track if we have unsaved changes locally
  useEffect(() => {
    if (!isInitialLoad) {
      // Check if current state differs from debounced (roughly implies typing)
      // Or simpler: just set to unsaved on any change, and let debounce effect handle save
      // But we can't easily compare "debounced" vs "current" in the same render easily without ref or separate effect.
      // Let's simplistically set 'unsaved' when title or cards change,
      // BUT we need to avoid setting it on initial load. `isInitialLoad` handles the initial hydration.
      setSaveStatus("unsaved");
    }
  }, [title, deckCards, isInitialLoad]);

  // Auto-save Effect
  useEffect(() => {
    // Don't save on initial load or if nothing changed (conceptually)
    if (isInitialLoad) return;

    const saveDeck = async () => {
      setSaveStatus("saving");
      try {
        const deckData = {
          title: debouncedTitle,
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
  }, [debouncedTitle, debouncedCards]);

  // Search State
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

  // Group cards
  const groupedCards = useMemo(() => {
    const groups: Record<string, DeckCard[]> = {};
    deckCards.forEach((dc) => {
      const type = getCardType(dc.card?.type_line);
      if (!groups[type]) groups[type] = [];
      groups[type].push(dc);
    });
    return groups;
  }, [deckCards]);

  const sortedGroups = useMemo(() => {
    return Object.keys(groupedCards).sort((a, b) => {
      return TYPE_ORDER.indexOf(a) - TYPE_ORDER.indexOf(b);
    });
  }, [groupedCards]);

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
            <Box sx={{ flex: 1 }}>
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
              <Typography
                variant="caption"
                fontWeight="700"
                color="text.secondary"
                sx={{ textTransform: "uppercase", letterSpacing: 1 }}
              >
                {deckCards.reduce((acc, curr) => acc + curr.quantity, 0)} Cards
              </Typography>
            </Box>

            {/* Status Indicator */}
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              {saveStatus === "saving" && (
                <Chip
                  icon={<CircularProgress size={14} color="inherit" />}
                  label="Saving..."
                  size="small"
                  variant="outlined"
                  color="default"
                />
              )}
              {saveStatus === "saved" && (
                <Chip
                  icon={<CheckCircleIcon />}
                  label="Saved"
                  size="small"
                  variant="outlined"
                  color="success"
                />
              )}
              {saveStatus === "unsaved" && (
                <Chip
                  icon={<CloudUploadIcon />}
                  label="Unsaved"
                  size="small"
                  variant="outlined"
                  color="warning"
                />
              )}
            </Box>
          </Box>
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

      {/* Right Column: Search (Reduced width) */}
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
            p: 4,
            zIndex: 10,
            bgcolor: "background.default",
            borderBottom: 1,
            borderColor: "divider",
          }}
        >
          <Typography
            variant="h4"
            fontWeight="900"
            gutterBottom
            sx={{ display: "flex", alignItems: "center", gap: 2 }}
          >
            Card Database{" "}
            <AutoAwesomeIcon sx={{ color: "warning.main", fontSize: 28 }} />
          </Typography>

          <Box
            component="form"
            onSubmit={handleSearch}
            sx={{ position: "relative", mt: 3 }}
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
        </Box>

        <Box sx={{ flex: 1, overflowY: "auto", p: 4 }}>
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
        </Box>
      </Box>
    </Box>
  );
};
