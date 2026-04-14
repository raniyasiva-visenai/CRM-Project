import React from 'react';
import {
    Grid, Box, Typography, Paper, Chip
} from '@mui/material';
import BuilderIcon from '@mui/icons-material/AccountBalance';
import PeopleIcon from '@mui/icons-material/People';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import StatCard from '../components/StatCard';

export default function Dashboard({ stats, builders, leads }) {
    // Computations wrapper for safe defaults
    const distStats = stats?.distribution || [];
    const successCount = distStats.find(s => s.status === 'SUCCESS')?.count || 0;
    const failedCount = distStats.find(s => s.status === 'FAILED' || s.status === 'DUPLICATE')?.count || 0;

    const totalBuilders = builders ? builders.length : 0;
    const totalLeads = leads ? leads.length : 0;

    return (
        <Box sx={{ flexGrow: 1 }}>
            <Grid container spacing={4} sx={{ mb: 6 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard label="Total Builders" val={totalBuilders.toString()} sub="Connected Systems" icon={<BuilderIcon sx={{ color: 'primary.main' }} />} />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard label="Leads Received" val={totalLeads.toString()} sub="Total leads captured" icon={<PeopleIcon sx={{ color: 'info.main' }} />} />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard label="Success Submissions" val={successCount.toString()} sub="Successfully Distributed" icon={<CheckCircleIcon sx={{ color: 'success.main' }} />} />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard label="Failed Submissions" val={failedCount.toString()} sub="Encountered Errors" icon={<ErrorIcon sx={{ color: 'error.main' }} />} />
                </Grid>
            </Grid>

            {/* Display Builders List directly below KPIs */}
            <Typography variant="h5" sx={{ fontWeight: 800, mb: 3, color: 'primary.main' }}>
                Active Builders
            </Typography>
            <Grid container spacing={3}>
                {builders && builders.map((b, idx) => (
                    <Grid item xs={12} sm={6} md={4} key={idx}>
                        <Paper sx={{ 
                            p: 3, 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: 2, 
                            borderRadius: 3,
                            transition: 'transform 0.2s',
                            boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                            '&:hover': { transform: 'translateY(-4px)', boxShadow: '0 8px 24px rgba(0,0,0,0.08)' }
                        }}>
                            <Box sx={{
                                width: 50, height: 50, borderRadius: '12px',
                                bgcolor: 'rgba(197, 160, 89, 0.1)', color: 'secondary.main',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                fontWeight: 900, fontSize: 20
                            }}>
                                {b.builder_name.charAt(0)}
                            </Box>
                            <Box>
                                <Typography variant="subtitle1" sx={{ fontWeight: 800, color: 'text.primary' }}>
                                    {b.builder_name}
                                </Typography>
                                <Chip 
                                    label={b.crm_type.toUpperCase()} 
                                    size="small" 
                                    sx={{ mt: 0.5, fontSize: 10, fontWeight: 700, height: 20, bgcolor: 'rgba(0,0,0,0.04)' }} 
                                />
                            </Box>
                        </Paper>
                    </Grid>
                ))}
            </Grid>
        </Box>
    );
}
