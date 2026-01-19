import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    Box,
    TextField,
    Typography,
    Button,
    Grid,
    CircularProgress,
    InputAdornment,
    Divider,
    Paper,
    Stack,
    Snackbar,
    Alert
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import CollectionsIcon from '@mui/icons-material/Collections';
import { apiClient } from '../api/client';
import type { ScryfallCard, CollectionCard } from '../types/mtg';
import { SearchCard } from '../components/SearchCard';
import { CollectionCardComponent } from '../components/CollectionCardComponent';

// Helper to determine primary type for grouping (reused logic)
const getCardType = (typeLine?: string): string => {
    if (!typeLine) return 'Unknown';
    const lower = typeLine.toLowerCase();
    if (lower.includes('creature')) return 'Creatures';
    if (lower.includes('planeswalker')) return 'Planeswalkers';
    if (lower.includes('instant')) return 'Instants';
    if (lower.includes('sorcery')) return 'Sorceries';
    if (lower.includes('artifact')) return 'Artifacts';
    if (lower.includes('enchantment')) return 'Enchantments';
    if (lower.includes('land')) return 'Lands';
    return 'Other';
};

const TYPE_ORDER = ['Creatures', 'Planeswalkers', 'Instants', 'Sorceries', 'Artifacts', 'Enchantments', 'Lands', 'Other', 'Unknown'];

export const Collection: React.FC = () => {
    const queryClient = useQueryClient();
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<ScryfallCard[]>([]);
    const [searchLoading, setSearchLoading] = useState(false);
    const [toast, setToast] = useState<{ open: boolean, message: string, severity: 'success' | 'error' }>({ open: false, message: '', severity: 'success' });

    // Fetch Collection
    const { data: collection = [], isLoading: collectionLoading } = useQuery<CollectionCard[]>({
        queryKey: ['collection'],
        queryFn: async () => {
            const res = await apiClient.get('/collection');
            return res.data;
        }
    });

    // Mutations
    const addMutation = useMutation({
        mutationFn: async (card: ScryfallCard) => {
            await apiClient.post('/collection', { card_id: card.id, quantity: 1 });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['collection'] });
            setToast({ open: true, message: 'Card added to collection', severity: 'success' });
        },
        onError: () => {
            setToast({ open: true, message: 'Failed to add card', severity: 'error' });
        }
    });

    const updateQuantityMutation = useMutation({
        mutationFn: async ({ id, delta }: { id: number, delta: number }) => {
            // Find current quantity to calculate new one
            const item = collection.find(c => c.id === id);
            if (!item) return;
            const newQuantity = item.quantity + delta;
            await apiClient.patch(`/collection/${id}`, { quantity: newQuantity });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['collection'] });
        },
        onError: () => {
            setToast({ open: true, message: 'Failed to update quantity', severity: 'error' });
        }
    });

    const removeMutation = useMutation({
        mutationFn: async (id: number) => {
            await apiClient.delete(`/collection/${id}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['collection'] });
            setToast({ open: true, message: 'Card removed from collection', severity: 'success' });
        },
        onError: () => {
            setToast({ open: true, message: 'Failed to remove card', severity: 'error' });
        }
    });

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!searchQuery.trim()) return;
        setSearchLoading(true);
        try {
            const res = await apiClient.get('/cards/search', { params: { q: searchQuery } });
            setSearchResults(res.data.data || []);
        } catch (error) {
            console.error("Search failed", error);
            setSearchResults([]);
        } finally {
            setSearchLoading(false);
        }
    };

    const handleCloseToast = () => setToast({ ...toast, open: false });

    // Grouping Logic
    const groupedCards = useMemo(() => {
        const groups: Record<string, CollectionCard[]> = {};
        collection.forEach(item => {
            const type = getCardType(item.card?.type_line);
            if (!groups[type]) groups[type] = [];
            groups[type].push(item);
        });
        return groups;
    }, [collection]);

    const sortedGroups = useMemo(() => {
        return Object.keys(groupedCards).sort((a, b) => TYPE_ORDER.indexOf(a) - TYPE_ORDER.indexOf(b));
    }, [groupedCards]);

    const totalCards = collection.reduce((acc, curr) => acc + curr.quantity, 0);

    return (
        <Box sx={{ display: 'flex', height: 'calc(100vh - 64px)', overflow: 'hidden' }}>
            {/* Left Pane: Collection Inventory */}
            <Paper
                square
                elevation={0}
                sx={{
                    width: '45%',
                    borderRight: 1,
                    borderColor: 'divider',
                    display: 'flex',
                    flexDirection: 'column',
                    bgcolor: 'background.paper',
                    zIndex: 10
                }}
            >
                {/* Header */}
                <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider', bgcolor: 'rgba(15, 23, 42, 0.8)', backdropFilter: 'blur(12px)', position: 'sticky', top: 0, zIndex: 20 }}>
                     <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="h5" fontWeight="900" sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <CollectionsIcon /> My Collection
                        </Typography>
                        <Box sx={{ px: 2, py: 0.5, bgcolor: 'primary.main', color: 'primary.contrastText', borderRadius: 4, fontWeight: 'bold' }}>
                             {totalCards} Cards
                        </Box>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                        Manage your card inventory.
                    </Typography>
                </Box>

                {/* Collection Content */}
                <Box sx={{ flex: 1, overflowY: 'auto', p: 3, pb: 10 }}>
                    {collectionLoading ? (
                         <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
                            <CircularProgress />
                        </Box>
                    ) : collection.length === 0 ? (
                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', opacity: 0.5, textAlign: 'center', gap: 2 }}>
                            <Box sx={{ width: 80, height: 80, borderRadius: '50%', bgcolor: 'action.hover', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <CollectionsIcon sx={{ fontSize: 40, color: 'text.secondary' }} />
                            </Box>
                            <Box>
                                <Typography variant="h5" fontWeight="800" color="text.primary">Empty Collection</Typography>
                                <Typography variant="body2" color="text.secondary">Search for cards on the right to add them.</Typography>
                            </Box>
                        </Box>
                    ) : (
                        <Stack spacing={4}>
                            {sortedGroups.map(type => (
                                <Box key={type}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                                        <Typography variant="subtitle2" fontWeight="900" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: 1 }}>
                                            {type}
                                        </Typography>
                                        <Box sx={{ px: 1, py: 0.5, bgcolor: 'action.selected', borderRadius: 1, fontSize: '0.7rem', fontWeight: 700, color: 'text.primary' }}>
                                            {groupedCards[type].reduce((a, c) => a + c.quantity, 0)}
                                        </Box>
                                        <Divider sx={{ flex: 1 }} />
                                    </Box>
                                    <Grid container spacing={2}>
                                        {groupedCards[type].map(item => (
                                            <Grid size={{ xs: 3, lg: 2 }} key={item.id}>
                                                <CollectionCardComponent
                                                    collectionCard={item}
                                                    onUpdateQuantity={(id, delta) => updateQuantityMutation.mutate({ id, delta })}
                                                    onRemove={(id) => removeMutation.mutate(id)}
                                                />
                                            </Grid>
                                        ))}
                                    </Grid>
                                </Box>
                            ))}
                        </Stack>
                    )}
                </Box>
            </Paper>

            {/* Right Pane: Card Database Search */}
            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', bgcolor: 'background.default' }}>
                <Box sx={{ p: 4, zIndex: 10, bgcolor: 'background.default', borderBottom: 1, borderColor: 'divider' }}>
                    <Typography variant="h4" fontWeight="900" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        Card Database <AutoAwesomeIcon sx={{ color: 'warning.main', fontSize: 28 }} />
                    </Typography>

                    <Box component="form" onSubmit={handleSearch} sx={{ position: 'relative', mt: 3 }}>
                        <TextField
                            fullWidth
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search cards..."
                            InputProps={{
                                startAdornment: (
                                    <InputAdornment position="start">
                                        <SearchIcon color="action" />
                                    </InputAdornment>
                                ),
                                endAdornment: (
                                    <InputAdornment position="end">
                                        <Button
                                            type="submit" 
                                            variant="contained" 
                                            disabled={searchLoading} 
                                            sx={{ minWidth: 80, borderRadius: 2 }}
                                        >
                                            {searchLoading ? <CircularProgress size={20} color="inherit" /> : 'Find'}
                                        </Button>
                                    </InputAdornment>
                                ),
                                sx: {
                                    borderRadius: 4,
                                    bgcolor: 'background.paper',
                                    boxShadow: 2,
                                    pl: 2,
                                    pr: 1,
                                    py: 1,
                                    '& fieldset': { border: 'none' }
                                }
                            }}
                        />
                    </Box>
                </Box>

                <Box sx={{ flex: 1, overflowY: 'auto', p: 4 }}>
                    {searchLoading ? (
                         <Grid container spacing={2}>
                            {[...Array(10)].map((_, i) => (
                                <Grid size={{ xs: 4, sm: 3, md: 2 }} key={i}>
                                    <Box sx={{ aspectRatio: '2.5/3.5', bgcolor: 'action.hover', borderRadius: 3, animation: 'pulse 1.5s infinite opacity' }} />
                                </Grid>
                            ))}
                        </Grid>
                    ) : (
                        <Grid container spacing={3}>
                            {searchResults.map((card) => (
                                <Grid size={{ xs: 4, sm: 3, md: 2 }} key={card.id}>
                                    <SearchCard card={card} onAdd={() => addMutation.mutate(card)} />
                                </Grid>
                            ))}
                             {searchResults.length === 0 && !searchLoading && searchQuery && (
                                <Box sx={{ gridColumn: '1 / -1', py: 10, display: 'flex', flexDirection: 'column', alignItems: 'center', opacity: 0.5, gap: 2 }}>
                                    <Typography variant="h6" color="text.secondary">No results found</Typography>
                                </Box>
                             )}
                              {searchResults.length === 0 && !searchLoading && !searchQuery && (
                                <Box sx={{ gridColumn: '1 / -1', py: 10, display: 'flex', flexDirection: 'column', alignItems: 'center', opacity: 0.3, gap: 2 }}>
                                    <AutoAwesomeIcon sx={{ fontSize: 60 }} />
                                    <Typography variant="h5" fontWeight="700">Search the multiverse</Typography>
                                </Box>
                             )}
                        </Grid>
                    )}
                </Box>
            </Box>

             <Snackbar open={toast.open} autoHideDuration={4000} onClose={handleCloseToast}>
                <Alert onClose={handleCloseToast} severity={toast.severity} sx={{ width: '100%' }}>
                    {toast.message}
                </Alert>
            </Snackbar>
        </Box>
    );
};
