import React from 'react';
import {
    Paper, Table, TableBody, TableCell, TableContainer,
    TableHead, TableRow, Typography, Chip, Box,
    Card, CardContent, Stack, useMediaQuery, useTheme
} from '@mui/material';

function BuilderList({ text, type }) {
    if (!text) return <Typography variant="caption" sx={{ color: 'text.disabled', fontStyle: 'italic', opacity: 0.5 }}>-</Typography>;
    
    let color = 'default';
    if (type === 'success') color = 'success';
    else if (type === 'error') color = 'error';
    else color = 'primary';

    const builders = text.split(',').map(b => b.trim()).filter(b => b);
    const limit = 4;
    const shown = builders.slice(0, limit);
    const remaining = builders.length - limit;

    return (
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', alignItems: 'flex-start' }}>
            {shown.map((b, i) => (
                <Chip 
                    key={i} 
                    label={b} 
                    size="small" 
                    color={color} 
                    variant={type === 'selected' ? 'outlined' : 'filled'}
                    sx={{ 
                        fontSize: 9, 
                        fontWeight: 700, 
                        height: 18,
                        borderRadius: 1,
                        ...(type === 'success' && { bgcolor: 'rgba(16, 185, 129, 0.08)', color: 'success.main', borderColor: 'transparent' }),
                        ...(type === 'error' && { bgcolor: 'rgba(239, 68, 68, 0.08)', color: 'error.main', borderColor: 'transparent' }),
                        ...(type === 'selected' && { borderColor: 'rgba(0,0,0,0.1)', color: 'text.primary' })
                    }} 
                />
            ))}
            {remaining > 0 && (
                <Typography variant="caption" sx={{ fontWeight: 700, fontSize: 9, color: 'text.secondary', ml: 0.5, mt: 0.3 }}>
                    +{remaining} more
                </Typography>
            )}
        </Box>
    );
}

function LeadCard({ l }) {
    const name = (l.first_name || l.last_name) ? `${l.first_name || ''} ${l.last_name || ''}`.trim() : 'Unknown Lead';
    return (
        <Card sx={{ mb: 2, border: '1px solid rgba(0,0,0,0.05)', boxShadow: '0 2px 8px rgba(0,0,0,0.04)', borderRadius: 3 }}>
            <CardContent sx={{ p: 2.5, '&:last-child': { pb: 2.5 } }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5 }}>
                    <Box>
                        <Typography variant="subtitle2" sx={{ fontWeight: 800, color: 'primary.main', mb: 0.2 }}>
                            {name}
                        </Typography>
                        {l.created_at && (
                            <Typography variant="caption" sx={{ color: 'text.disabled', fontWeight: 600, fontSize: 9 }}>
                                {new Date(l.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                            </Typography>
                        )}
                    </Box>
                    <Chip
                        label={l.status || 'PENDING'}
                        size="small"
                        sx={{
                            fontWeight: 800,
                            fontSize: 9,
                            height: 20,
                            bgcolor: l.status === 'SUCCESS' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                            color: l.status === 'SUCCESS' ? 'success.main' : 'warning.main',
                            border: '1px solid',
                            borderColor: 'currentColor'
                        }}
                    />
                </Box>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 500, display: 'block', mb: 1.5 }}>
                    📞 {l.mobile || 'No Phone'}
                </Typography>

                
                <Stack spacing={1.5}>
                    <Box>
                        <Typography variant="caption" sx={{ fontWeight: 700, color: 'text.secondary', fontSize: 10, display: 'block', mb: 0.5 }}>SELECTED BUILDERS</Typography>
                        <BuilderList text={l.selected_builders} type="selected" />
                    </Box>
                    <Box>
                        <Typography variant="caption" sx={{ fontWeight: 700, color: 'text.secondary', fontSize: 10, display: 'block', mb: 0.5 }}>SUCCESS BUILDERS</Typography>
                        <BuilderList text={l.success_builders} type="success" />
                    </Box>
                    <Box>
                        <Typography variant="caption" sx={{ fontWeight: 700, color: 'text.secondary', fontSize: 10, display: 'block', mb: 0.5 }}>FAILED BUILDERS</Typography>
                        <BuilderList text={l.failed_builders} type="error" />
                    </Box>
                </Stack>
            </CardContent>
        </Card>
    );
}

export default function Leads({ leads }) {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

    if (!leads || leads.length === 0) {
        return (
            <Box sx={{ py: 10, textAlign: 'center', border: '1px dashed', borderColor: 'divider', borderRadius: 3, bgcolor: 'rgba(0,0,0,0.01)' }}>
                <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.disabled' }}>
                    No lead data found in the current audit window.
                </Typography>
            </Box>
        );
    }

    if (isMobile) {
        return (
            <Box>
                {leads.map((l, i) => <LeadCard key={i} l={l} />)}
            </Box>
        );
    }

    return (
        <TableContainer
            component={Paper}
            sx={{ border: 'none', boxShadow: '0 4px 24px rgba(0,0,0,0.03)', borderRadius: 3, overflowX: 'auto', width: '100%' }}
        >
            <Table sx={{ minWidth: 1000, width: '100%', tableLayout: 'fixed' }}>
                <TableHead sx={{ bgcolor: 'rgba(15, 23, 42, 0.02)' }}>
                    <TableRow>
                        <TableCell sx={{ color: 'text.secondary', fontSize: 10, fontWeight: 800, textTransform: 'uppercase', py: 2.5, width: '12%' }}>Timestamp</TableCell>
                        <TableCell sx={{ color: 'text.secondary', fontSize: 10, fontWeight: 800, textTransform: 'uppercase', py: 2.5, width: '18%' }}>Lead Identity</TableCell>
                        <TableCell sx={{ color: 'text.secondary', fontSize: 10, fontWeight: 800, textTransform: 'uppercase', py: 2.5, width: '10%' }}>Contact</TableCell>
                        <TableCell align="center" sx={{ color: 'text.secondary', fontSize: 10, fontWeight: 800, textTransform: 'uppercase', py: 2.5, width: '8%' }}>Status</TableCell>
                        <TableCell sx={{ color: 'text.secondary', fontSize: 10, fontWeight: 800, textTransform: 'uppercase', py: 2.5, width: '18%' }}>Selected Builders</TableCell>
                        <TableCell sx={{ color: 'text.secondary', fontSize: 10, fontWeight: 800, textTransform: 'uppercase', py: 2.5, width: '17%' }}>Success</TableCell>
                        <TableCell sx={{ color: 'text.secondary', fontSize: 10, fontWeight: 800, textTransform: 'uppercase', py: 2.5, width: '17%' }}>Failed/Duplicate</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {leads.map((l, i) => {
                        const dateObj = l.created_at ? new Date(l.created_at) : null;
                        const dateStr = dateObj ? dateObj.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }) : '-';
                        const timeStr = dateObj ? dateObj.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }) : '';

                        return (
                            <TableRow
                                key={i}
                                hover
                                sx={{ '&:last-child td, &:last-child th': { border: 0 }, '& td': { py: 2.5, verticalAlign: 'top' } }}
                            >
                                <TableCell>
                                    <Typography variant="body2" sx={{ fontWeight: 700, fontSize: 12, color: 'text.primary' }}>
                                        {dateStr}
                                    </Typography>
                                    <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: 10, fontWeight: 500 }}>
                                        {timeStr}
                                    </Typography>
                                </TableCell>
                                <TableCell>
                                    <Typography variant="body2" sx={{ fontWeight: 800, color: 'primary.main', fontSize: 13 }}>
                                        {(l.first_name || l.last_name) ? `${l.first_name || ''} ${l.last_name || ''}` : 'Unknown'}
                                    </Typography>
                                    <Typography variant="caption" sx={{ color: 'text.disabled', fontSize: 9 }}> ID: {l.lead_id?.substring(0,8) || 'N/A'}</Typography>
                                </TableCell>
                                <TableCell sx={{ fontSize: 12, color: 'text.secondary', fontWeight: 600 }}>
                                    {l.mobile || '-'}
                                </TableCell>
                                <TableCell align="center">
                                    <Chip
                                        label={l.status || 'NEW'}
                                        size="small"
                                        sx={{
                                            fontWeight: 900, fontSize: 9, height: 20,
                                            bgcolor: l.status === 'SUCCESS' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                                            color: l.status === 'SUCCESS' ? 'success.main' : 'warning.main',
                                            border: '1px solid', borderColor: 'currentColor',
                                            borderRadius: 1
                                        }}
                                    />
                                </TableCell>
                                <TableCell>
                                    <BuilderList text={l.selected_builders} type="selected" />
                                </TableCell>
                                <TableCell>
                                    <BuilderList text={l.success_builders} type="success" />
                                </TableCell>
                                <TableCell>
                                    <BuilderList text={l.failed_builders} type="error" />
                                </TableCell>
                            </TableRow>
                        );
                    })}
                </TableBody>
            </Table>
        </TableContainer>

    );
}

