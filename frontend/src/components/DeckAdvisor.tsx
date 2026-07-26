import React, { useEffect, useRef, useState } from "react";
import {
  Box,
  List,
  ListItem,
  ListItemAvatar,
  Avatar,
  CircularProgress,
  Typography,
} from "@mui/material";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import { useMutation } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { ChatBubble } from "./Agent/ChatBubble";
import { ChatInput } from "./Agent/ChatInput";

interface Message {
  role: "user" | "agent";
  content: string;
}

interface DeckAdvisorProps {
  deckId?: number;
}

export const DeckAdvisor: React.FC<DeckAdvisorProps> = ({ deckId }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "agent",
      content:
        "Ask me for suggestions on this deck. Every card I recommend is looked up on Scryfall first, and I'll factor in this deck's mana curve, color balance, and format.",
    },
  ]);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const mutation = useMutation({
    mutationFn: async (query: string) => {
      const res = await apiClient.post("/ai/suggest", {
        deck_id: deckId,
        query,
      });
      return res.data.response as string;
    },
    onSuccess: (data) => {
      setMessages((prev) => [...prev, { role: "agent", content: data }]);
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          content: "Sorry, I couldn't get a suggestion. Please try again.",
        },
      ]);
    },
  });

  const handleSend = (message: string) => {
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    mutation.mutate(message);
  };

  if (!deckId) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="body2" color="text.secondary">
          Save this deck first (add a card to trigger auto-save) to get advisor
          suggestions.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <Box sx={{ flex: 1, overflowY: "auto" }}>
        <List>
          {messages.map((msg, index) => (
            <ChatBubble key={index} message={msg} />
          ))}
          {mutation.isPending && (
            <ListItem>
              <ListItemAvatar sx={{ minWidth: 40, mt: 0 }}>
                <Avatar sx={{ bgcolor: "primary.main" }}>
                  <SmartToyIcon />
                </Avatar>
              </ListItemAvatar>
              <CircularProgress size={24} />
            </ListItem>
          )}
          <div ref={messagesEndRef} />
        </List>
      </Box>
      <ChatInput
        onSend={handleSend}
        disabled={mutation.isPending}
        placeholder="Ask for deck suggestions..."
      />
    </Box>
  );
};
