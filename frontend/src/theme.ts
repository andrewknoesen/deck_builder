import { createTheme } from '@mui/material/styles';

// Color strategy: a deliberate "mana gold" accent (Magic's own mana-symbol
// gold, not a generic SaaS purple) on a warm near-black, not Tailwind's
// stock cool-gray Slate scale. Every value below is OKLCH-derived and
// contrast-checked against WCAG AA (>=4.5:1 body text, >=3:1 large text) —
// see the design notes in PLAN.md for the verification. Restrained color
// strategy: the gold carries primary actions and selection state only, not
// decoration, per this app's product (not marketing) register.
export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#ecaa0b', // mana gold
      light: '#f8c562',
      dark: '#d08700',
      contrastText: '#110c07',
    },
    secondary: {
      main: '#f04c5a', // danger/remove
    },
    success: {
      main: '#61bd67',
    },
    background: {
      default: '#110c07', // warm near-black, not Slate-950
      paper: '#1b150e',
    },
    text: {
      primary: '#f3ede7',
      secondary: '#ada397',
    },
    divider: '#2f271e',
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontWeight: 800, letterSpacing: '-0.02em' },
    h2: { fontWeight: 800, letterSpacing: '-0.02em' },
    h3: { fontWeight: 700, letterSpacing: '-0.01em' },
    h4: { fontWeight: 700 },
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
