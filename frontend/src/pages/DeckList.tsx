import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Book, Clock, Layers, ChevronRight, Loader2 } from 'lucide-react';
import { apiClient } from '../api/client';
import type { Deck } from '../types/mtg';

export const DeckList: React.FC = () => {
    const [decks, setDecks] = useState<Deck[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDecks = async () => {
            try {
                const res = await apiClient.get('/decks');
                setDecks(res.data);
            } catch (err) {
                console.error("Failed to fetch decks", err);
            } finally {
                setLoading(false);
            }
        };
        fetchDecks();
    }, []);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
                <Loader2 className="w-10 h-10 text-indigo-600 animate-spin" />
                <p className="text-gray-500 font-medium">Fetching your collection...</p>
            </div>
        );
    }

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-10">
                <div>
                    <h1 className="text-4xl font-black text-gray-900 tracking-tight flex items-center gap-3">
                        <Book className="w-10 h-10 text-indigo-600" /> My Grimoire
                    </h1>
                    <p className="text-gray-500 mt-2 font-medium">Manage and refine your Magic: The Gathering decks.</p>
                </div>
                <Link to="/decks/new" className="bg-gray-900 text-white px-6 py-3 rounded-2xl font-bold flex items-center gap-2 hover:bg-indigo-600 transition-all shadow-xl shadow-gray-200 group">
                    <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform" /> New Deck
                </Link>
            </div>

            {decks.length === 0 ? (
                <div className="bg-white border-2 border-dashed border-gray-200 rounded-[2rem] py-24 flex flex-col items-center justify-center text-center px-6">
                    <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mb-6">
                        <Layers className="w-10 h-10 text-gray-300" />
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">No decks found</h3>
                    <p className="text-gray-500 max-w-xs mb-8 font-medium">Your collection is waiting to be built. Start your first journey today.</p>
                    <Link to="/decks/new" className="text-indigo-600 font-bold flex items-center gap-1 hover:gap-2 transition-all">
                        Build one now <ChevronRight className="w-5 h-5" />
                    </Link>
                </div>
            ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {decks.map((deck) => (
                        <Link
                            key={deck.id}
                            to={`/decks/${deck.id}`}
                            className="group bg-white border border-gray-100 p-8 rounded-[2rem] hover:border-indigo-500 hover:shadow-2xl hover:shadow-indigo-100 transition-all block relative overflow-hidden"
                        >
                            <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-100 transition-opacity">
                                <ChevronRight className="w-6 h-6 text-indigo-600" />
                            </div>

                            <div className="flex flex-col h-full">
                                <div className="mb-6">
                                    <div className="inline-block px-3 py-1 bg-indigo-50 text-indigo-600 text-[10px] font-black uppercase tracking-widest rounded-full mb-3">
                                        {deck.format || 'Casual'}
                                    </div>
                                    <h3 className="font-black text-2xl text-gray-900 leading-tight group-hover:text-indigo-600 transition-colors">
                                        {deck.title}
                                    </h3>
                                </div>

                                <div className="mt-auto flex items-center gap-6 text-gray-400 font-bold text-sm">
                                    <div className="flex items-center gap-1.5">
                                        <Layers className="w-4 h-4" />
                                        <span>{deck.cards?.length || 0} Cards</span>
                                    </div>
                                    <div className="flex items-center gap-1.5">
                                        <Clock className="w-4 h-4" />
                                        <span>Modified Recently</span>
                                    </div>
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
};
