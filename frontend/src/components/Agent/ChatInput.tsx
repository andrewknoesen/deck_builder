import React, { useState } from "react";
import { Box, TextField, Button } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSend, disabled }) => {
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    onSend(input);
    setInput("");
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Box className="agent-chat-input-area">
      <TextField
        fullWidth
        placeholder="Ask a rules question..."
        variant="outlined"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyPress}
        disabled={disabled}
        multiline
        maxRows={4}
        sx={{ 
            "& .MuiOutlinedInput-root": {
                color: "text.primary",
                backgroundColor: "background.default",
                borderRadius: 2
            }
        }}
      />
      <Button
        variant="contained"
        color="primary"
        endIcon={<SendIcon />}
        onClick={handleSend}
        disabled={disabled || !input.trim()}
        className="agent-chat-send-btn"
      >
        Send
      </Button>
    </Box>
  );
};
