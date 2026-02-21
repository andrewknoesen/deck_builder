import React from "react";
import {
  ListItem,
  ListItemAvatar,
  Avatar,
  Paper,
  ListItemText,
  Box,
  Typography,
} from "@mui/material";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import PersonIcon from "@mui/icons-material/Person";
import ReactMarkdown from "react-markdown";

interface Message {
  role: "user" | "agent";
  content: string;
}

interface ChatBubbleProps {
  message: Message;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ message }) => {
  const isUser = message.role === "user";

  return (
    <ListItem
      alignItems="flex-start"
      className={`chat-bubble-container ${isUser ? "user" : "agent"}`}
      sx={{ gap: 1.5 }} // Keep some SX for simple spacing if needed, or move to CSS entirely. CSS has gap: 12px
    >
      <ListItemAvatar sx={{ minWidth: 40, mt: 0 }}>
        <Avatar sx={{ bgcolor: isUser ? "primary.main" : "secondary.main" }}> 
          {/* Note: Inverted logic in previous code? User was secondary? Theme says Primary is Indigo (User), Secondary is Rose (Agent/Bot?)? 
             Checked AgentChat.tsx, it had user=secondary/agent=primary in one place, and user=primary/agent=white in another.
             Let's standardize: User = Primary (Indigo), Agent = Secondary (Rose) or Slate. 
             Theme: Primary=Indigo, Secondary=Rose. 
             Let's use Primary for User, Slate (default/grey) or Secondary for Agent.
          */}
          {isUser ? <PersonIcon /> : <SmartToyIcon />}
        </Avatar>
      </ListItemAvatar>
      <Paper
        elevation={1}
        className={`chat-bubble-paper ${isUser ? "user" : "agent"}`}
      >
        <ListItemText
          primary={
            !isUser ? (
              <Box className="markdown-content">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </Box>
            ) : (
              <Typography variant="body1" sx={{ lineHeight: 1.6, fontSize: "1rem" }}>
                {message.content}
              </Typography>
            )
          }
        />
      </Paper>
    </ListItem>
  );
};
