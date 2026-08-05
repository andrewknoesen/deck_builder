import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Box,
  Typography,
  IconButton,
  TextField,
  Button,
  CircularProgress,
  List,
  ListItemButton,
  ListItemText,
  Divider,
  Drawer,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import DeleteIcon from "@mui/icons-material/DeleteOutline";
import LayersIcon from "@mui/icons-material/Layers";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import type {
  GoldfishSessionTree,
  GoldfishNode,
  GoldfishAction,
} from "../types/goldfish";
import type { Deck, ScryfallCard } from "../types/mtg";
import { GoldfishTree } from "../components/GoldfishTree";
import { NodeTrackerEditor } from "../components/NodeTrackerEditor";
import { GoldfishPlaymat } from "../components/GoldfishPlaymat";
import { useCardHover } from "../context/useCardHover";

export const GoldfishSessionPage: React.FC = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { setHoveredCard } = useCardHover();
  const theme = useTheme();
  // Below `md` the deck list + playmat + tree can't all fit side by side -
  // three fixed-width columns squeeze the playmat (the part you're actually
  // playing on) down to nothing. Start with both side panels closed there;
  // the header toggles still open them, as overlay drawers instead of
  // pushing the playmat out of view.
  const isNarrow = useMediaQuery(theme.breakpoints.down("md"));
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null);
  const [actionText, setActionText] = useState("");
  const [showDeckList, setShowDeckList] = useState(!isNarrow);
  const [showTree, setShowTree] = useState(!isNarrow);
  const [trackerDraft, setTrackerDraft] = useState<Record<string, number>>({});

  // The useState initializers above only run once, at mount. If the layout
  // crosses the isNarrow breakpoint afterwards (resizing an already-open
  // desktop window, rotating a tablet), showDeckList/showTree don't follow —
  // stale "true" values from a wide mount mean both panels render as
  // simultaneously-open overlay Drawers on a now-narrow screen, hiding the
  // playmat underneath both of them. Re-sync whenever the breakpoint itself
  // changes.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setShowDeckList(!isNarrow);
    setShowTree(!isNarrow);
  }, [isNarrow]);

  const queryKey = ["goldfishTree", sessionId];

  const { data, isLoading } = useQuery({
    queryKey,
    queryFn: async () => {
      const res = await apiClient.get(`/goldfish/sessions/${sessionId}`);
      return res.data as GoldfishSessionTree;
    },
  });

  const deckId = data?.session.deck_id;
  const { data: deck } = useQuery({
    queryKey: ["deck", deckId],
    queryFn: async () => {
      const res = await apiClient.get(`/decks/${deckId}`);
      return res.data as Deck;
    },
    enabled: !!deckId,
  });

  const selectedNode = data?.nodes.find((n) => n.id === selectedNodeId);

  // Trackers always mirror the selected node's own snapshot; re-synced
  // whenever the selection or the underlying data changes (e.g. right after
  // a new node is added and auto-selected).
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTrackerDraft(selectedNode?.trackers ?? {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedNodeId, data]);

  // Auto-select once the tree loads: for a session that already has nodes
  // (reopening a session you were mid-goldfish on), land on the most
  // recently created node so you pick up where you left off, instead of
  // always the empty "Game start" root - which was confusing on reopen,
  // since the tree panel doesn't make it obvious a later node exists.
  // A brand-new session only has its root, so this still resolves to it.
  useEffect(() => {
    if (data && selectedNodeId === null && data.nodes.length > 0) {
      const latest = data.nodes.reduce((a, b) =>
        new Date(b.created_at) > new Date(a.created_at) ? b : a,
      );
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSelectedNodeId(latest.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const addNode = useMutation({
    mutationFn: async (payload: {
      label?: string;
      trackers?: Record<string, number>;
      action?: GoldfishAction;
    }) => {
      const res = await apiClient.post(`/goldfish/sessions/${sessionId}/nodes`, {
        parent_id: selectedNodeId,
        ...payload,
      });
      return res.data as GoldfishNode;
    },
    onSuccess: (node) => {
      queryClient.invalidateQueries({ queryKey });
      setActionText("");
      setSelectedNodeId(node.id);
    },
  });

  const deleteNode = useMutation({
    mutationFn: async (nodeId: number) => {
      await apiClient.delete(`/goldfish/nodes/${nodeId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      setSelectedNodeId(null);
    },
  });

  if (isLoading || !data) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 6 }}>
        <CircularProgress color="primary" />
      </Box>
    );
  }

  const deckCards = (deck?.cards ?? [])
    .filter((dc) => dc.board === "main" || dc.board === "commander")
    .slice()
    .sort((a, b) => (a.card?.name ?? "").localeCompare(b.card?.name ?? ""));

  const cardById: Record<string, ScryfallCard> = {};
  (deck?.cards ?? []).forEach((dc) => {
    if (dc.card) cardById[dc.card_id] = dc.card;
  });

  const addCardToActionText = (name: string) => {
    setActionText((prev) => (prev ? `${prev}, ${name}` : name));
  };

  const deckListContent = (
    <>
      <Typography variant="overline" color="text.secondary" sx={{ pl: 1 }}>
        Deck List ({deckCards.reduce((acc, dc) => acc + dc.quantity, 0)})
      </Typography>
      <List dense disablePadding>
        {deckCards.map((dc) => (
          <ListItemButton
            key={`${dc.card_id}-${dc.board}`}
            onClick={() => dc.card && addCardToActionText(dc.card.name)}
            onMouseEnter={() => dc.card && setHoveredCard(dc.card)}
            onMouseLeave={() => setHoveredCard(null)}
            sx={{ borderRadius: 1, gap: 1, py: 0.5 }}
          >
            <Box
              component="img"
              src={dc.card?.image_uris?.small}
              alt={dc.card?.name}
              sx={{
                width: 32,
                height: 44,
                objectFit: "cover",
                borderRadius: 0.5,
                flexShrink: 0,
                bgcolor: "action.hover",
              }}
            />
            <ListItemText
              primary={`${dc.quantity}x ${dc.card?.name ?? dc.card_id}`}
              slotProps={{ primary: { fontSize: 13 } }}
            />
          </ListItemButton>
        ))}
      </List>
    </>
  );

  const treeContent = (
    <GoldfishTree
      nodes={data.nodes}
      selectedNodeId={selectedNodeId}
      onSelectNode={(id) => {
        setSelectedNodeId(id);
        if (isNarrow) setShowTree(false);
      }}
    />
  );

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        bgcolor: "background.default",
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1,
          p: 2,
          borderBottom: 1,
          borderColor: "divider",
        }}
      >
        <IconButton onClick={() => navigate(-1)} size="small">
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h6" fontWeight="700" sx={{ flex: 1 }}>
          {data.session.name}
        </Typography>
        <IconButton
          onClick={() => setShowDeckList((v) => !v)}
          size="small"
          color={showDeckList ? "primary" : "default"}
          title="Toggle deck list"
        >
          <LayersIcon fontSize="small" />
        </IconButton>
        <IconButton
          onClick={() => setShowTree((v) => !v)}
          size="small"
          color={showTree ? "primary" : "default"}
          title="Toggle branch tree"
        >
          <AccountTreeIcon fontSize="small" />
        </IconButton>
      </Box>

      <Box sx={{ flex: 1, minHeight: 0, display: "flex" }}>
        {isNarrow ? (
          <Drawer
            anchor="left"
            open={showDeckList}
            onClose={() => setShowDeckList(false)}
            sx={{ "& .MuiDrawer-paper": { width: 280, boxSizing: "border-box", p: 1.5 } }}
          >
            {deckListContent}
          </Drawer>
        ) : (
          showDeckList && (
            <Box
              sx={{
                width: 260,
                flexShrink: 0,
                borderRight: 1,
                borderColor: "divider",
                overflowY: "auto",
                p: 1.5,
              }}
            >
              {deckListContent}
            </Box>
          )
        )}

        {/* Main view: the playmat is what you look at while goldfishing, so
            it gets the primary flexible area, scrolling on its own if a big
            hand/battlefield doesn't fit — never hiding Add/Prune below the
            fold the way the old fixed-height footer could. */}
        <Box sx={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
          {selectedNode?.state && (
            <>
              <GoldfishPlaymat
                state={selectedNode.state}
                cardById={cardById}
                turnNumber={selectedNode.turn_number}
                onAction={(action) => addNode.mutate({ action })}
                disabled={addNode.isPending}
              />
              <Divider />
            </>
          )}

          <Box sx={{ p: 2 }}>
            <Typography variant="caption" color="text.secondary">
              {selectedNode
                ? `Adding after: "${selectedNode.label}". Adding another action here (instead of pruning first) creates a branch.`
                : "No node selected — the next action starts a new root line."}
            </Typography>

            <Box sx={{ mt: 1 }}>
              <NodeTrackerEditor trackers={trackerDraft} onChange={setTrackerDraft} />
            </Box>

            <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
              <TextField
                fullWidth
                size="small"
                placeholder='e.g. "Opponent passed the turn" (or use the actions above)'
                value={actionText}
                onChange={(e) => setActionText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && actionText.trim()) {
                    addNode.mutate({ label: actionText, trackers: trackerDraft });
                  }
                }}
              />
              <Button
                variant="contained"
                onClick={() =>
                  addNode.mutate({ label: actionText, trackers: trackerDraft })
                }
                disabled={!actionText.trim() || addNode.isPending}
              >
                Add
              </Button>
              {selectedNode && (
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={() => deleteNode.mutate(selectedNode.id)}
                  disabled={deleteNode.isPending}
                >
                  Prune
                </Button>
              )}
            </Box>
          </Box>
        </Box>

        {isNarrow ? (
          <Drawer
            anchor="right"
            open={showTree}
            onClose={() => setShowTree(false)}
            sx={{ "& .MuiDrawer-paper": { width: "85vw", maxWidth: 380, boxSizing: "border-box" } }}
          >
            {treeContent}
          </Drawer>
        ) : (
          showTree && (
            <Box
              sx={{
                width: 380,
                flexShrink: 0,
                borderLeft: 1,
                borderColor: "divider",
              }}
            >
              {treeContent}
            </Box>
          )
        )}
      </Box>
    </Box>
  );
};
