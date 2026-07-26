import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Alert,
  Stack,
} from "@mui/material";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { apiClient } from "../api/client";

interface DeckImportModalProps {
  open: boolean;
  onClose: () => void;
}

interface DeckImportResponse {
  id: number;
  title: string;
  missing_cards: string[];
}

export const DeckImportModal: React.FC<DeckImportModalProps> = ({
  open,
  onClose,
}) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [text, setText] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  const importMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post<DeckImportResponse>("/decks/import", {
        text,
        name: name || undefined,
      });
      return res.data;
    },
    onSuccess: (data) => {
      setText("");
      setName("");
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["decks"] });
      onClose();
      navigate(`/decks/${data.id}`, {
        state: { missingCards: data.missing_cards },
      });
    },
    onError: (err) => {
      const message = axios.isAxiosError(err)
        ? (err.response?.data?.detail ?? "Import failed. Check the pasted text and try again.")
        : "Import failed. Check the pasted text and try again.";
      setError(message);
    },
  });

  const handleClose = () => {
    if (importMutation.isPending) return;
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle fontWeight="700">Import Deck</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField
            label="Deck name (optional)"
            placeholder="Leave blank to use the imported list's name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            fullWidth
          />
          <TextField
            label="Paste your decklist"
            placeholder={"4 Blanchwood Prowler\n3 Swamp\n...\n\nor an MTGA export with Deck/Sideboard sections"}
            value={text}
            onChange={(e) => setText(e.target.value)}
            multiline
            minRows={10}
            fullWidth
          />
        </Stack>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={handleClose} sx={{ fontWeight: 700 }}>
          Cancel
        </Button>
        <Button
          onClick={() => importMutation.mutate()}
          variant="contained"
          disabled={!text.trim() || importMutation.isPending}
          sx={{ fontWeight: 700 }}
        >
          {importMutation.isPending ? "Importing..." : "Import"}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
