import { createTheme } from '@mui/material/styles';

// Color strategy: dark slate, per explicit product-owner override (2026-08) —
// the prior warm-gold accent read as too loud/neon in practice. Muted steel-
// blue accent on cool neutral slate, desaturated semantic colors (no bright
// red/green), all contrast-checked against WCAG AA (>=4.5:1 body text,
// >=3:1 large text). Restrained color strategy still applies: the accent
// carries primary actions and selection state only, not decoration.
export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#5b7fa3', // muted steel-blue accent
      light: '#82a0bf',
      dark: '#3d5a76',
      contrastText: '#f5f7f9',
    },
    secondary: {
      main: '#b56464', // danger/remove, desaturated
    },
    success: {
      main: '#5f9e78',
    },
    background: {
      default: '#12151a', // cool near-black slate
      paper: '#1a1e25',
    },
    text: {
      primary: '#e7e9ec',
      secondary: '#98a1ac',
    },
    divider: '#2a2f37',
  },
  typography: {
    // Font strategy: two families, not one undifferentiated stack (see
    // docs/UI_DEGENERIC_DESIGN.md item 1). Inter carries body/UI chrome,
    // where legibility at small sizes matters more than character — it's
    // still the right call there, just not for headlines. Besley (a spurred
    // slab serif, loaded in index.html) carries h1-h4: it has real weight
    // and contrast at display sizes, closer to card-frame titling than a
    // generic sans, without literally tracing Magic's own Beleren/Matrix
    // branding. Deliberately not Fraunces/Playfair/Georgia — those read as
    // their own "AI landing page" cliche at this point.
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontFamily: '"Besley", serif', fontWeight: 800, letterSpacing: '-0.01em' },
    h2: { fontFamily: '"Besley", serif', fontWeight: 700, letterSpacing: '-0.01em' },
    h3: { fontFamily: '"Besley", serif', fontWeight: 700 },
    h4: { fontFamily: '"Besley", serif', fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
  },
  shape: {
    borderRadius: 10,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 700,
          borderRadius: 10,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none', // Remove default elevation gradient
          borderRadius: 0, // deliberate: sharp panels vs. rounded interactive controls
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});
