import React from 'react';
import {
    Paper, Table, TableBody, TableCell, TableContainer,
    TableHead, TableRow, Typography, Chip, Box,
    Card, CardContent, Stack, useMediaQuery, useTheme
} from '@mui/material';

function BuilderList({ text, type }) {
    if (!text) return <Typography variant="caption" sx={{ color: 'text.disabled', fontStyle: 'italic' }}>None Matched</Typography>;
    
    let color = 'default';
    if (type === 'success') color = 'success';
    else if (type === 'error') color = 'error';
    else color = 'primary';

    const builders = text.split(',').map(b => b.trim()).filter(b => b);

    return (
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            {builders.map((b, i) => (
                <Chip 
                    key={i} 
                    label={b} 
                    size="small" 
                    color={color} 
                    variant={type === 'selected' ? 'outlined' : 'filled'}
                    sx={{ 
                        fontSize: 10, 
                        fontWeight: 700, 
                        height: 20,
                        ...(type === 'success' && { bgcolor: 'rgba(16, 185, 129, 0.1)', color: 'success.main', borderColor: 'transparent' }),
                        ...(type === 'error' && { bgcolor: 'rgba(245, 158, 11, 0.1)', color: 'error.main', borderColor: 'transparent' })
                    }} 
                />
            ))}
        </Box>
    );
}

function LeadCard({ l }) {
    return (
        <Card sx={{ mb: 2, border: '1px solid rgba(0,0,0,0.05)', boxShadow: '0 2px 8px rgba(0,0,0,0.04)', borderRadius: 3 }}>
            <CardContent sx={{ p: 2.5, '&:last-child': { pb: 2.5 } }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 800, color: 'primary.main', mb: 0.5 }}>
                        {l.first_name} {l.last_name || ''}
                    </Typography>
                    <Chip
                        label={l.status}
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
                    📞 {l.mobile}
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

    if (leads.length === 0) {
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
            <Table sx={{ minWidth: 800, width: '100%', tableLayout: 'fixed' }}>
                <TableHead sx={{ bgcolor: 'rgba(0,0,0,0.01)' }}>
                    <TableRow>
                        <TableCell sx={{ color: 'text.secondary', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', py: 1.8, width: '15%' }}>Name</TableCell>
                        <TableCell sx={{ color: 'text.secondary', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', py: 1.8, width: '12%' }}>Phone</TableCell>
                        <TableCell align="center" sx={{ color: 'text.secondary', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', py: 1.8, width: '13%' }}>Status</TableCell>
                        <TableCell sx={{ color: 'text.secondary', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', py: 1.8, width: '22%' }}>Selected Builders</TableCell>
                        <TableCell sx={{ color: 'text.secondary', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', py: 1.8, width: '19%' }}>Success</TableCell>
                        <TableCell sx={{ color: 'text.secondary', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', py: 1.8, width: '19%' }}>Failed</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {leads.map((l, i) => (
                        <TableRow
                            key={i}
                            hover
                            sx={{ '&:last-child td, &:last-child th': { border: 0 }, transition: 'background-color 0.15s', '& td': { py: 2 } }}
                        >
                            <TableCell>
                                <Typography variant="body2" sx={{ fontWeight: 700, color: 'primary.main', whiteSpace: 'nowrap' }}>
                                    {l.first_name} {l.last_name || ''}
                                </Typography>
                            </TableCell>
                            <TableCell sx={{ fontSize: 13, color: 'text.secondary', fontWeight: 500, whiteSpace: 'nowrap' }}>
                                {l.mobile}
                            </TableCell>
                            <TableCell align="center">
                                <Chip
                                    label={l.status}
                                    size="small"
                                    sx={{
                                        fontWeight: 800, fontSize: 10, height: 22,
                                        bgcolor: l.status === 'SUCCESS' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                                        color: l.status === 'SUCCESS' ? 'success.main' : 'warning.main',
                                        border: '1px solid', borderColor: 'currentColor'
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
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
}
