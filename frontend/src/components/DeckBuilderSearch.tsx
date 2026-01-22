import React, { useState, useEffect } from "react";
import {
  Autocomplete,
  TextField,
  Box,
  Typography,
  CircularProgress,
  InputAdornment,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import { apiClient } from "../api/client";
import type { ScryfallCard } from "../types/mtg";
import { useDebounce } from "../hooks/useDebounce";
import { useCardHover } from "../context/CardHoverContext";

interface DeckBuilderSearchProps {
  onAddCard: (card: ScryfallCard) => void;
}

export const DeckBuilderSearch: React.FC<DeckBuilderSearchProps> = ({
  onAddCard,
}) => {
  const [open, setOpen] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [options, setOptions] = useState<ScryfallCard[]>([]);
  const [loading, setLoading] = useState(false);

  const debouncedInput = useDebounce(inputValue, 500);
  const { setHoveredCard } = useCardHover();

  useEffect(() => {
    let active = true;

    if (debouncedInput === "") {
      setOptions([]);
      return undefined;
    }

    setLoading(true);

    const fetchCards = async () => {
      try {
        const res = await apiClient.get("/cards/search", {
          params: { q: debouncedInput },
        });
        if (active) {
          setOptions(res.data.data || []);
        }
      } catch (err) {
        console.error("Search failed", err);
        if (active) {
          setOptions([]);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    fetchCards();

    return () => {
      active = false;
    };
  }, [debouncedInput]);

  return (
    <Autocomplete
      open={open}
      onOpen={() => setOpen(true)}
      onClose={() => setOpen(false)}
      inputValue={inputValue}
      onInputChange={(_, newInputValue) => setInputValue(newInputValue)}
      options={options}
      getOptionLabel={(option) => option.name}
      loading={loading}
      clearOnBlur={false} // Keep input for rapid searches potentially
      onChange={(_, value) => {
        if (value) {
          onAddCard(value);
          setInputValue(""); // Clear after selection for next search
          setOptions([]); // Clear options
          // Keep it open? Standard behavior is close. We'll stick to default.
        }
      }}
      renderInput={(params) => (
        <TextField
          {...params}
          placeholder="Search for a card to add..."
          fullWidth
          variant="outlined"
          sx={{
             "& .MuiOutlinedInput-root": {
               bgcolor: "rgba(255,255,255,0.05)",
               borderRadius: 3, // slightly more rounded
               p: "6px 12px", // Fix padding to be uniform
               "& fieldset": { borderColor: "rgba(255,255,255,0.1)" },
               "&:hover fieldset": { borderColor: "rgba(255,255,255,0.3)" },
               "&.Mui-focused fieldset": { borderColor: "primary.main" },
             }
          }}
          InputProps={{
            ...params.InputProps,
            startAdornment: (
                <InputAdornment position="start">
                    <SearchIcon color="action" />
                </InputAdornment>
            ),
            endAdornment: (
              <>
                {loading ? (
                  <CircularProgress color="inherit" size={20} />
                ) : null}
                {params.InputProps.endAdornment}
              </>
            ),
          }}
        />
      )}
      renderOption={(props, option) => {
        // We need to extract the key and spread the rest of the props
        // to avoid React warning about key being part of spread
        const { key, ...optionProps } = props;
        
        return (
          <Box
            key={key}
            component="li"
            {...optionProps}
            sx={{
                display: "flex",
                flexDirection: "column",
                alignItems: "flex-start",
                borderBottom: "1px solid",
                borderColor: "divider",
                py: 1,
            }}
            onMouseEnter={() => setHoveredCard(option)}
            onMouseLeave={() => setHoveredCard(null)}
          >
            <Box sx={{ display: 'flex', width: '100%', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body2" fontWeight="700">
                {option.name}
                </Typography>
                <Typography variant="caption" sx={{ bgcolor: 'action.hover', px: 0.5, borderRadius: 0.5 }}>
                    {option.mana_cost}
                </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary">
              {option.type_line}
            </Typography>
          </Box>
        );
      }}
      noOptionsText={inputValue ? "No cards found" : "Type to search..."}
      filterOptions={(x) => x} // Disable client-side filtering since we do it server-side
    />
  );
};
