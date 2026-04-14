import React from 'react';
import { Card, Box, Typography, Icon } from '@mui/material';

export default function StatCard({ label, val, sub, icon }) {
    return (
        <Card className="premium-card" sx={{ p: 3.5, position: 'relative', overflow: 'hidden' }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                <Typography variant="subtitle1" sx={{ color: 'text.secondary', fontSize: 11 }}>
                    {label}
                </Typography>

                <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
                    <Typography variant="h4" color="primary">
                        {val}
                    </Typography>
                    {sub && (
                        <Typography variant="caption" sx={{ color: sub.includes('+') ? 'success.main' : 'text.disabled', fontWeight: 700 }}>
                            {sub}
                        </Typography>
                    )}
                </Box>
            </Box>

            <Box sx={{
                position: 'absolute',
                top: 20,
                right: 20,
                color: 'secondary.main',
                opacity: 0.2,
                transform: 'scale(1.2)'
            }}>
                {icon}
            </Box>

            <Box sx={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                width: '100%',
                height: 4,
                bgcolor: 'secondary.main',
                opacity: 0.1
            }} />
        </Card>
    );
}
