import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Box,
  Typography,
  IconButton,
  TextField,
  Button,
  Paper,
  CircularProgress,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import DeleteIcon from "@mui/icons-material/DeleteOutline";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import type { GoldfishSessionTree, GoldfishNode } from "../types/goldfish";
import { GoldfishTree } from "../components/GoldfishTree";

export const GoldfishSessionPage: React.FC = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null);
  const [actionText, setActionText] = useState("");

  const queryKey = ["goldfishTree", sessionId];

  const { data, isLoading } = useQuery({
    queryKey,
    queryFn: async () => {
      const res = await apiClient.get(`/goldfish/sessions/${sessionId}`);
      return res.data as GoldfishSessionTree;
    },
  });

  const addNode = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post(`/goldfish/sessions/${sessionId}/nodes`, {
        parent_id: selectedNodeId,
        label: actionText,
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

  const selectedNode = data.nodes.find((n) => n.id === selectedNodeId);

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
        <Typography variant="h6" fontWeight="700">
          {data.session.name}
        </Typography>
      </Box>

      <Box sx={{ flex: 1, minHeight: 0 }}>
        <GoldfishTree
          nodes={data.nodes}
          selectedNodeId={selectedNodeId}
          onSelectNode={setSelectedNodeId}
        />
      </Box>

      <Paper square sx={{ p: 2, borderTop: 1, borderColor: "divider" }}>
        <Typography variant="caption" color="text.secondary">
          {data.nodes.length === 0
            ? "Add the first action to start this session."
            : selectedNode
              ? `Adding after: "${selectedNode.label}". Adding another action here (instead of pruning first) creates a branch.`
              : "No node selected — the next action starts a new root line."}
        </Typography>
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
