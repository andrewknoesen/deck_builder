import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardActionArea,
  CardContent,
  Typography,
  Chip,
  Box,
  CardActions,
  Button,
} from "@mui/material";
import LayersIcon from '@mui/icons-material/Layers';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import type { Deck } from '../types/mtg';
// Style import is handled in parent or global if not modular, 
// strictly speaking it should be imported here if it's used here, 
// but DeckList.css is imported in DeckList page. 
// For better modularity, it's safer to ensure styles are available.
// However, since it shares the file, I'll assume it's loaded.

interface DeckListItemProps {
  deck: Deck;
  onDelete?: (id: number) => void;
}

export const DeckListItem: React.FC<DeckListItemProps> = ({
  deck,
  onDelete,
}) => {
  const navigate = useNavigate();

  return (
    <Card
      variant="outlined"
      className="deck-list-item-card"
    >
      <CardActionArea
        onClick={() => navigate(`/decks/${deck.id}`)}
        className="deck-list-item-action"
      >
        <CardContent className="deck-list-item-content">
          <Box className="deck-list-item-header">
            <Chip
              label={deck.format || "Casual"}
              size="small"
              color="primary"
              sx={{
                fontWeight: 800,
                borderRadius: 1,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                height: 20,
                fontSize: "0.65rem",
              }}
            />
            <ChevronRightIcon
              color="primary"
              sx={{
                opacity: 0,
                transition: "0.2s",
                ".MuiCardActionArea-root:hover &": {
                  opacity: 1,
                  transform: "translateX(0)",
                },
                transform: "translateX(-5px)",
              }}
            />
          </Box>

          <Typography
            variant="h5"
            component="h3"
            fontWeight="800"
            gutterBottom
            sx={{ lineHeight: 1.2, mb: 3 }}
          >
            {deck.title}
          </Typography>

          <div className="deck-list-item-stats">
            <div className="deck-list-item-stat">
              <LayersIcon sx={{ fontSize: 16 }} />
              <Typography variant="caption" fontWeight="700">
                {(deck.cards || []).reduce(
                  (acc, card) => acc + card.quantity,
                  0,
                )}{" "}
                Cards
              </Typography>
            </div>
            <div className="deck-list-item-stat">
              <AccessTimeIcon sx={{ fontSize: 16 }} />
              <Typography variant="caption" fontWeight="700">
                Modified Recently
              </Typography>
            </div>
          </div>
        </CardContent>
      </CardActionArea>
      {onDelete && (
        <CardActions
          sx={{
            borderTop: "1px solid",
            borderColor: "divider",
            justifyContent: "flex-end",
            px: 2,
            py: 1,
            mt: "auto"
          }}
        >
          <Button
            size="small"
            color="error"
            startIcon={<DeleteOutlineIcon />}
            onClick={(e) => {
              e.stopPropagation();
              if (deck.id) {
                onDelete(deck.id);
              }
            }}
            sx={{ fontWeight: 700 }}
          >
            Delete
          </Button>
        </CardActions>
      )}
    </Card>
  );
};
