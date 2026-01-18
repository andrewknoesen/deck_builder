import React from 'react';
import { Card, CardMedia, Box, Typography } from '@mui/material';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import type { ScryfallCard } from '../types/mtg';

interface SearchCardProps {
    card: ScryfallCard;
    onAdd: (card: ScryfallCard) => void;
}

export const SearchCard: React.FC<SearchCardProps> = ({ card, onAdd }) => {
    return (
        <Card sx={{ 
            height: '100%', 
            display: 'flex', 
            flexDirection: 'column', 
            borderRadius: 0, 
            bgcolor: 'transparent',
            boxShadow: 'none',
            '&:hover': { 
                '& .image-wrapper': { transform: 'translateY(-8px)', boxShadow: 12 },
                '& .card-name': { color: 'primary.main' }
            }
        }}>
            <Box 
                className="image-wrapper"
                sx={{ 
                    position: 'relative', 
                    borderRadius: 3, 
                    overflow: 'hidden', 
                    aspectRatio: '2.5/3.5', 
                    boxShadow: 4, 
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    mb: 1.5,
                    cursor: 'pointer',
                    bgcolor: 'background.paper'
                }}
                onClick={() => onAdd(card)}
            >
                 {card.image_uris?.normal ? (
                    <CardMedia
                        component="img"
                        image={card.image_uris.normal}
                        alt={card.name}
                        sx={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                ) : (
                    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 2, textAlign: 'center' }}>
                         <Typography variant="caption" color="text.secondary" fontWeight="900" textTransform="uppercase" letterSpacing={1} mb={1}>No Image</Typography>
                         <Typography variant="body2" color="text.secondary" fontWeight="700">{card.name}</Typography>
                    </Box>
                )}
                
                {/* Hover Add Overlay */}
                 <Box sx={{
                    position: 'absolute',
                    inset: 0,
                    bgcolor: 'rgba(99, 102, 241, 0.4)', // Indigo overlay
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    opacity: 0,
                    transition: 'opacity 0.2s',
                    '&:hover': { opacity: 1 }
                }}>
                    <Box sx={{ 
                        bgcolor: 'background.paper', 
                        borderRadius: '50%', 
                        p: 1, 
                        display: 'flex', 
                        boxShadow: 4 
                    }}>
                        <AddCircleIcon color="primary" sx={{ fontSize: 32 }} />
                    </Box>
                </Box>
            </Box>

            <Box sx={{ px: 0.5 }}>
                 <Typography 
                    className="card-name"
                    variant="subtitle2" 
                    fontWeight="700" 
                    noWrap 
                    sx={{ transition: 'color 0.2s' }}
                >
                    {card.name}
                </Typography>
                <Typography variant="caption" fontWeight="700" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: 0.5 }}>
                     {card.type_line?.split(' — ')[0]}
                </Typography>
            </Box>
        </Card>
    );
};
