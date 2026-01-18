import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Book } from 'lucide-react';
import { apiClient } from '../api/client';

export const DeckList: React.FC = () => {
    const [decks, setDecks] = useState<any[]>([]);
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

    if (loading) return <div>Loading decks...</div>;

    return (
        <div className="p-4">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold flex items-center gap-2">
                    <Book className="w-6 h-6" /> My Decks
                </h1>
                <Link to="/decks/new" className="bg-blue-600 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-blue-700">
                    <Plus className="w-4 h-4" /> New Deck
                </Link>
            </div>

            {decks.length === 0 ? (
                <p className="text-gray-500">No decks found. Create one to get started!</p>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {decks.map((deck) => (
                        <Link key={deck.id} to={`/decks/${deck.id}`} className="border p-4 rounded hover:shadow-lg transition block">
                            <h3 className="font-semibold text-lg">{deck.name}</h3>
                            <p className="text-gray-600">{deck.format}</p>
                            <div className="mt-2 text-sm text-gray-500">
                                {/* deck.card_count */} Cards
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
};
