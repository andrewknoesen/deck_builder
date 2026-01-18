import React, { useState } from 'react';
import { Search, Plus } from 'lucide-react';
import { apiClient } from '../api/client';
import { useParams } from 'react-router-dom';

export const DeckBuilder: React.FC = () => {
    const { deckId } = useParams();
    const [query, setQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [searching, setSearching] = useState(false);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query) return;
        setSearching(true);
        try {
            const res = await apiClient.get(`/cards/search`, { params: { q: query } });
            setSearchResults(res.data.data || []); // Assuming Scryfall shape or our proxy shape
        } catch (err) {
            console.error("Search failed", err);
        } finally {
            setSearching(false);
        }
    };

    return (
        <div className="flex h-[calc(100vh-64px)]">
            {/* Left: Deck Pane */}
            <div className="w-1/3 border-r p-4 overflow-y-auto">
                <h2 className="text-xl font-bold mb-4">Deck {deckId}</h2>
                <p className="text-gray-500">Deck cards will appear here.</p>

                {/* Placeholder for card list */}
            </div>

            {/* Right: Search Pane */}
            <div className="w-2/3 p-4 overflow-y-auto bg-gray-50">
                <form onSubmit={handleSearch} className="flex gap-2 mb-4">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search cards..."
                        className="flex-1 border p-2 rounded"
                    />
                    <button type="submit" disabled={searching} className="bg-gray-800 text-white p-2 rounded flex items-center">
                        <Search className="w-4 h-4" />
                    </button>
                </form>

                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {searchResults.map((card) => (
                        <div key={card.id} className="border rounded bg-white p-2 flex flex-col items-center">
                            {card.image_uris?.normal ? (
                                <img src={card.image_uris.normal} alt={card.name} className="w-full rounded mb-2" />
                            ) : (
                                <div className="w-full h-40 bg-gray-200 flex items-center justify-center text-xs">No Image</div>
                            )}
                            <h4 className="font-bold text-sm text-center">{card.name}</h4>
                            <button className="mt-2 bg-green-600 text-white text-xs px-2 py-1 rounded flex items-center gap-1 hover:bg-green-700">
                                <Plus className="w-3 h-3" /> Add
                            </button>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
