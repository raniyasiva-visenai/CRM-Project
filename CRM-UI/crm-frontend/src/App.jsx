import React, { useState, useEffect } from 'react';
import {
    Box, Typography, IconButton, CircularProgress,
    Chip, BottomNavigation, BottomNavigationAction, Paper, useMediaQuery, useTheme
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import DashboardIcon from '@mui/icons-material/Dashboard';
import People from '@mui/icons-material/People';
import Apartment from '@mui/icons-material/Apartment';
import Notifications from '@mui/icons-material/Notifications';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Leads from './pages/Leads';
import Builders from './pages/Builders';
import Alerts from './pages/Alerts';
import Login from './pages/Login';

const API_BASE = "http://localhost:8000";

function App() {
    const [token, setToken] = useState(localStorage.getItem("token"));
    const [activeTab, setActiveTab] = useState('dashboard');
    const [stats, setStats] = useState({ leads: [], distribution: [], recent_activity: [] });
    const [leads, setLeads] = useState([]);
    const [builders, setBuilders] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(false);

    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));   // < 600px
    const isTablet = useMediaQuery(theme.breakpoints.down('md'));   // < 900px

    const handleLogin = (user, pwd) => {
        const mockToken = "iris_jwt_test_token";
        localStorage.setItem("token", mockToken);
        setToken(mockToken);
    };

    const handleLogout = () => {
        localStorage.removeItem("token");
        setToken(null);
    };

    const fetchData = async () => {
        setLoading(true);
        try {
            const responses = await Promise.all([
                fetch(`${API_BASE}/stats`),
                fetch(`${API_BASE}/builders`),
                fetch(`${API_BASE}/leads`),
                fetch(`${API_BASE}/alerts`)
            ]);
            const [sData, bData, lData, aData] = await Promise.all(responses.map(r => r.json()));
            setStats(sData);
            setBuilders(bData);
            setLeads(lData);
            setAlerts(aData);
        } catch (e) {
            console.error("Dashboard Sync Error:", e);
        }
        setLoading(false);
    };

    useEffect(() => {
        if (token) fetchData();
    }, [token]);

    if (!token) return <Login onLogin={handleLogin} />;

    const tabLabels = {
        dashboard: 'Analytics Overview',
        leads: 'Leads Tracker',
        builders: 'Builders Status',
        alerts: 'Dist. Alerts',
    };

    const pageContent = (
        <Box
            component="main"
            className="scroll-container"
            sx={{
                flexGrow: 1,
                p: { xs: 2, sm: 3, md: 5 },
                pb: { xs: isMobile ? 10 : 5, md: 5 },
                bgcolor: 'background.default',
                minHeight: '100vh',
            }}
        >
            {/* Page Header */}
            <Box sx={{
                mb: { xs: 3, md: 5 },
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 2
            }}>
                <Box>
                    <Typography
                        variant={isMobile ? 'h6' : 'h5'}
                        color="primary"
                        sx={{ fontWeight: 800 }}
                    >
                        {tabLabels[activeTab]}
                    </Typography>
                    <Box sx={{ mt: 0.5, display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
                        <Chip
                            label="ENTERPRISE"
                            size="small"
                            color="secondary"
                            sx={{ height: 18, fontSize: 10, fontWeight: 900, borderRadius: 1 }}
                        />
                        <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary', letterSpacing: 0.5 }}>
                            Status: <Box component="span" sx={{ color: 'success.main', fontWeight: 800 }}>OPTIMAL</Box>
                        </Typography>
                    </Box>
                </Box>

                <IconButton
                    onClick={fetchData}
                    disabled={loading}
                    sx={{
                        bgcolor: 'white',
                        border: '1px solid',
                        borderColor: 'divider',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
                        p: 1.2,
                        '&:hover': { bgcolor: '#f8fafc', transform: 'rotate(180deg)', transition: 'all 0.4s' }
                    }}
                >
                    {loading ? <CircularProgress size={18} /> : <RefreshIcon sx={{ color: 'primary.main', fontSize: 20 }} />}
                </IconButton>
            </Box>

            {/* Page Content */}
            <Box sx={{ width: '100%' }}>
                {activeTab === 'dashboard' && <Dashboard stats={stats} builders={builders} leads={leads} />}
                {activeTab === 'leads' && <Leads leads={leads} />}
                {activeTab === 'builders' && <Builders builders={builders} />}
                {activeTab === 'alerts' && <Alerts alerts={alerts} />}
            </Box>
        </Box>
    );

    /* ── Mobile Layout: Bottom Nav ──────────────────────── */
    if (isMobile) {
        return (
            <Box sx={{ display: 'flex', flexDirection: 'column', height: '100dvh', overflow: 'hidden' }}>
                {/* Mobile Top Bar */}
                <Box sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    px: 2,
                    py: 1.5,
                    bgcolor: '#0f172a',
                    borderBottom: '1px solid rgba(255,255,255,0.05)',
                    flexShrink: 0
                }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Box sx={{
                            bgcolor: '#c5a059', width: 28, height: 28, borderRadius: 1.5,
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontWeight: 900, color: '#0f172a', fontSize: 13
                        }}>I</Box>
                        <Typography variant="subtitle1" sx={{ color: 'white', fontWeight: 800, letterSpacing: 0.5 }}>IRIS CRM</Typography>
                    </Box>
                    <IconButton onClick={handleLogout} size="small" sx={{ color: 'rgba(255,255,255,0.5)' }}>
                        <Typography variant="caption" sx={{ fontWeight: 700 }}>SIGN OUT</Typography>
                    </IconButton>
                </Box>

                {/* Scrollable Content */}
                <Box sx={{ flex: 1, overflowY: 'auto', overflowX: 'hidden' }}>
                    {pageContent}
                </Box>

                {/* Bottom Nav */}
                <Paper elevation={8} sx={{ flexShrink: 0, borderTop: '1px solid rgba(0,0,0,0.05)' }}>
                    <BottomNavigation
                        value={activeTab}
                        onChange={(_, v) => setActiveTab(v)}
                        sx={{ bgcolor: '#0f172a', '& .MuiBottomNavigationAction-root': { color: 'rgba(255,255,255,0.4)', minWidth: 0 }, '& .Mui-selected': { color: '#c5a059' } }}
                    >
                        <BottomNavigationAction label="Dashboard" value="dashboard" icon={<DashboardIcon fontSize="small" />} />
                        <BottomNavigationAction label="Leads" value="leads" icon={<People fontSize="small" />} />
                        <BottomNavigationAction label="Builders" value="builders" icon={<Apartment fontSize="small" />} />
                        <BottomNavigationAction label="Alerts" value="alerts" icon={<Notifications fontSize="small" />} />
                    </BottomNavigation>
                </Paper>
            </Box>
        );
    }

    /* ── Desktop / Tablet Layout: Sidebar ──────────────── */
    return (
        <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
            <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} onLogout={handleLogout} compact={isTablet} />
            {pageContent}
        </Box>
    );
}

export default App;
