import React from 'react';
import {
    Paper, Table, TableBody, TableCell, TableContainer,
    TableHead, TableRow, Typography, Box, Chip
} from '@mui/material';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import EmailIcon from '@mui/icons-material/Email';

export default function Alerts({ alerts }) {
    if (!alerts || !Array.isArray(alerts) || alerts.length === 0) {
        return (
            <Box sx={{ py: 10, textAlign: 'center', border: '1px dashed', borderColor: 'divider', borderRadius: 3, bgcolor: 'rgba(0,0,0,0.01)' }}>
                <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.disabled' }}>
                    No alerts detected. Distribution network is stable.
                </Typography>
            </Box>
        );
    }

    return (
        <TableContainer
            component={Paper}
            sx={{ border: 'none', boxShadow: '0 4px 24px rgba(0,0,0,0.03)', borderRadius: 3, overflowX: 'auto', width: '100%' }}
        >
            <Table sx={{ minWidth: 800, width: '100%', tableLayout: 'fixed' }}>
                <TableHead sx={{ bgcolor: 'rgba(245, 158, 11, 0.05)' }}>
                    <TableRow>
                        <TableCell sx={{ color: 'text.secondary', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', py: 1.8, width: '20%' }}>Timestamp</TableCell>
                        <TableCell sx={{ color: 'text.secondary', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', py: 1.8, width: '25%' }}>Lead / Builder</TableCell>
                        <TableCell sx={{ color: 'text.secondary', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', py: 1.8, width: '35%' }}>Technical Log</TableCell>
                        <TableCell align="right" sx={{ color: 'text.secondary', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', py: 1.8, width: '20%' }}>Escalation</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {alerts.map((a, i) => (
                        <TableRow
                            key={i}
                            hover
                            sx={{ '&:last-child td, &:last-child th': { border: 0 }, transition: 'background-color 0.15s', '& td': { py: 2 } }}
                        >
                            <TableCell>
                                <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary' }}>
                                    {new Date(a.sent_time).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' })}
                                </Typography>
                            </TableCell>
                            <TableCell>
                                <Typography variant="body2" sx={{ fontWeight: 800, color: 'error.main' }}>
                                    {a.builder_name}
                                </Typography>
                                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, display: 'block' }}>
                                    {a.first_name} {a.last_name || ''} ({a.mobile})
                                </Typography>
                            </TableCell>
                            <TableCell>
                                <Box sx={{ p: 1, bgcolor: '#fff5f5', borderRadius: 1, borderLeft: '3px solid', borderColor: 'error.main', fontSize: 10, fontFamily: 'monospace', color: '#c62828', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                    {JSON.stringify(a.crm_response) || "Connection Failed"}
                                </Box>
                                <Typography variant="caption" sx={{ color: 'text.disabled', fontWeight: 500, fontSize: 9, mt: 0.5, display: 'block' }}>
                                    Failed after {a.attempt_count} attempts
                                </Typography>
                            </TableCell>
                            <TableCell align="right">
                                <Chip 
                                    icon={<EmailIcon style={{ fontSize: 12 }} />}
                                    label="Email Sent" 
                                    size="small"
                                    sx={{ 
                                        fontWeight: 800, 
                                        fontSize: 10, 
                                        height: 22, 
                                        bgcolor: 'primary.main', 
                                        color: 'white'
                                    }} 
                                />
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
}
