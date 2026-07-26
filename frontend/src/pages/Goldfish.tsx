import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Container,
  Grid,
  Card,
  CardActionArea,
  CardContent,
  Typography,
  Button,
  Box,
  CircularProgress,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import AddIcon from "@mui/icons-material/Add";
import SportsEsportsIcon from "@mui/icons-material/SportsEsports";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import type { Deck } from "../types/mtg";
import type { GoldfishSession } from "../types/goldfish";

export const Goldfish: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedDeckId, setSelectedDeckId] = useState<number | null>(null);
  const [newSessionOpen, setNewSessionOpen] = useState(false);
  const [newSessionName, setNewSessionName] = useState("");

  const { data: decks = [], isLoading: loadingDecks } = useQuery({
    queryKey: ["decks"],
    queryFn: async () => {
      const res = await apiClient.get("/decks");
      return res.data as Deck[];
    },
  });

  const { data: sessions = [], isLoading: loadingSessions } = useQuery({
    queryKey: ["goldfishSessions", selectedDeckId],
    queryFn: async () => {
      const res = await apiClient.get("/goldfish/sessions", {
        params: { deck_id: selectedDeckId },
      });
      return res.data as GoldfishSession[];
    },
    enabled: selectedDeckId !== null,
  });

  const createSession = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post("/goldfish/sessions", {
        deck_id: selectedDeckId,
        name: newSessionName || undefined,
      });
      return res.data as GoldfishSession;
    },
    onSuccess: (session) => {
      queryClient.invalidateQueries({ queryKey: ["goldfishSessions", selectedDeckId] });
      setNewSessionOpen(false);
      setNewSessionName("");
      navigate(`/goldfish/${session.id}`);
    },
  });

  const selectedDeck = decks.find((d) => d.id === selectedDeckId);

  if (loadingDecks) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 6 }}>
        <CircularProgress color="primary" />
      </Box>
    );
  }

  if (!selectedDeckId) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Typography variant="h3" fontWeight="900" gutterBottom>
          <SportsEsportsIcon sx={{ fontSize: 36, color: "primary.main", mr: 1 }} />
          Practice Mode
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 4 }}>
          Pick a deck to goldfish. Every action you take becomes a node in a
          branching tree — rewind to any earlier point and try a different
          line without losing the original.
        </Typography>

        <Grid container spacing={3}>
          {decks.map((deck) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={deck.id}>
              <Card>
                <CardActionArea onClick={() => setSelectedDeckId(deck.id!)}>
                  <CardContent>
                    <Typography variant="h6" fontWeight="700">
                      {deck.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {deck.format || "No format set"}
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 3 }}>
        <IconButton onClick={() => setSelectedDeckId(null)} size="small">
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4" fontWeight="800">
          {selectedDeck?.title}
        </Typography>
      </Box>

      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h6" color="text.secondary">
          Practice Sessions
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setNewSessionOpen(true)}
        >
          New Session
        </Button>
      </Box>

      {loadingSessions ? (
        <CircularProgress size={24} />
      ) : sessions.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          No practice sessions yet for this deck. Start one to begin
          goldfishing.
        </Typography>
      ) : (
        <List>
          {sessions.map((session) => (
            <ListItemButton
              key={session.id}
              onClick={() => navigate(`/goldfish/${session.id}`)}
              sx={{ borderRadius: 2, mb: 1, bgcolor: "background.paper" }}
            >
              <ListItemText
                primary={session.name}
                secondary={new Date(session.created_at).toLocaleString()}
              />
            </ListItemButton>
          ))}
        </List>
      )}

      <Dialog open={newSessionOpen} onClose={() => setNewSessionOpen(false)}>
        <DialogTitle>New Practice Session</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Session name (optional)"
            value={newSessionName}
            onChange={(e) => setNewSessionName(e.target.value)}
            sx={{ mt: 1, minWidth: 320 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewSessionOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => createSession.mutate()}
            disabled={createSession.isPending}
          >
            Start
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};
