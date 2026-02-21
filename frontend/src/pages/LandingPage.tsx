
import {
  Box,
  Typography,
  Button,
  Container,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  Stack,
} from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import StyleIcon from "@mui/icons-material/Style"; // Represents Decks
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome"; // Represents Brewing
import CollectionsIcon from "@mui/icons-material/Collections"; // Represents Collection

import "../styles/LandingPage.css";

export const LandingPage = () => {
  return (
    <Box className="landing-container">
      {/* Hero Section */}
      <Box className="landing-hero">
        <Container maxWidth="md">
          <Stack spacing={2} alignItems="center">
            <Box className="landing-hero-icon-box">
              <StyleIcon sx={{ fontSize: 24, color: "white" }} />
            </Box>

            <Typography
              variant="h4"
              component="h1"
              fontWeight="900"
              className="landing-hero-title"
            >
              Master Your{" "}
              <Box component="span" className="landing-hero-highlight">
                Magic
              </Box>
            </Typography>
            <Typography
              variant="subtitle1"
              color="text.secondary"
              className="landing-hero-subtitle"
            >
              The ultimate tool for deck brewing, collection management, and
              theory-crafting. Built for modern Magic: The Gathering players.
            </Typography>

            <Stack direction="row" spacing={2} className="landing-cta-stack">
              <Button
                component={RouterLink}
                to="/decks/new"
                variant="contained"
                size="medium"
                startIcon={<AddCircleOutlineIcon />}
                className="landing-btn-primary"
              >
                Start Brewing
              </Button>
              <Button
                component={RouterLink}
                to="/decks"
                variant="outlined"
                size="medium"
                startIcon={<StyleIcon />}
                className="landing-btn-outlined"
              >
                View Decks
              </Button>
            </Stack>
          </Stack>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="xl" className="landing-features-container">
        <Grid container spacing={4}>
          {/* Decks Section */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Card className="landing-feature-card">
              <CardActionArea
                component={RouterLink}
                to="/decks"
                className="landing-feature-action"
              >
                <CardContent className="landing-feature-content">
                  <Box className="landing-feature-icon-box feature-icon-primary">
                    <StyleIcon sx={{ fontSize: 40, color: "primary.main" }} />
                  </Box>
                  <Typography variant="h4" fontWeight="800">
                    Your Decks
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Organize, analyze, and refine your deck library. Track your
                    builds across different formats.
                  </Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>

          {/* Brewing Section */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Card className="landing-feature-card">
              <CardActionArea
                component={RouterLink}
                to="/decks/new"
                className="landing-feature-action"
              >
                <CardContent className="landing-feature-content">
                  <Box className="landing-feature-icon-box feature-icon-secondary">
                    <AutoAwesomeIcon
                      sx={{ fontSize: 40, color: "secondary.main" }}
                    />
                  </Box>
                  <Typography variant="h4" fontWeight="800">
                    Start Brewing
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Powerful search, instant card previews, and a smooth curve
                    analyzer to craft your next winner.
                  </Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>

          {/* Collection Section */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Card className="landing-feature-card">
              {/* Pointing to decks for now as a placeholder, or could be /collection if we had it */}
              <CardActionArea
                component={RouterLink}
                to="/decks"
                className="landing-feature-action"
              >
                <CardContent className="landing-feature-content">
                  <Box className="landing-feature-icon-box feature-icon-success">
                    <CollectionsIcon sx={{ fontSize: 40, color: "#10b981" }} />
                  </Box>
                  <Typography variant="h4" fontWeight="800">
                    Collection
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Track every card you own. Filter by set, rarity, and foil
                    status. (Coming Soon)
                  </Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};
