import React, { useState } from "react";
import {
  Box,
  Typography,
  Button,
  IconButton,
  Chip,
  Popover,
  List,
  ListItem,
  ListItemText,
  TextField,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import RemoveIcon from "@mui/icons-material/Remove";
import ShuffleIcon from "@mui/icons-material/Shuffle";
import SkipNextIcon from "@mui/icons-material/SkipNext";
import type { GameState, GoldfishAction, GoldfishZone, Zones } from "../types/goldfish";
import type { ScryfallCard } from "../types/mtg";
import { useCardHover } from "../context/useCardHover";
import { opponentOwnerLabel } from "../utils/goldfishLabels";

interface GoldfishPlaymatProps {
  state: GameState;
  cardById: Record<string, ScryfallCard>;
  turnNumber: number | null;
  onAction: (action: GoldfishAction) => void;
  disabled?: boolean;
  // Opponent deck's title (untrimmed), used to derive the opponent board's
  // ownerLabel when `state.opponent_zones` is present. See
  // GoldfishSessionPage.tsx for where this comes from.
  opponentDeckTitle?: string;
}

const CardThumb: React.FC<{
  cardId: string;
  cardById: Record<string, ScryfallCard>;
}> = ({ cardId, cardById }) => {
  const { setHoveredCard } = useCardHover();
  const card = cardById[cardId];
  return (
    <Box
      component="img"
      src={card?.image_uris?.small}
      alt={card?.name ?? cardId}
      onMouseEnter={() => card && setHoveredCard(card)}
      onMouseLeave={() => setHoveredCard(null)}
      sx={{
        width: 56,
        height: 78,
        objectFit: "cover",
        borderRadius: 1,
        bgcolor: "action.hover",
        flexShrink: 0,
      }}
    />
  );
};

// A Lightning Bolt is one node, not three. The +/- buttons update the
// displayed number immediately but only commit (and create a tree node)
// after a short pause in clicking, so a burst of clicks collapses into a
// single life-total change instead of one node per click.
const LIFE_COMMIT_DELAY_MS = 700;

const LifeCounter: React.FC<{
  label: string;
  value: number;
  onChange: (newValue: number) => void;
  disabled?: boolean;
}> = ({ label, value, onChange, disabled }) => {
  const [input, setInput] = useState<string>(String(value));
  const pendingRef = React.useRef<number | null>(null);
  const timerRef = React.useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  React.useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    pendingRef.current = null;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setInput(String(value));
  }, [value]);

  React.useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const commitNow = (newValue: number) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    pendingRef.current = null;
    if (newValue !== value) onChange(newValue);
  };

  const bump = (delta: number) => {
    const newValue = (pendingRef.current ?? value) + delta;
    pendingRef.current = newValue;
    setInput(String(newValue));
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => commitNow(newValue), LIFE_COMMIT_DELAY_MS);
  };

  const commitInput = () => {
    const parsed = Number(input);
    if (!Number.isNaN(parsed)) {
      commitNow(parsed);
    } else {
      setInput(String(pendingRef.current ?? value));
    }
  };

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <IconButton size="small" disabled={disabled} onClick={() => bump(-1)}>
        <RemoveIcon fontSize="small" />
      </IconButton>
      <TextField
        size="small"
        variant="standard"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onBlur={commitInput}
        onKeyDown={(e) => {
          if (e.key === "Enter") commitInput();
        }}
        sx={{ width: 48, "& input": { textAlign: "center" } }}
        slotProps={{ input: { disableUnderline: true } }}
      />
      <IconButton size="small" disabled={disabled} onClick={() => bump(1)}>
        <AddIcon fontSize="small" />
      </IconButton>
    </Box>
  );
};

const ZoneCountChip: React.FC<{
  label: string;
  cardIds: string[];
  cardById: Record<string, ScryfallCard>;
  onRetrieve: (cardId: string) => void;
  zone: GoldfishZone;
}> = ({ label, cardIds, cardById, onRetrieve }) => {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  return (
    <>
      <Chip
        label={`${label}: ${cardIds.length}`}
        size="small"
        onClick={(e) => cardIds.length > 0 && setAnchorEl(e.currentTarget)}
        sx={{ cursor: cardIds.length > 0 ? "pointer" : "default" }}
      />
      <Popover
        open={!!anchorEl}
        anchorEl={anchorEl}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
      >
        <List dense sx={{ minWidth: 220, maxHeight: 300, overflowY: "auto" }}>
          {cardIds.map((cardId, i) => (
            <ListItem
              key={`${cardId}-${i}`}
              secondaryAction={
                <Button
                  size="small"
                  onClick={() => {
                    onRetrieve(cardId);
                    setAnchorEl(null);
                  }}
                >
                  To hand
                </Button>
              }
            >
              <ListItemText primary={cardById[cardId]?.name ?? cardId} />
            </ListItem>
          ))}
        </List>
      </Popover>
    </>
  );
};

interface GoldfishPlayerBoardProps {
  zones: Zones;
  cardById: Record<string, ScryfallCard>;
  lifeTotal: number;
  onLifeChange: (newValue: number) => void;
  // Callback already carries whichever `target` ("self"/"opponent") this
  // board's owner corresponds to — this component stays agnostic to that.
  onAction: (action: GoldfishAction) => void;
  ownerLabel: string;
  // Self board always uses the hardcoded adjective-form labels ("Your Hand
  // (N)") regardless of `ownerLabel`'s literal value; the opponent board
  // uses the possessive-noun form ("{ownerLabel}'s Hand (N)"). These are two
  // distinct templates, not one applied to both sides.
  isSelf: boolean;
  disabled?: boolean;
}

const GoldfishPlayerBoard: React.FC<GoldfishPlayerBoardProps> = ({
  zones,
  cardById,
  lifeTotal,
  onLifeChange,
  onAction,
  ownerLabel,
  isSelf,
  disabled,
}) => {
  const isLand = (cardId: string) =>
    (cardById[cardId]?.type_line ?? "").includes("Land");

  const handLabel = isSelf ? `Your Hand (${zones.hand.length})` : `${ownerLabel}'s Hand (${zones.hand.length})`;
  const battlefieldLabel = isSelf
    ? `Your Battlefield (${zones.battlefield.length})`
    : `${ownerLabel}'s Battlefield (${zones.battlefield.length})`;

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
      <Typography variant="overline" color="text.secondary" fontWeight="700">
        {ownerLabel}
      </Typography>

      <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
        <Button
          size="small"
          variant="outlined"
          startIcon={<ShuffleIcon />}
          disabled={disabled || zones.library.length < 2}
          onClick={() => onAction({ type: "shuffle" })}
        >
          Shuffle
        </Button>

        <ZoneCountChip
          label="Library"
          cardIds={zones.library}
          cardById={cardById}
          zone="library"
          onRetrieve={(cardId) =>
            onAction({
              type: "move_zone",
              card_id: cardId,
              from_zone: "library",
              to_zone: "hand",
            })
          }
        />
        <ZoneCountChip
          label="Graveyard"
          cardIds={zones.graveyard}
          cardById={cardById}
          zone="graveyard"
          onRetrieve={(cardId) =>
            onAction({
              type: "move_zone",
              card_id: cardId,
              from_zone: "graveyard",
              to_zone: "hand",
            })
          }
        />
        <ZoneCountChip
          label="Exile"
          cardIds={zones.exile}
          cardById={cardById}
          zone="exile"
          onRetrieve={(cardId) =>
            onAction({
              type: "move_zone",
              card_id: cardId,
              from_zone: "exile",
              to_zone: "hand",
            })
          }
        />

        <Button
          size="small"
          variant="contained"
          startIcon={<AddIcon />}
          disabled={disabled || zones.library.length === 0}
          onClick={() => onAction({ type: "draw" })}
        >
          Draw
        </Button>

        <Box sx={{ display: "flex", alignItems: "center", gap: 2, ml: "auto" }}>
          <LifeCounter label="Life" value={lifeTotal} disabled={disabled} onChange={onLifeChange} />
        </Box>
      </Box>

      <Box>
        <Typography variant="overline" color="text.secondary">
          {handLabel}
        </Typography>
        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mt: 0.5 }}>
          {zones.hand.map((cardId, i) => (
            <Box
              key={`${cardId}-${i}`}
              sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 0.5 }}
            >
              <CardThumb cardId={cardId} cardById={cardById} />
              <Button
                size="small"
                variant="outlined"
                disabled={disabled}
                onClick={() =>
                  onAction({
                    type: isLand(cardId) ? "play_land" : "cast",
                    card_id: cardId,
                  })
                }
                sx={{ fontSize: 11, py: 0, minWidth: 0, px: 1 }}
              >
                {isLand(cardId) ? "Play" : "Cast"}
              </Button>
            </Box>
          ))}
        </Box>
      </Box>

      <Box>
        <Typography variant="overline" color="text.secondary">
          {battlefieldLabel}
        </Typography>
        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mt: 0.5 }}>
          {zones.battlefield.map((cardId, i) => (
            <Box
              key={`${cardId}-${i}`}
              sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 0.5 }}
            >
              <CardThumb cardId={cardId} cardById={cardById} />
              <Box sx={{ display: "flex", gap: 0.5 }}>
                <Button
                  size="small"
                  disabled={disabled}
                  onClick={() =>
                    onAction({
                      type: "move_zone",
                      card_id: cardId,
                      from_zone: "battlefield",
                      to_zone: "graveyard",
                    })
                  }
                  sx={{ fontSize: 10, py: 0, minWidth: 0, px: 0.5 }}
                >
                  GY
                </Button>
                <Button
                  size="small"
                  disabled={disabled}
                  onClick={() =>
                    onAction({
                      type: "move_zone",
                      card_id: cardId,
                      from_zone: "battlefield",
                      to_zone: "hand",
                    })
                  }
                  sx={{ fontSize: 10, py: 0, minWidth: 0, px: 0.5 }}
                >
                  Hand
                </Button>
                <Button
                  size="small"
                  disabled={disabled}
                  onClick={() =>
                    onAction({
                      type: "move_zone",
                      card_id: cardId,
                      from_zone: "battlefield",
                      to_zone: "exile",
                    })
                  }
                  sx={{ fontSize: 10, py: 0, minWidth: 0, px: 0.5 }}
                >
                  Exile
                </Button>
              </Box>
            </Box>
          ))}
        </Box>
      </Box>
    </Box>
  );
};

export const GoldfishPlaymat: React.FC<GoldfishPlaymatProps> = ({
  state,
  cardById,
  turnNumber,
  onAction,
  disabled,
  opponentDeckTitle,
}) => {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2, p: 1.5 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
        <Chip
          label={turnNumber ? `Turn ${turnNumber}` : "Pre-game"}
          size="small"
          color="primary"
          variant="outlined"
        />
        <Button
          size="small"
          variant="outlined"
          startIcon={<SkipNextIcon />}
          disabled={disabled}
          onClick={() => onAction({ type: "next_turn" })}
        >
          Next Turn
        </Button>

        {/* Preserved standalone "Opp" life counter (the plain 3b feature —
            an opponent life total tracked with no opponent deck at all).
            Only stops rendering once a real opponent board exists to carry
            it instead. */}
        {!state.opponent_zones && (
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, ml: "auto" }}>
            <LifeCounter
              label="Opp"
              value={state.opponent_life_total}
              disabled={disabled}
              onChange={(newValue) =>
                onAction({ type: "set_life", life_total: newValue, target: "opponent" })
              }
            />
          </Box>
        )}
      </Box>

      <GoldfishPlayerBoard
        zones={state}
        cardById={cardById}
        lifeTotal={state.life_total}
        onLifeChange={(newValue) =>
          onAction({ type: "set_life", life_total: newValue, target: "self" })
        }
        onAction={(action) => onAction({ ...action, target: "self" })}
        ownerLabel="You"
        isSelf
        disabled={disabled}
      />

      {state.opponent_zones && (
        <GoldfishPlayerBoard
          zones={state.opponent_zones}
          cardById={cardById}
          lifeTotal={state.opponent_life_total}
          onLifeChange={(newValue) =>
            onAction({ type: "set_life", life_total: newValue, target: "opponent" })
          }
          onAction={(action) => onAction({ ...action, target: "opponent" })}
          ownerLabel={opponentOwnerLabel(opponentDeckTitle)}
          isSelf={false}
          disabled={disabled}
        />
      )}
    </Box>
  );
};
