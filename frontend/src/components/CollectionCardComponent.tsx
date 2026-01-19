import React from 'react';
import { Card, CardMedia, Box, Typography, IconButton, Button } from '@mui/material';
import RemoveIcon from '@mui/icons-material/Remove';
import AddIcon from '@mui/icons-material/Add';
import type { CollectionCard } from '../types/mtg';

interface CollectionCardProps {
    collectionCard: CollectionCard;
    onUpdateQuantity: (id: number, delta: number) => void; // Using numerical ID for collection items
    onRemove: (id: number) => void;
}

export const CollectionCardComponent = React.memo<CollectionCardProps>(({ collectionCard, onUpdateQuantity, onRemove }) => {
    return (
        <Box sx={{ position: 'relative', width: '100%', aspectRatio: '2.5/3.5' }}>
             {/* Quantity Badge */}
             <Box sx={{ 
                position: 'absolute', 
                top: -8, 
                right: -8, 
                width: 28, 
                height: 28, 
                bgcolor: 'background.paper', 
                border: 1, 
                borderColor: 'divider', 
                borderRadius: '50%', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                zIndex: 20, 
                boxShadow: 4,
                fontWeight: 900,
                fontSize: '0.75rem',
                transition: 'opacity 0.2s',
                opacity: 1,
                '.parent-card:hover &': { opacity: 0 }
            }}>
                x{collectionCard.quantity}
            </Box>

            <Card className="parent-card" sx={{ 
                width: '100%', 
                height: '100%',
                position: 'relative', 
                borderRadius: 0, 
                border: 1, 
                borderColor: 'divider',
                overflow: 'visible',
                '&:hover': { zIndex: 10 },
            }}>
                <Box sx={{ 
                    position: 'relative', 
                    width: '100%', 
                    height: '100%', 
                    borderRadius: 0, 
                    overflow: 'hidden',
                    transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    '&:hover': { transform: 'scale(1.05)', boxShadow: 12 }
                }}>
                    {collectionCard.card?.image_uris?.normal ? (
                        <CardMedia
                            component="img"
                            image={collectionCard.card.image_uris.normal}
                            alt={collectionCard.card.name}
                            loading="lazy"
                            sx={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        />
                    ) : (
                        <Box sx={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'background.paper', p: 2, textAlign: 'center' }}>
                            <Typography variant="body2" color="text.secondary" fontWeight="700">
                                {collectionCard.card?.name}
                            </Typography>
                        </Box>
                    )}

                    {/* Overlay */}
                    <Box sx={{
                        position: 'absolute',
                        inset: 0,
                        bgcolor: 'rgba(0,0,0,0.7)',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 1.5,
                        opacity: 0,
                        transition: 'opacity 0.2s',
                        '&:hover': { opacity: 1 }
                    }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <IconButton 
                                size="small" 
                                onClick={(e) => { e.stopPropagation(); onUpdateQuantity(collectionCard.id, -1); }}
                                sx={{ bgcolor: 'background.paper', '&:hover': { bgcolor: 'secondary.main', color: 'white' } }}
                            >
                                <RemoveIcon fontSize="small" />
                            </IconButton>
                            <Typography variant="h6" fontWeight="900" sx={{ minWidth: 24, textAlign: 'center' }}>
                                {collectionCard.quantity}
                            </Typography>
                            <IconButton 
                                size="small" 
                                onClick={(e) => { e.stopPropagation(); onUpdateQuantity(collectionCard.id, 1); }}
                                sx={{ bgcolor: 'background.paper', '&:hover': { bgcolor: '#10b981', color: 'white' } }}
                            >
                                <AddIcon fontSize="small" />
                            </IconButton>
                        </Box>
                        <Button
                            size="small"
                            variant="text"
                            color="secondary"
                            onClick={(e) => { e.stopPropagation(); onRemove(collectionCard.id); }}
                            sx={{ fontWeight: 800, letterSpacing: 1, fontSize: '0.65rem' }}
                        >
                            REMOVE
                        </Button>
                    </Box>
                </Box>
            </Card>
        </Box>
    );
});
