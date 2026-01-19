import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { DeckList } from "./pages/DeckList";
import { DeckBuilder } from "./pages/DeckBuilder";
import { LandingPage } from "./pages/LandingPage";
import { Collection } from "./pages/Collection";
import { ThemeProvider, CssBaseline } from "@mui/material";
import { theme } from "./theme";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MainLayout } from "./components/Layout/MainLayout";

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
            <MainLayout>
              <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/collection" element={<Collection />} />
                <Route path="/decks" element={<DeckList />} />
                <Route path="/decks/:deckId" element={<DeckBuilder />} />
                <Route path="/decks/new" element={<DeckBuilder />} />
              </Routes>
            </MainLayout>
          </Router>
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;
