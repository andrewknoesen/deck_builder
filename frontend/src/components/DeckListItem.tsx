import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardActionArea, CardContent, Typography, Chip, Box, Stack } from '@mui/material';
import LayersIcon from '@mui/icons-material/Layers';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import type { Deck } from '../types/mtg';

interface DeckListItemProps {
    deck: Deck;
}

export const DeckListItem: React.FC<DeckListItemProps> = ({ deck }) => {
    const navigate = useNavigate();

    return (
        <Card variant="outlined" sx={{ '&:hover': { boxShadow: 8, borderColor: 'primary.main' }, transition: 'all 0.2s ease-in-out' }}>
            <CardActionArea onClick={() => navigate(`/decks/${deck.id}`)} sx={{ height: '100%', p: 1 }}>
                <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                         <Chip 
                            label={deck.format || 'Casual'} 
                            size="small" 
                            color="primary" 
                            sx={{ 
                                fontWeight: 800, 
                                borderRadius: 1, 
                                textTransform: 'uppercase', 
                                letterSpacing: '0.05em',
                                height: 20,
                                fontSize: '0.65rem'
                            }} 
                        />
                        <ChevronRightIcon color="primary" sx={{ opacity: 0, transition: '0.2s', '.MuiCardActionArea-root:hover &': { opacity: 1, transform: 'translateX(0)' }, transform: 'translateX(-5px)' }} />
                    </Box>

                    <Typography variant="h5" component="h3" fontWeight="800" gutterBottom sx={{ lineHeight: 1.2, mb: 3 }}>
                        {deck.title}
                    </Typography>

                    <Stack direction="row" spacing={2} color="text.secondary">
                        <Stack direction="row" spacing={0.5} alignItems="center">
                            <LayersIcon sx={{ fontSize: 16 }} />
                            <Typography variant="caption" fontWeight="700">{deck.cards?.length || 0} Cards</Typography>
                        </Stack>
                        <Stack direction="row" spacing={0.5} alignItems="center">
                            <AccessTimeIcon sx={{ fontSize: 16 }} />
                            <Typography variant="caption" fontWeight="700">Modified Recently</Typography>
                        </Stack>
                    </Stack>
                </CardContent>
            </CardActionArea>
        </Card>
    );
};
