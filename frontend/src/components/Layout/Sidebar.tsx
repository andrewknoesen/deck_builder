// ... imports ...
import {
  Drawer,
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
// ... icons ...
import DashboardIcon from '@mui/icons-material/Dashboard';
import LayersIcon from '@mui/icons-material/Layers';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import CollectionsIcon from '@mui/icons-material/Collections';
import { Link, useLocation } from 'react-router-dom';

const drawerWidth = 240;

interface SidebarProps {
  open: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ open }) => {
// ...

  const location = useLocation();

  const menuItems = [
    { text: 'Home', icon: <DashboardIcon />, path: '/' },
    { text: 'My Decks', icon: <LayersIcon />, path: '/decks' },
    { text: 'New Deck', icon: <AddCircleOutlineIcon />, path: '/decks/new' },
    { text: 'Collection', icon: <CollectionsIcon />, path: '/collection' },
  ];

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={open}
      sx={{
        width: open ? drawerWidth : 0,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          top: 64, // Height of AppBar, push it down
          height: 'calc(100% - 64px)',
          borderRight: 1,
          borderColor: 'divider',
        },
      }}
    >
      <Box sx={{ overflow: 'auto' }}>
        <List>
          {menuItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton
                component={Link}
                to={item.path}
                selected={location.pathname === item.path}
                sx={{
                    '&.Mui-selected': {
                        bgcolor: 'primary.main',
                        color: 'white',
                        '&:hover': {
                            bgcolor: 'primary.dark',
                        },
                        '& .MuiListItemIcon-root': {
                            color: 'white',
                        }
                    },
                    borderRadius: 2,
                    mx: 1,
                    my: 0.5,
                }}
              >
                <ListItemIcon sx={{ minWidth: 40, color: 'inherit' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>
    </Drawer>
  );
};
