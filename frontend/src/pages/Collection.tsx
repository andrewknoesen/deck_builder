import React, { useState, useMemo } from 'react';
import "../styles/Collection.css";
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    Box,
    Typography,
    Grid,
    CircularProgress,
    Divider,
    Paper,
    Stack,
    Snackbar,
    Alert,
    Card,
    CardMedia
} from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import CollectionsIcon from '@mui/icons-material/Collections';
import { apiClient } from '../api/client';
import type { ScryfallCard, CollectionCard } from '../types/mtg';
import { DeckBuilderSearch } from '../components/DeckBuilderSearch';
import { CollectionCardComponent } from '../components/CollectionCardComponent';
import { useCardHover } from "../context/CardHoverContext";

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
    const { hoveredCard } = useCardHover();
    const [toast, setToast] = useState<{ open: boolean, message: string, severity: 'success' | 'error' }>({ open: false, message: '', severity: 'success' });
    const [searchKey, setSearchKey] = useState(0); // Force remount of search component to clear input

    // Fetch Collection
    const { data: collection = [], isLoading: collectionLoading } = useQuery<CollectionCard[]>({
        queryKey: ['collection'],
        queryFn: async () => {
            const res = await apiClient.get('/collection');
            return res.data;
        }
    });

    const handleAddCard = (card: ScryfallCard) => {
        addMutation.mutate(card);
        setSearchKey(prev => prev + 1); // Force remount to clear
    };

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



// ... imports remain the same ...

    return (
        <Box className="collection-container">
            {/* Left Pane: Collection Inventory */}
            <Paper
                square
                elevation={0}
                className="collection-pane-left"
            >
                {/* Header */}
                <Box className="collection-header">
                    <Box className="collection-title">
                        <Typography variant="h5" fontWeight="900" sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <CollectionsIcon /> My Collection
                        </Typography>
                        <Box className="collection-count-badge">
                            {totalCards} Cards
                        </Box>
                    </Box>
                    
                    <Box className="collection-search-box">
                        <DeckBuilderSearch key={searchKey} onAddCard={handleAddCard} />
                    </Box>
                </Box>

                {/* Collection Content */}
                <Box className="collection-content">
                    {collectionLoading ? (
                         <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
                            <CircularProgress />
                        </Box>
                    ) : collection.length === 0 ? (
                        <Box className="collection-empty">
                            <Box className="collection-empty-icon">
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
                                    <Box className="collection-group-header">
                                        <Typography variant="subtitle2" fontWeight="900" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: 1 }}>
                                            {type}
                                        </Typography>
                                        <Box className="collection-group-count">
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

            {/* Right Pane: Stats / Overlay */}
            {/* Right Pane: Stats / Overlay */}
            <Box className="collection-pane-right">
                <Box className={`collection-right-content ${hoveredCard ? "blurred" : ""}`}>
                     {/* Default Content when no hover - Placeholder */}
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', opacity: 0.3, textAlign: 'center', gap: 2 }}>
                        <AutoAwesomeIcon sx={{ fontSize: 60 }} />
                        <Typography variant="h6" fontWeight="700">Hover over a card to view details</Typography>
                        <Typography variant="body2">Or search for cards above to add them.</Typography>
                    </Box>
                </Box>

                 {/* Hover Overlay */}
                {hoveredCard && (
                    <Box className="collection-overlay">
                        <Card className="collection-overlay-card">
                            {hoveredCard.image_uris?.normal ? (
                                <CardMedia
                                    component="img"
                                    image={hoveredCard.image_uris.normal}
                                    alt={hoveredCard.name}
                                    sx={{ width: "100%", height: "100%", objectFit: "cover" }}
                                />
                            ) : (
                                <Box
                                    sx={{
                                        width: "100%",
                                        height: "100%",
                                        bgcolor: "background.paper",
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        p: 4,
                                        textAlign: "center",
                                    }}
                                >
                                    <Typography variant="h5" fontWeight="700">
                                        {hoveredCard.name}
                                    </Typography>
                                </Box>
                            )}
                        </Card>

                        {/* Info Panel */}
                        <Paper className="collection-overlay-info">
                            <Box
                                sx={{
                                    display: "flex",
                                    justifyContent: "space-between",
                                    alignItems: "flex-start",
                                    mb: 1,
                                    flexShrink: 0,
                                }}
                            >
                                <Typography variant="h6" fontWeight="900" lineHeight={1.1}>
                                    {hoveredCard.name}
                                </Typography>
                                <Typography
                                    variant="subtitle2"
                                    sx={{
                                        bgcolor: "action.hover",
                                        px: 1,
                                        py: 0.5,
                                        borderRadius: 1,
                                        fontFamily: "monospace",
                                        flexShrink: 0,
                                    }}
                                >
                                    {hoveredCard.mana_cost}
                                </Typography>
                            </Box>
                            <Typography
                                variant="subtitle2"
                                color="primary.main"
                                fontWeight="700"
                                gutterBottom
                                sx={{ flexShrink: 0 }}
                            >
                                {hoveredCard.type_line}
                            </Typography>
                            <Divider sx={{ my: 1.5, flexShrink: 0 }} />
                            <Typography
                                variant="body2"
                                sx={{
                                    whiteSpace: "pre-wrap",
                                    lineHeight: 1.6,
                                    color: "text.primary",
                                }}
                            >
                                {hoveredCard.oracle_text}
                            </Typography>
                        </Paper>
                    </Box>
                )}
            </Box>

             <Snackbar open={toast.open} autoHideDuration={4000} onClose={handleCloseToast}>
                <Alert onClose={handleCloseToast} severity={toast.severity} sx={{ width: '100%' }}>
                    {toast.message}
                </Alert>
            </Snackbar>
        </Box>
    );
};
