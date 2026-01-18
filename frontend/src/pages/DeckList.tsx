import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Container, Grid, Typography, Button, Box, CircularProgress } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import LayersIcon from '@mui/icons-material/Layers';
import AutoStoriesIcon from '@mui/icons-material/AutoStories';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import { apiClient } from '../api/client';
import type { Deck } from '../types/mtg';
import { DeckListItem } from '../components/DeckListItem';

import { useQuery } from '@tanstack/react-query';

export const DeckList: React.FC = () => {
    const { data: decks = [], isLoading: loading } = useQuery({
        queryKey: ['decks'],
        queryFn: async () => {
            const res = await apiClient.get('/decks');
            return res.data;
        }
    });

    if (loading) {
        return (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', gap: 2 }}>
                <CircularProgress color="primary" />
                <Typography variant="body1" color="text.secondary">Fetching your collection...</Typography>
            </Box>
        );
    }

    return (
        <Container maxWidth="xl" sx={{ py: 6 }}>
            <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' }, gap: 4, mb: 6 }}>
                <Box>
                    <Typography variant="h3" component="h1" fontWeight="900" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <AutoStoriesIcon sx={{ fontSize: 40, color: 'primary.main' }} /> My Grimoire
                    </Typography>
                    <Typography variant="subtitle1" color="text.secondary" fontWeight="500">
                        Manage and refine your Magic: The Gathering decks.
                    </Typography>
                </Box>
                <Button
                    component={RouterLink}
                    to="/decks/new"
                    variant="contained"
                    size="large"
                    startIcon={<AddIcon />}
                    sx={{ borderRadius: 4, px: 4, py: 1.5, fontSize: '1rem', fontWeight: 800 }}
                >
                    New Deck
                </Button>
            </Box>

            {decks.length === 0 ? (
                <Box sx={{
                    border: '2px dashed',
                    borderColor: 'divider',
                    borderRadius: 8,
                    py: 12,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    textAlign: 'center',
                    bgcolor: 'background.paper'
                }}>
                    <Box sx={{ width: 80, height: 80, bgcolor: 'background.default', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 3 }}>
                        <LayersIcon sx={{ fontSize: 40, color: 'text.secondary' }} />
                    </Box>
                    <Typography variant="h4" fontWeight="800" gutterBottom>No decks found</Typography>
                    <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 300, mb: 4 }}>
                        Your collection is waiting to be built. Start your first journey today.
                    </Typography>
                    <Button
                        component={RouterLink}
                        to="/decks/new"
                        endIcon={<ChevronRightIcon />}
                        sx={{ fontWeight: 800 }}
                    >
                        Build one now
                    </Button>
                </Box>
            ) : (
                    <Grid container spacing={4}>
                    {decks.map((deck) => (
                        <Grid size={{ xs: 12, md: 6, lg: 4 }} key={deck.id}>
                            <DeckListItem deck={deck} />
                        </Grid>
                    ))}
                    </Grid>
            )}
        </Container>
    );
};
