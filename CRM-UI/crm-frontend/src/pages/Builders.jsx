import React from 'react';
import { Grid, Card, Typography, Box, Chip, Stack } from '@mui/material';

export default function Builders({ builders }) {
    if (!builders || builders.length === 0) {
        return (
            <Box sx={{ py: 10, textAlign: 'center', border: '1px dashed', borderColor: 'divider', borderRadius: 3, bgcolor: 'rgba(0,0,0,0.01)' }}>
                <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.disabled' }}>
                    No builder data available.
                </Typography>
            </Box>
        );
    }
    return (
        <Grid container spacing={{ xs: 2, sm: 3, md: 4 }}>
            {builders.map((b, i) => (
                <Grid item xs={12} sm={6} md={4} key={i}>
                    <Card className="premium-card" sx={{ p: { xs: 2.5, md: 4 } }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
                            <Box>
                                <Typography variant="h6" color="primary" sx={{ fontWeight: 800 }}>
                                    {b.builder_name}
                                </Typography>
                                <Typography variant="caption" sx={{ fontWeight: 700, color: 'secondary.main', textTransform: 'uppercase', letterSpacing: 1.5 }}>
                                    {b.crm_type} Matrix
                                </Typography>
                            </Box>
                            <Box sx={{
                                width: 32,
                                height: 32,
                                bgcolor: 'rgba(0,0,0,0.02)',
                                borderRadius: '50%',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: 11,
                                fontWeight: 900,
                                color: 'text.disabled',
                                border: '1px solid rgba(0,0,0,0.05)'
                            }}>
                                {String(i + 1).padStart(2, '0')}
                            </Box>
                        </Box>

                        <Stack direction="row" spacing={2} sx={{ mt: 3 }}>
                            <StatusMiniCard label="Sync" val={b.success || 0} type="success" />
                            <StatusMiniCard label="Dupes" val={b.duplicates || 0} type="warning" />
                            <StatusMiniCard label="Drops" val={b.failures || 0} type="error" />
                        </Stack>

                        <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid rgba(0,0,0,0.03)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <Typography variant="caption" sx={{ fontWeight: 700, color: 'text.disabled' }}>
                                Connection Status
                            </Typography>
                            <Chip
                                label="ACTIVE"
                                size="small"
                                color="success"
                                sx={{ height: 16, fontSize: 8, fontWeight: 900 }}
                            />
                        </Box>
                    </Card>
                </Grid>
            ))}
        </Grid>
    );
}

function StatusMiniCard({ label, val, type }) {
    const colors = {
        success: { bg: 'rgba(16, 185, 129, 0.08)', text: '#059669' },
        warning: { bg: 'rgba(245, 158, 11, 0.08)', text: '#d97706' },
        error: { bg: 'rgba(239, 68, 68, 0.08)', text: '#dc2626' }
    };

    return (
        <Box sx={{
            flex: 1,
            bgcolor: colors[type].bg,
            px: 1,
            py: 1.5,
            borderRadius: 2,
            textAlign: 'center',
            border: '1px solid transparent',
            transition: 'all 0.2s',
            '&:hover': { borderColor: colors[type].text, bgcolor: 'white' }
        }}>
            <Typography variant="h6" sx={{ fontWeight: 800, lineHeight: 1, color: colors[type].text }}>
                {val}
            </Typography>
            <Typography variant="caption" sx={{ fontWeight: 700, textTransform: 'uppercase', fontSize: 9, color: 'text.secondary', opacity: 0.8 }}>
                {label}
            </Typography>
        </Box>
    );
}
