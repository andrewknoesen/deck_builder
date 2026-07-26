import React, { useState } from "react";
import { Box, Stack, TextField, IconButton } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import CloseIcon from "@mui/icons-material/Close";

interface NodeTrackerEditorProps {
  trackers: Record<string, number>;
  onChange: (trackers: Record<string, number>) => void;
}

/**
 * Generic named-counter editor: life, poison, storm count, whatever the user
 * wants to track at a node. Not a fixed set of fields on purpose - trackers
 * are an opaque key->value map both here and in the backend.
 */
export const NodeTrackerEditor: React.FC<NodeTrackerEditorProps> = ({
  trackers,
  onChange,
}) => {
  const [newName, setNewName] = useState("");
  const [newValue, setNewValue] = useState("");

  const updateValue = (name: string, value: number) => {
    onChange({ ...trackers, [name]: value });
  };

  const removeTracker = (name: string) => {
    const next = { ...trackers };
    delete next[name];
    onChange(next);
  };

  const addTracker = () => {
    const name = newName.trim();
    if (!name) return;
    onChange({ ...trackers, [name]: Number(newValue) || 0 });
    setNewName("");
    setNewValue("");
  };

  return (
    <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap", rowGap: 1 }}>
      {Object.entries(trackers).map(([name, value]) => (
        <Box
          key={name}
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 0.5,
            bgcolor: "background.paper",
            border: 1,
            borderColor: "divider",
            borderRadius: 2,
            pl: 1.5,
            pr: 0.5,
          }}
        >
          <Box
            component="span"
            sx={{ fontSize: 12, color: "text.secondary", whiteSpace: "nowrap" }}
          >
            {name}
          </Box>
          <TextField
            type="number"
            size="small"
            variant="standard"
            value={value}
            onChange={(e) => updateValue(name, Number(e.target.value))}
            sx={{ width: 56, "& input": { textAlign: "center", fontSize: 13 } }}
            slotProps={{ input: { disableUnderline: true } }}
          />
          <IconButton
            size="small"
            onClick={() => removeTracker(name)}
            sx={{ p: 0.25 }}
          >
            <CloseIcon sx={{ fontSize: 14 }} />
          </IconButton>
        </Box>
      ))}

      <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
        <TextField
          placeholder="Tracker (e.g. Life)"
          size="small"
          variant="standard"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") addTracker();
          }}
          sx={{ width: 120 }}
        />
        <TextField
          placeholder="0"
          type="number"
          size="small"
          variant="standard"
          value={newValue}
          onChange={(e) => setNewValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") addTracker();
          }}
          sx={{ width: 50 }}
        />
        <IconButton size="small" onClick={addTracker} disabled={!newName.trim()}>
          <AddIcon fontSize="small" />
        </IconButton>
      </Box>
    </Stack>
  );
};
