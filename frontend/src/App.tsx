import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DeckList } from './pages/DeckList';
import { DeckBuilder } from './pages/DeckBuilder';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, login } = useAuth();

  return (
    <div className="min-h-screen bg-gray-100 font-sans text-gray-900">
      <nav className="bg-white border-b px-4 py-3 flex justify-between items-center">
        <Link to="/" className="text-xl font-bold text-indigo-600">MTG Builder</Link>
        <div>
          {/* Placeholder Login Button */}
          <button onClick={() => login('mock-jwt-token')} className="text-sm bg-indigo-100 text-indigo-700 px-3 py-1 rounded hover:bg-indigo-200">
            {user ? user.name : 'Sign In (Mock)'}
          </button>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto">
        {children}
      </main>
    </div>
  );
};

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  // For dev, allow everything or mock login
  return <>{children}</>;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/decks" replace />} />
            <Route path="/decks" element={<DeckList />} />
            <Route path="/decks/:deckId" element={<DeckBuilder />} />
            <Route path="/decks/new" element={<div>Create Deck Placeholder</div>} />
          </Routes>
        </Layout>
      </Router>
    </AuthProvider>
  );
}

export default App;
