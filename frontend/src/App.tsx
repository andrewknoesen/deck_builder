import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link as RouterLink, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DeckList } from './pages/DeckList';
import { DeckBuilder } from './pages/DeckBuilder';
import { ThemeProvider, CssBaseline, AppBar, Toolbar, Typography, Button, Box, Avatar, Container } from '@mui/material';
import { theme } from './theme';
import DashboardIcon from '@mui/icons-material/Dashboard'; // Placeholder for custom logo
import LayersIcon from '@mui/icons-material/Layers';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, login } = useAuth();

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="sticky" elevation={0} sx={{ bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}>
        <Container maxWidth="xl">
          <Toolbar disableGutters sx={{ justifyContent: 'space-between' }}>
            {/* Logo area */}
            <Box
              component={RouterLink}
              to="/"
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1.5,
                textDecoration: 'none',
                color: 'text.primary',
                '&:hover': { color: 'primary.main' }, // Hover effect on text
              }}
            >
              <Box
                sx={{
                  width: 40,
                  height: 40,
                  bgcolor: 'primary.main',
                  borderRadius: 3,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: 4,
                }}
              >
                <DashboardIcon sx={{ color: 'white' }} />
              </Box>
              <Typography variant="h5" component="div" sx={{ fontWeight: 900, letterSpacing: '-0.02em' }}>
                MTG <Box component="span" sx={{ color: 'primary.main' }}>Builder</Box>
              </Typography>
            </Box>

            {/* Navigation & Auth */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Button
                component={RouterLink}
                to="/decks"
                startIcon={<LayersIcon />}
                sx={{ color: 'text.secondary', fontWeight: 700, '&:hover': { color: 'text.primary' } }}
              >
                My Decks
              </Button>

              <Button
                variant="outlined"
                onClick={() => login('mock-jwt-token')}
                sx={{
                  borderRadius: 3,
                  fontWeight: 700,
                  borderColor: 'divider',
                  color: 'white',
                  '&:hover': { borderColor: 'primary.main', bgcolor: 'primary.main' }
                }}
              >
                {user ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Avatar sx={{ width: 24, height: 24, bgcolor: 'primary.main', fontSize: '0.75rem' }}>
                      {user.name.charAt(0)}
                    </Avatar>
                    {user.name}
                  </Box>
                ) : 'Sign In'}
              </Button>
            </Box>
          </Toolbar>
        </Container>
      </AppBar>

      <Box component="main" sx={{ flexGrow: 1 }}>
        {children}
      </Box>
    </Box>
  );
};


import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false, // Prevent jarring refetches
      staleTime: 1000 * 60 * 5, // Data is fresh for 5 minutes
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Router>
            <Layout>
              <Routes>
                <Route path="/" element={<Navigate to="/decks" replace />} />
                <Route path="/decks" element={<DeckList />} />
                <Route path="/decks/:deckId" element={<DeckBuilder />} />
                <Route path="/decks/new" element={<DeckBuilder />} />
              </Routes>
            </Layout>
          </Router>
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;
