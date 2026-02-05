import React, { useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import "../styles/DeckList.css";
import {
  Container,
  Grid,
  Typography,
  Button,
  Box,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import LayersIcon from "@mui/icons-material/Layers";
import AutoStoriesIcon from "@mui/icons-material/AutoStories";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import { apiClient } from "../api/client";
import type { Deck } from "../types/mtg";
import { DeckListItem } from "../components/DeckListItem";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

export const DeckList: React.FC = () => {
  const queryClient = useQueryClient();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deckToDelete, setDeckToDelete] = useState<number | null>(null);

  const { data: decks = [], isLoading: loading } = useQuery({
    queryKey: ["decks"],
    queryFn: async () => {
      const res = await apiClient.get("/decks");
      return res.data;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (deckId: number) => {
      await apiClient.delete(`/decks/${deckId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["decks"] });
      handleCloseDialog();
    },
  });

  const handleDeleteClick = (id: number) => {
    setDeckToDelete(id);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = () => {
    if (deckToDelete) {
      deleteMutation.mutate(deckToDelete);
    }
  };

  const handleCloseDialog = () => {
    setDeleteDialogOpen(false);
    setDeckToDelete(null);
  };

  if (loading) {
    return (
      <Box className="deck-list-loading">
        <CircularProgress color="primary" />
        <Typography variant="body1" color="text.secondary">
          Fetching your collection...
        </Typography>
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" className="deck-list-container">
      <Box className="deck-list-header">
        <Box>
          <Typography
            variant="h3"
            component="h1"
            fontWeight="900"
            gutterBottom
            className="deck-list-title"
          >
            <AutoStoriesIcon sx={{ fontSize: 40, color: "primary.main" }} /> My
            Grimoire
          </Typography>
          <Typography
            variant="subtitle1"
            color="text.secondary"
            fontWeight="500"
          >
            Manage and refine your Magic: The Gathering decks.
          </Typography>
        </Box>
        <Button
          component={RouterLink}
          to="/decks/new"
          variant="contained"
          size="large"
          startIcon={<AddIcon />}
          className="deck-list-new-btn"
        >
          New Deck
        </Button>
      </Box>

      {decks.length === 0 ? (
        <Box className="deck-list-empty">
          <Box className="deck-list-empty-icon">
            <LayersIcon sx={{ fontSize: 40, color: "text.secondary" }} />
          </Box>
          <Typography variant="h4" fontWeight="800" gutterBottom>
            No decks found
          </Typography>
          <Typography
            variant="body1"
            color="text.secondary"
            className="deck-list-empty-text"
          >
            Your collection is waiting to be built. Start your first journey
            today.
          </Typography>
          <Button
            component={RouterLink}
            to="/decks/new"
            endIcon={<ChevronRightIcon />}
            sx={{ fontWeight: 800 }}
          >
            Build one now
          </Button>
        </Box>
      ) : (
        <Grid container spacing={4}>
          {decks.map((deck: Deck) => (
            <Grid size={{ xs: 12, md: 6, lg: 4 }} key={deck.id}>
              <DeckListItem deck={deck} onDelete={handleDeleteClick} />
            </Grid>
          ))}
        </Grid>
      )}

      <Dialog
        open={deleteDialogOpen}
        onClose={handleCloseDialog}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title" fontWeight="700">
          {"Delete this deck?"}
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="alert-dialog-description">
            Are you sure you want to delete this deck? This action cannot be
            undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={handleCloseDialog} sx={{ fontWeight: 700 }}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirmDelete}
            color="error"
            variant="contained"
            autoFocus
            sx={{ fontWeight: 700 }}
          >
            {deleteMutation.isPending ? "Deleting..." : "Delete"}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};
