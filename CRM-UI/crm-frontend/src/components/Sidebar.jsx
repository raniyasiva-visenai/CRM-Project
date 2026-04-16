import React from 'react';
import {
    Drawer, List, ListItem, ListItemButton,
    ListItemIcon, ListItemText, Box, Typography, Divider, Tooltip
} from '@mui/material';
import BarChart from '@mui/icons-material/BarChart';
import People from '@mui/icons-material/People';
import Apartment from '@mui/icons-material/Apartment';
import Notifications from '@mui/icons-material/Notifications';
import Logout from '@mui/icons-material/Logout';
import DashboardIcon from '@mui/icons-material/Dashboard';

const FULL_WIDTH = 260;
const COMPACT_WIDTH = 72;

export default function Sidebar({ activeTab, setActiveTab, onLogout, compact = false }) {
    const drawerWidth = compact ? COMPACT_WIDTH : FULL_WIDTH;

    const menuItems = [
        { id: 'dashboard', label: 'Dashboard', icon: <DashboardIcon /> },
        { id: 'leads', label: 'Leads Tracker', icon: <People /> },
        { id: 'builders', label: 'Builders Status', icon: <Apartment /> },
        { id: 'alerts', label: 'Alerts', icon: <Notifications /> },
    ];

    return (
        <Drawer
            variant="permanent"
            sx={{
                width: drawerWidth,
                flexShrink: 0,
                transition: 'width 0.3s ease',
                [`& .MuiDrawer-paper`]: {
                    width: drawerWidth,
                    boxSizing: 'border-box',
                    bgcolor: '#0f172a',
                    color: 'white',
                    borderRight: 'none',
                    boxShadow: '4px 0 24px rgba(0,0,0,0.08)',
                    overflow: 'hidden',
                    transition: 'width 0.3s ease',
                },
            }}
        >
            {/* Logo Area */}
            <Box sx={{
                p: compact ? 2 : 4,
                mb: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: compact ? 'center' : 'flex-start',
                gap: 2
            }}>
                <Box sx={{
                    bgcolor: 'secondary.main',
                    width: 32,
                    height: 32,
                    borderRadius: 1.5,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 900,
                    color: 'primary.main',
                    fontSize: 14,
                    flexShrink: 0,
                    boxShadow: '0 0 15px rgba(197, 160, 89, 0.3)'
                }}>
                    C
                </Box>
                {!compact && (
                    <Typography variant="h6" sx={{ fontWeight: 800, letterSpacing: 0.5, fontSize: 17, whiteSpace: 'nowrap' }}>
                        CRM
                    </Typography>
                )}
            </Box>

            <Divider sx={{ borderColor: 'rgba(255,255,255,0.06)', mx: compact ? 1 : 2, mb: 2 }} />

            {/* Nav Items */}
            <List sx={{ flexGrow: 1, px: compact ? 1 : 2 }}>
                {!compact && (
                    <Typography variant="caption" sx={{
                        px: 2, mb: 1.5, display: 'block',
                        fontWeight: 700, opacity: 0.35, textTransform: 'uppercase', letterSpacing: 1.5
                    }}>
                        Management
                    </Typography>
                )}
                {menuItems.map((item) => (
                    <ListItem key={item.id} disablePadding sx={{ mb: 0.5, display: 'block' }}>
                        <Tooltip title={compact ? item.label : ''} placement="right" arrow>
                            <ListItemButton
                                selected={activeTab === item.id}
                                onClick={() => setActiveTab(item.id)}
                                sx={{
                                    borderRadius: 2.5,
                                    py: 1.3,
                                    px: compact ? 1.5 : 2,
                                    justifyContent: compact ? 'center' : 'flex-start',
                                    minHeight: 44,
                                    bgcolor: activeTab === item.id ? 'rgba(255,255,255,0.09)' : 'transparent',
                                    '&.Mui-selected': {
                                        bgcolor: 'rgba(255,255,255,0.1)',
                                        '&:hover': { bgcolor: 'rgba(255,255,255,0.14)' }
                                    },
                                    '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' },
                                    transition: 'all 0.2s ease-in-out'
                                }}
                            >
                                <ListItemIcon sx={{
                                    color: activeTab === item.id ? 'secondary.main' : 'rgba(255,255,255,0.45)',
                                    minWidth: compact ? 0 : 40,
                                    mr: compact ? 0 : 0,
                                    transform: activeTab === item.id ? 'scale(1.1)' : 'scale(1)',
                                    transition: 'all 0.2s',
                                    justifyContent: 'center'
                                }}>
                                    {item.icon}
                                </ListItemIcon>
                                {!compact && (
                                    <ListItemText
                                        primary={item.label}
                                        primaryTypographyProps={{
                                            fontSize: 13.5,
                                            fontWeight: activeTab === item.id ? 700 : 500,
                                            color: activeTab === item.id ? 'white' : 'rgba(255,255,255,0.55)',
                                            noWrap: true
                                        }}
                                    />
                                )}
                            </ListItemButton>
                        </Tooltip>
                    </ListItem>
                ))}
            </List>

            {/* Logout */}
            <Box sx={{ p: compact ? 1 : 2, mb: 1 }}>
                <Divider sx={{ borderColor: 'rgba(255,255,255,0.06)', mb: 1 }} />
                <Tooltip title={compact ? 'Sign Out' : ''} placement="right" arrow>
                    <ListItemButton
                        onClick={onLogout}
                        sx={{
                            borderRadius: 2.5,
                            py: 1.2,
                            px: compact ? 1.5 : 2,
                            justifyContent: compact ? 'center' : 'flex-start',
                            color: 'rgba(255,255,255,0.4)',
                            '&:hover': { bgcolor: 'rgba(239,68,68,0.1)', color: '#ef4444' },
                            transition: 'all 0.2s'
                        }}
                    >
                        <ListItemIcon sx={{ color: 'inherit', minWidth: compact ? 0 : 40, justifyContent: 'center' }}>
                            <Logout fontSize="small" />
                        </ListItemIcon>
                        {!compact && (
                            <ListItemText
                                primary="Sign Out"
                                primaryTypographyProps={{ fontSize: 13, fontWeight: 600 }}
                            />
                        )}
                    </ListItemButton>
                </Tooltip>
            </Box>
        </Drawer>
    );
}
