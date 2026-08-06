import { Box, Typography, Button, Container, CardMedia } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";

import { apiClient } from "../api/client";
import type { ScryfallCard } from "../types/mtg";
import { CardGlyphIcon } from "../components/icons/CardGlyphIcon";
import { ManaCurveGlyphIcon } from "../components/icons/ManaCurveGlyphIcon";
import { CardStackGlyphIcon } from "../components/icons/CardStackGlyphIcon";
import { BinderGlyphIcon } from "../components/icons/BinderGlyphIcon";
import { BranchGlyphIcon } from "../components/icons/BranchGlyphIcon";
import "../styles/LandingPage.css";

// Command Tower's art doubles as hero texture: cool blue-grey palette that
// already sits close to the theme's steel-blue accent, and the card itself
// is the default Commander staple (the app defaults new decks to Commander),
// so the "which card" choice isn't arbitrary. Fetched live via the app's own
// Scryfall-backed endpoint rather than hardcoding a CDN URL, so it fails soft
// (falls back to the card-back placeholder below) instead of hotlinking
// something that can 404.
const HERO_CARD_QUERY = '!"Command Tower"';

export const LandingPage = () => {
  const { data: heroCard, isError: heroArtFailed } = useQuery({
    queryKey: ["landing-hero-card"],
    queryFn: async () => {
      const res = await apiClient.get("/cards/search", {
        params: { q: HERO_CARD_QUERY },
      });
      return res.data?.data?.[0] as ScryfallCard | undefined;
    },
    staleTime: Infinity,
    retry: 1,
  });

  return (
    <Box className="landing-container">
      {/* Hero */}
      <Box className="landing-hero">
        <Container maxWidth="lg" className="landing-hero-grid">
          <Box className="landing-hero-copy">
            <Typography
              variant="h2"
              component="h1"
              className="landing-hero-title"
            >
              Goldfish your list before you{" "}
              <Box component="span" className="landing-hero-highlight">
                sleeve it up
              </Box>
              .
            </Typography>
            <Typography
              variant="subtitle1"
              color="text.secondary"
              className="landing-hero-subtitle"
            >
              Real Scryfall card data, hypergeometric draw-odds instead of a
              rule of thumb, and a mana curve that updates as you build.
            </Typography>
          </Box>

          {/* Real card art, not a stock illustration — same rounded-corner,
              2.5:3.5 card-image treatment used everywhere else in the app
              (see SearchCard.tsx / CardHoverPreview.tsx), tilted for
              asymmetry so the hero doesn't read as a centered SaaS panel. */}
          <Box className="landing-hero-card-wrap">
            {heroCard?.image_uris?.normal && !heroArtFailed ? (
              <CardMedia
                component="img"
                image={heroCard.image_uris.normal}
                alt={heroCard.name}
                className="landing-hero-card-img"
              />
            ) : (
              <Box className="landing-hero-card-placeholder">
                <CardGlyphIcon sx={{ fontSize: 56 }} />
              </Box>
            )}
          </Box>
        </Container>
      </Box>

      {/* Feature composition, deliberately three different shapes rather
          than the same icon-heading-line row repeated three times (that
          exact pattern — even scaled down and stacked below a "hero" card —
          is the tell docs/UI_DEGENERIC_DESIGN.md calls out). Primary block
          keeps its outsized weight; Decks/Collection are compressed into one
          compact paired row instead of two identical rows; Practice Mode
          gets a wider illustrated row built around an actual branching-tree
          glyph, since that's literally what the feature looks like
          (see GoldfishTree.tsx), not a gamepad icon. */}
      <Container maxWidth="lg" className="landing-features">
        <Box className="landing-primary-feature">
          <ManaCurveGlyphIcon className="landing-primary-feature-icon" />
          <Typography variant="h3" component="h2">
            Numbers while you build
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Search live Scryfall data as you type. Land-count math, curve,
            and opening-hand odds — like your chance of 3 lands by turn 3 —
            update with every card you add.
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

        <Box className="landing-secondary">
          <Box className="landing-secondary-pair">
            <Box
              component={RouterLink}
              to="/decks"
              className="landing-secondary-pair-item"
            >
              <CardStackGlyphIcon className="landing-secondary-pair-icon" />
              <Typography variant="subtitle2" fontWeight={700}>
                Your Decks
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Deck size, banned-list legality, and sideboard limits,
                checked as you build.
              </Typography>
            </Box>
            <Box className="landing-secondary-pair-divider" />
            <Box
              component={RouterLink}
              to="/collection"
              className="landing-secondary-pair-item"
            >
              <BinderGlyphIcon className="landing-secondary-pair-icon" />
              <Typography variant="subtitle2" fontWeight={700}>
                Collection
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Every card you own, grouped by type.
              </Typography>
            </Box>
          </Box>

          <Box
            component={RouterLink}
            to="/goldfish"
            className="landing-secondary-tree"
          >
            <BranchGlyphIcon className="landing-secondary-tree-icon" />
            <Box>
              <Typography variant="subtitle1" fontWeight={700}>
                Practice Mode
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Goldfish a list on a branching tree — rewind to any past
                turn, replay it, try the other line.
              </Typography>
            </Box>
          </Box>
        </Box>
      </Container>
    </Box>
  );
};
