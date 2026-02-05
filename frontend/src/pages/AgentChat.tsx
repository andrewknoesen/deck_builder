import React, { useState, useRef, useEffect } from "react";
import {
  Box,
  Typography,
  Paper,
  Container,
  CircularProgress,
  List,
  ListItem,
  ListItemAvatar,
  Avatar,
  Divider,
} from "@mui/material";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import { useMutation } from "@tanstack/react-query";
import axios from "axios";
import { ChatBubble } from "../components/Agent/ChatBubble";
import { ChatInput } from "../components/Agent/ChatInput";

import "../styles/AgentChat.css";

// Reuse API URL from env or constant
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

interface Message {
  role: "user" | "agent";
  content: string;
}

export const AgentChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "agent",
      content:
        "Hello! I am the Magic: The Gathering Rules Judge. Ask me anything about game rules or card interactions.",
    },
  ]);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const mutation = useMutation({
    mutationFn: async (message: string) => {
      const response = await axios.post(`${API_URL}/ai/chat`, {
        message: message,
        context_cards: [], // Can be populated later
      });
      return response.data.response;
    },
    onSuccess: (data) => {
      setMessages((prev) => [...prev, { role: "agent", content: data }]);
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          content: "Sorry, I encountered an error. Please try again.",
        },
      ]);
    },
  });

  const handleSend = (message: string) => {
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    mutation.mutate(message);
  };

  return (
    <Container maxWidth="md" className="agent-chat-container">
      <Paper elevation={3} className="agent-chat-paper">
        <Box className="agent-chat-header">
          <Typography variant="h6" className="agent-chat-title">
            <SmartToyIcon /> AI Rules Judge
          </Typography>
        </Box>
        <Divider />
        
        <Box className="agent-chat-messages">
          <List>
            {messages.map((msg, index) => (
              <ChatBubble key={index} message={msg} />
            ))}
            {mutation.isPending && (
              <ListItem className="loading-item">
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

        <Divider />
        <ChatInput onSend={handleSend} disabled={mutation.isPending} />
      </Paper>
    </Container>
  );
};
