
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

export const LandingPage = () => {
  return (
    <Box sx={{ bgcolor: "background.default", minHeight: "100%", pb: 8 }}>
      {/* Hero Section */}
      <Box
        sx={{
          bgcolor: "background.paper",
          pt: 4,
          pb: 4,
          background:
            "linear-gradient(180deg, rgba(15,23,42,1) 0%, rgba(2,6,23,1) 100%)", // Slate-900 to Slate-950
          borderBottom: 1,
          borderColor: "divider",
          textAlign: "center",
        }}
      >
        <Container maxWidth="md">
          <Stack spacing={2} alignItems="center">
            <Box
              sx={{
                width: 48,
                height: 48,
                bgcolor: "primary.main",
                borderRadius: 3,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: 8,
                mb: 2,
              }}
            >
              <StyleIcon sx={{ fontSize: 24, color: "white" }} />
            </Box>

            <Typography
              variant="h4"
              component="h1"
              fontWeight="900"
              sx={{ letterSpacing: "-0.02em" }}
            >
              Master Your{" "}
              <Box component="span" sx={{ color: "primary.main" }}>
                Magic
              </Box>
            </Typography>
            <Typography
              variant="subtitle1"
              color="text.secondary"
              sx={{ maxWidth: "600px", mx: "auto", lineHeight: 1.6 }}
            >
              The ultimate tool for deck brewing, collection management, and
              theory-crafting. Built for modern Magic: The Gathering players.
            </Typography>

            <Stack direction="row" spacing={2} sx={{ pt: 2 }}>
              <Button
                component={RouterLink}
                to="/decks/new"
                variant="contained"
                size="medium"
                startIcon={<AddCircleOutlineIcon />}
                sx={{
                  borderRadius: 3,
                  px: 3,
                  py: 1,
                  fontSize: "1rem",
                  boxShadow: 8,
                }}
              >
                Start Brewing
              </Button>
              <Button
                component={RouterLink}
                to="/decks"
                variant="outlined"
                size="medium"
                startIcon={<StyleIcon />}
                sx={{ borderRadius: 3, px: 3, py: 1, fontSize: "1rem" }}
              >
                View Decks
              </Button>
            </Stack>
          </Stack>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="xl" sx={{ mt: 8 }}>
        <Grid container spacing={4}>
          {/* Decks Section */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Card
              sx={{
                height: "100%",
                borderRadius: 0,
                border: 1,
                borderColor: "divider",
                bgcolor: "transparent",
              }}
            >
              <CardActionArea
                component={RouterLink}
                to="/decks"
                sx={{ height: "100%", p: 2 }}
              >
                <CardContent
                  sx={{
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    textAlign: "center",
                    gap: 2,
                  }}
                >
                  <Box
                    sx={{
                      p: 2,
                      borderRadius: "50%",
                      bgcolor: "rgba(99, 102, 241, 0.1)",
                    }}
                  >
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
            <Card
              sx={{
                height: "100%",
                borderRadius: 0,
                border: 1,
                borderColor: "divider",
                bgcolor: "transparent",
              }}
            >
              <CardActionArea
                component={RouterLink}
                to="/decks/new"
                sx={{ height: "100%", p: 2 }}
              >
                <CardContent
                  sx={{
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    textAlign: "center",
                    gap: 2,
                  }}
                >
                  <Box
                    sx={{
                      p: 2,
                      borderRadius: "50%",
                      bgcolor: "rgba(244, 63, 94, 0.1)",
                    }}
                  >
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
            <Card
              sx={{
                height: "100%",
                borderRadius: 0,
                border: 1,
                borderColor: "divider",
                bgcolor: "transparent",
              }}
            >
              {/* Pointing to decks for now as a placeholder, or could be /collection if we had it */}
              <CardActionArea
                component={RouterLink}
                to="/decks"
                sx={{ height: "100%", p: 2 }}
              >
                <CardContent
                  sx={{
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    textAlign: "center",
                    gap: 2,
                  }}
                >
                  <Box
                    sx={{
                      p: 2,
                      borderRadius: "50%",
                      bgcolor: "rgba(16, 185, 129, 0.1)",
                    }}
                  >
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
