import React, { useState, useEffect, useCallback, useMemo } from "react";
import "../styles/DeckBuilder.css";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useNavigate, useLocation, Link as RouterLink } from "react-router-dom";
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
  Snackbar,
  Tooltip,
} from "@mui/material";
import {
  validateDeckSize,
  validateSideboardSize,
  getCardLimit,
  isCardLegal,
  isValidCommander,
} from "../utils/deckValidation";
import BarChartIcon from "@mui/icons-material/BarChart";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import SportsEsportsIcon from "@mui/icons-material/SportsEsports";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import GridViewIcon from "@mui/icons-material/GridView";
import { apiClient } from "../api/client";
import type { ScryfallCard, Deck, DeckCard } from "../types/mtg";
import { getFlippableFaces } from "../utils/cardFaces";
import { DeckCard as DeckCardComponent } from "../components/DeckCard";
import { DeckStats } from "../components/DeckStats";
import { DeckAdvisor } from "../components/DeckAdvisor";
import { DeckBuilderSearch } from "../components/DeckBuilderSearch";
import { useDebounce } from "../hooks/useDebounce";
import { useCardHover } from "../context/useCardHover";
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
  const location = useLocation();
  const queryClient = useQueryClient();
  const { hoveredCard } = useCardHover();

  const isNew = !deckId || deckId === "new";

  // State
  const [title, setTitle] = useState("New Deck");
  const [format, setFormat] = useState("Commander");
  const [deckCards, setDeckCards] = useState<DeckCard[]>([]);
  const [rightPaneTab, setRightPaneTab] = useState<"stats" | "advisor">("stats");
  const [synergySeed, setSynergySeed] = useState<{ query: string; nonce: number } | null>(null);
  const [saveStatus, setSaveStatus] = useState<"saved" | "saving" | "unsaved">(
    "saved",
  );
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [missingCards, setMissingCards] = useState<string[]>(
    (location.state as { missingCards?: string[] } | null)?.missingCards ?? [],
  );
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: "error" | "warning" | "info" | "success";
  }>({
    open: false,
    message: "",
    severity: "info",
  });

  const handleCloseSnackbar = () => {
    setSnackbar((prev) => ({ ...prev, open: false }));
  };

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

  // Sync remote data to local state ONLY on initial load. Intentionally one-shot
  // (guarded by isInitialLoad) rather than derived, since local state diverges
  // from the query result the moment the user starts editing.
  useEffect(() => {
    if (deck && isInitialLoad) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTitle(deck.title);
      setFormat(deck.format || "Commander");
      setDeckCards(deck.cards || []);
      setIsInitialLoad(false);
    } else if (isNew) {
      setIsInitialLoad(false);
    }
  }, [deck, isNew, isInitialLoad]);

  // Mark dirty on any edit after initial load; the auto-save effect below reads
  // saveStatus to decide whether to fire.
  useEffect(() => {
    if (!isInitialLoad) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
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
    // Intentionally keyed only off the debounced values: this should fire once per
    // settled edit, not on every saveStatus transition it causes, or on deckId/isNew
    // changing as a result of the navigate() call inside saveDeck. navigate and
    // queryClient are stable across renders.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedTitle, debouncedFormat, debouncedCards]);

  // Search State removed (now handled by DeckBuilderSearch)

  /* 
   * Card Management Logic (Board-Aware)
   * We now support the same card existing in multiple boards (e.g. 3 Main, 1 Side).
   */

  const addCard = useCallback(
    (card: ScryfallCard) => {
      setDeckCards((prev) => {
        // Default to adding to Mainboard
        const existingMain = prev.find((dc) => dc.card_id === card.id && dc.board === "main");

        if (existingMain) {
           return prev.map((dc) =>
            dc === existingMain ? { ...dc, quantity: dc.quantity + 1 } : dc
          );
        }
        return [
          ...prev,
          { card_id: card.id, quantity: 1, board: "main", card },
        ];
      });
    },
    [],
  );

  const updateQuantity = useCallback((cardId: string, board: string, delta: number) => {
    setDeckCards((prev) => {
      // Logic for Sideboard Limit Check
      if (board === "side" && delta > 0) {
          const currentSideboardCount = prev
              .filter(c => c.board === "side")
              .reduce((acc, curr) => acc + curr.quantity, 0);
          
          const splitRes = validateSideboardSize(format, currentSideboardCount + delta);
          // Block if it's an error (e.g. > 15 in constructed). Warnings (e.g. >0 in Commander) allow through.
          if (!splitRes.valid && splitRes.severity === "error") {
              setSnackbar({
                  open: true,
                  message: splitRes.message || "Sideboard limit reached.",
                  severity: "error",
              });
              return prev; // Do not apply change
          }
      }

      return prev
        .map((dc) => {
          if (dc.card_id === cardId && dc.board === board) {
            const newQty = Math.max(0, dc.quantity + delta);
            return { ...dc, quantity: newQty };
          }
          return dc;
        })
        .filter((dc) => dc.quantity > 0);
    });
  }, [format]);

  const removeCard = useCallback((cardId: string, board: string) => {
    setDeckCards((prev) => prev.filter((dc) => !(dc.card_id === cardId && dc.board === board)));
  }, []);

  const handleFindSynergies = useCallback((dc: DeckCard) => {
    const card = dc.card;
    if (!card) return;
    setRightPaneTab("advisor");
    setSynergySeed({
      query: `What cards would synergize well with \`${card.name}\` (${card.type_line})? Its text: "${card.oracle_text}"`,
      nonce: Date.now(),
    });
  }, []);

  const handleMoveCard = useCallback((cardId: string, fromBoard: string, toBoard: string, quantity: number = 1) => {
    setDeckCards((prev) => {
        const sourceIndex = prev.findIndex(dc => dc.card_id === cardId && dc.board === fromBoard);
        if (sourceIndex === -1) return prev;
        
        const source = prev[sourceIndex];
        
        // Validation: Commander
        if (toBoard === "commander" && !isValidCommander(source.card)) {
             setSnackbar({
               open: true,
               message: "This card cannot be your commander.",
               severity: "error",
             });
             return prev;
        }

        // Validation: Sideboard Limit
        if (toBoard === "side") {
            const currentSideboardCount = prev
                .filter(c => c.board === "side")
                .reduce((acc, curr) => acc + curr.quantity, 0);
            
            // moving FROM side TO side shouldn't happen, but if it did, net change is 0. 
            // Here we assume moving from Main/Maybe TO Side.
            if (fromBoard !== "side") {
                const splitRes = validateSideboardSize(format, currentSideboardCount + quantity);
                if (!splitRes.valid && splitRes.severity === "error") {
                    setSnackbar({
                        open: true,
                        message: splitRes.message || "Sideboard limit reached.",
                        severity: "error",
                    });
                    return prev; 
                }
            }
        }

        const newCards = [...prev];
        
        // 1. Decrement Source
        if (source.quantity <= quantity) {
             // Moved entire stack
             newCards.splice(sourceIndex, 1);
        } else {
             newCards[sourceIndex] = { ...source, quantity: source.quantity - quantity };
        }
        
        // 2. Increment/Create Destination
        // Commander can only have 1
        const actualQuantityToAdd = toBoard === "commander" ? 1 : quantity;

        const destIndex = newCards.findIndex(dc => dc.card_id === cardId && dc.board === toBoard);
        
        if (destIndex !== -1) {
             // Add to existing stack
             const dest = newCards[destIndex];
             // If commander, ensure quantity is 1 (idempotent)
             const newDestQty = toBoard === "commander" ? 1 : dest.quantity + actualQuantityToAdd;
             newCards[destIndex] = { ...dest, quantity: newDestQty };
        } else {
             // Create new stack
             newCards.push({
                 card_id: cardId,
                 quantity: actualQuantityToAdd,
                 board: toBoard,
                 card: source.card
             });
        }
        
        return newCards;
    });
  }, [format]);

  // Group cards
  const groupedCards = useMemo(() => {
    const groups: Record<string, DeckCard[]> = {};

    // Initialize standard mainboard groups
    TYPE_ORDER.forEach((t) => (groups[t] = []));
    groups["Commander"] = [];
    groups["Sideboard"] = [];
    groups["Maybeboard"] = [];

    deckCards.forEach((dc) => {
      if (dc.board === "commander") {
        groups["Commander"].push(dc);
      } else if (dc.board === "side") {
        groups["Sideboard"].push(dc);
      } else if (dc.board === "maybe") {
        groups["Maybeboard"].push(dc);
      } else {
        // Mainboard - group by type
        const typeKey = getCardType(dc.card?.type_line);
        if (!groups[typeKey]) groups[typeKey] = [];
        groups[typeKey].push(dc);
      }
    });

    // Remove empty groups
    Object.keys(groups).forEach((key) => {
      if (groups[key].length === 0) delete groups[key];
    });

    return groups;
  }, [deckCards]);

  const sortedGroups = useMemo(() => {
    // Order: Commander, then Mainboard types, then Sideboard, then Maybeboard
    const sectionOrder = [
      "Commander",
      ...TYPE_ORDER,
      "Sideboard",
      "Maybeboard",
    ];
    return Object.keys(groupedCards).sort((a, b) => {
      return sectionOrder.indexOf(a) - sectionOrder.indexOf(b);
    });
  }, [groupedCards]);

  const totalCards = useMemo(
    () => deckCards.filter(c => c.board === "main" || c.board === "commander").reduce((acc, curr) => acc + curr.quantity, 0),
    [deckCards],
  );

  const sideboardCount = useMemo(
    () => deckCards.filter(c => c.board === "side").reduce((acc, curr) => acc + curr.quantity, 0),
    [deckCards],
  );

  // Global card counts (Main + Side + Commander) for limit validation
  const globalCardCounts = useMemo(() => {
     const counts: Record<string, number> = {};
     deckCards.forEach(dc => {
         // Maybeboard usually doesn't count towards limit, but let's assume limit applies to Deck (Main+Side)
         if (dc.board !== "maybe") {
             counts[dc.card_id] = (counts[dc.card_id] || 0) + dc.quantity;
         }
     });
     return counts;
  }, [deckCards]);

  const validation = useMemo(() => {
    const deckVal = validateDeckSize(format, totalCards);
    const sideVal = validateSideboardSize(format, sideboardCount);
    
    if (!deckVal.valid) return deckVal;
    if (!sideVal.valid) return sideVal;
    
    return { valid: true, severity: "success", message: "" };
  }, [format, totalCards, sideboardCount]);



// ... existing imports ...

// ... within Code ...

  if (loadingDecks) {
    return (
      <Box className="deck-builder-loading">
        <CircularProgress size={48} color="primary" />
        <Typography variant="body1" color="text.secondary">
          Conjuring your deck...
        </Typography>
      </Box>
    );
  }

  return (
    <Box className="deck-builder-container">
      {/* Left Column: Deck Inventory (Expanded to 65%) */}
      <Paper
        square
        elevation={0}
        className="deck-builder-pane-left"
      >
        {/* Header */}
        <Box className="deck-builder-header">
          <Box className="deck-builder-header-top">
            <IconButton
              component={RouterLink}
              to="/decks"
              size="small"
              className="deck-builder-back-btn"
            >
              <ArrowBackIcon fontSize="small" />
            </IconButton>

            {/* Title & Format Row */}
            <Box className="deck-builder-controls">
              <TextField
                fullWidth
                variant="standard"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Deck Title"
                className="deck-builder-title-input"
                InputProps={{
                  disableUnderline: true,
                  // CSS class deck-builder-title-input handles font size/weight on input
                }}
              />
              <TextField
                select
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                variant="outlined"
                size="small"
                SelectProps={{ native: true }}
                sx={{ width: 140, "& .MuiInputBase-input": { py: 0.5 } }} // Keep minimal sizing SX if tricky in CSS or move to class
              >
                {FORMATS.map((fmt) => (
                  <option key={fmt} value={fmt}>
                    {fmt}
                  </option>
                ))}
              </TextField>
            </Box>

            <Tooltip
              title={
                deck?.id
                  ? "Practice with this deck"
                  : "Save this deck first to practice with it"
              }
            >
              <span>
                <IconButton
                  component={RouterLink}
                  to={deck?.id ? `/goldfish?deckId=${deck.id}` : "#"}
                  size="small"
                  disabled={!deck?.id}
                  className="deck-builder-practice-btn"
                >
                  <SportsEsportsIcon fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>
          </Box>

          {/* Search Row */}
          <Box className="deck-builder-search-row">
            <Box className="deck-builder-search-box">
              <DeckBuilderSearch onAddCard={addCard} />
            </Box>
            <Typography
              variant="caption"
              fontWeight="700"
              color="text.secondary"
              className="deck-builder-count"
            >
              {totalCards} Cards
            </Typography>
          </Box>

          <Collapse in={missingCards.length > 0}>
            <Alert
              severity="warning"
              className="deck-builder-alert"
              onClose={() => setMissingCards([])}
            >
              {missingCards.length} card{missingCards.length === 1 ? "" : "s"}{" "}
              from the import couldn't be found and {missingCards.length === 1 ? "was" : "were"}{" "}
              left out — use the search above to add the right card for each:
              <Box component="ul" sx={{ m: 0, mt: 0.5, pl: 2.5 }}>
                {missingCards.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </Box>
            </Alert>
          </Collapse>

          <Collapse in={!validation.valid}>
            {validation.message && (
              <Alert
                severity={validation.severity === "error" ? "error" : "warning"}
                className="deck-builder-alert"
              >
                {validation.message}
              </Alert>
            )}
          </Collapse>
        </Box>

        {/* Deck Content */}
        <Box className="deck-builder-content">
          {deckCards.length === 0 ? (
            <Box className="deck-builder-empty">
              <Box className="deck-builder-empty-icon">
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
                  <Box className="deck-builder-group-header">
                    <Typography
                      variant="subtitle2"
                      fontWeight="900"
                      color="text.secondary"
                      sx={{ textTransform: "uppercase", letterSpacing: 1 }}
                    >
                      {type}
                    </Typography>
                    <Box className="deck-builder-group-count">
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
                              onUpdateQuantity={(cid, delta) => updateQuantity(cid, dc.board, delta)}
                              onRemove={(cid) => removeCard(cid, dc.board)}
                              onMoveCard={handleMoveCard}
                              onFindSynergies={deck?.id ? handleFindSynergies : undefined}
                              limit={getCardLimit(format, dc.card)}
                              isCommanderFormat={isCommanderLike}
                              isIllegal={
                                !isCardLegal(format, dc.card) ||
                                isIllegalPlacement
                              }
                              canBeCommander={isValidCommander(dc.card)}
                              currentTotalQuantity={globalCardCounts[dc.card_id]}
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
      <Box className="deck-builder-pane-right">
        {/* Main Content (Stats) - active when NO hover */}
        <Box className={`deck-builder-stats ${hoveredCard ? "blurred" : ""}`}>
          <Box className="deck-builder-stats-header">
            <IconButton
              size="small"
              onClick={() => setRightPaneTab("stats")}
              color={rightPaneTab === "stats" ? "primary" : "default"}
            >
              <BarChartIcon />
            </IconButton>
            <IconButton
              size="small"
              onClick={() => setRightPaneTab("advisor")}
              color={rightPaneTab === "advisor" ? "primary" : "default"}
            >
              <SmartToyIcon />
            </IconButton>
            <Typography variant="h6" fontWeight="700">
              {rightPaneTab === "stats" ? "Deck Statistics" : "Deck Advisor"}
            </Typography>
          </Box>

          <Box className="deck-builder-stats-content">
            {rightPaneTab === "stats" ? (
              <DeckStats
                cards={deckCards.filter(
                  (c) => c.board === "main" || c.board === "commander",
                )}
                deckId={deck ? deck.id : undefined}
                format={format}
              />
            ) : (
              <DeckAdvisor
                deckId={deck ? deck.id : undefined}
                synergySeed={synergySeed}
              />
            )}
          </Box>
        </Box>

        {/* Hover Overlay */}
        {hoveredCard && (() => {
          // Double-faced/split cards: show both faces at once, side by side,
          // rather than a click-to-flip control -- this overlay only exists
          // while the mouse stays over the source card, so a button inside
          // it would vanish the instant the pointer moved toward it.
          const faces = getFlippableFaces(hoveredCard);
          return (
          <Box className="deck-builder-overlay">
            {faces ? (
              <Box sx={{ display: "flex", gap: 1.5, maxHeight: "55%", flexShrink: 1 }}>
                {faces.map((face) => (
                  <Card
                    key={face.name}
                    className="deck-builder-overlay-card"
                    sx={{ maxHeight: "100%" }}
                  >
                    {face.image_uris?.normal ? (
                      <CardMedia
                        component="img"
                        image={face.image_uris.normal}
                        alt={face.name}
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
                          p: 2,
                          textAlign: "center",
                        }}
                      >
                        <Typography variant="body1" fontWeight="700">
                          {face.name}
                        </Typography>
                      </Box>
                    )}
                  </Card>
                ))}
              </Box>
            ) : (
              <Card className="deck-builder-overlay-card">
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
            )}

            {/* Info Panel */}
            <Paper className="deck-builder-overlay-info">
              {faces ? (
                <Stack divider={<Divider sx={{ my: 1 }} />} spacing={1} sx={{ overflow: "auto" }}>
                  {faces.map((face) => (
                    <Box key={face.name}>
                      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", mb: 0.5 }}>
                        <Typography variant="subtitle1" fontWeight="900" lineHeight={1.1}>
                          {face.name}
                        </Typography>
                        <Typography
                          variant="subtitle2"
                          sx={{ bgcolor: "action.hover", px: 1, py: 0.5, borderRadius: 1, fontFamily: "monospace", flexShrink: 0 }}
                        >
                          {face.mana_cost}
                        </Typography>
                      </Box>
                      <Typography variant="subtitle2" color="primary.main" fontWeight="700" gutterBottom>
                        {face.type_line}
                      </Typography>
                      <Typography variant="body2" sx={{ whiteSpace: "pre-wrap", lineHeight: 1.6, color: "text.primary" }}>
                        {face.oracle_text}
                      </Typography>
                    </Box>
                  ))}
                </Stack>
              ) : (
                <>
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
                </>
              )}
            </Paper>
          </Box>
          );
        })()}
      </Box>
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          sx={{ width: "100%" }}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};;
