import {
  Box,
  Typography,
  Button,
  Container,
  Stack,
} from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import StyleIcon from "@mui/icons-material/Style"; // Represents Decks
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome"; // Represents Brewing
import CollectionsIcon from "@mui/icons-material/Collections"; // Represents Collection
import SportsEsportsIcon from "@mui/icons-material/SportsEsports"; // Represents Practice Mode

import "../styles/LandingPage.css";

const secondaryLinks = [
  {
    to: "/decks",
    icon: StyleIcon,
    title: "Your Decks",
    description: "Organize and refine your library across every format.",
  },
  {
    to: "/collection",
    icon: CollectionsIcon,
    title: "Collection",
    description: "Track every card you own, filtered by set and rarity.",
  },
  {
    to: "/goldfish",
    icon: SportsEsportsIcon,
    title: "Practice Mode",
    description: "Goldfish a deck on a branching tree you can rewind.",
  },
];

export const LandingPage = () => {
  return (
    <Box className="landing-container">
      {/* Hero */}
      <Box className="landing-hero">
        <Container maxWidth="md">
          <Typography
            variant="h2"
            component="h1"
            className="landing-hero-title"
          >
            Build decks that actually{" "}
            <Box component="span" className="landing-hero-highlight">
              win
            </Box>
            .
          </Typography>
          <Typography
            variant="subtitle1"
            color="text.secondary"
            className="landing-hero-subtitle"
          >
            Search, brew, and stress-test Magic: The Gathering decks in one
            place — real Scryfall data, real mana-curve math, no guesswork.
          </Typography>
        </Container>
      </Box>

      {/* Feature composition: one emphasized entry point, not four
          identical cards — Start Brewing is the primary action most
          visitors want, so it gets the weight; the rest read as a plain
          list, not a repeated icon-circle template. */}
      <Container maxWidth="lg" className="landing-features">
        <Box className="landing-primary-feature">
          <AutoAwesomeIcon className="landing-primary-feature-icon" />
          <Typography variant="h3" component="h2">
            Start Brewing
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Instant card search with live previews and a mana-curve analyzer
            that updates as you build — see the shape of your deck while
            you're still shaping it.
          </Typography>
          <Button
            component={RouterLink}
            to="/decks/new"
            variant="contained"
            endIcon={<ArrowForwardIcon />}
            className="landing-primary-feature-cta"
          >
            Start Brewing
          </Button>
        </Box>

        <Stack className="landing-secondary-list" divider={<Box className="landing-secondary-divider" />}>
          {secondaryLinks.map(({ to, icon: Icon, title, description }) => (
            <Box
              key={title}
              component={RouterLink}
              to={to}
              className="landing-secondary-item"
            >
              <Icon className="landing-secondary-item-icon" />
              <Box>
                <Typography variant="subtitle1" fontWeight={700}>
                  {title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {description}
                </Typography>
              </Box>
            </Box>
          ))}
        </Stack>
      </Container>
    </Box>
  );
};
