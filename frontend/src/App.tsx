import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DeckList } from './pages/DeckList';
import { DeckBuilder } from './pages/DeckBuilder';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, login } = useAuth();

  return (
    <div className="min-h-screen bg-[#f8fafc] font-sans text-gray-900 selection:bg-indigo-100 selection:text-indigo-900">
      <nav className="bg-white/80 backdrop-blur-xl border-b border-gray-100 px-8 py-5 flex justify-between items-center sticky top-0 z-50 shadow-sm">
        <Link to="/" className="text-2xl font-black text-gray-900 tracking-tighter flex items-center gap-2 group">
          <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center transform group-hover:rotate-12 transition-transform shadow-lg shadow-indigo-200">
            <div className="w-5 h-5 border-2 border-white rounded-sm transform rotate-45" />
          </div>
          MTG <span className="text-indigo-600">Builder</span>
        </Link>
        <div className="flex items-center gap-6">
          <Link to="/decks" className="font-bold text-gray-500 hover:text-indigo-600 transition-colors">My Decks</Link>
          <button
            onClick={() => login('mock-jwt-token')}
            className="bg-gray-900 text-white px-5 py-2.5 rounded-xl font-bold hover:bg-indigo-600 transition-all shadow-lg shadow-gray-200 flex items-center gap-2"
          >
            {user ? (
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 bg-indigo-500 rounded-full" />
                {user.name}
              </div>
            ) : 'Sign In'}
          </button>
        </div>
      </nav>
      <main className="">
        {children}
      </main>
    </div>
  );
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
            <Route path="/decks/new" element={<DeckBuilder />} />
          </Routes>
        </Layout>
      </Router>
    </AuthProvider>
  );
}

export default App;
