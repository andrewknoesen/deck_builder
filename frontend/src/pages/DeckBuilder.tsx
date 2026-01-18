import React, { useState, useEffect, useCallback } from 'react';
import { Search, Plus, Minus, Trash2, Save, ArrowLeft, Loader2, Sparkles } from 'lucide-react';
import { apiClient } from '../api/client';
import { useParams, useNavigate, Link } from 'react-router-dom';
import type { ScryfallCard, Deck, DeckCard } from '../types/mtg';
import { useAuth } from '../context/AuthContext';

export const DeckBuilder: React.FC = () => {
    const { deckId } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();

    const [title, setTitle] = useState('New Deck');
    const [deckCards, setDeckCards] = useState<DeckCard[]>([]);
    const [query, setQuery] = useState('');
    const [searchResults, setSearchResults] = useState<ScryfallCard[]>([]);
    const [searching, setSearching] = useState(false);
    const [saving, setSaving] = useState(false);
    const [loading, setLoading] = useState(false);

    const isNew = !deckId || deckId === 'new';

    const fetchDeck = useCallback(async () => {
        if (isNew) return;
        setLoading(true);
        try {
            const res = await apiClient.get(`/decks/${deckId}`);
            const deck: Deck = res.data;
            setTitle(deck.title);
            setDeckCards(deck.cards || []);
        } catch (err) {
            console.error("Failed to fetch deck", err);
        } finally {
            setLoading(false);
        }
    }, [deckId, isNew]);

    useEffect(() => {
        fetchDeck();
    }, [fetchDeck]);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query) return;
        setSearching(true);
        try {
            const res = await apiClient.get(`/cards/search`, { params: { q: query } });
            setSearchResults(res.data.data || []);
        } catch (err) {
            console.error("Search failed", err);
        } finally {
            setSearching(false);
        }
    };

    const addCard = (card: ScryfallCard) => {
        setDeckCards(prev => {
            const existing = prev.find(dc => dc.card_id === card.id);
            if (existing) {
                return prev.map(dc => dc.card_id === card.id
                    ? { ...dc, quantity: dc.quantity + 1 }
                    : dc
                );
            }
            return [...prev, { card_id: card.id, quantity: 1, board: 'main', card }];
        });
    };

    const updateQuantity = (cardId: string, delta: number) => {
        setDeckCards(prev => prev.map(dc => {
            if (dc.card_id === cardId) {
                const newQty = Math.max(0, dc.quantity + delta);
                return { ...dc, quantity: newQty };
            }
            return dc;
        }).filter(dc => dc.quantity > 0));
    };

    const removeCard = (cardId: string) => {
        setDeckCards(prev => prev.filter(dc => dc.card_id !== cardId));
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const deckData = {
                title,
                user_id: user?.id || 1, // Fallback for POC
                cards: deckCards.map(({ card_id, quantity, board }) => ({ card_id, quantity, board }))
            };

            if (isNew) {
                const res = await apiClient.post('/decks/', deckData);
                navigate(`/decks/${res.data.id}`, { replace: true });
            } else {
                await apiClient.put(`/decks/${deckId}`, deckData);
            }
        } catch (err) {
            console.error("Save failed", err);
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-[calc(100vh-64px)] space-y-4">
                <Loader2 className="w-12 h-12 text-indigo-600 animate-spin" />
                <p className="text-gray-500 font-medium">Loading your deck...</p>
            </div>
        );
    }

    return (
        <div className="flex h-[calc(100vh-64px)] bg-[#f8fafc]">
            {/* Left Column: Deck Inventory */}
            <div className="w-1/3 border-r bg-white shadow-sm flex flex-col">
                <div className="p-6 border-b flex justify-between items-center bg-white/80 backdrop-blur-md sticky top-0 z-10">
                    <div className="flex items-center gap-3">
                        <Link to="/decks" className="p-2 hover:bg-gray-100 rounded-lg transition">
                            <ArrowLeft className="w-5 h-5 text-gray-600" />
                        </Link>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="text-xl font-bold bg-transparent border-b border-transparent hover:border-gray-300 focus:border-indigo-500 focus:outline-none transition-colors px-1"
                            placeholder="Deck Title"
                        />
                    </div>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="bg-indigo-600 text-white px-4 py-2 rounded-xl font-semibold flex items-center gap-2 hover:bg-indigo-700 disabled:opacity-50 transition-all shadow-lg shadow-indigo-200"
                    >
                        {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                        Save
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
                    {deckCards.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-center space-y-4 px-8">
                            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center">
                                <Plus className="w-8 h-8 text-gray-400" />
                            </div>
                            <p className="text-gray-500">Your deck is empty. Search and add cards from the right pane!</p>
                        </div>
                    ) : (
                        deckCards.map((dc) => (
                            <div key={dc.card_id} className="group flex items-center gap-3 p-3 bg-white border rounded-2xl hover:border-indigo-200 hover:shadow-md transition-all">
                                <div className="w-12 h-16 bg-gray-100 rounded-lg overflow-hidden shrink-0 shadow-sm">
                                    {dc.card?.image_uris?.small && (
                                        <img src={dc.card.image_uris.small} alt={dc.card.name} className="w-full h-full object-cover" />
                                    )}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <h4 className="font-semibold text-gray-900 truncate">{dc.card?.name}</h4>
                                    <p className="text-xs text-gray-500 uppercase tracking-wider font-bold">{dc.board}</p>
                                </div>
                                <div className="flex items-center bg-gray-50 rounded-xl p-1 border">
                                    <button onClick={() => updateQuantity(dc.card_id, -1)} className="p-1 hover:text-indigo-600 transition">
                                        <Minus className="w-4 h-4" />
                                    </button>
                                    <span className="w-8 text-center font-bold text-gray-700">{dc.quantity}</span>
                                    <button onClick={() => updateQuantity(dc.card_id, 1)} className="p-1 hover:text-indigo-600 transition">
                                        <Plus className="w-4 h-4" />
                                    </button>
                                </div>
                                <button onClick={() => removeCard(dc.card_id)} className="p-2 text-gray-400 hover:text-red-500 transition opacity-0 group-hover:opacity-100">
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        ))
                    )}
                </div>

                <div className="p-6 border-t bg-gray-50/50">
                    <div className="flex justify-between items-center">
                        <span className="text-gray-500 font-medium">Total Cards</span>
                        <span className="text-2xl font-black text-gray-900">
                            {deckCards.reduce((acc, curr) => acc + curr.quantity, 0)}
                        </span>
                    </div>
                </div>
            </div>

            {/* Right Column: Search & Discovery */}
            <div className="flex-1 flex flex-col overflow-hidden">
                <div className="p-8 bg-white/40 backdrop-blur-xl border-b z-10 sticky top-0">
                    <div className="max-w-3xl mx-auto flex flex-col space-y-6">
                        <div className="flex items-center justify-between">
                            <h2 className="text-3xl font-black text-gray-900 tracking-tight flex items-center gap-3">
                                Card Discovery <Sparkles className="w-6 h-6 text-amber-400 fill-amber-400" />
                            </h2>
                        </div>

                        <form onSubmit={handleSearch} className="relative group">
                            <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                                <Search className="w-6 h-6 text-gray-400 group-focus-within:text-indigo-500 transition-colors" />
                            </div>
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Find your next card (name, type, or color)..."
                                className="w-full bg-white border-2 border-gray-100 hover:border-indigo-100 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 focus:outline-none rounded-2xl py-5 pl-14 pr-32 text-lg font-medium transition-all shadow-sm"
                            />
                            <button
                                type="submit"
                                disabled={searching}
                                className="absolute right-3 top-2.5 bottom-2.5 bg-gray-900 text-white px-6 rounded-xl font-bold flex items-center gap-2 hover:bg-indigo-600 transition-all disabled:opacity-50"
                            >
                                {searching ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Search'}
                            </button>
                        </form>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                    {searching ? (
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-8 animate-pulse text-transparent select-none">
                            {[...Array(10)].map((_, i) => (
                                <div key={i} className="aspect-[2.5/3.5] bg-gray-200 rounded-3xl" />
                            ))}
                        </div>
                    ) : (
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-x-8 gap-y-12">
                            {searchResults.map((card) => (
                                <div
                                    key={card.id}
                                    className="group relative flex flex-col space-y-4 cursor-pointer"
                                    onClick={() => addCard(card)}
                                >
                                    <div className="relative aspect-[2.5/3.5] rounded-[1.5rem] overflow-hidden shadow-xl group-hover:shadow-2xl group-hover:-translate-y-2 transition-all duration-300">
                                        {card.image_uris?.normal ? (
                                            <img src={card.image_uris.normal} alt={card.name} className="w-full h-full object-cover" />
                                        ) : (
                                            <div className="w-full h-full bg-gradient-to-br from-gray-100 to-gray-200 flex flex-col items-center justify-center p-6 text-center">
                                                <div className="text-gray-400 font-black mb-2 uppercase tracking-tighter">No Preview</div>
                                                <div className="text-gray-600 font-bold text-sm tracking-tight">{card.name}</div>
                                            </div>
                                        )}
                                        <div className="absolute inset-0 bg-indigo-600/0 group-hover:bg-indigo-600/10 transition-colors" />
                                        <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-all transform scale-90 group-hover:scale-100">
                                            <div className="bg-white text-indigo-600 p-3 rounded-2xl shadow-xl">
                                                <Plus className="w-6 h-6 stroke-[3]" />
                                            </div>
                                        </div>
                                    </div>
                                    <div className="px-1">
                                        <h4 className="font-black text-gray-900 leading-tight group-hover:text-indigo-600 transition-colors truncate">{card.name}</h4>
                                        <p className="text-sm font-bold text-gray-500 tracking-wide uppercase mt-1">
                                            {card.type_line?.split(' — ')[0].split(' ').pop()}
                                        </p>
                                    </div>
                                </div>
                            ))}

                            {searchResults.length === 0 && !searching && (
                                <div className="col-span-full py-32 flex flex-col items-center justify-center text-center opacity-40">
                                    <Search className="w-24 h-24 mb-6 stroke-[0.5]" />
                                    <p className="text-2xl font-medium tracking-tight">Try searching for your favorite cards!</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
