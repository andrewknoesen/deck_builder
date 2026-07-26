import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Box,
  Typography,
  IconButton,
  TextField,
  Button,
  Paper,
  CircularProgress,
  List,
  ListItemButton,
  ListItemText,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import DeleteIcon from "@mui/icons-material/DeleteOutline";
import LayersIcon from "@mui/icons-material/Layers";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import type { GoldfishSessionTree, GoldfishNode } from "../types/goldfish";
import type { Deck } from "../types/mtg";
import { GoldfishTree } from "../components/GoldfishTree";
import { NodeTrackerEditor } from "../components/NodeTrackerEditor";
import { useCardHover } from "../context/useCardHover";

export const GoldfishSessionPage: React.FC = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { setHoveredCard } = useCardHover();
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null);
  const [actionText, setActionText] = useState("");
  const [showDeckList, setShowDeckList] = useState(true);
  const [trackerDraft, setTrackerDraft] = useState<Record<string, number>>({});

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

  const addNode = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post(`/goldfish/sessions/${sessionId}/nodes`, {
        parent_id: selectedNodeId,
        label: actionText,
        trackers: trackerDraft,
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

  const addCardToActionText = (name: string) => {
    setActionText((prev) => (prev ? `${prev}, ${name}` : name));
  };

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
      </Box>

      <Box sx={{ flex: 1, minHeight: 0, display: "flex" }}>
        {showDeckList && (
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
            <Typography
              variant="overline"
              color="text.secondary"
              sx={{ pl: 1 }}
            >
              Deck List (
              {deckCards.reduce((acc, dc) => acc + dc.quantity, 0)})
            </Typography>
            <List dense disablePadding>
              {deckCards.map((dc) => (
                <ListItemButton
                  key={`${dc.card_id}-${dc.board}`}
                  onClick={() =>
                    dc.card && addCardToActionText(dc.card.name)
                  }
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
          </Box>
        )}

        <Box sx={{ flex: 1, minHeight: 0 }}>
          <GoldfishTree
            nodes={data.nodes}
            selectedNodeId={selectedNodeId}
            onSelectNode={setSelectedNodeId}
          />
        </Box>
      </Box>

      <Paper square sx={{ p: 2, borderTop: 1, borderColor: "divider" }}>
        <Typography variant="caption" color="text.secondary">
          {data.nodes.length === 0
            ? "Add the first action to start this session."
            : selectedNode
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
            placeholder='e.g. "Turn 2: cast Llanowar Elves"'
            value={actionText}
            onChange={(e) => setActionText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && actionText.trim()) addNode.mutate();
            }}
          />
          <Button
            variant="contained"
            onClick={() => addNode.mutate()}
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
      </Paper>
    </Box>
  );
};
